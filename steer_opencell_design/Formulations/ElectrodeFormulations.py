from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Electrochemical import calculate_half_cell_curve
from steer_core.Constants.Units import *

from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_materials.CellMaterials.Electrode import (
    _ActiveMaterial,
    Binder,
    ConductiveAdditive,
)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, Any
import warnings


class _ElectrodeFormulation(
    ValidationMixin, 
    DunderMixin,
    PlotterMixin
    ):

    def __init__(
        self,
        active_materials: Dict[_ActiveMaterial, float],
        binders: Optional[Dict[Binder, float]] = {},
        conductive_additives: Optional[Dict[ConductiveAdditive, float]] = {},
        voltage_cutoff: Optional[float] = None,
        name: Optional[str] = "Electrode Formulation",
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
        """
        self._update_properties = False

        self.active_materials = active_materials
        self.binders = binders
        self.conductive_additives = conductive_additives
        self.voltage_cutoff = voltage_cutoff
        self.name = name

        self._check_formulation()
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """
        Retrieve the properties of the electrode formulation.
        This method is called to ensure that all properties are calculated and available.
        """
        self._get_bulk_properties()
        self._get_breakdowns()
        self._check_formulation()

        self._get_voltage_operation_window()
        self._calculate_half_cell_curve()

    def _get_breakdowns(self) -> None:
        """
        Retrieve the breakdowns of the electrode formulation.
        This method is called to ensure that all breakdowns are calculated and available.
        """
        self._get_density_breakdown()
        self._get_specific_cost_breakdown()

    def _get_bulk_properties(self) -> None:
        self._calculate_density()
        self._calculate_specific_cost()
        self._get_color()

    def _calculate_density(self) -> float:
        """
        Calculate the density of the electrode formulation.

        :return: The density of the electrode formulation in kg/m³.
        """

        def extract_material_data(material_dict):
            return [(material._density, fraction) for material, fraction in material_dict.items()]

        # Collect (density, mass_fraction) pairs from all sources
        components = extract_material_data(self._active_materials) + extract_material_data(self._binders) + extract_material_data(self._conductive_additives)

        # Weighted average density
        self._density = sum(d * mf for d, mf in components)
        self._specific_volume = 1 / self._density
        return self._density, self._specific_volume

    def _calculate_specific_cost(self) -> float:
        """
        Calculate the specific cost of the electrode formulation.

        :return: The specific cost of the electrode formulation in $/kg.
        """

        def extract_cost_data(material_dict):
            return [(material._specific_cost, fraction) for material, fraction in material_dict.items()]

        components = extract_cost_data(self._active_materials) + extract_cost_data(self._binders) + extract_cost_data(self._conductive_additives)

        self._specific_cost = sum(cost * mf for cost, mf in components)
        return self._specific_cost

    def _get_color(self) -> str:
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

        def extract_color_data(material_dict):
            return [(hex_to_rgb(material._color), fraction) for material, fraction in material_dict.items()]

        # Gather all (rgb, fraction) pairs
        components = extract_color_data(self._active_materials) + extract_color_data(self._binders) + extract_color_data(self._conductive_additives)

        # Weighted average of RGB channels
        total_r = sum(rgb[0] * f for rgb, f in components)
        total_g = sum(rgb[1] * f for rgb, f in components)
        total_b = sum(rgb[2] * f for rgb, f in components)

        avg_rgb = (total_r, total_g, total_b)

        self._color = rgb_to_hex(avg_rgb)

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

        if not (0.999 <= total_fraction <= 1.001):
            warnings.warn(
                f"The total mass percentages of the formulation should sum to 100%. Current sum: {round(total_fraction * 100, 1)}%",
                UserWarning,
            )

        self._check_unique_names(self._active_materials, "active materials")
        self._check_unique_names(self._binders, "binders")
        self._check_unique_names(self._conductive_additives, "conductive additives")

    def _check_unique_names(self, components: Dict, component_type: str) -> None:
        """
        Validate that the components have unique names.

        :param components: Dictionary of components to validate.
        :param component_type: Type of components being validated (for error messages).
        """
        names = [component.name for component in components.keys()]

        if len(names) != len(set(names)):
            warnings.warn(
                f"Duplicate names found in {component_type} of your {type(self)}. Each component should have a unique name.",
                UserWarning,
            )

    def _get_specific_cost_breakdown(self) -> None:
        active_material_specific_costs = [c._specific_cost for c in self._active_materials.keys()]

        active_material_costs = {key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_specific_costs)}

        binder_specific_costs = [c._specific_cost for c in self._binders.keys()]
        binder_costs = {key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_specific_costs)} if self._binders else {}

        conductive_additive_costs = [c._specific_cost for c in self._conductive_additives.keys()]
        conductive_additive_costs = {key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_costs)} if self._conductive_additives else {}

        self._specific_cost_breakdown = active_material_costs | binder_costs | conductive_additive_costs

    def _get_density_breakdown(self) -> Dict[str, float]:
        """
        Calculate the density breakdown of the electrode formulation.

        :return: A dictionary with the density contribution of each component.
        """
        active_material_densities = [c._density for c in self._active_materials.keys()]

        active_material_density_breakdown = {key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_densities)}

        binder_densities = [c._density for c in self._binders.keys()]

        binder_density_breakdown = {key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_densities)} if self._binders else {}

        conductive_additive_densities = [c._density for c in self._conductive_additives.keys()]

        conductive_additive_density_breakdown = {key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_densities)} if self._conductive_additives else {}

        self._density_breakdown = active_material_density_breakdown | binder_density_breakdown | conductive_additive_density_breakdown

    def _calculate_half_cell_curve(self) -> None:
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
            curve = material._half_cell_curve.copy()
            curve[:, 0] *= weight_frac
            self._half_cell_curve = curve
            return

        # Determine common charge/discharge voltage ranges
        def get_common_voltage_range(direction: str):
            direction_value = 1 if direction == "charge" else -1
            v_starts = []
            v_ends = []

            for material in self._active_materials:
                direction_mask = material._half_cell_curve[:, 2] == direction_value
                direction_curve = material._half_cell_curve[direction_mask]

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
            curve = material._half_cell_curve.copy()
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
            self._half_cell_curve = np.vstack(curves_to_stack)
        else:
            # Fallback empty curve
            self._half_cell_curve = np.array([]).reshape(0, 3)

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

    def plot_half_cell_curve(self, add_materials: bool = False, show_direction: bool = True, **kwargs) -> go.Figure:
        """
        Plot the half-cell curve for the formulation.

        Parameters
        ----------
        add_materials : bool, optional
            Whether to add individual material curves. Default is False.
        show_direction : bool, optional
            Whether to show charge/discharge direction markers. Default is True.
        **kwargs : dict
            Additional arguments to pass to the plotly figure layout.

        Returns
        -------
        go.Figure
            A plotly figure showing the half-cell curve.
        """
        figure = go.Figure()

        # Add main formulation curve as a single continuous line
        figure.add_trace(self.half_cell_curve_trace)

        # Add individual material curves if requested
        if add_materials:
            for material in self._active_materials.keys():
                figure.add_trace(material.half_cell_curve_trace)

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
    def half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.half_cell_curve["Specific Capacity (mAh/g)"],
            y=self.half_cell_curve["Voltage (V)"],
            name=self.name,
            line=dict(color=self._color, width=3, shape="spline"),
            mode="lines",
            hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
            customdata=self.half_cell_curve["Direction"],
            showlegend=True,
        )

    @property
    def name(self) -> Optional[str]:
        return self._name.replace("_", " ").title()

    @property
    def active_materials(self) -> Dict[_ActiveMaterial, float]:
        return {key: value * 100 for key, value in self._active_materials.items()}

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
        return round(self._voltage_cutoff, 3)

    @property
    def voltage_cutoff_range(self) -> tuple:
        return (min(self.voltage_operation_window), max(self.voltage_operation_window))

    @property
    def voltage_cutoff_hard_range(self) -> tuple:
        return self.voltage_cutoff_range

    @property
    def voltage_cutoff_hard_range(self) -> tuple:
        return self.voltage_operation_window

    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / (M_TO_CM**3), 2)

    @property
    def specific_cost(self) -> float:
        return round(self._specific_cost, 2)

    @property
    def specific_cost_breakdown(self) -> Dict[str, float]:
        return {key: round(value, 4) for key, value in self._specific_cost_breakdown.items()}

    @property
    def density_breakdown(self) -> Dict[str, float]:
        return {key: round(value * KG_TO_G / (M_TO_CM**3), 4) for key, value in self._density_breakdown.items()}

    @property
    def specific_volume(self) -> float:
        """
        Get the theoretical specific volume of the formulation.

        :return: Theoretical specific volume in cm³/g.
        """
        return round(self._specific_volume * (M_TO_CM**3) / KG_TO_G, 2)

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
    def half_cell_curve(self) -> pd.DataFrame:
        return (
            pd.DataFrame(
                self._half_cell_curve,
                columns=["specific_capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                specific_capacity=lambda x: x["specific_capacity"] * (S_TO_H * A_TO_mA / KG_TO_G),
            )
            .rename(
                columns={
                    "specific_capacity": "Specific Capacity (mAh/g)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
            .round(4)
        )

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

    @voltage_cutoff.setter
    @calculate_half_cell_curve
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
