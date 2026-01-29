from copy import copy, deepcopy
from enum import Enum
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import brentq

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
from steer_opencell_design.Constructions.Layups.ArealCapacityCurveUtils import ArealCapacityCurveMixin
from steer_opencell_design.Utils.Decorators import calculate_electrochemical_properties
from steer_opencell_design.Components.CurrentCollectors.Base import _TapeCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Punched import PunchedCurrentCollector


# Module-level constants for overhang ranges and plotting parameters
PLOT_PADDING_FACTOR = 0.05  # 5% padding for plot bounds
PLOT_FALLBACK_BOUND = 100.0  # Fallback axis bounds in mm

# Separator range extension constants for Laminate validation
SEPARATOR_WIDTH_EXTENSION = 0.1  # Extension factor (10%) for separator width range
SEPARATOR_LENGTH_EXTENSION = 1.0  # Extension factor (100%) for separator length range

# Sampling resolution for flattened center line calculations
DEFAULT_X_SPACING = 0.004  # Default x-axis sampling spacing in meters (4mm)

# Thickness calculation fallback
THICKNESS_FALLBACK = 0.0  # Return value when thickness cannot be determined

# Electrochemical calculation constants
MINIMUM_VOLTAGE_RANGE_FRACTION = 0.5
VOLTAGE_PRECISION = 2
AREAL_CAPACITY_PRECISION = 3


class NPRatioControlMode(Enum):
    """Control modes for N/P ratio adjustments."""
    FIXED_ANODE = "fixed_anode"
    FIXED_CATHODE = "fixed_cathode"
    FIXED_THICKNESS = "fixed_thickness"


class ElectrodeOrientation(Enum):
    """Orientation options for electrode layups."""
    TRANSVERSE = "transverse"
    LONGITUDINAL = "longitudinal"


