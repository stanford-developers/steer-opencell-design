from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Components.CurrentCollectors import _TapeCurrentCollector, PunchedCurrentCollector

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_core.Decorators.General import calculate_all_properties

from App.styles import *
from steer_core.Constants.Units import *

from copy import copy, deepcopy
import plotly.graph_objects as go
from typing import Tuple
from enum import Enum


class OverhangControlMode(Enum):
    """Control modes for anode overhang adjustments."""
    FIXED_COMPONENT = "fixed_component"    # Move anode position to achieve overhang
    FIXED_OVERHANGS = "fixed_overhangs"    # Extend anode body to achieve overhang


class _Layup(CoordinateMixin, ValidationMixin, SerializerMixin):
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
            name: str = "Layup"
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
        self.cathode = cathode
        self.bottom_separator = bottom_separator
        self.anode = anode
        self.top_separator = top_separator
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        self._calculate_anode_overhangs()
        self._calculate_bottom_separator_overhangs()
        self._calculate_top_separator_overhangs()
        self._set_z_positions()

    def _set_z_positions(self):

        _bottom_separator_z = self._cathode._current_collector._datum[2] + (self._cathode._thickness/2 + self._bottom_separator._thickness/2) * UM_TO_M
        _anode_z = _bottom_separator_z + (self._bottom_separator._thickness/2 + self._anode._thickness/2) * UM_TO_M
        _top_separator_z = _anode_z + (self._anode._thickness/2 + self._top_separator._thickness/2) * UM_TO_M

        self._bottom_separator.datum = (
            self._bottom_separator.datum[0],
            self._bottom_separator.datum[1],
            _bottom_separator_z * M_TO_MM
        )

        self.anode.datum = (
            self.anode.datum[0],
            self.anode.datum[1],
            _anode_z * M_TO_MM
        )

        self._top_separator.datum = (
            self._top_separator.datum[0],
            self._top_separator.datum[1],
            _top_separator_z * M_TO_MM
        )

    def _calculate_anode_overhangs(self):
        """
        Calculate the anode overhangs relative to the cathode.
        """
        if hasattr(self, '_cathode') and hasattr(self, '_anode') and self._cathode is not None and self._anode is not None:

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
        if hasattr(self, '_cathode') and hasattr(self, '_bottom_separator') and self._cathode is not None and self._bottom_separator is not None:

            # Cathode edges (using internal SI units - meters)
            cathode_left = self._cathode._current_collector._datum[0] - self._cathode._current_collector._x_body_length / 2
            cathode_right = self._cathode._current_collector._datum[0] + self._cathode._current_collector._x_body_length / 2
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Bottom separator edges (using internal SI units - meters)
            separator_left = min(self._bottom_separator._coordinates[:,0])
            separator_right = max(self._bottom_separator._coordinates[:,0])
            separator_bottom = min(self._bottom_separator._coordinates[:,1])
            separator_top = max(self._bottom_separator._coordinates[:,1])

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
        if hasattr(self, '_cathode') and hasattr(self, '_top_separator') and self._cathode is not None and self._top_separator is not None:

            # Cathode edges (using internal SI units - meters)
            cathode_left = self._cathode._current_collector._datum[0] - self._cathode._current_collector._x_body_length / 2
            cathode_right = self._cathode._current_collector._datum[0] + self._cathode._current_collector._x_body_length / 2
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Top separator edges (using internal SI units - meters)
            separator_left = min(self._top_separator._coordinates[:,0])
            separator_right = max(self._top_separator._coordinates[:,0])
            separator_bottom = min(self._top_separator._coordinates[:,1])
            separator_top = max(self._top_separator._coordinates[:,1])
            
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
        current_overhang = getattr(self, f'{component}_overhang_{direction}')
        overhang_difference = target_overhang - current_overhang
        
        # Get the component object
        component_obj = getattr(self, f'_{component}')
        
        # get component datum
        datum = component_obj.datum

        if direction == 'left':
            datum = (datum[0] - overhang_difference, datum[1], datum[2])
        elif direction == 'right':
            datum = (datum[0] + overhang_difference, datum[1], datum[2])
        elif direction == 'bottom':
            datum = (datum[0], datum[1] - overhang_difference, datum[2])
        elif direction == 'top':
            datum = (datum[0], datum[1] + overhang_difference, datum[2])

        component_obj.datum = datum

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
        current_overhang = getattr(self, f'_{component}_overhang_{direction}')
        overhang_difference = target_overhang - current_overhang
        
        # Get the component object
        component_obj = getattr(self, f'_{component}')
        
        if component == 'anode':
            # Determine which dimension and position to adjust
            if direction in ['left', 'right']:
                self.anode.current_collector.x_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == 'left':
                    self.anode.current_collector.datum_x -= position_adjustment
                else:  # right
                    self.anode.current_collector.datum_x += position_adjustment
            else:  # bottom or top
                self.anode.current_collector.y_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == 'bottom':
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
            is_horizontal = direction in ['left', 'right']
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
            if direction == 'left':
                component_obj.datum_x -= position_adjustment
            elif direction == 'right':
                component_obj.datum_x += position_adjustment
            elif direction == 'bottom':
                component_obj.datum_y -= position_adjustment
            else:  # top
                component_obj.datum_y += position_adjustment

            # Trigger setter
            setattr(self, component, component_obj)

    def get_top_down_view(self, opacity: float = 0.2, **kwargs) -> go.Figure:

        def adjust_fill_opacity(color_str, opacity):
            """Helper function to adjust fill opacity while preserving line opacity"""
            if not color_str:
                return color_str
            
            if 'rgba' in color_str:
                # Replace the alpha value in existing rgba
                return color_str.rsplit(',', 1)[0] + f', {opacity})'
            elif 'rgb' in color_str:
                # Convert rgb to rgba
                return color_str.replace('rgb(', 'rgba(').replace(')', f', {opacity})')
            elif color_str.startswith('#'):
                # Convert hex to rgba
                hex_color = color_str.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return f'rgba({r}, {g}, {b}, {opacity})'
            
            # For named colors or other formats, return as is
            return color_str

        fig = go.Figure()

        # Get trace groups
        cathode_fig = self._cathode._get_full_top_down_view()
        for i, trace in enumerate(cathode_fig.data):
            trace.name = self._cathode.name
            trace.legendgroup = self._cathode.name
            trace.showlegend = i == 0
            # Adjust fill opacity while keeping line opacity at 1.0
            if hasattr(trace, 'fillcolor') and trace.fillcolor:
                trace.fillcolor = adjust_fill_opacity(trace.fillcolor, opacity)
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
        # Adjust fill opacity while keeping line opacity at 1.0
        if hasattr(bottom_separator_trace, 'fillcolor') and bottom_separator_trace.fillcolor:
            bottom_separator_trace.fillcolor = adjust_fill_opacity(bottom_separator_trace.fillcolor, opacity)
        fig.add_trace(bottom_separator_trace)

        anode_fig = self._anode._get_full_top_down_view()
        for i, trace in enumerate(anode_fig.data):
            trace.name = self._anode.name
            trace.legendgroup = self._anode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            # Adjust fill opacity while keeping line opacity at 1.0
            if hasattr(trace, 'fillcolor') and trace.fillcolor:
                trace.fillcolor = adjust_fill_opacity(trace.fillcolor, opacity)
            fig.add_trace(trace)

        # Add top separator
        top_separator_trace = copy(self._top_separator.top_down_trace)
        if separators_same_name:
            top_separator_trace.name = f"{self._top_separator.name} (Top)"
            top_separator_trace.legendgroup = f"{self._top_separator.name}_top"
        else:
            top_separator_trace.name = f"{self._top_separator.name}"
            top_separator_trace.legendgroup = f"{self._top_separator.name}"
        # Adjust fill opacity while keeping line opacity at 1.0
        if hasattr(top_separator_trace, 'fillcolor') and top_separator_trace.fillcolor:
            top_separator_trace.fillcolor = adjust_fill_opacity(top_separator_trace.fillcolor, opacity)
        fig.add_trace(top_separator_trace)

        # Calculate overall bounds to fix axis ranges
        all_x = []
        all_y = []
        
        # Collect coordinates from all traces
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None:
                all_x.extend([x for x in trace.x if x is not None])
            if hasattr(trace, 'y') and trace.y is not None:
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
                title='', 
                showticklabels=False,
                range=x_bounds,
                fixedrange=True
            ),
            yaxis=dict(
                showgrid=False, 
                zeroline=False, 
                title='', 
                showticklabels=False,
                range=y_bounds,
                fixedrange=True
            ),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            title=kwargs.get('title', f"{self.name} Top-Down View"),
            **kwargs
        )

        return fig

    #### COMPONENT PROPERTY/SETTERS ####

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
    @calculate_all_properties
    def bottom_separator(self, bottom_separator: Separator):

        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # make deep copy
        bottom_separator = deepcopy(bottom_separator)

        # if there is an anode, update its ranges
        if not self._update_properties:
            bottom_separator.datum = (self.cathode.datum[0], self.cathode.datum[1], bottom_separator.datum[2])
        elif self._update_properties:
            bottom_separator.datum = (self.bottom_separator.datum[0], self.bottom_separator.datum[1], bottom_separator.datum[2])
           
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
            top_separator.datum = (self.cathode.datum[0], self.cathode.datum[1], top_separator.datum[2])
        elif self._update_properties:
            top_separator.datum = (self.top_separator.datum[0], self.top_separator.datum[1], top_separator.datum[2])

        # assign to self
        self._top_separator = top_separator

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
        return round(self._anode_overhang_left * M_TO_MM, 3)

    @property
    def anode_overhang_right(self) -> float:
        """
        Get the right overhang of the anode relative to the cathode in mm.
        
        Returns
        -------
        float
            Right overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_right * M_TO_MM, 3)

    @property
    def anode_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the anode relative to the cathode in mm.
        
        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_bottom * M_TO_MM, 3)

    @property
    def anode_overhang_top(self) -> float:
        """
        Get the top overhang of the anode relative to the cathode in mm.
        
        Returns
        -------
        float
            Top overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_top * M_TO_MM, 3)

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
            'left': self.anode_overhang_left,
            'right': self.anode_overhang_right,
            'bottom': self.anode_overhang_bottom,
            'top': self.anode_overhang_top
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
            self._adjust_overhang_fixed_component('anode', overhang, 'left')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('anode', overhang, 'left')

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
            self._adjust_overhang_fixed_component('anode', overhang, 'right')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('anode', overhang, 'right')

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
            self._adjust_overhang_fixed_component('anode', overhang, 'bottom')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('anode', overhang, 'bottom')

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
            self._adjust_overhang_fixed_component('anode', overhang, 'top')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('anode', overhang, 'top')

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
            'left': self.bottom_separator_overhang_left,
            'right': self.bottom_separator_overhang_right,
            'bottom': self.bottom_separator_overhang_bottom,
            'top': self.bottom_separator_overhang_top
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
            self._adjust_overhang_fixed_component('bottom_separator', overhang, 'left')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('bottom_separator', overhang, 'left')

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
            self._adjust_overhang_fixed_component('bottom_separator', overhang, 'right')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('bottom_separator', overhang, 'right')

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
            self._adjust_overhang_fixed_component('bottom_separator', overhang, 'bottom')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('bottom_separator', overhang, 'bottom')

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
            self._adjust_overhang_fixed_component('bottom_separator', overhang, 'top')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('bottom_separator', overhang, 'top')

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
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.bottom_separator_overhang_left + self.bottom_separator_overhang_right)

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
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.bottom_separator_overhang_left + self.bottom_separator_overhang_right)

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
            return (0.0, self.bottom_separator_overhang_bottom + self.bottom_separator_overhang_top)

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
            return (0.0, self.bottom_separator_overhang_bottom + self.bottom_separator_overhang_top)

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
            'left': self.top_separator_overhang_left,
            'right': self.top_separator_overhang_right,
            'bottom': self.top_separator_overhang_bottom,
            'top': self.top_separator_overhang_top
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
            self._adjust_overhang_fixed_component('top_separator', overhang, 'left')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('top_separator', overhang, 'left')

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
            self._adjust_overhang_fixed_component('top_separator', overhang, 'right')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('top_separator', overhang, 'right')

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
            self._adjust_overhang_fixed_component('top_separator', overhang, 'bottom')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('top_separator', overhang, 'bottom')

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
            self._adjust_overhang_fixed_component('top_separator', overhang, 'top')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs('top_separator', overhang, 'top')

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
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.top_separator_overhang_left + self.top_separator_overhang_right)

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
            return (0.0, 20.0)
        else:  # FIXED_COMPONENT
            return (0.0, self.top_separator_overhang_left + self.top_separator_overhang_right)

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
            return (0.0, self.top_separator_overhang_bottom + self.top_separator_overhang_top)

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
            return (0.0, self.top_separator_overhang_bottom + self.top_separator_overhang_top)

    #### OVERHANG CONTROL MODE ####

    @property
    def overhang_control_mode(self) -> OverhangControlMode:
        """Get the current overhang control mode."""
        return self._overhang_control_mode
  
    @overhang_control_mode.setter
    def overhang_control_mode(self, mode: OverhangControlMode):
        self.validate_type(mode, OverhangControlMode, "overhang_control_mode")
        self._overhang_control_mode = mode
 
    #### STRING REPRESENTATIONS ####

    def __str__(self):
        """
        String representation of the Layup object.
        
        Returns
        -------
        str
            A string representation of the MonoLayer.
        """
        return f"{self.__class__.__name__}: {self.name} | Anode: {self.anode.name} | Cathode: {self.cathode.name} | Bottom Sep: {self.bottom_separator.name} | Top Sep: {self.top_separator.name} | Anode Overhangs (L,R,B,T): ({self.anode_overhang_left} mm, {self.anode_overhang_right} mm, {self.anode_overhang_bottom} mm, {self.anode_overhang_top} mm) | Bottom Sep Overhangs (L,R,B,T): ({self.bottom_separator_overhang_left} mm, {self.bottom_separator_overhang_right} mm, {self.bottom_separator_overhang_bottom} mm, {self.bottom_separator_overhang_top} mm) | Top Sep Overhangs (L,R,B,T): ({self.top_separator_overhang_left} mm, {self.top_separator_overhang_right} mm, {self.top_separator_overhang_bottom} mm, {self.top_separator_overhang_top} mm)"

    def __repr__(self):
        """
        Official string representation of the MonoLayer object.
        
        Returns
        -------
        str
            An official string representation of the MonoLayer.
        """
        return self.__str__()


