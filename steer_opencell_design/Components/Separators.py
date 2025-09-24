from steer_core.Constants.Units import *
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import (
    calculate_all_properties,
    calculate_bulk_properties,
)

from steer_materials.CellMaterials.Base import SeparatorMaterial

from typing import Tuple
from copy import deepcopy
from App.styles import *

import numpy as np
import pandas as pd


class Separator(CoordinateMixin, ValidationMixin):
    def __init__(
        self,
        material: SeparatorMaterial,
        thickness: float,
        width: float,
        length: float = None,
        name: str = "Separator",
        datum: Tuple[float, float, float] = (0, 0, 0),
    ):
        """
        Initialize an object that represents a separator

        Parameters
        ----------
        material : SeparatorMaterial
            Material of the separator.
        thickness : float
            Thickness of the separator in um.
        width : float, optional
            Width of the separator in mm. Does not need to be provided as it can be calculated from the layup and stack.
        length : float, optional
            Length of the separator in mm. If None, bulk properties won't be calculated until set.
        name : str, optional
            Name of the separator. Defaults to 'Separator'.
        datum : Tuple[float, float, float], optional
            Datum point for the separator, used for positioning in 3D space. Defaults to (0, 0, 0).
        """
        self._folded = False
        self._rotated_xy = False
        self._update_properties = False

        self.datum = datum
        self.width = width
        self.thickness = thickness
        self.material = material
        self.name = name

        # Set length after other properties
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
        self._calculate_coordinates()

    def _calculate_areal_properties(self):
        self._areal_cost = self._material._specific_cost * self._material._density * self._thickness

    def _calculate_bulk_properties(self):
        """
        Calculate bulk properties of the separator.
        Only calculates if length is available.
        """
        if self._length is None:
            self._area = None
            self._mass = None
            self._cost = None
            self._pore_volume = None
            return

        self._area = self._length * self._width
        self._mass = self._area * self._material._density * self._thickness
        self._cost = self._area * self._areal_cost
        self._pore_volume = self._area * self._thickness * self._material._porosity

    def _calculate_coordinates(self):
        """
        Calculate coordinates only if length is available.
        """
        if self._length is None:
            self._coordinates = None
            return

        x, y = self.build_square_array(
            self._datum[0] - self._length / 2,
            self._datum[1] - self._width / 2,
            self._length,
            self._width,
        )

        x, y, z, _ = self.extrude_footprint(x, y, self._datum, self._thickness)

        self._coordinates = np.column_stack((x, y, z))

        if self._rotated_xy:
            self._rotate_90_xy(update_bool=False)

    def _rotate_90_xy(self, update_bool: bool = True) -> "Separator":
        if self._coordinates is None:
            raise ValueError("Cannot rotate: length not set")

        self._coordinates = self.rotate_coordinates(self._coordinates, axis="z", angle=90, center=self._datum)

        if update_bool:
            self._rotated_xy = not self._rotated_xy

        return self

    def get_top_down_view(self, **kwargs) -> go.Figure:
        if self._coordinates is None:
            raise ValueError("Cannot generate top-down view: length not set")

        fig = go.Figure()
        fig.add_trace(self.top_down_trace)

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X (mm)"),
            yaxis=dict(showgrid=False, zeroline=False, title="Y (mm)"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    @property
    def coordinates(self) -> pd.DataFrame:
        if self._coordinates is None:
            return None

        return pd.DataFrame(self._coordinates, columns=["x", "y", "z"]).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
        )

    @property
    def top_down_trace(self) -> go.Scatter:
        if self._coordinates is None:
            return None

        # get the side with the maximum z value
        coordinates = self.coordinates.query("z == z.max()")

        # make the body trace
        body_trace = go.Scatter(
            x=coordinates["x"],
            y=coordinates["y"],
            mode="lines",
            name="Tab",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Separator",
            showlegend=True,
        )

        return body_trace

    @property
    def right_left_trace(self) -> go.Scatter:
        if self._coordinates is None:
            return None

        # get the coordinates
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="yz")

        # make the trace
        a_side_insulation_trace = go.Scatter(
            x=coordinates["y"],
            y=coordinates["z"],
            mode="lines",
            name=self.name,
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self._insulation_material._color,
            legendgroup=self.name,
            showlegend=True,
        )

        return a_side_insulation_trace

    @property
    def cost(self) -> float:
        if self._cost is None:
            return None
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        if self._mass is None:
            return None
        return round(self._mass * KG_TO_G, 2)

    @property
    def area(self) -> float:
        if self._area is None:
            return None
        return round(self._area * M_TO_CM**2, 2)

    @property
    def areal_cost(self) -> float:
        return round(self._areal_cost, 2)

    @property
    def pore_volume(self) -> float:
        if self._pore_volume is None:
            return None
        return round(self._pore_volume * M_TO_MM**3, 2)

    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            self._datum[0] * M_TO_MM,
            self._datum[1] * M_TO_MM,
            self._datum[2] * M_TO_MM,
        )

    @property
    def datum_x(self) -> float:
        return round(self._datum[0] * M_TO_MM, 2)

    @property
    def datum_y(self) -> float:
        return round(self._datum[1] * M_TO_MM, 2)

    @property
    def datum_z(self) -> float:
        return round(self._datum[2] * M_TO_MM, 2)

    @property
    def name(self) -> str:
        return self._name

    @property
    def length(self) -> float:
        if self._length is None:
            return None
        return round(self._length * M_TO_MM, 2)

    @property
    def width(self) -> float:
        return round(self._width * M_TO_MM, 2)

    @property
    def material(self) -> SeparatorMaterial:
        return self._material

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)

    @areal_cost.setter
    @calculate_all_properties
    def areal_cost(self, areal_cost: float) -> None:
        self.validate_positive_float(areal_cost, "Areal Cost")
        new_material_specific_cost = areal_cost / (self.material._density * self._thickness)  # $/kg
        self._material.specific_cost = new_material_specific_cost

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
    @calculate_bulk_properties
    def material(self, material: SeparatorMaterial) -> None:
        self.validate_type(material, SeparatorMaterial, "Material")
        self._material = deepcopy(material)

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        # Validate datum
        self.validate_datum(datum)

        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )

    @datum_x.setter
    def datum_x(self, x: float) -> None:
        self.datum = (float(x), self.datum[1], self.datum[2])

    @datum_y.setter
    def datum_y(self, y: float) -> None:
        self.datum = (self.datum[0], float(y), self.datum[2])

    @datum_z.setter
    def datum_z(self, z: float) -> None:
        self.datum = (self.datum[0], self.datum[1], float(z))

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * UM_TO_M

    def __str__(self):
        if self._name is not None:
            return f"{self._name}"
        else:
            return f"Separator"

    def __repr__(self):
        return self.__str__()
