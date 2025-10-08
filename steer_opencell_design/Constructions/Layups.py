from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Components.CurrentCollectors import (
    _TapeCurrentCollector,
    PunchedCurrentCollector,
)

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_volumes

from steer_core.Constants.Units import *

from copy import copy, deepcopy
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Tuple
from enum import Enum


class OverhangControlMode(Enum):
    """Control modes for anode overhang adjustments."""
    FIXED_COMPONENT = "fixed_component"  # Move anode position to achieve overhang
    FIXED_OVERHANGS = "fixed_overhangs"  # Extend anode body to achieve overhang


class NPRatioControlMode(Enum):
    """Control modes for N/P ratio adjustments."""
    FIXED_ANODE = "fixed_anode"  # Adjust cathode mass loading to achieve N/P ratio
    FIXED_CATHODE = "fixed_cathode"  # Adjust anode mass loading to achieve N/P ratio
    FIXED_THICKNESS = "fixed_thickness"  # Adjust both mass loadings to keep the same thickness but the target N/P ratio


class _Layup(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin
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
        self._update_properties = False

        self.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT
        self.np_ratio_control_mode = NPRatioControlMode.FIXED_ANODE

        self.cathode = cathode
        self.bottom_separator = bottom_separator
        self.anode = anode
        self.top_separator = top_separator
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        self._calculate_coordinates()
        self._calculate_bulk_properties()
        self._calculate_full_cell_curves()

    def _calculate_bulk_properties(self):
        # calculate thickness
        self._thickness = self._cathode.thickness + self._bottom_separator.thickness + self._anode.thickness + self._top_separator.thickness

    def _calculate_coordinates(self):
        self._calculate_anode_overhangs()
        self._calculate_bottom_separator_overhangs()
        self._calculate_top_separator_overhangs()
        self._set_z_positions()

    def _set_z_positions(self):
        _bottom_separator_z = self._cathode._current_collector._datum[2] + (self._cathode._thickness / 2 + self._bottom_separator._thickness / 2) * UM_TO_M
        _anode_z = _bottom_separator_z + (self._bottom_separator._thickness / 2 + self._anode._thickness / 2) * UM_TO_M
        _top_separator_z = _anode_z + (self._anode._thickness / 2 + self._top_separator._thickness / 2) * UM_TO_M

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

    def _calculate_anode_overhangs(self):
        """
        Calculate the anode overhangs relative to the cathode.
        """
        if hasattr(self, "_cathode") and hasattr(self, "_anode") and self._cathode is not None and self._anode is not None:
            # Cathode edges (using internal SI units - meters)
            cathode_left = self._cathode._current_collector._datum[0] - self._cathode._current_collector._x_body_length / 2
            cathode_right = self._cathode._current_collector._datum[0] + self._cathode._current_collector._x_body_length / 2
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Anode edges (using internal SI units - meters)
            anode_left = self._anode._current_collector._datum[0] - self._anode._current_collector._x_body_length / 2
            anode_right = self._anode._current_collector._datum[0] + self._anode._current_collector._x_body_length / 2
            anode_bottom = self._anode._current_collector._datum[1] - self._anode._current_collector._y_body_length / 2
            anode_top = self._anode._current_collector._datum[1] + self._anode._current_collector._y_body_length / 2

            # Calculate overhangs (positive values mean anode extends beyond cathode)
            self._anode_overhang_left = cathode_left - anode_left
            self._anode_overhang_right = anode_right - cathode_right
            self._anode_overhang_bottom = cathode_bottom - anode_bottom
            self._anode_overhang_top = anode_top - cathode_top

        else:
            # Set default values if components are not available
            self._anode_overhang_left = 0.0
            self._anode_overhang_right = 0.0
            self._anode_overhang_bottom = 0.0
            self._anode_overhang_top = 0.0

    def _calculate_bottom_separator_overhangs(self):
        """
        Calculate the bottom separator overhangs relative to the cathode.
        """

        if hasattr(self, "_cathode") and hasattr(self, "_bottom_separator") and self._cathode is not None and self._bottom_separator is not None:
            # Cathode edges (using internal SI units - meters)
            cathode_left = self._cathode._current_collector._datum[0] - self._cathode._current_collector._x_body_length / 2
            cathode_right = self._cathode._current_collector._datum[0] + self._cathode._current_collector._x_body_length / 2
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Bottom separator edges (using internal SI units - meters)
            separator_left = min(self._bottom_separator._coordinates[:, 0])
            separator_right = max(self._bottom_separator._coordinates[:, 0])
            separator_bottom = min(self._bottom_separator._coordinates[:, 1])
            separator_top = max(self._bottom_separator._coordinates[:, 1])

            # Calculate overhangs (positive values mean separator extends beyond cathode)
            self._bottom_separator_overhang_left = cathode_left - separator_left
            self._bottom_separator_overhang_right = separator_right - cathode_right
            self._bottom_separator_overhang_bottom = cathode_bottom - separator_bottom
            self._bottom_separator_overhang_top = separator_top - cathode_top

        else:
            # Set default values if components are not available
            self._bottom_separator_overhang_left = 0.0
            self._bottom_separator_overhang_right = 0.0
            self._bottom_separator_overhang_bottom = 0.0
            self._bottom_separator_overhang_top = 0.0

    def _calculate_top_separator_overhangs(self):
        """
        Calculate the top separator overhangs relative to the cathode.
        """
        if hasattr(self, "_cathode") and hasattr(self, "_top_separator") and self._cathode is not None and self._top_separator is not None:
            # Cathode edges (using internal SI units - meters)
            cathode_left = self._cathode._current_collector._datum[0] - self._cathode._current_collector._x_body_length / 2
            cathode_right = self._cathode._current_collector._datum[0] + self._cathode._current_collector._x_body_length / 2
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Top separator edges (using internal SI units - meters)
            separator_left = min(self._top_separator._coordinates[:, 0])
            separator_right = max(self._top_separator._coordinates[:, 0])
            separator_bottom = min(self._top_separator._coordinates[:, 1])
            separator_top = max(self._top_separator._coordinates[:, 1])

            # Calculate overhangs (positive values mean separator extends beyond cathode)
            self._top_separator_overhang_left = cathode_left - separator_left
            self._top_separator_overhang_right = separator_right - cathode_right
            self._top_separator_overhang_bottom = cathode_bottom - separator_bottom
            self._top_separator_overhang_top = separator_top - cathode_top

        else:
            # Set default values if components are not available
            self._top_separator_overhang_left = 0.0
            self._top_separator_overhang_right = 0.0
            self._top_separator_overhang_bottom = 0.0
            self._top_separator_overhang_top = 0.0

    def _calculate_full_cell_curves(self) -> np.ndarray:
        """
        Calculate the half-cell curves for the cathode and anode.

        Returns
        -------
        np.ndarray
            The combined half-cell curve for the full cell.
        """
        cathode_half_cell = copy(self._cathode._half_cell_curve)
        anode_half_cell = copy(self._anode._half_cell_curve)

        max_cap_cathode = max(self._cathode._half_cell_curve[:, 4])
        max_cap_anode = max(self._anode._half_cell_curve[:, 4])
        self._np_ratio = max_cap_anode / max_cap_cathode

        # Split cathode curves by direction (column 2: 0=discharge, 1=charge)
        cathode_charge = cathode_half_cell[cathode_half_cell[:, 2] == 1]
        cathode_discharge = cathode_half_cell[cathode_half_cell[:, 2] == -1]

        # Split anode curves by direction
        anode_charge = anode_half_cell[anode_half_cell[:, 2] == 1]
        anode_discharge = anode_half_cell[anode_half_cell[:, 2] == -1]

        # Calculate valid x range (column 4 is areal capacity)
        # For charge: find overlapping range (intersection)
        charge_x_min = max(cathode_charge[:, 4].min(), anode_charge[:, 4].min())
        charge_x_max = min(cathode_charge[:, 4].max(), anode_charge[:, 4].max())

        # For discharge: find overlapping range (intersection)
        discharge_x_min = max(cathode_discharge[:, 4].min(), anode_discharge[:, 4].min())
        discharge_x_max = min(cathode_discharge[:, 4].max(), anode_discharge[:, 4].max())

        # Create interpolation functions for voltage vs areal capacity

        # Sort by areal capacity for interpolation
        cathode_charge_sorted = cathode_charge[cathode_charge[:, 4].argsort()]
        cathode_discharge_sorted = cathode_discharge[cathode_discharge[:, 4].argsort()]
        anode_charge_sorted = anode_charge[anode_charge[:, 4].argsort()]
        anode_discharge_sorted = anode_discharge[anode_discharge[:, 4].argsort()]

        # Create common x arrays for interpolation
        n_points = 100  # Number of points for smooth curves
        charge_x_common = np.linspace(charge_x_min, charge_x_max, n_points)
        discharge_x_common = np.linspace(discharge_x_min, discharge_x_max, n_points)

        # Interpolate voltages using numpy.interp (voltage = column 1, areal capacity = column 4)
        cathode_charge_voltage = np.interp(charge_x_common, cathode_charge_sorted[:, 4], cathode_charge_sorted[:, 1])
        cathode_discharge_voltage = np.interp(
            discharge_x_common,
            cathode_discharge_sorted[:, 4],
            cathode_discharge_sorted[:, 1],
        )
        anode_charge_voltage = np.interp(charge_x_common, anode_charge_sorted[:, 4], anode_charge_sorted[:, 1])
        anode_discharge_voltage = np.interp(
            discharge_x_common,
            anode_discharge_sorted[:, 4],
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

        # Discharge curve: descending x order (direction = 0)
        discharge_curve = np.column_stack(
            [
                discharge_x_common[::-1],  # Column 0: areal capacity (descending)
                discharge_voltage_full[::-1],  # Column 1: voltage
                np.zeros(len(discharge_x_common)),  # Column 2: direction (0 = discharge)
            ]
        )

        # Recombine: charge first (ascending), then discharge (descending)
        self._full_cell_curve = np.vstack([charge_curve, discharge_curve])

        return self._full_cell_curve

    def _adjust_overhang_fixed_component(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust overhang by moving the component position (fixed component mode).

        Parameters
        ----------
        component : str
            Component name ('anode', 'bottom_separator', 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        current_overhang = getattr(self, f"{component}_overhang_{direction}")
        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        # get component datum
        datum = component_obj.datum

        if direction == "left":
            datum = (datum[0] - overhang_difference, datum[1], datum[2])
        elif direction == "right":
            datum = (datum[0] + overhang_difference, datum[1], datum[2])
        elif direction == "bottom":
            datum = (datum[0], datum[1] - overhang_difference, datum[2])
        elif direction == "top":
            datum = (datum[0], datum[1] + overhang_difference, datum[2])

        component_obj.datum = datum

        # Special handling for ZFoldMonoLayer: when anode moves left/right, top separator should follow
        if hasattr(self, "__class__") and self.__class__.__name__ == "ZFoldMonoLayer" and component == "anode" and direction in ["left", "right"]:

            # Get the top separator and adjust its position by the same amount
            top_separator_datum = self._top_separator.datum

            if direction == "left":
                top_separator_datum = (top_separator_datum[0] - overhang_difference, top_separator_datum[1], top_separator_datum[2])
            elif direction == "right":
                top_separator_datum = (top_separator_datum[0] + overhang_difference, top_separator_datum[1], top_separator_datum[2])

            self._top_separator.datum = top_separator_datum

    def _adjust_overhang_fixed_overhangs(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust overhang by extending the component dimensions (fixed overhangs mode).

        Parameters
        ----------
        component : str
            Component name ('anode', 'bottom_separator', 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        target_overhang = target_overhang * MM_TO_M
        current_overhang = getattr(self, f"_{component}_overhang_{direction}")
        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        if component == "anode":
            # Determine which dimension and position to adjust
            if direction in ["left", "right"]:
                self.anode.current_collector.x_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == "left":
                    self.anode.current_collector.datum_x -= position_adjustment
                else:  # right
                    self.anode.current_collector.datum_x += position_adjustment
            else:  # bottom or top
                self.anode.current_collector.y_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == "bottom":
                    self.anode.current_collector.datum_y -= position_adjustment
                else:  # top
                    self.anode.current_collector.datum_y += position_adjustment

            # Trigger setters
            self.anode.current_collector = self.anode.current_collector
            self.anode = self.anode

        elif isinstance(component_obj, Separator):
            # Create mapping for dimension and position adjustments
            position_adjustment = (overhang_difference / 2) * M_TO_MM

            # Determine which dimension to adjust based on rotation and direction
            is_horizontal = direction in ["left", "right"]
            is_rotated = component_obj._rotated_xy

            # Logic: if rotated, horizontal directions affect width, vertical affects length
            # If not rotated, horizontal directions affect length, vertical affects width
            if (is_horizontal and not is_rotated) or (not is_horizontal and is_rotated):
                # Adjust length
                component_obj.length += overhang_difference * M_TO_MM
            else:
                # Adjust width
                component_obj.width += overhang_difference * M_TO_MM

            # Adjust position
            if direction == "left":
                component_obj.datum_x -= position_adjustment
            elif direction == "right":
                component_obj.datum_x += position_adjustment
            elif direction == "bottom":
                component_obj.datum_y -= position_adjustment
            else:  # top
                component_obj.datum_y += position_adjustment

            # Trigger setter
            setattr(self, component, component_obj)

    def get_top_down_view(self, opacity: float = 0.2, **kwargs) -> go.Figure:
        # Validate opacity using ColorMixin
        self.validate_opacity(opacity)

        fig = go.Figure()

        # Get trace groups
        cathode_fig = self._cathode._get_full_top_down_view()
        for i, trace in enumerate(cathode_fig.data):
            trace.name = trace.name + " (Cathode)"
            trace.legendgroup = trace.name + " (Cathode)"
            # Use ColorMixin method to adjust trace opacity
            self.adjust_trace_opacity(trace, opacity)
            fig.add_trace(trace)

        # Check if separators have the same name and create distinct legend groups
        separators_same_name = self._bottom_separator.name == self._top_separator.name

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
        fig.add_trace(bottom_separator_trace)

        anode_fig = self._anode._get_full_top_down_view()
        for i, trace in enumerate(anode_fig.data):
            trace.name = trace.name + " (Anode)"
            trace.legendgroup = trace.name + " (Anode)"
            trace.xaxis = "x"
            trace.yaxis = "y"
            # Use ColorMixin method to adjust trace opacity
            self.adjust_trace_opacity(trace, opacity)
            fig.add_trace(trace)

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

            # Add 5% padding
            x_range = x_max - x_min
            y_range = y_max - y_min
            padding_x = x_range * 0.05
            padding_y = y_range * 0.05

            x_bounds = [x_min - padding_x, x_max + padding_x]
            y_bounds = [y_min - padding_y, y_max + padding_y]
        else:
            # Fallback bounds
            x_bounds = [-100, 100]
            y_bounds = [-100, 100]

        # Final layout with fixed axis ranges
        fig.update_layout(
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                scaleanchor="y",
                title="",
                showticklabels=False,
                range=x_bounds,
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                title="",
                showticklabels=False,
                range=y_bounds,
            ),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            title=kwargs.get("title", f"Top-Down View"),
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
        anode_half_cell = self.anode.half_cell_curve
        cathode_half_cell = self.cathode.half_cell_curve

        fig = go.Figure()

        # Thicker lines for better visibility
        line_width = kwargs.get("line_width", 2.5)
        
        fig.add_trace(
            go.Scatter(
                x=cathode_half_cell["Areal Capacity (mAh/cm²)"],
                y=cathode_half_cell["Voltage (V)"],
                mode="lines",
                name=f"{self.cathode.name} Half-Cell",
                line=dict(color=self.cathode.formulation.color, width=line_width),
                customdata=cathode_half_cell["Direction"],
                hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=anode_half_cell["Areal Capacity (mAh/cm²)"],
                y=anode_half_cell["Voltage (V)"],
                mode="lines",
                name=f"{self.anode.name} Half-Cell",
                line=dict(color=self.anode.formulation.color, width=line_width),
                customdata=anode_half_cell["Direction"],
                hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
            )
        )

        # Add full-cell curve
        full_cell_curve = self.full_cell_curve
        full_cell_color = kwargs.get("full_cell_color", "#ff8c00")  # Default orange

        fig.add_trace(
            go.Scatter(
                x=full_cell_curve["Areal Capacity (mAh/cm²)"],
                y=full_cell_curve["Voltage (V)"],
                mode="lines",
                name=f"{self.name} Full-Cell",
                line=dict(color=full_cell_color, width=line_width + 0.5),  # Slightly thicker for emphasis
                customdata=full_cell_curve["Direction"],
                hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
            )
        )

        # Enhanced layout with zero lines and faint grid
        fig.update_layout(
            title=kwargs.get("title", f"Areal Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis=dict(
                title="Areal Capacity (mAh/cm²)",
                showgrid=True,
                gridcolor="rgba(128, 128, 128, 0.2)",  # Faint gray grid lines
                gridwidth=1,
                zeroline=True,
                zerolinecolor="rgba(0, 0, 0, 0.5)",  # Semi-transparent black zero line
                zerolinewidth=1,
            ),
            yaxis=dict(
                title="Voltage (V)",
                showgrid=True,
                gridcolor="rgba(128, 128, 128, 0.2)",  # Faint gray grid lines
                gridwidth=1,
                zeroline=True,
                zerolinecolor="rgba(0, 0, 0, 0.5)",  # Semi-transparent black zero line
                zerolinewidth=1,
            ),
            hovermode="closest",
        )

        return fig

    #### COMPONENT PROPERTY/SETTERS ####

    @property
    def thickness(self) -> float:
        """
        Get the total thickness of the layup in micrometers (µm).
        """
        return round(self._thickness * M_TO_UM, 3)

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
    def full_cell_curve(self) -> pd.DataFrame:
        return (
            pd.DataFrame(
                self._full_cell_curve,
                columns=["areal_capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                areal_capacity=lambda x: x["areal_capacity"] * (S_TO_H * A_TO_mA / M_TO_CM**2),
            )
            .rename(
                columns={
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                    "areal_capacity": "Areal Capacity (mAh/cm²)",
                }
            )
            .round(4)
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
    def separator(self) -> Separator:
        """
        Get the Z-fold separator. Returns the bottom separator as the canonical reference.
        In Z-fold configuration, both separators are constrained to be identical.
        """
        return self._bottom_separator

    @separator.setter
    @calculate_volumes
    def separator(self, separator: Separator):

        # validate the type
        self.validate_type(separator, Separator, "Separator")

        # move attributes to bottom separator
        self.bottom_separator.material = separator.material
        self.bottom_separator.thickness = separator.thickness

        # set the top separator to be identical
        self.top_separator.material = separator.material
        self.top_separator.thickness = separator.thickness

    @cathode.setter
    @calculate_all_properties
    def cathode(self, cathode: Cathode):
        # validate the type
        self.validate_type(cathode, Cathode, "Cathode")

        # if there is an anode, update its ranges
        if self._update_properties:

            # update the anode ranges
            self._anode.current_collector.set_ranges_from_reference(self.cathode.current_collector)

            # if the anode has a shorter length then update it
            if self.anode.current_collector._x_body_length < self.cathode.current_collector._x_body_length:
                new_anode_current_collector = deepcopy(self.anode.current_collector)
                new_anode_current_collector.x_body_length = cathode.current_collector.x_body_length
                self.anode.current_collector = new_anode_current_collector

            # if the anode has a shorter width then update it
            if self.anode.current_collector._y_body_length < self.cathode.current_collector._y_body_length:
                new_anode_current_collector = deepcopy(self.anode.current_collector)
                new_anode_current_collector.y_body_length = cathode.current_collector.y_body_length
                self.anode.current_collector = new_anode_current_collector

        # set the cathode to self
        self._cathode = deepcopy(cathode)

    @bottom_separator.setter
    @calculate_volumes
    def bottom_separator(self, bottom_separator: Separator):

        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # make deep copy
        bottom_separator = deepcopy(bottom_separator)

        # if there is an anode, update its ranges
        if not self._update_properties:
            bottom_separator.datum = (
                self.cathode.datum[0],
                self.cathode.datum[1],
                bottom_separator.datum[2],
            )
        elif self._update_properties:
            bottom_separator.datum = (
                self.bottom_separator.datum[0],
                self.bottom_separator.datum[1],
                bottom_separator.datum[2],
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

        # reset the separator to ensure it has the right propertions
        if self._update_properties:
            self._update_properties = False
            separator = self._bottom_separator
            self.separator = separator
            self._update_properties = True

        # assign to self
        self._anode = anode

    @top_separator.setter
    @calculate_all_properties
    def top_separator(self, top_separator: Separator):
        # validate the type
        self.validate_type(top_separator, Separator, "Top Separator")

        # make deep copy
        top_separator = deepcopy(top_separator)

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
            self.anode.mass_loading = new_anode_mass_loading * (KG_TO_MG / M_TO_CM**2)
            self.anode = self.anode

        elif self.np_ratio_control_mode == NPRatioControlMode.FIXED_ANODE:
            new_cathode_mass_loading = (self._np_ratio / np_ratio) * self.cathode._mass_loading
            self.cathode.mass_loading = new_cathode_mass_loading * (KG_TO_MG / M_TO_CM**2)
            self.cathode = self.cathode

        elif self.np_ratio_control_mode == NPRatioControlMode.FIXED_THICKNESS:
            
            # Store initial mass loadings
            _initial_anode_ml = self.anode._mass_loading  # kg/m²
            _initial_cathode_ml = self.cathode._mass_loading  # kg/m²
            _total_mass_loading = _initial_anode_ml + _initial_cathode_ml
            
            # Store the maximum capacity
            _anode_max_cap = max(self.anode._half_cell_curve[:, 4])  # Ah/m²
            _cathode_max_cap = max(self.cathode._half_cell_curve[:, 4])

            # Get capacity per mass loading for each electrode
            _anode_cap_per_ml = _anode_max_cap / _initial_anode_ml
            _cathode_cap_per_ml = _cathode_max_cap / _initial_cathode_ml
            
            _new_anode_ml = (np_ratio * _total_mass_loading * _cathode_cap_per_ml) / (_anode_cap_per_ml + np_ratio * _cathode_cap_per_ml)
            _new_cathode_ml = _total_mass_loading - _new_anode_ml
            
            # Apply the new mass loadings (convert from kg/m² to mg/cm²)
            self.anode.mass_loading = _new_anode_ml * (KG_TO_MG / M_TO_CM**2)
            self.cathode.mass_loading = _new_cathode_ml * (KG_TO_MG / M_TO_CM**2)
            
            # Trigger setters to update properties
            self.anode = self.anode
            self.cathode = self.cathode

    #### ANODE OVERHANG PROPERTY/SETTERS ####

    @property
    def anode_overhang_left(self) -> float:
        """
        Get the left overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_left * M_TO_MM, 2)

    @property
    def anode_overhang_right(self) -> float:
        """
        Get the right overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_right * M_TO_MM, 2)

    @property
    def anode_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_bottom * M_TO_MM, 2)

    @property
    def anode_overhang_top(self) -> float:
        """
        Get the top overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_top * M_TO_MM, 2)

    @property
    def anode_overhangs(self) -> dict:
        """
        Get all anode overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.anode_overhang_left,
            "right": self.anode_overhang_right,
            "bottom": self.anode_overhang_bottom,
            "top": self.anode_overhang_top,
        }

    @anode_overhang_left.setter
    @calculate_all_properties
    def anode_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self.validate_positive_float(overhang, "anode_overhang_left")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("anode", overhang, "left")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("anode", overhang, "left")

    @anode_overhang_right.setter
    @calculate_all_properties
    def anode_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self.validate_positive_float(overhang, "anode_overhang_right")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("anode", overhang, "right")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("anode", overhang, "right")

    @anode_overhang_bottom.setter
    @calculate_all_properties
    def anode_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self.validate_positive_float(overhang, "anode_overhang_bottom")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("anode", overhang, "bottom")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("anode", overhang, "bottom")

    @anode_overhang_top.setter
    @calculate_all_properties
    def anode_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self.validate_positive_float(overhang, "anode_overhang_top")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("anode", overhang, "top")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("anode", overhang, "top")

    #### ANODE OVERHANG RANGE PROPERTIES ####

    @property
    def anode_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.anode_overhang_left + self.anode_overhang_right)

    @property
    def anode_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.anode_overhang_left + self.anode_overhang_right)

    @property
    def anode_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.anode_overhang_bottom + self.anode_overhang_top)

    @property
    def anode_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.anode_overhang_bottom + self.anode_overhang_top)

    #### BOTTOM SEPARATOR OVERHANG PROPERTY/SETTERS ####

    @property
    def bottom_separator_overhang_left(self) -> float:
        """
        Get the left overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_left * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_right(self) -> float:
        """
        Get the right overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_right * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_bottom * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_top(self) -> float:
        """
        Get the top overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_top * M_TO_MM, 3)

    @property
    def bottom_separator_overhangs(self) -> dict:
        """
        Get all bottom separator overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.bottom_separator_overhang_left,
            "right": self.bottom_separator_overhang_right,
            "bottom": self.bottom_separator_overhang_bottom,
            "top": self.bottom_separator_overhang_top,
        }

    @bottom_separator_overhang_left.setter
    @calculate_all_properties
    def bottom_separator_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "bottom_separator_overhang_left")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("bottom_separator", overhang, "left")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("bottom_separator", overhang, "left")

    @bottom_separator_overhang_right.setter
    @calculate_all_properties
    def bottom_separator_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "bottom_separator_overhang_right")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("bottom_separator", overhang, "right")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("bottom_separator", overhang, "right")

    @bottom_separator_overhang_bottom.setter
    @calculate_all_properties
    def bottom_separator_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "bottom_separator_overhang_bottom")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("bottom_separator", overhang, "bottom")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("bottom_separator", overhang, "bottom")

    @bottom_separator_overhang_top.setter
    @calculate_all_properties
    def bottom_separator_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "bottom_separator_overhang_top")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("bottom_separator", overhang, "top")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("bottom_separator", overhang, "top")

    #### BOTTOM SEPARATOR OVERHANG RANGE PROPERTIES ####

    @property
    def bottom_separator_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self) == Laminate:
                return (0.0, 500.0)
            else:
                return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            min = 0
            max = (self._bottom_separator_overhang_left + self._bottom_separator_overhang_right) * M_TO_MM
            return (min, max)

    @property
    def bottom_separator_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self) == Laminate:
                return (0.0, 500.0)
            else:
                return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            min = 0
            max = (self._bottom_separator_overhang_left + self._bottom_separator_overhang_right) * M_TO_MM
            return (min, max)

    @property
    def bottom_separator_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            min = 0
            max = (self._bottom_separator_overhang_bottom + self._bottom_separator_overhang_top) * M_TO_MM
            return (min, max)

    @property
    def bottom_separator_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            min = 0
            max = (self._bottom_separator_overhang_bottom + self._bottom_separator_overhang_top) * M_TO_MM
            return (min, max)

    #### TOP SEPARATOR OVERHANG PROPERTY/SETTERS ####

    @property
    def top_separator_overhang_left(self) -> float:
        """
        Get the left overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_left * M_TO_MM, 3)

    @property
    def top_separator_overhang_right(self) -> float:
        """
        Get the right overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_right * M_TO_MM, 3)

    @property
    def top_separator_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_bottom * M_TO_MM, 3)

    @property
    def top_separator_overhang_top(self) -> float:
        """
        Get the top overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_top * M_TO_MM, 3)

    @property
    def top_separator_overhangs(self) -> dict:
        """
        Get all top separator overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.top_separator_overhang_left,
            "right": self.top_separator_overhang_right,
            "bottom": self.top_separator_overhang_bottom,
            "top": self.top_separator_overhang_top,
        }

    @top_separator_overhang_left.setter
    @calculate_all_properties
    def top_separator_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "top_separator_overhang_left")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("top_separator", overhang, "left")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("top_separator", overhang, "left")

    @top_separator_overhang_right.setter
    @calculate_all_properties
    def top_separator_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "top_separator_overhang_right")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("top_separator", overhang, "right")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("top_separator", overhang, "right")

    @top_separator_overhang_bottom.setter
    @calculate_all_properties
    def top_separator_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "top_separator_overhang_bottom")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("top_separator", overhang, "bottom")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("top_separator", overhang, "bottom")

    @top_separator_overhang_top.setter
    @calculate_all_properties
    def top_separator_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self.validate_positive_float(overhang, "top_separator_overhang_top")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component("top_separator", overhang, "top")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs("top_separator", overhang, "top")

    #### TOP SEPARATOR OVERHANG RANGE PROPERTIES ####

    @property
    def top_separator_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self) == Laminate:
                return (0.0, 500.0)
            else:
                return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (
                0.0,
                self.top_separator_overhang_left + self.top_separator_overhang_right,
            )

    @property
    def top_separator_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self) == Laminate:
                return (0.0, 500.0)
            else:
                return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (
                0.0,
                self.top_separator_overhang_left + self.top_separator_overhang_right,
            )

    @property
    def top_separator_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (
                0.0,
                self.top_separator_overhang_bottom + self.top_separator_overhang_top,
            )

    @property
    def top_separator_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (
                0.0,
                self.top_separator_overhang_bottom + self.top_separator_overhang_top,
            )

    #### OVERHANG CONTROL MODE ####

    @property
    def overhang_control_mode(self) -> OverhangControlMode:
        """Get the current overhang control mode."""
        return self._overhang_control_mode

    @overhang_control_mode.setter
    def overhang_control_mode(self, mode: OverhangControlMode):

        if isinstance(mode, OverhangControlMode):
            self._overhang_control_mode = mode
            return
        
        elif isinstance(mode, str):
            for enum_member in OverhangControlMode:
                if mode.lower().replace(" ", "_") == enum_member.value:
                    self._overhang_control_mode = enum_member
                    return

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


