from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Constants.Units import *

from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_opencell_design.Materials.ActiveMaterials import _ActiveMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive
from steer_opencell_design.Materials.CapacityCurveUtils import calculate_specific_capacity_curve, calculate_capacity_curve

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, Any
import warnings
from collections import Counter


class _ElectrodeFormulation(
    ValidationMixin, 
    DunderMixin,
    PlotterMixin,
    SerializerMixin,
    ):

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

    def _calculate_all_properties(self) -> None:
        """
        Retrieve the properties of the electrode formulation.
        This method is called to ensure that all properties are calculated and available.
        """
        self._calculate_material_properties()
        self._check_formulation()

        self._get_voltage_operation_window()
        self._calculate_specific_capacity_curve()

        if hasattr(self, '_mass') and self._mass is not None:
            self._calculate_bulk_properties()

    def _calculate_material_properties(self) -> None:
        self._calculate_density()
        self._calculate_specific_cost()
        self._calculate_color()

    def _calculate_bulk_properties(self) -> None:
        self._calculate_breakdowns()
        self._calculate_capacity_curve()

    def _calculate_capacity_curve(self) -> np.ndarray:

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
        Note: Voltage cutoff compatibility is now handled in active_materials.setter
        """
        if not hasattr(self, "_voltage_operation_window"):
            # If voltage operation window hasn't been set yet (during initialization)
            voltage_operation_windows = [material._voltage_operation_window for material in self._active_materials.keys()]
            starts, middles, ends = zip(*voltage_operation_windows)

            if type(self) == CathodeFormulation:
                common_start = max(starts)
                common_end = min(ends)
            else:  # AnodeFormulation
                common_start = min(starts)
                common_end = max(ends)

            self._voltage_operation_window = (common_start, common_end)

        return self._voltage_operation_window

    def _validate_and_set_voltage_cutoff(self) -> None:
        """
        Validate formulation voltage cutoff against common voltage range and set material cutoffs.
        """
        common_start, common_end = self._voltage_operation_window

        # Determine the valid range boundaries based on formulation type
        if type(self) == CathodeFormulation:
            min_voltage = common_start
            max_voltage = common_end
        else:  # AnodeFormulation
            min_voltage = common_end  # For anodes, end is actually lower
            max_voltage = common_start  # For anodes, start is actually higher

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

        # Set the voltage cutoff for each active material
        for material in self._active_materials.keys():
            material.voltage_cutoff = self._voltage_cutoff

    def _check_formulation(self) -> None:
        """
        Validate the electrode formulation to ensure it meets the required criteria.
        """
        total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())

        if not (0.99 <= total_fraction <= 1.01):
            warnings.warn(
                f"The total mass percentages of the formulation should sum to 100%. Current sum: {round(total_fraction * 100, 1)}%",
                UserWarning,
            )

        self._check_unique_names(self._active_materials, "active materials")
        self._check_unique_names(self._binders, "binders")
        self._check_unique_names(self._conductive_additives, "conductive additives")

    def _check_unique_names(self, components: Dict, component_type: str) -> None:

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
        Calculate the half-cell curve for the cathode formulation based on the active materials
        and their weight fractions, treating charge and discharge curves separately.

        Parameters
        ----------
        voltage : Optional[float]
            The maximum voltage for the half-cell curve. If not provided, it will be set to
            the maximum voltage from the active materials' voltage cutoff range.
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

            return np.linspace(v_start, v_end, num=100)

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
        """
        # First, calculate the new voltage operation window
        voltage_operation_windows = [material._voltage_operation_window for material in self._active_materials.keys()]
        starts, middles, ends = zip(*voltage_operation_windows)

        # Determine the common voltage operation window
        if type(self) == CathodeFormulation:
            common_start = max(starts)
            common_end = min(ends)
            valid_range = common_start <= common_end
        else:  # AnodeFormulation
            common_start = min(starts)
            common_end = max(ends)
            valid_range = common_start >= common_end

        # Check if there's a valid common range
        if not valid_range:
            material_ranges = [f"{mat.name}: {mat._voltage_operation_window}" for mat in self._active_materials.keys()]
            raise ValueError(f"The active materials have incompatible voltage operation windows.\n" f"Material ranges: {material_ranges}\n" f"No common voltage range exists for these materials.")

        # Store the new voltage operation window
        self._voltage_operation_window = (common_start, common_end)

        # Determine the valid range boundaries based on formulation type
        if type(self) == CathodeFormulation:
            min_voltage = common_start
            max_voltage = common_end
        else:  # AnodeFormulation
            min_voltage = common_end  # For anodes, end is actually lower
            max_voltage = common_start  # For anodes, start is actually higher

        # Check if we have an existing voltage cutoff
        if hasattr(self, "_voltage_cutoff") and self._voltage_cutoff is not None:
            # Check if current voltage cutoff is compatible with new materials
            if min_voltage <= self._voltage_cutoff <= max_voltage:
                # Current voltage cutoff is compatible - keep it and set it to materials
                for material in self._active_materials.keys():
                    material.voltage_cutoff = self._voltage_cutoff
            else:
                # Current voltage cutoff is incompatible - adjust to nearest boundary
                if self._voltage_cutoff < min_voltage:
                    new_voltage = min_voltage
                else:  # self._voltage_cutoff > max_voltage
                    new_voltage = max_voltage

                # Update formulation voltage cutoff and set to materials
                self._voltage_cutoff = new_voltage
                for material in self._active_materials.keys():
                    material.voltage_cutoff = self._voltage_cutoff
        else:
            # No existing voltage cutoff - set to appropriate boundary
            if type(self) == CathodeFormulation:
                self._voltage_cutoff = max_voltage  # Use upper bound for cathodes
            else:
                self._voltage_cutoff = min_voltage  # Use lower bound for anodes

            # Set voltage cutoff to all materials
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

        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj, 2)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        if not hasattr(self, '_mass'):
            return {}

        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj * KG_TO_G, 2)

        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def mass(self) -> Optional[float]:
        if self._mass is None:
            return None
        else:
            return np.round(self._mass * KG_TO_G, 2)
        
    @property
    def volume(self) -> Optional[float]:
        if self._volume is None:
            return None
        else:
            return np.round(self._volume * M_TO_CM**3, 2)

    @property
    def cost(self) -> Optional[float]:
        if self._cost is None:
            return None
        else:
            return np.round(self._cost, 2)

    @property
    def specific_capacity_curve_trace(self) -> go.Scatter:

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
        return self._name.replace("_", " ").title()

    @property
    def active_materials(self) -> Dict[_ActiveMaterial, float]:
        return {key: value * 100 for key, value in self._active_materials.items()}

    @property
    def active_material_1(self) -> _ActiveMaterial:
        """
        Get the first active material in the formulation.
        
        Returns
        -------
        _ActiveMaterial
            The first active material in the formulation
        """
        materials_list = list(self._active_materials.keys())
        return materials_list[0] if len(materials_list) >= 1 else None

    @property
    def active_material_2(self) -> _ActiveMaterial:
        """
        Get the second active material in the formulation.
        
        Returns
        -------
        _ActiveMaterial or None
            The second active material in the formulation, or None if it doesn't exist
        """
        materials_list = list(self._active_materials.keys())
        return materials_list[1] if len(materials_list) >= 2 else None

    @property
    def active_material_3(self) -> _ActiveMaterial:
        """
        Get the third active material in the formulation.
        
        Returns
        -------
        _ActiveMaterial or None
            The third active material in the formulation, or None if it doesn't exist
        """
        materials_list = list(self._active_materials.keys())
        return materials_list[2] if len(materials_list) >= 3 else None

    @property
    def active_material_1_weight(self) -> float:
        """
        Get the weight percentage of the first active material.
        
        Returns
        -------
        float
            Weight percentage of the first active material
        """
        if not self._active_materials:
            raise ValueError("No active materials found in the formulation")
        first_material = next(iter(self._active_materials.keys()))
        return self._active_materials[first_material] * 100

    @property
    def active_material_2_weight(self) -> float:
        """
        Get the weight percentage of the second active material.
        
        Returns
        -------
        float or None
            Weight percentage of the second active material, or None if it doesn't exist
        """
        materials_list = list(self._active_materials.items())
        return materials_list[1][1] * 100 if len(materials_list) >= 2 else None

    @property
    def active_material_3_weight(self) -> float:
        """
        Get the weight percentage of the third active material.
        
        Returns
        -------
        float or None
            Weight percentage of the third active material, or None if it doesn't exist
        """
        materials_list = list(self._active_materials.items())
        return materials_list[2][1] * 100 if len(materials_list) >= 3 else None

    @property
    def active_material_1_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the first active material.
        
        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the first active material, or None if it doesn't exist
        """
        return 0, 100
    
    @property
    def active_material_2_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the second active material.
        
        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the second active material, or None if it doesn't exist
        """
        return 0, 100
    
    @property
    def active_material_3_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the third active material.
        
        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the third active material, or None if it doesn't exist
        """
        return 0, 100

    @property
    def binder_1(self) -> Binder:
        """
        Get the first binder in the formulation based on insertion order.
        
        Returns
        -------
        Binder or None
            The first binder material, or None if no binders exist
        """
        binders_list = list(self._binders.items())
        return binders_list[0][0] if len(binders_list) >= 1 else None

    @property
    def binder_2(self) -> Binder:
        """
        Get the second binder in the formulation based on insertion order.
        
        Returns
        -------
        Binder or None
            The second binder material, or None if it doesn't exist
        """
        binders_list = list(self._binders.items())
        return binders_list[1][0] if len(binders_list) >= 2 else None

    @property
    def binder_1_weight(self) -> float:
        """
        Get the weight percentage of the first binder.
        
        Returns
        -------
        float or None
            Weight percentage of the first binder, or None if it doesn't exist
        """
        binders_list = list(self._binders.items())
        return binders_list[0][1] * 100 if len(binders_list) >= 1 else None

    @property
    def binder_2_weight(self) -> float:
        """
        Get the weight percentage of the second binder.
        
        Returns
        -------
        float or None
            Weight percentage of the second binder, or None if it doesn't exist
        """
        binders_list = list(self._binders.items())
        return binders_list[1][1] * 100 if len(binders_list) >= 2 else None

    @property
    def binder_1_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the first binder.
        
        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the first binder, or None if it doesn't exist
        """
        return 0, 100

    @property
    def binder_2_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the second binder.

        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the second binder, or None if it doesn't exist
        """
        return 0, 100

    @property
    def conductive_additive_1(self) -> ConductiveAdditive:
        """
        Get the first conductive additive in the formulation based on insertion order.
        
        Returns
        -------
        ConductiveAdditive or None
            The first conductive additive material, or None if no conductive additives exist
        """
        additives_list = list(self._conductive_additives.items())
        return additives_list[0][0] if len(additives_list) >= 1 else None

    @property
    def conductive_additive_2(self) -> ConductiveAdditive:
        """
        Get the second conductive additive in the formulation based on insertion order.
        
        Returns
        -------
        ConductiveAdditive or None
            The second conductive additive material, or None if it doesn't exist
        """
        additives_list = list(self._conductive_additives.items())
        return additives_list[1][0] if len(additives_list) >= 2 else None

    @property
    def conductive_additive_1_weight(self) -> float:
        """
        Get the weight percentage of the first conductive additive.
        
        Returns
        -------
        float or None
            Weight percentage of the first conductive additive, or None if it doesn't exist
        """
        additives_list = list(self._conductive_additives.items())
        return additives_list[0][1] * 100 if len(additives_list) >= 1 else None

    @property
    def conductive_additive_2_weight(self) -> float:
        """
        Get the weight percentage of the second conductive additive.
        
        Returns
        -------
        float or None
            Weight percentage of the second conductive additive, or None if it doesn't exist
        """
        additives_list = list(self._conductive_additives.items())
        return additives_list[1][1] * 100 if len(additives_list) >= 2 else None

    @property
    def conductive_additive_1_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the first conductive additive.
        
        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the first conductive additive, or None if it doesn't exist
        """
        return 0, 100

    @property
    def conductive_additive_2_weight_range(self) -> tuple:
        """
        Get the weight percentage range of the second conductive additive.

        Returns
        -------
        tuple or None
            Weight percentage range (min, max) of the second conductive additive, or None if it doesn't exist
        """
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
        Get the maximum voltage of the half cell curves.

        :return: float: maximum voltage of the half cell curves
        """
        return np.round(self._voltage_cutoff, 3)

    @property
    def voltage_cutoff_range(self) -> tuple:
        return (min(self.voltage_operation_window), max(self.voltage_operation_window))

    @property
    def voltage_cutoff_hard_range(self) -> tuple:
        return self.voltage_cutoff_range

    @property
    def density(self) -> float:
        return np.round(self._density * KG_TO_G / (M_TO_CM**3), 2)

    @property
    def specific_cost(self) -> float:
        return np.round(self._specific_cost, 2)

    @property
    def specific_volume(self) -> float:
        """
        Get the theoretical specific volume of the formulation.

        :return: Theoretical specific volume in cm³/g.
        """
        return np.round(self._specific_volume * (M_TO_CM**3) / KG_TO_G, 2)

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
        specific_capacity = np.round(curve[:, 0] * capacity_conversion, 4)
        voltage = np.round(curve[:, 1], 4)
        direction = np.where(curve[:, 2] == 1, "charge", "discharge")

        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Specific Capacity (mAh/g)": specific_capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def capacity_curve(self) -> pd.DataFrame:
        """Get the capacity curve with proper units and formatting."""

        if self._specific_capacity_curve is None:
            return None

        # Pre-compute unit conversion factor
        capacity_conversion = S_TO_H * A_TO_mA

        # original curve
        curve = self._specific_capacity_curve.copy()
        
        # compute the columns
        capacity = np.round(curve[:, 0] * capacity_conversion, 4)
        voltage = np.round(curve[:, 1], 4)
        direction = np.where(curve[:, 2] == 1, "charge", "discharge")

        # Create DataFrame with converted values directly
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
            "Specific Cost": f"$ {self.specific_cost} /g",
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

        self._conductive_additives = {key: value / 100 for key, value in conductive_additives.items() if key is not None}

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

        # assign
        self._binders = {key: value / 100 for key, value in binders.items()}

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

        # Store the new active materials
        self._active_materials = {key: value / 100 for key, value in active_materials.items()}

        # Handle voltage cutoff compatibility with new materials
        self._handle_voltage_cutoff_compatibility()

    @active_material_1.setter
    @calculate_all_properties
    def active_material_1(self, new_material: _ActiveMaterial):
        """
        Set the first active material in the formulation, keeping its mass fraction.
        If None is passed, removes the first active material from the formulation.
        
        Parameters
        ----------
        new_material : _ActiveMaterial or None
            The new active material to replace the first one, or None to remove it
        """
        if new_material is None:
            # Remove the first active material
            materials_list = list(self._active_materials.items())
            if len(materials_list) > 0:
                # Create new dictionary without the first material
                new_active_materials = {}
                for material, fraction in materials_list[1:]:
                    new_active_materials[material] = fraction
                self._active_materials = new_active_materials
            return
            
        # Validate the input
        self.validate_type(new_material, _ActiveMaterial, "Active material")
        
        # Get the materials and mass fractions as lists
        materials_list = list(self._active_materials.keys())
        weight_fractions_list = list(self._active_materials.values())

        # Set the first material to the new material, keeping its mass fraction
        materials_list[0] = new_material

        # Reconstruct the active materials dictionary with the updated first material
        new_active_materials = {k: v for (k, v) in zip(materials_list, weight_fractions_list)}

        # Update the active materials
        self._active_materials = new_active_materials
        
        # Handle voltage cutoff compatibility with new materials
        self._handle_voltage_cutoff_compatibility()

    @active_material_2.setter
    @calculate_all_properties
    def active_material_2(self, new_material: _ActiveMaterial):
        """
        Set the second active material in the formulation.
        If there's already a second material, it keeps its mass fraction.
        If there's no second material, it adds one with mass fraction of 0.
        If None is passed, removes the second active material from the formulation.
        
        Parameters
        ----------
        new_material : _ActiveMaterial or None
            The new active material to set as the second one, or None to remove it
        """
        if new_material is None:
            # Remove the second active material
            materials_list = list(self._active_materials.items())
            if len(materials_list) >= 2:
                # Create new dictionary without the second material
                new_active_materials = {}
                # Keep first material
                new_active_materials[materials_list[0][0]] = materials_list[0][1]
                # Keep materials from third position onwards
                for material, fraction in materials_list[2:]:
                    new_active_materials[material] = fraction
                self._active_materials = new_active_materials
            return
            
        # Validate the input
        self.validate_type(new_material, _ActiveMaterial, "Active material")
        
        # Get the materials and mass fractions as lists
        materials_list = list(self._active_materials.keys())
        weight_fractions_list = list(self._active_materials.values())

        if len(materials_list) < 2:
            self._active_materials[new_material] = 0.0
        else:
            materials_list[1] = new_material
            new_active_materials = {k: v for (k, v) in zip(materials_list, weight_fractions_list)}
            self._active_materials = new_active_materials
            
        # Handle voltage cutoff compatibility with new materials
        self._handle_voltage_cutoff_compatibility()

    @active_material_3.setter
    @calculate_all_properties
    def active_material_3(self, new_material: _ActiveMaterial):
        """
        Set the third active material in the formulation.
        If there's already a third material, it keeps its mass fraction.
        If there's no third material, it adds one with mass fraction of 0.
        If None is passed, removes the third active material from the formulation.
        
        Parameters
        ----------
        new_material : _ActiveMaterial or None
            The new active material to set as the third one, or None to remove it
        """
        if new_material is None:
            # Remove the third active material
            materials_list = list(self._active_materials.items())
            if len(materials_list) >= 3:
                # Create new dictionary without the third material
                new_active_materials = {}
                # Keep first two materials
                new_active_materials[materials_list[0][0]] = materials_list[0][1]
                new_active_materials[materials_list[1][0]] = materials_list[1][1]
                # Keep materials from fourth position onwards
                for material, fraction in materials_list[3:]:
                    new_active_materials[material] = fraction
                self._active_materials = new_active_materials
            return
            
        # Validate the input
        self.validate_type(new_material, _ActiveMaterial, "Active material")
        
        materials_list = list(self._active_materials.items())
        
        if len(materials_list) < 3:
            # Add new material with mass fraction of 0
            new_active_materials = {}
            # Keep existing materials
            for material, fraction in materials_list:
                new_active_materials[material] = fraction
            # Add new material with 0 mass fraction
            new_active_materials[new_material] = 0.0
        else:
            # Replace existing third material, keeping its mass fraction
            third_material_fraction = materials_list[2][1]
            
            # Create new dictionary maintaining order
            new_active_materials = {}
            new_active_materials[materials_list[0][0]] = materials_list[0][1]  # Keep first material
            new_active_materials[materials_list[1][0]] = materials_list[1][1]  # Keep second material
            new_active_materials[new_material] = third_material_fraction       # Replace third material
            
            # Add remaining materials (if any)
            for material, fraction in materials_list[3:]:
                new_active_materials[material] = fraction
        
        # Update the active materials
        self._active_materials = new_active_materials
        
        # Handle voltage cutoff compatibility with new materials
        self._handle_voltage_cutoff_compatibility()

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
    def binder_1(self, material: Binder):
        """
        Set the first binder material. If a first binder already exists,
        it will be replaced. If no binder exists, the material will be added
        with 0 mass fraction. If None is passed, removes the first binder.
        
        Parameters
        ----------
        material : Binder or None
            The binder material to set as the first binder, or None to remove it
        """
        if material is None:
            # Remove the first binder
            binders_list = list(self._binders.items())
            if len(binders_list) > 0:
                # Create new dictionary without the first binder
                new_binders = {}
                for binder, fraction in binders_list[1:]:
                    new_binders[binder] = fraction
                self._binders = new_binders
            return
            
        self.validate_type(material, Binder, "Binder material")
        
        binders_list = list(self._binders.items())
        
        if len(binders_list) >= 1:
            # Replace existing first binder
            old_material = binders_list[0][0]
            old_weight = self._binders[old_material]
            del self._binders[old_material]
            self._binders[material] = old_weight
            # Reorder to put new material first
            self._binders = {material: self._binders.pop(material), **self._binders}
        else:
            # Add new material with 0 weight fraction
            self._binders[material] = 0.0

    @binder_2.setter
    @calculate_all_properties
    def binder_2(self, material: Binder):
        """
        Set the second binder material. If a second binder already exists,
        it will be replaced. If only one binder exists, the material will be added
        with 0 mass fraction. If no binders exist, raises an error.
        If None is passed, removes the second binder.
        
        Parameters
        ----------
        material : Binder or None
            The binder material to set as the second binder, or None to remove it
        """
        if material is None:
            # Remove the second binder
            binders_list = list(self._binders.items())
            if len(binders_list) >= 2:
                # Create new dictionary without the second binder
                new_binders = {}
                # Keep first binder
                new_binders[binders_list[0][0]] = binders_list[0][1]
                # Keep binders from third position onwards
                for binder, fraction in binders_list[2:]:
                    new_binders[binder] = fraction
                self._binders = new_binders
            return
            
        self.validate_type(material, Binder, "Binder material")
        
        binders_list = list(self._binders.items())
        
        if len(binders_list) == 0:
            raise ValueError("Cannot set binder_2: formulation has no binders. Set binder_1 first.")
        elif len(binders_list) == 1:
            # Add second binder with 0 weight fraction
            self._binders[material] = 0.0
        else:
            # Replace existing second binder
            old_material = binders_list[1][0]
            old_weight = self._binders[old_material]
            del self._binders[old_material]
            # Insert as second material
            first_material = binders_list[0][0]
            first_weight = self._binders[first_material]
            self._binders = {first_material: first_weight, material: old_weight, **{k: v for k, v in self._binders.items() if k != first_material}}

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
    def conductive_additive_1(self, material: ConductiveAdditive):
        """
        Set the first conductive additive material. If a first conductive additive already exists,
        it will be replaced. If no conductive additive exists, the material will be added
        with 0 mass fraction.
        
        Parameters
        ----------
        material : ConductiveAdditive
            The conductive additive material to set as the first conductive additive
        """
        self.validate_type(material, ConductiveAdditive, "Conductive additive material")
        
        additives_list = list(self._conductive_additives.items())
        
        if len(additives_list) >= 1:
            # Replace existing first conductive additive
            old_material = additives_list[0][0]
            old_weight = self._conductive_additives[old_material]
            del self._conductive_additives[old_material]
            self._conductive_additives[material] = old_weight
            # Reorder to put new material first
            self._conductive_additives = {material: self._conductive_additives.pop(material), **self._conductive_additives}
        else:
            # Add new material with 0 weight fraction
            self._conductive_additives[material] = 0.0

    @conductive_additive_2.setter
    @calculate_all_properties
    def conductive_additive_2(self, material: ConductiveAdditive):
        """
        Set the second conductive additive material. If a second conductive additive already exists,
        it will be replaced. If only one conductive additive exists, the material will be added
        with 0 mass fraction. If no conductive additives exist, raises an error.
        
        Parameters
        ----------
        material : ConductiveAdditive
            The conductive additive material to set as the second conductive additive
        """
        self.validate_type(material, ConductiveAdditive, "Conductive additive material")
        
        additives_list = list(self._conductive_additives.items())
        
        if len(additives_list) == 0:
            raise ValueError("Cannot set conductive_additive_2: formulation has no conductive additives. Set conductive_additive_1 first.")
        elif len(additives_list) == 1:
            # Add second conductive additive with 0 weight fraction
            self._conductive_additives[material] = 0.0
        else:
            # Replace existing second conductive additive
            old_material = additives_list[1][0]
            old_weight = self._conductive_additives[old_material]
            del self._conductive_additives[old_material]
            # Insert as second material
            first_material = additives_list[0][0]
            first_weight = self._conductive_additives[first_material]
            self._conductive_additives = {first_material: first_weight, material: old_weight, **{k: v for k, v in self._conductive_additives.items() if k != first_material}}

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
        # First ensure we have a voltage operation window
        self._get_voltage_operation_window()

        if voltage is None:
            if type(self) == CathodeFormulation:
                voltage = max(self._voltage_operation_window)
            else:
                voltage = min(self._voltage_operation_window)

        self.validate_positive_float(voltage, "Voltage cutoff")

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
            The maximum voltage for the half-cell curves. If not provided, it will be set to
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
