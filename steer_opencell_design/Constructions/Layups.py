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


class Layup(CoordinateMixin, ValidationMixin, SerializerMixin):
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

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        # self._calculate_overhangs()
        
    def _calculate_bulk_properties(self):
        self._calculate_thickness_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()      

    def _calculate_thickness_properties(self):

        self._thickness = self._cathode._thickness + \
                          self._bottom_separator._thickness + \
                          self._anode._thickness + \
                          self._top_separator._thickness
        
        return self._thickness

    def _calculate_mass_properties(self):

        self._mass = self._cathode._mass + \
                     self._bottom_separator._mass + \
                     self._anode._mass + \
                     self._top_separator._mass
        
        return self._mass

    def _calculate_cost_properties(self):

        self._cost = self._cathode._cost + \
                     self._bottom_separator._cost + \
                     self._anode._cost + \
                     self._top_separator._cost
        
        return self._cost

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

    def _get_full_top_down_view(self, **kwargs) -> go.Figure:

        fig = go.Figure()

        # Get trace groups
        cathode_fig = self._cathode._get_full_top_down_view()
        for i, trace in enumerate(cathode_fig.data):
            trace.name = self._cathode.name
            trace.legendgroup = self._cathode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        bottom_separator_trace = copy(self._bottom_separator.top_down_trace)
        bottom_separator_trace.name = self.bottom_separator.name
        bottom_separator_trace.legendgroup = self.bottom_separator.name
        bottom_separator_trace.xaxis = 'x'
        bottom_separator_trace.yaxis = 'y'
        fig.add_trace(bottom_separator_trace)

        anode_fig = self._anode._get_full_top_down_view()
        for i, trace in enumerate(anode_fig.data):
            trace.name = self._anode.name
            trace.legendgroup = self._anode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        top_separator_trace = copy(self._top_separator.top_down_trace)
        top_separator_trace.name = self.top_separator.name
        top_separator_trace.legendgroup = self.top_separator.name
        top_separator_trace.xaxis = 'x'
        top_separator_trace.yaxis = 'y'
        fig.add_trace(top_separator_trace)

        # Final layout
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            title=kwargs.get('title', f"{self.name} Top-Down View"),
            **kwargs
        )

        return fig

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 1)

    @property
    def anode(self):
        return self._anode
   
    @property
    def cathode(self):
        return self._cathode

    @property
    def top_separator(self):
        return self._top_separator

    @property
    def bottom_separator(self):
        return self._bottom_separator

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def cost(self) -> float:
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
        }

    @cathode.setter
    @calculate_all_properties
    def cathode(self, cathode: Cathode):

        # validate the type
        self.validate_type(cathode, Cathode, "Cathode")
        self.validate_type(cathode.current_collector, _TapeCurrentCollector, "Cathode Current Collector")

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

        # modify name
        bottom_separator.name = f"Bottom {bottom_separator.name}"

        # set to the layup
        self._bottom_separator = deepcopy(bottom_separator)

        # modify the separator datum
        self._bottom_separator.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._bottom_separator.thickness/2
        )

    @anode.setter
    @calculate_all_properties
    def anode(self, anode: Anode):
        
        # validate type
        self.validate_type(anode, Anode, "Anode")
        self.validate_type(anode.current_collector, _TapeCurrentCollector, "Anode Current Collector")

        # flip the anode, so the a side of the anode faces the a side of the cathode
        if not anode._flipped_y:
            anode._flip('y')

        # update the anodes datum position
        anode.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._bottom_separator.thickness + anode.thickness/2
        )

        # set the ranges on the anode current collector based on the cathode current collector
        anode.current_collector.set_ranges_from_reference(self.cathode.current_collector)

        # assign the anode to the layup and update its position based on the cathode
        self._anode = deepcopy(anode)

    @top_separator.setter
    @calculate_all_properties
    def top_separator(self, top_separator: Separator):

        # validate the type
        self.validate_type(top_separator, Separator, "Top Separator")

        # modify name
        top_separator.name = f"Top {top_separator.name}"

        # set to the layup
        self._top_separator = deepcopy(top_separator)

        self._top_separator.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._top_separator.thickness + self._anode.thickness + self._bottom_separator.thickness/2
        )

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


