from steer_opencell_design.Constructions.Layups import _Layup
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Data import DataMixin

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.AuxillaryComponents.WindingEquipment import RoundMandrel, FlatMandrel

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial

from copy import deepcopy
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
from shapely import minimum_bounding_circle
import warnings
import plotly.graph_objects as go
from typing import Any, Dict, Tuple



class _ElectrodeAssembly(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin,
    PlotterMixin,
    DataMixin
):
    
    def __init__(
            self,
            layup: _Layup,
            name: str = "Electrode Assembly"
        ):

        self._update_properties = False

        self.layup = layup
        self.name = name

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_interfacial_area()
        self._calcualate_full_cell_curve()
        self._calculate_energy()

    def _calculate_bulk_properties(self):
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_energy(self):
        discharge_curve = self._full_cell_curve[self._full_cell_curve[:,2] == -1]
        discharge_curve = discharge_curve[np.argsort(discharge_curve[:,0])]
        capacity = discharge_curve[:,0]
        voltage = discharge_curve[:,1]
        energy = np.trapz(capacity, voltage)
        self._energy = energy
        return self._energy

    def _calculate_mass_properties(self):
        pass

    def _calculate_cost_properties(self):
        pass

    def _calculate_interfacial_area(self):
        """Calculate interfacial area of the electrode assembly."""
        pass

    def _calculate_geometry_parameters(self):
        """Calculate geometry parameters of the electrode assembly."""
        pass

    def _calcualate_full_cell_curve(self):

        """Calculate full cell voltage curve of the electrode assembly."""
        _full_cell_curve = deepcopy(self._layup._full_cell_curve)
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * self._interfacial_area
        self._full_cell_curve = _full_cell_curve

        # also calculate half-cell curve for cathode
        _cathode_half_cell_curve = deepcopy(self._layup._cathode._half_cell_curve)
        _cathode_half_cell_curve[:, 4] = _cathode_half_cell_curve[:, 4] * self._interfacial_area
        self._cathode_half_cell_curve = np.column_stack([_cathode_half_cell_curve[:,4], _cathode_half_cell_curve[:,1], _cathode_half_cell_curve[:,2]])

        # also calculate half-cell curve for anode
        _anode_half_cell_curve = deepcopy(self._layup._anode._half_cell_curve)
        _anode_half_cell_curve[:, 4] = _anode_half_cell_curve[:, 4] * self._interfacial_area
        self._anode_half_cell_curve = np.column_stack([_anode_half_cell_curve[:,4], _anode_half_cell_curve[:,1], _anode_half_cell_curve[:,2]])

        return self._full_cell_curve, self._cathode_half_cell_curve, self._anode_half_cell_curve
    
    def _calculate_anode_half_cell_curve(self):
        """Calculate anode half-cell voltage curve of the electrode assembly."""
        _anode_half_cell = deepcopy(self._layup._anode._half_cell_curve)
        _anode_half_cell[:, 0] = _anode_half_cell[:, 0] * self._interfacial_area
        self._anode_half_cell = _anode_half_cell
        return self._anode_half_cell
    
    def _calculate_cathode_half_cell_curve(self):
        """Calculate cathode half-cell voltage curve of the electrode assembly."""
        _cathode_half_cell = deepcopy(self._layup._cathode._half_cell_curve)
        _cathode_half_cell[:, 0] = _cathode_half_cell[:, 0] * self._interfacial_area
        self._cathode_half_cell = _cathode_half_cell
        return self._cathode_half_cell
    
    def plot_mass_breakdown(self, title: str = None, **kwargs) -> go.Figure:

        fig = self.plot_breakdown_sunburst(
            self.mass_breakdown,
            title=title or f"{self.name} Mass Breakdown",
            unit="g",
            **kwargs,
        )

        return fig

    def plot_cost_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        
        fig = self.plot_breakdown_sunburst(
            self.cost_breakdown,
            title=title or f"{self.name} Cost Breakdown",
            unit="$",
            **kwargs,
        )

        return fig

    def get_capacity_plot(self, **kwargs) -> go.Figure:
        """
        Generate capacity plot for the assembly.

        Parameters
        ----------
        **kwargs
            Additional plotting parameters for customization

        Returns
        -------
        go.Figuren
            Plotly figure with capacity curves

        Raises
        ------
        ValueError
            If half-cell data is missing or invalid
        """
        fig = go.Figure()

        fig.add_trace(self.cathode_half_cell_curve_trace)
        fig.add_trace(self.anode_half_cell_curve_trace)
        fig.add_trace(self.full_cell_curve_trace)

        # Enhanced layout with zero lines and faint grid
        fig.update_layout(
            title=kwargs.get("title", f"Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Capacity (Ah)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
        )

        return fig

    @property
    def energy(self) -> float:
        """Return the energy of the electrode assembly in Wh."""
        return round(self._energy * J_TO_WH, 2)

    @property
    def name(self) -> str:
        """Return the name of the electrode assembly."""
        return self._name

    @property
    def interfacial_area(self) -> float:
        """Return the interfacial area of the electrode assembly in cm²."""
        return round(self._interfacial_area * M_TO_CM**2, 2)

    @property
    def layup(self) -> _Layup:
        """Return the underlying `_Layup` instance."""
        return self._layup
    
    @property
    def full_cell_curve(self) -> pd.DataFrame:

        return (
            pd.DataFrame(
                self._full_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                    "capacity": "Capacity (Ah)",
                }
            )
            .round(4)
        )
    
    @property
    def full_cell_curve_trace(self) -> go.Scatter:

        full_cell_color = "#ff8c00"

        return go.Scatter(
            x=self.full_cell_curve["Capacity (Ah)"],
            y=self.full_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Full-Cell",
            line=dict(color=full_cell_color, width=3),  # Slightly thicker for emphasis
            customdata=self.full_cell_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def anode_half_cell_curve(self) -> pd.DataFrame:

        return (
            pd
            .DataFrame(
                self._anode_half_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "capacity": "Capacity (Ah)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
        )
    
    @property
    def anode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_half_cell_curve["Capacity (Ah)"],
            y=self.anode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.anode.name} Half-Cell",
            line=dict(color=self.layup.anode.formulation.color, width=2.5),
            customdata=self.anode_half_cell_curve["Direction"],
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cathode_half_cell_curve(self) -> pd.DataFrame:
        
        return (
            pd
            .DataFrame(
                self._cathode_half_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "capacity": "Capacity (Ah)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
        )
    
    @property
    def cathode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_half_cell_curve["Capacity (Ah)"],
            y=self.cathode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.cathode.name} Half-Cell",
            line=dict(color=self.layup.cathode.formulation.color, width=2.5),
            customdata=self.cathode_half_cell_curve["Direction"],
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cost(self) -> float:
        """Return the cost of the electrode assembly in $."""
        return round(self._cost, 2)

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """

        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj, 2)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass(self) -> float:
        """Return the mass of the electrode assembly in g."""
        return round(self._mass * KG_TO_G, 2)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj * KG_TO_G, 2)

        return _convert_and_round_recursive(self._mass_breakdown)

    @name.setter
    def name(self, value: str):
        self.validate_string(value, "name")
        self._name = value


class _JellyRoll(_ElectrodeAssembly):
    """Jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel | RoundMandrel
        ):

        self.mandrel = mandrel
        super().__init__(laminate)

    def _calculate_all_properties(self):
        """Calculate all properties of the jelly roll electrode assembly."""
        self._calculate_roll()
        self._calculate_roll_properties()
        super()._calculate_all_properties()

    def _calculate_roll(self):
        """Public entry to generate variable-thickness winding spiral."""
        self._calculate_variable_thickness_spiral()
        self._build_component_spirals()
        self._build_extruded_component_spirals()
        self._calculate_spiral_properties()

    def _calculate_spiral_properties(self):
        """Calculate spiral properties of the electrode assembly."""
        self._calculate_interfacial_area()
        self._calculate_geometry_parameters()

    def _calculate_variable_thickness_spiral(self):
        pass

    def _build_component_spirals(self):
        pass

    def _build_extruded_component_spirals(self):
        pass

    def _calculate_roll_properties(self):
        """Calculate roll properties with optimized performance and error handling.
        
        Computes turn counts for all components and separator inner/outer turns
        relative to anode placement.
        """
        roll_properties = {}
        
        # Define column indices for clarity
        THETA_COL = 0
        TURNS_COL = 5
        
        # Cache component spirals to avoid repeated dictionary lookups
        component_spirals = {}
        component_names = [
            "anode_a_side_coating", "anode_b_side_coating", "anode_current_collector",
            "cathode_a_side_coating", "cathode_b_side_coating", "cathode_current_collector", 
            "bottom_separator", "top_separator"
        ]
        
        # Pre-fetch all component spirals with validation
        for name in component_names:
            spiral = self._component_spirals.get(name)
            if spiral is not None and len(spiral) > 0:
                component_spirals[name] = spiral
            else:
                # Handle missing components gracefully
                component_spirals[name] = np.empty((0, 6))
        
        # Calculate basic turn counts for all components
        for name in component_names:
            spiral = component_spirals[name]
            if len(spiral) > 0:
                roll_properties[f"{name}_turns"] = np.max(spiral[:, TURNS_COL])
            else:
                roll_properties[f"{name}_turns"] = 0.0
        
        # Calculate separator inner/outer turns relative to anode placement
        if (len(component_spirals["anode_a_side_coating"]) > 0 and 
            len(component_spirals["anode_b_side_coating"]) > 0):
            
            # Get anode theta boundaries
            anode_start_theta = component_spirals["anode_a_side_coating"][0, THETA_COL]
            anode_end_theta = component_spirals["anode_b_side_coating"][-1, THETA_COL]
            
            # Process both separators with the same logic
            for sep_name in ["bottom_separator", "top_separator"]:
                separator_spiral = component_spirals[sep_name]
                
                if len(separator_spiral) > 0:
                    # Inner turns: separator region after anode starts
                    inner_mask = separator_spiral[:, THETA_COL] > anode_start_theta
                    if np.any(inner_mask):
                        inner_turns = np.max(separator_spiral[inner_mask, TURNS_COL])
                    else:
                        inner_turns = 0.0
                    
                    # Outer turns: separator region before anode ends (turn range)
                    outer_mask = separator_spiral[:, THETA_COL] < anode_end_theta
                    if np.any(outer_mask):
                        outer_spiral = separator_spiral[outer_mask, TURNS_COL]
                        outer_turns = np.max(outer_spiral) - np.min(outer_spiral)
                    else:
                        outer_turns = 0.0
                    
                    # Store results
                    roll_properties[f"{sep_name}_inner_turns"] = inner_turns
                    roll_properties[f"{sep_name}_outer_turns"] = outer_turns
                else:
                    # Handle empty separator spirals
                    roll_properties[f"{sep_name}_inner_turns"] = 0.0
                    roll_properties[f"{sep_name}_outer_turns"] = 0.0
        else:
            # Handle case where anode components are missing
            for sep_name in ["bottom_separator", "top_separator"]:
                roll_properties[f"{sep_name}_inner_turns"] = 0.0  
                roll_properties[f"{sep_name}_outer_turns"] = 0.0
        
        self._roll_properties = roll_properties
        return self._roll_properties

    def _calculate_mass_properties(self):

        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._mass = self.layup.anode._mass + self.layup.cathode._mass + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anode": self.layup.anode._mass_breakdown,
            "Cathode": self.layup.cathode._mass_breakdown,
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._cost = self.layup.anode._cost + self.layup.cathode._cost + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anode": self.layup.anode._cost_breakdown,
            "Cathode": self.layup.cathode._cost_breakdown,
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    def get_spiral_plot(
            self, 
            layered: bool = True,
            extruded: bool = True,
            **kwargs) -> go.Figure:

        fig = go.Figure()

        if layered and not extruded:
            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_spiral_trace)
            fig.add_trace(self.cathode_current_collector_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_spiral_trace)

        elif layered and extruded:
            fig.add_trace(self.top_separator_extruded_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_extruded_spiral_trace)
            fig.add_trace(self.anode_current_collector_extruded_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_extruded_spiral_trace)
            fig.add_trace(self.bottom_separator_extruded_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_extruded_spiral_trace)
            fig.add_trace(self.cathode_current_collector_extruded_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_extruded_spiral_trace)

            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_spiral_trace)
            fig.add_trace(self.cathode_current_collector_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_spiral_trace)

        elif not layered:
            fig.add_trace(self.spiral_trace)

        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            hovermode="closest",
        )

        return fig

    @staticmethod
    def _format_np_spiral_for_df(np_array: np.ndarray) -> pd.DataFrame:
        """Format numpy spiral array into pandas DataFrame with proper units and column names.

        Columns: theta (degrees), x_unwrapped (mm), r (mm), x (mm), z (mm), turns
        """
        # Pre-compute all conversions in numpy (much faster than pandas operations)
        theta_deg = np.abs(np_array[:, 0] * (180.0 / PI) - 90)
        length_mm = np_array[:, 1] * M_TO_MM
        r_mm = np_array[:, 2] * M_TO_MM
        x_mm = np_array[:, 3] * M_TO_MM
        z_mm = np_array[:, 4] * M_TO_MM
        turns = np_array[:, 5]  # Number of turns (dimensionless)
        
        # Create DataFrame directly with final column names and converted values
        return pd.DataFrame({
            "Theta (degrees)": theta_deg,
            "Unwrapped Length (mm)": length_mm,
            "Radius (mm)": r_mm,
            "X (mm)": x_mm,
            "Z (mm)": z_mm,
            "Turns": turns,
        })
    
    def _format_spiral_trace(self, property_name: str, color: str, name: str) -> go.Scatter:
        
        df = getattr(self, property_name)
        # Build customdata array for rich hover (theta, length, radius, x, z, turns)
        customdata = np.stack([
            df['Theta (degrees)'],
            df['Unwrapped Length (mm)'],
            df['Radius (mm)'],
            df['X (mm)'],
            df['Z (mm)'],
            df['Turns']
        ], axis=-1)

        hovertemplate = (
            '<b>'+name+'</b><br>'
            'Theta: %{customdata[0]:.2f}°<br>'
            'Unwrapped Length: %{customdata[1]:.2f} mm<br>'
            'Radius: %{customdata[2]:.2f} mm<br>'
            'X: %{customdata[3]:.2f} mm<br>'
            'Z: %{customdata[4]:.2f} mm<br>'
            'Turns: %{customdata[5]:.2f}<extra></extra>'
        )

        trace = go.Scatter(
            x=df['X (mm)'],
            y=df['Z (mm)'],
            mode='lines',
            line=dict(color=color, width=0),
            line_shape='spline',
            name=name,
            customdata=customdata,
            hovertemplate=hovertemplate,
        )

        trace.showlegend = False

        return trace
    
    def _format_extruded_spiral_trace(self, property_name: str, color: str, name: str) -> go.Scatter:
        
        df = getattr(self, property_name)
        # Use same hover data schema as line spirals
        customdata = np.stack([
            df['Theta (degrees)'],
            df['Unwrapped Length (mm)'],
            df['Radius (mm)'],
            df['X (mm)'],
            df['Z (mm)'],
            df['Turns']
        ], axis=-1)

        hovertemplate = (
            '<b>'+name+' (Extruded)</b><br>'
            'Theta: %{customdata[0]:.2f}°<br>'
            'Unwrapped Length: %{customdata[1]:.2f} mm<br>'
            'Radius: %{customdata[2]:.2f} mm<br>'
            'X: %{customdata[3]:.2f} mm<br>'
            'Z: %{customdata[4]:.2f} mm<br>'
            'Turns: %{customdata[5]:.2f}<extra></extra>'
        )

        return go.Scatter(
            x=df['X (mm)'],
            y=df['Z (mm)'],
            mode='lines',
            fill='toself',
            fillcolor=color,
            line=dict(color="black", width=0.1),
            line_shape='spline',
            name=name,
            customdata=customdata,
            hovertemplate=hovertemplate,
        )

    @property
    def roll_properties(self) -> pd.DataFrame:
        """Return the roll properties as a pandas DataFrame with values rounded to 2 decimal places.
        
        Returns
        -------
        pd.DataFrame
            DataFrame containing roll properties with component names as index and turn counts as values.
        """
        # Create a formatted dictionary with rounded values
        formatted_props = {key: round(value, 2) for key, value in self._roll_properties.items()}
        
        # Convert to DataFrame with descriptive names
        df = pd.DataFrame.from_dict(formatted_props, orient='index', columns=['Turns'])
        df.index.name = 'Component'
        
        # Sort by component type for better readability
        component_order = [
            'anode_a_side_coating_turns',
            'anode_current_collector_turns', 
            'anode_b_side_coating_turns',
            'cathode_a_side_coating_turns',
            'cathode_current_collector_turns',
            'cathode_b_side_coating_turns',
            'bottom_separator_turns',
            'bottom_separator_inner_turns',
            'bottom_separator_outer_turns',
            'top_separator_turns',
            'top_separator_inner_turns',
            'top_separator_outer_turns'
        ]
        
        # Reorder DataFrame according to component_order, keeping any additional components at the end
        existing_components = [comp for comp in component_order if comp in df.index]
        additional_components = [comp for comp in df.index if comp not in component_order]
        ordered_index = existing_components + additional_components
        
        return df.reindex(ordered_index)

    @property
    def spiral(self) -> pd.DataFrame:
        """Return the spiral as a pandas DataFrame.

        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        spiral = self._spiral
        return self._format_np_spiral_for_df(spiral)

    @property
    def spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("spiral", "black", "Spiral")

    @property
    def top_separator_spiral(self) -> pd.DataFrame:
        """Return the top separator spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        ts_spiral = self._component_spirals.get("top_separator")
        return self._format_np_spiral_for_df(ts_spiral)

    @property
    def bottom_separator_spiral(self) -> pd.DataFrame:
        """Return the bottom separator spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        bs_spiral = self._component_spirals.get("bottom_separator")
        return self._format_np_spiral_for_df(bs_spiral)

    @property
    def anode_a_side_coating_spiral(self) -> pd.DataFrame:
        """Return the anode a-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        aasc_spiral = self._component_spirals.get("anode_a_side_coating")
        return self._format_np_spiral_for_df(aasc_spiral)

    @property
    def anode_current_collector_spiral(self) -> pd.DataFrame:
        """Return the anode current collector spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        acc_spiral = self._component_spirals.get("anode_current_collector")
        return self._format_np_spiral_for_df(acc_spiral)
    
    @property
    def anode_b_side_coating_spiral(self) -> pd.DataFrame:
        """Return the anode b-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        absc_spiral = self._component_spirals.get("anode_b_side_coating")
        return self._format_np_spiral_for_df(absc_spiral)
    
    @property
    def cathode_a_side_coating_spiral(self) -> pd.DataFrame:
        """Return the cathode a-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        casc_spiral = self._component_spirals.get("cathode_a_side_coating")
        return self._format_np_spiral_for_df(casc_spiral)

    @property
    def cathode_current_collector_spiral(self) -> pd.DataFrame:
        """Return the cathode current collector spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        ccc_spiral = self._component_spirals.get("cathode_current_collector")
        return self._format_np_spiral_for_df(ccc_spiral)
    
    @property
    def cathode_b_side_coating_spiral(self) -> pd.DataFrame:
        """Return the cathode b-side coating spiral as a pandas DataFrame.
        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        cbsc_spiral = self._component_spirals.get("cathode_b_side_coating")
        return self._format_np_spiral_for_df(cbsc_spiral)

    @property
    def top_separator_extruded_spiral(self) -> pd.DataFrame:
        ts_extruded_spiral = self._extruded_spirals.get("top_separator")
        return self._format_np_spiral_for_df(ts_extruded_spiral)

    @property
    def bottom_separator_extruded_spiral(self) -> pd.DataFrame:
        bs_extruded_spiral = self._extruded_spirals.get("bottom_separator")
        return self._format_np_spiral_for_df(bs_extruded_spiral)

    @property
    def anode_a_side_coating_extruded_spiral(self) -> pd.DataFrame:
        aasc_extruded_spiral = self._extruded_spirals.get("anode_a_side_coating")
        return self._format_np_spiral_for_df(aasc_extruded_spiral)
    
    @property
    def anode_current_collector_extruded_spiral(self) -> pd.DataFrame:
        acc_extruded_spiral = self._extruded_spirals.get("anode_current_collector")
        return self._format_np_spiral_for_df(acc_extruded_spiral)
    
    @property
    def anode_b_side_coating_extruded_spiral(self) -> pd.DataFrame:
        absc_extruded_spiral = self._extruded_spirals.get("anode_b_side_coating")
        return self._format_np_spiral_for_df(absc_extruded_spiral)

    @property
    def cathode_a_side_coating_extruded_spiral(self) -> pd.DataFrame:
        casc_extruded_spiral = self._extruded_spirals.get("cathode_a_side_coating")
        return self._format_np_spiral_for_df(casc_extruded_spiral)
    
    @property
    def cathode_current_collector_extruded_spiral(self) -> pd.DataFrame:
        ccc_extruded_spiral = self._extruded_spirals.get("cathode_current_collector")
        return self._format_np_spiral_for_df(ccc_extruded_spiral)
    
    @property
    def cathode_b_side_coating_extruded_spiral(self) -> pd.DataFrame:
        cbsc_extruded_spiral = self._extruded_spirals.get("cathode_b_side_coating")
        return self._format_np_spiral_for_df(cbsc_extruded_spiral)

    @property
    def top_separator_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("top_separator_spiral", self.layup.top_separator.material._color, f"Top Separator")
    
    @property
    def bottom_separator_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("bottom_separator_spiral", self.layup.bottom_separator.material._color, f"Bottom Separator")
    
    @property
    def anode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_a_side_coating_spiral", self.layup.anode.formulation._color, f"Anode a-side Coating")
    
    @property
    def anode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_current_collector_spiral", self.layup.anode.current_collector.material._color, f"Anode Current Collector")
    
    @property
    def anode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("anode_b_side_coating_spiral", self.layup.anode.formulation._color, f"Anode b-side Coating")
    
    @property
    def cathode_a_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_a_side_coating_spiral", self.layup.cathode.formulation._color, f"Cathode a-side Coating")

    @property
    def cathode_current_collector_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_current_collector_spiral", self.layup.cathode.current_collector.material._color, f"Cathode Current Collector")
    
    @property
    def cathode_b_side_coating_spiral_trace(self) -> go.Scatter:
        return self._format_spiral_trace("cathode_b_side_coating_spiral", self.layup.cathode.formulation._color, f"Cathode b-side Coating")
    
    @property
    def top_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("top_separator_extruded_spiral", self.layup.top_separator.material._color, f"Top Separator Extruded")

    @property
    def bottom_separator_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("bottom_separator_extruded_spiral", self.layup.bottom_separator.material._color, f"Bottom Separator Extruded")

    @property
    def anode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_a_side_coating_extruded_spiral", self.layup.anode.formulation._color, f"Anode a-side Coating Extruded")

    @property
    def anode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_current_collector_extruded_spiral", self.layup.anode.current_collector.material._color, f"Anode Current Collector Extruded")   

    @property
    def anode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("anode_b_side_coating_extruded_spiral", self.layup.anode.formulation._color, f"Anode b-side Coating Extruded")

    @property
    def cathode_a_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_a_side_coating_extruded_spiral", self.layup.cathode.formulation._color, f"Cathode a-side Coating Extruded")
    
    @property
    def cathode_current_collector_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_current_collector_extruded_spiral", self.layup.cathode.current_collector.material._color, f"Cathode Current Collector Extruded")
    
    @property
    def cathode_b_side_coating_extruded_spiral_trace(self) -> go.Scatter:
        return self._format_extruded_spiral_trace("cathode_b_side_coating_extruded_spiral", self.layup.cathode.formulation._color, f"Cathode b-side Coating Extruded")

    @property
    def mandrel(self) -> RoundMandrel | FlatMandrel:
        """Return the mandrel instance."""
        return self._mandrel

    @property
    def layup(self) -> Laminate:
        """Return the underlying `Laminate` instance."""
        return self._layup

    @property
    def total_layup_length(self) -> float:
        """Return the total length of the layup in mm."""
        return self.layup.total_length

    @mandrel.setter
    @calculate_all_properties
    def mandrel(self, value: RoundMandrel | FlatMandrel):
        self.validate_type(value, (RoundMandrel, FlatMandrel), "mandrel")
        self._mandrel = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: Laminate):

        # validate type
        self.validate_type(value, Laminate, "layup")
    
        # get the min x in the flattened center lines
        x_list = [c[:, 0] for c in value._flattened_center_lines.values()]
        min_x = min([np.min(mx) for mx in x_list])

        # get the most negative z value
        z_min = np.min(value._flattened_center_lines['cathode_b_side_coating'][:, 1]) # - value.cathode._coating_thickness

        # set the new x value
        new_x = (value.datum[0] * MM_TO_M) - min_x

        # set the new y value
        new_y = (value.datum[1] * MM_TO_M)

        # set the new z value
        new_z = (value.datum[2] * MM_TO_M) - z_min + value.cathode._coating_thickness / 2 + self.mandrel._radius

        # Convert back to mm and set the new datum
        value.datum = (new_x * M_TO_MM, new_y * M_TO_MM, new_z * M_TO_MM)

        # set to self
        self._layup = value


class WoundJellyRoll(_JellyRoll):
    """Wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: RoundMandrel
        ):

        super().__init__(
            laminate=laminate,
            mandrel=mandrel,
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_interfacial_area(self):
        """Calculate the interfacial area between cathode and anode surfaces in a wound jelly roll.
        
        Computes two interfacial surfaces:
        1. Inner surface: cathode b-side to anode a-side (first contact)
        2. Outer surface: cathode a-side to anode b-side (after one full rotation)
        
        Returns
        -------
        float
            Total interfacial area in m²
        """
        # Extract electrode coordinates
        cathode_coords = self._get_electrode_coordinates('cathode')
        anode_coords = self._get_electrode_coordinates('anode')
        
        # Calculate inner interfacial area (first contact)
        inner_area = self._calculate_inner_interface_area(
            cathode_coords['b_side'], anode_coords['a_side']
        )
        
        # Calculate outer interfacial area (after one full rotation)
        outer_area = self._calculate_outer_interface_area(
            cathode_coords['a_side'], anode_coords['b_side']
        )
        
        self._interfacial_area = inner_area + outer_area
        return self._interfacial_area
    
    def _get_electrode_coordinates(self, electrode_type: str) -> dict:
        """Extract electrode coating coordinates.
        
        Parameters
        ----------
        electrode_type : str
            Either 'cathode' or 'anode'
            
        Returns
        -------
        dict
            Dictionary with 'a_side' and 'b_side' coordinate arrays (2D)
        """
        electrode = getattr(self._layup, f'_{electrode_type}')
        current_collector = electrode._current_collector
        
        # Extract 2D coordinates (x, y plane)
        a_side_coords = current_collector._a_side_coated_coordinates[:, :2]
        b_side_coords = current_collector._b_side_coated_coordinates[:, :2]
        
        return {
            'a_side': a_side_coords,
            'b_side': b_side_coords
        }
    
    def _calculate_inner_interface_area(self, cathode_coords: np.ndarray, anode_coords: np.ndarray) -> float:
        """Calculate interfacial area for inner surface contact.
        
        Parameters
        ----------
        cathode_coords : np.ndarray
            Cathode b-side coordinates (2D)
        anode_coords : np.ndarray  
            Anode a-side coordinates (2D)
            
        Returns
        -------
        float
            Inner interfacial area in m²
        """
        cathode_polygon = Polygon(cathode_coords)
        anode_polygon = Polygon(anode_coords)
        
        intersection = cathode_polygon.intersection(anode_polygon)
        return intersection.area
    
    def _calculate_outer_interface_area(self, cathode_coords: np.ndarray, anode_coords: np.ndarray) -> float:
        """Calculate interfacial area for outer surface contact after one full rotation.
        
        Parameters
        ----------
        cathode_coords : np.ndarray
            Cathode a-side coordinates (2D)
        anode_coords : np.ndarray
            Anode b-side coordinates (2D)
            
        Returns
        -------
        float
            Outer interfacial area in m²
        """
        # Calculate cathode shift after one full rotation
        cathode_shift = self._calculate_full_rotation_shift()
        
        # Apply shift to cathode coordinates
        shifted_cathode_coords = cathode_coords + np.array([cathode_shift, 0])
        
        # Create polygons and calculate intersection
        shifted_cathode_polygon = Polygon(shifted_cathode_coords)
        anode_polygon = Polygon(anode_coords)
        
        intersection = shifted_cathode_polygon.intersection(anode_polygon)
        return intersection.area
    
    def _calculate_full_rotation_shift(self) -> float:
        """Calculate the x-direction shift after cathode completes one full rotation.
        
        Returns
        -------
        float
            Shift distance in meters
        """
        # Column indices for clarity
        THETA_COL = 0
        X_UNWRAPPED_COL = 1
        
        # Get cathode a-side spiral data
        cathode_spiral = self._component_spirals['cathode_a_side_coating']
        
        # Get starting position
        cathode_start_angle = cathode_spiral[0, THETA_COL]
        cathode_start_x = cathode_spiral[0, X_UNWRAPPED_COL]
        
        # Find point where cathode completes one full rotation (2π radians)
        full_rotation_angle = cathode_start_angle - 2 * np.pi
        rotation_indices = np.where(cathode_spiral[:, THETA_COL] <= full_rotation_angle)[0]
        
        # Get x position at full rotation
        cathode_full_rotation_x = cathode_spiral[rotation_indices[0], X_UNWRAPPED_COL]
        
        # Calculate shift distance
        return cathode_full_rotation_x - cathode_start_x
    
    def _calculate_geometry_parameters(self):
        
        radius_list = []

        # create the boundings surface
        for component_name, spiral_data in self._component_spirals.items():
            x_coords = spiral_data[:, 3]
            z_coords = spiral_data[:, 4]
            coords_2d = np.column_stack((x_coords, z_coords))
            polygon = Polygon(coords_2d)
            circle = minimum_bounding_circle(polygon)
            center = circle.centroid
            first_point = list(circle.exterior.coords)[0]
            radius = Point(center).distance(Point(first_point))
            radius_list.append(radius)

        self._radius = max(radius_list)
        self._diameter = self._radius * 2

        return self._radius, self._diameter

    def _calculate_variable_thickness_spiral(self, dtheta: float = 0.1) -> pd.DataFrame:
        """Integrate a variable-thickness Archimedean-like spiral (clockwise) with adaptive RK4.

        Governing relations (parametrized by θ, clockwise so θ decreases from π/2):
            dr/dθ = t(x) / (2π)
            ds/dθ = sqrt(r² + (dr/dθ)²)         (local arc length rate)
            dx_unwrapped/dθ = ds/dθ              (treat unwrapped length x as accumulated arc length)

        With spatially varying thickness t(x) provided by layup.get_thickness_at_x(x).

        Improvements over prior implementation:
            - 4th order Runge–Kutta integration for coupled (r, x) system.
            - Adaptive step sizing via local Richardson error estimate (1 step h vs 2 half-steps).
            - Automatic fallback to analytic uniform-thickness solution when thickness variation is negligible.
            - Gradient-aware minimum step to avoid under-resolving rapid thickness changes.
            - Early termination and endpoint interpolation to land exactly on total unwrapped length.
            - Conservative iteration / memory limits to avoid runaway loops.

        Parameters
        ----------
        dtheta : float
            Nominal (maximum) angular step magnitude (radians). Smaller steps are chosen adaptively as needed.

        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z]
        """
        total_length = self.layup._total_length  # meters
        r0 = self.mandrel._radius
        if total_length <= 0:
            self._spiral = np.array([[np.pi/2, 0.0, r0, r0 * 0.0, r0, 0.0]])  # Added turns column (0.0)
            return self._spiral

        # Build interpolation grid for thickness
        # Heuristic: finer where dtheta small or mandrel small
        base_dl = max(dtheta * r0 / 8.0, 0.00025)
        n_grid = min(6000, max(400, int(total_length / base_dl) + 2))
        x_grid = np.linspace(0.0, total_length, n_grid)
        t_grid = np.array([self.layup.get_thickness_at_x(x) for x in x_grid], dtype=float)
        t_min, t_max = float(t_grid.min()), float(t_grid.max())
        near_uniform = (t_max - t_min) < 1e-6 * max(1e-9, t_max)
        two_pi = 2.0 * np.pi

        def thickness_at(x):
            if x <= 0: return t_grid[0]
            if x >= total_length: return t_grid[-1]
            return float(np.interp(x, x_grid, t_grid))

        # Analytic fast path (uniform thickness)
        if near_uniform:
            t = (t_min + t_max) / 2.0
            k = t / two_pi  # dr/dθ
            # Solve s(θ) ≈ ((r0 + kθ)^2 - r0^2)/(2k) for θ_end where s = total_length
            if k > 0:
                theta_span = (np.sqrt(r0*r0 + 2*k*total_length) - r0) / k
            else:
                theta_span = 0.0
            # Choose number of steps so arc increment ~ dtheta*r scale
            n_steps = max(3, int(theta_span / dtheta) + 2)
            theta_arr = np.linspace(np.pi/2, np.pi/2 - theta_span, n_steps)
            dtheta_arr = -(theta_arr - theta_arr[0])  # not used directly, just for clarity
            # r(θ) = r0 + k(θ - θ_start) with θ_start=π/2
            delta = theta_arr - theta_arr[0]
            r_arr = r0 + k * delta
            # s(θ) relative to start: ((r)^2 - r0^2)/(2k)
            if k > 0:
                x_unwrapped_arr = ((r_arr**2 - r0**2) / (2*k))
            else:
                x_unwrapped_arr = np.zeros_like(r_arr)
            # Adjust sign (θ decreases for clockwise). Ensure monotonic x.
            # Trim / interpolate final
            if x_unwrapped_arr[-1] > total_length and len(x_unwrapped_arr) > 1:
                idx = np.searchsorted(x_unwrapped_arr, total_length)
                idx = min(max(idx, 1), len(x_unwrapped_arr)-1)
                x0, x1 = x_unwrapped_arr[idx-1], x_unwrapped_arr[idx]
                f = (total_length - x0)/(x1 - x0)
                theta_trim = theta_arr[idx-1] + f*(theta_arr[idx]-theta_arr[idx-1])
                r_trim = r_arr[idx-1] + f*(r_arr[idx]-r_arr[idx-1])
                theta_arr = np.concatenate([theta_arr[:idx], [theta_trim]])
                r_arr = np.concatenate([r_arr[:idx], [r_trim]])
                x_unwrapped_arr = np.concatenate([x_unwrapped_arr[:idx], [total_length]])
            
            # Calculate number of turns: cumulative rotations from start (theta decreases from π/2)
            theta_start = np.pi/2
            theta_traveled = theta_start - theta_arr  # Total angle traveled (positive)
            turns_arr = theta_traveled / (2 * np.pi)  # Number of complete turns
            
            x_coords = r_arr * np.cos(theta_arr)
            z_coords = r_arr * np.sin(theta_arr)
            self._spiral = np.column_stack([theta_arr, x_unwrapped_arr, r_arr, x_coords, z_coords, turns_arr])
            return self._spiral

        # Adaptive RK4 integration (θ decreases)
        # State: (r, x); derivatives w.r.t θ
        def deriv(r, x):
            tloc = thickness_at(x)
            dr_dth = tloc / two_pi
            ds_dth = np.sqrt(r*r + dr_dth*dr_dth)
            return dr_dth, ds_dth

        theta = np.pi/2  # start top
        r = r0
        x_unwrapped = 0.0
        h_max = abs(dtheta)
        h_min = h_max / 64.0
        target_err = 5e-5  # relative error target for x & r
        max_points = 120000
        max_iterations = 500000
        growth = 1.5
        shrink = 0.5

        theta_list = [theta]
        r_list = [r]
        x_list = [x_unwrapped]

        iterations = 0
        h = h_max
        # Pre-compute rough gradient to modulate minimal step
        dt_dx = np.gradient(t_grid, x_grid)
        max_grad = np.max(np.abs(dt_dx)) + 1e-12

        while x_unwrapped < total_length and iterations < max_iterations and len(theta_list) < max_points:
            iterations += 1
            # Clamp step not to overshoot total_length (rough estimate)
            # Predict ds ≈ r * h; adjust if would exceed remaining length by large margin
            remaining = total_length - x_unwrapped
            if r * h > 1.5 * remaining:
                h = max(remaining / (r + 1e-12), h_min)

            # Single RK4 full step size h
            dr1, dx1 = deriv(r, x_unwrapped)
            r2 = r + 0.5*h*dr1; x2 = x_unwrapped + 0.5*h*dx1
            dr2, dx2 = deriv(r2, x2)
            r3 = r + 0.5*h*dr2; x3 = x_unwrapped + 0.5*h*dx2
            dr3, dx3 = deriv(r3, x3)
            r4 = r + h*dr3; x4 = x_unwrapped + h*dx3
            dr4, dx4 = deriv(r4, x4)
            r_full = r + (h/6.0)*(dr1 + 2*dr2 + 2*dr3 + dr4)
            x_full = x_unwrapped + (h/6.0)*(dx1 + 2*dx2 + 2*dx3 + dx4)

            # Two half steps (h/2 + h/2)
            h2 = 0.5 * h
            # First half
            dr1h, dx1h = dr1, dx1  # same as above first evaluation
            r2h = r + 0.5*h2*dr1h; x2h = x_unwrapped + 0.5*h2*dx1h
            dr2h, dx2h = deriv(r2h, x2h)
            r3h = r + 0.5*h2*dr2h; x3h = x_unwrapped + 0.5*h2*dx2h
            dr3h, dx3h = deriv(r3h, x3h)
            r4h = r + h2*dr3h; x4h = x_unwrapped + h2*dx3h
            dr4h, dx4h = deriv(r4h, x4h)
            r_half = r + (h2/6.0)*(dr1h + 2*dr2h + 2*dr3h + dr4h)
            x_half = x_unwrapped + (h2/6.0)*(dx1h + 2*dx2h + 2*dx3h + dx4h)
            # Second half from (r_half, x_half)
            dr1s, dx1s = deriv(r_half, x_half)
            r2s = r_half + 0.5*h2*dr1s; x2s = x_half + 0.5*h2*dx1s
            dr2s, dx2s = deriv(r2s, x2s)
            r3s = r_half + 0.5*h2*dr2s; x3s = x_half + 0.5*h2*dx2s
            dr3s, dx3s = deriv(r3s, x3s)
            r4s = r_half + h2*dr3s; x4s = x_half + h2*dx3s
            dr4s, dx4s = deriv(r4s, x4s)
            r_two_half = r_half + (h2/6.0)*(dr1s + 2*dr2s + 2*dr3s + dr4s)
            x_two_half = x_half + (h2/6.0)*(dx1s + 2*dx2s + 2*dx3s + dx4s)

            # Error estimate (local): difference between full and two half steps (O(h^5))
            err_r = abs(r_full - r_two_half)
            err_x = abs(x_full - x_two_half)
            scale_r = max(abs(r), abs(r_two_half), 1e-9)
            scale_x = max(abs(x_unwrapped), abs(x_two_half), 1e-9)
            rel_err = max(err_r/scale_r, err_x/scale_x)

            if rel_err > target_err and h > h_min * 1.01:
                # Reject step, shrink and retry
                h = max(h * shrink * max(0.2, (target_err / (rel_err + 1e-14))**0.25), h_min)
                continue

            # Accept step -> use higher accuracy two half-steps solution
            r = r_two_half
            x_unwrapped = x_two_half
            theta -= h  # clockwise (θ decreasing)

            theta_list.append(theta)
            r_list.append(r)
            x_list.append(x_unwrapped)

            if rel_err < target_err / 8.0 and h < h_max / 0.6:
                h = min(h * growth * min(2.0, (target_err / (rel_err + 1e-14))**0.20), h_max)

            # Enforce minimal step if local thickness gradient high
            local_grad = abs(interp_grad := (np.interp(x_unwrapped, x_grid, dt_dx) if 0 < x_unwrapped < total_length else 0.0))
            grad_factor = 1.0 + 5.0 * (local_grad / max_grad)
            h = max(h / grad_factor, h_min)

        # Interpolate final point if overshoot
        if x_list[-1] > total_length and len(x_list) > 1:
            x_prev, x_curr = x_list[-2], x_list[-1]
            f = (total_length - x_prev)/(x_curr - x_prev + 1e-14)
            r_prev, r_curr = r_list[-2], r_list[-1]
            th_prev, th_curr = theta_list[-2], theta_list[-1]
            x_list[-1] = total_length
            r_list[-1] = r_prev + f*(r_curr - r_prev)
            theta_list[-1] = th_prev + f*(th_curr - th_prev)

        theta_arr = np.array(theta_list)
        x_unwrapped_arr = np.array(x_list)
        r_arr = np.array(r_list)

        # Calculate number of turns: cumulative rotations from start (theta decreases from π/2)
        theta_start = np.pi/2
        theta_traveled = theta_start - theta_arr  # Total angle traveled (positive)
        turns_arr = theta_traveled / (2 * np.pi)  # Number of complete turns

        x_coords = r_arr * np.cos(theta_arr)
        z_coords = r_arr * np.sin(theta_arr)
        self._spiral = np.column_stack([theta_arr, x_unwrapped_arr, r_arr, x_coords, z_coords, turns_arr])

        return self._spiral

    def _build_component_spirals(self):
        """Build component spirals by mapping flattened center lines onto the wound spiral.
        
        Optimized version that:
        - Pre-computes center line data for all components
        - Vectorizes height calculations
        - Reduces redundant array operations
        - Uses more efficient coordinate updates
        """
        self._component_spirals = {}
        
        # Component names in processing order
        component_names = [
            'bottom_separator', 'top_separator',
            'anode_a_side_coating', 'anode_current_collector', 'anode_b_side_coating',
            'cathode_a_side_coating', 'cathode_current_collector', 'cathode_b_side_coating'
        ]
        
        # Pre-compute all center line data to avoid repeated access
        center_line_data = {}
        for component_name in component_names:
            if component_name in self.layup._flattened_center_lines:
                center_line = self.layup._flattened_center_lines[component_name]
                center_line_data[component_name] = {
                    'x_coords': center_line[:, 0],
                    'z_coords': center_line[:, 1],
                    'x_min': np.min(center_line[:, 0]),
                    'x_max': np.max(center_line[:, 0])
                }
        
        # Cache the base spiral reference (avoid repeated copying)
        base_spiral = self._spiral
        mandrel_radius = self._mandrel._radius
        
        # Process each component
        for component_name in component_names:
            if component_name not in center_line_data:
                # Skip missing components with empty array
                self._component_spirals[component_name] = np.empty((0, 6))  # Updated to 6 columns
                continue
                
            cl_data = center_line_data[component_name]
            
            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, 1]  # Extract x_unwrapped column
            mask = (x_unwrapped >= cl_data['x_min']) & (x_unwrapped <= cl_data['x_max'])
            
            if not np.any(mask):
                # No spiral points in component range
                self._component_spirals[component_name] = np.empty((0, 6))  # Updated to 6 columns
                continue
            
            # Apply mask to get component spiral slice
            component_spiral = base_spiral[mask].copy()
            
            # Vectorized height calculation using numpy interpolation
            # This replaces the slow loop with a single vectorized operation
            x_vals = component_spiral[:, 1]
            z_unwrapped = np.interp(x_vals, cl_data['x_coords'], cl_data['z_coords'])
            height_adjustments = z_unwrapped - mandrel_radius
            
            # Update radius and coordinates in-place for efficiency
            component_spiral[:, 2] += height_adjustments  # Update radius
            
            # Vectorized coordinate recalculation
            theta_vals = component_spiral[:, 0]
            new_radii = component_spiral[:, 2]
            component_spiral[:, 3] = new_radii * np.cos(theta_vals)  # x coordinates
            component_spiral[:, 4] = new_radii * np.sin(theta_vals)  # z coordinates
            
            # Recalculate turns starting from 0 for this component
            theta_start_component = component_spiral[0, 0]  # Starting theta for this component
            theta_traveled_component = theta_start_component - component_spiral[:, 0]  # Angle traveled from component start
            component_spiral[:, 5] = theta_traveled_component / (2 * np.pi)  # Turns relative to component start
            
            self._component_spirals[component_name] = component_spiral

        return self._component_spirals

    def _build_extruded_component_spirals(self):
        """Build extruded component spirals by radially thickening center line spirals.
        
        For each component, creates a filled shape by:
        1. Taking the center line spiral from _component_spirals
        2. Creating outer spiral by adding thickness/2 to radius
        3. Creating inner spiral by subtracting thickness/2 from radius
        4. Reversing inner spiral direction for proper winding
        5. Combining outer + inner spirals into a closed filled shape
        
        Results stored in self._extruded_spirals for visualization.
        """
        self._extruded_spirals = {}

        component_thicknesses = {
            'top_separator': self.layup.top_separator._thickness,
            'anode_a_side_coating': self.layup.anode._coating_thickness,
            'anode_current_collector': self.layup.anode.current_collector._thickness,
            'anode_b_side_coating': self.layup.anode._coating_thickness,
            'bottom_separator': self.layup.bottom_separator._thickness,
            'cathode_a_side_coating': self.layup.cathode._coating_thickness,
            'cathode_current_collector': self.layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': self.layup.cathode._coating_thickness,
        }
        
        # Process each component that has a center line spiral
        for component_name, thickness in component_thicknesses.items():

            center_spiral = self._component_spirals[component_name]
            half_thickness = thickness / 2.0
            
            # Create outer spiral (center + thickness/2)
            outer_spiral = center_spiral.copy()
            outer_spiral[:, 2] += half_thickness  # Increase radius
            
            # Update outer spiral coordinates
            outer_spiral[:, 3] = outer_spiral[:, 2] * np.cos(outer_spiral[:, 0])  # x coordinates
            outer_spiral[:, 4] = outer_spiral[:, 2] * np.sin(outer_spiral[:, 0])  # z coordinates
            
            # Create inner spiral (center - thickness/2)
            inner_spiral = center_spiral.copy()
            inner_spiral[:, 2] -= half_thickness  # Decrease radius
            
            # Update inner spiral coordinates
            inner_spiral[:, 3] = inner_spiral[:, 2] * np.cos(inner_spiral[:, 0])  # x coordinates
            inner_spiral[:, 4] = inner_spiral[:, 2] * np.sin(inner_spiral[:, 0])  # z coordinates
            
            # Reverse inner spiral direction for proper winding (creates closed shape)
            inner_spiral_reversed = inner_spiral[::-1, :]
            
            # Add transition padding points to smooth spline interpolation
            # Duplicate end points to create smooth transitions
            outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))
            inner_start_padding = np.tile(inner_spiral_reversed[0, :], (2, 1))
            
            # Combine into filled shape: outer → padding → inner (reversed) → close
            if len(outer_spiral) > 0 and len(inner_spiral_reversed) > 0:
                filled_spiral = np.vstack([
                    outer_spiral,           # Outer boundary
                    outer_end_padding,      # Smooth transition
                    inner_start_padding,    # Smooth transition  
                    inner_spiral_reversed   # Inner boundary (reversed)
                ])
            else:
                # Fallback for edge cases
                filled_spiral = outer_spiral
            
            self._extruded_spirals[component_name] = filled_spiral

        return self._extruded_spirals

    @property
    def radius(self) -> float:
        """Return the outer radius of the wound jelly roll in mm."""
        return round(self._radius * M_TO_MM, 2)

    @property
    def diameter(self) -> float:
        """Return the outer diameter of the wound jelly roll in mm."""
        return round(self._diameter * M_TO_MM, 2)


