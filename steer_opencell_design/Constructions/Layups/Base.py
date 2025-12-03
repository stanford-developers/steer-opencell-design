from copy import copy, deepcopy
from enum import Enum
from typing import Tuple, TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from steer_core.Constants.Units import *
from steer_core.Decorators.Coordinates import calculate_volumes, calculate_coordinates
from steer_core.Decorators.General import calculate_all_properties

from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups.OverhangUtils import OverhangMixin

if TYPE_CHECKING:
    from steer_opencell_design.Constructions.Layups.Laminate import Laminate

# Module-level constants for overhang ranges and plotting parameters
PLOT_PADDING_FACTOR = 0.05  # 5% padding for plot bounds
CAPACITY_INTERPOLATION_POINTS = 100  # Number of points for capacity curve interpolation
PLOT_FALLBACK_BOUND = 100.0  # Fallback axis bounds in mm

# Separator range extension constants for Laminate validation
SEPARATOR_WIDTH_EXTENSION = 0.1  # Extension factor (10%) for separator width range
SEPARATOR_LENGTH_EXTENSION = 1.0  # Extension factor (100%) for separator length range

# Sampling resolution for flattened center line calculations
DEFAULT_X_SPACING = 0.004  # Default x-axis sampling spacing in meters (4mm)

# Thickness calculation fallback
THICKNESS_FALLBACK = 0.0  # Return value when thickness cannot be determined


class NPRatioControlMode(Enum):
    """Control modes for N/P ratio adjustments."""
    FIXED_ANODE = "fixed_anode"
    FIXED_CATHODE = "fixed_cathode"
    FIXED_THICKNESS = "fixed_thickness"


