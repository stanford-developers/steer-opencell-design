# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Electrode formulation definitions combining active materials, binders, and conductive additives.

Blending rule
-------------
A formulation is a list of (component, mass_fraction) pairs for three collections:

* ``active_materials`` — store or source lithium and contribute to capacity.
* ``binders`` — mechanical/chemical support, non-capacity contributors.
* ``conductive_additives`` — improve electronic conductivity, non-capacity contributors.

All mass fractions are internally stored in the range ``[0, 1]``. The public
``*_weight`` properties expose them as percentages (``[0, 100]``). The sum of
all fractions across active materials, binders, and conductive additives must
equal 1.0 within ``MASS_FRACTION_SUM_TOLERANCE`` (see ``Utils.Constants``).

Blended properties are computed with the following rules:

* Density: volume additivity, ``1/rho = sum(w_i / rho_i)``.
* Specific cost: mass-weighted sum, ``c = sum(c_i * w_i)``.
* Colour: mass-weighted RGB.
* Specific capacity curve: for a single active material, its curve scaled by
  the active material's mass fraction. For multiple active materials the
  common charge and discharge voltage windows are resampled on a grid of
  ``VOLTAGE_BLEND_GRID_POINTS`` points (see ``Utils.Constants``); each
  material's weighted contribution is interpolated onto the grid and summed.

Indexed slot properties
-----------------------
Each formulation exposes a fixed number of indexed slot properties
(``active_material_1``, ``active_material_2``, ``active_material_3``,
``binder_1``, ``binder_2``, ``conductive_additive_1``,
``conductive_additive_2``) that map to slots in the underlying dict. These
names are required by ``PropagationMixin`` — child objects store the name of
their slot in ``_parent_attr_name`` and ``setattr(parent, attr_name, self)``
is used to trigger recalculation up the tree.