class FlatWoundJellyRoll(_JellyRoll):
    """Flat wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel,
        ):

        super().__init__(
            laminate=laminate,
            mandrel=mandrel
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_interfacial_area(self):
        self._interfacial_area = 1
        return self._interfacial_area

    def _calculate_variable_thickness_spiral(self, ds_target: float = 0.5e-3) -> np.ndarray:
        """Calculate spiral path around flat mandrel with racetrack cross-section.
        
        The racetrack consists of:
        - Two semicircular ends (radius = height/2)
        - Two straight sections (length = width - height)
        
        Parameters
        ----------
        ds_target : float
            Target arc length step size in meters
            
        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z, turns]
        """
        total_length = self.layup._total_length  # meters
        mandrel_radius = self.mandrel._radius  # height/2
        straight_length = self.mandrel._straight_length  # width - height
        
        if total_length <= 0:
            # Return minimal spiral at starting position
            self._spiral = np.array([[0.0, 0.0, mandrel_radius, mandrel_radius, 0.0, 0.0]])
            return self._spiral
        
        # Calculate perimeter of one racetrack loop
        perimeter_base = 2 * np.pi * mandrel_radius + 2 * straight_length
        
        # Initialize arrays for spiral path
        positions = []
        x_unwrapped = 0.0
        accumulated_thickness = 0.0  # Track actual thickness buildup
        turn_count = 0.0
        
        # Start at top of right semicircle (theta=0 in racetrack coordinates)
        theta_racetrack = 0.0
        
        while x_unwrapped < total_length:
            # Get thickness at current unwrapped position
            thickness = self.layup.get_thickness_at_x(x_unwrapped)
            current_radius = mandrel_radius + accumulated_thickness
            
            # Calculate position on current racetrack
            x_pos, z_pos = self._racetrack_position(theta_racetrack, current_radius, straight_length)
            
            # Store position data
            positions.append([
                theta_racetrack,  # Parametric angle around racetrack
                x_unwrapped,      # Cumulative unwrapped length
                current_radius,   # Distance from center to current layer
                x_pos,           # Cartesian x coordinate
                z_pos,           # Cartesian z coordinate  
                turn_count       # Number of complete racetrack loops
            ])
            
            # Calculate step size based on local curvature and thickness
            curvature = self._racetrack_curvature(theta_racetrack, current_radius, straight_length)
            if curvature > 0:
                # On curved sections, limit step by curvature
                ds_max = min(ds_target, 0.1 / curvature)
            else:
                # On straight sections, use target step size
                ds_max = ds_target
            
            ds_actual = min(ds_max, total_length - x_unwrapped)
            
            # Calculate how much thickness to add based on this step
            # Thickness accumulation rate depends on perimeter
            perimeter_current = 2 * np.pi * current_radius + 2 * straight_length
            dtheta = ds_actual * (2 * np.pi) / perimeter_current
            
            # Add thickness proportional to angular progress
            thickness_increment = thickness * dtheta / (2 * np.pi)
            accumulated_thickness += thickness_increment
            
            theta_racetrack += dtheta
            x_unwrapped += ds_actual
            
            # Update turn count when completing full loops
            if theta_racetrack >= 2 * np.pi:
                full_turns = theta_racetrack // (2 * np.pi)
                turn_count += full_turns
                theta_racetrack = theta_racetrack % (2 * np.pi)
        
        # Convert to numpy array
        self._spiral = np.array(positions)
        return self._spiral
    
    def _racetrack_position(self, theta: float, radius: float, straight_length: float) -> tuple:
        """Calculate x,z position on racetrack at given parametric angle.
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π)
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (x_position, z_position) in meters
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate total perimeter proportions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        
        # Determine position based on parametric angle
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        if arc_length <= semi_arc_length:
            # Right semicircle (0 to π)
            phi = arc_length / radius  # Actual geometric angle
            x = straight_length/2 + radius * np.cos(phi - np.pi/2)
            z = radius * np.sin(phi - np.pi/2)
            
        elif arc_length <= semi_arc_length + straight_length:
            # Top straight section
            progress = (arc_length - semi_arc_length) / straight_length
            x = straight_length/2 - progress * straight_length
            z = radius
            
        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle (π to 2π)
            phi = (arc_length - semi_arc_length - straight_length) / radius
            x = -straight_length/2 + radius * np.cos(phi + np.pi/2)
            z = radius * np.sin(phi + np.pi/2)
            
        else:
            # Bottom straight section
            progress = (arc_length - 2 * semi_arc_length - straight_length) / straight_length
            x = -straight_length/2 + progress * straight_length
            z = -radius
        
        return x, z
    
    def _racetrack_curvature(self, theta: float, radius: float, straight_length: float) -> float:
        """Calculate curvature at given position on racetrack.
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π)
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        float
            Curvature (1/radius on curves, 0 on straight sections)
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate position fractions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        # Determine if on curved or straight section
        if (arc_length <= semi_arc_length or 
            (semi_arc_length + straight_length <= arc_length <= 2 * semi_arc_length + straight_length)):
            # On semicircular sections
            return 1.0 / radius if radius > 0 else 0.0
        else:
            # On straight sections
            return 0.0

    def _build_component_spirals(self):
        """Build component spirals by mapping flattened center lines onto the flat mandrel spiral.
        
        Key difference from cylindrical winding: height adjustments must be applied in the 
        correct direction based on position on the racetrack:
        - On flat sections (top/bottom): adjust z-coordinate directly
        - On curved sections (semicircles): adjust radially outward from local center
        """
        self._component_spirals = {}
        
        # Component names in processing order
        component_names = [
            'bottom_separator', 'top_separator',
            'anode_a_side_coating', 'anode_current_collector', 'anode_b_side_coating',
            'cathode_a_side_coating', 'cathode_current_collector', 'cathode_b_side_coating'
        ]
        
        # Pre-compute all center line data to avoid repeated access
        center_line_data = {}
        for component_name in component_names:
            if component_name in self.layup._flattened_center_lines:
                center_line = self.layup._flattened_center_lines[component_name]
                center_line_data[component_name] = {
                    'x_coords': center_line[:, 0],
                    'z_coords': center_line[:, 1],
                    'x_min': np.min(center_line[:, 0]),
                    'x_max': np.max(center_line[:, 0])
                }
        
        # Cache the base spiral reference and mandrel parameters
        base_spiral = self._spiral
        mandrel_radius = self._mandrel._radius
        straight_length = self._mandrel._straight_length
        
        # Process each component
        for component_name in component_names:
            if component_name not in center_line_data:
                # Skip missing components with empty array
                self._component_spirals[component_name] = np.empty((0, 6))
                continue
                
            cl_data = center_line_data[component_name]
            
            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, 1]  # Extract x_unwrapped column
            mask = (x_unwrapped >= cl_data['x_min']) & (x_unwrapped <= cl_data['x_max'])
            
            if not np.any(mask):
                # No spiral points in component range
                self._component_spirals[component_name] = np.empty((0, 6))
                continue
            
            # Apply mask to get component spiral slice
            component_spiral = base_spiral[mask].copy()
            
            # Vectorized height calculation using numpy interpolation
            x_vals = component_spiral[:, 1]
            z_unwrapped = np.interp(x_vals, cl_data['x_coords'], cl_data['z_coords'])
            height_adjustments = z_unwrapped - mandrel_radius
            
            # Apply height adjustments in correct direction based on racetrack position
            self._apply_flat_mandrel_height_adjustments(
                component_spiral, height_adjustments, mandrel_radius, straight_length
            )
            
            # Recalculate turns starting from 0 for this component
            theta_start_component = component_spiral[0, 0]  # Starting theta for this component
            theta_traveled_component = component_spiral[:, 0] - theta_start_component  # Angle traveled from component start
            component_spiral[:, 5] = theta_traveled_component / (2 * np.pi)  # Turns relative to component start
            
            self._component_spirals[component_name] = component_spiral

        return self._component_spirals
    
    def _apply_flat_mandrel_height_adjustments(self, spiral: np.ndarray, height_adjustments: np.ndarray, 
                                             mandrel_radius: float, straight_length: float):
        """Apply height adjustments to spiral points based on their position on the racetrack.
        
        Parameters
        ----------
        spiral : np.ndarray
            Component spiral array (modified in-place)
        height_adjustments : np.ndarray
            Height adjustments to apply at each point
        mandrel_radius : float
            Radius of the semicircular ends
        straight_length : float
            Length of straight sections
        """
        # Process each point to determine adjustment direction
        for i in range(len(spiral)):
            current_x = spiral[i, 3]  # Current x position
            current_z = spiral[i, 4]  # Current z position
            height_adj = height_adjustments[i]
            
            # Determine position type and adjustment direction based on actual coordinates
            adjustment_vector = self._get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Apply height adjustment in the correct direction
            new_x = current_x + height_adj * adjustment_vector[0]
            new_z = current_z + height_adj * adjustment_vector[1]
            
            # Update spiral coordinates
            spiral[i, 3] = new_x  # x coordinate
            spiral[i, 4] = new_z  # z coordinate
            
            # Update effective radius (distance from origin)
            spiral[i, 2] = np.sqrt(new_x**2 + new_z**2)
    
    def _get_height_adjustment_direction(self, theta: float, radius: float, straight_length: float,
                                       mandrel_radius: float) -> np.ndarray:
        """Get the direction vector for height adjustment at a given racetrack position.
        
        Parameters
        ----------
        theta : float
            Parametric angle around racetrack
        radius : float
            Current radius at this position
        straight_length : float
            Length of straight sections
        mandrel_radius : float
            Radius of semicircular ends
            
        Returns
        -------
        np.ndarray
            Unit vector [dx, dz] indicating direction for height adjustment
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate position fractions to determine section
        semi_arc_length = np.pi * mandrel_radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        if arc_length <= semi_arc_length:
            # Right semicircle: radial direction outward from right center
            phi = arc_length / mandrel_radius  # Actual geometric angle
            center_x = straight_length / 2
            center_z = 0.0
            # Unit vector pointing outward from semicircle center
            direction_x = np.cos(phi - np.pi/2)
            direction_z = np.sin(phi - np.pi/2)
            
        elif arc_length <= semi_arc_length + straight_length:
            # Top straight section: directly upward (positive z)
            direction_x = 0.0
            direction_z = 1.0
            
        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle: radial direction outward from left center
            phi = (arc_length - semi_arc_length - straight_length) / mandrel_radius
            center_x = -straight_length / 2
            center_z = 0.0
            # Unit vector pointing outward from semicircle center
            direction_x = np.cos(phi + np.pi/2)
            direction_z = np.sin(phi + np.pi/2)
            
        else:
            # Bottom straight section: directly downward (negative z)
            direction_x = 0.0
            direction_z = -1.0
        
        return np.array([direction_x, direction_z])

    def _get_coordinate_based_adjustment_direction(self, x: float, z: float, mandrel_radius: float,
                                                 straight_length: float) -> np.ndarray:
        """Get the direction vector for height adjustment based on actual coordinates.
        
        This method determines the adjustment direction by analyzing the actual position
        rather than using parametric angles, which avoids bunching issues on curved sections.
        
        Parameters
        ----------
        x : float
            Current x coordinate
        z : float
            Current z coordinate  
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        np.ndarray
            Unit vector [dx, dz] indicating direction for height adjustment
        """
        # Define the centers of the semicircular ends
        right_center_x = straight_length / 2
        left_center_x = -straight_length / 2
        center_z = 0.0
        
        # Tolerance for determining if we're on a straight section
        straight_tolerance = mandrel_radius * 0.1
        
        # Check if we're on the right semicircle
        if x > (straight_length / 2 - straight_tolerance):
            # Distance from right semicircle center
            dx_from_center = x - right_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from right center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # Check if we're on the left semicircle
        elif x < (-straight_length / 2 + straight_tolerance):
            # Distance from left semicircle center
            dx_from_center = x - left_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from left center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # We're on a straight section
        else:
            if z > 0:
                # Top straight section: directly upward
                direction_x = 0.0
                direction_z = 1.0
            else:
                # Bottom straight section: directly downward
                direction_x = 0.0
                direction_z = -1.0
        
        return np.array([direction_x, direction_z])

    def _build_extruded_component_spirals(self):
        """Build extruded component spirals for flat mandrel by applying thickness in correct directions.
        
        For each component, creates a filled shape by:
        1. Taking the center line spiral from _component_spirals
        2. Creating outer spiral by adding thickness/2 in the correct direction
        3. Creating inner spiral by subtracting thickness/2 in the correct direction
        4. Reversing inner spiral direction for proper winding
        5. Combining outer + inner spirals into a closed filled shape
        
        Key difference from cylindrical: thickness is applied based on racetrack position:
        - On flat sections: thickness applied vertically (±z direction)
        - On curved sections: thickness applied radially from local semicircle center
        
        Results stored in self._extruded_spirals for visualization.
        """
        self._extruded_spirals = {}

        component_thicknesses = {
            'top_separator': self.layup.top_separator._thickness,
            'anode_a_side_coating': self.layup.anode._coating_thickness,
            'anode_current_collector': self.layup.anode.current_collector._thickness,
            'anode_b_side_coating': self.layup.anode._coating_thickness,
            'bottom_separator': self.layup.bottom_separator._thickness,
            'cathode_a_side_coating': self.layup.cathode._coating_thickness,
            'cathode_current_collector': self.layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': self.layup.cathode._coating_thickness,
        }
        
        # Cache mandrel parameters
        mandrel_radius = self._mandrel._radius
        straight_length = self._mandrel._straight_length
        
        # Process each component that has a center line spiral
        for component_name, thickness in component_thicknesses.items():
            center_spiral = self._component_spirals[component_name]
            
            if len(center_spiral) == 0:
                # Skip empty components
                self._extruded_spirals[component_name] = np.empty((0, 6))
                continue
                
            half_thickness = thickness / 2.0
            
            # Create outer and inner spirals with proper flat mandrel thickness application
            outer_spiral, inner_spiral = self._create_flat_mandrel_thickness_spirals(
                center_spiral, half_thickness, mandrel_radius, straight_length
            )
            
            # Reverse inner spiral direction for proper winding (creates closed shape)
            inner_spiral_reversed = inner_spiral[::-1, :]
            
            # Add transition padding points to smooth spline interpolation
            # Duplicate end points to create smooth transitions
            outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))
            inner_start_padding = np.tile(inner_spiral_reversed[0, :], (2, 1))
            
            # Combine into filled shape: outer → padding → inner (reversed) → close
            if len(outer_spiral) > 0 and len(inner_spiral_reversed) > 0:
                filled_spiral = np.vstack([
                    outer_spiral,           # Outer boundary
                    outer_end_padding,      # Smooth transition
                    inner_start_padding,    # Smooth transition  
                    inner_spiral_reversed   # Inner boundary (reversed)
                ])
            else:
                # Fallback for edge cases
                filled_spiral = outer_spiral
            
            self._extruded_spirals[component_name] = filled_spiral

        return self._extruded_spirals
    
    def _create_flat_mandrel_thickness_spirals(self, center_spiral: np.ndarray, half_thickness: float,
                                             mandrel_radius: float, straight_length: float) -> tuple:
        """Create outer and inner spirals by applying thickness in correct directions.
        
        Parameters
        ----------
        center_spiral : np.ndarray
            Center line spiral coordinates
        half_thickness : float
            Half of the component thickness
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (outer_spiral, inner_spiral) as numpy arrays
        """
        # Initialize outer and inner spirals
        outer_spiral = center_spiral.copy()
        inner_spiral = center_spiral.copy()
        
        # Process each point to apply thickness in correct direction
        for i in range(len(center_spiral)):
            current_x = center_spiral[i, 3]  # Current x position
            current_z = center_spiral[i, 4]  # Current z position
            
            # Get the direction vector for thickness application based on coordinates
            direction_vector = self._get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Calculate outer position (center + half_thickness in direction)
            outer_x = center_spiral[i, 3] + half_thickness * direction_vector[0]
            outer_z = center_spiral[i, 4] + half_thickness * direction_vector[1]
            
            # Calculate inner position (center - half_thickness in direction)
            inner_x = center_spiral[i, 3] - half_thickness * direction_vector[0]
            inner_z = center_spiral[i, 4] - half_thickness * direction_vector[1]
            
            # Update outer spiral
            outer_spiral[i, 3] = outer_x
            outer_spiral[i, 4] = outer_z
            outer_spiral[i, 2] = np.sqrt(outer_x**2 + outer_z**2)  # Update effective radius
            
            # Update inner spiral
            inner_spiral[i, 3] = inner_x
            inner_spiral[i, 4] = inner_z
            inner_spiral[i, 2] = np.sqrt(inner_x**2 + inner_z**2)  # Update effective radius
        
        return outer_spiral, inner_spiral



