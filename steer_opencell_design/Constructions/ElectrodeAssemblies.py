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

    def get_spiral_plot(self, layered: bool = True ,**kwargs) -> go.Figure:

        fig = go.Figure()

        if layered:
            fig.add_trace(self.top_separator_spiral_trace)
            fig.add_trace(self.anode_a_side_coating_spiral_trace)
            fig.add_trace(self.anode_current_collector_spiral_trace)
            fig.add_trace(self.anode_b_side_coating_spiral_trace)
            fig.add_trace(self.bottom_separator_spiral_trace)
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

    def _calculate_roll(self):
        """Public entry to generate variable-thickness winding spiral."""
        self._calculate_variable_thickness_spiral()
        self._build_layered_spiral()
        self._calculate_spiral_properties()

    def _calculate_spiral_properties(self):
        self._calculate_interfacial_area()
        self._calculate_radius()

    def _calculate_interfacial_area(self):

        # calculate the inner surface, cathode-a-side to anode-b-side
        # cathode-a-side
        cathode_b_side_coordinates = self._layup._cathode._current_collector._b_side_coated_coordinates[:, :2]
        cathode_b_side_polygon = Polygon(cathode_b_side_coordinates)

        # anode-b-side
        anode_a_side_coordinates = self._layup._anode._current_collector._a_side_coated_coordinates[:, :2]
        anode_a_side_polygon = Polygon(anode_a_side_coordinates)

        # intersection area
        inner_area = cathode_b_side_polygon.intersection(anode_a_side_polygon).area


        # calculate the outer surface, cathode-b-side to anode-a-side
        # cathode-b-side
        cathode_a_side_coordinates = self._layup._cathode._current_collector._a_side_coated_coordinates[:, :2]

        # get the x_unfolded at which the cathode has done one full rotation
        cathode_a_side_spiral = self._component_spirals['cathode_a_side_coating']
        cathode_start_angle = cathode_a_side_spiral[0, 0]
        cathode_start_x = cathode_a_side_spiral[0, 1]
        cathode_full_rotation_index = np.where(cathode_a_side_spiral[:, 0] <= cathode_start_angle - 2 * np.pi)[0]
        cathode_full_rotation_x = cathode_a_side_spiral[cathode_full_rotation_index[0], 1]
        cathode_shift = cathode_full_rotation_x - cathode_start_x

        # shift cathode a side polygon in +x direction by cathode_shift
        shifted_cathode_a_side_coordinates = cathode_a_side_coordinates + np.array([cathode_shift, 0])
        shifted_cathode_a_side_polygon = Polygon(shifted_cathode_a_side_coordinates)

        # anode-a-side
        anode_b_side_coordinates = self._layup._anode._current_collector._b_side_coated_coordinates[:, :2]
        anode_b_side_polygon = Polygon(anode_b_side_coordinates)

        # get the overlap
        outer_area = shifted_cathode_a_side_polygon.intersection(anode_b_side_polygon).area

        self._interfacial_area = inner_area + outer_area
        
        return self._interfacial_area
    
    def _calculate_radius(self):
        
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

        self._radiues = max(radius_list)
        self._diameter = self._radiues * 2

        return self._radiues, self._diameter

    def _calculate_variable_thickness_spiral(self, dtheta: float = 0.1) -> pd.DataFrame:
        """Numerically integrate an Archimedean-style spiral (clockwise) using local thickness.

        Model:
            dr/dθ = t(x_current)/(2π)
            ds/dθ = √(r^2 + (dr/dθ)^2)
            x_unwrapped = ∫ ds

        Clockwise rotation:
            The spiral starts at θ = π/2 (12 o'clock position) and rotates clockwise by using negative angular increments.

        Local thickness:
            At each step we sample thickness at the current unwrapped length position.

        Parameters
        ----------
        dtheta : float
            Angular increment magnitude (radians) for numerical integration. Actual step is -dtheta (clockwise).

        Returns
        -------
        np.ndarray
            Array with columns matching DataFrame order:
            [theta, x_unwrapped, r, x, z]
        """
        # total unwrapped length of laminate (meters)
        total_length = self.layup._total_length

        # Precompute a coarse grid of thickness vs x for interpolation
        # spatial resolution heuristic (restore original logic)
        dl = max(dtheta * self.mandrel._radius / 10, 0.001)
        num_points = int(total_length / dl) + 2
        x_grid = np.linspace(0.0, total_length, num_points)
        t_grid = np.array([self.layup.get_thickness_at_x(x) for x in x_grid])

        # Estimate max iterations needed
        estimated_steps = int(2 * total_length / (dtheta * self.mandrel._radius)) + 100
        max_iterations = max(estimated_steps * 2, 1000)  # Safety factor
        
        # Pre-allocate arrays with estimated size (avoid list appending)
        theta_arr = np.zeros(max_iterations)
        x_unwrapped_arr = np.zeros(max_iterations)
        r_arr = np.zeros(max_iterations)
        
        # Initialize integration variables
        theta = np.pi / 2.0  # Start at 12 o'clock position (top)
        x_unwrapped = 0.0
        r = self.mandrel._radius
        dtheta_clockwise = -abs(dtheta)
        
        # Cache constants
        two_pi = 2 * np.pi
        pi_neg = -np.pi
        abs_dtheta = abs(dtheta_clockwise)
        
        # Set initial values
        theta_arr[0] = theta
        x_unwrapped_arr[0] = x_unwrapped
        r_arr[0] = r
        
        i = 0
        # Integrate until we reach or exceed total unwrapped length
        while x_unwrapped < total_length and i < max_iterations - 1:
            # Calculate look-ahead thickness (one half turn = π radians ahead)
            # Estimate the x-position after a half turn using current radius
            arc_look_ahead = pi_neg * r  
            x_lookahead = x_unwrapped + arc_look_ahead
            
            # Fast thickness lookup using numpy interpolation
            if x_lookahead <= 0:
                t_local = t_grid[0]
            elif x_lookahead >= total_length:
                t_local = t_grid[-1]
            else:
                t_local = np.interp(x_lookahead, x_grid, t_grid)
            
            dr_dtheta = t_local / two_pi
            # Advance radius using explicit Euler (small dθ keeps error low)
            r_next = r + dr_dtheta * abs_dtheta
            # Use average radius for arc-length increment for better accuracy
            r_avg = 0.5 * (r + r_next)
            ds = np.sqrt(r_avg**2 + dr_dtheta**2) * abs_dtheta
            x_next = x_unwrapped + ds
            theta_next = theta + dtheta_clockwise

            # Store values
            i += 1
            theta_arr[i] = theta_next
            x_unwrapped_arr[i] = x_next
            r_arr[i] = r_next

            # Update state
            theta = theta_next
            x_unwrapped = x_next
            r = r_next

        # Trim arrays to actual size
        actual_size = i + 1
        theta_arr = theta_arr[:actual_size]
        x_unwrapped_arr = x_unwrapped_arr[:actual_size]
        r_arr = r_arr[:actual_size]

        # If we overshot x_unwrapped beyond total_length, trim / interpolate final point
        if x_unwrapped_arr[-1] > total_length:
            x_prev = x_unwrapped_arr[-2]
            overshoot = x_unwrapped_arr[-1] - total_length
            segment_len = x_unwrapped_arr[-1] - x_prev
            frac = (segment_len - overshoot) / segment_len
            x_unwrapped_arr[-1] = total_length
            theta_arr[-1] = theta_arr[-2] + frac * dtheta_clockwise
            r_arr[-1] = r_arr[-2] + frac * (r_arr[-1] - r_arr[-2])

        # Vectorized coordinate calculations
        x_coords = r_arr * np.cos(theta_arr)
        z_coords = r_arr * np.sin(theta_arr)

        # Stack into single array (n,5)
        self._spiral = np.column_stack([
            theta_arr,
            x_unwrapped_arr,
            r_arr,
            x_coords,
            z_coords,
        ])

        return self._spiral

    def _build_layered_spiral(self):

        """Build layered spirals for components.

        Existing behavior:
            - Creates filled shapes (outer + inner + closure) for each component based on stacked thickness.

        Extension:
            - Also maps each component's flat center line (mid-thickness path along unwrapped length)
              onto the wound spiral. Center line radius at a given unwrapped length is:
                  r_center = r_spiral - (sum_thickness_below + component_thickness/2)
              where r_spiral is the spiral radius at that unwrapped length.

        Results stored in:
            self._component_spirals      (filled shapes: outer/inner)
            self._component_centerlines  (center line only)
        """
        self._component_spirals = {}

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

        def get_height_of_center_line(component_string: str, x_unwrapped: float) -> Tuple[float, float]:
            center_line = self.layup._flattened_center_lines[component_string]
            z_unwrapped = np.interp(x_unwrapped, center_line[:, 0], center_line[:, 1])
            height = z_unwrapped - self._mandrel._radius
            return height
        
        def get_range_of_center_line(component_string: str) -> Tuple[float, float]:
            center_line = self.layup._flattened_center_lines[component_string]
            min_x = np.min(center_line[:, 0])
            max_x = np.max(center_line[:, 0])
            return (min_x, max_x)
        
        def build_component_spiral(original_spiral: np.array, component_string: str):

            new_height_list = []

            # clip spiral to component length range
            min_x, max_x = get_range_of_center_line(component_string)
            mask = (original_spiral[:, 1] >= min_x) & (original_spiral[:, 1] <= max_x)
            original_spiral = original_spiral[mask]

            # get new heights along spiral
            for l in original_spiral[:, 1]:
                height = get_height_of_center_line(component_string, l)
                new_height_list.append(height)

            new_height_array = np.array(new_height_list)

            # adjust spiral radius to match component center line height
            original_spiral[:, 2] = original_spiral[:, 2] + new_height_array
            original_spiral[:, 3] = original_spiral[:, 2] * np.cos(original_spiral[:, 0])
            original_spiral[:, 4] = original_spiral[:, 2] * np.sin(original_spiral[:, 0])

            return original_spiral
        
        def build_and_extrude_component_spiral(component_string: str):

            component_spiral = build_component_spiral(self._spiral.copy(), component_string)
            
            # Handle empty spiral case
            if len(component_spiral) == 0:
                return np.empty((0, 5))  # Return empty array with correct shape
                
            thickness = component_thicknesses[component_string]

            # outer spiral
            outer_spiral = component_spiral.copy()
            outer_spiral[:, 2] = outer_spiral[:, 2] + thickness / 2
            outer_spiral[:, 3] = outer_spiral[:, 2] * np.cos(outer_spiral[:, 0])
            outer_spiral[:, 4] = outer_spiral[:, 2] * np.sin(outer_spiral[:, 0])

            # inner spiral
            inner_spiral = component_spiral.copy()
            inner_spiral[:, 2] = inner_spiral[:, 2] - thickness / 2
            inner_spiral[:, 3] = inner_spiral[:, 2] * np.cos(inner_spiral[:, 0])
            inner_spiral[:, 4] = inner_spiral[:, 2] * np.sin(inner_spiral[:, 0])

            # add padding points at transition to dampen spline interpolation
            # Only add padding if we have points to work with
            if len(outer_spiral) > 0:
                outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))  # duplicate last outer point
                inner_start_padding = np.tile(inner_spiral[-1, :], (2, 1))  # duplicate first inner point (after reverse)
                
                # combine outer and inner for filled shape with padding
                combined_spiral = np.vstack([
                    outer_spiral, 
                    outer_end_padding,
                    inner_start_padding,
                    inner_spiral[::-1, :]
                ])
            else:
                # Fallback for empty spirals
                combined_spiral = np.empty((0, 5))
                
            return combined_spiral

        self._component_spirals['bottom_separator'] = build_and_extrude_component_spiral('bottom_separator')
        self._component_spirals['top_separator'] = build_and_extrude_component_spiral('top_separator')
        self._component_spirals['anode_a_side_coating'] = build_and_extrude_component_spiral('anode_a_side_coating')
        self._component_spirals['anode_current_collector'] = build_and_extrude_component_spiral('anode_current_collector')
        self._component_spirals['anode_b_side_coating'] = build_and_extrude_component_spiral('anode_b_side_coating')
        self._component_spirals['cathode_a_side_coating'] = build_and_extrude_component_spiral('cathode_a_side_coating')
        self._component_spirals['cathode_current_collector'] = build_and_extrude_component_spiral('cathode_current_collector')
        self._component_spirals['cathode_b_side_coating'] = build_and_extrude_component_spiral('cathode_b_side_coating')

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
    def radius(self) -> float:
        """Return the outer radius of the wound jelly roll in mm."""
        return round(self._radiues * M_TO_MM, 2)

    @property
    def diameter(self) -> float:
        """Return the outer diameter of the wound jelly roll in mm."""
        return round(self._diameter * M_TO_MM, 2)

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
            name=f"Top Separator"
        )
    
    @property
    def bottom_separator_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="bottom_separator_spiral",
            fill_color=self.layup.bottom_separator.material._color,
            name=f"Bottom Separator"
        )
    
    @property
    def anode_a_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_a_side_coating_spiral",
            fill_color=self.layup.anode.formulation._color,
            name=f"Anode a-side Coating"
        )
    
    @property
    def anode_current_collector_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_current_collector_spiral",
            fill_color=self.layup.anode.current_collector.material._color,
            name=f"Anode Current Collector"
        )
    
    @property
    def anode_b_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="anode_b_side_coating_spiral",
            fill_color=self.layup.anode.formulation._color,
            name=f"Anode b-side Coating"
        )
    
    @property
    def cathode_a_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_a_side_coating_spiral",
            fill_color=self.layup.cathode.formulation._color,
            name=f"Cathode a-side Coating"
        )

    @property
    def cathode_current_collector_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_current_collector_spiral",
            fill_color=self.layup.cathode.current_collector.material._color,
            name=f"Cathode Current Collector"
        )
    
    @property
    def cathode_b_side_coating_spiral_trace(self) -> go.Scatter:

        return self._format_trace_property(
            property_name="cathode_b_side_coating_spiral",
            fill_color=self.layup.cathode.formulation._color,
            name=f"Cathode b-side Coating"
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



