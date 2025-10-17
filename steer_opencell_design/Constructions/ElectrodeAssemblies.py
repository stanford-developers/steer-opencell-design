from steer_opencell_design.Constructions.Layups import _Layup
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer

# Mixins from steer_core
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin

# Decorators from steer_core
from steer_core.Decorators.General import calculate_all_properties

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from copy import deepcopy
from copy import copy
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from shapely import minimum_bounding_circle
import warnings
import plotly.graph_objects as go
from typing import Dict


class _ElectrodeAssembly(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin
):
    
    def __init__(
            self,
            layup: _Layup
        ):

        self._update_properties = False

        self.layup = layup

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_interfacial_area()
        self._calcualate_full_cell_curve()

    def _calculate_bulk_properties(self):
        """Calculate bulk properties of the electrode assembly."""
        pass

    def _calculate_interfacial_area(self):
        """Calculate interfacial area of the electrode assembly."""
        pass

    def _calcualate_full_cell_curve(self):
        """Calculate full cell voltage curve of the electrode assembly."""
        pass


class _JellyRoll(_ElectrodeAssembly):
    """Jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate
        ):

        super().__init__(laminate)

    @property
    def layup(self) -> Laminate:
        """Return the underlying `Laminate` instance."""
        return self._layup

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
            laminate: Laminate
        ):

        super().__init__(laminate)

        self._calculate_all_properties()
        self._update_properties = True


class FlatWoundJellyRoll(_JellyRoll):
    """Flat wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate
        ):

        super().__init__(laminate)

        self._calculate_all_properties()
        self._update_properties = True


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
        pass

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
            n_layers: int
        ):

        super().__init__(
            layup,
            n_layers
        )

        self._calculate_all_properties()
        self._update_properties = True

    @property
    def layup(self) -> ZFoldMonoLayer:
        """Return the underlying `ZFoldMonoLayer` instance."""
        return self._layup

    @layup.setter
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

    def _calculate_stack(self):
        
        def add_layer(stack: Dict, component, z_datum):
            new_component = deepcopy(component)
            new_component.datum = (new_component.datum_x, new_component.datum_y, z_datum)
            new_z_datum = z_datum + new_component._thickness * M_TO_MM
            return new_component, new_z_datum

        # Initialize dictionaries for components
        stack = {}

        # set the starting z datum
        z_datum = 0

        # get bottom separator for initial half-layer
        bottom_separator = deepcopy(self.layup._canonical_separator)
        
        # set its datum
        bottom_separator.datum = (
            bottom_separator.datum_x, 
            bottom_separator.datum_y,
            bottom_separator.thickness * UM_TO_MM, 
        )

        # add it to separators dict
        stack[0] = bottom_separator

        # get the anode for the initial half-layer
        anode = deepcopy(self.layup.anode)

        # set the anodes datum
        anode.datum = (
            anode.datum_x, 
            anode.datum_y,
            bottom_separator.datum[2] + (anode.thickness * UM_TO_MM) / 2, 
        )

        # add it to anodes dict
        stack[1] = anode

        # Create deep copies of components for each layer
        for n in range(1, self.n_layers + 1):

            # Create a deep copy of the monolayer
            monolayer = deepcopy(self.layup)

            # Set the monolayer's datum
            monolayer.datum = (
                monolayer.datum_x, 
                monolayer.datum_y,
                (bottom_separator.thickness + anode.thickness + monolayer.cathode.thickness + (n-1) * monolayer.thickness) * UM_TO_MM
            )

            # Add components to their respective dictionaries
            stack[4*n - 2] = monolayer.top_separator
            stack[4*n - 1] = monolayer.cathode
            stack[4*n + 0] = monolayer.bottom_separator
            stack[4*n + 1] = monolayer.anode

        self._stack = stack

        return self._stack
    
    def get_side_view(self, **kwargs):

        figure = go.Figure()

        for _, component in self.stack.items():
            layer_figure = component.get_right_left_view()
            for trace in layer_figure.data:
                figure.add_trace(trace)

        figure.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, title="X (mm)", scaleanchor="y"),
            yaxis=dict(showgrid=False, zeroline=False, title="Y (mm)"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def layup(self) -> MonoLayer:
        """Return the underlying `MonoLayer` instance."""
        return self._layup

    @layup.setter
    def layup(self, value: MonoLayer):
        self.validate_type(value, MonoLayer, "layup")
        self._layup = value