class _Layup(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin,
    PlotterMixin,
    OverhangMixin,
):
    """
    Base class for layup structures containing common functionality for overhang calculations
    and electrode positioning. This class provides the foundation for both MonoLayer and Laminate classes.

    This class handles:
    - Anode overhang calculations relative to cathode
    - Overhang control modes (FIXED_COMPONENT and FIXED_OVERHANGS)
    - Common properties and validation for electrode layup structures
    """

    def __init__(
        self,
        cathode: Cathode,
        bottom_separator: Separator,
        anode: Anode,
        top_separator: Separator,
        name: str = "Layup",
    ):
        """
        Initialize the base layup with anode and cathode components.

        Parameters
        ----------
        anode : Anode
            The anode component of the layup.
        cathode : Cathode
            The cathode component of the layup.
        name : str, optional
            Name of the layup (default: "Layup").
        """
        super().__init__()

        self._update_properties = False
        self._flipped_x = False
        self._flipped_y = False
        self._flipped_z = False

        self.np_ratio_control_mode = NPRatioControlMode.FIXED_ANODE

        self.cathode = cathode
        self.bottom_separator = bottom_separator
        self.anode = anode
        self.top_separator = top_separator
        self.name = name

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()
        self._calculate_areal_capacity_curves()

    def _calculate_bulk_properties(self):
        pass

    def _calculate_coordinates(self):
        self._set_z_positions()
        super()._calculate_coordinates()

    def _set_z_positions(self):

        _bottom_separator_z = self._cathode._current_collector._datum[2] + self._cathode._thickness / 2 + self._bottom_separator._thickness / 2
        _anode_z = _bottom_separator_z + self._bottom_separator._thickness / 2 + self._anode._thickness / 2
        _top_separator_z = _anode_z + self._anode._thickness / 2 + self._top_separator._thickness / 2

        self._bottom_separator.datum = (
            self._bottom_separator.datum[0],
            self._bottom_separator.datum[1],
            _bottom_separator_z * M_TO_MM,
        )

        self.anode.datum = (
            self.anode.datum[0],
            self.anode.datum[1],
            _anode_z * M_TO_MM,
        )

        self._top_separator.datum = (
            self._top_separator.datum[0],
            self._top_separator.datum[1],
            _top_separator_z * M_TO_MM,
        )

    def _calculate_areal_capacity_curves(self) -> np.ndarray:
        """
        Calculate the half-cell curves for the cathode and anode.

        Returns
        -------
        np.ndarray
            The combined half-cell curve for the full cell.
        """
        cathode_areal_capacity_curve = copy(self._cathode._areal_capacity_curve)
        anode_areal_capacity_curve = copy(self._anode._areal_capacity_curve)

        max_cap_cathode = max(cathode_areal_capacity_curve[:, 0])
        max_cap_anode = max(anode_areal_capacity_curve[:, 0])
        self._np_ratio = max_cap_anode / max_cap_cathode

        # Split cathode curves by direction (column 2: 0=discharge, 1=charge)
        cathode_charge = cathode_areal_capacity_curve[cathode_areal_capacity_curve[:, 2] == 1]
        cathode_discharge = cathode_areal_capacity_curve[cathode_areal_capacity_curve[:, 2] == -1]

        # Split anode curves by direction
        anode_charge = anode_areal_capacity_curve[anode_areal_capacity_curve[:, 2] == 1]
        anode_discharge = anode_areal_capacity_curve[anode_areal_capacity_curve[:, 2] == -1]

        # Calculate valid x range (column 0 is areal capacity)
        # For charge: find overlapping range (intersection)
        charge_x_min = max(cathode_charge[:, 0].min(), anode_charge[:, 0].min())
        charge_x_max = min(cathode_charge[:, 0].max(), anode_charge[:, 0].max())

        # For discharge: find overlapping range (intersection)
        discharge_x_min = max(cathode_discharge[:, 0].min(), anode_discharge[:, 0].min())
        discharge_x_max = min(cathode_discharge[:, 0].max(), anode_discharge[:, 0].max())
        # Create interpolation functions for voltage vs areal capacity

        # Sort by areal capacity for interpolation
        cathode_charge_sorted = cathode_charge[cathode_charge[:, 0].argsort()]
        cathode_discharge_sorted = cathode_discharge[cathode_discharge[:, 0].argsort()]
        anode_charge_sorted = anode_charge[anode_charge[:, 0].argsort()]
        anode_discharge_sorted = anode_discharge[anode_discharge[:, 0].argsort()]

        # Create common x arrays for interpolation
        n_points = CAPACITY_INTERPOLATION_POINTS  # Number of points for smooth curves
        charge_x_common = np.linspace(charge_x_min, charge_x_max, n_points)
        discharge_x_common = np.linspace(discharge_x_min, discharge_x_max, n_points)

        # Interpolate voltages using numpy.interp (voltage = column 1, areal capacity = column 0)
        cathode_charge_voltage = np.interp(charge_x_common, cathode_charge_sorted[:, 0], cathode_charge_sorted[:, 1])
        cathode_discharge_voltage = np.interp(
            discharge_x_common,
            cathode_discharge_sorted[:, 0],
            cathode_discharge_sorted[:, 1],
        )
        anode_charge_voltage = np.interp(charge_x_common, anode_charge_sorted[:, 0], anode_charge_sorted[:, 1])
        anode_discharge_voltage = np.interp(
            discharge_x_common,
            anode_discharge_sorted[:, 0],
            anode_discharge_sorted[:, 1],
        )

        # Calculate full-cell voltages (cathode - anode)
        charge_voltage_full = cathode_charge_voltage - anode_charge_voltage
        discharge_voltage_full = cathode_discharge_voltage - anode_discharge_voltage

        # Create full-cell arrays
        # Charge curve: ascending x order (direction = 1)
        charge_curve = np.column_stack(
            [
                charge_x_common,  # Column 0: areal capacity
                charge_voltage_full,  # Column 1: voltage
                np.ones(len(charge_x_common)),  # Column 2: direction (1 = charge)
            ]
        )

        # Discharge curve: descending x order (direction = -1)
        discharge_curve = np.column_stack(
            [
                discharge_x_common[::-1],  # Column 0: areal capacity (descending)
                discharge_voltage_full[::-1],  # Column 1: voltage
                -np.ones(len(discharge_x_common)),  # Column 2: direction (-1 = discharge)
            ]
        )

        # Recombine: charge first (ascending), then discharge (descending)
        self._areal_capacity_curve = np.vstack([charge_curve, discharge_curve])

        return self._areal_capacity_curve

    def _update_anode_ranges(self, cathode: Cathode):
        """Update anode current collector ranges based on cathode."""
        self._anode.current_collector.set_ranges_from_reference(cathode.current_collector)

    def _update_separator_sizes(self, cathode: Cathode):
        """Update separator dimensions to ensure proper coverage."""
        self._ensure_separator_coverage(self._bottom_separator, cathode, "bottom")
        if hasattr(self, '_top_separator') and self._top_separator is not None:
            self._ensure_separator_coverage(self._top_separator, cathode, "top")

    def _ensure_separator_coverage(self, separator: Separator, reference_electrode: Cathode, separator_name: str):
        """Ensure separator covers the reference electrode with thickness buffer."""
        thickness_buffer = separator._thickness * M_TO_MM
        
        if separator._rotated_xy:
            # When rotated, width maps to x-direction, length to y-direction
            required_width = reference_electrode.current_collector.x_body_length + thickness_buffer
            required_length = reference_electrode.current_collector.y_body_length + thickness_buffer
            
            if separator._width < reference_electrode.current_collector._x_body_length:
                new_separator = deepcopy(separator)
                new_separator.width = required_width
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
                
            if separator._length < reference_electrode.current_collector._y_body_length:
                new_separator = deepcopy(separator)
                new_separator.length = required_length
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
        else:
            # When not rotated, length maps to x-direction, width to y-direction
            required_length = reference_electrode.current_collector.x_body_length + thickness_buffer
            required_width = reference_electrode.current_collector.y_body_length + thickness_buffer
            
            if separator._length < reference_electrode.current_collector._x_body_length:
                new_separator = deepcopy(separator)
                new_separator.length = required_length
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
                
            if separator._width < reference_electrode.current_collector._y_body_length:
                new_separator = deepcopy(separator)
                new_separator.width = required_width
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator

    def _update_anode_dimensions(self, cathode: Cathode):
        """Update anode dimensions to match cathode if smaller."""
        anode_cc = self.anode.current_collector
        cathode_cc = cathode.current_collector
        
        # Check if x_body_length needs updating
        if anode_cc._x_body_length < cathode_cc._x_body_length:
            new_anode_current_collector = deepcopy(anode_cc)
            new_anode_current_collector.x_body_length = cathode_cc.x_body_length
            self.anode.current_collector = new_anode_current_collector
            
        # Check if y_body_length needs updating
        if anode_cc._y_body_length < cathode_cc._y_body_length:
            new_anode_current_collector = deepcopy(anode_cc)
            new_anode_current_collector.y_body_length = cathode_cc.y_body_length
            self.anode.current_collector = new_anode_current_collector

    def get_top_down_view(self, opacity: float = 0.5, **kwargs) -> go.Figure:

        # Validate opacity using ColorMixin
        self.validate_opacity(opacity)

        fig = go.Figure()

        # Get trace groups
        cathode_fig = self._cathode.get_top_down_view()

        # Check if separators have the same name and create distinct legend groups
        separators_same_name = self._bottom_separator.name == self._top_separator.name

        # Prepare all traces first
        cathode_traces = []
        for i, trace in enumerate(cathode_fig.data):
            trace.name = trace.name + " (Cathode)"
            trace.legendgroup = trace.name + " (Cathode)"
            # Use ColorMixin method to adjust trace opacity
            self.adjust_trace_opacity(trace, opacity)
            cathode_traces.append(trace)

        # Add bottom separator
        bottom_separator_trace = copy(self._bottom_separator.top_down_trace)
        if separators_same_name:
            bottom_separator_trace.name = f"{self._bottom_separator.name} (Bottom)"
            bottom_separator_trace.legendgroup = f"{self._bottom_separator.name}_bottom"
        else:
            bottom_separator_trace.name = f"{self._bottom_separator.name}"
            bottom_separator_trace.legendgroup = f"{self._bottom_separator.name}"
        # Use ColorMixin method to adjust trace opacity
        self.adjust_trace_opacity(bottom_separator_trace, opacity)

        anode_fig = self._anode.get_top_down_view()
        anode_traces = []
        for i, trace in enumerate(anode_fig.data):
            trace.name = trace.name + " (Anode)"
            trace.legendgroup = trace.name + " (Anode)"
            trace.xaxis = "x"
            trace.yaxis = "y"
            # Use ColorMixin method to adjust trace opacity
            self.adjust_trace_opacity(trace, opacity)
            anode_traces.append(trace)

        # Add top separator
        top_separator_trace = copy(self._top_separator.top_down_trace)
        if separators_same_name:
            top_separator_trace.name = f"{self._top_separator.name} (Top)"
            top_separator_trace.legendgroup = f"{self._top_separator.name}_top"
        else:
            top_separator_trace.name = f"{self._top_separator.name}"
            top_separator_trace.legendgroup = f"{self._top_separator.name}"
        # Use ColorMixin method to adjust trace opacity
        self.adjust_trace_opacity(top_separator_trace, opacity)

        # Add traces in correct order based on x-axis flip state
        if self._flipped_x:
            # When flipped in x, add traces in reverse z-order
            fig.add_trace(top_separator_trace)
            for trace in anode_traces:
                fig.add_trace(trace)
            fig.add_trace(bottom_separator_trace)
            for trace in cathode_traces:
                fig.add_trace(trace)
        else:
            # Normal order (bottom to top in z)
            for trace in cathode_traces:
                fig.add_trace(trace)
            fig.add_trace(bottom_separator_trace)
            for trace in anode_traces:
                fig.add_trace(trace)
            fig.add_trace(top_separator_trace)

        # Calculate overall bounds to fix axis ranges
        all_x = []
        all_y = []

        # Collect coordinates from all traces
        for trace in fig.data:
            if hasattr(trace, "x") and trace.x is not None:
                all_x.extend([x for x in trace.x if x is not None])
            if hasattr(trace, "y") and trace.y is not None:
                all_y.extend([y for y in trace.y if y is not None])

        # Calculate bounds with some padding
        if all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)

            # Add padding
            x_range = x_max - x_min
            y_range = y_max - y_min
            padding_x = x_range * PLOT_PADDING_FACTOR
            padding_y = y_range * PLOT_PADDING_FACTOR

            x_bounds = [x_min - padding_x, x_max + padding_x]
            y_bounds = [y_min - padding_y, y_max + padding_y]
        else:
            # Fallback bounds
            x_bounds = [-PLOT_FALLBACK_BOUND, PLOT_FALLBACK_BOUND]
            y_bounds = [-PLOT_FALLBACK_BOUND, PLOT_FALLBACK_BOUND]

        # Final layout with fixed axis ranges
        fig.update_layout(
            xaxis={**self.SCHEMATIC_X_AXIS, "range": x_bounds},
            yaxis={**self.SCHEMATIC_Y_AXIS, "range": y_bounds},
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    def get_areal_capacity_plot(self, **kwargs) -> go.Figure:
        """
        Generate areal capacity plot for the layup's electrode half-cells.

        Parameters
        ----------
        **kwargs
            Additional plotting parameters for customization

        Returns
        -------
        go.Figure
            Plotly figure with areal capacity curves

        Raises
        ------
        ValueError
            If half-cell data is missing or invalid
        """
        # Validate that half-cell data exists
        fig = go.Figure()

        traces = [
            self.cathode.areal_capacity_curve_trace,
            self.anode.areal_capacity_curve_trace,
            self.areal_capacity_curve_trace,
        ]

        # add the traces
        fig.add_traces(traces)

        # Enhanced layout with zero lines and faint grid
        fig.update_layout(
            title=kwargs.get("title", f"Areal Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Areal Capacity (mAh/cm²)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
            **kwargs,
        )

        return fig

    def get_down_top_view(self, opacity: float = 0.2, **kwargs) -> go.Figure:
        """Generate bottom-up (cross-sectional) view of the layup.

        Parameters
        ----------
        **kwargs
            Additional plotting parameters for customization

        Returns
        -------
        go.Figure
            Plotly figure with bottom-up view of all layup components

        Raises
        ------
        ValueError
            If component trace data is missing or invalid
        """
        self._flip("x")
        figure = self.get_top_down_view(opacity=opacity, **kwargs)
        self._flip("x")
        return figure

    #### ACTIONS ####

    def _flip(self, axis: str) -> None:
        """
        Function to rotate the electrode around a specified axis by 180 degrees
        around the current datum position.

        Parameters
        ----------
        axis : str
            The axis to rotate around. Must be 'x', 'y', or 'z'.
        """
        if axis not in ["x", "y", "z"]:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")

        self._cathode._flip(axis)
        self._anode._flip(axis)
        self._bottom_separator._flip(axis)
        self._top_separator._flip(axis)

        if axis == "x":
            self._flipped_x = not self._flipped_x
        if axis == "y":
            self._flipped_y = not self._flipped_y
        if axis == "z":
            self._flipped_z = not self._flipped_z

    #### COMPONENT PROPERTY/SETTERS ####

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Layup datum anchored to the cathode datum.

        Returns
        -------
        (x, y, z) in mm: The cathode datum coordinates.
        """
        return self.cathode.datum

    @property
    def datum_x(self) -> float:
        """Get the x-coordinate of the layup datum in mm."""
        return self.datum[0]
    
    @property
    def datum_y(self) -> float:
        """Get the y-coordinate of the layup datum in mm."""
        return self.datum[1]

    @property
    def datum_z(self) -> float:
        """Get the z-coordinate of the layup datum in mm."""
        return self.datum[2]

    @property
    def np_ratio(self) -> float:
        """
        Get the n/p ratio of the layup (anode to cathode capacity ratio).
        """
        return round(self._np_ratio, 3)

    @property
    def np_ratio_range(self) -> Tuple[float, float]:
        """
        Get the n/p ratio range based on electrode capacities.
        """
        return 0, 1.5

    @property
    def areal_capacity_curve(self) -> pd.DataFrame:
        """Get the areal capacity curve with proper units and formatting."""
        # Pre-compute unit conversion factor
        capacity_conversion = S_TO_H * A_TO_mA / M_TO_CM**2

        # calculate the columns 
        areal_capacity = np.round(self._areal_capacity_curve[:, 0] * capacity_conversion, 4)
        voltage = np.round(self._areal_capacity_curve[:, 1], 4)
        direction = np.where(self._areal_capacity_curve[:, 2] == 1, "charge", "discharge")
        
        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Areal Capacity (mAh/cm²)": areal_capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def areal_capacity_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.areal_capacity_curve["Areal Capacity (mAh/cm²)"],
            y=self.areal_capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Full-Cell",
            line=dict(color= "#ff8c00", width=3),  # Slightly thicker for emphasis
            customdata=self.areal_capacity_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cathode(self):
        return self._cathode

    @property
    def bottom_separator(self):
        return self._bottom_separator

    @property
    def anode(self):
        return self._anode

    @property
    def top_separator(self):
        return self._top_separator

    @datum.setter
    @calculate_coordinates
    def datum(self, new_datum: Tuple[float, float, float]):
        """Shift entire layup so cathode datum becomes ``new_datum``.

        All components (cathode, anode, separators) are translated by the same
        (dx, dy, dz) so relative overhangs and spacing are preserved.

        Parameters
        ----------
        new_datum : tuple[float, float, float]
            Target cathode datum in mm.
        """
        self.validate_datum(new_datum)

        old = self.cathode.datum

        dx = new_datum[0] - old[0]
        dy = new_datum[1] - old[1]
        dz = new_datum[2] - old[2]

        # Shift cathode first
        self.cathode.datum = new_datum

        # Components to shift (if present)
        for comp_attr in ["anode", "bottom_separator", "top_separator"]:
            comp = getattr(self, comp_attr)
            cx, cy, cz = comp.datum
            comp.datum = (cx + dx, cy + dy, cz + dz)

    @datum_x.setter
    def datum_x(self, new_x: float):
        """Set the x-coordinate of the layup datum in mm."""
        self.validate_coordinate(new_x, "datum_x")
        self.datum = (new_x, self.datum[1], self.datum[2])

    @datum_y.setter
    def datum_y(self, new_y: float):
        """Set the y-coordinate of the layup datum in mm."""
        self.validate_coordinate(new_y, "datum_y")
        self.datum = (self.datum[0], new_y, self.datum[2])

    @datum_z.setter
    def datum_z(self, new_z: float):
        """Set the z-coordinate of the layup datum in mm."""
        self.validate_coordinate(new_z, "datum_z")
        self.datum = (self.datum[0], self.datum[1], new_z)

    @cathode.setter
    @calculate_all_properties
    def cathode(self, cathode: Cathode):
        """Set the cathode and update dependent components."""
        # validate the type
        self.validate_type(cathode, Cathode, "Cathode")

        # if there is an anode, update its ranges
        if self._update_properties:
            self._update_anode_ranges(cathode)
            self._update_separator_sizes(cathode)
            self._update_anode_dimensions(cathode)

        # set the cathode to self
        self._cathode = cathode

    @bottom_separator.setter
    @calculate_volumes
    def bottom_separator(self, bottom_separator: Separator):

        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # if there is an anode, update its ranges
        if not self._update_properties:

            bottom_separator._datum = (
                self.cathode._datum[0],
                self.cathode._datum[1],
                bottom_separator._datum[2],
            )

        elif self._update_properties:

            bottom_separator._datum = (
                self.bottom_separator._datum[0],
                self.bottom_separator._datum[1],
                bottom_separator._datum[2],
            )

        # assign to self
        self._bottom_separator = bottom_separator

    @anode.setter
    @calculate_all_properties
    def anode(self, anode: Anode):

        # validate type
        self.validate_type(anode, Anode, "Anode")

        # make a deep copy of the anode
        anode = deepcopy(anode)

        # set the ranges on the anode current collector based on the cathode current collector
        anode.current_collector.set_ranges_from_reference(self.cathode.current_collector)

        # modify the anodes datum position
        if not self._update_properties:
            anode.datum = (self.cathode.datum[0], self.cathode.datum[1], anode.datum[2])
        elif self._update_properties:
            anode.datum = (anode.datum[0], anode.datum[1], anode.datum[2])

        # if there is an anode, update its ranges
        if self._update_properties:
            self._update_separator_sizes(anode)

        # assign to self
        self._anode = anode

    @top_separator.setter
    @calculate_volumes
    def top_separator(self, top_separator: Separator):

        # validate the type
        self.validate_type(top_separator, Separator, "Top Separator")
        
        # if there is an anode, update its ranges
        if not self._update_properties:
            top_separator.datum = (
                self.cathode.datum[0],
                self.cathode.datum[1],
                top_separator.datum[2],
            )
        elif self._update_properties:
            top_separator.datum = (
                self.top_separator.datum[0],
                self.top_separator.datum[1],
                top_separator.datum[2],
            )

        # assign to self
        self._top_separator = top_separator

    @np_ratio.setter
    @calculate_all_properties
    def np_ratio(self, np_ratio: float) -> None:
        """
        Set the n/p ratio (anode to cathode capacity ratio) of the layup.

        Parameters
        ----------
        np_ratio : float
            Target n/p ratio (must be > 0)
        """
        self.validate_positive_float(np_ratio, "np_ratio")

        if self.np_ratio_control_mode == NPRatioControlMode.FIXED_CATHODE:
            new_anode_mass_loading = (np_ratio / self._np_ratio) * self.anode._mass_loading
            self._anode.mass_loading = new_anode_mass_loading * (KG_TO_MG / M_TO_CM**2)

        elif self.np_ratio_control_mode == NPRatioControlMode.FIXED_ANODE:
            new_cathode_mass_loading = (self._np_ratio / np_ratio) * self.cathode._mass_loading
            self._cathode.mass_loading = new_cathode_mass_loading * (KG_TO_MG / M_TO_CM**2)

        elif self.np_ratio_control_mode == NPRatioControlMode.FIXED_THICKNESS:
            
            # store the initial coating thicknesses
            initial_anode_thickness = self._anode.coating_thickness
            initial_cathode_thickness = self._cathode.coating_thickness
            total_thickness = initial_anode_thickness + initial_cathode_thickness

            # Store the maximum capacity
            _anode_max_cap = max(self._anode._areal_capacity_curve[:, 0])  # Ah/m²
            _cathode_max_cap = max(self._cathode._areal_capacity_curve[:, 0])

            # get the capacity per thickness for each electrode
            _anode_cap_per_thickness = _anode_max_cap / initial_anode_thickness
            _cathode_cap_per_thickness = _cathode_max_cap / initial_cathode_thickness

            # Target ratio (R) relates thicknesses through:
            # (A * t_a') / (C * t_c') = R  with  t_a' + t_c' = T
            # => t_a' = (R * C * T) / (A + R * C)
            R = np_ratio
            A = _anode_cap_per_thickness
            C = _cathode_cap_per_thickness
            T = total_thickness

            new_anode_thickness = (R * C * T) / (A + R * C)
            new_cathode_thickness = T - new_anode_thickness

            self._anode.coating_thickness = new_anode_thickness
            self._cathode.coating_thickness = new_cathode_thickness


    #### N/P RATIO CONTROL MODE ####

    @property
    def np_ratio_control_mode(self) -> NPRatioControlMode:
        """Get the current N/P ratio control mode."""
        return self._np_ratio_control_mode
    
    @np_ratio_control_mode.setter
    def np_ratio_control_mode(self, mode: NPRatioControlMode):

        if isinstance(mode, NPRatioControlMode):
            self._np_ratio_control_mode = mode
            return
        
        elif isinstance(mode, str):
            for enum_member in NPRatioControlMode:
                if mode.lower().replace(" ", "_") == enum_member.value:
                    self._np_ratio_control_mode = enum_member
                    return