class Laminate(_Layup):
    
    def __init__(
            self,
            cathode: Cathode,
            bottom_separator: Separator,
            anode: Anode,
            top_separator: Separator,
            name: str = "Layup"
        ):

        if not anode._flipped_y:
            anode._flip('y')

        super().__init__(
            cathode=cathode,
            bottom_separator=bottom_separator,
            anode=anode,
            top_separator=top_separator,
            name=name
        )

    def _calculate_all_properties(self):
        super()._calculate_all_properties()
        self.validate_type(self.anode.current_collector, _TapeCurrentCollector, "Anode Current Collector")
        self.validate_type(self.cathode.current_collector, _TapeCurrentCollector, "Cathode Current Collector")


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
            name: str = "MonoLayer"
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
            name=name
        )
        
        # Add MonoLayer-specific components and properties
        self.transverse = transverse
        
        # Recalculate properties now that separator is set
        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        super()._calculate_all_properties()
        self.validate_type(self.anode.current_collector, PunchedCurrentCollector, "Anode Current Collector")
        self.validate_type(self.cathode.current_collector, PunchedCurrentCollector, "Cathode Current Collector")

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
        if transverse and hasattr(self, '_anode') and self._anode is not None:
            if not self._anode._flipped_y:
                self._anode._flip('y')

    @bottom_separator.setter
    @calculate_all_properties
    def bottom_separator(self, bottom_separator: Separator):

        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # make deep copy
        bottom_separator = deepcopy(bottom_separator)

        # if there is an anode, update its ranges
        if not self._update_properties:
            bottom_separator.datum = (self.cathode.datum[0], self.cathode.datum[1], bottom_separator.datum[2])
        elif self._update_properties:
            bottom_separator.datum = (self.bottom_separator.datum[0], self.bottom_separator.datum[1], bottom_separator.datum[2])
           
        # assign to self
        self._bottom_separator = bottom_separator
        
        # Add MonoLayer-specific rotation logic
        if hasattr(self._bottom_separator, '_rotated_xy') and not self._bottom_separator._rotated_xy:
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
            top_separator.datum = (self.cathode.datum[0], self.cathode.datum[1], top_separator.datum[2])
        elif self._update_properties:
            top_separator.datum = (self.top_separator.datum[0], self.top_separator.datum[1], top_separator.datum[2])

        # assign to self
        self._top_separator = top_separator
        
        # Add MonoLayer-specific rotation logic
        if hasattr(self._top_separator, '_rotated_xy') and not self._top_separator._rotated_xy:
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
            overhang_control_mode: OverhangControlMode = OverhangControlMode.FIXED_COMPONENT,
            name: str = "Z-Fold MonoLayer"
        ):

        self._update_properties = False

        # Create copies of the separator with Z-fold length constraints
        top_separator = deepcopy(separator)
        bottom_separator = deepcopy(separator)

        top_separator.length = (anode.current_collector._x_body_length + 2*top_separator._thickness) * M_TO_MM
        bottom_separator.length = (cathode.current_collector._x_body_length + 2*bottom_separator._thickness) * M_TO_MM

        # Bypass MonoLayer.__init__ to avoid calling blocked setters
        # Call _Layup.__init__ directly and set up necessary attributes
        self._overhang_control_mode = overhang_control_mode
        self._cathode = cathode
        self._anode = anode
        self._top_separator = top_separator
        self._bottom_separator = bottom_separator
        self._transverse = transverse
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True

    # ============================================================================
    # Core Component Properties
    # ============================================================================

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
        bottom_separator.length = (self.cathode.current_collector._x_body_length + 2*bottom_separator._thickness) * M_TO_MM
        top_separator.length = (self.anode.current_collector._x_body_length + 2*top_separator._thickness) * M_TO_MM

        # Set positions based on existing datums if updating properties
        if not self._update_properties:
            bottom_separator.datum = (self._cathode.datum[0], self._cathode.datum[1], bottom_separator.datum[2])
            top_separator.datum = (self._anode.datum[0], self._anode.datum[1], top_separator.datum[2])
        elif self._update_properties:
            bottom_separator.datum = (self._cathode.datum[0], self._bottom_separator.datum[1], bottom_separator.datum[2])
            top_separator.datum = (self._anode.datum[0], self._top_separator.datum[1], top_separator.datum[2])

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
            self._adjust_zfold_overhang_fixed_component('bottom_separator', overhang, 'bottom')
            self._adjust_zfold_overhang_fixed_component('top_separator', overhang, 'bottom')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_zfold_overhang_fixed_overhangs('bottom_separator', overhang, 'bottom')
            self._adjust_zfold_overhang_fixed_overhangs('top_separator', overhang, 'bottom')

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
            self._adjust_zfold_overhang_fixed_component('bottom_separator', overhang, 'top')
            self._adjust_zfold_overhang_fixed_component('top_separator', overhang, 'top')
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            # Extend both separators to achieve the target overhang
            self._adjust_zfold_overhang_fixed_overhangs('bottom_separator', overhang, 'top')
            self._adjust_zfold_overhang_fixed_overhangs('top_separator', overhang, 'top')

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
            'left': 0.0,
            'right': 0.0,
            'bottom': self.separator_overhang_bottom,
            'top': self.separator_overhang_top
        }

    # ============================================================================
    # Range Properties
    # ============================================================================

    @property
    def separator_overhang_bottom_range(self) -> tuple:
        """Get the valid range for bottom separator overhang."""
        return super().bottom_separator_overhang_bottom_range
    
    @property
    def separator_overhang_top_range(self) -> tuple:
        """Get the valid range for top separator overhang."""
        return super().bottom_separator_overhang_top_range

    # ============================================================================
    # Internal/Helper Methods
    # ============================================================================

    def _calculate_bottom_separator_overhangs(self):
        """
        Override: Calculate overhangs for Z-fold separators.
        Left/right overhangs are constrained by Z-fold geometry.
        Top/bottom overhangs are shared between top and bottom separators.
        """
        if hasattr(self, '_cathode') and hasattr(self, '_bottom_separator') and self._cathode is not None and self._bottom_separator is not None:

            # Cathode edges (using internal SI units - meters)
            cathode_bottom = self._cathode._current_collector._datum[1] - self._cathode._current_collector._y_body_length / 2
            cathode_top = self._cathode._current_collector._datum[1] + self._cathode._current_collector._y_body_length / 2

            # Bottom separator edges (using internal SI units - meters)
            separator_bottom = min(self._bottom_separator._coordinates[:,1])
            separator_top = max(self._bottom_separator._coordinates[:,1])

            # Calculate only top/bottom overhangs (left/right are constrained)
            self._bottom_separator_overhang_left = 0.0  # Constrained by Z-fold
            self._bottom_separator_overhang_right = 0.0  # Constrained by Z-fold
            self._bottom_separator_overhang_bottom = cathode_bottom - separator_bottom
            self._bottom_separator_overhang_top = separator_top - cathode_top

            # Ensure top separator has the same overhangs (Z-fold constraint)
            if hasattr(self, '_top_separator') and self._top_separator is not None:
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
        if component == 'bottom_separator':
            current_overhang = getattr(self, f'_bottom_separator_overhang_{direction}') * M_TO_MM
        elif component == 'top_separator':
            current_overhang = getattr(self, f'_top_separator_overhang_{direction}') * M_TO_MM
        else:
            raise ValueError(f"Unknown component: {component}")
            
        overhang_difference = target_overhang - current_overhang
        
        # Get the component object
        component_obj = getattr(self, f'_{component}')
        
        # get component datum
        datum = component_obj.datum

        if direction == 'left':
            datum = (datum[0] - overhang_difference, datum[1], datum[2])
        elif direction == 'right':
            datum = (datum[0] + overhang_difference, datum[1], datum[2])
        elif direction == 'bottom':
            datum = (datum[0], datum[1] - overhang_difference, datum[2])
        elif direction == 'top':
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
        if component == 'bottom_separator':
            current_overhang = getattr(self, f'_bottom_separator_overhang_{direction}')
        elif component == 'top_separator':
            current_overhang = getattr(self, f'_top_separator_overhang_{direction}')
        else:
            raise ValueError(f"Unknown component: {component}")
            
        target_overhang = target_overhang * MM_TO_M
        overhang_difference = target_overhang - current_overhang
        
        # Get the component object
        component_obj = getattr(self, f'_{component}')
        
        # Use the same logic as the parent class for separators
        position_adjustment = (overhang_difference / 2) * M_TO_MM
        
        # Determine which dimension to adjust based on rotation and direction
        is_horizontal = direction in ['left', 'right']
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
        if direction == 'left':
            component_obj.datum_x -= position_adjustment
        elif direction == 'right':
            component_obj.datum_x += position_adjustment
        elif direction == 'bottom':
            component_obj.datum_y -= position_adjustment
        else:  # top
            component_obj.datum_y += position_adjustment

    # ============================================================================
    # String Representation
    # ============================================================================

    def __str__(self):
        """String representation of the Z-Fold MonoLayer object."""
        return f"{self.__class__.__name__}: {self.name} | Anode: {self.anode.name} | Cathode: {self.cathode.name} | Separator: {self.separator.name} | Anode Overhangs (L,R,B,T): ({self.anode_overhang_left} mm, {self.anode_overhang_right} mm, {self.anode_overhang_bottom} mm, {self.anode_overhang_top} mm) | Separator Overhangs (B,T): ({self.separator_overhang_bottom} mm, {self.separator_overhang_top} mm)"

    # ============================================================================
    # Blocked Properties - Individual Separator APIs Disabled  
    # ============================================================================

    @property
    def bottom_separator(self) -> None:
        """Individual separator access disabled. Use 'separator' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator' property. Individual 'bottom_separator' access is not available.")
    
    @property
    def top_separator(self) -> None:
        """Individual separator access disabled. Use 'separator' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator' property. Individual 'top_separator' access is not available.")
    
    @property
    def bottom_separator_overhang_bottom(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_bottom' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_bottom' property. Individual 'bottom_separator_overhang_bottom' access is not available.")
    
    @property
    def bottom_separator_overhang_top(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_top' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_top' property. Individual 'bottom_separator_overhang_top' access is not available.")
    
    @property
    def bottom_separator_overhang_left(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_left' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_left' property. Individual 'bottom_separator_overhang_left' access is not available.")
    
    @property
    def bottom_separator_overhang_right(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_right' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_right' property. Individual 'bottom_separator_overhang_right' access is not available.")

    @property
    def top_separator_overhang_bottom(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_bottom' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_bottom' property. Individual 'top_separator_overhang_bottom' access is not available.")
    
    @property
    def top_separator_overhang_top(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_top' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_top' property. Individual 'top_separator_overhang_top' access is not available.")

    @property
    def top_separator_overhang_left(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_left' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_left' property. Individual 'top_separator_overhang_left' access is not available.")

    @property
    def top_separator_overhang_right(self) -> None:
        """Individual overhang access disabled. Use 'separator_overhang_right' property instead."""
        raise AttributeError("ZFoldMonoLayer uses unified 'separator_overhang_right' property. Individual 'top_separator_overhang_right' access is not available.")



