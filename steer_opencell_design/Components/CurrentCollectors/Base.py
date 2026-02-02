# Standard library imports
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Tuple, Optional, Iterable, Union

# Third-party imports
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Core STEER imports
from steer_core.Constants.Units import *
from steer_core.Decorators.General import (
    calculate_all_properties,
    calculate_bulk_properties,
)
from steer_core.Decorators.Coordinates import calculate_areas
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_opencell_design.Materials.Other import CurrentCollectorMaterial


class _CurrentCollector(
    ABC, 
    CoordinateMixin, 
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    SerializerMixin
    ):
    """
    Abstract base class for all current collector implementations.

    This class provides the foundational functionality for battery current collectors,
    including geometric calculations, material properties, and coordinate management.
    Current collectors are critical components that facilitate electron flow in
    lithium-ion batteries and similar electrochemical cells.

    The class handles:

    - Geometric coordinate calculations for 3D visualization
    - Area calculations for coated and uncoated regions
    - Material property management and validation
    - Integration with battery cell structures

    All concrete current collector implementations should inherit from this class
    and implement the required abstract methods for specific geometries.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        The material composition of the current collector, defining properties
        like conductivity, density, and cost
    x_foil_length : float
        Length of the current collector foil in the x-direction (mm)
        Typical range: 50-300 mm depending on cell format
    y_foil_length : float
        Width of the current collector foil in the y-direction (mm)
        Typical range: 50-500 mm depending on cell format
    thickness : float
        Material thickness in micrometers (μm)
        Typical range: 6-25 μm for aluminum, 8-35 μm for copper
    insulation_width : float, optional
        Width of insulation strip around the edges in mm (default: 0)
        Used to prevent short circuits and improve safety
    datum : tuple of float, optional
        Reference point (x, y, z) for coordinate system in mm (default: (0, 0, 0))
        Defines the origin for all geometric calculations
    name : str, optional
        Descriptive name for the current collector (default: 'Current Collector')

    Attributes
    ----------
    foil_area : float
        Total surface area of the current collector foil (mm²)
    coated_area : float
        Area available for active material coating (mm²)
    mass : float
        Total mass of the current collector (g)
    volume : float
        Total volume of the current collector (mm³)
    properties : dict
        Dictionary containing all calculated geometric and material properties

    Notes
    -----
    The coordinate system assumes the current collector lies flat in the xy-plane
    with the 'a-side' (typically cathode-facing) pointing upward (+z direction).
    All geometric calculations are performed in metric units but may be converted
    for display purposes.

    Examples
    --------
    This is an abstract base class and cannot be instantiated directly.
    Use concrete implementations like PunchedCurrentCollector:

    >>> from steer_materials import aluminum_foil
    >>> collector = PunchedCurrentCollector(
    ...     material=aluminum_foil,
    ...     x_foil_length=150.0,  # mm
    ...     y_foil_length=200.0,  # mm
    ...     thickness=12.0,       # μm
    ...     tab_width=25.0,       # mm
    ...     tab_height=10.0       # mm
    ... )

    See Also
    --------
    PunchedCurrentCollector : Simple rectangular collector with single tab
    NotchedCurrentCollector : Collector with multiple rectangular cutouts
    TablessCurrentCollector : Collector without protruding tabs
    TabWeldedCurrentCollector : Collector with separate welded tabs
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        x_foil_length: float,
        y_foil_length: float,
        thickness: float,
        insulation_width: Optional[float] = 0,
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
        name: Optional[str] = "Current Collector",
        **kwargs,
    ):
        """
        Initialize an object that represents a current collector.

        Parameters
        ----------
        material : CurrentCollectorMaterial
            Material of the current collector.
        x_foil_length : float
            Length of the current collector in mm.
        y_foil_length : float
            Width of the current collector in mm.
        thickness : float
            Thickness of the current collector in µm.
        insulation_width : Optional[float], default=0
            Width of the insulation in mm.
        datum : Optional[Tuple[float, float, float]], default=(0,0,0)
            Datum of the current collector in mm.
        name : Optional[str], default='Current Collector'
            Name for the current collector.
        **kwargs : dict
            Additional keyword args.
        """
        self._update_properties = False

        # properties
        self.datum = datum
        self.material = material
        self.x_foil_length = x_foil_length
        self.y_foil_length = y_foil_length
        self.thickness = thickness
        self.insulation_width = insulation_width
        self.name = name

        # action booleans
        self._flipped_x = False
        self._flipped_y = False
        self._flipped_z = False

    def _calculate_all_properties(self) -> None:
        self._calculate_coordinates()
        self._calculate_areas()
        self._calculate_bulk_properties()

    def _calculate_coordinates(self) -> None:
        """
        When calculating the coordinates, we assume the cc is lying flat in the xy-plane with the a side pointing upwards.
        """
        self._get_foil_coordinates()
        self._get_a_side_coated_coordinates()
        self._get_b_side_coated_coordinates()

        if hasattr(self, "_insulation_width"):
            self._get_a_side_insulation_coordinates()
            self._get_b_side_insulation_coordinates()

        # perform flipping if needed
        if self._flipped_x:
            self._flip("x", bool_update=False)
        if self._flipped_y:
            self._flip("y", bool_update=False)
        if self._flipped_z:
            self._flip("z", bool_update=False)

    def _calculate_areas(self) -> None:
        # calculate the area of the a side
        mask = self._foil_coordinates_side == "a"
        foil_a_side_area = self.get_area_from_points(self._foil_coordinates[mask][:, 0], self._foil_coordinates[mask][:, 1])

        # calculate the total upper and lower area of the foil
        self._foil_area = foil_a_side_area * 2

        # calculate the area of the a side coated area
        self._a_side_coated_area = self.get_area_from_points(self._a_side_coated_coordinates[:, 0], self._a_side_coated_coordinates[:, 1])

        # calculate the area of the b side coated area
        self._b_side_coated_area = self.get_area_from_points(self._b_side_coated_coordinates[:, 0], self._b_side_coated_coordinates[:, 1])

        self._coated_area = self._a_side_coated_area + self._b_side_coated_area

        if hasattr(self, "_a_side_insulation_coordinates") and hasattr(self, "_b_side_insulation_coordinates"):
            # calculate the area of the a side insulation area
            if len(self._a_side_insulation_coordinates) >= 3:
                self._a_side_insulation_area = self.get_area_from_points(
                    self._a_side_insulation_coordinates[:, 0],
                    self._a_side_insulation_coordinates[:, 1],
                )
            else:
                self._a_side_insulation_area = 0

            # calculate the area of the b side insulation area
            if len(self._b_side_insulation_coordinates) >= 3:
                self._b_side_insulation_area = self.get_area_from_points(
                    self._b_side_insulation_coordinates[:, 0],
                    self._b_side_insulation_coordinates[:, 1],
                )
            else:
                self._b_side_insulation_area = 0

            self._insulation_area = self._a_side_insulation_area + self._b_side_insulation_area

        else:
            self._a_side_insulation_area = 0
            self._b_side_insulation_area = 0
            self._insulation_area = 0

    def _calculate_bulk_properties(self) -> None:
        self._volume = self._foil_area / 2 * self._thickness
        volume = self._volume * M_TO_CM**3
        self._material.volume = volume

        self._mass = self._material._mass
        self._cost = self._material._cost

        # trigger material setter

    def _calculate_fill_patterns(self) -> None:
        # Shading patterns
        self._a_am_fill_pattern = dict(shape="/", size=20, solidity=0.6, fgcolor=self._material._color)
        self._b_am_fill_pattern = dict(shape="\\", size=20, solidity=0.6, fgcolor=self._material._color)
        self._a_in_fill_pattern = dict(shape="\\", size=10, solidity=0.6, fgcolor=self._material._color)
        self._b_in_fill_pattern = dict(shape="/", size=10, solidity=0.6, fgcolor=self._material._color)

    def get_top_down_view(self, **kwargs) -> go.Figure:
        
        fig = go.Figure()

        z_coords = self._foil_coordinates[:, 2]
        z_a = z_coords[self._foil_coordinates_side == "a"].mean()
        z_b = z_coords[self._foil_coordinates_side == "b"].mean()
        top_side = "a" if z_a > z_b else "b"

        # check if weld tabs are present
        if hasattr(self, "_tab_weld_side") and self._tab_weld_side != top_side:
            for i, tab in enumerate(self._weld_tabs):
                trace = tab.top_down_foil_trace
                trace.showlegend = i == 0
                fig.add_trace(trace)

        # add traces to the figure
        fig.add_trace(self.top_down_foil_trace)
        fig.add_trace(self.top_down_coated_area_trace)

        if hasattr(self, "top_down_insulation_area_trace"):
            fig.add_trace(self.top_down_insulation_area_trace)

        # check if weld tabs are present
        if hasattr(self, "_tab_weld_side") and self._tab_weld_side == top_side:
            for i, tab in enumerate(self._weld_tabs):
                trace = tab.top_down_foil_trace
                trace.showlegend = i == 0
                fig.add_trace(trace)

        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    def _get_foil_coordinates(self) -> None:
        
        if hasattr(self, "_tab_height"):
            x, y = self._get_footprint(notch_height=self._tab_height)
        else:
            x, y = self._get_footprint()

        x, y, z, side = self.extrude_footprint(x, y, self._datum, self._thickness)
        self._foil_coordinates = np.column_stack((x, y, z))
        self._foil_coordinates_side = side

    def _get_a_side_coated_coordinates(self) -> Tuple[go.Scatter, float]:
        self._a_side_coated_coordinates = self._get_coated_area_coordinates(side="a")

    def _get_b_side_coated_coordinates(self) -> Tuple[go.Scatter, float]:
        self._b_side_coated_coordinates = self._get_coated_area_coordinates(side="b")

    def _get_a_side_insulation_coordinates(self) -> go.Scatter:
        self._a_side_insulation_coordinates = self._get_insulation_coordinates(side="a")

    def _get_b_side_insulation_coordinates(self) -> go.Scatter:
        self._b_side_insulation_coordinates = self._get_insulation_coordinates(side="b")

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
        self._foil_coordinates = self.rotate_coordinates(self._foil_coordinates, rotation_axis, 180, center=self._datum)
        self._a_side_coated_coordinates = self.rotate_coordinates(self._a_side_coated_coordinates, rotation_axis, 180, center=self._datum)
        self._b_side_coated_coordinates = self.rotate_coordinates(self._b_side_coated_coordinates, rotation_axis, 180, center=self._datum)

        if hasattr(self, "_a_side_insulation_coordinates"):
            self._a_side_insulation_coordinates = self.rotate_coordinates(
                self._a_side_insulation_coordinates,
                rotation_axis,
                180,
                center=self._datum,
            )
        if hasattr(self, "_b_side_insulation_coordinates"):
            self._b_side_insulation_coordinates = self.rotate_coordinates(
                self._b_side_insulation_coordinates,
                rotation_axis,
                180,
                center=self._datum,
            )

        if hasattr(self, "_weld_tabs"):
            for tab in self._weld_tabs:
                tab._foil_coordinates = self.rotate_coordinates(tab._foil_coordinates, rotation_axis, 180, center=self._datum)
                tab_datum_array = np.array([[tab._datum[0], tab._datum[1], tab._datum[2]]])
                rotated_datum = self.rotate_coordinates(tab_datum_array, rotation_axis, 180, center=self._datum)
                tab._datum = tuple(rotated_datum[0])

        if bool_update:
            # update action booleans
            if axis == "x":
                self._flipped_x = not self._flipped_x
            if axis == "y":
                self._flipped_y = not self._flipped_y
            if axis == "z":
                self._flipped_z = not self._flipped_z

        return self

    def _translate(self, vector: Iterable[float]) -> None:

        # convert to numpy array
        vector = np.array(vector)

        # translate foil coordinates coordinates
        self._foil_coordinates = self._foil_coordinates.copy()
        self._foil_coordinates += vector

        # translate a side coated coordinates
        coords_copy = self._a_side_coated_coordinates.copy()
        nan_mask = np.isnan(coords_copy)
        coords_copy[nan_mask] = 0
        coords_copy += vector
        coords_copy[nan_mask] = np.nan
        self._a_side_coated_coordinates = coords_copy

        # translate b side coated coordinates
        coords_copy = self._b_side_coated_coordinates.copy()
        nan_mask = np.isnan(coords_copy)
        coords_copy[nan_mask] = 0
        coords_copy += vector
        coords_copy[nan_mask] = np.nan
        self._b_side_coated_coordinates = coords_copy

        # translate insulation coordinates if they exist
        if hasattr(self, "_a_side_insulation_coordinates") and self._a_side_insulation_coordinates is not None:
            self._a_side_insulation_coordinates = self._a_side_insulation_coordinates.copy()
            self._a_side_insulation_coordinates += vector
        if hasattr(self, "_b_side_insulation_coordinates") and self._b_side_insulation_coordinates is not None:
            self._b_side_insulation_coordinates = self._b_side_insulation_coordinates.copy()
            self._b_side_insulation_coordinates += vector

        # translate the tabs if they exist
        if hasattr(self, "_weld_tabs"):
            for tab in self._weld_tabs:
                _new_datum = (
                    tab._datum[0] + vector[0],
                    tab._datum[1] + vector[1],
                    tab._datum[2] + vector[2],
                )

                new_datum = tuple(d * M_TO_MM for d in _new_datum)

                tab.datum = new_datum

        return self

    def get_center_line(self) -> np.ndarray:
        return self.get_xz_center_line(self._foil_coordinates)

    def get_a_side_view(self, **kwargs) -> go.Figure:
        z_coords = self._foil_coordinates[:, 2]
        z_a = z_coords[self._foil_coordinates_side == "a"].mean()
        z_b = z_coords[self._foil_coordinates_side == "b"].mean()

        top_side = "a" if z_a > z_b else "b"

        if top_side == "a":
            return self.get_top_down_view(**kwargs)
        else:
            self._flip("y")
            figure = self.get_top_down_view(**kwargs)
            self._flip("y")
            return figure

    def get_b_side_view(self, **kwargs) -> go.Figure:
        z_coords = self._foil_coordinates[:, 2]
        z_a = z_coords[self._foil_coordinates_side == "a"].mean()
        z_b = z_coords[self._foil_coordinates_side == "b"].mean()

        top_side = "a" if z_a > z_b else "b"

        if top_side == "b":
            return self.get_top_down_view(**kwargs)
        else:
            self._flip("y")
            figure = self.get_top_down_view(**kwargs)
            self._flip("y")
            return figure

    def get_right_left_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the right-left view of the punched current collector.
        The right-left view is a rectangle representing the right and left sides of the current collector.
        """
        figure = go.Figure()

        figure.add_trace(self.right_left_foil_trace)
        figure.add_trace(self.right_left_a_side_coated_trace)
        figure.add_trace(self.right_left_b_side_coated_trace)

        if hasattr(self, "_right_left_a_side_insulation_coordinates") and self._right_left_a_side_insulation_coordinates is not None:
            figure.add_trace(self.right_left_a_side_insulation_trace)

        if hasattr(self, "_right_left_b_side_insulation_coordinates") and self._right_left_b_side_insulation_coordinates is not None:
            figure.add_trace(self.right_left_b_side_insulation_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    def set_ranges_from_reference(
        self,
        reference: "_CurrentCollector",
        length_multiplier: float = 1.2,
    ) -> None:
        """
        Set the length and width ranges based on a reference current collector.

        Parameters:
        ----------
        reference: CurrentCollector
            The reference current collector to derive ranges from.
        """
        # validate the reference type
        self.validate_type(reference, _CurrentCollector, "reference")

        self._x_foil_length_range = (
            reference._x_foil_length,
            reference._x_foil_length * length_multiplier,
        )

        self._y_foil_length_range = (
            reference._y_foil_length,
            reference._y_foil_length * length_multiplier,
        )

    @abstractmethod
    def _get_coated_area_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Get the coordinates of the coated area for a given side ('a' or 'b').
        """
        pass

    @abstractmethod
    def _get_insulation_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Get the coordinates of the insulation area for a given side ('a' or 'b').
        """
        pass

    @abstractmethod
    def _get_footprint(self) -> pd.DataFrame:
        """
        Get the footprint of the current collector.
        """
        pass

    @property
    def mass(self) -> float:
        """
        Get the mass of the current collector in grams.
        """
        return np.round(self._mass * KG_TO_G, 2)
    
    @property
    def cost(self) -> float:
        """
        Get the cost of the current collector in USD.
        """
        return np.round(self._cost, 2)

    @property
    def right_left_b_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the b side insulation area.
        """
        # get the coordinates
        b_side_insulation_coordinates = self.order_coordinates_clockwise(self.b_side_insulation_coordinates, plane="yz")

        # make the trace
        b_side_insulation_trace = go.Scatter(
            x=b_side_insulation_coordinates["y"],
            y=b_side_insulation_coordinates["z"],
            mode="lines",
            name="B Side Insulation Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor="white",
            fillpattern=self._b_in_fill_pattern,
            legendgroup="B Side Insulation Area",
            showlegend=True,
        )

        return b_side_insulation_trace

    @property
    def right_left_a_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the a side insulation area.
        """
        # get the coordinates
        a_side_insulation_coordinates = self.order_coordinates_clockwise(self.a_side_insulation_coordinates, plane="yz")

        # make the trace
        a_side_insulation_trace = go.Scatter(
            x=a_side_insulation_coordinates["y"],
            y=a_side_insulation_coordinates["z"],
            mode="lines",
            name="A Side Insulation Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor="white",
            fillpattern=self._a_in_fill_pattern,
            legendgroup="A Side Insulation Area",
            showlegend=True,
        )

        return a_side_insulation_trace

    @property
    def right_left_b_side_coated_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the b side coated area.
        """
        # get the coordinates
        b_side_coated_coordinates = self.order_coordinates_clockwise(self.b_side_coated_coordinates, plane="yz")

        # make the trace
        b_side_coated_trace = go.Scatter(
            x=b_side_coated_coordinates["y"],
            y=b_side_coated_coordinates["z"],
            mode="lines",
            name="B Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor="black",
            fillpattern=self._b_am_fill_pattern,
            legendgroup="B Side Coated Area",
            showlegend=True,
        )

        return b_side_coated_trace

    @property
    def right_left_a_side_coated_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the a side coated area.
        """
        # get the coordinates
        a_side_coated_coordinates = self.order_coordinates_clockwise(self.a_side_coated_coordinates, plane="yz")

        # make the trace
        a_side_coated_trace = go.Scatter(
            x=a_side_coated_coordinates["y"],
            y=a_side_coated_coordinates["z"],
            mode="lines",
            name="A Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor="black",
            fillpattern=self._a_am_fill_pattern,
            legendgroup="A Side Coated Area",
            showlegend=True,
        )

        return a_side_coated_trace

    @property
    def right_left_foil_trace(self) -> go.Scatter:

        # get the coordinates of the foil, ordered clockwise
        foil_coordinates = self.order_coordinates_clockwise(self.foil_coordinates, plane="yz")

        # make the foil trace
        foil_trace = go.Scatter(
            x=foil_coordinates["y"],
            y=foil_coordinates["z"],
            mode="lines",
            name="Foil",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Foil",
            showlegend=True,
        )

        return foil_trace

    @property
    def top_down_foil_trace(self) -> go.Scatter:
        # get the side with the maximum z value
        foil_coordinates = self.foil_coordinates.query("z == z.max()")

        # make the foil trace
        foil_trace = go.Scatter(
            x=foil_coordinates["x"],
            y=foil_coordinates["y"],
            mode="lines",
            name="Foil",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Foil",
            showlegend=True,
        )

        return foil_trace

    @property
    def bottom_up_foil_trace(self) -> go.Scatter:

        # get the coordinates of the foil, ordered clockwise
        foil_coordinates = self.order_coordinates_clockwise(self.foil_coordinates, plane="xz")

        # add first row to end to close the shape
        foil_coordinates = pd.concat([foil_coordinates, foil_coordinates.iloc[[0]]], ignore_index=True)

        # make the foil trace
        foil_trace = go.Scatter(
            x=foil_coordinates["x"],
            y=foil_coordinates["z"],
            mode="lines",
            name="Foil",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Foil",
            showlegend=True,
        )

        return foil_trace

    @property
    def top_down_coated_area_trace(self) -> go.Scatter:
        
        side = self.top_side
        coated_area_coordinates = self.a_side_coated_coordinates if side == "a" else self.b_side_coated_coordinates

        # make the coated area trace
        coated_area_trace = go.Scatter(
            x=coated_area_coordinates["x"],
            y=coated_area_coordinates["y"],
            mode="lines",
            name="A Side Coated Area" if side == "a" else "B Side Coated Area",
            line=dict(width=1, color="black"),
            fillcolor="black",
            fill="toself",
            fillpattern=self._a_am_fill_pattern if side == "a" else self._b_am_fill_pattern,
        )

        return coated_area_trace

    @property
    def top_down_insulation_area_trace(self) -> go.Scatter:
        side = self.top_side
        insulation_area_coordinates = self.a_side_insulation_coordinates if side == "a" else self.b_side_insulation_coordinates

        # make the insulation area trace
        insulation_area_trace = go.Scatter(
            x=insulation_area_coordinates["x"],
            y=insulation_area_coordinates["y"],
            mode="lines",
            name="A Side Insulation Area" if side == "a" else "B Side Insulation Area",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor="white",
            fillpattern=self._a_in_fill_pattern if side == "a" else self._b_in_fill_pattern,
        )

        return insulation_area_trace

    @property
    def foil_coordinates(self) -> pd.DataFrame:
        return pd.DataFrame(
            np.column_stack((self._foil_coordinates, self._foil_coordinates_side)),
            columns=["x", "y", "z", "side"],
        ).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
            side=lambda df: df["side"].astype(str),
        )

    @property
    def top_side(self) -> str:
        """
        Get the top side of the current collector based on the z-coordinates.
        """
        z_coords = self._foil_coordinates[:, 2]
        z_a = z_coords[self._foil_coordinates_side == "a"].mean()
        z_b = z_coords[self._foil_coordinates_side == "b"].mean()
        return "a" if z_a > z_b else "b"

    @property
    def datum(self) -> Tuple[float, float, float]:
        """
        Get the datum of the current collector.
        """
        return (
            np.round(self._datum[0] * M_TO_MM, 2),
            np.round(self._datum[1] * M_TO_MM, 2),
            np.round(self._datum[2] * M_TO_MM, 2),
        )

    @property
    def datum_x(self) -> float:
        """
        Get the x-coordinate of the datum in mm.
        """
        return np.round(self._datum[0] * M_TO_MM, 2)

    @property
    def datum_x_range(self) -> Tuple[float, float]:
        """
        Get the x-coordinate range of the datum in mm.
        """
        return (-100, 100)

    @property
    def datum_y(self) -> float:
        """
        Get the y-coordinate of the datum in mm.
        """
        return np.round(self._datum[1] * M_TO_MM, 2)

    @property
    def datum_y_range(self) -> Tuple[float, float]:
        """
        Get the y-coordinate range of the datum in mm.
        """
        return (-100, 100)

    @property
    def datum_z(self) -> float:
        """
        Get the z-coordinate of the datum in mm.
        """
        return np.round(self._datum[2] * M_TO_MM, 2)

    @property
    def material(self) -> CurrentCollectorMaterial:
        """
        Get the material of the current collector.
        """
        return self._material

    @property
    def x_foil_length(self) -> float:
        return np.round(self._x_foil_length * M_TO_MM, 2)

    @property
    def y_foil_length(self) -> float:
        return np.round(self._y_foil_length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        return np.round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        min = 1e-6
        max = 20e-6
        return (round(min * M_TO_UM, 2), np.round(max * M_TO_UM, 2))

    @property
    def thickness_hard_range(self):
        return (0, 100)

    @property
    def insulation_width(self) -> float:
        return np.round(self._insulation_width * M_TO_MM, 2)

    @property
    def insulation_width_range(self) -> Tuple[float, float]:
        """
        Get the insulation width range in mm.
        """
        min = 0
        max = self._y_foil_length / 4 - 0.001

        return (round(min * M_TO_MM, 1), np.round(max * M_TO_MM, 1))

    @property
    def insulation_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the hard range for the insulation width in mm.
        """
        return (0, self.y_foil_length / 2)

    @property
    def name(self) -> str:
        """
        Get the name of the current collector.
        """
        return self._name

    @property
    def properties(self) -> dict:
        """
        Get the properties of the current collector.
        """
        return {
            "Mass": f"{self.mass} g",
            "Cost": f"{self.cost} $",
            "Total single sided area": f"{self.foil_area} cm²",
            "Total coated area": f"{self.coated_area} cm²",
            "Total insulation area": f"{self.insulation_area} cm²",
        }

    @property
    def coated_area(self) -> float:
        return np.round(self._coated_area * M_TO_CM**2, 1)

    @property
    def a_side_coated_area(self) -> float:
        return np.round(self._a_side_coated_area * M_TO_CM**2, 2)

    @property
    def a_side_coated_coordinates(self) -> pd.DataFrame:
        """
        Get the A side coated coordinates of the current collector.
        """
        return pd.DataFrame(self._a_side_coated_coordinates, columns=["x", "y", "z"]).assign(
            x=lambda x: (x["x"].astype(float) * M_TO_MM).round(10),
            y=lambda x: (x["y"].astype(float) * M_TO_MM).round(10),
            z=lambda x: (x["z"].astype(float) * M_TO_MM).round(10),
        )

    @property
    def b_side_coated_area(self) -> float:
        return np.round(self._b_side_coated_area * M_TO_CM**2, 2)

    @property
    def b_side_coated_coordinates(self) -> pd.DataFrame:
        """
        Get the B side coated coordinates of the current collector.
        """
        return pd.DataFrame(self._b_side_coated_coordinates, columns=["x", "y", "z"]).assign(
            x=lambda x: (x["x"].astype(float) * M_TO_MM).round(10),
            y=lambda x: (x["y"].astype(float) * M_TO_MM).round(10),
            z=lambda x: (x["z"].astype(float) * M_TO_MM).round(10),
        )

    @property
    def foil_area(self) -> float:
        return np.round(self._foil_area * M_TO_CM**2, 2)

    @property
    def a_side_insulation_area(self) -> float:
        return np.round(self._a_side_insulation_area * M_TO_CM**2, 2)

    @property
    def a_side_insulation_coordinates(self) -> pd.DataFrame:
        """
        Get the A side insulation coordinates of the current collector.
        """
        return (
            pd.DataFrame(self._a_side_insulation_coordinates, columns=["x", "y", "z"])
            .assign(
                x=lambda x: (x["x"].astype(float) * M_TO_MM).round(10),
                y=lambda x: (x["y"].astype(float) * M_TO_MM).round(10),
                z=lambda x: (x["z"].astype(float) * M_TO_MM).round(10),
            )
            .astype({"x": float, "y": float, "z": float})
        )

    @property
    def b_side_insulation_area(self) -> float:
        return np.round(self._b_side_insulation_area * M_TO_CM**2, 2)

    @property
    def b_side_insulation_coordinates(self) -> pd.DataFrame:
        """
        Get the B side insulation coordinates of the current collector.
        """
        return (
            pd.DataFrame(self._b_side_insulation_coordinates, columns=["x", "y", "z"])
            .assign(
                x=lambda x: (x["x"].astype(float) * M_TO_MM).round(10),
                y=lambda x: (x["y"].astype(float) * M_TO_MM).round(10),
                z=lambda x: (x["z"].astype(float) * M_TO_MM).round(10),
            )
            .astype({"x": float, "y": float, "z": float})
        )

    @property
    def insulation_area(self) -> float:
        return np.round(self._insulation_area * M_TO_CM**2, 2)

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        return (0, 5000)

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:

        # validate the datum
        self.validate_datum(datum)

        if self._update_properties:
            # calculate the translation vector in m
            translation_vector = (
                float(datum[0]) * MM_TO_M - self._datum[0],
                float(datum[1]) * MM_TO_M - self._datum[1],
                float(datum[2]) * MM_TO_M - self._datum[2],
            )

            # translate all coordinates
            self._translate(translation_vector)

        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )

    @material.setter
    @calculate_bulk_properties
    def material(self, material: CurrentCollectorMaterial) -> None:
        self.validate_type(material, CurrentCollectorMaterial, "material")
        self._material = deepcopy(material)
        self._calculate_fill_patterns()

    @datum_x.setter
    def datum_x(self, x: float) -> None:
        self.datum = (x, self.datum_y, self.datum_z)

    @datum_y.setter
    def datum_y(self, y: float) -> None:
        self.datum = (self.datum_x, y, self.datum_z)

    @datum_z.setter
    def datum_z(self, z: float) -> None:
        self.datum = (self.datum_x, self.datum_y, z)

    @x_foil_length.setter
    @calculate_all_properties
    def x_foil_length(self, x_foil_length: float) -> None:

        # validate the x_foil_length
        self.validate_positive_float(x_foil_length, "x_foil_length")

        # set the x_foil_length in m
        self._x_foil_length = float(x_foil_length) * MM_TO_M

        # update the weld tab positions if they exist
        if hasattr(self, "_weld_tabs"):
            self.weld_tab_positions = self.weld_tab_positions

    @y_foil_length.setter
    @calculate_all_properties
    def y_foil_length(self, y_foil_length: float) -> None:
        self.validate_positive_float(y_foil_length, "y_foil_length")
        self._y_foil_length = float(y_foil_length) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "thickness")
        self._thickness = float(thickness) * UM_TO_M

    @insulation_width.setter
    @calculate_areas
    def insulation_width(self, insulation_width: float) -> None:
        self.validate_positive_float(insulation_width, "insulation_width")
        self._insulation_width = float(insulation_width) * MM_TO_M

    @name.setter
    def name(self, name: str) -> None:
        self.validate_string(name, "name")
        self._name = name


class _TabbedCurrentCollector(_CurrentCollector):
    """
    Abstract base class for current collectors with integrated tabs.

    This class extends the basic current collector functionality to include
    tab geometries that provide electrical connection points for battery cells.

    The tabbed current collector includes:
    - Main foil geometry for active material support
    - Integrated tab extending from the foil
    - Coating area calculations that account for tab regions

    This class serves as a foundation for collectors where the tab is
    formed as part of the main collector sheet, as opposed to separately
    welded components.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical, thermal, and mechanical properties
    x_foil_length : float
        Length of the collector foil in the x-direction (mm)
        Does not include tab extension
    y_foil_length : float
        Width of the collector foil in the y-direction (mm)
    tab_width : float
        Width of the tab extension (mm)
        Typical range: 10-50 mm depending on current requirements
    tab_height : float
        Height/extension of the tab beyond the foil (mm)
        Typical range: 5-25 mm for accessibility and current capacity
    coated_tab_height : float
        Height of active material coating on the tab (mm)
        Usually less than tab_height to prevent short circuits
        Set to 0 for uncoated tabs
    thickness : float
        Material thickness in micrometers (μm)
    insulation_width : float, optional
        Width of insulation strip around edges (mm, default: 0)
    name : str, optional
        Descriptive name for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Attributes
    ----------
    tab_area : float
        Surface area of the tab extension (mm²)
    coated_tab_area : float
        Area of tab covered with active material (mm²)
    uncoated_tab_area : float
        Area of tab not covered with active material (mm²)
    tab_resistance : float
        Electrical resistance through the tab (Ω)
    current_density_max : float
        Maximum recommended current density (A/mm²)

    The coated tab height should always be less than the total tab height
    to provide an uncoated connection area and prevent active material
    from interfering with electrical connections.

    Examples
    --------
    This is an abstract class. Use concrete implementations:

    >>> from steer_materials import copper_foil
    >>> collector = PunchedCurrentCollector(
    ...     material=copper_foil,
    ...     x_foil_length=120.0,
    ...     y_foil_length=180.0,
    ...     tab_width=20.0,
    ...     tab_height=12.0,
    ...     coated_tab_height=8.0,
    ...     thickness=10.0
    ... )
    >>> print(f"Tab area: {collector.tab_area:.1f} mm²")
    >>> print(f"Uncoated tab area: {collector.uncoated_tab_area:.1f} mm²")

    See Also
    --------
    PunchedCurrentCollector : Simple tabbed collector with rectangular geometry
    NotchedCurrentCollector : Tabbed collector with notched foil
    _TapeCurrentCollector : Alternative tape-based connection method
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        x_foil_length: float,
        y_foil_length: float,
        tab_width: float,
        tab_height: float,
        coated_tab_height: float,
        thickness: float,
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Tabbed Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
        **kwargs,
    ):
        """
        Initialize an object that represents a tabbed current collector.

        Parameters:
        ----------
        material: CurrentCollectorMaterial
            Material of the current collector.
        x_foil_length: float
            Length of the current collector in mm.
        y_foil_length: float
            Width of the current collector in mm.
        tab_width: float
            Width of the tab in mm.
        tab_height: float
            Height of the tab in mm.
        coated_tab_height: float
            Height of the coated tab on the top side in mm.
        thickness: float
            Thickness of the current collector in um.
        insulation_width: Optional[float]
            Width of the insulation in mm, default is 0.
        name: Optional[str]
            Name of the current collector, default is 'Tabbed Current Collector'.
        kwargs: dict
            Additional keyword arguments for customization.
        """
        super().__init__(
            material=material,
            x_foil_length=x_foil_length,
            y_foil_length=y_foil_length,
            thickness=thickness,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
            **kwargs,
        )

        self.tab_width = tab_width
        self.tab_height = tab_height
        self.coated_tab_height = coated_tab_height
        self._total_height = self._y_foil_length + self._tab_height

    def _get_coated_area_coordinates(self, side: str) -> np.ndarray:
        """
        Return coated area coordinates for the specified side as a regular NumPy array [x, y, z].
        """
        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_coat_end = self._y_foil_length + self._coated_tab_height - self._insulation_width

        if _y_coat_end > self._y_foil_length:
            notch = self._coated_tab_height - self._insulation_width
            y_depth = self._y_foil_length
        else:
            notch = 0
            y_depth = _y_coat_end

        # Get x, y coordinates as separate 1D arrays
        if hasattr(self, "_bare_lengths_a_side") or hasattr(self, "_bare_lengths_b_side"):
            initial_skip_coat = self._bare_lengths_a_side[0] if side == "a" else self._bare_lengths_b_side[0]
            final_skip_coat = self._bare_lengths_a_side[1] if side == "a" else self._bare_lengths_b_side[1]
            
            # Check if bare lengths exceed foil length - return empty arrays if so
            if initial_skip_coat + final_skip_coat >= self._x_foil_length:
                x = np.array([])
                y = np.array([])
            else:
                x_start = self._datum[0] - self._x_foil_length / 2 + initial_skip_coat
                x_end = self._datum[0] + self._x_foil_length / 2 - final_skip_coat
                x, y = self._get_footprint(notch_height=notch, y_depth=y_depth, x_start=x_start, x_end=x_end)

        else:
            x, y = self._get_footprint(notch_height=notch, y_depth=y_depth)  # each of shape (N,)

        # If no coated area (empty arrays), return empty coordinate array
        if len(x) == 0 or len(y) == 0:
            return np.empty((0, 3))

        # Get z value from foil coordinates
        idx = np.where(self._foil_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No foil coordinates found for side '{side}'")

        z_value = self._foil_coordinates[idx[0], 2]

        # Create z array
        z = np.full_like(x, z_value)

        # Combine into (N, 3) array
        coated_area = np.column_stack((x, y, z))

        return coated_area

    @property
    def tab_width(self) -> float:
        return np.round(self._tab_width * M_TO_MM, 2)

    @property
    def tab_height(self) -> float:
        return np.round(self._tab_height * M_TO_MM, 2)

    @property
    def tab_height_range(self) -> Tuple[float, float]:
        return (1, self.y_foil_length * 1 / 4)

    @property
    def tab_height_hard_range(self) -> Tuple[float, float]:
        return (self.tab_height_range[0], 100)

    @property
    def coated_tab_height(self) -> float:
        return np.round(self._coated_tab_height * M_TO_MM, 2)

    @property
    def coated_tab_height_range(self) -> Tuple[float, float]:
        min = 0
        max = self._tab_height / 2 - 0.1 * MM_TO_M

        return (round(min * M_TO_MM, 1), np.round(max * M_TO_MM, 1))

    @property
    def coated_tab_height_hard_range(self) -> Tuple[float, float]:
        return self.coated_tab_height_range

    @property
    def total_height(self) -> float:
        return np.round(self._total_height * M_TO_MM, 2)

    @property
    def tab_position_range(self) -> Tuple[float, float]:
        return self.tab_position_hard_range

    @property
    def tab_position_hard_range(self) -> Tuple[float, float]:
        min = self._tab_width / 2 + 1 * MM_TO_M
        max = self._x_foil_length - self._tab_width / 2 - 1 * MM_TO_M
        return (round(min * M_TO_MM, 1), np.round(max * M_TO_MM, 1))

    @tab_width.setter
    @calculate_all_properties
    def tab_width(self, tab_width: float) -> None:
        self.validate_positive_float(tab_width, "tab_width")
        self._tab_width = float(tab_width) * MM_TO_M

        if self._tab_width > self._x_foil_length:
            raise ValueError("Tab width cannot be greater than the length of the current collector.")

    @tab_height.setter
    @calculate_all_properties
    def tab_height(self, tab_height: float) -> None:
        self.validate_positive_float(tab_height, "tab_height")
        self._tab_height = float(tab_height) * MM_TO_M

    @coated_tab_height.setter
    @calculate_areas
    def coated_tab_height(self, coated_tab_height: float) -> None:
        self.validate_positive_float(coated_tab_height, "coated_tab_height")
        self._coated_tab_height = float(coated_tab_height) * MM_TO_M

        if self._coated_tab_height > self._tab_height:
            raise ValueError("Covered tab height on the top side cannot be greater than the tab height.")


class _TapeCurrentCollector(_CurrentCollector):
    """
    Abstract base class for current collectors using tape-style connections.

    This class implements current collectors which are much longer than they
    are wide. These are typically used in wound configurations where a single
    cathode current collector and a single anode current collector is used.

    Key features include:
    - Configurable bare lengths on both sides for connections
    - Precise coating area calculations excluding bare regions
    - Support for asymmetric bare regions for different applications

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material defining electrical, thermal, and mechanical properties
    x_foil_length : float
        Total length of the collector foil in x-direction (mm)
    y_foil_length : float
        Total width of the collector foil in y-direction (mm)
    thickness : float
        Material thickness in micrometers (μm)
    bare_lengths_a_side : tuple of float, optional
        (start, end) bare region lengths on a-side in mm (default: (0, 0))
        Defines uncoated regions at the beginning and end of the collector
    bare_lengths_b_side : tuple of float, optional
        (start, end) bare region lengths on b-side in mm (default: (0, 0))
        Allows for asymmetric bare region configuration
    insulation_width : float, optional
        Width of insulation strip around edges in mm (default: 0)
    name : str, optional
        Descriptive name for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Attributes
    ----------
    bare_area_a_side : float
        Total uncoated area on the a-side (mm²)
    bare_area_b_side : float
        Total uncoated area on the b-side (mm²)
    total_bare_area : float
        Combined uncoated area from both sides (mm²)
    connection_width : float
        Effective width available for electrical connections (mm)
    current_path_length : float
        Distance current must travel through the collector (mm)

    Examples
    --------
    This is an abstract class. Use concrete implementations:

    >>> from steer_materials import aluminum_foil
    >>> collector = NotchedCurrentCollector(
    ...     material=aluminum_foil,
    ...     x_foil_length=150.0,
    ...     y_foil_length=200.0,
    ...     bare_lengths_a_side=(10.0, 10.0),  # 10mm bare on each end
    ...     bare_lengths_b_side=(5.0, 5.0),   # Asymmetric bare regions
    ...     thickness=15.0
    ... )
    >>> print(f"Total bare area: {collector.total_bare_area:.1f} mm²")
    >>> print(f"Coated area: {collector.coated_area:.1f} mm²")

    See Also
    --------
    NotchedCurrentCollector : Tape-style collector with rectangular cutouts
    TablessCurrentCollector : Tape-style collector without protruding features
    _TabbedCurrentCollector : Alternative tab-based connection method
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        x_foil_length: float,
        y_foil_length: float,
        thickness: float,
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Tape Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
        **kwargs,
    ) -> None:
        """
        Construct a tape current collector.

        Parameters:
        ----------
        material: CurrentCollectorMaterial
            Material of the current collector.
        x_foil_length: float
            Length of the current collector in mm.
        y_foil_length: float
            Width of the current collector in mm.
        thickness: float
            Thickness of the current collector in um.
        bare_lengths_a_side: Tuple[float, float]
            Bare lengths on the A side in mm, default is (0, 0).
        bare_lengths_b_side: Tuple[float, float]
            Bare lengths on the B side in mm, default is (0, 0).
        insulation_width: Optional[float]
            Width of the insulation in mm, default is 0.
        name: Optional[str]
            Name of the current collector, default is 'Tape Current Collector'.
        datum: Optional[Tuple[float, float, float]]
            Datum of the current collector in mm, default is (0, 0, 0).
        kwargs: dict
            Additional keyword arguments for customization.
        """
        super().__init__(
            material=material,
            x_foil_length=x_foil_length,
            y_foil_length=y_foil_length,
            insulation_width=insulation_width,
            thickness=thickness,
            name=name,
            datum=datum,
        )

        self.bare_lengths_a_side = bare_lengths_a_side
        self.bare_lengths_b_side = bare_lengths_b_side

    def _calculate_total_length_with_skip_coating(self):
        a_side_left = self._bare_lengths_a_side[0] if hasattr(self, "_bare_lengths_a_side") else 0
        a_side_right = self._bare_lengths_a_side[1] if hasattr(self, "_bare_lengths_a_side") else 0
        b_side_left = self._bare_lengths_b_side[0] if hasattr(self, "_bare_lengths_b_side") else 0
        b_side_right = self._bare_lengths_b_side[1] if hasattr(self, "_bare_lengths_b_side") else 0
        left_side = max(a_side_left, b_side_left)
        right_side = max(a_side_right, b_side_right)
        return left_side + right_side

    @property
    def x_foil_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_x_foil_length_range") and self._x_foil_length_range is not None:

            return (
                np.round(self._x_foil_length_range[0] * M_TO_MM, 2),
                np.round(self._x_foil_length_range[1] * M_TO_MM, 2),
            )

        else:
            min_length = self._calculate_total_length_with_skip_coating() * M_TO_MM
            return (np.round(min_length, 2), 10000)

    @property
    def y_foil_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_foil_length_range") and self._y_foil_length_range is not None:
            return (
                np.round(self._y_foil_length_range[0] * M_TO_MM, 2),
                np.round(self._y_foil_length_range[1] * M_TO_MM, 2),
            )
        else:
            return (10, 1000)

    @property
    def bare_lengths_a_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_a_side)

    @property
    def bare_lengths_b_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_b_side)

    @property
    def a_side_coated_section(self):
        """
        Property inidcating the length of the current collector that is coated on the A side. Given as a tuple, with the first float being the start point along the tape of the
        coated area, and the second float being the end point along the tape of the coated area.
        """
        return (
            np.round(self._bare_lengths_a_side[0] * M_TO_MM, 1),
            np.round((self._x_foil_length - self._bare_lengths_a_side[1]) * M_TO_MM, 1),
        )

    @property
    def a_side_coated_section_hard_range(self) -> Tuple[float, float]:
        """
        Get the range of the A side coated section in mm.
        """
        return (0, self.x_foil_length)

    @property
    def a_side_coated_section_range(self) -> Tuple[float, float]:
        return self.a_side_coated_section_hard_range

    @property
    def b_side_coated_section(self):
        """
        Property inidcating the length of the current collector that is coated on the B side. Given as a tuple, with the first float being the start point along the tape of the
        coated area, and the second float being the end point along the tape of the coated area.
        """
        return (
            np.round(self._bare_lengths_b_side[0] * M_TO_MM, 1),
            np.round((self._x_foil_length - self._bare_lengths_b_side[1]) * M_TO_MM, 1),
        )

    @property
    def b_side_coated_section_hard_range(self) -> Tuple[float, float]:
        """
        Get the range of the B side coated section in mm.
        """
        return (0, self.x_foil_length)

    @property
    def b_side_coated_section_range(self) -> Tuple[float, float]:
        return self.b_side_coated_section_hard_range

    @property
    def length(self) -> float:
        return self.x_foil_length

    @property
    def length_range(self) -> Tuple[float, float]:
        return self.x_foil_length_range

    @property
    def length_hard_range(self) -> Tuple[float, float]:
        """
        Get the length range in mm.
        """
        return (250, 10000)

    @property
    def width(self) -> float:
        return self.y_foil_length

    @property
    def width_range(self) -> Tuple[float, float]:
        return self.y_foil_length_range

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self.y_foil_length = width

    @bare_lengths_a_side.setter
    @calculate_areas
    def bare_lengths_a_side(self, bare_lengths_a_side: Iterable[float]) -> None:
        self.validate_two_iterable_of_floats(bare_lengths_a_side, "bare_lengths_a_side")
        self._bare_lengths_a_side = tuple(float(length) * MM_TO_M for length in bare_lengths_a_side)

        if self._x_foil_length < sum(self._bare_lengths_a_side):
            raise ValueError("Total bare lengths on A side cannot be greater than the length of the current collector.")

    @bare_lengths_b_side.setter
    @calculate_areas
    def bare_lengths_b_side(self, bare_lengths_b_side: Iterable[float]) -> None:
        self.validate_two_iterable_of_floats(bare_lengths_b_side, "bare_lengths_b_side")

        self._bare_lengths_b_side = tuple(float(length) * MM_TO_M for length in bare_lengths_b_side)

        if self._x_foil_length < sum(self._bare_lengths_b_side):
            raise ValueError("Total bare lengths on B side cannot be greater than the length of the current collector.")

    @a_side_coated_section.setter
    @calculate_areas
    def a_side_coated_section(self, section: Tuple[float, float]) -> None:
        """
        Set the A side coated section.

        Parameters:
        ----------
        section: Tuple[float, float]
            A tuple containing the start and end points of the coated section along the tape in mm.
        """
        self.validate_two_iterable_of_floats(section, "a_side_coated_section")

        self._bare_lengths_a_side = (
            float(section[0]) * MM_TO_M,
            self._x_foil_length - float(section[1]) * MM_TO_M,
        )

    @b_side_coated_section.setter
    @calculate_areas
    def b_side_coated_section(self, section: Tuple[float, float]) -> None:
        """
        Set the B side coated section.

        Parameters:
        ----------
        section: Tuple[float, float]
            A tuple containing the start and end points of the coated section along the tape in mm.
        """
        self.validate_two_iterable_of_floats(section, "b_side_coated_section")

        self._bare_lengths_b_side = (
            float(section[0]) * MM_TO_M,
            self._x_foil_length - float(section[1]) * MM_TO_M,
        )

    @length.setter
    def length(self, length: float) -> None:

        # Validate the input length
        self.validate_positive_float(length, "length")

        # remove the weld tab positions that are greater than the new length
        if hasattr(self, "_weld_tabs"):
            self._weld_tab_positions = [p * MM_TO_M for p in self.weld_tab_positions if p <= length]

        # Set the new length
        self.x_foil_length = length