class _Layup(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin,
    PlotterMixin,
    ArealCapacityCurveMixin,
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
        electrode_orientation: ElectrodeOrientation = ElectrodeOrientation.LONGITUDINAL,
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
        electrode_orientation : ElectrodeOrientation
            The orientation of the electrode (default: ElectrodeOrientation.LONGITUDINAL).
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
        self.electrode_orientation = electrode_orientation
        self.name = name

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()
        self._calculate_electrochemical_properties()
        self._calculate_voltage_limits()

    def _calculate_bulk_properties(self):
        pass

    def _calculate_coordinates(self):
        self._set_z_positions()
        super()._calculate_coordinates()

    def _calculate_electrochemical_properties(self):
        self._calculate_areal_capacity_curves()

    def _calculate_voltage_limits(self) -> None:
        """Calculate upper and lower voltage limits for the operating window."""
        if hasattr(self, '_areal_capacity_curve') and self._areal_capacity_curve is not None:
            self._calculate_upper_voltage_limit_range()
            self._calculate_lower_voltage_limit_range()
            self._minimum_operating_voltage = min(self._minimum_operating_voltage_range)
            self._operating_voltage_window = (self._minimum_operating_voltage, self._maximum_operating_voltage)
            self._operating_reversible_areal_capacity = max(self._maximum_areal_reversible_capacity_range)

    def _calculate_lower_voltage_limit_range(self) -> None:
        """Calculate the minimum operating voltage range from discharge curve.
        
        Sets the minimum voltage range as the bottom quartile of the discharge voltage range,
        providing a safe operating window above the absolute minimum voltage.
        """
        # Extract discharge voltages directly using boolean indexing
        discharge_mask = self._areal_capacity_curve[:, 2] == -1
        discharge_voltages = self._areal_capacity_curve[discharge_mask, 1]

        # Calculate min and max in one pass using numpy's aminmax (faster than separate calls)
        _lower_voltage_minimum, voltage_max = discharge_voltages.min(), discharge_voltages.max()

        # Calculate top limit directly
        _lower_voltage_top_limit = _lower_voltage_minimum + (voltage_max - _lower_voltage_minimum) * MINIMUM_VOLTAGE_RANGE_FRACTION

        # set the minimum operating voltage range
        self._minimum_operating_voltage_range = (_lower_voltage_minimum, _lower_voltage_top_limit)

    def _compute_voltage_and_capacity_at_cutoff(self, layup, voltage_cutoff: float) -> Tuple[float, float]:
        """Helper method to compute max voltage and reversible capacity at a given voltage cutoff.
        
        Parameters
        ----------
        layup : _Layup
            Layup copy to modify
        voltage_cutoff : float
            Cathode voltage cutoff to apply
            
        Returns
        -------
        Tuple[float, float]
            Maximum voltage and reversible areal capacity at the given cutoff
        """
        layup._cathode._formulation.voltage_cutoff = voltage_cutoff
        layup._cathode.formulation = layup._cathode._formulation
        
        _, areal_curve = self._compute_areal_full_cell_curve(
            layup._cathode._areal_capacity_curve,
            layup._anode._areal_capacity_curve,
        )
        
        discharge_mask = areal_curve[:, 2] == -1
        discharge_curve = areal_curve[discharge_mask]
        
        max_voltage = areal_curve[:, 1].max()
        reversible_capacity = discharge_curve[:, 0].max() - discharge_curve[:, 0].min()
        
        return max_voltage, reversible_capacity

    def _calculate_upper_voltage_limit_range(self) -> None:
        """Calculate the maximum operating voltage range from cathode voltage cutoff range.
        
        Determines the upper voltage bounds by testing the cathode's voltage cutoff range
        and observing the resulting maximum voltages in the capacity curve.
        """
        # Get voltage cutoff range bounds
        _voltage_cutoff_range = self._cathode._formulation._voltage_operation_window
        _formulation_min_voltage, _formulation_max_voltage = min(_voltage_cutoff_range), max(_voltage_cutoff_range)

        # Create a single layup copy for all calculations
        _layup = deepcopy(self)

        # Get the current layup cutoff voltage
        _voltage_cutoff, _ = self._compute_voltage_and_capacity_at_cutoff(_layup, _layup._cathode._formulation.voltage_cutoff)

        # Get upper voltage max (at maximum formulation voltage)
        _upper_voltage_max, _upper_areal_reversible_capacity_max = self._compute_voltage_and_capacity_at_cutoff(
            _layup, _formulation_max_voltage
        )

        # Get lower voltage min (at minimum formulation voltage)
        _upper_voltage_min, _upper_areal_reversible_capacity_min = self._compute_voltage_and_capacity_at_cutoff(
            _layup, _formulation_min_voltage
        )

        # Set the maximum and minimum operating voltage ranges
        self._maximum_operating_voltage = _voltage_cutoff
        self._maximum_operating_voltage_range = (_upper_voltage_min, _upper_voltage_max)
        self._maximum_areal_reversible_capacity_range = (_upper_areal_reversible_capacity_min, _upper_areal_reversible_capacity_max)

        return (
            self._maximum_operating_voltage,
            self._maximum_operating_voltage_range, 
            self._maximum_areal_reversible_capacity_range
        )
    
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

    def _calculate_areal_capacity_curves(self) -> Tuple[float, np.ndarray]:
        """
        Calculate the half-cell curves for the cathode and anode.

        Returns
        -------
        Tuple[float, np.ndarray]
            A tuple containing the n/p ratio and the combined half-cell curve for the full cell.
        """
        # Use views instead of copies for better performance
        if hasattr(self._cathode, '_areal_capacity_curve') and self._cathode._areal_capacity_curve is not None and hasattr(self._anode, '_areal_capacity_curve') and self._anode._areal_capacity_curve is not None:
            cathode_areal_curve = self._cathode._areal_capacity_curve
            anode_areal_curve = self._anode._areal_capacity_curve

            # Call the static helper method to compute the full-cell curve
            self._np_ratio, self._areal_capacity_curve = self._compute_areal_full_cell_curve(cathode_areal_curve, anode_areal_curve)

            # Return n/p ratio and areal capacity curve
            return self._np_ratio, self._areal_capacity_curve
        
        else:
            return self._np_ratio, self._areal_capacity_curve

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
            required_width = reference_electrode.current_collector.x_foil_length + thickness_buffer
            required_length = reference_electrode.current_collector.y_foil_length + thickness_buffer
            
            if separator._width < reference_electrode.current_collector._x_foil_length:
                new_separator = deepcopy(separator)
                new_separator.width = required_width
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
                
            if separator._length < reference_electrode.current_collector._y_foil_length:
                new_separator = deepcopy(separator)
                new_separator.length = required_length
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
        else:
            # When not rotated, length maps to x-direction, width to y-direction
            required_length = reference_electrode.current_collector.x_foil_length + thickness_buffer
            required_width = reference_electrode.current_collector.y_foil_length + thickness_buffer
            
            if separator._length < reference_electrode.current_collector._x_foil_length:
                new_separator = deepcopy(separator)
                new_separator.length = required_length
                if separator_name == "bottom":
                    self._bottom_separator = new_separator
                else:
                    self._top_separator = new_separator
                
            if separator._width < reference_electrode.current_collector._y_foil_length:
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
        
        # Check if x_foil_length needs updating
        if anode_cc._x_foil_length < cathode_cc._x_foil_length:
            new_anode_current_collector = deepcopy(anode_cc)
            new_anode_current_collector.x_foil_length = cathode_cc.x_foil_length
            self.anode.current_collector = new_anode_current_collector
            
        # Check if y_foil_length needs updating
        if anode_cc._y_foil_length < cathode_cc._y_foil_length:
            new_anode_current_collector = deepcopy(anode_cc)
            new_anode_current_collector.y_foil_length = cathode_cc.y_foil_length
            self.anode.current_collector = new_anode_current_collector

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

    @property
    def maximum_operating_voltage_range(self) -> Tuple[float, float]:
        """Maximum operating voltage range in volts."""
        return (
            np.round(self._maximum_operating_voltage_range[0], VOLTAGE_PRECISION),
            np.round(self._maximum_operating_voltage_range[1], VOLTAGE_PRECISION),
        )
    
    @property
    def maximum_areal_reversible_capacity_range(self) -> Tuple[float, float]:
        """Maximum areal capacity range in mAh/cm²."""
        capacity_conversion = S_TO_H * A_TO_mA / M_TO_CM**2
        return (
            np.round(self._maximum_areal_reversible_capacity_range[0] * capacity_conversion, AREAL_CAPACITY_PRECISION),
            np.round(self._maximum_areal_reversible_capacity_range[1] * capacity_conversion, AREAL_CAPACITY_PRECISION),
        )
    
    @property
    def operating_reversible_areal_capacity(self) -> float:
        """Operating reversible areal capacity in mAh/cm²."""
        capacity_conversion = S_TO_H * A_TO_mA / M_TO_CM**2
        return np.round(self._operating_reversible_areal_capacity * capacity_conversion, AREAL_CAPACITY_PRECISION)
    
    @property
    def minimum_operating_voltage_range(self) -> Tuple[float, float]:
        """Minimum operating voltage range in volts."""
        return (
            np.round(self._minimum_operating_voltage_range[0], VOLTAGE_PRECISION),
            np.round(self._minimum_operating_voltage_range[1], VOLTAGE_PRECISION),
        )

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
        return np.round(self._np_ratio, 3)

    @property
    def np_ratio_range(self) -> Tuple[float, float]:
        """
        Get the n/p ratio range based on electrode capacities.
        """
        return 0, 1.5

    @property
    def areal_capacity_curve(self) -> pd.DataFrame:
        """Get the areal capacity curve with proper units and formatting."""

        if self._areal_capacity_curve is None:
            return None

        # Pre-compute unit conversion factor
        capacity_conversion = S_TO_H * A_TO_mA / M_TO_CM**2

        # split into charge and discharge
        charge_mask = self._areal_capacity_curve[:, 2] == 1
        discharge_mask = self._areal_capacity_curve[:, 2] == -1
        _charge_curve = self._areal_capacity_curve[charge_mask]
        _discharge_curve = self._areal_capacity_curve[discharge_mask]

        # pad the end of the charge curve to the max capacity of the discharge curve
        _charge_curve = np.vstack([_charge_curve, _charge_curve[-1, :]])
        _discharge_curve = np.vstack([_discharge_curve[0, :], _discharge_curve])
        _curve = np.vstack([_charge_curve, _discharge_curve])
        _curve = _curve[np.isnan(_curve).sum(axis=1) == 0]

        # calculate the columns 
        areal_capacity = np.round(_curve[:, 0] * capacity_conversion, 4)
        voltage = np.round(_curve[:, 1], 4)
        direction = np.where(_curve[:, 2] == 1, "charge", "discharge")
        
        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Areal Capacity (mAh/cm²)": areal_capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def areal_capacity_curve_trace(self) -> go.Scatter:

        if self.areal_capacity_curve is None:
            return None

        curve = self.areal_capacity_curve

        return go.Scatter(
            x=curve["Areal Capacity (mAh/cm²)"],
            y=curve["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Full-Cell",
            line=dict(color= "#ff8c00", width=3, shape="spline"),
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

    @property
    def np_ratio_control_mode(self) -> NPRatioControlMode:
        """Get the current N/P ratio control mode."""
        return self._np_ratio_control_mode
    
    @property
    def electrode_orientation(self) -> ElectrodeOrientation:
        """
        Get the electrode orientation.

        Returns
        -------
        ElectrodeOrientation
            The orientation of the electrode.
        """
        return self._electrode_orientation
    
    @property
    def operating_voltage_window(self) -> Tuple[float, float]:
        """Operating voltage window (min, max) in volts."""
        return (
            np.round(self._operating_voltage_window[0], VOLTAGE_PRECISION),
            np.round(self._operating_voltage_window[1], VOLTAGE_PRECISION),
        )
    
    @property
    def maximum_operating_voltage(self) -> float:
        """Maximum operating voltage in volts."""
        return np.round(self._operating_voltage_window[1], VOLTAGE_PRECISION)
    
    @property
    def minimum_operating_voltage(self) -> float:
        """Minimum operating voltage in volts."""
        return np.round(self._operating_voltage_window[0], VOLTAGE_PRECISION)

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

        if isinstance(self.cathode.current_collector, _TapeCurrentCollector) and isinstance(anode.current_collector, _TapeCurrentCollector):
            # if the anode has a larger minimum length range, then set that to the cathode
            cathode_min_length = self.cathode.current_collector.length_range[0] * MM_TO_M
            anode_min_length = anode.current_collector.length_range[0] * MM_TO_M
            new_cathode_min_length = max(cathode_min_length, anode_min_length)
            self.cathode.current_collector._x_foil_length_range = (
                new_cathode_min_length,
                self.cathode.current_collector.length_range[1] * MM_TO_M,
            )

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

    @operating_voltage_window.setter
    @calculate_electrochemical_properties
    def operating_voltage_window(self, value: Tuple[float, float]) -> None:
        """Set operating voltage window (min, max) in volts."""
        old_update_state = self._update_properties
        self._update_properties = False
        self.minimum_operating_voltage = value[0]
        self.maximum_operating_voltage = value[1]
        self._operating_voltage_window = (self._minimum_operating_voltage, self._maximum_operating_voltage)
        self._update_properties = old_update_state

    @minimum_operating_voltage.setter
    @calculate_electrochemical_properties
    def minimum_operating_voltage(self, value: float) -> None:

        range_min = min(self._minimum_operating_voltage_range)
        range_max = max(self._minimum_operating_voltage_range)
        
        if value is None:
            value = range_min

        # validate positive float
        self.validate_positive_float(value, "minimum_operating_voltage")
        
        # clamp to operating voltage range
        if value < range_min:
            self._minimum_operating_voltage = range_min
        elif value > range_max:
            self._minimum_operating_voltage = range_max
        else:
            self._minimum_operating_voltage = value

        if self._update_properties:
            self._operating_voltage_window = (
                self._minimum_operating_voltage,
                self._maximum_operating_voltage,
            )

    @maximum_operating_voltage.setter
    @calculate_electrochemical_properties
    def maximum_operating_voltage(self, value: float) -> None:

        # get the minimum and maximum of the operating voltage range
        range_min = min(self._maximum_operating_voltage_range)
        range_max = max(self._maximum_operating_voltage_range)
        
        # if value is None, set to max of range
        if value is None:
            value = range_max

        # validate positive float
        self.validate_positive_float(value, "maximum_operating_voltage")
        
        # clamp values to range
        self._maximum_operating_voltage = np.clip(value, range_min, range_max)

        if self._update_properties:

            self._operating_voltage_window = (
                self._minimum_operating_voltage,
                self._maximum_operating_voltage,
            )

        def voltage_objective(cutoff: float):
            """Calculate difference between target and actual maximum voltage.
        
            Parameters
            ----------
            cutoff : float
                Cathode formulation voltage cutoff to test.
                
            Returns
            -------
            float
                Difference between achieved max voltage and target.
            """
            # get the cathode with modified cutoff
            _cathode = deepcopy(self._cathode)
            _cathode._formulation.voltage_cutoff = cutoff
            _cathode.formulation = _cathode._formulation

            # get the electrode curves
            _cathode_areal_curve = _cathode._areal_capacity_curve
            _anode_areal_curve = self._anode._areal_capacity_curve

            # compute the full-cell curve
            _, full_cell_curve = self._compute_areal_full_cell_curve(
                _cathode_areal_curve, 
                _anode_areal_curve
            )

            # get the max voltage of the full-cell curve
            max_voltage = full_cell_curve[:, 1].max()

            # calculate the difference
            difference = max_voltage - self._maximum_operating_voltage

            # return the difference from target
            return difference
        
        # Find optimal cutoff using Brent's method
        optimal_cathode_cutoff = brentq(
            voltage_objective,
            min(self._cathode._formulation._voltage_operation_window),
            max(self._cathode._formulation._voltage_operation_window),
            xtol=1e-5,
            rtol=1e-5,
        )

        # set the cathode formulation voltage cutoff
        self._cathode._formulation.voltage_cutoff = optimal_cathode_cutoff
        self._cathode.formulation = self._cathode._formulation
        self._cathode = self._cathode


    @operating_reversible_areal_capacity.setter
    @calculate_electrochemical_properties
    def operating_reversible_areal_capacity(self, value: float) -> None:

        # get the minimum and maximum of the operating voltage range
        range_min = min(self._maximum_areal_reversible_capacity_range)
        range_max = max(self._maximum_areal_reversible_capacity_range)
        
        # if value is None, set to max of range
        if value is None:
            value = range_max

        # validate positive float
        self.validate_positive_float(value, "operating_reversible_areal_capacity")
        
        # convert value to Ah/m²
        capacity_conversion = M_TO_CM**2 / (S_TO_H * A_TO_mA)
        value = value * capacity_conversion

        # clamp values to range
        self._operating_reversible_areal_capacity = np.clip(value, range_min, range_max)

        def areal_capacity_objective(voltage_cutoff: float):
            """Calculate difference between target and actual maximum voltage.
        
            Parameters
            ----------
            cutoff : float
                Cathode formulation voltage cutoff to test.
                
            Returns
            -------
            float
                Difference between achieved max voltage and target.
            """
            # get the cathode with modified cutoff
            _cathode = deepcopy(self._cathode)
            _cathode._formulation.voltage_cutoff = voltage_cutoff
            _cathode.formulation = _cathode._formulation

            # get the electrode curves
            _cathode_areal_curve = _cathode._areal_capacity_curve
            _anode_areal_curve = self._anode._areal_capacity_curve

            # compute the full-cell curve
            _, full_cell_curve = self._compute_areal_full_cell_curve(
                _cathode_areal_curve, 
                _anode_areal_curve
            )

            # get the discharge portion of the full-cell curve
            discharge_mask = full_cell_curve[:, 2] == -1
            discharge_curve = full_cell_curve[discharge_mask]

            # get the max areal capacity of the discharge curve
            max_capacity = discharge_curve[:, 0].max()
            min_capacity = discharge_curve[:, 0].min()
            reversible_capacity = max_capacity - min_capacity

            # calculate the difference
            difference = reversible_capacity - self._operating_reversible_areal_capacity

            # return the difference from target
            return difference
        
        # Find optimal cutoff using Brent's method
        optimal_cathode_cutoff = brentq(
            areal_capacity_objective,
            min(self._cathode._formulation._voltage_operation_window),
            max(self._cathode._formulation._voltage_operation_window),
            xtol=1e-5,
            rtol=1e-5,
        )

        # set the cathode formulation voltage cutoff
        self._cathode._formulation.voltage_cutoff = optimal_cathode_cutoff
        self._cathode.formulation = self._cathode._formulation
        self._cathode = self._cathode

    @electrode_orientation.setter
    def electrode_orientation(self, electrode_orientation: ElectrodeOrientation) -> None:
        """
        Set the electrode orientation of the layup.

        When electrode_orientation is ElectrodeOrientation.TRANSVERSE, ensures the anode tab comes out the bottom
        by flipping the anode if it's not already flipped in the y direction.

        Parameters
        ----------
        electrode_orientation : ElectrodeOrientation
            The orientation of the electrode.
        """
        if isinstance(electrode_orientation, ElectrodeOrientation):
            self._electrode_orientation = electrode_orientation

        elif isinstance(electrode_orientation, str):
            for enum_member in ElectrodeOrientation:
                if electrode_orientation.lower().replace(" ", "_") == enum_member.value:
                    self._electrode_orientation = enum_member

        else:
            # validate the type
            self.validate_type(electrode_orientation, ElectrodeOrientation, "electrode_orientation")

        # if electrode_orientation is ElectrodeOrientation.TRANSVERSE, check and adjust anode orientation
        if self._electrode_orientation == ElectrodeOrientation.TRANSVERSE:
            if not self._cathode._flipped_y:
                self._cathode._flip("y")
                self._cathode._flip("x")
        elif self._electrode_orientation == ElectrodeOrientation.LONGITUDINAL:
            if self._cathode._flipped_y:
                self._cathode._flip("y")
                self._cathode._flip("x")