Do not rename these indexed slot attributes without updating the
corresponding ``_set_parent(..., "<name>")`` call sites and the
``_restore_child_parent_refs`` override.
"""

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Constants.Units import *
from steer_core.Utils import round_dict_recursive

from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Propagation import PropagationMixin

from steer_opencell_design.Materials.ActiveMaterials import _ActiveMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive
from steer_opencell_design.Materials.CapacityCurveUtils import calculate_specific_capacity_curve, calculate_capacity_curve
from steer_opencell_design.Utils.Constants import (
    MASS_FRACTION_SUM_TOLERANCE,
    VOLTAGE_BLEND_GRID_POINTS,
)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, Any
import warnings
from collections import Counter


def _slot_material(coll: dict, index: int):
    """Return the material at position *index* in *coll*, or ``None`` if out of range."""
    items = list(coll.keys())
    return items[index] if index < len(items) else None


def _slot_weight(coll: dict, index: int):
    """Return the percentage weight at position *index* in *coll*, or ``None`` if out of range."""
    values = list(coll.values())
    return values[index] * 100 if index < len(values) else None


class _ElectrodeFormulation(
    ValidationMixin, 
    DunderMixin,
    PlotterMixin,
    PropagationMixin,
    SerializerMixin,
    ):
    """Base class for electrode formulations.

    Combines active materials, binders, and conductive additives with mass
    fractions to calculate blended density, cost, color, and composite
    voltage-capacity curves.
    """

    def __init__(
        self,
        active_materials: Dict[_ActiveMaterial, float],
        binders: Optional[Dict[Binder, float]] = {},
        conductive_additives: Optional[Dict[ConductiveAdditive, float]] = {},
        voltage_cutoff: Optional[float] = None,
        name: Optional[str] = "Electrode Formulation",
        *,
        mass: float = None,
        volume: float = None,
        **kwargs,
    ):
        """
        Initialize an object that represents an electrode formulation.

        Parameters
        ----------
        active_materials : Dict[_ActiveMaterial, float]
            A dictionary where keys are instances of _ActiveMaterial and values are their mass fractions in percent
        binders : Optional[Dict[Binder, float]]
            A dictionary where keys are instances of Binder and values are their mass fractions in percent
        conductive_additives : Optional[Dict[ConductiveAdditive, float]]
            A dictionary where keys are instances of ConductiveAdditive and values are their mass fractions in percent
        voltage_cutoff : Optional[float]
            The maximum voltage for the half-cell curves. If not provided, it will be set to
            the maximum voltage from the active materials' voltage cutoff range.
        name : Optional[str]
            Name of the electrode formulation. Defaults to 'Electrode Formulation'.
        mass : float
            Total mass of the electrode formulation. Defaults to None.
        volume : float
            Total volume of the electrode formulation. Defaults to None.
        """
        self._update_properties = False
        self._user_set_voltage_cutoff = False

        self.active_materials = active_materials
        self.binders = binders
        self.conductive_additives = conductive_additives
        self.voltage_cutoff = voltage_cutoff
        self.name = name

        self._mass = None
        self._volume = None
        self._cost = None
        self._cost_breakdown = {}
        self._mass_breakdown = {}

        if volume is not None:
            self.volume = volume
        if mass is not None:
            self.mass = mass

        self._check_formulation()
        self._calculate_all_properties()

    def _clear_cached_data(self) -> None:
        
        # clear the specific capacity curve cache
        self._specific_capacity_curve = None

        # clear the _specific_capacity_curve cache of all active materials
        for material in self._active_materials.keys():
            material._specific_capacity_curve = None
            material._specific_capacity_curves = None

    def _restore_child_parent_refs(self) -> None:
        """
        Override to set indexed property names for dict-based material collections.
        
        The default PropagationMixin implementation would set attr_name="active_materials"
        for all materials in _active_materials dict, but propagation requires indexed
        names like "active_material_1" to route through the correct setter.
        """
        for key, value in self.__dict__.items():
            if key in ('_parent', '_parent_attr_name'):
                continue
            
            # Handle dict-based material collections with indexed property names
            if key == '_active_materials' and isinstance(value, dict):
                for i, material in enumerate(value.keys(), 1):
                    if hasattr(material, '_set_parent'):
                        material._set_parent(self, f"active_material_{i}")
            elif key == '_binders' and isinstance(value, dict):
                for i, material in enumerate(value.keys(), 1):
                    if hasattr(material, '_set_parent'):
                        material._set_parent(self, f"binder_{i}")
            elif key == '_conductive_additives' and isinstance(value, dict):
                for i, material in enumerate(value.keys(), 1):
                    if hasattr(material, '_set_parent'):
                        material._set_parent(self, f"conductive_additive_{i}")
            else:
                # Default behavior for other attributes
                attr_name = key[1:] if key.startswith('_') else key
                self._set_parent_on_value(value, attr_name)

    def _calculate_all_properties(self) -> None:
        """Recalculate material, bulk, and electrochemical properties."""
        self._calculate_material_properties()
        self._check_formulation()

        self._get_voltage_operation_window()
        self._validate_and_set_voltage_cutoff()
        self._calculate_specific_capacity_curve()

        if hasattr(self, '_mass') and self._mass is not None:
            self._calculate_bulk_properties()

    def _calculate_material_properties(self) -> None:
        """Calculate density, specific cost, and colour from individual materials."""
        self._calculate_density()
        self._calculate_specific_cost()
        self._calculate_color()

    def _calculate_bulk_properties(self) -> None:
        """Calculate mass/cost breakdowns and the capacity curve."""
        self._calculate_breakdowns()
        self._calculate_capacity_curve()

    def _calculate_capacity_curve(self) -> np.ndarray:
        """Scale the specific capacity curve by mass to produce an absolute capacity curve."""

        if hasattr(self, "_specific_capacity_curve") and self._specific_capacity_curve is not None:

            # get the half cell curve from the formulation
            curve = self._specific_capacity_curve.copy()

            # calculate the capacity
            capacity = curve[:, 0] * self._mass

            # assign the capacity curve
            self._capacity_curve = np.column_stack((capacity, curve[:, 1], curve[:, 2]))

            # return the capacity curve
            return self._capacity_curve
        
        else:
            self._capacity_curve = None
            return self._capacity_curve

    def _calculate_breakdowns(self) -> None:
        """Calculate mass and cost breakdowns across all components."""
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()

    def _calculate_density(self) -> tuple[float, float]:
        """
        Calculate density using volume additivity assumption.
        For a mixture: 1/ρ_mix = Σ(w_i / ρ_i) where w_i are mass fractions.
        
        Returns
        -------
        tuple[float, float]
            (density in kg/m³, specific_volume in m³/kg)
        """
        # Collect (density, mass_fraction) pairs
        components = [(material._density, fraction) for material, fraction in self._iter_all_materials()]
        
        # Calculate specific volume: V_mix/m_mix = Σ(w_i / ρ_i)
        specific_volume = sum(fraction / density for density, fraction in components)
        density = 1.0 / specific_volume
        
        self._density = density
        self._specific_volume = specific_volume
        return density, specific_volume

    def _calculate_specific_cost(self) -> float:
        """
        Calculate the specific cost of the electrode formulation.

        :return: The specific cost of the electrode formulation in $/kg.
        """
        components = [(material._specific_cost, fraction) for material, fraction in self._iter_all_materials()]

        self._specific_cost = sum(cost * mf for cost, mf in components)
        return self._specific_cost

    def _calculate_color(self) -> str:
        """
        Calculate the average HTML color of the electrode formulation,
        weighted by the mass fraction of each component.

        :return: A hex color string representing the weighted average color.
        """

        def hex_to_rgb(hex_code: str) -> tuple:
            hex_code = hex_code.lstrip("#")
            return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb: tuple) -> str:
            return "#{:02x}{:02x}{:02x}".format(*map(lambda x: int(round(x)), rgb))

        # Gather all (rgb, fraction) pairs
        components = [(hex_to_rgb(material._color), fraction) for material, fraction in self._iter_all_materials()]

        # Weighted average of RGB channels
        total_r = sum(rgb[0] * f for rgb, f in components)
        total_g = sum(rgb[1] * f for rgb, f in components)
        total_b = sum(rgb[2] * f for rgb, f in components)

        avg_rgb = (total_r, total_g, total_b)

        self._color = rgb_to_hex(avg_rgb)
        return self._color

    def _get_voltage_operation_window(self) -> None:
        """
        Get the voltage operation window from each active material.
        Recalculates every time so that changes to active materials are reflected.

        Computes the intersection of all material voltage ranges and stores
        the result as (lower_bound, upper_bound) regardless of formulation type.
        """
        voltage_operation_windows = [material._voltage_operation_window for material in self._active_materials.keys()]

        lower_bounds = [min(w) for w in voltage_operation_windows]
        upper_bounds = [max(w) for w in voltage_operation_windows]

        common_lower = max(lower_bounds)
        common_upper = min(upper_bounds)

        self._voltage_operation_window = (common_lower, common_upper)

        return self._voltage_operation_window

    def _validate_and_set_voltage_cutoff(self) -> None:
        """
        Validate formulation voltage cutoff against common voltage range and set material cutoffs.
        The stored _voltage_operation_window is always (lower_bound, upper_bound).
        """
        min_voltage, max_voltage = self._voltage_operation_window

        # If no voltage cutoff is set, use the appropriate boundary
        if not hasattr(self, "_voltage_cutoff") or self._voltage_cutoff is None:
            if type(self) == CathodeFormulation:
                self._voltage_cutoff = max_voltage  # Use upper bound for cathodes
            else:
                self._voltage_cutoff = min_voltage  # Use lower bound for anodes
        else:
            # Check if current voltage cutoff is within the common range
            if self._voltage_cutoff < min_voltage:
                self._voltage_cutoff = min_voltage
            elif self._voltage_cutoff > max_voltage:
                self._voltage_cutoff = max_voltage

        # Set the voltage cutoff for each active material (skip if already in sync
        # to avoid triggering unnecessary @calculate_all_properties on materials)
        for material in self._active_materials.keys():
            if material._voltage_cutoff != self._voltage_cutoff:
                material.voltage_cutoff = self._voltage_cutoff

    def _check_formulation(self) -> None:
        """
        Validate the electrode formulation to ensure it meets the required criteria.
        """
        total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())

        if not (1.0 - MASS_FRACTION_SUM_TOLERANCE <= total_fraction <= 1.0 + MASS_FRACTION_SUM_TOLERANCE):
            warnings.warn(
                f"The total mass percentages of the formulation should sum to 100%. Current sum: {round(total_fraction * 100, 1)}%",
                UserWarning,
            )

        self._check_unique_names(self._active_materials, "active materials")
        self._check_unique_names(self._binders, "binders")
        self._check_unique_names(self._conductive_additives, "conductive additives")

    def _check_unique_names(self, components: Dict, component_type: str) -> None:
        """Warn if any components in *components* share the same name."""

        names = [comp.name for comp in components.keys()]
        duplicates = [name for name, count in Counter(names).items() if count > 1]
        if duplicates:
            warnings.warn(
                f"Duplicate names found in {component_type}: {duplicates}. "
                f"Each component should have a unique name.",
                UserWarning
            )

    def _calculate_specific_capacity_curve(self) -> None:
        """
        Calculate the half-cell curve for the electrode formulation based on the active materials
        and their weight fractions, treating charge and discharge curves separately.
        """

        def safe_interp(target_values, x_vals, y_vals):
            """Safe interpolation that handles decreasing x values."""
            if len(x_vals) <= 1:
                return np.full_like(target_values, np.nan)

            # Check if x values are decreasing
            if x_vals[0] > x_vals[-1] or np.mean(np.diff(x_vals)) < 0:
                # Sort by x values (ascending) and reorder y accordingly
                sort_idx = np.argsort(x_vals)
                return np.interp(target_values, x_vals[sort_idx], y_vals[sort_idx])
            else:
                # Normal case - x values already increasing
                return np.interp(target_values, x_vals, y_vals)

        # If just one material, then get that materials half-cell curve
        if len(self._active_materials) == 1:
            material = next(iter(self._active_materials))
            weight_frac = self._active_materials[material]
            curve = material._specific_capacity_curve.copy()
            curve[:, 0] *= weight_frac
            self._specific_capacity_curve = curve
            return

        # Determine common charge/discharge voltage ranges
        def get_common_voltage_range(direction: str):
            direction_value = 1 if direction == "charge" else -1
            v_starts = []
            v_ends = []

            for material in self._active_materials:
                direction_mask = material._specific_capacity_curve[:, 2] == direction_value
                direction_curve = material._specific_capacity_curve[direction_mask]

                if len(direction_curve) > 0:
                    voltages = direction_curve[:, 1]
                    v_starts.append(voltages.min())
                    v_ends.append(voltages.max())

            if not v_starts:  # No data for this direction
                return np.array([])

            v_start = max(v_starts)
            v_end = min(v_ends)

            # Ensure valid range
            if v_start >= v_end:
                return np.array([v_start])

            return np.linspace(v_start, v_end, num=VOLTAGE_BLEND_GRID_POINTS)

        v_charge_grid = get_common_voltage_range("charge")
        v_discharge_grid = get_common_voltage_range("discharge")

        charge_dfs = []
        discharge_dfs = []

        # Interpolate each material's contribution and weight by mass fraction
        for material, weight_frac in self._active_materials.items():
            curve = material._specific_capacity_curve.copy()
            curve[:, 0] *= weight_frac

            charge_curve = curve[curve[:, 2] == 1]
            discharge_curve = curve[curve[:, 2] == -1]

            # Safe interpolation for charge curve
            if len(charge_curve) > 0 and len(v_charge_grid) > 0:
                charge_interp = safe_interp(
                    v_charge_grid,
                    charge_curve[:, 1],  # voltage (x)
                    charge_curve[:, 0],  # capacity (y)
                )
            else:
                charge_interp = np.full_like(v_charge_grid, 0.0)

            # Safe interpolation for discharge curve
            if len(discharge_curve) > 0 and len(v_discharge_grid) > 0:
                discharge_interp = safe_interp(
                    v_discharge_grid,
                    discharge_curve[:, 1],  # voltage (x)
                    discharge_curve[:, 0],  # capacity (y)
                )
            else:
                discharge_interp = np.full_like(v_discharge_grid, 0.0)

            charge_dfs.append(charge_interp)
            discharge_dfs.append(discharge_interp)

        # Sum across interpolated curves
        summed_charge_capacity = np.sum(charge_dfs, axis=0) if charge_dfs else np.array([])
        summed_discharge_capacity = np.sum(discharge_dfs, axis=0) if discharge_dfs else np.array([])

        # Assemble final half-cell curve - always charge first, then discharge
        curves_to_stack = []

        # Always add charge curve first (if it exists) - sorted from lowest to highest specific capacity
        if len(summed_charge_capacity) > 0:
            charge_df = np.column_stack([summed_charge_capacity, v_charge_grid, np.ones_like(v_charge_grid)])
            # Sort charge curve by specific capacity (ascending - lowest to highest)
            charge_df = charge_df[np.argsort(charge_df[:, 0])]
            curves_to_stack.append(charge_df)

        # Then add discharge curve (if it exists) - sorted from highest to lowest specific capacity
        if len(summed_discharge_capacity) > 0:
            discharge_df = np.column_stack(
                [
                    summed_discharge_capacity,
                    v_discharge_grid,
                    -np.ones_like(v_discharge_grid),
                ]
            )
            # Sort discharge curve by specific capacity (descending - highest to lowest)
            discharge_df = discharge_df[np.argsort(discharge_df[:, 0])[::-1]]
            curves_to_stack.append(discharge_df)

        if curves_to_stack:
            self._specific_capacity_curve = np.vstack(curves_to_stack)
        else:
            # Fallback empty curve
            self._specific_capacity_curve = np.array([]).reshape(0, 3)

    def _handle_voltage_cutoff_compatibility(self) -> None:
        """
        Check if current voltage cutoff is compatible with new materials and adjust if necessary.
        Uses intersection of actual voltage ranges regardless of formulation type.
        """
        voltage_operation_windows = [material._voltage_operation_window for material in self._active_materials.keys()]

        lower_bounds = [min(w) for w in voltage_operation_windows]
        upper_bounds = [max(w) for w in voltage_operation_windows]

        min_voltage = max(lower_bounds)
        max_voltage = min(upper_bounds)

        valid_range = min_voltage <= max_voltage

        if not valid_range:
            material_ranges = [f"{mat.name}: {mat._voltage_operation_window}" for mat in self._active_materials.keys()]
            raise ValueError(f"The active materials have incompatible voltage operation windows.\n" f"Material ranges: {material_ranges}\n" f"No common voltage range exists for these materials.")

        self._voltage_operation_window = (min_voltage, max_voltage)

        # Check if we have an existing voltage cutoff
        if hasattr(self, "_voltage_cutoff") and self._voltage_cutoff is not None:
            if min_voltage <= self._voltage_cutoff <= max_voltage:
                for material in self._active_materials.keys():
                    material.voltage_cutoff = self._voltage_cutoff
            else:
                new_voltage = min_voltage if self._voltage_cutoff < min_voltage else max_voltage
                self._voltage_cutoff = new_voltage
                for material in self._active_materials.keys():
                    material.voltage_cutoff = self._voltage_cutoff
        else:
            if type(self) == CathodeFormulation:
                self._voltage_cutoff = max_voltage
            else:
                self._voltage_cutoff = min_voltage

            for material in self._active_materials.keys():
                material.voltage_cutoff = self._voltage_cutoff

    def _calculate_mass_breakdown(self) -> dict:

        # calculate mass breakdown
        self._mass_breakdown = {}
        for material in self._active_materials.keys():
            self._mass_breakdown[material.name] = material._mass
        for material in self._binders.keys():
            self._mass_breakdown[material.name] = material._mass
        for material in self._conductive_additives.keys():
            self._mass_breakdown[material.name] = material._mass

        return self._mass_breakdown
    
    def _calculate_cost_breakdown(self) -> dict:

        # calculate cost breakdown
        self._cost_breakdown = {}

        for material in self._active_materials.keys():
            self._cost_breakdown[material.name] = material._cost
        for material in self._binders.keys():
            self._cost_breakdown[material.name] = material._cost
        for material in self._conductive_additives.keys():
            self._cost_breakdown[material.name] = material._cost

        return self._cost_breakdown

    def _iter_all_materials(self):
        """Yield (material, fraction) pairs for all components."""
        yield from self._active_materials.items()
        yield from self._binders.items()
        yield from self._conductive_additives.items()

    def _set_component_weight(self, material_dict: dict, index: int, weight: float, component_type: str):
        """
        Helper method to set the weight of a component at a specific index.
        
        Parameters
        ----------
        material_dict : dict
            The dictionary of materials (e.g., _active_materials, _binders)
        index : int
            The 0-based index of the component to modify
        weight : float
            Weight percentage (0-100) for the component
        component_type : str
            Type name for error messages (e.g., "active material", "binder")
        """
        materials_list = list(material_dict.items())
        
        if len(materials_list) <= index:
            raise ValueError(
                f"Cannot set {component_type} {index + 1} weight: "
                f"formulation has {'no' if not materials_list else 'fewer than ' + str(index + 1)} {component_type}s"
            )
        
        self.validate_percentage(weight, f"{component_type.title()} {index + 1} weight")
        
        # Update the weight fraction
        target_material = materials_list[index][0]
        material_dict[target_material] = weight / 100

    def _replace_material_slot(
        self,
        collection_attr: str,
        index: int,
        new_material,
        slot_name: str,
        min_required: int = 0,
        prerequisite_label: str = "",
    ) -> None:
        """Replace material at a fixed index, preserving its weight and the dict order.

        If *index* is beyond the current length, appends *new_material* with a
        weight fraction of ``0.0`` (used for adding a new slot). If the
        collection currently has fewer than *min_required* items, raises
        ``ValueError`` with a message mentioning *prerequisite_label*.
        """
        coll = getattr(self, collection_attr)
        items = list(coll.items())

        if len(items) < min_required:
            raise ValueError(
                f"Cannot set {slot_name}: formulation has no {prerequisite_label}s. "
                f"Set {prerequisite_label}_1 first."
            )

        if index < len(items):
            _, weight = items[index]
            items[index] = (new_material, weight)
            setattr(self, collection_attr, dict(items))
        else:
            coll[new_material] = 0.0

    def _remove_material_slot(self, collection_attr: str, index: int) -> None:
        """Remove the material at *index* from *collection_attr* if present.

        Preserves the order of remaining items. Silently no-ops if the index
        is out of range (matches the existing public behaviour).
        """
        coll = getattr(self, collection_attr)
        items = list(coll.items())
        if index < len(items):
            items.pop(index)
            setattr(self, collection_attr, dict(items))

    def plot_specific_capacity_curve(self, add_materials: bool = False, **kwargs) -> go.Figure:
        """
        Plot the half-cell curve for the formulation.

        Parameters
        ----------
        add_materials : bool, optional
            Whether to add individual material curves. Default is False.
        **kwargs : dict
            Additional arguments to pass to the plotly figure layout.

        Returns
        -------
        go.Figure
            A plotly figure showing the half-cell curve.
        """
        figure = go.Figure()

        # Add main formulation curve as a single continuous line
        figure.add_trace(self.specific_capacity_curve_trace)

        # Add individual material curves if requested
        if add_materials:
            for material in self._active_materials.keys():
                figure.add_trace(material.specific_capacity_curve_trace)

        # Enhanced layout with better defaults
        figure.update_layout(
            title=kwargs.get("title", ""),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Specific Capacity (mAh/g)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
        )
    
        return figure

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """
        if not hasattr(self, '_cost'):
            return {}

        return round_dict_recursive(self._cost_breakdown, precision=None)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        if not hasattr(self, '_mass'):
            return {}

        return round_dict_recursive(self._mass_breakdown, precision=None, unit_conversion=KG_TO_G)

    @property
    def mass(self) -> Optional[float]:
        """Formulation mass in g, or None if not set."""
        if self._mass is None:
            return None
        else:
            return self._mass * KG_TO_G

    @property
    def volume(self) -> Optional[float]:
        """Formulation volume in cm³, or None if not set."""
        if self._volume is None:
            return None
        else:
            return self._volume * M_TO_CM**3

    @property
    def cost(self) -> Optional[float]:
        """Formulation cost in $, or None if not set."""
        if self._cost is None:
            return None
        else:
            return self._cost

    @property
    def specific_capacity_curve_trace(self) -> go.Scatter:
        """Plotly trace of the formulation's specific capacity curve."""

        if self._specific_capacity_curve is None:
            return None

        return go.Scatter(
            x=self.specific_capacity_curve["Specific Capacity (mAh/g)"],
            y=self.specific_capacity_curve["Voltage (V)"],
            name=self.name,
            line=dict(color=self._color, width=3, shape="spline"),
            mode="lines",
            hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
            customdata=self.specific_capacity_curve["Direction"],
            showlegend=True,
        )

    @property
    def name(self) -> Optional[str]:
        """Formatted display name (underscores replaced, title-cased)."""
        return self._name.replace("_", " ").title()

    @property
    def active_materials(self) -> Dict[_ActiveMaterial, float]:
        """Active materials mapped to their weight percentages (0-100)."""
        return {key: value * 100 for key, value in self._active_materials.items()}

    # ------------------------------------------------------------------
    # Indexed slot getters
    #
    # These expose the dict-based collections (_active_materials, _binders,
    # _conductive_additives) as numbered, positional properties. The names
    # are required by ``PropagationMixin`` — child objects store the slot
    # name in ``_parent_attr_name`` and parent setters are routed by name.
    # ------------------------------------------------------------------

    @property
    def active_material_1(self) -> Optional[_ActiveMaterial]:
        """First active material in the formulation, or ``None``."""
        return _slot_material(self._active_materials, 0)

    @property
    def active_material_2(self) -> Optional[_ActiveMaterial]:
        """Second active material in the formulation, or ``None``."""
        return _slot_material(self._active_materials, 1)

    @property
    def active_material_3(self) -> Optional[_ActiveMaterial]:
        """Third active material in the formulation, or ``None``."""
        return _slot_material(self._active_materials, 2)

    @property
    def active_material_1_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the first active material."""
        if not self._active_materials:
            raise ValueError("No active materials found in the formulation")
        return _slot_weight(self._active_materials, 0)

    @property
    def active_material_2_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the second active material, or ``None``."""
        return _slot_weight(self._active_materials, 1)

    @property
    def active_material_3_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the third active material, or ``None``."""
        return _slot_weight(self._active_materials, 2)

    @property
    def active_material_1_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the first active material."""
        return 0, 100

    @property
    def active_material_2_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the second active material."""
        return 0, 100

    @property
    def active_material_3_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the third active material."""
        return 0, 100

    @property
    def binder_1(self) -> Optional[Binder]:
        """First binder in the formulation (insertion order), or ``None``."""
        return _slot_material(self._binders, 0)

    @property
    def binder_2(self) -> Optional[Binder]:
        """Second binder in the formulation (insertion order), or ``None``."""
        return _slot_material(self._binders, 1)

    @property
    def binder_1_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the first binder, or ``None``."""
        return _slot_weight(self._binders, 0)

    @property
    def binder_2_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the second binder, or ``None``."""
        return _slot_weight(self._binders, 1)

    @property
    def binder_1_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the first binder."""
        return 0, 100

    @property
    def binder_2_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the second binder."""
        return 0, 100

    @property
    def conductive_additive_1(self) -> Optional[ConductiveAdditive]:
        """First conductive additive (insertion order), or ``None``."""
        return _slot_material(self._conductive_additives, 0)

    @property
    def conductive_additive_2(self) -> Optional[ConductiveAdditive]:
        """Second conductive additive (insertion order), or ``None``."""
        return _slot_material(self._conductive_additives, 1)

    @property
    def conductive_additive_1_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the first conductive additive, or ``None``."""
        return _slot_weight(self._conductive_additives, 0)

    @property
    def conductive_additive_2_weight(self) -> Optional[float]:
        """Weight percentage (0-100) of the second conductive additive, or ``None``."""
        return _slot_weight(self._conductive_additives, 1)

    @property
    def conductive_additive_1_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the first conductive additive."""
        return 0, 100

    @property
    def conductive_additive_2_weight_range(self) -> tuple:
        """Allowed (min, max) percentage range for the second conductive additive."""
        return 0, 100

    @property
    def binders(self) -> Dict[Binder, float]:
        return {key: value * 100 for key, value in self._binders.items()} if self._binders != {} else {}

    @property
    def conductive_additives(self) -> Dict[ConductiveAdditive, float]:
        return {key: value * 100 for key, value in self._conductive_additives.items()} if self._conductive_additives != {} else {}

    @property
    def voltage_cutoff(self) -> float:
        """
        Get the voltage cutoff for this formulation.

        :return: float: voltage cutoff of the half cell curves
        """
        return self._voltage_cutoff

    @property
    def voltage_cutoff_range(self) -> tuple:
        return (min(self.voltage_operation_window), max(self.voltage_operation_window))

    @property
    def voltage_cutoff_hard_range(self) -> tuple:
        return self.voltage_cutoff_range

    @property
    def density(self) -> float:
        return self._density * KG_TO_G / (M_TO_CM**3)

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def specific_volume(self) -> float:
        """
        Get the theoretical specific volume of the formulation.

        :return: Theoretical specific volume in cm³/g.
        """
        return self._specific_volume * (M_TO_CM**3) / KG_TO_G

    @property
    def voltage_operation_window(self) -> tuple:
        """
        Get the valid voltage range for the half cell curves.

        :return: tuple: (minimum voltage, maximum voltage)
        """
        min_voltage = self._voltage_operation_window[0]
        max_voltage = self._voltage_operation_window[1]

        # Determine which value is actually min/max since order can vary
        actual_min = min(min_voltage, max_voltage)
        actual_max = max(min_voltage, max_voltage)

        # Round the bounds conservatively (inward to stay within window)
        rounded_min = np.ceil(actual_min * 1000) / 1000  # Round up (more conservative for min)
        rounded_max = np.floor(actual_max * 1000) / 1000  # Round down (more conservative for max)

        # Return in original order
        if min_voltage <= max_voltage:
            return (rounded_min, rounded_max)
        else:
            return (rounded_max, rounded_min)

    @property
    def specific_capacity_curve(self) -> pd.DataFrame:
        """Get the specific capacity curve with proper units and formatting."""

        if self._specific_capacity_curve is None:
            return None

        # Pre-compute unit conversion factor
        capacity_conversion = S_TO_H * A_TO_mA / KG_TO_G

        # original curve
        curve = self._specific_capacity_curve.copy()
        
        # compute the columns
        specific_capacity = curve[:, 0] * capacity_conversion
        voltage = curve[:, 1]
        direction = np.where(curve[:, 2] == 1, "charge", "discharge")

        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Specific Capacity (mAh/g)": specific_capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def capacity_curve(self) -> pd.DataFrame:
        """Get the absolute capacity curve (specific capacity * mass) with proper units and formatting."""

        if getattr(self, "_capacity_curve", None) is None:
            return None

        # Pre-compute unit conversion factor (A·s → mAh)
        capacity_conversion = S_TO_H * A_TO_mA

        curve = self._capacity_curve.copy()
        
        capacity = curve[:, 0] * capacity_conversion
        voltage = curve[:, 1]
        direction = np.where(curve[:, 2] == 1, "charge", "discharge")

        return pd.DataFrame({
            "Capacity (mAh)": capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def color(self) -> str:
        return self._color

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Get the properties of the electrode.

        :return: Dictionary containing the properties of the electrode.
        """
        return {
            "Specific Cost": f"$ {self.specific_cost} /kg",
            "Density": f"{self.density} g/cm³",
            "Specific Volume": f"{self.specific_volume} cm³/g",
        }

    @mass.setter
    @calculate_bulk_properties
    def mass(self, mass: Optional[float] = None):

        # validate input
        self.validate_positive_float(mass, "Mass")

        # calculate self properties
        self._mass = mass * G_TO_KG
        self._volume = self._mass / self._density
        self._cost = self._mass * self._specific_cost

        # assign masses to materials
        for material, fraction in self._iter_all_materials():
            material.mass = self._mass * KG_TO_G * fraction
            
    @volume.setter
    @calculate_bulk_properties
    def volume(self, volume: Optional[float] = None):

        # validate input
        self.validate_positive_float(volume, "Volume")

        # calculate self properties
        self._volume = volume * (CM_TO_M**3)
        self._mass = self._volume * self._density
        self._cost = self._mass * self._specific_cost

        # assign masses to materials
        for material, fraction in self._iter_all_materials():
            material.mass = self._mass * KG_TO_G * fraction

    @name.setter
    def name(self, name: str):
        self.validate_string(name, "Name")
        self._name = name

    @conductive_additives.setter
    @calculate_all_properties
    def conductive_additives(self, conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None):

        # validate input
        self.validate_type(conductive_additives, dict, "Conductive additives")

        # remove cases where either the key or value is None
        conductive_additives = {k: v for k, v in conductive_additives.items() if k is not None and v is not None}

        # validate types
        if conductive_additives != {}:
            for key, value in conductive_additives.items():
                self.validate_type(key, ConductiveAdditive, "Conductive additive")
                self.validate_percentage(value, f"Mass fraction for {key.name}")

        # Clear parent references on old materials (only if not in new dict)
        if hasattr(self, '_conductive_additives') and self._conductive_additives:
            new_keys = set(conductive_additives.keys())
            for material in self._conductive_additives.keys():
                if material not in new_keys:
                    material._set_parent(None)

        self._conductive_additives = {key: value / 100 for key, value in conductive_additives.items() if key is not None}

        # Set parent references on new materials with indexed attr names for propagation
        for i, material in enumerate(self._conductive_additives.keys(), 1):
            material._set_parent(self, f"conductive_additive_{i}")

    @binders.setter
    @calculate_all_properties
    def binders(self, binders: Optional[Dict[Binder, float]] = None):

        # validate input
        self.validate_type(binders, dict, "Binders")

        # remove cases where either the key or value is None
        binders = {k: v for k, v in binders.items() if k is not None and v is not None}

        # validate types
        if binders != {}:
            for key, value in binders.items():
                self.validate_type(key, Binder, "Binder")
                self.validate_percentage(value, f"Mass fraction for {key.name}")

        # Clear parent references on old materials (only if not in new dict)
        if hasattr(self, '_binders') and self._binders:
            new_keys = set(binders.keys())
            for material in self._binders.keys():
                if material not in new_keys:
                    material._set_parent(None)

        # assign
        self._binders = {key: value / 100 for key, value in binders.items()}

        # Set parent references on new materials with indexed attr names for propagation
        for i, material in enumerate(self._binders.keys(), 1):
            material._set_parent(self, f"binder_{i}")

    @active_materials.setter
    @calculate_all_properties
    def active_materials(self, active_materials: Dict[_ActiveMaterial, float]):
        """
        Set active materials and validate voltage compatibility with current voltage cutoff.
        """
        # Check if active_materials is empty
        if len(active_materials) == 0:
            raise ValueError("You must include at least one active material in the formulation.")
        
        # remove cases where either the key or value is None
        active_materials = {k: v for k, v in active_materials.items() if k is not None and v is not None}

        # Check the types and values of the active materials
        for key, value in active_materials.items():
            self.validate_type(key, _ActiveMaterial, "Active material")
            self.validate_percentage(value, f"Mass fraction for {key.name}")

        # Clear parent references on old materials (only if not in new dict)
        if hasattr(self, '_active_materials') and self._active_materials:
            new_keys = set(active_materials.keys())
            for material in self._active_materials.keys():
                if material not in new_keys:
                    material._set_parent(None)

        # Store the new active materials
        self._active_materials = {key: value / 100 for key, value in active_materials.items()}

        # Set parent references on new materials with indexed attr names for propagation
        for i, material in enumerate(self._active_materials.keys(), 1):
            material._set_parent(self, f"active_material_{i}")

        # Reset auto-calculated cutoff so it is recalculated for the new material set
        if not self._user_set_voltage_cutoff:
            self._voltage_cutoff = None

        # Handle voltage cutoff compatibility with new materials
        self._handle_voltage_cutoff_compatibility()

    def _set_active_material_slot(self, index: int, new_material: Optional[_ActiveMaterial], slot_name: str) -> None:
        """Shared implementation for the indexed ``active_material_N`` setters.

        Handles parent ref management, replacement, appending (for missing
        slots), removal (when ``new_material`` is ``None``), and voltage
        cutoff compatibility recalculation.

        Raises ``ValueError`` if removing the slot would leave the formulation
        with zero active materials (i.e. setting ``active_material_1`` to
        ``None`` when it is the only active material). A formulation must
        always retain at least one active material.
        """
        if new_material is None and index < len(self._active_materials) and len(self._active_materials) == 1:
            raise ValueError(
                "Cannot remove the last active material: a formulation must "
                "contain at least one active material."
            )

        old_material = _slot_material(self._active_materials, index)
        if old_material is not None and old_material is not new_material:
            old_material._set_parent(None)

        if new_material is None:
            self._remove_material_slot("_active_materials", index)
        else:
            self.validate_type(new_material, _ActiveMaterial, "Active material")
            self._replace_material_slot("_active_materials", index, new_material, slot_name)
            new_material._set_parent(self, slot_name)

        if not self._user_set_voltage_cutoff:
            self._voltage_cutoff = None
        self._handle_voltage_cutoff_compatibility()

    @active_material_1.setter
    @calculate_all_properties
    def active_material_1(self, new_material: Optional[_ActiveMaterial]):
        """Set the first active material. Passing ``None`` removes the slot.

        If the slot already exists its weight fraction is preserved; otherwise
        the new material is appended with a weight of ``0``.
        """
        self._set_active_material_slot(0, new_material, "active_material_1")

    @active_material_2.setter
    @calculate_all_properties
    def active_material_2(self, new_material: Optional[_ActiveMaterial]):
        """Set the second active material. Passing ``None`` removes the slot."""
        self._set_active_material_slot(1, new_material, "active_material_2")

    @active_material_3.setter
    @calculate_all_properties
    def active_material_3(self, new_material: Optional[_ActiveMaterial]):
        """Set the third active material. Passing ``None`` removes the slot."""
        self._set_active_material_slot(2, new_material, "active_material_3")

    @active_material_1_weight.setter
    @calculate_all_properties
    def active_material_1_weight(self, weight: float):
        """
        Set the weight percentage of the first active material.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the first active material
        """
        if not self._active_materials:
            raise ValueError("No active materials found in the formulation")
        
        self._set_component_weight(self._active_materials, 0, weight, "active material")

    @active_material_2_weight.setter
    @calculate_all_properties
    def active_material_2_weight(self, weight: float):
        """
        Set the weight percentage of the second active material.
        If there's no second material, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the second active material
        """
        self._set_component_weight(self._active_materials, 1, weight, "active material")

    @active_material_3_weight.setter
    @calculate_all_properties
    def active_material_3_weight(self, weight: float):
        """
        Set the weight percentage of the third active material.
        If there's no third material, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the third active material
        """
        self._set_component_weight(self._active_materials, 2, weight, "active material")

    @binder_1.setter
    @calculate_all_properties
    def binder_1(self, material: Optional[Binder]):
        """Set the first binder. Passing ``None`` removes the slot.

        If a binder is already at index 0 it is replaced while preserving its
        weight. If no binders exist the material is appended with weight ``0``.
        """
        old_material = self.binder_1
        if old_material is not None and old_material is not material:
            old_material._set_parent(None)

        if material is None:
            self._remove_material_slot("_binders", 0)
            return

        self.validate_type(material, Binder, "Binder material")
        self._replace_material_slot("_binders", 0, material, "binder_1")
        material._set_parent(self, "binder_1")

    @binder_2.setter
    @calculate_all_properties
    def binder_2(self, material: Optional[Binder]):
        """Set the second binder. Passing ``None`` removes the slot.

        Raises ``ValueError`` if no binders exist yet (``binder_1`` must be
        set first).
        """
        old_binder = self.binder_2
        if old_binder is not None and old_binder is not material:
            old_binder._set_parent(None)

        if material is None:
            self._remove_material_slot("_binders", 1)
            return

        self.validate_type(material, Binder, "Binder material")
        self._replace_material_slot(
            "_binders", 1, material, "binder_2",
            min_required=1, prerequisite_label="binder",
        )
        material._set_parent(self, "binder_2")

    @binder_1_weight.setter
    @calculate_all_properties
    def binder_1_weight(self, weight: float):
        """
        Set the weight percentage of the first binder.
        If there's no first binder, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the first binder
        """
        self._set_component_weight(self._binders, 0, weight, "binder")

    @binder_2_weight.setter
    @calculate_all_properties
    def binder_2_weight(self, weight: float):
        """
        Set the weight percentage of the second binder.
        If there's no second binder, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the second binder
        """
        self._set_component_weight(self._binders, 1, weight, "binder")

    @conductive_additive_1.setter
    @calculate_all_properties
    def conductive_additive_1(self, material: Optional[ConductiveAdditive]):
        """Set the first conductive additive. Passing ``None`` removes the slot.

        If an additive already occupies index 0 it is replaced while its
        weight is preserved; otherwise the material is appended with weight
        ``0``.
        """
        old_material = self.conductive_additive_1
        if old_material is not None and old_material is not material:
            old_material._set_parent(None)

        if material is None:
            self._remove_material_slot("_conductive_additives", 0)
            return

        self.validate_type(material, ConductiveAdditive, "Conductive additive material")
        self._replace_material_slot(
            "_conductive_additives", 0, material, "conductive_additive_1"
        )
        material._set_parent(self, "conductive_additive_1")

    @conductive_additive_2.setter
    @calculate_all_properties
    def conductive_additive_2(self, material: Optional[ConductiveAdditive]):
        """Set the second conductive additive. Passing ``None`` removes the slot.

        Raises ``ValueError`` when assigning a non-``None`` material while no
        additives exist yet (``conductive_additive_1`` must be set first).
        """
        old_additive = self.conductive_additive_2
        if old_additive is not None and old_additive is not material:
            old_additive._set_parent(None)

        if material is None:
            self._remove_material_slot("_conductive_additives", 1)
            return

        self.validate_type(material, ConductiveAdditive, "Conductive additive material")
        self._replace_material_slot(
            "_conductive_additives", 1, material, "conductive_additive_2",
            min_required=1, prerequisite_label="conductive additive",
        )
        material._set_parent(self, "conductive_additive_2")

    @conductive_additive_1_weight.setter
    @calculate_all_properties
    def conductive_additive_1_weight(self, weight: float):
        """
        Set the weight percentage of the first conductive additive.
        If there's no first conductive additive, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the first conductive additive
        """
        self._set_component_weight(self._conductive_additives, 0, weight, "conductive additive")

    @conductive_additive_2_weight.setter
    @calculate_all_properties
    def conductive_additive_2_weight(self, weight: float):
        """
        Set the weight percentage of the second conductive additive.
        If there's no second conductive additive, this will raise an error.
        
        Parameters
        ----------
        weight : float
            Weight percentage (0-100) for the second conductive additive
        """
        self._set_component_weight(self._conductive_additives, 1, weight, "conductive additive")

    @voltage_cutoff.setter
    @calculate_capacity_curve
    @calculate_specific_capacity_curve
    def voltage_cutoff(self, voltage: float):
        """
        Set the voltage cutoff for the half cell curves with validation.

        :param voltage: float: voltage cutoff for the half cell curves
        """
        # Track whether the user explicitly set a voltage cutoff
        self._user_set_voltage_cutoff = voltage is not None

        # First ensure we have a voltage operation window
        self._get_voltage_operation_window()

        if voltage is None:
            if type(self) == CathodeFormulation:
                voltage = max(self._voltage_operation_window)
            else:
                voltage = min(self._voltage_operation_window)

        self.validate_number(voltage, "Voltage cutoff")

        # Store the requested voltage cutoff
        self._voltage_cutoff = voltage

        # Validate and adjust if necessary
        self._validate_and_set_voltage_cutoff()


class CathodeFormulation(_ElectrodeFormulation):
    """
    Represents a cathode formulation in a battery.
    Inherits from _ElectrodeFormulation.
    """

    def __init__(
        self,
        active_materials: Dict[_ActiveMaterial, float],
        binders: Optional[Dict[Binder, float]] = {},
        conductive_additives: Optional[Dict[ConductiveAdditive, float]] = {},
        voltage_cutoff: Optional[float] = None,
        name: Optional[str] = "Cathode Formulation",
    ):
        """
        Initialize a cathode formulation with active materials, binders, and conductive additives.

        Parameters
        ----------
        active_materials : Dict[_ActiveMaterial, float]
            Dictionary of active materials and their mass fractions in percent.
        binders : Optional[Dict[Binder, float]]
            Dictionary of binders and their mass fractions in percent.
        conductive_additives : Optional[Dict[ConductiveAdditive, float]]
            Dictionary of conductive additives and their mass fractions in percent.
        voltage_cutoff : Optional[float]
            The maximum voltage for the half-cell curves. If not provided, it will be set to
            the maximum voltage from the active materials' voltage cutoff range.
        name : Optional[str]
            Name of the cathode formulation. Defaults to 'Cathode Formulation'.
        """
        super().__init__(
            active_materials=active_materials,
            binders=binders,
            conductive_additives=conductive_additives,
            voltage_cutoff=voltage_cutoff,
            name=name,
        )

        self._update_properties = True


class AnodeFormulation(_ElectrodeFormulation):
    """
    Represents an anode formulation in a battery.
    Inherits from _ElectrodeFormulation.
    """

    def __init__(
        self,
        active_materials: Dict[_ActiveMaterial, float],
        binders: Optional[Dict[Binder, float]] = {},
        conductive_additives: Optional[Dict[ConductiveAdditive, float]] = {},
        voltage_cutoff: Optional[float] = None,
        name: Optional[str] = "Anode Formulation",
    ):
        """
        Initialize an anode formulation with active materials, binders, and conductive additives.

        Parameters
        ----------
        active_materials : Dict[_ActiveMaterial, float]
            Dictionary of active materials and their mass fractions in percent.
        binders : Optional[Dict[Binder, float]]
            Dictionary of binders and their mass fractions in percent.
        conductive_additives : Optional[Dict[ConductiveAdditive, float]]
            Dictionary of conductive additives and their mass fractions in percent.
        voltage_cutoff : Optional[float]
            The voltage cutoff for the half-cell curves. If not provided, it will be set to
            the minimum voltage from the active materials' voltage cutoff range.
        name : Optional[str]
            Name of the anode formulation. Defaults to 'Anode Formulation'.
        """
        super().__init__(
            active_materials=active_materials,
            binders=binders,
            conductive_additives=conductive_additives,
            voltage_cutoff=voltage_cutoff,
            name=name,
        )

        self._update_properties = True
