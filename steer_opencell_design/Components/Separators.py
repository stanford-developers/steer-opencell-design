"""Separator component for battery cells."""

from steer_core.Constants.Units import *

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Datum import DatumMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Propagation import PropagationMixin, propagating_setter

from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import (
    calculate_all_properties,
    calculate_bulk_properties,
)

from steer_opencell_design.Materials.Other import SeparatorMaterial

from steer_opencell_design.Components.Electrodes import _Electrode

from typing import Tuple
from copy import deepcopy

import numpy as np
import pandas as pd
import plotly.graph_objects as go


class Separator(
    CoordinateMixin,
    DatumMixin,
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    PropagationMixin,
    SerializerMixin,
    ):
    """Porous separator membrane that electrically isolates the anode from the cathode while allowing ion transport. Manages separator geometry (length, width, thickness), coordinates, and Plotly visualization traces."""

    def __init__(
        self,
        material: SeparatorMaterial,
        thickness: float,
        width: float = None,
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
            Width of the separator in mm. If None, bulk properties won't be calculated until set.
        length : float, optional
            Length of the separator in mm. If None, bulk properties won't be calculated until set.
        name : str, optional
            Name of the separator. Defaults to 'Separator'.
        datum : Tuple[float, float, float], optional
            Datum point for the separator, used for positioning in 3D space. Defaults to (0, 0, 0).
        """
        self._folded = False
        self._rotated_xy = False
        self._flipped_x = False
        self._flipped_y = False
        self._flipped_z = False
        self._update_properties = False

        # Initialize _datum early so mixin properties work during component setup
        self._datum = tuple(float(d) * MM_TO_M for d in datum)

        self.datum = datum
        self.thickness = thickness
        self.material = material
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
        self._calculate_coordinates()

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
        self._pore_volume = self._material._volume * self._material._porosity

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

    def _set_width_range(self, electrode: _Electrode, extended_range: float):

        if not self._rotated_xy:
            self._width_range = (electrode._current_collector._y_foil_length, electrode._current_collector._y_foil_length + extended_range)
            
        elif self._rotated_xy:
            self._width_range = (electrode._current_collector._x_foil_length, electrode._current_collector._x_foil_length + extended_range)

    def _set_length_range(self, electrode: _Electrode, extended_range: float):

        if not self._rotated_xy:
            self._length_range = (electrode._current_collector._x_foil_length, electrode._current_collector._x_foil_length + extended_range)
        elif self._rotated_xy:
            self._length_range = (electrode._current_collector._y_foil_length, electrode._current_collector._y_foil_length + extended_range)

    def _flip(self, axis: str, bool_update: bool = True) -> None:
        """
        Function to rotate the current collector around a specified axis by 180 degrees
        around the current datum position.

        Parameters
        ----------
        axis : str
            The axis to rotate around. Must be 'x', 'y', or 'z'.
        """
        if axis not in ["x", "y", "z"]:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")

        axis_map = {"x": "y", "y": "x", "z": "z"}

        rotation_axis = axis_map[axis]

        # Keep datum as the center of rotation - don't move it to origin
        # Rotate coordinates around the current datum position
        self._coordinates = self.rotate_coordinates(self._coordinates, rotation_axis, 180, center=self._datum)

        if bool_update:
            # update action booleans
            if axis == "x":
                self._flipped_x = not self._flipped_x
            if axis == "y":
                self._flipped_y = not self._flipped_y
            if axis == "z":
                self._flipped_z = not self._flipped_z

        return self

    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Generate a top-down Plotly figure of the separator."""
        if self._coordinates is None:
            raise ValueError("Cannot generate top-down view: length not set")

        fig = go.Figure()
        fig.add_trace(self.top_down_trace)

        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig
    
    def get_right_left_view(self, **kwargs):
        """Generate a right-left (side) Plotly figure of the separator."""
        if self._coordinates is None:
            raise ValueError("Cannot generate right-left view: length not set")

        fig = go.Figure()

        fig.add_trace(self.right_left_trace)

        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    def get_bottom_up_view(self, **kwargs):
        """Generate a bottom-up Plotly figure of the separator."""
        if self._coordinates is None:
            raise ValueError("Cannot generate bottom-up view: length not set")

        fig = go.Figure()

        fig.add_trace(self.bottom_up_trace)

        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    def get_center_line(self) -> np.ndarray:
        """Get the center line coordinates of the separator."""
        return self.get_xz_center_line(self._coordinates)

    @property
    def coordinates(self) -> pd.DataFrame:
        """Get the separator boundary coordinates as a DataFrame in mm."""
        if self._coordinates is None:
            return None

        return pd.DataFrame(self._coordinates, columns=["x", "y", "z"]).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
        )

    @property
    def top_down_trace(self) -> go.Scatter:
        """Get the Plotly trace for the top-down separator view."""
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
        """Get the Plotly trace for the right-left separator view."""
        if self._coordinates is None:
            return None

        # get the coordinates
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="yz")

        # make the trace
        trace = go.Scatter(
            x=coordinates["y"],
            y=coordinates["z"],
            mode="lines",
            name=self.name,
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self.material._color,
            legendgroup=self.name,
            showlegend=True,
        )

        return trace

    @property
    def bottom_up_trace(self) -> go.Scatter:
        """Get the Plotly trace for the bottom-up separator view."""
        if self._coordinates is None:
            return None

        # get the coordinates
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="xz")

        # add first row to end to close the shape
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        # make the trace
        trace = go.Scatter(
            x=coordinates["x"],
            y=coordinates["z"],
            mode="lines",
            name=self.name,
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self.material._color,
            legendgroup=self.name,
            showlegend=True,
        )

        return trace

    @property
    def cost(self) -> float:
        """Get the total separator cost in $."""
        if self._cost is None:
            return None
        return np.round(self._cost, 2)

    @property
    def mass(self) -> float:
        """Get the total separator mass in g."""
        if self._mass is None:
            return None
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def area(self) -> float:
        """Get the separator area in cm²."""
        if self._area is None:
            return None
        return np.round(self._area * M_TO_CM**2, 2)

    @property
    def areal_cost(self) -> float:
        """Get the separator areal cost in $/m²."""
        return np.round(self._areal_cost, 2)
    
    @property
    def areal_cost_range(self) -> Tuple[float, float]:
        """Get the allowable areal cost range in $/cm²."""
        _specific_cost_minimum = self.material._specific_cost_range[0]
        _specific_cost_maximum = self.material._specific_cost_range[1]
        _areal_cost_minimum = _specific_cost_minimum * self.material._density * self._thickness
        _areal_cost_maximum = _specific_cost_maximum * self.material._density * self._thickness
        return (
            np.round(_areal_cost_minimum, 2),
            np.round(_areal_cost_maximum, 2),
        )

    @property
    def pore_volume(self) -> float:
        """Get the separator pore volume in mm³."""
        if self._pore_volume is None:
            return None
        return np.round(self._pore_volume * M_TO_MM**3, 2)

    @property
    def name(self) -> str:
        """Get the separator name."""
        return self._name

    @property
    def length(self) -> float:
        """Get the separator length in mm."""
        if self._length is None:
            return None
        return np.round(self._length * M_TO_MM, 2)

    @property
    def length_range(self):
        """Get the allowable separator length range in mm."""
        if hasattr(self, "_length_range") and hasattr(self, "_length"):
            return (
                np.round(self._length_range[0] * M_TO_MM, 2),
                np.round(self._length_range[1] * M_TO_MM, 2),
            )
        else:
            return (0, 500)

    @property
    def width(self) -> float:
        """Get the separator width in mm."""
        if self._width is None:
            return None
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self):
        """Get the allowable separator width range in mm."""
        if hasattr(self, "_width_range"):
            return (
                np.round(self._width_range[0] * M_TO_MM, 2),
                np.round(self._width_range[1] * M_TO_MM, 2),
            )
        else:
            return (0, 300)

    @property
    def material(self) -> SeparatorMaterial:
        """Get the separator material."""
        return self._material

    @property
    def thickness(self):
        """Get the separator thickness in um."""
        return np.round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        """Get the allowable separator thickness range in um."""
        return (0, 100)

    @areal_cost.setter
    @calculate_all_properties
    def areal_cost(self, areal_cost: float) -> None:
        self.validate_positive_float(areal_cost, "Areal Cost")
        new_material_specific_cost = areal_cost / (self.material._density * self._thickness)  # $/kg
        self._material.specific_cost = new_material_specific_cost
        self.material = self._material 

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
    @propagating_setter(deepcopy=True)
    def material(self, material: SeparatorMaterial) -> None:
        self.validate_type(material, SeparatorMaterial, "Material")
        self._material = material  # Already a copy due to decorator

    # Override datum setter to use @calculate_coordinates decorator
    @DatumMixin.datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        self.validate_datum(datum)
        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * UM_TO_M

