from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Electrochemical import calculate_half_cell_curve
from steer_core.Constants.Units import *
from steer_core.Mixins.Validators import ValidationMixin

from steer_materials.CellMaterials.Electrode import _ActiveMaterial, Binder, ConductiveAdditive

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional



class _ElectrodeFormulation(ValidationMixin):
    
    def __init__(
            self, 
            active_materials: Dict[_ActiveMaterial, float], 
            binders: Optional[Dict[Binder, float]] = None, 
            conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None,
            voltage_cutoff: Optional[float] = None,
            name: Optional[str] = 'Electrode Formulation'
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
        self._get_voltage_operation_window()
        self._check_formulation()
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

        :return: The density of the electrode formulation in g/cm³.
        """
        def extract_material_data(material_dict):
            return [(material._density, fraction) for material, fraction in material_dict.items()]

        # Collect (density, mass_fraction) pairs from all sources
        components = (
            extract_material_data(self._active_materials) +
            extract_material_data(self._binders) +
            extract_material_data(self._conductive_additives)
        )

        # Weighted average density
        self._density = sum(d * mf for d, mf in components)
        return self._density

    def _calculate_specific_cost(self) -> float:
        """
        Calculate the specific cost of the electrode formulation.

        :return: The specific cost of the electrode formulation in $/kg.
        """
        def extract_cost_data(material_dict):
            return [(material._specific_cost, fraction) for material, fraction in material_dict.items()]

        components = (
            extract_cost_data(self._active_materials) +
            extract_cost_data(self._binders) +
            extract_cost_data(self._conductive_additives)
        )

        self._specific_cost = sum(cost * mf for cost, mf in components)
        return self._specific_cost

    def _get_color(self) -> str:
        """
        Calculate the average HTML color of the electrode formulation,
        weighted by the mass fraction of each component.

        :return: A hex color string representing the weighted average color.
        """
        def hex_to_rgb(hex_code: str) -> tuple:
            hex_code = hex_code.lstrip('#')
            return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb: tuple) -> str:
            return '#{:02x}{:02x}{:02x}'.format(*map(lambda x: int(round(x)), rgb))

        def extract_color_data(material_dict):
            return [(hex_to_rgb(material._color), fraction) for material, fraction in material_dict.items()]

        # Gather all (rgb, fraction) pairs
        components = (
            extract_color_data(self._active_materials) +
            extract_color_data(self._binders) +
            extract_color_data(self._conductive_additives)
        )

        # Weighted average of RGB channels
        total_r = sum(rgb[0] * f for rgb, f in components)
        total_g = sum(rgb[1] * f for rgb, f in components)
        total_b = sum(rgb[2] * f for rgb, f in components)

        avg_rgb = (total_r, total_g, total_b)

        self._color = rgb_to_hex(avg_rgb)

    def _get_voltage_operation_window(self) -> None:

        # Get the voltage operation window from each active material
        voltage_operation_windows = [material._voltage_operation_window for material in self._active_materials.keys()]

        # Determine the common voltage operation window
        starts, middles, ends = zip(*voltage_operation_windows)
        common_start = max(starts) if type(self) == CathodeFormulation else min(starts)
        common_end = min(ends) if type(self) == CathodeFormulation else max(ends)

        if (common_start <= common_end and type(self) == CathodeFormulation) or (common_start >= common_end and type(self) == AnodeFormulation):
            self._voltage_operation_window = (common_start, common_end)
        else:
            raise ValueError("The active materials have incompatible voltage cutoff ranges.")

    def _check_formulation(self) -> None:
        """
        Validate the electrode formulation to ensure it meets the required criteria.
        """
        total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())

        if not (0.999 <= total_fraction <= 1.001):
            raise ValueError(f"Your weight fractions sum to {round(total_fraction * 100, 1)} %. Ensure they sum to 100 %.")

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
            raise ValueError(f"The {component_type} must have unique names.")

    def _get_specific_cost_breakdown(self) -> None:

        active_material_specific_costs = [c._specific_cost for c in self._active_materials.keys()]

        active_material_costs = {
            key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_specific_costs)
        }

        binder_specific_costs = [c._specific_cost for c in self._binders.keys()]
        binder_costs = {
            key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_specific_costs)
        } if self._binders else {}

        conductive_additive_costs = [c._specific_cost for c in self._conductive_additives.keys()]
        conductive_additive_costs = {
            key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_costs)
        } if self._conductive_additives else {}

        self._specific_cost_breakdown = active_material_costs | binder_costs | conductive_additive_costs

    def _get_density_breakdown(self) -> Dict[str, float]:
        """
        Calculate the density breakdown of the electrode formulation.

        :return: A dictionary with the density contribution of each component.
        """
        active_material_densities = [c._density for c in self._active_materials.keys()]

        active_material_density_breakdown = {
            key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_densities)
        }

        binder_densities = [c._density for c in self._binders.keys()]

        binder_density_breakdown = {
            key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_densities)
        } if self._binders else {}

        conductive_additive_densities = [c._density for c in self._conductive_additives.keys()]
        
        conductive_additive_density_breakdown = {
            key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_densities)
        } if self._conductive_additives else {}

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
            curve[:,0] *= weight_frac
            self._half_cell_curve = curve
            return 

        # Determine common charge/discharge voltage ranges
        def get_common_voltage_range(direction: str):
            direction_value = 1 if direction == 'charge' else -1
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

        v_charge_grid = get_common_voltage_range('charge')
        v_discharge_grid = get_common_voltage_range('discharge')

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
                    charge_curve[:, 0]   # capacity (y)
                )
            else:
                charge_interp = np.full_like(v_charge_grid, 0.0)

            # Safe interpolation for discharge curve
            if len(discharge_curve) > 0 and len(v_discharge_grid) > 0:
                discharge_interp = safe_interp(
                    v_discharge_grid, 
                    discharge_curve[:, 1],  # voltage (x)
                    discharge_curve[:, 0]   # capacity (y)
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
            charge_df = np.column_stack([
                summed_charge_capacity, 
                v_charge_grid, 
                np.ones_like(v_charge_grid)
            ])
            # Sort charge curve by specific capacity (ascending - lowest to highest)
            charge_df = charge_df[np.argsort(charge_df[:, 0])]
            curves_to_stack.append(charge_df)

        # Then add discharge curve (if it exists) - sorted from highest to lowest specific capacity
        if len(summed_discharge_capacity) > 0:
            discharge_df = np.column_stack([
                summed_discharge_capacity,
                v_discharge_grid,
                -np.ones_like(v_discharge_grid)
            ])
            # Sort discharge curve by specific capacity (descending - highest to lowest)
            discharge_df = discharge_df[np.argsort(discharge_df[:, 0])[::-1]]
            curves_to_stack.append(discharge_df)

        if curves_to_stack:
            self._half_cell_curve = np.vstack(curves_to_stack)
        else:
            # Fallback empty curve
            self._half_cell_curve = np.array([]).reshape(0, 3)

    def plot_half_cell_curve(self, add_materials: bool = False, **kwargs):

        figure = go.Figure()

        main_curve_data = self.half_cell_curve

        figure.add_trace(
            go.Scatter(
                x=main_curve_data['Specific Capacity (mAh/g)'],
                y=main_curve_data['Voltage (V)'],
                name=self.name,
                line=dict(color=self._color, width=2, shape='spline'),
            )
        )

        if add_materials:
            for material in self._active_materials.keys():
                
                material_curve = material.half_cell_curve

                figure.add_trace(
                    go.Scatter(
                        x=material_curve['Specific Capacity (mAh/g)'],
                        y=material_curve['Voltage (V)'],
                        name=material.name,
                        line=dict(color=material._color, width=2, dash='dash')
                    )
                )

        figure.update_layout(
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            xaxis=dict(title='Specific Capacity (mAh/g)'),
            yaxis=dict(title='Voltage (V)'),
            **kwargs
        )

        return figure

    def plot_specific_cost_breakdown(self, **kwargs) -> go.Figure:
        """
        Create a sunburst plot showing the specific cost breakdown of the formulation.
        
        Parameters
        ----------
        **kwargs : dict
            Additional arguments to pass to the plotly figure layout.
            
        Returns
        -------
        go.Figure
            A plotly sunburst chart showing the cost breakdown by material type and individual materials.
        """
        # Get the cost breakdown data
        cost_data = self.specific_cost_breakdown
        
        if not cost_data:
            # Return empty figure if no cost data
            fig = go.Figure()
            fig.add_annotation(
                text="No cost breakdown data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Separate materials by type
        active_material_names = [material.name for material in self._active_materials.keys()]
        binder_names = [material.name for material in self._binders.keys()] if self._binders else []
        conductive_additive_names = [material.name for material in self._conductive_additives.keys()] if self._conductive_additives else []
        
        # Prepare data for sunburst
        labels = ["Total"]  # Root node
        parents = [""]      # Root has no parent
        values = [sum(cost_data.values())]  # Total cost
        colors = ["lightgray"]  # Root color
        
        # Add category nodes (Active Materials, Binders, Conductive Additives)
        categories = []
        category_costs = {}
        
        if active_material_names:
            categories.append("Active Materials")
            category_costs["Active Materials"] = sum(cost_data[name] for name in active_material_names if name in cost_data)
            
        if binder_names:
            categories.append("Binders")
            category_costs["Binders"] = sum(cost_data[name] for name in binder_names if name in cost_data)
            
        if conductive_additive_names:
            categories.append("Conductive Additives")
            category_costs["Conductive Additives"] = sum(cost_data[name] for name in conductive_additive_names if name in cost_data)
        
        # Add category nodes
        for category in categories:
            labels.append(category)
            parents.append("Total")
            values.append(category_costs[category])
            colors.append("lightblue" if "Active" in category else "lightgreen" if "Binder" in category else "lightyellow")
        
        # Add individual material nodes
        for material_name, cost in cost_data.items():
            labels.append(material_name)
            values.append(cost)
            
            # Determine parent category
            if material_name in active_material_names:
                parents.append("Active Materials")
                # Get the actual material color
                material_obj = next((m for m in self._active_materials.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "blue")
            elif material_name in binder_names:
                parents.append("Binders")
                material_obj = next((m for m in self._binders.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "green")
            elif material_name in conductive_additive_names:
                parents.append("Conductive Additives")
                material_obj = next((m for m in self._conductive_additives.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "orange")
            else:
                parents.append("Total")
                colors.append("gray")
        
        # Create the sunburst plot
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:.4f}/kg<br>Percentage: %{percentParent}<extra></extra>',
            maxdepth=3,
        ))
        
        # Update layout
        fig.update_layout(
            font_size=12,
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            margin=dict(l=10, r=10, t=10, b=10),  # Minimal margins with no title
            **kwargs
        )
        
        return fig

    def plot_density_breakdown(self, **kwargs) -> go.Figure:
        """
        Create a sunburst plot showing the density breakdown of the formulation.
        
        Parameters
        ----------
        **kwargs : dict
            Additional arguments to pass to the plotly figure layout.
            
        Returns
        -------
        go.Figure
            A plotly sunburst chart showing the density breakdown by material type and individual materials.
        """
        # Get the density breakdown data
        density_data = self.density_breakdown
        
        if not density_data:
            # Return empty figure if no density data
            fig = go.Figure()
            fig.add_annotation(
                text="No density breakdown data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            return fig
        
        # Separate materials by type
        active_material_names = [material.name for material in self._active_materials.keys()]
        binder_names = [material.name for material in self._binders.keys()] if self._binders else []
        conductive_additive_names = [material.name for material in self._conductive_additives.keys()] if self._conductive_additives else []
        
        # Prepare data for sunburst
        labels = ["Total"]  # Root node
        parents = [""]      # Root has no parent
        values = [sum(density_data.values())]  # Total density
        colors = ["lightgray"]  # Root color
        
        # Add category nodes (Active Materials, Binders, Conductive Additives)
        categories = []
        category_densities = {}
        
        if active_material_names:
            categories.append("Active Materials")
            category_densities["Active Materials"] = sum(density_data[name] for name in active_material_names if name in density_data)
            
        if binder_names:
            categories.append("Binders")
            category_densities["Binders"] = sum(density_data[name] for name in binder_names if name in density_data)
            
        if conductive_additive_names:
            categories.append("Conductive Additives")
            category_densities["Conductive Additives"] = sum(density_data[name] for name in conductive_additive_names if name in density_data)
        
        # Add category nodes
        for category in categories:
            labels.append(category)
            parents.append("Total")
            values.append(category_densities[category])
            colors.append("lightblue" if "Active" in category else "lightgreen" if "Binder" in category else "lightyellow")
        
        # Add individual material nodes
        for material_name, density in density_data.items():
            labels.append(material_name)
            values.append(density)
            
            # Determine parent category
            if material_name in active_material_names:
                parents.append("Active Materials")
                # Get the actual material color
                material_obj = next((m for m in self._active_materials.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "blue")
            elif material_name in binder_names:
                parents.append("Binders")
                material_obj = next((m for m in self._binders.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "green")
            elif material_name in conductive_additive_names:
                parents.append("Conductive Additives")
                material_obj = next((m for m in self._conductive_additives.keys() if m.name == material_name), None)
                colors.append(material_obj._color if material_obj else "orange")
            else:
                parents.append("Total")
                colors.append("gray")
        
        # Create the sunburst plot
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>Density: %{value:.4f} g/cm³<br>Percentage: %{percentParent}<extra></extra>',
            maxdepth=3,
        ))
        
        # Update layout
        fig.update_layout(
            font_size=12,
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            margin=dict(l=10, r=10, t=10, b=10),  # Minimal margins with no title
            **kwargs
        )
        
        return fig

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
        return self.voltage_operation_window
    
    @property
    def voltage_cutoff_hard_range(self) -> tuple:
        return self.voltage_operation_window

    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / (M_TO_CM ** 3), 2)
    
    @property
    def specific_cost(self) -> float:
        return round(self._specific_cost, 2)

    @property
    def specific_cost_breakdown(self) -> Dict[str, float]:
        return {key: round(value, 4) for key, value in self._specific_cost_breakdown.items()}
    
    @property
    def density_breakdown(self) -> Dict[str, float]:
        return {key: round(value * KG_TO_G / (M_TO_CM ** 3), 4) for key, value in self._density_breakdown.items()}

    @property
    def voltage_operation_window(self) -> tuple:
        """
        Get the valid voltage range for the half cell curves.
        
        :return: tuple: (minimum voltage, maximum voltage)
        """
        return (
            round(self._voltage_operation_window[0], 3), 
            round(self._voltage_operation_window[1], 3)
        )

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        return (
            pd.DataFrame(
                self._half_cell_curve,
                columns=['specific_capacity', 'voltage', 'direction']
            )
            .assign(
                direction = lambda x: np.where(x['direction'] == 1, 'charge', 'discharge'),
                specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
            ).rename(
                columns={
                    'specific_capacity': 'Specific Capacity (mAh/g)', 
                    'voltage': 'Voltage (V)', 
                    'direction': 'Direction',
                }
            ).round(
                4
            )
        )

    @property
    def color(self) -> str:
        return self._color

    @name.setter
    def name(self, name: str):
        self.validate_string(name, "Name")        
        self._name = name

    @conductive_additives.setter
    @calculate_all_properties
    def conductive_additives(self, conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None):

        if conductive_additives != {}:

            for key, value in conductive_additives.items():
                self.validate_conductive_additive(key)
                self.validate_percentage(value, f"Mass fraction for {key.name}")

        self._conductive_additives = {key: value / 100 for key, value in conductive_additives.items() if key is not None}
        
    @binders.setter
    def binders(self, binders: Optional[Dict[Binder, float]] = None):

        if binders != {}:        

            for key, value in binders.items():
                self.validate_binder(key)
                self.validate_percentage(value, f"Mass fraction for {key.name}")
        
        self._binders = {key: value / 100 for key, value in binders.items()}
 
    @active_materials.setter
    @calculate_all_properties
    def active_materials(self, active_materials: Dict[_ActiveMaterial, float]):

        # Check if active_materials is empty
        if len(active_materials) == 0:
            raise ValueError("You must include at least one active material in the formulation.")

        # Check the types and values of the active materials
        for key, value in active_materials.items():
            self.validate_active_material(key)
            self.validate_percentage(value, f"Mass fraction for {key.name}")

        self._active_materials = {key: value / 100 for key, value in active_materials.items()}
        self._get_voltage_operation_window()

    @voltage_cutoff.setter
    @calculate_half_cell_curve
    def voltage_cutoff(self, voltage: float):
        """
        Set the voltage cutoff for the half cell curves.
        
        :param voltage: float: maximum voltage of the half cell curves
        """
        self._get_voltage_operation_window()

        if voltage is None:
            voltage = max(self._voltage_operation_window) if type(self) == CathodeFormulation else min(self._voltage_operation_window)

        self.validate_positive_float(voltage, "Voltage cutoff")
        
        if voltage < min(self._voltage_operation_window) or voltage > max(self._voltage_operation_window):
            raise ValueError(f"Voltage cutoff must be within the range {self._voltage_operation_window}")
        
        # set the voltage cutoff for each active material
        for material in self._active_materials:
            material.voltage_cutoff = voltage

        self._voltage_cutoff = voltage

    def __str__(self) -> str:
        return self._name if self._name else "Electrode Formulation"
    
    def __repr__(self) -> str:
        return self.__str__()


class CathodeFormulation(_ElectrodeFormulation):
    """
    Represents a cathode formulation in a battery.
    Inherits from _ElectrodeFormulation.
    """
    def __init__(
            self, 
            active_materials: Dict[_ActiveMaterial, float], 
            binders: Optional[Dict[Binder, float]] = None, 
            conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None,
            voltage_cutoff: Optional[float] = None,
            name: Optional[str] = 'Cathode Formulation'
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
            name=name
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
            binders: Optional[Dict[Binder, float]] = None, 
            conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None,
            voltage_cutoff: Optional[float] = None,
            name: Optional[str] = 'Anode Formulation'
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
            name=name
        )
        
        self._update_properties = True