class _Stack(_ElectrodeAssembly):
    """Stack electrode assembly.

    Accepts a `MonoLayer` or `ZFoldMonoLayer` layup representing stacked sheets.
    """
    def __init__(
            self, 
            layup: MonoLayer | ZFoldMonoLayer,
            n_layers: int = 1
        ):

        super().__init__(layup)
        self.n_layers = n_layers

    def _calculate_all_properties(self):
        self._calculate_stack()
        super()._calculate_all_properties()

    def _calculate_stack(self):
        
        # Initialize dictionaries for components
        stack = {}

        # set the starting z datum
        z_datum = 0

        # add bottom separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)

        # add anode to stack
        z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add layups to stack
        for _ in range(self.n_layers):
            z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._cathode, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add top separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._top_separator, z_datum)

        self._stack = stack

        return self._stack

    def _calculate_interfacial_area(self):
        
        # set the z tolerance
        z_tol = 1e-8

        # get the anode polygon
        _anode_coords = self._layup._anode._a_side_coating_coordinates
        _max_z = np.max(_anode_coords[:, 2])
        _top_anode_coords = _anode_coords[np.abs(_anode_coords[:, 2] - _max_z) < z_tol][:, :2]
        _anode_polygon = Polygon(_top_anode_coords)

        # get the cathode polygon
        _cathode_coords = self._layup._cathode._a_side_coating_coordinates
        _max_z = np.max(_cathode_coords[:, 2])
        _top_cathode_coords = _cathode_coords[np.abs(_cathode_coords[:, 2] - _max_z) < z_tol][:, :2]
        _cathode_polygon = Polygon(_top_cathode_coords)

        # calculate the intersection
        intersection_polygon = _anode_polygon.intersection(_cathode_polygon)

        # overlapping area
        _single_layer_interfacial_area = intersection_polygon.area

        # calculate the number of interfaces
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]       
        n_interfaces = len(cathodes) * 2

        # calculate total interfacial area
        self._interfacial_area = _single_layer_interfacial_area * n_interfaces

        return self._interfacial_area

    def _calculate_mass_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._mass = sum([a._mass for a in anodes]) + sum([c._mass for c in cathodes]) + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "mass"),
            "Cathodes": self.sum_breakdowns(cathodes, "mass"),
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._cost = sum([a._cost for a in anodes]) + sum([c._cost for c in cathodes]) + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "cost"),
            "Cathodes": self.sum_breakdowns(cathodes, "cost"),
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    def get_side_view(self, **kwargs):

        figure = go.Figure()

        for _, component in self.stack.items():
            layer_figure = component.get_right_left_view()
            legend_group = component.__class__.__name__
            for trace in layer_figure.data:
                trace.legendgroup = legend_group
                trace.name = legend_group
                trace.showlegend = True if legend_group not in [t.legendgroup for t in figure.data] else False
                # Set line width to 0.5
                if hasattr(trace, 'line') and trace.line is not None:
                    trace.line.width = 0.5
                figure.add_trace(trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @staticmethod
    def add_layer(stack: Dict, component, z_datum):

        stack_size = len(stack)

        new_component = deepcopy(component)

        if stack_size == 0:
            new_z_datum = z_datum + new_component._thickness * M_TO_MM / 2
        else:
            new_z_datum = z_datum + new_component._thickness * M_TO_MM / 2 + stack[stack_size - 1]._thickness * M_TO_MM / 2

        new_component.datum = (new_component._datum[0] * M_TO_MM, new_component._datum[1] * M_TO_MM, new_z_datum)
        stack_size = len(stack)
        stack[stack_size] = new_component

        return new_z_datum, stack

    @property
    def stack(self) -> dict:
        """Return the stack of components."""
        return self._stack

    @property
    def n_layers(self) -> int:
        """Return the number of layers in the stack."""
        return self._n_layers
    
    @n_layers.setter
    @calculate_all_properties
    def n_layers(self, value: int):
        self.validate_positive_int(value, "n_layers")
        self._n_layers = value


class ZFoldStack(_Stack):
    """Z-Fold stack electrode assembly.

    Accepts a `ZFoldMonoLayer` layup representing stacked sheets in a Z-fold configuration.
    """
    def __init__(
            self, 
            layup: ZFoldMonoLayer,
            n_layers: int,
            additional_separator_wraps: float = 1
        ):

        super().__init__(
            layup,
            n_layers
        )

        self.additional_separator_wraps = additional_separator_wraps

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_stack(self):

        # get bottom and top separator layers
        bottom_separator = deepcopy(self.layup._bottom_separator)
        top_separator = deepcopy(self.layup._top_separator)

        # estimate thickness of stack
        thickness = (
            self.n_layers * self.layup.cathode._thickness + \
            (self.n_layers + 1) * self.layup.anode._thickness + \
            ((self.n_layers * 2 + 1) + 2 * self.additional_separator_wraps) * self.layup._bottom_separator._thickness
        ) * M_TO_MM

        # Initialize dictionaries for components
        stack = {}

        # set the starting z datum
        z_datum = 0

        # for each additional separator wrap, add a separator to bottom
        for _ in range(self._additional_separator_wraps):
            bottom_separator_copy = deepcopy(bottom_separator)
            bottom_separator.length = bottom_separator.length + thickness
            z_datum, stack = self.add_layer(stack, bottom_separator_copy, z_datum)

        # add bottom separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)

        # add anode to stack
        z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add layups to stack
        for _ in range(self.n_layers):
            z_datum, stack = self.add_layer(stack, bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._cathode, z_datum)
            z_datum, stack = self.add_layer(stack, top_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add top separator to stack
        z_datum, stack = self.add_layer(stack, top_separator, z_datum)

        # for each additional separator wrap, add a separator to top
        for _ in range(self._additional_separator_wraps):
            top_separator_copy = deepcopy(top_separator)
            top_separator.length = top_separator.length + thickness
            z_datum, stack = self.add_layer(stack, top_separator_copy, z_datum)

        self._stack = stack

        return self._stack

    def _calculate_mass_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._mass = sum([a._mass for a in anodes]) + sum([c._mass for c in cathodes]) + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "mass"),
            "Cathodes": self.sum_breakdowns(cathodes, "mass"),
            "Separator": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._cost = sum([a._cost for a in anodes]) + sum([c._cost for c in cathodes]) + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "cost"),
            "Cathodes": self.sum_breakdowns(cathodes, "cost"),
            "Separator": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    @property
    def additional_separator_wraps(self) -> int:
        """Return the number of additional separator wraps."""
        return self._additional_separator_wraps

    @property
    def layup(self) -> ZFoldMonoLayer:
        """Return the underlying `ZFoldMonoLayer` instance."""
        return self._layup

    @additional_separator_wraps.setter
    @calculate_bulk_properties
    def additional_separator_wraps(self, value: float):
        self.validate_positive_float(value, "additional_separator_wraps")
        self._additional_separator_wraps = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: ZFoldMonoLayer):
        self.validate_type(value, ZFoldMonoLayer, "layup")
        self._layup = value


class PunchedStack(_Stack):
    """Mono-layer stack electrode assembly.

    Accepts a `MonoLayer` layup representing stacked sheets in a mono-layer configuration.
    """
    def __init__(
            self, 
            layup: MonoLayer,
            n_layers: int
        ):

        super().__init__(
            layup,
            n_layers
        )

        self._calculate_all_properties()
        self._update_properties = True
    
    @property
    def layup(self) -> MonoLayer:
        """Return the underlying `MonoLayer` instance."""
        return self._layup

    @layup.setter
    @calculate_all_properties
    def layup(self, value: MonoLayer):
        self.validate_type(value, MonoLayer, "layup")
        self._layup = value



