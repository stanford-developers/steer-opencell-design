from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Components.CurrentCollectors import (
    _CurrentCollector,
    TabWeldedCurrentCollector,
    NotchedCurrentCollector,
)
from steer_opencell_design.Constructions.Layups import _Layup
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer

# Mixins from steer_core
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin

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


class _ElectrodeAssembly(
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin
):
    
    def __init__(self):
        pass

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


class _JellyRoll(
    _ElectrodeAssembly
):
    """Jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(self, laminate: Laminate):
        self.laminate = laminate

    @property
    def laminate(self) -> Laminate:
        """Return the underlying `Laminate` instance."""
        return self._laminate

    @laminate.setter
    def laminate(self, value: Laminate):
        self.validate_type(value, Laminate, "laminate")
        self._laminate = value


class _Stack(_ElectrodeAssembly):
    """Stack electrode assembly.

    Accepts a `MonoLayer` or `ZFoldMonoLayer` layup representing stacked sheets.
    """
    def __init__(self, layup: MonoLayer | ZFoldMonoLayer):
        self.validate_type(layup, (MonoLayer, ZFoldMonoLayer), "layup")
        super().__init__(layup)




