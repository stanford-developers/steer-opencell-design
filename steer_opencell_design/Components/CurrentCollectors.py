# import core mixins
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin

# import core decorators
from steer_core.Decorators.General import (
    calculate_all_properties,
    calculate_bulk_properties,
)
from steer_core.Decorators.Coordinates import calculate_areas
from steer_core.Decorators.Objects import calculate_weld_tab_properties

# import core units
from steer_core.Constants.Units import *

# import materials
from steer_materials.CellMaterials.Base import CurrentCollectorMaterial

# import base functions
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Iterable
from plotly.subplots import make_subplots
from copy import deepcopy

# import base packages
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class _CurrentCollector(
    ABC, 
    CoordinateMixin, 
    ValidationMixin,
    DunderMixin,
    PlotterMixin
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
    x_body_length : float
        Length of the current collector body in the x-direction (mm)
        Typical range: 50-300 mm depending on cell format
    y_body_length : float
        Width of the current collector body in the y-direction (mm)
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
    body_area : float
        Total surface area of the current collector body (mm²)
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
    ...     x_body_length=150.0,  # mm
    ...     y_body_length=200.0,  # mm
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
        x_body_length: float,
        y_body_length: float,
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
        x_body_length : float
            Length of the current collector in mm.
        y_body_length : float
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
        self.x_body_length = x_body_length
        self.y_body_length = y_body_length
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
        self._get_body_coordinates()
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
        mask = self._body_coordinates_side == "a"
        body_a_side_area = self.get_area_from_points(self._body_coordinates[mask][:, 0], self._body_coordinates[mask][:, 1])

        # calculate the total upper and lower area of the body
        self._body_area = body_a_side_area * 2

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
        self._volume = self._body_area / 2 * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost

    def _calculate_fill_patterns(self) -> None:
        # Shading patterns
        self._a_am_fill_pattern = dict(shape="/", size=20, solidity=0.6, fgcolor=self._material._color)
        self._b_am_fill_pattern = dict(shape="\\", size=20, solidity=0.6, fgcolor=self._material._color)
        self._a_in_fill_pattern = dict(shape="\\", size=10, solidity=0.6, fgcolor=self._material._color)
        self._b_in_fill_pattern = dict(shape="/", size=10, solidity=0.6, fgcolor=self._material._color)

    def _get_full_top_down_view(self, **kwargs) -> go.Figure:
        
        fig = go.Figure()

        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == "a"].mean()
        z_b = z_coords[self._body_coordinates_side == "b"].mean()
        top_side = "a" if z_a > z_b else "b"

        # check if weld tabs are present
        if hasattr(self, "_tab_weld_side") and self._tab_weld_side != top_side:
            for i, tab in enumerate(self._weld_tabs):
                trace = tab.top_down_body_trace
                trace.showlegend = i == 0
                fig.add_trace(trace)

        # add traces to the figure
        fig.add_trace(self.top_down_body_trace)
        fig.add_trace(self.top_down_coated_area_trace)

        if hasattr(self, "top_down_insulation_area_trace"):
            fig.add_trace(self.top_down_insulation_area_trace)

        # check if weld tabs are present
        if hasattr(self, "_tab_weld_side") and self._tab_weld_side == top_side:
            for i, tab in enumerate(self._weld_tabs):
                trace = tab.top_down_body_trace
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

    def _get_body_coordinates(self) -> None:
        if hasattr(self, "_tab_height"):
            x, y = self._get_footprint(notch_height=self._tab_height)
        else:
            x, y = self._get_footprint()

        x, y, z, side = self.extrude_footprint(x, y, self._datum, self._thickness)
        self._body_coordinates = np.column_stack((x, y, z))
        self._body_coordinates_side = side

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
        self._body_coordinates = self.rotate_coordinates(self._body_coordinates, rotation_axis, 180, center=self._datum)
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
                tab._body_coordinates = self.rotate_coordinates(tab._body_coordinates, rotation_axis, 180, center=self._datum)
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

        # translate body coordinates coordinates
        self._body_coordinates += vector

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
            self._a_side_insulation_coordinates += vector
        if hasattr(self, "_b_side_insulation_coordinates") and self._b_side_insulation_coordinates is not None:
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
        return self.get_xz_center_line(self._body_coordinates)

    def get_a_side_view(self, **kwargs) -> go.Figure:
        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == "a"].mean()
        z_b = z_coords[self._body_coordinates_side == "b"].mean()

        top_side = "a" if z_a > z_b else "b"

        if top_side == "a":
            return self.get_top_down_view(**kwargs)
        else:
            self._flip("y")
            figure = self.get_top_down_view(**kwargs)
            self._flip("y")
            return figure

    def get_b_side_view(self, **kwargs) -> go.Figure:
        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == "a"].mean()
        z_b = z_coords[self._body_coordinates_side == "b"].mean()

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

        figure.add_trace(self.right_left_body_trace)
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
        self.validate_type(reference, _CurrentCollector, "reference")

        self._x_body_length_range = (
            reference._x_body_length,
            reference._x_body_length * length_multiplier,
        )

        self._y_body_length_range = (
            reference._y_body_length,
            reference._y_body_length * length_multiplier,
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
    def right_left_body_trace(self) -> go.Scatter:

        # get the coordinates of the body, ordered clockwise
        body_coordinates = self.order_coordinates_clockwise(self.body_coordinates, plane="yz")

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates["y"],
            y=body_coordinates["z"],
            mode="lines",
            name="Body",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )

        return body_trace

    @property
    def top_down_body_trace(self) -> go.Scatter:
        # get the side with the maximum z value
        body_coordinates = self.body_coordinates.query("z == z.max()")

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates["x"],
            y=body_coordinates["y"],
            mode="lines",
            name="Body",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )

        return body_trace

    @property
    def bottom_up_body_trace(self) -> go.Scatter:

        # get the coordinates of the body, ordered clockwise
        body_coordinates = self.order_coordinates_clockwise(self.body_coordinates, plane="xz")

        # add first row to end to close the shape
        body_coordinates = pd.concat([body_coordinates, body_coordinates.iloc[[0]]], ignore_index=True)

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates["x"],
            y=body_coordinates["z"],
            mode="lines",
            name="Body",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )

        return body_trace

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
    def body_coordinates(self) -> pd.DataFrame:
        return pd.DataFrame(
            np.column_stack((self._body_coordinates, self._body_coordinates_side)),
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
        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == "a"].mean()
        z_b = z_coords[self._body_coordinates_side == "b"].mean()
        return "a" if z_a > z_b else "b"

    @property
    def datum(self) -> Tuple[float, float, float]:
        """
        Get the datum of the current collector.
        """
        return (
            round(self._datum[0] * M_TO_MM, 2),
            round(self._datum[1] * M_TO_MM, 2),
            round(self._datum[2] * M_TO_MM, 2),
        )

    @property
    def datum_x(self) -> float:
        """
        Get the x-coordinate of the datum in mm.
        """
        return round(self._datum[0] * M_TO_MM, 2)

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
        return round(self._datum[1] * M_TO_MM, 2)

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
        return round(self._datum[2] * M_TO_MM, 2)

    @property
    def material(self) -> CurrentCollectorMaterial:
        """
        Get the material of the current collector.
        """
        return self._material

    @property
    def x_body_length(self) -> float:
        return round(self._x_body_length * M_TO_MM, 2)

    @property
    def y_body_length(self) -> float:
        return round(self._y_body_length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        min = 1e-6
        max = 20e-6
        return (round(min * M_TO_UM, 2), round(max * M_TO_UM, 2))

    @property
    def thickness_hard_range(self):
        return (0, 100)

    @property
    def insulation_width(self) -> float:
        return round(self._insulation_width * M_TO_MM, 2)

    @property
    def insulation_width_range(self) -> Tuple[float, float]:
        """
        Get the insulation width range in mm.
        """
        min = 0
        max = self._y_body_length / 4 - 0.001

        return (round(min * M_TO_MM, 1), round(max * M_TO_MM, 1))

    @property
    def insulation_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the hard range for the insulation width in mm.
        """
        return (0, self.y_body_length / 2)

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
            "Total single sided area": f"{self.body_area} cm²",
            "Total coated area": f"{self.coated_area} cm²",
            "Total insulation area": f"{self.insulation_area} cm²",
        }

    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_CM**2, 1)

    @property
    def a_side_coated_area(self) -> float:
        return round(self._a_side_coated_area * M_TO_CM**2, 2)

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
        return round(self._b_side_coated_area * M_TO_CM**2, 2)

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
    def body_area(self) -> float:
        return round(self._body_area * M_TO_CM**2, 2)

    @property
    def a_side_insulation_area(self) -> float:
        return round(self._a_side_insulation_area * M_TO_CM**2, 2)

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
        return round(self._b_side_insulation_area * M_TO_CM**2, 2)

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
        return round(self._insulation_area * M_TO_CM**2, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 3)

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
        self._material = material
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

    @x_body_length.setter
    @calculate_all_properties
    def x_body_length(self, x_body_length: float) -> None:
        self.validate_positive_float(x_body_length, "x_body_length")
        self._x_body_length = float(x_body_length) * MM_TO_M

        if hasattr(self, "_weld_tabs"):
            self.weld_tab_positions = self.weld_tab_positions

    @y_body_length.setter
    @calculate_all_properties
    def y_body_length(self, y_body_length: float) -> None:
        self.validate_positive_float(y_body_length, "y_body_length")
        self._y_body_length = float(y_body_length) * MM_TO_M

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
    - Main body geometry for active material support
    - Integrated tab extending from the body
    - Coating area calculations that account for tab regions

    This class serves as a foundation for collectors where the tab is
    formed as part of the main collector sheet, as opposed to separately
    welded components.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical, thermal, and mechanical properties
    x_body_length : float
        Length of the collector body in the x-direction (mm)
        Does not include tab extension
    y_body_length : float
        Width of the collector body in the y-direction (mm)
    tab_width : float
        Width of the tab extension (mm)
        Typical range: 10-50 mm depending on current requirements
    tab_height : float
        Height/extension of the tab beyond the body (mm)
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
    ...     x_body_length=120.0,
    ...     y_body_length=180.0,
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
    NotchedCurrentCollector : Tabbed collector with notched body
    _TapeCurrentCollector : Alternative tape-based connection method
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        x_body_length: float,
        y_body_length: float,
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
        x_body_length: float
            Length of the current collector in mm.
        y_body_length: float
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
            x_body_length=x_body_length,
            y_body_length=y_body_length,
            thickness=thickness,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
            **kwargs,
        )

        self.tab_width = tab_width
        self.tab_height = tab_height
        self.coated_tab_height = coated_tab_height
        self._total_height = self._y_body_length + self._tab_height

    def _get_coated_area_coordinates(self, side: str) -> np.ndarray:
        """
        Return coated area coordinates for the specified side as a regular NumPy array [x, y, z].
        """
        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_coat_end = self._y_body_length + self._coated_tab_height - self._insulation_width

        if _y_coat_end > self._y_body_length:
            notch = self._coated_tab_height - self._insulation_width
            y_depth = self._y_body_length
        else:
            notch = 0
            y_depth = _y_coat_end

        # Get x, y coordinates as separate 1D arrays
        if hasattr(self, "_bare_lengths_a_side") or hasattr(self, "_bare_lengths_b_side"):
            initial_skip_coat = self._bare_lengths_a_side[0] if side == "a" else self._bare_lengths_b_side[0]
            final_skip_coat = self._bare_lengths_a_side[1] if side == "a" else self._bare_lengths_b_side[1]
            x_start = self._datum[0] - self._x_body_length / 2 + initial_skip_coat
            x_end = self._datum[0] + self._x_body_length / 2 - final_skip_coat
            x, y = self._get_footprint(notch_height=notch, y_depth=y_depth, x_start=x_start, x_end=x_end)
        else:
            x, y = self._get_footprint(notch_height=notch, y_depth=y_depth)  # each of shape (N,)

        # Get z value from body coordinates
        idx = np.where(self._body_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No body coordinates found for side '{side}'")

        z_value = self._body_coordinates[idx[0], 2]

        # Create z array
        z = np.full_like(x, z_value)

        # Combine into (N, 3) array
        coated_area = np.column_stack((x, y, z))

        return coated_area

    @property
    def tab_width(self) -> float:
        return round(self._tab_width * M_TO_MM, 2)

    @property
    def tab_height(self) -> float:
        return round(self._tab_height * M_TO_MM, 2)

    @property
    def tab_height_range(self) -> Tuple[float, float]:
        return (1, self.y_body_length * 1 / 4)

    @property
    def tab_height_hard_range(self) -> Tuple[float, float]:
        return (self.tab_height_range[0], 100)

    @property
    def coated_tab_height(self) -> float:
        return round(self._coated_tab_height * M_TO_MM, 2)

    @property
    def coated_tab_height_range(self) -> Tuple[float, float]:
        min = 0
        max = self._tab_height / 2 - 0.1 * MM_TO_M

        return (round(min * M_TO_MM, 1), round(max * M_TO_MM, 1))

    @property
    def coated_tab_height_hard_range(self) -> Tuple[float, float]:
        return self.coated_tab_height_range

    @property
    def total_height(self) -> float:
        return round(self._total_height * M_TO_MM, 2)

    @property
    def tab_position_range(self) -> Tuple[float, float]:
        return self.tab_position_hard_range

    @property
    def tab_position_hard_range(self) -> Tuple[float, float]:
        min = self._tab_width / 2 + 1 * MM_TO_M
        max = self._x_body_length - self._tab_width / 2 - 1 * MM_TO_M
        return (round(min * M_TO_MM, 1), round(max * M_TO_MM, 1))

    @tab_width.setter
    @calculate_all_properties
    def tab_width(self, tab_width: float) -> None:
        self.validate_positive_float(tab_width, "tab_width")
        self._tab_width = float(tab_width) * MM_TO_M

        if self._tab_width > self._x_body_length:
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
    x_body_length : float
        Total length of the collector body in x-direction (mm)
    y_body_length : float
        Total width of the collector body in y-direction (mm)
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
    ...     x_body_length=150.0,
    ...     y_body_length=200.0,
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
        x_body_length: float,
        y_body_length: float,
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
        x_body_length: float
            Length of the current collector in mm.
        y_body_length: float
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
            x_body_length=x_body_length,
            y_body_length=y_body_length,
            insulation_width=insulation_width,
            thickness=thickness,
            name=name,
            datum=datum,
        )

        self.bare_lengths_a_side = bare_lengths_a_side
        self.bare_lengths_b_side = bare_lengths_b_side

    def _add_length_dimension(self, fig: go.Figure, aspect_ratio: float = 3, pad: float = 0.05) -> go.Figure:
        y = self._datum[1] - self._y_body_length / 2 - pad * self._y_body_length
        if self._x_body_length > self._y_body_length * aspect_ratio:
            xmin = self._datum[0] - self._x_body_length / 2
            xmax = xmin + aspect_ratio * self._y_body_length
            xmid = (xmin + xmax) / 2
            fig.add_annotation(
                x=xmax,
                ax=xmin,
                y=y,
                ay=y,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
            )
            fig.add_annotation(
                x=xmid,
                y=y,
                xref="x",
                yref="y",
                showarrow=False,
                yshift=-12,
                text=f"Length: {self.length} mm",
            )
            xmin = self._datum[0] + self._x_body_length / 2 - aspect_ratio * self._y_body_length
            xmax = self._datum[0] + self._x_body_length / 2
            xmid = (xmin + xmax) / 2
            fig.add_annotation(
                x=xmax,
                ax=xmin,
                y=y,
                ay=y,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
            )
            fig.add_annotation(
                x=xmid,
                y=y,
                xref="x",
                yref="y",
                showarrow=False,
                yshift=-12,
                text=f"\u00a0",
            )
        else:
            xmin = self._datum[0] - self._x_body_length / 2
            xmax = xmin + self._x_body_length
            xmid = (xmin + xmax) / 2
            fig.add_annotation(
                x=xmax,
                ax=xmin,
                y=y,
                ay=y,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
            )
            fig.add_annotation(
                x=xmid,
                y=y,
                xref="x",
                yref="y",
                showarrow=False,
                yshift=-12,
                text=f"Length: {self.length} mm",
            )

        return fig

    def _add_height_dimension(self, fig: go.Figure, pad: float = 0.05) -> go.Figure:
        # Height line
        x = self._datum[0] - self._x_body_length / 2 - pad * self._y_body_length
        ymin = self._datum[1] - self._y_body_length / 2
        ymax = ymin + self._y_body_length
        ymid = (ymin + ymax) / 2
        fig.add_annotation(
            x=x,
            ax=x,
            y=ymax,
            ay=ymin,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
        )
        fig.add_annotation(
            x=x,
            ax=x,
            y=ymin,
            ay=ymax,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
        )
        fig.add_annotation(
            x=x,
            y=ymid,
            xref="x",
            yref="y",
            showarrow=False,
            xshift=-12,
            text=f"Height: {self.y_body_length} mm",
            textangle=-90,
        )

        return fig

    # TODO: improve this function. Axes seem strange when overriding a previous figure in dash
    def get_top_down_view(self, aspect_ratio: float = 4, side: str = "a", use_subplots: bool = False, **kwargs) -> go.Figure:
        """
        Visualize the notched current collector.
        If use_subplots is True and the collector is long, split into two subplots for left and right ends.
        The vertical datum is centered at y = self.width / 2.

        :param aspect_ratio: float: aspect ratio of the plot, default is 4
        :param side: str: 'a' or 'b' to indicate which side to visualize
        :param use_subplots: bool: whether to create subplots for long collectors, default is False
        """
        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        max_x = self.y_body_length * aspect_ratio

        figure = self._get_full_top_down_view(**kwargs)

        if use_subplots and max_x < self.x_body_length:
            figure_subplot = make_subplots(
                rows=2,
                cols=1,
                vertical_spacing=0.2,
                subplot_titles=("Tape start", "Tape end"),
            )

            for trace in figure.data:
                trace1 = deepcopy(trace)
                trace2 = deepcopy(trace)

                group_name = trace.name or f"group_{id(trace)}"
                trace1.legendgroup = group_name
                trace2.legendgroup = group_name
                trace2.showlegend = False

                figure_subplot.add_trace(trace1, row=1, col=1)
                figure_subplot.add_trace(trace2, row=2, col=1)

            top_row_range = [
                (self.datum[0] - self.x_body_length / 2) - 300,
                self.datum[0] - self.x_body_length / 2 + max_x,
            ]

            bottom_row_range = [
                self.datum[0] + self.x_body_length / 2 - max_x,
                self.datum[0] + self.x_body_length / 2 + 300,
            ]

            # Set x-axis ranges
            figure_subplot.update_xaxes(range=top_row_range, row=1, col=1)
            figure_subplot.update_xaxes(range=bottom_row_range, row=2, col=1)

            # Set y-axis ranges to match the aspect ratio
            y_range = [
                self.datum[1] - self.y_body_length / 2,
                self.datum[1] + self.y_body_length / 2,
            ]

            figure_subplot.update_yaxes(range=y_range, row=1, col=1)
            figure_subplot.update_yaxes(range=y_range, row=2, col=1)

            # Ensure the same scale for x and y axes
            figure_subplot.update_layout(
                xaxis=dict(scaleanchor="y"),
                xaxis2=dict(scaleanchor="y2"),
            )

            figure = figure_subplot

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def x_body_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_x_body_length_range") and self._x_body_length_range is not None:
            return (
                round(self._x_body_length_range[0] * M_TO_MM, 2),
                round(self._x_body_length_range[1] * M_TO_MM, 2),
            )

        else:
            return (300, 5000)

    @property
    def y_body_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_body_length_range") and self._y_body_length_range is not None:
            return (
                round(self._y_body_length_range[0] * M_TO_MM, 2),
                round(self._y_body_length_range[1] * M_TO_MM, 2),
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
            round(self._bare_lengths_a_side[0] * M_TO_MM, 1),
            round((self._x_body_length - self._bare_lengths_a_side[1]) * M_TO_MM, 1),
        )

    @property
    def a_side_coated_section_hard_range(self) -> Tuple[float, float]:
        """
        Get the range of the A side coated section in mm.
        """
        return (0, self.x_body_length)

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
            round(self._bare_lengths_b_side[0] * M_TO_MM, 1),
            round((self._x_body_length - self._bare_lengths_b_side[1]) * M_TO_MM, 1),
        )

    @property
    def b_side_coated_section_hard_range(self) -> Tuple[float, float]:
        """
        Get the range of the B side coated section in mm.
        """
        return (0, self.x_body_length)

    @property
    def b_side_coated_section_range(self) -> Tuple[float, float]:
        return self.b_side_coated_section_hard_range

    @property
    def length(self) -> float:
        return self.x_body_length

    @property
    def length_range(self) -> Tuple[float, float]:
        return self.x_body_length_range

    @property
    def length_hard_range(self) -> Tuple[float, float]:
        """
        Get the length range in mm.
        """
        return (100, 10000)

    @property
    def width(self) -> float:
        return self.y_body_length

    @property
    def width_range(self) -> Tuple[float, float]:
        return self.y_body_length_range

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self.y_body_length = width

    @bare_lengths_a_side.setter
    @calculate_areas
    def bare_lengths_a_side(self, bare_lengths_a_side: Iterable[float]) -> None:
        self.validate_two_iterable_of_floats(bare_lengths_a_side, "bare_lengths_a_side")
        self._bare_lengths_a_side = tuple(float(length) * MM_TO_M for length in bare_lengths_a_side)

        if self._x_body_length < sum(self._bare_lengths_a_side):
            raise ValueError("Total bare lengths on A side cannot be greater than the length of the current collector.")

    @bare_lengths_b_side.setter
    @calculate_areas
    def bare_lengths_b_side(self, bare_lengths_b_side: Iterable[float]) -> None:
        self.validate_two_iterable_of_floats(bare_lengths_b_side, "bare_lengths_b_side")

        self._bare_lengths_b_side = tuple(float(length) * MM_TO_M for length in bare_lengths_b_side)

        if self._x_body_length < sum(self._bare_lengths_b_side):
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
            self._x_body_length - float(section[1]) * MM_TO_M,
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
            self._x_body_length - float(section[1]) * MM_TO_M,
        )

    @length.setter
    def length(self, length: float) -> None:
        self.validate_positive_float(length, "length")

        if hasattr(self, "_weld_tabs"):
            self._weld_tab_positions = [p * MM_TO_M for p in self.weld_tab_positions if p <= length]

        self.x_body_length = length


class PunchedCurrentCollector(_TabbedCurrentCollector):
    """
    Simple rectangular current collector with a single integrated tab.

    The punched current collector is the most common and straightforward
    collector design, featuring a rectangular body with a single tab
    extending from one edge. This design is widely used in
    prismatic and pouch cell formats due to its simplicity,
    manufacturing efficiency, and reliable electrical performance.

    Key characteristics:
    - Simple rectangular geometry with minimal complexity
    - Single tab for electrical connection
    - Configurable tab position along the width
    - Suitable for high-volume manufacturing
    - Compatible with standard coating and assembly processes

    This collector type is particularly well-suited for:
    - Z-fold electrode assemblies
    - Flat sheet cell constructions
    - Applications requiring simple, cost-effective designs
    - Automated manufacturing processes

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical and mechanical properties
        Common materials: aluminum foil (cathode), copper foil (anode)
    width : float
        Total width of the collector body in mm
        Typical range: 50-300 mm depending on cell capacity
    height : float
        Total height of the collector body in mm
        Typical range: 50-500 mm depending on cell format
    thickness : float
        Material thickness in micrometers (μm)
        Typical range: 6-20 μm (Al), 8-35 μm (Cu)
    tab_width : float
        Width of the protruding tab in mm
        Typical range: 10-50 mm based on current requirements
        Should be optimized for current density and welding requirements
    tab_height : float
        Extension height of the tab beyond the body in mm
        Typical range: 5-25 mm for manufacturing and assembly accessibility
    tab_position : float
        Horizontal position of the tab center from the left edge in mm
        Range: tab_width/2 to (width - tab_width/2)
        Central positioning (width/2) provides optimal current distribution
    coated_tab_height : float, optional
        Height of active material coating on the tab in mm (default: 0)
        Must be less than tab_height to provide bare connection area
        Set to 0 for completely uncoated tabs
    insulation_width : float, optional
        Width of insulation strip around the perimeter in mm (default: 0)
        Helps prevent short circuits and improves safety
    name : str, optional
        Descriptive name for identification
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Attributes
    ----------
    body_area : float
        Surface area of the rectangular body excluding tab (mm²)
    tab_area : float
        Surface area of the tab extension (mm²)
    total_area : float
        Combined surface area of body and tab (mm²)
    coated_area : float
        Area available for active material coating (mm²)
    current_density : float
        Current density through the tab connection (A/mm²)
    resistance : float
        Electrical resistance from body center to tab (Ω)

    Methods
    -------
    get_footprint()
        Returns the 2D outline coordinates of the collector
    get_a_side_view()
        Generates plotly figure of the collector from above
    get_properties()
        Returns dictionary of all geometric and electrical properties

    Examples
    --------
    Create a standard punched cathode current collector:

    >>> from steer_materials import aluminum_foil_12um
    >>> collector = PunchedCurrentCollector(
    ...     material=aluminum_foil_12um,
    ...     width=150.0,      # mm
    ...     height=200.0,     # mm
    ...     thickness=12.0,   # μm
    ...     tab_width=25.0,   # mm
    ...     tab_height=10.0,  # mm
    ...     tab_position=75.0 # mm (centered)
    ... )
    >>> print(f"Coated area: {collector.coated_area:.1f} mm²")
    >>> print(f"Tab current density at 10A: {10/collector.tab_area:.2f} A/mm²")

    Create an anode collector with coated tab:

    >>> from steer_materials import CurrentCollectorMaterial
    >>> anode_collector = PunchedCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Aluminum'),
    ...     width=152.0,      # Slightly larger than cathode
    ...     height=202.0,
    ...     thickness=10.0,
    ...     tab_width=20.0,
    ...     tab_height=12.0,
    ...     tab_position=74.0,
    ...     coated_tab_height=8.0  # Partial coating on tab
    ... )

    Visualize the collector geometry:

    >>> fig = collector.get_a_side_view()
    >>> fig.show()  # Interactive plotly visualization

    See Also
    --------
    NotchedCurrentCollector : Collector with cutout features for tape connections
    TablessCurrentCollector : Collector without protruding tabs
    TabWeldedCurrentCollector : Collector with separately welded tabs
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        width: float,
        height: float,
        thickness: float,
        tab_width: float,
        tab_height: float,
        tab_position: float,
        coated_tab_height: float = 0,
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Punched Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a punched current collector.

        Parameters
        ----------
        material: CurrentCollectorMaterial
            Material of the current collector.
        width: float
            Length of the current collector in mm.
        height: float
            Width of the current collector in mm.
        tab_width: float
            Width of the tab in mm.
        tab_height: float
            Height of the tab in mm.
        tab_position: float
            Position of the tab in mm, relative to the left edge of the current collector.
        coated_tab_height: float
            Height of the coated tab on the top side in mm, default is 0.
        thickness: float
            Thickness of the current collector in um.
        insulation_width: Optional[float]
            Width of the insulation in mm, default is 0.
        name: Optional[str]
            Name of the current collector, default is 'Punched Current Collector'.
        datum: Optional[Tuple[float, float, float]]
            Datum of the current collector in mm, default is (0, 0, 0).
        """
        super().__init__(
            material=material,
            x_body_length=width,
            y_body_length=height,
            tab_width=tab_width,
            tab_height=tab_height,
            coated_tab_height=coated_tab_height,
            thickness=thickness,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self.tab_position = tab_position
        self._calculate_all_properties()
        self._update_properties = True

    def _get_footprint(
        self,
        notch_height: float = None,
        y_depth: float = None,
        y_start: float = 0,
    ) -> np.ndarray:
        """
        Get the footprint of the current collector as a NumPy array of shape (N, 2).
        Each row is a (x, y) coordinate.
        """
        # Cache attribute access
        x_len = self._x_body_length
        y_len = self._y_body_length
        tab_pos = self._tab_position
        tab_width = self._tab_width
        datum_x, datum_y, _ = self._datum

        y_depth = y_len if y_depth is None else y_depth
        notch_height = self._tab_height if notch_height is None else notch_height

        start_x = datum_x - x_len / 2
        start_y = datum_y - y_len / 2 + y_start

        x_steps = np.array(
            [
                0,
                tab_pos - tab_width / 2,
                0,
                tab_width,
                0,
                x_len - tab_pos - tab_width / 2,
                0,
                -x_len,
            ]
        )

        y_steps = np.array([y_depth, 0, notch_height, 0, -notch_height, 0, -y_depth, 0])

        # Cumulative sum to get coordinates
        x_coords = np.cumsum(np.insert(x_steps, 0, start_x))
        y_coords = np.cumsum(np.insert(y_steps, 0, start_y))

        return x_coords, y_coords

    def _get_insulation_coordinates(self, side: str) -> np.ndarray:
        """
        Returns a NumPy array representing the insulation area.
        The shape depends on whether the insulation is entirely above, below,
        or straddling the body length. Output columns are ['x', 'y', 'z', 'side'].
        """
        if self._insulation_width == 0:
            return np.empty((0, 3))

        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_insulation_start = self._datum[1] + self._y_body_length / 2 + self._coated_tab_height - self._insulation_width
        _y_insulation_end = _y_insulation_start + self._insulation_width

        # Determine which case applies
        if _y_insulation_start > self._datum[1] + self._y_body_length / 2:
            x0 = self._datum[0] - self._x_body_length / 2 + self._tab_position - self._tab_width / 2
            y0 = _y_insulation_start

            x, y = self.build_square_array(x=x0, y=y0, x_width=self._tab_width, y_width=self._insulation_width)

        elif round(_y_insulation_end, 10) <= round(self._datum[1] + self._y_body_length / 2, 10):
            x0 = self._datum[0] - self._x_body_length / 2
            y0 = _y_insulation_start

            x, y = self.build_square_array(x=x0, y=y0, x_width=self._x_body_length, y_width=self._insulation_width)

        else:
            notch_height = _y_insulation_end - (self._datum[1] + self._y_body_length / 2)
            y_depth = (self._datum[1] + self._y_body_length / 2) - _y_insulation_start
            y_start = self._y_body_length + self._coated_tab_height - self._insulation_width

            x, y = self._get_footprint(notch_height=notch_height, y_depth=y_depth, y_start=y_start)

        # Get z-coordinate from body coordinates for this side
        idx = np.where(self._body_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No body coordinates found for side '{side}'")

        z_val = self._body_coordinates[idx[0], 2]

        # Create z and side columns
        z = np.full_like(x, z_val)

        # Stack into final (N, 4) array
        return np.column_stack((x, y, z))

    def get_top_down_view(self, **kwargs) -> go.Figure:
        return self._get_full_top_down_view(**kwargs)

    def rotate_90(self) -> None:
        """
        Rotate the current collector by 90 degrees in the clockwise direction.
        """
        # Keep datum as the center of rotation - don't move it to origin
        # Rotate coordinates around the current datum position
        self._body_coordinates = self.rotate_coordinates(self._body_coordinates, "z", -90, center=self._datum)
        self._a_side_coated_coordinates = self.rotate_coordinates(self._a_side_coated_coordinates, "z", -90, center=self._datum)
        self._b_side_coated_coordinates = self.rotate_coordinates(self._b_side_coated_coordinates, "z", -90, center=self._datum)

        if hasattr(self, "_a_side_insulation_coordinates"):
            self._a_side_insulation_coordinates = self.rotate_coordinates(self._a_side_insulation_coordinates, "z", -90, center=self._datum)
        if hasattr(self, "_b_side_insulation_coordinates"):
            self._b_side_insulation_coordinates = self.rotate_coordinates(self._b_side_insulation_coordinates, "z", -90, center=self._datum)

        if hasattr(self, "_weld_tabs"):
            for tab in self._weld_tabs:
                tab._body_coordinates = self.rotate_coordinates(tab._body_coordinates, "z", -90, center=self._datum)
                tab_datum_array = np.array([[tab._datum[0], tab._datum[1], tab._datum[2]]])
                rotated_datum = self.rotate_coordinates(tab_datum_array, "z", -90, center=self._datum)
                tab._datum = tuple(rotated_datum[0])

        return self

    @property
    def x_body_length_range(self) -> Tuple[float, float]:

        if hasattr(self, "_x_body_length_range") and self._x_body_length_range is not None:
            return (
                round(self._x_body_length_range[0] * M_TO_MM, 2),
                round(self._x_body_length_range[1] * M_TO_MM, 2),
            )

        else:
            return (10, 500)

    @property
    def y_body_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_body_length_range") and self._y_body_length_range is not None:
            return (
                round(self._y_body_length_range[0] * M_TO_MM, 2),
                round(self._y_body_length_range[1] * M_TO_MM, 2),
            )
        else:
            return (10, 500)

    @property
    def mass_range(self) -> Tuple[float, float]:
        min = 0
        hyp_max = 0.1
        max = hyp_max * (1 - np.exp(-0.5 / self._mass))

        return (round(min * KG_TO_G, 2), round(max * KG_TO_G, 2))

    @property
    def width(self) -> float:
        return self.x_body_length

    @property
    def width_range(self) -> Tuple[float, float]:
        return self.x_body_length_range

    @property
    def height(self) -> float:
        return self.y_body_length

    @property
    def height_range(self) -> Tuple[float, float]:
        return self.y_body_length_range

    @property
    def height_hard_range(self) -> Tuple[float, float]:
        return (0, 5000)

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        min = 0.01
        max = self._x_body_length - 0.01

        return (round(min * M_TO_MM, 2), round(max * M_TO_MM, 2))

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        return self.tab_width_hard_range

    @property
    def tab_position(self) -> float:
        return round(self._tab_position * M_TO_MM, 1)

    @tab_position.setter
    def tab_position(self, tab_position: float) -> None:
        self.validate_positive_float(tab_position, "tab_position")

        self._tab_position = float(tab_position) * MM_TO_M

        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")

        if self._tab_position + self._tab_width / 2 > self.x_body_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")

        if self._update_properties:
            self._calculate_coordinates()

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self.x_body_length = width

    @height.setter
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "height")
        self.y_body_length = height


class NotchedCurrentCollector(_TabbedCurrentCollector, _TapeCurrentCollector):
    """
    The notched current collector combines features from both tabbed and tape
    connection methods. It features multiple tabs along its length for improved
    current distribution and configurable bare regions for tape-style connections,
    offering excellent flexibility for various cell architectures and connection
    strategies.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical, thermal, and mechanical properties
        Selection impacts resistance, cost, and compatibility with active materials
    length : float
        Total length of the collector in the primary direction (mm)
        Determines the number of tabs that can be accommodated
    width : float
        Width of the collector perpendicular to the length (mm)
        Affects current path lengths and collector resistance
    thickness : float
        Material thickness in micrometers (μm)
        Impacts electrical resistance and mechanical stiffness
    tab_width : float
        Width of each individual tab (mm)
        Should be optimized for current density and manufacturing constraints
    tab_spacing : float
        Center-to-center distance between adjacent tabs (mm)
        Determines current distribution uniformity
    tab_height : float
        Extension height of tabs beyond the body (mm)
        Must provide adequate access for welding and connections
    coated_tab_height : float, optional
        Height of active material coating on each tab (mm, default: 0)
        Allows for energy density optimization while maintaining connections
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated lengths on a-side for tape connections (mm)
        Enables hybrid connection strategies
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated lengths on b-side for tape connections (mm)
        Provides flexibility for asymmetric designs
    insulation_width : float, optional
        Width of insulation strip around perimeter (mm, default: 0)
    name : str, optional
        Descriptive identifier for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Create a high-performance notched collector for an EV battery:

    >>> from steer_materials import copper_foil_12um
    >>> collector = NotchedCurrentCollector(
    ...     material=copper_foil_12um,
    ...     length=2500.0,        # mm - large format cell
    ...     width=180.0,         # mm
    ...     thickness=12.0,      # μm
    ...     tab_width=30.0,      # mm - wide tabs for high current
    ...     tab_spacing=50.0,    # mm - 5 tabs total
    ...     tab_height=15.0,     # mm
    ...     coated_tab_height=10.0,  # Partially coated tabs
    ...     bare_lengths_a_side=(15.0, 15.0),  # Tape connection option
    ...     bare_lengths_b_side=(10.0, 10.0)
    ... )
    >>> print(f"Number of tabs: {collector.number_of_tabs}")
    >>> print(f"Total tab area: {collector.total_tab_area:.1f} mm²")
    >>> print(f"Effective resistance: {collector.effective_resistance:.6f} Ω")

    >>> thermal_fig = collector.get_thermal_map()
    >>> thermal_fig.show()

    Compare connection strategies:

    >>> print("Available connections:", collector.connection_flexibility.keys())
    >>> # Output: ['tab_welding', 'tape_welding_a', 'tape_welding_b', 'hybrid']

    See Also
    --------
    PunchedCurrentCollector : Simple single-tab design
    TablessCurrentCollector : Tape-only connection without tabs
    TabWeldedCurrentCollector : Separate welded tab approach
    _TabbedCurrentCollector : Base class for tab functionality
    _TapeCurrentCollector : Base class for tape functionality
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        thickness: float,
        tab_width: float,
        tab_spacing: float,
        tab_height: float,
        coated_tab_height: float = 0,
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Notched Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a notched current collector.

        Parameters
        ----------
        material : CurrentCollectorMaterial
            Material of the current collector.
        length : float
            Length of the current collector in mm.
        width : float
            Width of the current collector in mm.
        thickness : float
            Thickness of the current collector in µm.
        tab_width : float
            Width of the tabs in mm.
        tab_spacing : float
            Spacing between the tabs in mm.
        tab_height : float
            Height of the tabs in mm.
        coated_tab_height : float
            Height of the coated tab on the top side in mm.
        bare_lengths_a_side : Tuple[float, float]
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side : Tuple[float, float]
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        insulation_width : Optional[float], default=0
            Width of the insulation strip in mm.
        name : Optional[str], default='Notched Current Collector'
            Name of the current collector.
        datum : Optional[Tuple[float, float, float]], default=(0, 0, 0)
            Datum of the current collector in mm.
        """
        super().__init__(
            material=material,
            x_body_length=length,
            y_body_length=width,
            tab_width=tab_width,
            tab_height=tab_height,
            thickness=thickness,
            coated_tab_height=coated_tab_height,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self.tab_spacing = tab_spacing
        self._calculate_all_properties()
        self._update_properties = True

    @classmethod
    def from_tabless(cls, tabless: "TablessCurrentCollector") -> "NotchedCurrentCollector":
        """
        Create a NotchedCurrentCollector from a TablessCurrentCollector.
        """
        new_current_collector = cls(
            material=tabless.material,
            length=tabless.x_body_length,
            width=tabless.y_body_length,
            thickness=tabless.thickness,
            tab_width=50,
            tab_spacing=100,
            tab_height=tabless.tab_height,
            coated_tab_height=0,
            bare_lengths_a_side=tabless.bare_lengths_a_side,
            bare_lengths_b_side=tabless.bare_lengths_b_side,
            insulation_width=tabless.insulation_width,
            datum=tabless.datum,
        )

        # perform actions if needed
        if tabless._flipped_x:
            new_current_collector._flip("x")
        if tabless._flipped_y:
            new_current_collector._flip("y")
        if tabless._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @classmethod
    def from_tab_welded(cls, tab_welded: "TabWeldedCurrentCollector") -> "NotchedCurrentCollector":
        """
        Create a NotchedCurrentCollector from a TabWeldedCurrentCollector.
        """
        new_current_collector = cls(
            material=tab_welded.material,
            length=tab_welded.x_body_length,
            width=tab_welded.y_body_length - 10,
            thickness=tab_welded.thickness,
            tab_width=50,
            tab_spacing=100,
            tab_height=10,
            coated_tab_height=0,
            bare_lengths_a_side=tab_welded.bare_lengths_a_side,
            bare_lengths_b_side=tab_welded.bare_lengths_b_side,
            insulation_width=0,
            datum=tab_welded.datum,
        )

        # perform actions if needed
        if tab_welded._flipped_x:
            new_current_collector._flip("x")
        if tab_welded._flipped_y:
            new_current_collector._flip("y")
        if tab_welded._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    def _calculate_tab_positions(self) -> None:
        """
        Function to calculate the positions of the tabs along the length of the current collector.
        """
        x_min = self._datum[0] - self._x_body_length / 2
        x_max = self._datum[0] + self._x_body_length / 2 + self._tab_spacing

        number_of_tabs = 1
        tab_positions = [x_min + self._tab_spacing / 2]
        tab_starts = [tab_positions[0] - self._tab_width / 2]
        tab_ends = [tab_positions[0] + self._tab_width / 2]

        while tab_positions[-1] < x_max:
            number_of_tabs += 1
            next_tab_position = tab_positions[-1] + self._tab_spacing

            if next_tab_position + self._tab_width / 2 > x_max:
                break

            tab_positions.append(next_tab_position)
            tab_starts.append(next_tab_position - self._tab_width / 2)
            tab_ends.append(next_tab_position + self._tab_width / 2)

        if tab_starts[-1] > self._datum[0] + self._x_body_length / 2:
            tab_starts = tab_starts[:-1]
            tab_ends = tab_ends[:-1]

        if tab_ends[-1] > self._datum[0] + self._x_body_length / 2:
            tab_ends[-1] = self._datum[0] + self._x_body_length / 2

        self._tab_positions = np.column_stack((tab_starts, tab_ends))

    def _calculate_coordinates(self):
        self._calculate_tab_positions()
        super()._calculate_coordinates()

    def _get_footprint(
        self,
        notch_height: Optional[float] = None,
        bare_lengths: Tuple[float, float] = (0, 0),
        y_depth: Optional[float] = None,
        y_start: Optional[float] = None,
        x_start: Optional[float] = None,
        x_end: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return a closed polyline (DataFrame of x/y) for the notched collector.
        All internal units in meters; bare_lengths come in mm.
        Optional x_start and x_end can restrict the x-bounds of the shape.
        """
        # Default values
        y_depth = self._y_body_length if y_depth is None else y_depth
        y_start = self._datum[1] - self._y_body_length / 2 if y_start is None else y_start
        notch = self._tab_height if notch_height is None else notch_height

        # Convert bare lengths to meters (they come in mm according to docstring)
        bare_left = bare_lengths[0] * MM_TO_M if bare_lengths[0] != 0 else 0
        bare_right = bare_lengths[1] * MM_TO_M if bare_lengths[1] != 0 else 0

        # X bounds
        default_x0 = self._datum[0] - self._x_body_length / 2 + bare_left
        default_x1 = self._datum[0] + self._x_body_length / 2 - bare_right
        x0 = default_x0 if x_start is None else x_start
        x1 = default_x1 if x_end is None else x_end

        y0 = y_start
        y1 = y_start + y_depth

        pts = []

        # Start at bottom-left
        pts.append((x0, y0))
        # Go up to top edge
        pts.append((x0, y1))

        # Get valid tab positions within the x-range and sort them
        valid_tabs = []
        for ts, te in self._tab_positions:
            # Check if tab overlaps with our x-range
            if te > x0 and ts < x1:
                # Clip tab to our x-range
                s = max(ts, x0)
                e = min(te, x1)
                if e > s:  # Valid tab after clipping
                    valid_tabs.append((s, e))

        # Sort tabs by start position
        valid_tabs.sort(key=lambda tab: tab[0])

        # Process each valid tab
        current_x = x0

        for tab_start, tab_end in valid_tabs:
            # Horizontal run to start of notch (if needed)
            if current_x < tab_start:
                if pts[-1] != (current_x, y1):
                    pts.append((current_x, y1))
                pts.append((tab_start, y1))

            # Draw the notch
            pts.append((tab_start, y1 + notch))
            pts.append((tab_end, y1 + notch))
            pts.append((tab_end, y1))

            # Update current position
            current_x = tab_end

        # Finish the top edge to x1
        if current_x < x1:
            if pts[-1] != (current_x, y1):
                pts.append((current_x, y1))
            pts.append((x1, y1))

        # Close the shape
        pts.append((x1, y0))
        pts.append((x0, y0))

        # Convert to numpy arrays
        x = np.array([p[0] for p in pts], dtype=float)
        y = np.array([p[1] for p in pts], dtype=float)

        return x, y

    def _get_insulation_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Return insulation coordinates for a given side ('a' or 'b') as numpy array.
        Handles three cases: (1) above body, (2) below body, (3) straddling edge.
        """
        if self._insulation_width == 0:
            return np.empty((0, 3))

        # Compute insulation Y-range
        y_body_top = self._datum[1] + self._y_body_length / 2
        y_ins_start = y_body_top + self._coated_tab_height - self._insulation_width
        y_ins_end = y_ins_start + self._insulation_width

        # Compute x bounds of coated region
        bare_left, bare_right = self._bare_lengths_a_side if side == "a" else self._bare_lengths_b_side
        x_start = self._datum[0] - self._x_body_length / 2 + bare_left
        x_end = self._datum[0] + self._x_body_length / 2 - bare_right

        # Case 1: Insulation entirely above the body
        if round(y_ins_start, 5) >= round(y_body_top, 5):
            all_x = []
            all_y = []

            for idx, (ts, te) in enumerate(self._tab_positions):
                ts = float(ts)
                te = float(te)

                # Clip tab to coated region
                if te < x_start or ts > x_end:
                    continue

                s = max(ts, x_start)
                e = min(te, x_end)

                # Get coordinates for this tab's insulation rectangle
                tab_x, tab_y = self.build_square_array(x_width=e - s, y_width=self._insulation_width, x=s, y=y_ins_start)

                # Add to lists
                all_x.extend(tab_x)
                all_y.extend(tab_y)

                # Add None values to break the fill for multiple rectangles
                if idx < len(self._tab_positions) - 1:  # Don't add break after last tab
                    all_x.append(None)
                    all_y.append(None)

            x = np.array(all_x)
            y = np.array(all_y)

        # Case 2: Insulation entirely below the body
        elif round(y_ins_end, 10) <= round(y_body_top, 10):
            x, y = self.build_square_array(
                x_width=x_end - x_start,
                y_width=self._insulation_width,
                x=x_start,
                y=y_ins_start,
            )

        # Case 3: Insulation straddles the top of the body
        else:
            notch = y_ins_end - y_body_top
            depth = y_body_top - y_ins_start
            x, y = self._get_footprint(
                notch_height=notch,
                y_depth=depth,
                y_start=y_ins_start,
                x_start=x_start,
                x_end=x_end,
            )

        # Get z-coordinate from body coordinates for this side
        idx = np.where(self._body_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No body coordinates found for side '{side}'")

        z_val = self._body_coordinates[idx[0], 2]

        # Create z array with proper numeric dtype
        z = np.full_like(x, z_val, dtype=float)
        
        # Handle None values by converting to NaN for numeric arrays
        none_mask = np.array([val is None for val in x])
        if np.any(none_mask):
            z[none_mask] = np.nan

        # Stack into final (N, 3) array
        return np.column_stack((x, y, z))

    @property
    def tab_positions(self) -> list:
        return [(round(start * M_TO_MM, 4), round(end * M_TO_MM, 4)) for start, end in self._tab_positions]

    @property
    def tab_spacing(self) -> float:
        return round(self._tab_spacing * M_TO_MM, 2)

    @property
    def tab_spacing_range(self) -> Tuple[float, float]:
        """
        Get the tab spacing range in mm.
        """
        return (round(self.tab_width + 0.1, 2), 1000)

    @property
    def tab_spacing_hard_range(self) -> Tuple[float, float]:
        return self.tab_spacing_range

    @property
    def tab_gap(self) -> float:
        return round(self._tab_gap * M_TO_MM, 2)

    @property
    def tab_gap_range(self) -> Tuple[float, float]:
        """
        Get the tab gap range in mm.
        """
        return (
            0.1,  # Minimum gap
            1000 - self.tab_width,  # Maximum gap (based on max spacing minus tab width)
        )

    @property
    def tab_gap_hard_range(self) -> Tuple[float, float]:
        return self.tab_gap_range

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        min = 0.01
        max = 0.5

        return (round(min * M_TO_MM, 2), round(max * M_TO_MM, 2))

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        return self.tab_width_hard_range

    @tab_spacing.setter
    @calculate_all_properties
    def tab_spacing(self, tab_spacing: float) -> None:
        self.validate_positive_float(tab_spacing, "tab_spacing")

        self._tab_spacing = float(tab_spacing) * MM_TO_M
        self._tab_gap = self._tab_spacing - self._tab_width

        if self._tab_gap < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")

    @tab_gap.setter
    @calculate_all_properties
    def tab_gap(self, tab_gap: float) -> None:
        """
        Set the tab gap by adjusting the tab spacing.

        Parameters
        ----------
        tab_gap : float
            The gap between tabs in mm.
        """
        self.validate_positive_float(tab_gap, "tab_gap")

        # Convert to internal units (meters)
        tab_gap_m = float(tab_gap) * MM_TO_M

        # Calculate new tab spacing: gap + tab width
        new_tab_spacing = tab_gap_m + self._tab_width

        # Update internal values
        self._tab_gap = tab_gap_m
        self._tab_spacing = new_tab_spacing


class TablessCurrentCollector(NotchedCurrentCollector):
    """
    Streamlined current collector without protruding tabs.

    The tabless current collector represents the most space-efficient design,
    eliminating protruding tabs entirely in favor of edge-based connections.
    This design is particularly advantageous for cylindrical cells, flatwound
    configurations, and applications where minimizing cell volume and complexity
    are paramount.

    Key advantages of the tabless design:
    - Simplified manufacturing with fewer cutting/forming operations
    - Reduced risk of tab damage during handling and assembly
    - Better suitability for automated winding and stacking processes
    - Lower material waste during production
    - Enhanced mechanical robustness

    This design is especially well-suited for:
    - Cylindrical cells (18650, 21700, 4680 formats)
    - Flatwound rectangular cells
    - High-volume consumer applications
    - Cells requiring consistent cylindrical geometry
    - Applications where tab damage is a reliability concern

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition for electrical and mechanical properties
        Typically aluminum for cathodes, copper for anodes
    length : float
        Total length of the collector in the primary direction (mm)
        For cylindrical cells, this determines the winding length
    width : float
        Total width of the collector (mm)
        For cylindrical cells, this affects the electrode height
    coated_width : float
        Width of the region available for active material coating (mm)
        Must be less than total width to provide bare connection strips
    thickness : float
        Material thickness in micrometers (μm)
        Affects cell internal resistance and energy density
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated lengths on a-side for connections (mm)
        Provides flexibility for different cell termination strategies
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated lengths on b-side for connections (mm)
        Enables asymmetric designs for specific applications
    insulation_width : float, optional
        Width of insulation strip around edges (mm, default: 0)
        Critical for preventing short circuits in tabless designs
    name : str, optional
        Descriptive identifier for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Design a tabless collector for a 21700 cylindrical cell:

    >>> from steer_materials import CurrentCollectorMaterial
    >>> collector = TablessCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Aluminum'),
    ...     length=650.0,        # mm - enough for multiple winds
    ...     width=65.0,          # mm - fits 21700 height
    ...     coated_width=60.0,   # mm - 2.5mm bare strips on edges
    ...     thickness=15.0,      # μm
    ...     bare_lengths_a_side=(10.0, 10.0),  # mm
    ...     bare_lengths_b_side=(10.0, 10.0),  # mm
    ...     insulation_width=0.5 # mm - prevent shorts
    ... )
    >>> print(f"Coated fraction: {collector.coated_fraction:.2%}")
    >>> print(f"Connection strip width: {collector.connection_strip_width:.1f} mm")

    See Also
    --------
    PunchedCurrentCollector : Simple tabbed alternative
    NotchedCurrentCollector : Multi-tab design with more connection points
    TabWeldedCurrentCollector : Separate welded tab approach
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        coated_width: float,
        thickness: float,
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Tabless Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a tabless current collector.

        Parameters
        ----------
        material: CurrentCollectorMaterial:
            Material of the current collector.
        length: float:
            Length of the current collector in mm.
        width: float:
            Width of the current collector in mm.
        coated_width: float:
            Width of the coated area in mm.
        thickness: float:
            Thickness of the current collector in um.
        bare_lengths_a_side: Tuple[float, float]:
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side: Tuple[float, float]:
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        insulation_width: Optional[float]:
            Width of the insulation strip in mm, default is 0.
        name: Optional[str]:
            Name of the current collector, default is 'Tabless Current Collector'.
        """
        tab_height = width - coated_width
        width = width - tab_height

        super().__init__(
            material=material,
            length=length,
            width=width,
            thickness=thickness,
            tab_height=tab_height,
            tab_width=length,
            tab_spacing=length,
            coated_tab_height=0,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self._update_properties = False
        self.coated_width = coated_width
        self._update_properties = True

    @classmethod
    def from_notched(cls, notched: "NotchedCurrentCollector") -> "TablessCurrentCollector":
        """
        Create a TablessCurrentCollector from a NotchedCurrentCollector.
        """
        new_current_collector = cls(
            material=notched.material,
            length=notched.x_body_length,
            width=notched.y_body_length + notched.tab_height,
            coated_width=notched.y_body_length,
            thickness=notched.thickness,
            bare_lengths_a_side=notched.bare_lengths_a_side,
            bare_lengths_b_side=notched.bare_lengths_b_side,
            insulation_width=notched.insulation_width,
            datum=notched.datum,
        )

        # perform actions if needed
        if notched._flipped_x:
            new_current_collector._flip("x")
        if notched._flipped_y:
            new_current_collector._flip("y")
        if notched._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @classmethod
    def from_tab_welded(cls, tab_welded: "TabWeldedCurrentCollector") -> "TablessCurrentCollector":
        """
        Create a TablessCurrentCollector from a TabWeldedCurrentCollector.
        """
        new_current_collector = cls(
            material=tab_welded.material,
            length=tab_welded.x_body_length,
            width=tab_welded.y_body_length,
            coated_width=tab_welded.y_body_length - 10,
            thickness=tab_welded.thickness,
            bare_lengths_a_side=tab_welded.bare_lengths_a_side,
            bare_lengths_b_side=tab_welded.bare_lengths_b_side,
            insulation_width=0,
            datum=tab_welded.datum,
        )

        # perform actions if needed
        if tab_welded._flipped_x:
            new_current_collector._flip("x")
        if tab_welded._flipped_y:
            new_current_collector._flip("y")
        if tab_welded._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @property
    def coated_width(self) -> float:
        return round(self._coated_width * M_TO_MM, 2)

    @property
    def coated_width_range(self) -> Tuple[float, float]:
        """
        Get the coated width range in mm.
        """
        if hasattr(self, "_y_body_length_range") and self._y_body_length_range is not None:
            min = self.y_body_length_range[0]
        else:
            min = self.width - self.tab_height_range[1]

        max = self.width - self.tab_height_range[0]

        return (min, max)

    @property
    def coated_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the coated width range in mm.
        """
        return (0, self.width)

    @property
    def tab_height_range(self) -> Tuple[float, float]:
        return (1, self.width * 1 / 4)

    @property
    def width(self) -> float:
        return round((self._y_body_length + self._tab_height) * M_TO_MM, 2)

    @property
    def width_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_body_length_range") and self._y_body_length_range is not None:
            min_width = self.y_body_length_range[0] + self.tab_height
            max_width = self.y_body_length_range[1] + self.tab_height
            return (round(min_width, 2), round(max_width, 2))
        else:
            return (0, 1000)

    @property
    def tab_height(self) -> float:
        return round(self._tab_height * M_TO_MM, 2)

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")

        new_y_length = width - self.tab_height
        self._coated_width = new_y_length * MM_TO_M
        self.y_body_length = new_y_length

        # Automatically adjust coated_width if it's now too large
        _max_coated_width = self._y_body_length

        if self._coated_width > _max_coated_width:
            self.coated_width = _max_coated_width * M_TO_MM

    @coated_width.setter
    @calculate_areas
    def coated_width(self, coated_width: float) -> None:
        self.validate_positive_float(coated_width, "coated_width")

        # Store the current total width
        current_total_width = self.width

        # Set the new coated width
        self._coated_width = float(coated_width) * MM_TO_M

        # Calculate new tab height to maintain total width
        new_tab_height = current_total_width - coated_width

        # Validate the new tab height is positive
        if new_tab_height < 0:
            raise ValueError(f"Coated width {coated_width} mm is too large. Maximum allowed is {current_total_width} mm.")

        # Update tab height and y_body_length
        self._tab_height = new_tab_height * MM_TO_M
        self._y_body_length = self._coated_width  # y_body_length equals coated_width

    @tab_height.setter
    @calculate_all_properties
    def tab_height(self, tab_height: float) -> None:
        self.validate_positive_float(tab_height, "tab_height")
        self._tab_height = float(tab_height) * MM_TO_M


