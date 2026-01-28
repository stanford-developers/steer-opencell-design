from time import time
from steer_core.Constants.Units import *

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_core.Decorators.General import calculate_all_properties

from steer_opencell_design.Materials.Other import TapeMaterial

from typing import Tuple
from copy import deepcopy
import numpy as np

class Tape(
    CoordinateMixin, 
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    SerializerMixin,
    ):
    def __init__(
        self,
        material: TapeMaterial,
        thickness: float,
        width: float = None,
        length: float = None,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Tape"
    ):
        """
        Initialize an object that represents insulating tape

        Parameters
        ----------
        material : TapeMaterial
            Material of the tape.
        thickness : float
            Thickness of the tape in um.
        width : float, optional
            Width of the tape in mm. If None, bulk properties won't be calculated until set.
        length : float, optional
            Length of the tape in mm. If None, bulk properties won't be calculated until set.
        datum : Tuple[float, float, float], optional
            Reference point (x, y, z) in mm. Defaults to (0.0, 0.0, 0.0).
        name : str, optional
            Name of the tape. Defaults to 'Tape'.
        """
        self._update_properties = False

        self.thickness = thickness
        self.material = material
        self.datum = datum
        self.name = name

        # Set width and length after other properties
        if width is not None:
            self.width = width
        else:
            self._width = None

        if length is not None:
            self.length = length
        else:
            self._length = None

        self._calculate_all_properties()

        self._update_properties = True

    def _calculate_all_properties(self):
        """
        Calculate all properties of the separator.
        This method is called when length or width is set.
        """
        self._calculate_areal_properties()
        self._calculate_bulk_properties()

    def _calculate_areal_properties(self):
        self._areal_cost = self._material._specific_cost * self._material._density * self._thickness

    def _calculate_bulk_properties(self):
        """
        Calculate bulk properties of the separator.
        Only calculates if both length and width are available.
        """
        if self._length is None or self._width is None:
            self._area = None
            self._mass = None
            self._cost = None
            self._pore_volume = None
            return

        self._area = self._length * self._width
        _mass = self._area * self._material._density * self._thickness
        mass = _mass * KG_TO_G
        self._material.mass = mass

        self._mass = self._material._mass
        self._cost = self._material._cost

    def _set_width_range(self, jellyroll, length_multiplier: float = 1.1):

        self._width_range = (
            jellyroll._layup._anode._current_collector._y_foil_length, 
            jellyroll._layup._anode._current_collector._y_foil_length * length_multiplier
        )

    @property
    def areal_cost_range(self) -> Tuple[float, float]:
        min = self._material._specific_cost_range[0] * self._material._density * self._thickness
        max = self._material._specific_cost_range[1] * self._material._density * self._thickness
        return (
            np.round(min, 2), 
            np.round(max, 2)
        )
            
    @property
    def cost(self) -> float:
        if self._cost is None:
            return None
        return np.round(self._cost, 2)

    @property
    def mass(self) -> float:
        if self._mass is None:
            return None
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def area(self) -> float:
        if self._area is None:
            return None
        return np.round(self._area * M_TO_CM**2, 2)

    @property
    def areal_cost(self) -> float:
        return np.round(self._areal_cost, 2)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Get the datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        return self._name

    @property
    def length(self) -> float:
        if self._length is None:
            return None
        return np.round(self._length * M_TO_MM, 2)
    
    @property
    def length_range(self):
        return (0, 1000)

    @property
    def width(self) -> float:
        if self._width is None:
            return None
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self):

        if hasattr(self, "_width_range"):
            return (
                np.round(self._width_range[0] * M_TO_MM, 2),
                np.round(self._width_range[1] * M_TO_MM, 2),
            )
        else:
            return (0, 500)

    @property
    def material(self) -> TapeMaterial:
        return self._material

    @property
    def thickness(self):
        return np.round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        return (0, 100)

    @areal_cost.setter
    @calculate_all_properties
    def areal_cost(self, areal_cost: float) -> None:
        self.validate_positive_float(areal_cost, "Areal Cost")
        new_material_specific_cost = areal_cost / (self.material._density * self._thickness)  # $/kg
        self._material.specific_cost = new_material_specific_cost

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """Set the datum position in mm."""
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @name.setter
    def name(self, name: str) -> None:
        self.validate_string(name, "Name")
        self._name = name

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        self.validate_positive_float(length, "Length")
        self._length = float(length) * MM_TO_M

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @material.setter
    @calculate_all_properties
    def material(self, material: TapeMaterial) -> None:
        self.validate_type(material, TapeMaterial, "Material")
        self._material = deepcopy(material)

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * UM_TO_M
