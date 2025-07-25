from SteerEnergyStorage.Constructions.Electrodes import Anode, Cathode
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.CurrentCollectors import TabWeldedCurrentCollector, NotchedCurrentCollector

from App.styles import *
from SteerEnergyStorage.Constants import *

from copy import deepcopy
from copy import copy
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Tuple


class Layup:
    """
    Class for a Layup, which is a combination of anode, cathode, and separators. This class represents the 
    item which will be wound into a jelly roll or stacked into a z-stack.
    """
    def __init__(
            self,
            anode: Anode,
            cathode: Cathode,
            top_separator: Separator,
            bottom_separator: Separator,
            anode_offset: Tuple[float, float] = (0.0, 0.0),
            top_separator_offset: Tuple[float, float] = (0.0, 0.0),
            bottom_separator_offset: Tuple[float, float] = (0.0, 0.0),
            name: str = "Layup"
        ):
        """
        Initialize the Layup with the given components and offsets.

        Parameters
        ----------
        anode : Anode
            The anode component of the layup.
        cathode : Cathode
            The cathode component of the layup.
        top_separator : Separator
            The top separator component of the layup.
        bottom_separator : Separator
            The bottom separator component of the layup.
        anode_offset : tuple
            The (x, y) offset for the anode in mm.
        top_separator_offset : tuple
            The (x, y) offset for the top separator in mm.
        bottom_separator_offset : tuple
            The (x, y) offset for the bottom separator in mm.
        """
        self._update_properties = False

        self.cathode = cathode
        self.bottom_separator = bottom_separator
        self.anode = anode
        self.top_separator = top_separator
        self.name = name

        self._set_bottom_separator_datum()
        self._set_anode_datum()
        self._set_top_separator_datum()
        self._calculate_properties()

        self._update_properties = True

    def _calculate_properties(self):

        self._thickness = self._cathode._thickness + \
                          self._bottom_separator._thickness + \
                          self._anode._thickness + \
                          self._top_separator._thickness
        
        self._mass = self._cathode._mass + \
                     self._bottom_separator._mass + \
                     self._anode._mass + \
                     self._top_separator._mass
        
        self._cost = self._cathode._cost + \
                     self._bottom_separator._cost + \
                     self._anode._cost + \
                     self._top_separator._cost
        
        self._calculate_overhangs()
        
    def _calculate_overhangs(self):
        """ 
        Calculate the overhangs of the layup based on the positions of the components.
        This method calculates the positions of the edges of the cathode, anode, and separators,
        and sets the overhangs for the bottom separator. Note - overhangs are left, bottom, right, top.
        All overhangs are relative to the cathode.
        """
        # Positions of cathode edges
        cathode_left = self._cathode._datum[0] - self._cathode._current_collector._x_body_length / 2
        cathode_right = self._cathode._datum[0] + self._cathode._current_collector._x_body_length / 2
        cathode_bottom = self._cathode._datum[1] - self._cathode._current_collector._y_body_length / 2
        cathode_top = self._cathode._datum[1] + self._cathode._current_collector._y_body_length / 2

        # Positions of anode edges
        anode_left = self._anode._datum[0] - self._anode._current_collector._x_body_length / 2
        anode_right = self._anode._datum[0] + self._anode._current_collector._x_body_length / 2
        anode_bottom = self._anode._datum[1] - self._anode._current_collector._y_body_length / 2
        anode_top = self._anode._datum[1] + self._anode._current_collector._y_body_length / 2

        # Positions of top separator edges
        top_separator_left = self._top_separator._datum[0] - self._top_separator._length / 2
        top_separator_right = self._top_separator._datum[0] + self._top_separator._length / 2
        top_separator_bottom = self._top_separator._datum[1] - self._top_separator._width / 2
        top_separator_top = self._top_separator._datum[1] + self._top_separator._width / 2

        # Positions of bottom separator edges
        bottom_separator_left = self._bottom_separator._datum[0] - self._bottom_separator._length / 2
        bottom_separator_right = self._bottom_separator._datum[0] + self._bottom_separator._length / 2
        bottom_separator_bottom = self._bottom_separator._datum[1] - self._bottom_separator._width / 2
        bottom_separator_top = self._bottom_separator._datum[1] + self._bottom_separator._width / 2

        # calculate the overhangs for the bottom separator
        self._bottom_separator_overhang = (
            cathode_left - bottom_separator_left,
            cathode_bottom - bottom_separator_bottom,
            bottom_separator_right - cathode_right,
            bottom_separator_top - cathode_top
        )

        # calculate the overhangs for top separator
        self._top_separator_overhang = (
            cathode_left - top_separator_left,
            cathode_bottom - top_separator_bottom,
            top_separator_right - cathode_right,
            top_separator_top - cathode_top
        )

        # calculate the overhangs for anode
        self._anode_overhang = (
            cathode_left - anode_left,
            cathode_bottom - anode_bottom,
            anode_right - cathode_right,
            anode_top - cathode_top
        )

        for i, (a, b) in enumerate(zip(self._top_separator_overhang, self._anode_overhang)):
            if a < b:
                raise ValueError("The overhang of your top separator is less than that of the anode, meaning there will be bare anode exposed. Please check your layup design.")

    def _get_flat_view(self, side: str, **kwargs) -> go.Figure:

        if side not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'. Currently, only 'a' or 'b' side view is supported.")
        
        fig = go.Figure()

        # Get trace groups
        cathode_traces = []
        cathode_fig = self._cathode.get_a_side_view() if side == 'a' else self._cathode.get_b_side_view()
        for i, trace in enumerate(cathode_fig.data):
            trace.name = self._cathode.name
            trace.legendgroup = self._cathode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            cathode_traces.append(trace)

        bottom_separator_trace = copy(self._bottom_separator._top_down_trace)
        bottom_separator_trace.name = self._bottom_separator.name
        bottom_separator_trace.xaxis = 'x'
        bottom_separator_trace.yaxis = 'y'

        anode_traces = []
        anode_fig = self._anode.get_a_side_view() if side == 'a' else self._anode.get_b_side_view()
        for i, trace in enumerate(anode_fig.data):
            trace.name = self._anode.name
            trace.legendgroup = self._anode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            anode_traces.append(trace)

        top_separator_trace = copy(self._top_separator._top_down_trace)
        top_separator_trace.name = self._top_separator.name
        top_separator_trace.xaxis = 'x'
        top_separator_trace.yaxis = 'y'

        # Order depends on side
        if side == 'a':
            ordered_traces = cathode_traces + [bottom_separator_trace] + anode_traces + [top_separator_trace]
        else:
            ordered_traces = [top_separator_trace] + anode_traces + [bottom_separator_trace] + cathode_traces

        for trace in ordered_traces:
            fig.add_trace(trace)

        # Final layout
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            title=kwargs.get('title', f"{self.name} - {side.upper()} Side View"),
            **kwargs
        )

        return fig

    def _set_cathode_datum(self, x, y):
        """
        Set the datum for the cathode when added to the layup.
        The datum is set to the center of the cathode current collector.
        """
        cathode_datum = (
            x,
            y,
            (self._bottom_separator._datum[2] - self._bottom_separator._thickness/2 - self._cathode._thickness/2) * M_TO_MM
        )
        self._cathode.datum = cathode_datum

    def _set_anode_datum(self):
        """
        Set the datum for the anode when added to the layup based on the cathode and bottom separator positions.
        """
        cathode_a_side_coating_x_min = min(self._cathode._current_collector._b_side_coated_area_trace.x)
        cathode_a_side_coating_x_max = max(self._cathode._current_collector._b_side_coated_area_trace.x)
        cathode_a_side_coating_y_min = min(self._cathode._current_collector._b_side_coated_area_trace.y)
        cathode_a_side_coating_y_max = max(self._cathode._current_collector._b_side_coated_area_trace.y)
        cathode_a_side_x_center = cathode_a_side_coating_x_min + (cathode_a_side_coating_x_max - cathode_a_side_coating_x_min) / 2
        cathode_a_side_y_center = cathode_a_side_coating_y_min + (cathode_a_side_coating_y_max - cathode_a_side_coating_y_min) / 2

        anode_b_side_coating_x_min = min(self._anode._current_collector._b_side_coated_area_trace.x)
        anode_b_side_coating_x_max = max(self._anode._current_collector._b_side_coated_area_trace.x)
        anode_b_side_coating_y_min = min(self._anode._current_collector._b_side_coated_area_trace.y)
        anode_b_side_coating_y_max = max(self._anode._current_collector._b_side_coated_area_trace.y)
        anode_b_side_x_center = anode_b_side_coating_x_min + (anode_b_side_coating_x_max - anode_b_side_coating_x_min) / 2
        anode_b_side_y_center = anode_b_side_coating_y_min + (anode_b_side_coating_y_max - anode_b_side_coating_y_min) / 2

        anode_x_shift = anode_b_side_x_center - cathode_a_side_x_center
        anode_y_shift = anode_b_side_y_center + cathode_a_side_y_center

        anode_datum = (
            (self._anode._datum[0] + anode_x_shift) * M_TO_MM,
            (self._anode._datum[1] + anode_y_shift) * M_TO_MM,
            (self._bottom_separator._datum[2] + self._bottom_separator._thickness/2 + self._anode._thickness/2) * M_TO_MM
        )

        self._anode.datum = anode_datum

    def _set_bottom_separator_datum(self):
        """
        Set the datum for the bottom separator when added to the layup based on the cathode position.
        """
        bottom_separator_datum = (
            self._cathode._datum[0] * M_TO_MM,
            self._cathode._datum[1] * M_TO_MM,
            (self._cathode._datum[2] + self._cathode._thickness / 2 + self._bottom_separator._thickness / 2) * M_TO_MM
        )
        self._bottom_separator.datum = bottom_separator_datum

    def _set_top_separator_datum(self):
        """
        Set the datum for the top separator when added to the layup based on the anode position.
        """
        top_separator_datum = (
            self._anode._datum[0] * M_TO_MM,
            self._anode._datum[1] * M_TO_MM,
            (self._anode._datum[2] + self._anode._thickness / 2 + self._top_separator._thickness / 2) * M_TO_MM
        )
        self._top_separator.datum = top_separator_datum

    def get_a_side_view(self, **kwargs) -> go.Figure:
        """
        Get the A side view of the layup as a Plotly figure.
        
        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments to pass to the Plotly figure layout.

        Returns
        -------
        go.Figure
            A Plotly figure representing the A side view of the layup.
        """
        return self._get_flat_view('a', **kwargs)
    
    def get_b_side_view(self, **kwargs) -> go.Figure:
        """
        Get the B side view of the layup as a Plotly figure.
        
        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments to pass to the Plotly figure layout.
        
        Returns
        -------
        go.Figure
            A Plotly figure representing the B side view of the layup.
        """
        return self._get_flat_view('b', **kwargs)

    def get_end_view(self, **kwargs) -> go.Figure:
        """
        Get the end view of the layup as a Plotly figure.
        
        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments to pass to the Plotly figure layout.
        
        Returns
        -------
        go.Figure
            A Plotly figure representing the end view of the layup.
        """
        fig = go.Figure()

        for i, trace in enumerate(self._cathode.get_end_view().data):
            trace.name = self._cathode.name
            trace.legendgroup = self._cathode.name
            trace.showlegend = True if i == 0 else False
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        bottom_separator_trace = copy(self._bottom_separator._end_view_trace)
        bottom_separator_trace.name = self._bottom_separator.name
        bottom_separator_trace.xaxis = 'x'
        bottom_separator_trace.yaxis = 'y'
        fig.add_trace(bottom_separator_trace)

        for i, trace in enumerate(self._anode.get_end_view().data):
            trace.name = self._anode.name
            trace.legendgroup = self._anode.name
            trace.showlegend = True if i == 0 else False
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        top_separator_trace = copy(self._top_separator._end_view_trace)
        top_separator_trace.name = self._top_separator.name
        top_separator_trace.xaxis = 'x'
        top_separator_trace.yaxis = 'y'
        fig.add_trace(top_separator_trace)

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            title=kwargs.get('title', f"{self.name} - END VIEW"),
            **kwargs
        )

        return fig

    @property
    def thickness(self) -> float:
        """
        Get the total thickness of the layup in mm.
        
        Returns
        -------
        float
            The total thickness of the layup in mm.
        """
        return round(self._thickness * M_TO_UM, 1)

    @property
    def anode(self):
        return self._anode
    
    @anode.setter
    def anode(self, anode: Anode):

        # value checks
        if not isinstance(anode, Anode):
            raise TypeError("Anode must be an instance of the Anode class.")
        
        # check that the anode has a greater coating width than the cathode
        if anode._current_collector._coated_width < self._cathode._current_collector._coated_width:
            raise ValueError("Anode current collector must have a coating width greater or equal to the cathode coating width.")
        
        # check that the anode has a greater coating length than the cathode
        if anode._current_collector._b_side_coated_length < self._cathode._current_collector._a_side_coated_length:
            raise ValueError("Anode b side coating length must be greater or equal to the cathode a side coating length.")
        
        # check that the anode has a greater coating length than the cathode
        if anode._current_collector._a_side_coated_length < self._cathode._current_collector._b_side_coated_length:
            raise ValueError("Anode a side coating length must be greater or equal to the cathode b side coating length.")

        # if the anode current collector is not flipped, flip it so the tabs are pointing on the other side to the cathode
        if not hasattr(anode._current_collector, '_x_flipped') or not anode._current_collector._x_flipped:
            anode._current_collector._flip_on_x()

        # assign the anode to the layup and update its position based on the cathode
        self._anode = anode
        self._set_anode_datum()

        # calculate the top anode overhang based on the coated area traces
        _y_max_anode_coated = max(self._anode._current_collector._b_side_coated_area_trace.y)
        _y_max_cathode_coated = max(self._cathode._current_collector._a_side_coated_area_trace.y)
        _anode_top_overhang = _y_max_anode_coated - _y_max_cathode_coated
        self._anode._top_overhang = _anode_top_overhang

        # calculate the bottom anode overhang based on the coated area traces
        _y_min_anode_coated = min(self._anode._current_collector._b_side_coated_area_trace.y)
        _y_min_cathode_coated = min(self._cathode._current_collector._a_side_coated_area_trace.y)
        _anode_bottom_overhang = _y_min_cathode_coated - _y_min_anode_coated
        self._anode._bottom_overhang = _anode_bottom_overhang

        # update properties if needed
        if self._update_properties:
            self._calculate_properties()

    @property
    def cathode(self):
        return self._cathode
    
    @cathode.setter
    def cathode(self, cathode: Cathode):

        if not isinstance(cathode, Cathode):
            raise TypeError("Cathode must be an instance of the Cathode class.")
        
        old_x = self._cathode.datum[0] if hasattr(self, '_cathode') else 0.0
        old_y = self._cathode.datum[1] if hasattr(self, '_cathode') else 0.0

        self._cathode = cathode

        if self._update_properties:
            self._set_cathode_datum(old_x, old_y)
            self._calculate_properties()

    @property
    def top_separator(self):
        return self._top_separator
    
    @top_separator.setter
    def top_separator(self, top_separator: Separator):

        if not isinstance(top_separator, Separator):
            raise TypeError("Top separator must be an instance of the Separator class.")
        
        if not hasattr(top_separator, '_length') or top_separator._length is None:
            top_separator.length = self._cathode._current_collector._x_body_length * M_TO_MM + 400

        if top_separator._length < self._anode._current_collector._x_body_length:
            raise ValueError("Top separator length must be at least as long as the anode current collector.")
        
        if top_separator._width < self._anode._current_collector._y_body_length:
            raise ValueError("Top separator width must be at least as wide as the anode current collector.")
        
        self._top_separator = top_separator
        self._set_top_separator_datum()

        if self._update_properties:
            self._set_component_z_datums()
            self._calculate_properties()

    @property
    def bottom_separator(self):
        return self._bottom_separator

    @bottom_separator.setter
    def bottom_separator(self, bottom_separator: Separator):

        if not isinstance(bottom_separator, Separator):
            raise TypeError("Bottom separator must be an instance of the Separator class.")

        if not hasattr(bottom_separator, '_length') or bottom_separator._length is None:
            bottom_separator.length = self._cathode._current_collector._x_body_length * M_TO_MM + 400

        self._bottom_separator = bottom_separator
        self._set_bottom_separator_datum()

        if self._update_properties:
            self._set_component_z_datums()
            self._calculate_properties()

    @property
    def mass(self) -> float:
        """
        Get the total mass of the layup in grams.
        
        Returns
        -------
        float
            The total mass of the layup in grams.
        """
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def cost(self) -> float:
        """
        Get the total cost of the layup in currency units.
        
        Returns
        -------
        float
            The total cost of the layup in currency units.
        """
        return round(self._cost, 2)

    @property
    def properties(self):
        """
        Get the properties of the layup as a dictionary.
        
        Returns
        -------
        dict
            A dictionary containing the properties of the layup.
        """
        return {
            'Thickness': f"{self.thickness} um",
            'Mass': f"{self.mass} g",
            'Cost': f"$ {self.cost}",
            'Anode top overhang': f"{self.anode.top_overhang} mm",
            'Anode bottom overhang': f"{self.anode.bottom_overhang} mm",
        }

    def __str__(self):
        """
        String representation of the Layup object.
        
        Returns
        -------
        str
            A string representation of the Layup.
        """
        return f"Layup(anode={self.anode}, cathode={self.cathode}, top_separator={self.top_separator}, bottom_separator={self.bottom_separator})"

    def __repr__(self):
        """
        Official string representation of the Layup object.
        
        Returns
        -------
        str
            An official string representation of the Layup.
        """
        return self.__str__()