class WeldTab(ValidationMixin, CoordinateMixin, DunderMixin, PlotterMixin):
    """
    Specification and modeling class for separately manufactured welded tabs.

    The WeldTab class represents individual tab components that are manufactured
    separately and subsequently welded to current collectors. This design approach
    enables independent optimization of tab materials, geometry, and properties
    while providing sophisticated control over electrical and mechanical
    performance characteristics.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material specification for the tab component
        Defines electrical, thermal, and mechanical properties
        Must be compatible with welding processes and base collector material
    width : float
        Tab width dimension in mm
        Affects current carrying capacity and mechanical strength
        Typical range: 10-100 mm depending on application requirements
    length : float
        Tab length dimension in mm
        Determines contact area and current distribution characteristics
        Typical range: 5-50 mm for most battery applications
    thickness : float
        Tab thickness in μm
        Critical for electrical resistance and mechanical robustness
        Typical range: 50-500 μm based on current requirements
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm
        Default: (0, 0, 0) - places tab at coordinate system origin

    Examples
    --------
    Create a high-performance copper tab for EV applications:

    >>> from steer_materials import CurrentCollectorMaterial
    >>>
    >>> # Design a robust tab for high current applications
    >>> heavy_duty_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=50.0,          # mm - wide for high current
    ...     length=25.0,         # mm - substantial contact area
    ...     thickness=200.0,     # μm - thick for low resistance
    ...     datum=(0, 0, 0)      # Centered reference
    ... )
    >>>
    >>> print(f"Tab resistance: {heavy_duty_tab.electrical_resistance:.6f} Ω")
    >>> print(f"Tab mass: {heavy_duty_tab.mass:.3f} g")
    >>> print(f"Current capacity: {heavy_duty_tab.current_density_limit * heavy_duty_tab.body_area/2:.1f} A")

    Create a compact tab for space-constrained applications:

    >>> # Design for minimal size while maintaining performance
    >>> compact_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=20.0,          # mm - compact width
    ...     length=15.0,         # mm - minimal length
    ...     thickness=150.0,     # μm - optimized thickness
    ...     datum=(10, 5, 0)     # Offset positioning
    ... )

    Visualize tab geometry and validate design:

    >>> # Generate visualization plots
    >>> top_view = heavy_duty_tab.get_view(
    ...     title="Heavy Duty Tab - Top View",
    ...     paper_bgcolor='lightgray'
    ... )
    >>> side_view = heavy_duty_tab.get_side_view(
    ...     title="Heavy Duty Tab - Side View"
    ... )
    >>>
    >>> # Validate welding compatibility
    >>> from steer_materials import aluminum_1235_foil
    >>> compatibility = heavy_duty_tab.validate_welding_compatibility(
    ...     aluminum_1235_foil
    ... )
    >>> if not compatibility['suitable']:
    ...     print("Warning: Material incompatibility detected")

    See Also
    --------
    TabWeldedCurrentCollector : Current collector using welded tabs
    CurrentCollectorMaterial : Material specification class
    PunchedCurrentCollector : Alternative integrated tab design
    NotchedCurrentCollector : Multiple integrated tab approach
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        width: float,
        length: float,
        thickness: float,
        datum: Tuple[float, float] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a weld tab used on current collectors

        :param material: CurrentCollectorMaterial: material of the weld tab
        :param width: float: width of the weld tab in mm
        :param length: float: length of the weld tab in mm
        :param thickness: float: thickness of the weld tab in um
        """
        self._update_properties = False

        self.datum = datum
        self.material = material
        self.width = width
        self.length = length
        self.thickness = thickness

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self) -> None:
        self._calculate_coordinates()
        self._calculate_areas()
        self._calculate_bulk_properties()

    def _calculate_bulk_properties(self) -> None:
        """
        Calculate the bulk properties of the tab.
        """
        self._volume = self._body_area * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost

    def _calculate_coordinates(self) -> None:
        """
        Calculate the coordinates of the weld tab based on its dimensions and datum.
        """
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._length / 2,
            self._width,
            self._length,
        )

        x, y, z, side = self.extrude_footprint(x, y, self._datum, self._thickness)

        self._body_coordinates = np.column_stack((x, y, z))
        self._body_coordinates_side = side

    def _calculate_areas(self) -> None:
        # calculate the area of the a side
        body_a_side_area = self.get_area_from_points(
            self._body_coordinates[self._body_coordinates_side == "a"][:, 0],
            self._body_coordinates[self._body_coordinates_side == "a"][:, 1],
        )

        # calculate the total upper and lower area of the body
        self._body_area = body_a_side_area * 2

    def _translate(self, vector: Tuple[float, float, float]) -> None:
        self._body_coordinates += np.array(vector)

    def get_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self.top_down_body_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    def get_side_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the side view of the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self.right_left_body_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def body_coordinates(self) -> pd.DataFrame:
        return pd.DataFrame(
            np.column_stack((self._body_coordinates, self._body_coordinates_side)),
            columns=["x", "y", "z", "side"],
        ).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
            side=lambda df: df["side"].astype(str),
        )

    @property
    def right_left_body_trace(self) -> go.Scatter:
        # get the coordinates of the body, ordered clockwise
        body_coordinates = self.order_coordinates_clockwise(self.body_coordinates, plane="yz")

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates["y"],
            y=body_coordinates["z"],
            mode="lines",
            name="Body",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )

        return body_trace

    @property
    def top_down_body_trace(self) -> go.Scatter:
        # get the side with the maximum z value
        body_coordinates = self.body_coordinates.query("z == z.max()")

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates["x"],
            y=body_coordinates["y"],
            mode="lines",
            name="Tab",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Tabs",
            showlegend=True,
        )

        return body_trace

    @property
    def datum(self) -> Tuple[float, float]:
        return (
            round(self._datum[0] * M_TO_MM, 2),
            round(self._datum[1] * M_TO_MM, 2),
            round(self._datum[2] * M_TO_MM, 2),
        )

    @property
    def material(self) -> CurrentCollectorMaterial:
        return self._material

    @property
    def width(self) -> float:
        return round(self._width * M_TO_MM, 2)

    @property
    def length(self) -> float:
        return round(self._length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @property
    def volume(self) -> float:
        return round(self._volume * M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def body_area(self) -> float:
        return round(self._body_area * M_TO_MM**2, 2)

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
    @calculate_all_properties
    def material(self, material: CurrentCollectorMaterial) -> None:
        self.validate_type(material, CurrentCollectorMaterial, "material")
        self._material = material

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self._width = float(width) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "thickness")
        self._thickness = float(thickness) * UM_TO_M

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        self.validate_positive_float(length, "length")
        self._length = float(length) * MM_TO_M


class TabWeldedCurrentCollector(_TapeCurrentCollector):
    """
    Current collector with separately manufactured and welded tabs.

    The tab-welded current collector represents a design approach
    where tabs are manufactured separately and then welded to the main collector
    body.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Base material for the current collector body
        Can be optimized independently from tab material
    length : float
        Total length of the collector body in mm
        Defines the available space for tab positioning
    width : float
        Width of the collector body in mm
        Affects current distribution and tab placement options
    thickness : float
        Thickness of the base collector material in μm
        May differ from tab thickness for optimized performance
    weld_tab : WeldTab
        Specification object defining tab geometry, material, and properties
        Encapsulates all tab-specific design parameters
    weld_tab_positions : Iterable[float]
        Array of tab center positions along the length in mm
        Enables precise, flexible tab placement for optimal current distribution
    skip_coat_width : float
        Width of uncoated area around each tab in mm
        Prevents coating interference with welding and ensures reliable connections
    tab_overhang : float
        Distance tabs extend beyond the collector body edge in mm
        Provides access for external connections and welding operations
    tab_weld_side : str, optional
        Side of collector for tab welding ('a' or 'b', default: 'a')
        Determines which surface receives the welded tabs
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated regions on a-side in mm
        Enables hybrid connection strategies combining tabs and tape methods
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated regions on b-side in mm
        Provides additional connection flexibility
    name : str, optional
        Descriptive identifier for the collector assembly
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Create a high-performance tab-welded collector for an EV application:

    >>> from steer_materials import CurrentCollectorMaterial
    >>>
    >>> # Define the weld tab specification
    >>> weld_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=40.0,          # mm - wide for high current
    ...     height=20.0,         # mm
    ...     thickness=100.0      # μm - thick for low resistance
    ... )
    >>>
    >>> # Create collector with optimally positioned tabs
    >>> collector = TabWeldedCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     length=300.0,        # mm
    ...     width=200.0,         # mm
    ...     thickness=15.0,      # μm
    ...     weld_tab=weld_tab,
    ...     weld_tab_positions=[75.0, 150.0, 225.0],  # 3 evenly spaced tabs
    ...     skip_coat_width=45.0,    # mm - larger than tab width
    ...     tab_overhang=18.0,       # mm - accessible for connections
    ...     tab_weld_side='a',
    ...     bare_lengths_a_side=(20.0, 20.0)  # Additional tape connection option
    ... )

    See Also
    --------
    PunchedCurrentCollector : Simpler integrated tab design
    NotchedCurrentCollector : Multiple integrated tabs
    TablessCurrentCollector : No-tab edge connection design
    WeldTab : Specification class for welded tab components
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        thickness: float,
        weld_tab: WeldTab,
        weld_tab_positions: Iterable[float],
        skip_coat_width: float,
        tab_overhang: float,
        tab_weld_side: str = "a",
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        name: Optional[str] = "Tab Welded Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a current collector with tabs welded on it.

        Parameters
        ----------
        material: CurrentCollectorMaterial:
            Material of the current collector.
        length: float:
            Length of the current collector in mm.
        width: float:
            Width of the current collector in mm.
        thickness: float:
            Thickness of the current collector in um.
        weld_tab: WeldTab:
            Weld tab to be used on the current collector.
        weld_tab_positions: Iterable[float]:
            Positions of the weld tabs along the length of the current collector in mm.
        skip_coat_width: float:
            Width of the skip coat area in mm.
        tab_overhang: float:
            Overhang of the weld tab in mm.
        tab_weld_side: str:
            Side of the current collector where the weld tabs are welded ('a' or 'b').
        bare_lengths_a_side: Tuple[float, float]:
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side: Tuple[float, float]:
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        name: Optional[str]:
            Name of the current collector, default is 'Tab Welded Current Collector'.
        datum: Optional[Tuple[float, float, float]]:
            Datum of the current collector in mm, default is (0, 0, 0).
        """
        super().__init__(
            material=material,
            x_body_length=length,
            y_body_length=width,
            thickness=thickness,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            name=name,
            datum=datum,
        )

        self.weld_tab = weld_tab
        self.tab_overhang = tab_overhang
        self.weld_tab_positions = weld_tab_positions
        self.skip_coat_width = skip_coat_width
        self.tab_weld_side = tab_weld_side

        self._calculate_all_properties()
        self._update_properties = True

    @classmethod
    def from_notched(cls, notched: "NotchedCurrentCollector") -> "TabWeldedCurrentCollector":
        """
        Create a TabWeldedCurrentCollector from a NotchedCurrentCollector.
        """
        tab = WeldTab(
            material=notched.material,
            width=10,
            length=notched.y_body_length + notched.tab_height,
            thickness=notched.thickness,
        )

        new_current_collector = cls(
            material=notched.material,
            length=notched.x_body_length,
            width=notched.y_body_length + notched.tab_height,
            thickness=notched.thickness,
            weld_tab=tab,
            weld_tab_positions=[
                10,
                notched.x_body_length / 2,
                notched.x_body_length - 10,
            ],
            tab_overhang=20,
            skip_coat_width=30,
            tab_weld_side="a",
            bare_lengths_a_side=notched.bare_lengths_a_side,
            bare_lengths_b_side=notched.bare_lengths_b_side,
            datum=notched.datum,
        )

        # perform actions if needed
        if notched._flipped_x:
            new_current_collector._flip("x")
        if notched._flipped_y:
            new_current_collector._flip("y")
        if notched._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @classmethod
    def from_tabless(cls, tabless: "TablessCurrentCollector") -> "TabWeldedCurrentCollector":
        """
        Create a TabWeldedCurrentCollector from a TablessCurrentCollector.
        """
        tab = WeldTab(
            material=tabless.material,
            width=10,
            length=tabless.y_body_length + tabless.tab_height,
            thickness=tabless.thickness,
        )

        new_current_collector = cls(
            material=tabless.material,
            length=tabless.x_body_length,
            width=tabless.y_body_length + tabless.tab_height,
            thickness=tabless.thickness,
            weld_tab=tab,
            weld_tab_positions=[
                10,
                tabless.x_body_length / 2,
                tabless.x_body_length - 10,
            ],
            tab_overhang=20,
            skip_coat_width=30,
            tab_weld_side="a",
            bare_lengths_a_side=tabless.bare_lengths_a_side,
            bare_lengths_b_side=tabless.bare_lengths_b_side,
            datum=tabless.datum,
        )

        # perform actions if needed
        if tabless._flipped_x:
            new_current_collector._flip("x")
        if tabless._flipped_y:
            new_current_collector._flip("y")
        if tabless._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    def _calculate_all_properties(self) -> None:
        self._calculate_weld_tab_properties()
        super()._calculate_all_properties()

    def _calculate_bulk_properties(self) -> None:
        self._volume = self._body_area / 2 * self._thickness + sum([t._volume for t in self._weld_tabs])
        self._mass = self._volume * self._material._density + sum([t._mass for t in self._weld_tabs])
        self._cost = self._mass * self._material._specific_cost + sum([t._cost for t in self._weld_tabs])

    def _calculate_weld_tab_properties(self) -> None:
        # copy the weld tabs and set their datums
        self._weld_tabs = []
        for x in self._weld_tab_positions:
            new_weld_tab = deepcopy(self._weld_tab)
            x_datum = (self._datum[0] - self._x_body_length / 2 + x) * M_TO_MM
            y_datum = (self._datum[1] + self._y_body_length / 2 + self._tab_overhang - new_weld_tab._length / 2) * M_TO_MM

            if self._tab_weld_side == "a":
                z_datum = (self._datum[2] + self._thickness * UM_TO_MM / 2 + new_weld_tab._thickness * UM_TO_MM / 2) * M_TO_MM
            elif self._tab_weld_side == "b":
                z_datum = (self._datum[2] - self._thickness * UM_TO_MM / 2 - new_weld_tab._thickness * UM_TO_MM / 2) * M_TO_MM

            new_weld_tab.datum = (x_datum, y_datum, z_datum)
            self._weld_tabs.append(new_weld_tab)

    def _get_full_view(self, side="a", aspect_ratio: float = 3, **kwargs) -> go.Figure:
        # Get the base figure from the parent class
        figure = super()._get_full_view(side=side, aspect_ratio=aspect_ratio, **kwargs)

        # Add the weld‐tab traces but group them under one legend entry
        for i, tab in enumerate(self._weld_tabs):
            tr = tab._trace
            tr.legendgroup = "Weld Tabs"
            tr.name = "Weld Tabs"
            tr.showlegend = True if i == 0 else False
            figure.add_trace(tr)

        if side != self._tab_weld_side:
            n = len(self._weld_tabs)
            traces = list(figure.data)
            figure.data = traces[n:] + traces[:n]

        return figure

    def _get_footprint(self, x_indent_start: float = 0, x_indent_end: float = 0) -> Tuple[np.ndarray, np.ndarray]:
        return self.build_square_array(
            x_width=self._x_body_length - x_indent_start - x_indent_end,
            y_width=self._y_body_length,
            x=self._datum[0] - self._x_body_length / 2 + x_indent_start,
            y=self._datum[1] - self._y_body_length / 2,
        )

    def _get_coated_area_coordinates(self, side: str = "a") -> Tuple[go.Scatter, float]:
        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        x_indent_start = self._bare_lengths_a_side[0] if side == "a" else self._bare_lengths_b_side[0]
        x_indent_end = self._bare_lengths_a_side[1] if side == "a" else self._bare_lengths_b_side[1]
        x, y = self._get_footprint(x_indent_start=x_indent_start, x_indent_end=x_indent_end)

        weld_tab_positions = np.array([t._datum[0] for t in self._weld_tabs])

        x, y = self.remove_skip_coat_area(x, y, weld_tab_positions, self._skip_coat_width)

        # Get the indices of the body coordinates for the specified side
        idx = np.where(self._body_coordinates_side == side)[0]

        # get the z value from the body coordinates for this side
        z_value = self._body_coordinates[idx[0], 2]

        # Create z array
        z = np.full_like(x, z_value)

        # Combine into (N, 3) array
        coated_area = np.column_stack((x, y, z))

        return coated_area

    def _get_a_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side="a")

    def _get_b_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side="b")

    def _get_insulation_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Return empty insulation coordinates for TabWeldedCurrentCollector.

        TabWeldedCurrentCollectors don't have traditional insulation areas
        since they use welded tabs instead.

        Parameters
        ----------
        side : str
            Side of the current collector ('a' or 'b')

        Returns
        -------
        np.ndarray
            Empty array with shape (0, 3) representing no insulation coordinates
        """
        return np.empty((0, 3))

    def _get_a_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()

    def _get_b_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()

    @property
    def weld_tab_positions(self) -> list:
        """
        Returns the positions of the weld tabs along the length of the current collector in mm.
        """
        return [round(pos * M_TO_MM, 2) for pos in self._weld_tab_positions]

    @property
    def skip_coat_width(self) -> float:
        """
        Returns the width of the skip coat area in mm.
        """
        return round(self._skip_coat_width * M_TO_MM, 2)

    @property
    def skip_coat_width_range(self) -> Tuple[float, float]:
        """
        Get the skip coat width range in mm.
        """
        return (self._weld_tabs[0].width, 100)

    @property
    def skip_coat_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the skip coat width range in mm.
        """
        return (self._weld_tabs[0].width, 1000)

    @property
    def tab_weld_side(self) -> str:
        """
        Returns the side of the current collector where the weld tabs are located ('a' or 'b').
        """
        return self._tab_weld_side

    @property
    def tab_overhang(self) -> float:
        """
        Returns the overhang of the weld tab on the current collector in mm.
        """
        return round(self._tab_overhang * M_TO_MM, 2)

    @property
    def tab_overhang_range(self) -> Tuple[float, float]:
        """
        Returns the overhang range of the weld tab in mm.
        """
        return (0, self.weld_tab.length / 2)

    @property
    def tab_overhang_hard_range(self) -> Tuple[float, float]:
        return (0, self.weld_tab.length)

    @property
    def weld_tab(self) -> list:
        """
        Returns a list of WeldTab objects representing the weld tabs on the current collector.
        """
        return self._weld_tab

    @property
    def weld_tabs(self) -> list:
        """
        Returns a list of WeldTab objects representing the weld tabs on the current collector.
        """
        return self._weld_tabs

    @property
    def tab_width(self) -> float:
        """
        Returns the width of the weld tab in mm.
        """
        return self.weld_tab.width

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        """
        Returns the width range of the weld tab in mm.
        """
        return (1, self.skip_coat_width)

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        return self.tab_width_range

    @property
    def tab_length(self) -> float:
        """
        Returns the length of the weld tab in mm.
        """
        return self.weld_tab.length

    @property
    def tab_length_range(self) -> Tuple[float, float]:
        """
        Returns the length range of the weld tab in mm.
        """
        return (self.tab_overhang, self.y_body_length + self.tab_overhang)

    @property
    def tab_length_hard_range(self) -> Tuple[float, float]:
        return self.tab_length_range

    @property
    def tab_positions_text(self) -> str:
        """
        Returns the weld tab positions as a formatted string in mm.

        Returns
        -------
        str
            Comma-separated string of tab positions (e.g., "75.0, 150.0, 225.0")
        """
        positions = [str(round(pos * M_TO_MM, 2)) for pos in self._weld_tab_positions]
        return ", ".join(positions)

    @tab_positions_text.setter
    def tab_positions_text(self, positions_text: str) -> None:
        """
        Set weld tab positions from a formatted string.

        Parameters
        ----------
        positions_text : str
            Comma-separated string of tab positions in mm
            Examples: "75.0, 150.0, 225.0" or "10,50,100" or "25.5, 75.25, 125"

        Raises
        ------
        ValueError
            If the string cannot be parsed into valid numbers
        """
        try:
            # Split by comma and strip whitespace
            position_strings = [s.strip() for s in positions_text.split(",")]

            # Filter out empty strings
            position_strings = [s for s in position_strings if s]

            if not position_strings:
                raise ValueError("No valid positions found in the input string")

            # Convert to float list
            positions_list = [float(pos) for pos in position_strings]

            # Use the existing setter for validation and conversion
            self.weld_tab_positions = positions_list

        except ValueError as e:
            if "could not convert string to float" in str(e):
                raise ValueError(f"Invalid number format in tab positions: '{positions_text}'. Use comma-separated numbers like '75.0, 150.0, 225.0'")
            else:
                raise  # Re-raise other ValueError from weld_tab_positions setter

    @tab_overhang.setter
    @calculate_weld_tab_properties
    def tab_overhang(self, tab_overhang: float) -> None:
        """
        Set the overhang of the weld tab on the current collector.

        Parameters
        ----------
        tab_overhang : float
            The overhang of the weld tab in mm.
        """
        self.validate_positive_float(tab_overhang, "tab_overhang")

        # Convert to internal units (meters)
        self._tab_overhang = float(tab_overhang) * MM_TO_M

        if self._tab_overhang > self.weld_tab.length / 2:
            raise ValueError("Tab overhang cannot be greater than half the length of the weld tab.")

    @tab_width.setter
    @calculate_all_properties
    def tab_width(self, tab_width: float) -> None:
        self.validate_positive_float(tab_width, "tab_width")
        self.weld_tab.width = tab_width

    @tab_length.setter
    @calculate_all_properties
    def tab_length(self, tab_length: float) -> None:
        self.validate_positive_float(tab_length, "tab_length")

        if tab_length < self.tab_overhang:
            raise ValueError("Tab length cannot be less than the tab overhang.")

        self.weld_tab.length = tab_length

    @weld_tab.setter
    @calculate_all_properties
    def weld_tab(self, weld_tab: WeldTab) -> None:
        self.validate_type(weld_tab, WeldTab, "weld_tab")
        self._weld_tab = weld_tab

    @weld_tab_positions.setter
    @calculate_all_properties
    def weld_tab_positions(self, weld_tab_positions: Iterable[float]) -> None:

        print(weld_tab_positions)

        self.validate_type(weld_tab_positions, Iterable, "weld_tab_positions")

        if any(pos > self.x_body_length for pos in weld_tab_positions):
            raise ValueError("Weld tab positions cannot be greater than the length of the current collector.")

        self._weld_tab_positions = [float(pos) * MM_TO_M for pos in sorted(weld_tab_positions)]

    @tab_overhang.setter
    @calculate_weld_tab_properties
    def tab_overhang(self, tab_overhang: float) -> None:
        self.validate_positive_float(tab_overhang, "tab_overhang")
        self._tab_overhang = float(tab_overhang) * MM_TO_M

    @skip_coat_width.setter
    @calculate_areas
    def skip_coat_width(self, skip_coat_width: float) -> None:
        self.validate_positive_float(skip_coat_width, "skip_coat_width")

        if skip_coat_width < self._weld_tab._width / 2:
            self._skip_coat_width = self._weld_tab._width
        else:
            self._skip_coat_width = float(skip_coat_width) * MM_TO_M

        if self._skip_coat_width > self._x_body_length:
            raise ValueError("Skip coat width cannot be greater than the length of the current collector.")

    @tab_weld_side.setter
    @calculate_weld_tab_properties
    def tab_weld_side(self, tab_weld_side: str) -> None:
        if tab_weld_side not in ["a", "b"]:
            raise ValueError("Tab weld side must be either 'a' or 'b'.")

        self._tab_weld_side = tab_weld_side

