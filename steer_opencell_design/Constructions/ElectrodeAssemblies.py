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
from shapely.geometry import Polygon
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

    def _calculate_bulk_properties(self):
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_mass_properties(self):
        pass

    def _calculate_cost_properties(self):
        pass

    def _calculate_interfacial_area(self):
        """Calculate interfacial area of the electrode assembly."""
        pass

    def _calcualate_full_cell_curve(self):
        """Calculate full cell voltage curve of the electrode assembly."""
        _full_cell_curve = deepcopy(self._layup._full_cell_curve)
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * self._interfacial_area
        self._full_cell_curve = _full_cell_curve
        return self._full_cell_curve
    
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
            title=kwargs.get("title", f"Areal Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Areal Capacity (mAh/cm²)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
        )

        return fig

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
                capacity=lambda x: x["capacity"] * (S_TO_H * A_TO_mA),
            )
            .rename(
                columns={
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                    "capacity": "Capacity (mAh)",
                }
            )
            .round(4)
        )
    
    @property
    def full_cell_curve_trace(self) -> go.Scatter:

        full_cell_color = "#ff8c00"

        return go.Scatter(
            x=self.full_cell_curve["Capacity (mAh)"],
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
            self
            .layup
            .anode
            .half_cell_curve
            .copy()
            .assign(capacity = lambda x: x["Areal Capacity (mAh/cm²)"] * self.interfacial_area,)
            .drop(columns=["Areal Capacity (mAh/cm²)"])
            .rename(columns={"capacity": "Capacity (mAh)"})
        )
    
    @property
    def anode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_half_cell_curve["Capacity (mAh)"],
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
            self
            .layup
            .cathode
            .half_cell_curve
            .copy()
            .assign(capacity = lambda x: x["Areal Capacity (mAh/cm²)"] * self.interfacial_area,)
            .drop(columns=["Areal Capacity (mAh/cm²)"])
            .rename(columns={"capacity": "Capacity (mAh)"})
        )
    
    @property
    def cathode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_half_cell_curve["Capacity (mAh)"],
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

        super().__init__(laminate)

        self.mandrel = mandrel

    def _calculate_all_properties(self):
        self._calculate_roll()
        super()._calculate_all_properties()

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

    def _center_laminate(self):
        # Determine mandrel radius based on mandrel type (round vs flat) to avoid forward class reference issues
        if isinstance(self.mandrel, RoundMandrel):
            _mandrel_radius = self.mandrel._radius
        else:  # FlatMandrel
            _mandrel_radius = self.mandrel._short_radius

        _current_x = self.layup._cathode._current_collector._datum[0]
        _current_y = self.layup._cathode._current_collector._datum[1]
        _current_z = self.layup._cathode._current_collector._datum[2]

        new_x = (_current_x - self.layup._start_position[0]) * M_TO_MM
        new_y = (_current_y - self.layup._start_position[1]) * M_TO_MM
        new_z = (_current_z - self.layup._start_position[2] + _mandrel_radius) * M_TO_MM

        self.layup.datum = (new_x, new_y, new_z)

        return self.layup

    def get_spiral_plot(self, layered: bool = True ,**kwargs) -> go.Figure:

        fig = go.Figure()

        if layered:
            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.cathode_a_side_coating_spiral_trace)
            fig.add_trace(self.cathode_current_collector_spiral_trace)
            fig.add_trace(self.cathode_b_side_coating_spiral_trace)

        else:
            fig.add_trace(self.spiral_trace)

        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            hovermode="closest",
        )

        return fig

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
        self.validate_type(value, Laminate, "layup")
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

    def _calculate_roll(self):
        """Public entry to generate variable-thickness winding spiral."""
        self._center_laminate()
        self._calculate_variable_thickness_spiral()
        self._build_layered_spiral()

    def _calculate_interfacial_area(self):
        self._interfacial_area = 1
        return 1

    def _calculate_variable_thickness_spiral(self, dtheta: float = 0.2) -> pd.DataFrame:
        """Numerically integrate an Archimedean-style spiral using a fixed one-full-turn thickness lookahead.

        Model:
            dr/dθ = t(x_future)/(2π)
            ds/dθ = √(r^2 + (dr/dθ)^2)
            x_unwrapped = ∫ ds

        Fixed lookahead:
            At each step we sample thickness at a future unwrapped length corresponding to one
            complete turn ahead: future_x = x_current + 2π r_current, clamped to total laminate length.
            This anticipatory thickness stabilizes early growth while remaining simple.

        Parameters
        ----------
        dtheta : float
            Angular increment (radians) for numerical integration.

        Returns
        -------
        np.ndarray
            Array with columns matching DataFrame order:
            [theta, x_unwrapped, r, x, z]
        """
        # total unwrapped length of laminate (meters)
        total_length = self.layup._total_length

        # Precompute a coarse grid of thickness vs x for interpolation
        dl = max(dtheta * self.mandrel._radius / 10, 0.001)  # spatial resolution heuristic
        num_points = int(total_length / dl) + 2
        x_grid = np.linspace(0.0, total_length, num_points)
        t_grid = np.array([self.layup._get_thickness_at_x(x)[0] for x in x_grid])

        # Interpolator for thickness (allow extrapolation clamp)
        def thickness_at(x: float) -> float:
            if x <= 0:
                return t_grid[0]
            if x >= total_length:
                return t_grid[-1]
            return float(np.interp(x, x_grid, t_grid))

        # Fixed one-turn lookahead thickness
        def thickness_full_turn_ahead(current_x: float, current_r: float) -> float:
            future_x = min(current_x + current_r * (2.0 * np.pi), total_length)
            return thickness_at(future_x)

        # Initialize integration variables
        theta = 0.0
        x_unwrapped = 0.0
        # initial radius uses one full-turn lookahead
        initial_thickness = thickness_full_turn_ahead(0.0, self.mandrel._radius + thickness_at(0.0))
        r = self.mandrel._radius + initial_thickness

        theta_list = [theta]
        x_list = [x_unwrapped]
        r_list = [r]
        # store the lookahead thickness used for this layer
        t_list = [initial_thickness]

        # Integrate until we reach or exceed total unwrapped length
        while x_unwrapped < total_length:
            # constant one-turn lookahead thickness
            t_local = thickness_full_turn_ahead(x_unwrapped, r)
            dr_dtheta = t_local / (2 * np.pi)
            # Advance radius using explicit Euler (small dθ keeps error low)
            r_next = r + dr_dtheta * dtheta
            # Use average radius for arc-length increment for better accuracy
            r_avg = 0.5 * (r + r_next)
            ds = np.sqrt(r_avg**2 + dr_dtheta**2) * dtheta
            x_next = x_unwrapped + ds
            theta_next = theta + dtheta

            # Append
            theta_list.append(theta_next)
            x_list.append(x_next)
            r_list.append(r_next)
            t_list.append(t_local)

            # Update state
            theta = theta_next
            x_unwrapped = x_next
            r = r_next

        # If we overshot x_unwrapped beyond total_length, trim / interpolate final point
        if x_list[-1] > total_length:
            x_prev = x_list[-2]
            overshoot = x_list[-1] - total_length
            segment_len = x_list[-1] - x_prev
            frac = (segment_len - overshoot) / segment_len
            x_list[-1] = total_length
            theta_list[-1] = theta_list[-2] + frac * dtheta
            r_list[-1] = r_list[-2] + frac * (r_list[-1] - r_list[-2])
        # Recompute final thickness using one-turn lookahead at trimmed position
        t_list[-1] = thickness_full_turn_ahead(x_list[-1], r_list[-1])

        # Convert lists to numpy arrays
        theta_arr = np.asarray(theta_list)
        x_unwrapped_arr = np.asarray(x_list)
        r_arr = np.asarray(r_list)
        x_arr = r_arr * np.cos(theta_arr)
        z_arr = r_arr * np.sin(theta_arr)

        # Stack into single array (n,9)
        self._spiral = np.column_stack([
            theta_arr,
            x_unwrapped_arr,
            r_arr,
            x_arr,
            z_arr,
        ])

        return self._spiral

    def _build_layered_spiral(self):

        """Build layered spirals for separator components."""

        component_thicknesses = {
            'ts': self.layup.top_separator._thickness,
            'aasc': self.layup.anode._coating_thickness,
            'acc': self.layup.anode.current_collector._thickness,
            'absc': self.layup.anode._coating_thickness,
            'bs': self.layup.bottom_separator._thickness,
            'casc': self.layup.cathode._coating_thickness,
            'ccc': self.layup.cathode.current_collector._thickness,
            'cbsc': self.layup.cathode._coating_thickness,
        }

        components_at_each_length = [
            self.layup._get_thickness_at_x(l)[1] for l in self._spiral[:, 1]
        ]

        def _component_spiral(comp_key: str) -> np.ndarray:
            """Return stacked (outer+inner+closure) spiral for a component key or empty array."""
            thickness_map = component_thicknesses.get
            rows = []
            above_list = []
            below_list = []
            for i, comps in enumerate(components_at_each_length):
                if comp_key not in comps:
                    continue
                idx = comps.index(comp_key)
                below_sum = 0.0
                for c in comps[:idx]:
                    below_sum += thickness_map(c, 0.0)
                rows.append(i)
                above_list.append(below_sum)
                below_list.append(below_sum + thickness_map(comp_key, 0.0))

            if not rows:
                return np.empty((0, self._spiral.shape[1]))

            rows_arr = np.asarray(rows, dtype=int)
            outer = self._spiral[rows_arr].copy()
            inner = outer.copy()

            above_arr = np.asarray(above_list, dtype=float)
            below_arr = np.asarray(below_list, dtype=float)

            # radius column index 2
            outer[:, 2] -= above_arr
            inner[:, 2] -= below_arr

            # recompute x,z columns 3,4
            theta_outer = outer[:, 0]
            r_outer = outer[:, 2]
            outer[:, 3] = r_outer * np.cos(theta_outer)
            outer[:, 4] = r_outer * np.sin(theta_outer)

            theta_inner = inner[:, 0]
            r_inner = inner[:, 2]
            inner[:, 3] = r_inner * np.cos(theta_inner)
            inner[:, 4] = r_inner * np.sin(theta_inner)

            # sort inner descending theta (optional symmetry)
            inner = inner[np.argsort(inner[:, 0])[::-1]]

            # --- Endpoint padding to damp spline overshoot ---
            # Duplicate first and last points several times to reduce Catmull-Rom bulging.
            pad_points = 5  # number of duplicate points at each end

            def _pad_endpoints(arr: np.ndarray, n: int) -> np.ndarray:
                if arr.shape[0] == 0 or n <= 0:
                    return arr
                first_block = np.repeat(arr[0:1, :], n, axis=0)
                last_block = np.repeat(arr[-1:, :], n, axis=0)
                return np.vstack([first_block, arr, last_block])

            outer_padded = _pad_endpoints(outer, pad_points)
            inner_padded = _pad_endpoints(inner, pad_points)

            stacked = np.vstack([outer_padded, inner_padded])

            # close shape
            closing_point = stacked[0].copy()
            stacked = np.vstack([stacked, closing_point])
            return stacked

        ts_spiral = _component_spiral('ts')
        bs_spiral = _component_spiral('bs')
        aasc_spiral = _component_spiral('aasc')
        acc_spiral = _component_spiral('acc')
        absc_spiral = _component_spiral('absc')
        casc_spiral = _component_spiral('casc')
        ccc_spiral = _component_spiral('ccc')
        cbsc_spiral = _component_spiral('cbsc')

        self._component_spirals = {
            "top_separator": ts_spiral,
            "bottom_separator": bs_spiral,
            "anode_a_side_coating": aasc_spiral,
            "anode_current_collector": acc_spiral,
            "anode_b_side_coating": absc_spiral,
            "cathode_a_side_coating": casc_spiral,
            "cathode_current_collector": ccc_spiral,
            "cathode_b_side_coating": cbsc_spiral,
        }

        return self._component_spirals

    @staticmethod
    def _format_np_spiral_for_df(np_array: np.ndarray) -> pd.DataFrame:
        """Format numpy spiral array into pandas DataFrame with proper units and column names.

        Columns: theta (degrees), x_unwrapped (mm), thickness (mm), r (mm), x (mm), y (mm)
        """
        return (
            pd
            .DataFrame(np_array, columns=["theta","length","r","x","z"])
            .assign(
                theta = lambda df: df["theta"] * (180.0 / PI),
                length = lambda df: df["length"] * M_TO_MM,
                r = lambda df: df["r"] * M_TO_MM,
                x = lambda df: df["x"] * M_TO_MM,
                z = lambda df: df["z"] * M_TO_MM,
            )
            .rename(
                columns={
                    "x": "X (mm)",
                    "z": "Z (mm)",
                    "r": "Radius (mm)",
                    "length": "Unwrapped Length (mm)",
                    "theta": "Theta (degrees)",
                }
            )
        )
    
    def _format_trace_property(self, property_name: str, fill_color: str, name: str) -> go.Scatter:
        
        df = getattr(self, property_name)

        return go.Scatter(
            x=df['X (mm)'],
            y=df['Z (mm)'],
            fillcolor=fill_color,
            fill='toself',
            mode='lines',
            line=dict(color='black', width=0.1),
            line_shape='spline',
            name=name
        )

    @property
    def spiral(self) -> pd.DataFrame:
        """Return the spiral as a pandas DataFrame.

        Columns: theta, x_unwrapped, thickness, r, x, y
        """
        spiral = self._spiral
        return self._format_np_spiral_for_df(spiral)

    @property
    def spiral_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.spiral['X (mm)'],
            y=self.spiral['Z (mm)'],
            mode='lines',
            line=dict(color='black', width=1),
            line_shape='spline',
            name="Spiral"
        )

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
    def top_separator_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="top_separator_spiral",
            fill_color=self.layup.top_separator.material._color,
            name=f"{self.layup.top_separator.name} (Top)"
        )
    
    @property
    def bottom_separator_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="bottom_separator_spiral",
            fill_color=self.layup.bottom_separator.material._color,
            name=f"{self.layup.bottom_separator.name} (Bottom)"
        )
    
    @property
    def anode_a_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_a_side_coating_spiral",
            fill_color=self.layup.anode.formulation._color,
            name=f"{self.layup.anode.name} (Anode Coating)"
        )
    
    @property
    def anode_current_collector_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_current_collector_spiral",
            fill_color=self.layup.anode.current_collector.material._color,
            name=f"{self.layup.anode.current_collector.name} (Anode CC)"
        )
    
    @property
    def anode_b_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_b_side_coating_spiral",
            fill_color=self.layup.anode.formulation._color,
            name=f"{self.layup.anode.name} (Anode Coating)"
        )
    
    @property
    def cathode_a_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_a_side_coating_spiral",
            fill_color=self.layup.cathode.formulation._color,
            name=f"{self.layup.cathode.name} (Cathode Coating)"
        )

    @property
    def cathode_current_collector_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_current_collector_spiral",
            fill_color=self.layup.cathode.current_collector.material._color,
            name=f"{self.layup.cathode.current_collector.name} (Cathode CC)"
        )
    
    @property
    def cathode_b_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_b_side_coating_spiral",
            fill_color=self.layup.cathode.formulation._color,
            name=f"{self.layup.cathode.name} (Cathode Coating)"
        )
    


class FlatWoundJellyRoll(_JellyRoll):
    """Flat wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel,
            mandrel_gap: float = 0.0
        ):

        super().__init__(
            laminate=laminate,
            mandrel=mandrel
        )

        self.mandrel_gap = mandrel_gap

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_roll(self):
        pass

    @property
    def mandrel_gap(self) -> float:
        """Return the mandrel gap in mm."""
        return round(self._mandrel_gap * M_TO_MM, 2)
    
    @mandrel_gap.setter
    @calculate_all_properties
    def mandrel_gap(self, value: float):
        self.validate_type(value, float, "mandrel_gap")
        self._mandrel_gap = value


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