class Laminate(_Layup):
    def __init__(
        self,
        cathode: Cathode,
        bottom_separator: Separator,
        anode: Anode,
        top_separator: Separator,
        name: str = "Layup",
    ):
        if not anode._flipped_y:
            anode._flip("y")

        super().__init__(
            cathode=cathode,
            bottom_separator=bottom_separator,
            anode=anode,
            top_separator=top_separator,
            name=name,
        )

    def _calculate_all_properties(self):
        
        # First call parent method to calculate all standard properties
        super()._calculate_all_properties()
        
        # Then validate that current collectors are of the correct type
        self.validate_type(
            self.anode.current_collector,
            _TapeCurrentCollector,
            "Anode Current Collector",
        )
        
        self.validate_type(
            self.cathode.current_collector,
            _TapeCurrentCollector,
            "Cathode Current Collector",
        )

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._top_separator._set_length_range(self._anode, extended_range=1)
        self._bottom_separator._set_width_range(self._cathode, extended_range=0.1)
        self._bottom_separator._set_length_range(self._cathode, extended_range=1)


class MonoLayer(_Layup):
    """
    Class for a MonoLayer, which is a combination of anode, cathode, and separator. This class represents the
    item which will be repeated in space to form a z-fold stack.
    """

    def __init__(
        self,
        cathode: Cathode,
        bottom_separator: Separator,
        anode: Anode,
        top_separator: Separator,
        transverse: bool = False,
        name: str = "MonoLayer",
    ):
        """
        Initialize the MonoLayer with the given components and offsets.

        Parameters
        ----------
        anode : Anode
            The anode component of the monolayer.
        cathode : Cathode
            The cathode component of the monolayer.
        separator : Separator
            The separator component of the monolayer.
        anode_offset : tuple
            The (x, y) offset for the anode in mm.
        bottom_separator_offset : float
            The (x, y) offset for the bottom separator in mm.
        top_separator_offset : float
            The (x, y) offset for the top separator in mm.
        transverse : bool
            Whether the monolayer is oriented transversely (default: False).
        """
        # Initialize parent class first
        super().__init__(
            cathode=cathode,
            bottom_separator=bottom_separator,
            anode=anode,
            top_separator=top_separator,
            name=name,
        )

        # Add MonoLayer-specific components and properties
        self.transverse = transverse

        # Recalculate properties now that separator is set
        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):

        super()._calculate_all_properties()

        self.validate_type(
            self.anode.current_collector,
            PunchedCurrentCollector,
            "Anode Current Collector",
        )

        self.validate_type(
            self.cathode.current_collector,
            PunchedCurrentCollector,
            "Cathode Current Collector",
        )

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._top_separator._set_length_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_width_range(self._cathode, extended_range=0.1)
        self._bottom_separator._set_length_range(self._cathode, extended_range=0.1)

    @classmethod
    def from_zfold_monolayer(cls, zfold_monolayer: "ZFoldMonoLayer") -> "MonoLayer":
        """
        Create a MonoLayer instance from a ZFoldMonoLayer instance.

        Parameters
        ----------
        zfold_monolayer : ZFoldMonoLayer
            The ZFoldMonoLayer instance to convert.

        Returns
        -------
        MonoLayer
            A new MonoLayer instance with the same properties as the input ZFoldMonoLayer.
        """
        bottom_separator = deepcopy(zfold_monolayer._bottom_separator)
        bottom_separator.width = zfold_monolayer.anode.current_collector.x_body_length + 4
        bottom_separator.length = zfold_monolayer.anode.current_collector.y_body_length + 4

        top_separator = deepcopy(bottom_separator)

        return cls(
            cathode=deepcopy(zfold_monolayer.cathode),
            bottom_separator=bottom_separator,
            anode=deepcopy(zfold_monolayer.anode),
            top_separator=top_separator,
            transverse=zfold_monolayer.transverse,
        )

    @property
    def transverse(self):
        return self._transverse

    @property
    def bottom_separator(self) -> Separator:
        return self._bottom_separator

    @property
    def top_separator(self) -> Separator:
        return self._top_separator

    @transverse.setter
    def transverse(self, transverse: bool) -> None:
        """
        Set the transverse orientation of the monolayer.

        When transverse is True, ensures the anode tab comes out the bottom
        by flipping the anode if it's not already flipped in the y direction.

        Parameters
        ----------
        transverse : bool
            Whether the monolayer is oriented transversely.
        """
        # validate the type
        self.validate_type(transverse, bool, "transverse")

        # set the transverse orientation
        self._transverse = transverse

        # if transverse is True, check and adjust anode orientation
        if transverse and hasattr(self, "_anode") and self._anode is not None:
            if not self._anode._flipped_y:
                self._anode._flip("y")
        elif not transverse and hasattr(self, "_anode") and self._anode is not None:
            if self._anode._flipped_y:
                self._anode._flip("y")

    @bottom_separator.setter
    @calculate_all_properties
    def bottom_separator(self, bottom_separator: Separator):
        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # make deep copy
        bottom_separator = deepcopy(bottom_separator)

        # if there is an anode, update its ranges
        if not self._update_properties:
            bottom_separator.datum = (
                self.cathode.datum[0],
                self.cathode.datum[1],
                bottom_separator.datum[2],
            )
        elif self._update_properties:
            bottom_separator.datum = (
                self.bottom_separator.datum[0],
                self.bottom_separator.datum[1],
                bottom_separator.datum[2],
            )

        # assign to self
        self._bottom_separator = bottom_separator

        # Add MonoLayer-specific rotation logic
        if hasattr(self._bottom_separator, "_rotated_xy") and not self._bottom_separator._rotated_xy:
            self._bottom_separator._rotate_90_xy()

    @top_separator.setter
    @calculate_all_properties
    def top_separator(self, top_separator: Separator):
        # validate the type
        self.validate_type(top_separator, Separator, "Top Separator")

        # make deep copy
        top_separator = deepcopy(top_separator)

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

        # Add MonoLayer-specific rotation logic
        if hasattr(self._top_separator, "_rotated_xy") and not self._top_separator._rotated_xy:
            self._top_separator._rotate_90_xy()


