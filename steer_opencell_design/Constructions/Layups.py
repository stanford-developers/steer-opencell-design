from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Validators import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_core.Decorators.General import calculate_all_properties

from App.styles import *
from steer_core.Constants.Units import *

from copy import copy
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

    def _get_full_top_down_view(self, side: str, **kwargs) -> go.Figure:

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

        bottom_separator_trace = copy(self._bottom_separator.top_down_trace)
        bottom_separator_trace.name = 'Bottom Separator'
        bottom_separator_trace.legendgroup = 'Bottom Separator'
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

        top_separator_trace = copy(self._top_separator.top_down_trace)
        top_separator_trace.name = 'Top Separator'
        top_separator_trace.legendgroup = 'Top Separator'
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
        self.validate_type(cathode, Cathode, "Cathode")
        self._cathode = cathode

    @bottom_separator.setter
    @calculate_all_properties
    def bottom_separator(self, bottom_separator: Separator):

        # validate the type
        self.validate_type(bottom_separator, Separator, "Bottom Separator")

        # set to the layup
        self._bottom_separator = bottom_separator

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

        # flip the anode, so the a side of the anode faces the a side of the cathode
        anode._flip('y')

        # update the anodes datum position
        anode.datum = (
            self._cathode.datum[0],
            self._cathode.datum[1],
            self._cathode.datum[2] + self._cathode.thickness/2 + self._bottom_separator.thickness + anode.thickness/2
        )

        # assign the anode to the layup and update its position based on the cathode
        self._anode = anode

    @top_separator.setter
    @calculate_all_properties
    def top_separator(self, top_separator: Separator):

        # validate the type
        self.validate_type(top_separator, Separator, "Top Separator")

        # set to the layup
        self._top_separator = top_separator

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