class MonoLayer(CoordinateMixin, ValidationMixin, SerializerMixin):
    """
    Class for a MonoLayer, which is a combination of anode, cathode, and separator. This class represents the 
    item which will be repeated in space to form a z-fold stack.
    """
    def __init__(
            self,
            anode: Anode,
            cathode: Cathode,
            separator: Separator,
            anode_offset: Tuple[float, float] = (0.0, 0.0),
            separator_offset: float = 0,
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
        separator_offset : float
            The (x, y) offset for the separator in mm.
        """
        self._update_properties = False

        self.cathode = cathode
        self.separator = separator
        self.anode = anode
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        
    def _calculate_bulk_properties(self):
        self._calculate_thickness_properties()

    def _calculate_thickness_properties(self):

        self._thickness = self._separator._thickness + \
                          self._cathode._thickness + \
                          self._separator._thickness + \
                          self._anode._thickness
        
        return self._thickness
   
    def _get_full_top_down_view(self, **kwargs) -> go.Figure:

        top_separator = deepcopy(self._separator)
        top_separator.length = self.cathode.current_collector.x_body_length + 2 * (self.separator.thickness * UM_TO_MM)

        bottom_separator = deepcopy(self._separator)
        bottom_separator.length = self.anode.current_collector.x_body_length + 2 * (self.separator.thickness * UM_TO_MM)

        fig = go.Figure()

        # Get trace groups
        cathode_fig = self._cathode._get_full_top_down_view()
        for i, trace in enumerate(cathode_fig.data):
            trace.name = self._cathode.name
            trace.legendgroup = self._cathode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        top_separator_trace = copy(top_separator.top_down_trace)
        top_separator_trace.name = f"{self.separator.name} top layer"
        top_separator_trace.legendgroup = f"{self.separator.name} top layer"
        top_separator_trace.xaxis = 'x'
        top_separator_trace.yaxis = 'y'
        fig.add_trace(top_separator_trace)

        anode_fig = self._anode._get_full_top_down_view()
        for i, trace in enumerate(anode_fig.data):
            trace.name = self._anode.name
            trace.legendgroup = self._anode.name
            trace.showlegend = i == 0
            trace.xaxis = 'x'
            trace.yaxis = 'y'
            fig.add_trace(trace)

        bottom_separator_trace = copy(bottom_separator.top_down_trace)
        bottom_separator_trace.name = f"{self.separator.name} bottom layer"
        bottom_separator_trace.legendgroup = f"{self.separator.name} bottom layer"
        bottom_separator_trace.xaxis = 'x'
        bottom_separator_trace.yaxis = 'y'
        fig.add_trace(bottom_separator_trace)

        # Final layout
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            title=kwargs.get('title', f"{self.name} Top-Down View"),
            **kwargs
        )

        return fig

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 1)

    @property
    def anode(self):
        return self._anode
   
    @property
    def cathode(self):
        return self._cathode

    @property
    def separator(self):
        return self._separator

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
        }

    @cathode.setter
    @calculate_all_properties
    def cathode(self, cathode: Cathode):

        # validate the type
        self.validate_type(cathode, Cathode, "Cathode")
        self.validate_type(cathode.current_collector, PunchedCurrentCollector, "Cathode Current Collector")

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

    @separator.setter
    @calculate_all_properties
    def separator(self, separator: Separator):

        # validate the type
        self.validate_type(separator, Separator, "Separator")

        # set to the layup
        self._separator = deepcopy(separator)

        # modify the separator datum
        self._separator.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._separator.thickness/2
        )

    @anode.setter
    @calculate_all_properties
    def anode(self, anode: Anode):
        
        # validate type
        self.validate_type(anode, Anode, "Anode")
        self.validate_type(anode.current_collector, PunchedCurrentCollector, "Anode Current Collector")

        # update the anodes datum position
        anode.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._separator.thickness + anode.thickness/2
        )

        # set the ranges on the anode current collector based on the cathode current collector
        anode.current_collector.set_ranges_from_reference(self.cathode.current_collector)

        # assign the anode to the layup and update its position based on the cathode
        self._anode = deepcopy(anode)

    def __str__(self):
        """
        String representation of the Layup object.
        
        Returns
        -------
        str
            A string representation of the MonoLayer.
        """
        return f"MonoLayer(anode={self.anode}, cathode={self.cathode}, top_separator={self.top_separator}, bottom_separator={self.bottom_separator})"

    def __repr__(self):
        """
        Official string representation of the MonoLayer object.
        
        Returns
        -------
        str
            An official string representation of the MonoLayer.
        """
        return self.__str__()