class ZFoldMonoLayer(MonoLayer):
    """
    A specialized MonoLayer for Z-fold battery configurations.

    In Z-fold configuration, the separator is folded in a Z-shape where:
    - Left and right overhangs are constrained to 0 (Z-fold geometry)
    - Top and bottom overhangs are synchronized between both separator layers
    - A unified separator interface manages both top and bottom separators
    """

    def __init__(
        self,
        cathode: Cathode,
        separator: Separator,
        anode: Anode,
        transverse: bool = False,
        name: str = "Z-Fold MonoLayer",
    ):
        self._update_properties = False

        # Create copies of the separator with Z-fold length constraints
        top_separator = deepcopy(separator)
        bottom_separator = deepcopy(separator)
        top_separator.length = (anode.current_collector._x_body_length + 2 * top_separator._thickness) * M_TO_MM
        bottom_separator.length = (cathode.current_collector._x_body_length + 2 * bottom_separator._thickness) * M_TO_MM

        # Bypass MonoLayer.__init__ to avoid calling blocked setters
        # Call _Layup.__init__ directly and set up necessary attributes
        self._overhang_control_mode = OverhangControlMode.FIXED_COMPONENT
        self._np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE

        self.cathode = cathode
        self.anode = anode
        self._top_separator = top_separator
        self._bottom_separator = bottom_separator
        self._transverse = transverse
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):

        super()._calculate_all_properties()

        # set separator width/length ranges based on anode size
        self._bottom_separator._set_width_range(self._anode, extended_range=0.1)

    # ============================================================================
    # Core Component Properties
    # ============================================================================

    @classmethod
    def from_monolayer(cls, monolayer: MonoLayer) -> "ZFoldMonoLayer":

        separator = deepcopy(monolayer.bottom_separator)

        # Ensure separator is rotated to have length along the x axis
        if separator._rotated_xy:
            separator._rotate_90_xy()

        # ensure the separator width is wide enough
        if separator.width < (monolayer.anode.current_collector.y_body_length):
            separator.width = monolayer.anode.current_collector.y_body_length

        return cls(
            cathode=deepcopy(monolayer.cathode),
            separator=separator,
            anode=deepcopy(monolayer.anode),
            transverse=monolayer.transverse,
        )

    @property
    def separator(self) -> Separator:
        """
        Get the Z-fold separator. Returns the bottom separator as the canonical reference.
        In Z-fold configuration, both separators are constrained to be identical.
        """
        return self._bottom_separator

    @separator.setter
    @calculate_all_properties
    def separator(self, separator: Separator):
        """
        Set both bottom and top separators for Z-fold configuration.

        Parameters
        ----------
        separator : Separator
            The separator to use for both top and bottom positions.
            Length will be automatically constrained by Z-fold geometry.
        """
        # Validate the type
        self.validate_type(separator, Separator, "Separator")

        # Create deep copies for both positions
        bottom_separator = deepcopy(separator)
        top_separator = deepcopy(separator)

        # Set lengths according to Z-fold constraints
        bottom_separator.length = (self.cathode.current_collector._x_body_length + 2 * bottom_separator._thickness) * M_TO_MM
        top_separator.length = (self.anode.current_collector._x_body_length + 2 * top_separator._thickness) * M_TO_MM

        # make sure it is wide enough for the anode
        if bottom_separator.width < (self.anode.current_collector.y_body_length):
            bottom_separator.width = self.anode.current_collector.y_body_length
            top_separator.width = self.anode.current_collector.y_body_length

        # Set positions based on existing datums if updating properties
        if not self._update_properties:
            bottom_separator.datum = (
                self._cathode.datum[0],
                self._cathode.datum[1],
                bottom_separator.datum[2],
            )
            top_separator.datum = (
                self._anode.datum[0],
                self._anode.datum[1],
                top_separator.datum[2],
            )
        elif self._update_properties:
            bottom_separator.datum = (
                self._cathode.datum[0],
                self._bottom_separator.datum[1],
                bottom_separator.datum[2],
            )
            top_separator.datum = (
                self._anode.datum[0],
                self._top_separator.datum[1],
                top_separator.datum[2],
            )

        # Assign to both internal separators
        self._bottom_separator = bottom_separator
        self._top_separator = top_separator

    # ============================================================================
    # Unified Separator Overhang Properties
    # ============================================================================

    @property
    def separator_overhang_left(self) -> float:
        """Get the left overhang of the Z-fold separator. Always 0.0 due to Z-fold constraints."""
        return 0.0

    @property
    def separator_overhang_right(self) -> float:
        """Get the right overhang of the Z-fold separator. Always 0.0 due to Z-fold constraints."""
        return 0.0

    @property
    def separator_overhang_bottom(self) -> float:
        """Get the bottom overhang of the Z-fold separator."""
        return super().bottom_separator_overhang_bottom

    @separator_overhang_bottom.setter
    @calculate_all_properties
    def separator_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang for the Z-fold separator.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Applied to both separator layers.
        """
        self.validate_positive_float(overhang, "separator_overhang_bottom")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_zfold_overhang_fixed_component("bottom_separator", overhang, "bottom")
            self._adjust_zfold_overhang_fixed_component("top_separator", overhang, "bottom")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_zfold_overhang_fixed_overhangs("bottom_separator", overhang, "bottom")
            self._adjust_zfold_overhang_fixed_overhangs("top_separator", overhang, "bottom")

    @property
    def separator_overhang_top(self) -> float:
        """Get the top overhang of the Z-fold separator."""
        return super().bottom_separator_overhang_top

    @separator_overhang_top.setter
    @calculate_all_properties
    def separator_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang for the Z-fold separator.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Applied to both separator layers.
        """
        self.validate_positive_float(overhang, "separator_overhang_top")

        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            # Move both separators to achieve the target overhang
            self._adjust_zfold_overhang_fixed_component("bottom_separator", overhang, "top")
            self._adjust_zfold_overhang_fixed_component("top_separator", overhang, "top")
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            # Extend both separators to achieve the target overhang
            self._adjust_zfold_overhang_fixed_overhangs("bottom_separator", overhang, "top")
            self._adjust_zfold_overhang_fixed_overhangs("top_separator", overhang, "top")

    @property
    def separator_overhangs(self) -> dict:
        """
        Get all separator overhangs as a dictionary.
        Note: In Z-fold configuration, left/right overhangs are always 0.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
            Left and right values are always 0.0 due to Z-fold constraints.
        """
        return {
            "left": 0.0,
            "right": 0.0,
            "bottom": self.separator_overhang_bottom,
            "top": self.separator_overhang_top,
        }

    # ============================================================================
    # Range Properties
    # ============================================================================

    @property
    def separator_overhang_bottom_range(self) -> tuple:
        """Get the valid range for bottom separator overhang."""
        return self.bottom_separator_overhang_bottom_range

    @property
    def separator_overhang_top_range(self) -> tuple:
        """Get the valid range for top separator overhang."""
        return self.bottom_separator_overhang_top_range

    # ============================================================================
    # Internal/Helper Methods
    # ============================================================================

    def _calculate_bottom_separator_overhangs(self):
        """
        Override: Calculate overhangs for Z-fold separators.
        Left/right overhangs are constrained by Z-fold geometry.
        Top/bottom overhangs are shared between top and bottom separators.
        """
        if hasattr(self, "_cathode") and hasattr(self, "_bottom_separator") and self._cathode is not None and self._bottom_separator is not None:
            # Cathode edges (using internal SI units - meters)
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Bottom separator edges (using internal SI units - meters)
            separator_bottom = min(self._bottom_separator._coordinates[:, 1])
            separator_top = max(self._bottom_separator._coordinates[:, 1])

            # Calculate only top/bottom overhangs (left/right are constrained)
            self._bottom_separator_overhang_left = 0.0  # Constrained by Z-fold
            self._bottom_separator_overhang_right = 0.0  # Constrained by Z-fold
            self._bottom_separator_overhang_bottom = cathode_bottom - separator_bottom
            self._bottom_separator_overhang_top = separator_top - cathode_top

            # Ensure top separator has the same overhangs (Z-fold constraint)
            if hasattr(self, "_top_separator") and self._top_separator is not None:
                self._top_separator_overhang_left = 0.0  # Constrained by Z-fold
                self._top_separator_overhang_right = 0.0  # Constrained by Z-fold
                self._top_separator_overhang_bottom = self._bottom_separator_overhang_bottom
                self._top_separator_overhang_top = self._bottom_separator_overhang_top

        else:
            # Set default values if components are not available
            self._bottom_separator_overhang_left = 0.0
            self._bottom_separator_overhang_right = 0.0
            self._bottom_separator_overhang_bottom = 0.0
            self._bottom_separator_overhang_top = 0.0

    def _calculate_top_separator_overhangs(self):
        """
        Override: Top separator overhangs are synchronized with bottom separator.
        This method does nothing since overhangs are set in _calculate_bottom_separator_overhangs.
        """
        # Overhangs are calculated and synchronized in _calculate_bottom_separator_overhangs
        pass

    def _adjust_zfold_overhang_fixed_component(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust separator position to achieve target overhang (Z-fold specific).

        Parameters
        ----------
        component : str
            Component name ('bottom_separator' or 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        # Access internal overhang values directly to avoid AttributeError
        # Use internal property names which return values in meters (not mm)
        if component == "bottom_separator":
            current_overhang = getattr(self, f"_bottom_separator_overhang_{direction}") * M_TO_MM
        elif component == "top_separator":
            current_overhang = getattr(self, f"_top_separator_overhang_{direction}") * M_TO_MM
        else:
            raise ValueError(f"Unknown component: {component}")

        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        # get component datum
        datum = component_obj.datum

        if direction == "left":
            datum = (datum[0] - overhang_difference, datum[1], datum[2])
        elif direction == "right":
            datum = (datum[0] + overhang_difference, datum[1], datum[2])
        elif direction == "bottom":
            datum = (datum[0], datum[1] - overhang_difference, datum[2])
        elif direction == "top":
            datum = (datum[0], datum[1] + overhang_difference, datum[2])

        # set the datum
        component_obj.datum = datum

    def _adjust_zfold_overhang_fixed_overhangs(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust separator dimensions to achieve target overhang (Z-fold specific).

        Parameters
        ----------
        component : str
            Component name ('bottom_separator' or 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        # Access internal overhang values directly to avoid AttributeError
        # Use internal property names which return values in meters (not mm)
        if component == "bottom_separator":
            current_overhang = getattr(self, f"_bottom_separator_overhang_{direction}")
        elif component == "top_separator":
            current_overhang = getattr(self, f"_top_separator_overhang_{direction}")
        else:
            raise ValueError(f"Unknown component: {component}")

        target_overhang = target_overhang * MM_TO_M
        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        # Use the same logic as the parent class for separators
        position_adjustment = (overhang_difference / 2) * M_TO_MM

        # Determine which dimension to adjust based on rotation and direction
        is_horizontal = direction in ["left", "right"]
        is_rotated = component_obj._rotated_xy

        # Logic: if rotated, horizontal directions affect width, vertical affects length
        # If not rotated, horizontal directions affect length, vertical affects width
        if (is_horizontal and not is_rotated) or (not is_horizontal and is_rotated):
            # Adjust length
            component_obj.length += overhang_difference * M_TO_MM
        else:
            # Adjust width
            component_obj.width += overhang_difference * M_TO_MM

        # Adjust position
        if direction == "left":
            component_obj.datum_x -= position_adjustment
        elif direction == "right":
            component_obj.datum_x += position_adjustment
        elif direction == "bottom":
            component_obj.datum_y -= position_adjustment
        else:  # top
            component_obj.datum_y += position_adjustment

    # ============================================================================
    # Blocked Properties - Individual Separator APIs Disabled
    # ============================================================================

    @property
    def bottom_separator(self) -> None:
        return None

    @property
    def top_separator(self) -> None:
        return None

    @property
    def bottom_separator_overhang_bottom(self) -> None:
        return None

    @property
    def bottom_separator_overhang_top(self) -> None:
        return None

    @property
    def bottom_separator_overhang_left(self) -> None:
        return None

    @property
    def bottom_separator_overhang_right(self) -> None:
        return None

    @property
    def top_separator_overhang_bottom(self) -> None:
        return None

    @property
    def top_separator_overhang_top(self) -> None:
        return None

    @property
    def top_separator_overhang_left(self) -> None:
        return None

    @property
    def top_separator_overhang_right(self) -> None:
        return None

