from copy import deepcopy
from steer_opencell_design.Components.Containers.Base import _Container
from steer_opencell_design.Materials.Other import PrismaticContainerMaterial
from steer_core.Constants.Units import *
from steer_core.Decorators.General import calculate_bulk_properties, calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Tuple, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from steer_core import (
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
)


# Module-level constants for prismatic components
DEFAULT_FILL_FACTOR = 0.7
DEFAULT_ROTATION_DEGREES = 90

# Dimension ranges (in mm)
WIDTH_RANGE_MIN = 10.0
WIDTH_RANGE_MAX = 600.0
WIDTH_HARD_MIN = 5.0
WIDTH_HARD_MAX = 800.0

LENGTH_RANGE_MIN = 10.0
LENGTH_RANGE_MAX = 600.0
LENGTH_HARD_MIN = 5.0
LENGTH_HARD_MAX = 800.0

THICKNESS_RANGE_MIN = 0.1
THICKNESS_RANGE_MAX = 5.0
THICKNESS_HARD_MIN = 0.05
THICKNESS_HARD_MAX = 10.0

HEIGHT_RANGE_MIN = 10.0
HEIGHT_RANGE_MAX = 600.0
HEIGHT_HARD_MIN = 5.0
HEIGHT_HARD_MAX = 500.0

INTERNAL_HEIGHT_RANGE_MIN = 5.0
INTERNAL_HEIGHT_RANGE_MAX = 250.0

WALL_THICKNESS_RANGE_MIN = 0.1
WALL_THICKNESS_RANGE_MAX = 3.0

FILL_FACTOR_MIN = 0.0
FILL_FACTOR_MAX = 1.0

# Plotting constants
PLOT_LINE_WIDTH = 0.5
PLOT_LINE_COLOR = "black"

# Precision constants
COORDINATE_PRECISION = 10
DIMENSION_PRECISION = 2


class ConnectorOrientation(Enum):
    """Orientation options for electrode layups."""
    TRANSVERSE = "transverse"
    LONGITUDINAL = "longitudinal"


class _PrismaticComponent(
    ABC,
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
):
    """Base class for prismatic components with common functionality.
    
    This abstract base class provides shared functionality for prismatic
    (rectangular) components including bulk property calculations, coordinate 
    management, plotting capabilities, and property handling. Subclasses need 
    only implement the `_calculate_footprint` method to define their specific geometry.
    
    Attributes
    ----------
    material : PrismaticContainerMaterial
        The material properties of the component
    width : float
        Width of the component in mm
    length : float
        Length of the component in mm
    thickness : float
        Thickness of the component in mm
    fill_factor : float
        Fraction for material calculations (0.0-1.0)
    datum : Tuple[float, float, float]
        Position of component center in mm (x, y, z)
    name : str
        Identifier name for the component
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        thickness: float,
        width: float = None,
        length: float = None,
        fill_factor: float = DEFAULT_FILL_FACTOR,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Prismatic Component",
    ):
        """Initialize a prismatic component.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Material for the component
        thickness : float
            Thickness of the component in mm. Must be positive.
        width : float, optional
            Width of the component in mm. Must be positive when provided.
            If None, bulk properties and coordinates won't be calculated until set.
        length : float, optional
            Length of the component in mm. Must be positive when provided.
            If None, bulk properties and coordinates won't be calculated until set.
        fill_factor : float, default=0.7
            Fraction for material calculations. Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Position of component center in mm as (x, y, z) coordinates
        name : str, default="Prismatic Component"
            Name identifier for the component
            
        Raises
        ------
        ValueError
            If fill_factor not in [0.0, 1.0] or width/length/thickness <= 0 when provided
        TypeError
            If material is not a PrismaticContainerMaterial instance
        """
        self._update_properties = False
        self._rotated_x = False
        self._rotated_y = False
        self._rotated_z = False

        self.material = material
        self.thickness = thickness
        self.fill_factor = fill_factor
        self.datum = datum
        self.name = name
        
        # Set dimensions using setters (handles None and conversion)
        self.width = width
        self.length = length

    def _calculate_all_properties(self):
        """Calculate all component properties."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate volume, mass, and cost if dimensions are available."""
        if self._width is None or self._length is None:
            self._volume = None
            self._mass = None
            self._cost = None
            return
            
        _volume = self._width * self._length * self._thickness * self._fill_factor
        _mass = _volume * self._material._density
        mass = _mass * KG_TO_G
        self._material.mass = mass

        self._mass = self._material._mass
        self._volume = self._material._volume
        self._cost = self._material._cost

    def _calculate_coordinates(self):
        """Calculate 3D coordinates if dimensions are available."""
        if self._width is None or self._length is None:
            self._coordinates = None
            return
            
        footprint = self._calculate_footprint()
        coordinates = self._extrude_footprint(footprint)
        self._coordinates = coordinates

        # apply rotations if any
        if self._rotated_x:
            self._rotate_x()
        if self._rotated_y:
            self._rotate_y()
        if self._rotated_z:
            self._rotate_z()

    def _extrude_footprint(self, footprint):
        """Extrude a 2D footprint into 3D coordinates."""

        x, y, z, _ = self.extrude_footprint(
            footprint[:,0],
            footprint[:,1],
            self._datum,
            self._thickness
        )

        coordinates = np.column_stack((x, y, z))
        
        return coordinates

    @abstractmethod
    def _calculate_footprint(self):
        """Calculate the 2D footprint of the prismatic component.
        
        This method must be implemented by subclasses to define the
        specific geometry of their footprint.
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
            Path should be closed (first and last points identical).
            
        Raises
        ------
        NotImplementedError
            Must be implemented by subclasses
        """
        return

    def _rotate_x(self, degrees: float = DEFAULT_ROTATION_DEGREES) -> None:
        """
        Rotate the component around the x-axis by the specified degrees.
        
        Parameters
        ----------
        degrees : float, default=90
            Rotation angle in degrees. Positive values rotate counter-clockwise
            when looking along the positive x-axis.
        """
        if self._coordinates is None:
            return
            
        self._coordinates = self.rotate_coordinates(
            self._coordinates, 
            'x', 
            degrees, 
            center=self._datum
        )
    
    def _rotate_y(self, degrees: float = DEFAULT_ROTATION_DEGREES) -> None:
        """
        Rotate the component around the y-axis by the specified degrees.
        
        Parameters
        ----------
        degrees : float, default=90
            Rotation angle in degrees. Positive values rotate counter-clockwise
            when looking along the positive y-axis.
        """
        if self._coordinates is None:
            return
            
        self._coordinates = self.rotate_coordinates(
            self._coordinates, 
            'y', 
            degrees, 
            center=self._datum
        )
    
    def _rotate_z(self, degrees: float = DEFAULT_ROTATION_DEGREES) -> None:
        """
        Rotate the component around the z-axis by the specified degrees.
        
        Parameters
        ----------
        degrees : float, default=90
            Rotation angle in degrees. Positive values rotate counter-clockwise
            when looking along the positive z-axis.
        """
        if self._coordinates is None:
            return
            
        self._coordinates = self.rotate_coordinates(
            self._coordinates, 
            'z', 
            degrees, 
            center=self._datum
        )

    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Generate a top-down view plot of the component.
        
        Creates a Plotly figure showing the component from above,
        displaying the x-y plane footprint.
        
        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to figure.update_layout().
            
        Returns
        -------
        go.Figure
            Interactive Plotly figure with top-down view
        """
        figure = go.Figure()
        figure.add_trace(self.top_down_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    def get_right_left_plot(self, **kwargs) -> go.Figure:
        """Generate a right-left view plot of the component.
        
        Creates a Plotly figure showing the component from the side,
        displaying the x-y plane cross-section.
        
        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to figure.update_layout().
            
        Returns
        -------
        go.Figure
            Interactive Plotly figure with right-left view
        """
        figure = go.Figure()
        figure.add_trace(self.right_left_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def coordinates(self) -> pd.DataFrame:
        """Get 3D coordinates of the component in mm."""
        if self._coordinates is None:
            return pd.DataFrame(columns=["x", "y", "z"])
            
        x = np.round(self._coordinates[:, 0] * M_TO_MM, COORDINATE_PRECISION)
        y = np.round(self._coordinates[:, 1] * M_TO_MM, COORDINATE_PRECISION)
        z = np.round(self._coordinates[:, 2] * M_TO_MM, COORDINATE_PRECISION)

        return pd.DataFrame(
            np.column_stack((x, y, z)),
            columns=["X (mm)", "Y (mm)", "Z (mm)"]
        )
    
    @property
    def top_down_trace(self) -> go.Scatter:
        """Get top-down view trace for plotting (x-y plane)."""
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="xy")
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["X (mm)"],
            y=coordinates["Y (mm)"],
            mode="lines",
            name=self.name,
            line=dict(color=PLOT_LINE_COLOR, width=PLOT_LINE_WIDTH),
            fill="toself",
            fillcolor=self._material.color,
            showlegend=True,
        )
    
    @property
    def right_left_coordinates(self) -> pd.DataFrame:
        """Get right-left view coordinates in mm (y-z plane cross-section)."""
        if self._coordinates is None:
            return pd.DataFrame(columns=["y", "z"])
            
        # Extract y,z coordinates (side profile)
        y = np.round(self._coordinates[:, 1] * M_TO_MM, COORDINATE_PRECISION)
        z = np.round(self._coordinates[:, 2] * M_TO_MM, COORDINATE_PRECISION)

        return pd.DataFrame(
            np.column_stack((y, z)),
            columns=["Y (mm)", "Z (mm)"]
        )
    
    @property
    def right_left_trace(self) -> go.Scatter:
        """Get right-left view trace for plotting (y-z plane cross-section)."""
        coordinates = self.right_left_coordinates
        if len(coordinates) == 0:
            return go.Scatter()
            
        # Order and close the path
        coordinates = self.order_coordinates_clockwise(coordinates, plane="yz")
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["Y (mm)"],
            y=coordinates["Z (mm)"],
            mode="lines",
            name=self.name,
            line=dict(color=PLOT_LINE_COLOR, width=PLOT_LINE_WIDTH),
            fill="toself",
            fillcolor=self._material.color,
            showlegend=True,
        )
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[1] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[2] * M_TO_MM, DIMENSION_PRECISION)
        )

    @property
    def material(self) -> PrismaticContainerMaterial:
        return self._material
    
    @property
    def width(self) -> float:
        """Component width in mm, rounded to 2 decimal places. None if not set."""
        if self._width is None:
            return None
        return np.round(self._width * M_TO_MM, DIMENSION_PRECISION)
    
    @property
    def width_range(self) -> Tuple[float, float]:
        """Valid outer width range in mm, rounded to 2 decimal places."""
        return (WIDTH_RANGE_MIN, WIDTH_RANGE_MAX)

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        """Hard limits for outer width in mm, rounded to 2 decimal places."""
        return (WIDTH_HARD_MIN, WIDTH_HARD_MAX)

    @property
    def length(self) -> float:
        """Component length in mm, rounded to 2 decimal places. None if not set."""
        if self._length is None:
            return None
        return np.round(self._length * M_TO_MM, DIMENSION_PRECISION)
    
    @property
    def length_range(self) -> Tuple[float, float]:
        """Valid outer length range in mm, rounded to 2 decimal places."""
        return (LENGTH_RANGE_MIN, LENGTH_RANGE_MAX)

    @property
    def length_hard_range(self) -> Tuple[float, float]:
        """Hard limits for outer length in mm, rounded to 2 decimal places."""
        return (LENGTH_HARD_MIN, LENGTH_HARD_MAX)

    @property
    def thickness(self) -> float:
        """Component thickness in mm, rounded to 2 decimal places."""
        return np.round(self._thickness * M_TO_MM, DIMENSION_PRECISION)
    
    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Valid thickness range in mm, rounded to 2 decimal places."""
        return (THICKNESS_RANGE_MIN, THICKNESS_RANGE_MAX)

    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Hard limits for thickness in mm, rounded to 2 decimal places."""
        return (THICKNESS_HARD_MIN, THICKNESS_HARD_MAX)

    @property
    def fill_factor(self) -> float:
        """Fill factor (0.0-1.0) for material calculations."""
        return np.round(self._fill_factor, DIMENSION_PRECISION)
    
    @property
    def fill_factor_range(self) -> Tuple[float, float]:
        """Valid fill factor range (0.0-1.0)."""
        return (FILL_FACTOR_MIN, FILL_FACTOR_MAX)

    @property
    def mass(self) -> float:
        """Total mass in grams, accounting for fill factor. None if dimensions not set."""
        if self._mass is None:
            return None
        return np.round(self._mass * KG_TO_G, DIMENSION_PRECISION)
    
    @property
    def cost(self) -> float:
        """Material cost in currency units. None if dimensions not set."""
        if self._cost is None:
            return None
        return np.round(self._cost, DIMENSION_PRECISION)
    
    @property
    def volume(self) -> float:
        """Effective volume in mm³, accounting for fill factor. None if dimensions not set."""
        if self._volume is None:
            return None
        return np.round(self._volume * M_TO_MM**3, DIMENSION_PRECISION)
    
    @property
    def rotated_x(self) -> bool:
        """Whether the component has been rotated around the x-axis."""
        return self._rotated_x
    
    @property
    def rotated_y(self) -> bool:
        """Whether the component has been rotated around the y-axis."""
        return self._rotated_y
    
    @property
    def rotated_z(self) -> bool:
        """Whether the component has been rotated around the z-axis."""
        return self._rotated_z
    
    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        self.validate_datum(datum)
        
        if self._update_properties and hasattr(self, '_datum'):
            # Calculate translation vector in meters
            translation_vector = np.array([
                float(datum[0]) * MM_TO_M - self._datum[0],
                float(datum[1]) * MM_TO_M - self._datum[1],
                float(datum[2]) * MM_TO_M - self._datum[2],
            ])
            
            # Apply translation to coordinates if they exist
            if self._coordinates is not None:
                self._coordinates = self._coordinates + translation_vector
        
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @material.setter
    @calculate_bulk_properties
    def material(self, material: PrismaticContainerMaterial) -> None:
        self.validate_type(material, PrismaticContainerMaterial, "Material")
        self._material = deepcopy(material)

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set width and trigger property calculations."""
        if width is not None:
            self.validate_positive_float(width, "Width")
            self._width = float(width) * MM_TO_M
        else:
            self._width = None

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        """Set length and trigger property calculations."""
        if length is not None:
            self.validate_positive_float(length, "Length")
            self._length = float(length) * MM_TO_M
        else:
            self._length = None

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        """Set thickness and trigger property calculations."""
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * MM_TO_M

    @fill_factor.setter
    @calculate_all_properties
    def fill_factor(self, fill_factor: float) -> None:
        self.validate_positive_float(fill_factor, "Fill Factor")
        if fill_factor > 1.0:
            raise ValueError("Fill Factor must be between 0 and 1.")
        self._fill_factor = float(fill_factor)
    
    def _apply_rotation_setter(self, axis: str, value: bool) -> None:
        """Helper method to handle rotation state changes.
        
        Parameters
        ----------
        axis : str
            Rotation axis ('x', 'y', or 'z')
        value : bool
            Whether to rotate (True) or unrotate (False)
        """
        flag_attr = f'_rotated_{axis}'
        rotate_method = getattr(self, f'_rotate_{axis}')
        current_state = getattr(self, flag_attr)
        
        if value and not current_state:
            rotate_method()
            setattr(self, flag_attr, True)
        elif not value and current_state:
            rotate_method(degrees=-90)
            setattr(self, flag_attr, False)
    
    @rotated_x.setter
    def rotated_x(self, value: bool) -> None:
        """Set rotation state around x-axis. Setting to True triggers rotation, False unrotates."""
        self.validate_type(value, bool, "Rotated X")
        self._apply_rotation_setter('x', value)
    
    @rotated_y.setter
    def rotated_y(self, value: bool) -> None:
        """Set rotation state around y-axis. Setting to True triggers rotation, False unrotates."""
        self.validate_type(value, bool, "Rotated Y")
        self._apply_rotation_setter('y', value)
    
    @rotated_z.setter
    def rotated_z(self, value: bool) -> None:
        """Set rotation state around z-axis. Setting to True triggers rotation, False unrotates."""
        self.validate_type(value, bool, "Rotated Z")
        self._apply_rotation_setter('z', value)


class PrismaticTerminalConnector(_PrismaticComponent):
    """A prismatic terminal connector with rectangular footprint.

    The PrismaticTerminalConnector creates a rectangular footprint for 
    terminal connections in prismatic battery cells. The connector is 
    positioned under the lid assembly.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        thickness: float,
        width: float = None,
        length: float = None,
        fill_factor: float = DEFAULT_FILL_FACTOR,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Prismatic Terminal Connector",
    ):
        """Initialize a prismatic terminal connector.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        thickness : float
            Component thickness in mm. Must be positive.
        width : float, optional
            Component width in mm. Must be positive when provided.
        length : float, optional
            Component length in mm. Must be positive when provided.
        fill_factor : float, default=0.7
            Material density factor for calculations. Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Prismatic Terminal Connector"
            Component identifier name
        """
        super().__init__(material, thickness, width, length, fill_factor, datum, name)
        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_footprint(self):
        """Calculate the 2D rectangular footprint of the terminal connector.
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
        """
        if self._width is None or self._length is None:
            raise ValueError("Cannot calculate footprint: width or length is not set")
            
        half_width = self._width / 2
        half_length = self._length / 2
        
        # Create rectangular footprint (clockwise from bottom-left)
        x_coords = np.array([
            self._datum[0] - half_width,
            self._datum[0] + half_width,
            self._datum[0] + half_width,
            self._datum[0] - half_width,
            self._datum[0] - half_width,  # Close the path
        ])
        
        y_coords = np.array([
            self._datum[1] - half_length,
            self._datum[1] - half_length,
            self._datum[1] + half_length,
            self._datum[1] + half_length,
            self._datum[1] - half_length,  # Close the path
        ])
        
        footprint = np.column_stack((x_coords, y_coords))
        return footprint


class PrismaticLidAssembly(_PrismaticComponent):
    """A prismatic lid assembly with rectangular footprint.
    
    This class represents a rectangular lid assembly for prismatic containers.
    The lid has a simple rectangular footprint and sits on top of the canister.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        thickness: float,
        width: float = None,
        length: float = None,
        fill_factor: float = DEFAULT_FILL_FACTOR,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Prismatic Lid Assembly",
    ):
        """Initialize a prismatic lid assembly.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        thickness : float
            Component thickness in mm. Must be positive.
        width : float, optional
            Component width in mm. Must be positive when provided.
        length : float, optional
            Component length in mm. Must be positive when provided.
        fill_factor : float, default=0.7
            Material density factor for calculations. Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Prismatic Lid Assembly"
            Component identifier name
        """
        super().__init__(material, thickness, width, length, fill_factor, datum, name)
        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_footprint(self):
        """Calculate the 2D rectangular footprint of the lid assembly.
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
        """
        if self._width is None or self._length is None:
            raise ValueError("Cannot calculate footprint: width or length is not set")
            
        half_width = self._width / 2
        half_length = self._length / 2
        
        # Create rectangular footprint (clockwise from bottom-left)
        x_coords = np.array([
            self._datum[0] - half_width,
            self._datum[0] + half_width,
            self._datum[0] + half_width,
            self._datum[0] - half_width,
            self._datum[0] - half_width,  # Close the path
        ])
        
        y_coords = np.array([
            self._datum[1] - half_length,
            self._datum[1] - half_length,
            self._datum[1] + half_length,
            self._datum[1] + half_length,
            self._datum[1] - half_length,  # Close the path
        ])
        
        footprint = np.column_stack((x_coords, y_coords))
        return footprint

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Valid thickness range in mm, rounded to 2 decimal places."""
        return (0.5, 10)
    
    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Hard limits for thickness in mm, rounded to 2 decimal places."""
        return (0.1, 20)


class PrismaticCanister(
    CoordinateMixin, 
    SerializerMixin,
    ValidationMixin,
    PlotterMixin
):
    """A prismatic (rectangular) container with walls.
    
    This class represents a rectangular container with walls defined by 
    inner and outer dimensions. The container has a base and four walls,
    forming a rectangular box shape.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        width: float,
        length: float,
        height: float,
        wall_thickness: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Prismatic Canister",
    ):
        """Initialize a prismatic canister.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        width : float
            Outer width of the canister in mm. Must be positive.
        length : float
            Outer length of the canister in mm. Must be positive.
        height : float
            Height of the canister in mm. Must be positive.
        wall_thickness : float
            Wall thickness in mm. Must be positive and less than half of outer dimensions.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Prismatic Canister"
            Component identifier name
        """
        self._update_properties = False
        self._rotated_z = False

        self.material = material
        self.width = width
        self.length = length
        self.height = height
        self.wall_thickness = wall_thickness
        self.datum = datum
        self.name = name

        self._calculate_all_properties()
        self._update_properties = True
        
    def _calculate_all_properties(self):
        """Calculate all canister properties."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate volume, mass, and cost of the canister."""
        # Calculate inner dimensions
        self._inner_width = self._width - 2 * self._wall_thickness
        self._inner_length = self._length - 2 * self._wall_thickness
        self._inner_height = self._height - self._wall_thickness

        # Calculate volumes
        _outer_volume = self._width * self._length * self._height
        _inner_volume = self._inner_width * self._inner_length * self._inner_height
        _wall_volume = _outer_volume - _inner_volume
        
        # Calculate mass
        _mass = _wall_volume * self._material._density
        mass = _mass * KG_TO_G
        self._material.mass = mass

        # Set properties
        self._mass = self._material._mass
        self._cost = self._material._cost
        self._volume = _outer_volume

    def _calculate_coordinates(self):
        """Calculate coordinate representations."""
        self._get_top_down_coordinates()
        self._get_right_left_coordinates()
        
        # Reapply rotation if active
        if self._rotated_z:
            self._rotate_z()

    def _get_top_down_coordinates(self):
        """Calculate the right-left view coordinates showing U-shaped profile."""
        half_width = self._width / 2
        
        # Define the U-shape profile points (clockwise from bottom-left)
        # Bottom-left outer corner
        x1 = self._datum[0] - half_width
        y1 = self._datum[1]
        
        # Bottom-left inner corner  
        x2 = self._datum[0] - half_width + self._wall_thickness
        y2 = self._datum[1] + self._wall_thickness
        
        # Top-left inner corner
        x3 = self._datum[0] - half_width + self._wall_thickness
        y3 = self._datum[1] + self._height
        
        # Top-right inner corner
        x4 = self._datum[0] + half_width - self._wall_thickness
        y4 = self._datum[1] + self._height
        
        # Bottom-right inner corner
        x5 = self._datum[0] + half_width - self._wall_thickness
        y5 = self._datum[1] + self._wall_thickness
        
        # Bottom-right outer corner
        x6 = self._datum[0] + half_width
        y6 = self._datum[1]
        
        # Top-right outer corner
        x7 = self._datum[0] + half_width
        y7 = self._datum[1] + self._height
        
        # Top-left outer corner
        x8 = self._datum[0] - half_width
        y8 = self._datum[1] + self._height
        
        # Create the U-shaped profile
        x_coords = np.array([x1, x8, x3, x2, x5, x4, x7, x6, x1])
        y_coords = np.array([y1, y8, y3, y2, y5, y4, y7, y6, y1])
        
        self._top_down_coordinates = np.column_stack((x_coords, y_coords))
    
    def _get_right_left_coordinates(self):
        """Calculate the right-left view coordinates.
        
        If rotated_z is False: U-shaped profile (bucket shape) with opening in +y direction, height in +z direction.
        If rotated_z is True: Rectangular profile with x-axis as width, y-axis as length.
        """
        if not self._rotated_z:
            # Bucket shape (U-shape) - opening towards +y direction, height in +z
            half_length = self._length / 2
            
            # Define the U-shape profile points (clockwise from bottom-left)
            # Bottom-left (back-bottom) outer corner
            y1 = self._datum[1]
            z1 = self._datum[2] - half_length
            
            # Bottom-left (back-bottom) inner corner  
            y2 = self._datum[1] + self._wall_thickness
            z2 = self._datum[2] - half_length + self._wall_thickness
            
            # Top-left (back-top) inner corner
            y3 = self._datum[1] + self._height
            z3 = self._datum[2] - half_length + self._wall_thickness
            
            # Top-right (front-top) inner corner
            y4 = self._datum[1] + self._height
            z4 = self._datum[2] + half_length - self._wall_thickness
            
            # Bottom-right (front-bottom) inner corner
            y5 = self._datum[1] + self._wall_thickness
            z5 = self._datum[2] + half_length - self._wall_thickness
            
            # Bottom-right (front-bottom) outer corner
            y6 = self._datum[1]
            z6 = self._datum[2] + half_length
            
            # Top-right (front-top) outer corner
            y7 = self._datum[1] + self._height
            z7 = self._datum[2] + half_length
            
            # Top-left (back-top) outer corner
            y8 = self._datum[1] + self._height
            z8 = self._datum[2] - half_length
            
            # Create the U-shaped profile - store as [y, z] coordinates
            x_coords = np.array([y1, y8, y3, y2, y5, y4, y7, y6, y1])
            y_coords = np.array([z1, z8, z3, z2, z5, z4, z7, z6, z1])
        else:
            # Rectangular hollow profile when rotated - showing wall thickness in y-z plane
            # When rotated around z-axis, the right-left view (y-z plane) still shows:
            # y-axis = height, z-axis = length (rotation around z doesn't change this view)
            half_width = self._width / 2
            half_length = self._length / 2
            
            # Outer rectangle corners (y-axis shows height, z-axis shows length)
            y_outer_bottom = self._datum[1] - half_width
            y_outer_top = self._datum[1] + half_width
            z_outer_left = self._datum[2] - half_length
            z_outer_right = self._datum[2] + half_length
            
            # Inner rectangle corners (accounting for wall thickness on all sides)
            y_inner_bottom = y_outer_bottom + self._wall_thickness
            y_inner_top = y_outer_top - self._wall_thickness
            z_inner_left = z_outer_left + self._wall_thickness
            z_inner_right = z_outer_right - self._wall_thickness
            
            # Create hollow rectangular frame (outer path, then inner path to create hole)
            # Outer rectangle (clockwise)
            x_coords = np.array([
                y_outer_bottom, y_outer_top, y_outer_top, y_outer_bottom, y_outer_bottom,
                # Inner rectangle (counter-clockwise to create hole)
                y_inner_bottom, y_inner_bottom, y_inner_top, y_inner_top, y_inner_bottom,
            ])
            
            y_coords = np.array([
                z_outer_left, z_outer_left, z_outer_right, z_outer_right, z_outer_left,
                # Inner rectangle (counter-clockwise to create hole)
                z_inner_left, z_inner_right, z_inner_right, z_inner_left, z_inner_left,
            ])
        
        self._right_left_coordinates = np.column_stack((x_coords, y_coords))

    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Generate a top-down view plot of the canister."""
        figure = go.Figure()
        figure.add_trace(self.top_down_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure
    
    def get_right_left_view(self, **kwargs) -> go.Figure:
        """Generate a right-left view plot of the canister."""
        figure = go.Figure()
        figure.add_trace(self.right_left_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    def _rotate_z(self, degrees: float = -90) -> None:
        """
        Rotate the canister around the z-axis by the specified degrees.
        
        Parameters
        ----------
        degrees : float, default=-90
            Rotation angle in degrees. Positive values rotate counter-clockwise
            when looking along the positive z-axis.
        """
        if self._top_down_coordinates is not None:
            self._top_down_coordinates = self.rotate_coordinates(
                self._top_down_coordinates, 
                'z', 
                degrees, 
                center=(self._datum[0], self._datum[1])
            )
    
    @property
    def inner_width(self) -> float:
        """Inner width of the canister in mm."""
        return np.round(self._inner_width * M_TO_MM, 2)
    
    @property
    def inner_length(self) -> float:
        """Inner length of the canister in mm."""
        return np.round(self._inner_length * M_TO_MM, 2)

    @property
    def right_left_coordinates(self) -> pd.DataFrame:
        """Get right-left view coordinates in mm."""
        x = np.round(self._right_left_coordinates[:, 0] * M_TO_MM, 10)
        y = np.round(self._right_left_coordinates[:, 1] * M_TO_MM, 10)

        return pd.DataFrame(
            np.column_stack((x, y)),
            columns=["X (mm)", "Y (mm)"]
        )
    
    @property
    def right_left_trace(self) -> go.Scatter:
        """Get right-left view trace for plotting."""
        coordinates = self.right_left_coordinates
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["X (mm)"],
            y=coordinates["Y (mm)"],
            mode="lines",
            name=self.name,
            line=dict(color=PLOT_LINE_COLOR, width=PLOT_LINE_WIDTH),
            fill="toself",
            fillcolor=self._material.color,
            showlegend=True,
        )

    @property
    def top_down_coordinates(self) -> pd.DataFrame:
        """Get top-down view coordinates in mm."""
        x = np.round(self._top_down_coordinates[:, 0] * M_TO_MM, 10)
        z = np.round(self._top_down_coordinates[:, 1] * M_TO_MM, 10)

        return pd.DataFrame(
            np.column_stack((x, z)),
            columns=["X (mm)", "Z (mm)"]
        )

    @property
    def top_down_trace(self) -> go.Scatter:
        """Get top-down view trace for plotting."""
        coordinates = self.top_down_coordinates

        return go.Scatter(
            x=coordinates["X (mm)"],
            y=coordinates["Z (mm)"],
            mode="lines",
            name=self.name,
            line=dict(color=PLOT_LINE_COLOR, width=PLOT_LINE_WIDTH),
            fill="toself",
            fillcolor=self._material.color,
            showlegend=True,
        )
    
    @property
    def inner_height(self) -> float:
        """Inner height of the canister in mm."""
        return np.round(self._inner_height * M_TO_MM, 2)

    @property
    def cost(self) -> float:
        """Total cost in currency units."""
        return np.round(self._cost, DIMENSION_PRECISION)

    @property
    def mass(self) -> float:
        """Total mass in grams."""
        return np.round(self._mass * KG_TO_G, DIMENSION_PRECISION)

    @property
    def volume(self) -> float:
        """Total volume in mm³."""
        return np.round(self._volume * M_TO_MM**3, DIMENSION_PRECISION)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[1] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[2] * M_TO_MM, DIMENSION_PRECISION)
        )
    
    @property
    def material(self) -> PrismaticContainerMaterial:
        return self._material
    
    @property
    def width(self) -> float:
        """Outer width in mm."""
        return np.round(self._width * M_TO_MM, DIMENSION_PRECISION)
    
    @property
    def width_range(self) -> Tuple[float, float]:
        """Valid outer width range in mm, rounded to 2 decimal places."""
        return (WIDTH_RANGE_MIN, WIDTH_RANGE_MAX)

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        """Hard limits for outer width in mm, rounded to 2 decimal places."""
        return (WIDTH_HARD_MIN, WIDTH_HARD_MAX)

    @property
    def length(self) -> float:
        """Outer length in mm."""
        return np.round(self._length * M_TO_MM, DIMENSION_PRECISION)
    
    @property
    def length_range(self) -> Tuple[float, float]:
        """Valid outer length range in mm, rounded to 2 decimal places."""
        return (LENGTH_RANGE_MIN, LENGTH_RANGE_MAX)
    
    @property
    def length_hard_range(self) -> Tuple[float, float]:
        """Hard limits for outer length in mm, rounded to 2 decimal places."""
        return (LENGTH_HARD_MIN, LENGTH_HARD_MAX)

    @property
    def height(self) -> float:
        """Height in mm."""
        return np.round(self._height * M_TO_MM, 2)
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Valid height range in mm, rounded to 2 decimal places."""
        return (HEIGHT_RANGE_MIN, HEIGHT_RANGE_MAX)
    
    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Hard limits for height in mm, rounded to 2 decimal places."""
        return (HEIGHT_HARD_MIN, HEIGHT_HARD_MAX)

    @property
    def wall_thickness(self) -> float:
        """Wall thickness in mm."""
        return np.round(self._wall_thickness * M_TO_MM, 2)
    
    @property
    def wall_thickness_range(self) -> Tuple[float, float]:
        """Valid wall thickness range in mm, rounded to 2 decimal places."""
        return (WALL_THICKNESS_RANGE_MIN, WALL_THICKNESS_RANGE_MAX)

    @property
    def rotated_z(self) -> bool:
        """Whether the canister has been rotated around the z-axis."""
        return self._rotated_z
    
    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        self.validate_datum(datum)
        
        if self._update_properties and hasattr(self, '_datum'):
            # Calculate translation vector in meters
            translation_vector = np.array([
                float(datum[0]) * MM_TO_M - self._datum[0],
                float(datum[1]) * MM_TO_M - self._datum[1],
                float(datum[2]) * MM_TO_M - self._datum[2],
            ])
            
            # Apply translation to coordinate arrays if they exist
            if hasattr(self, '_right_left_coordinates') and self._right_left_coordinates is not None:
                self._right_left_coordinates = self._right_left_coordinates + np.array([translation_vector[1], translation_vector[2]])
            
            if hasattr(self, '_top_down_coordinates') and self._top_down_coordinates is not None:
                self._top_down_coordinates = self._top_down_coordinates + np.array([translation_vector[0], translation_vector[1]])
        
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @material.setter
    @calculate_bulk_properties
    def material(self, material: PrismaticContainerMaterial) -> None:
        self.validate_type(material, PrismaticContainerMaterial, "Material")
        self._material = deepcopy(material)

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        self.validate_positive_float(length, "Length")
        self._length = float(length) * MM_TO_M

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        self._height = float(height) * MM_TO_M

    @wall_thickness.setter
    @calculate_all_properties
    def wall_thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Wall Thickness")
        self._wall_thickness = float(thickness) * MM_TO_M

    @inner_width.setter
    def inner_width(self, inner_width: float) -> None:
        self.validate_positive_float(inner_width, "Inner Width")
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        new_width = inner_width + 2 * wall_thickness_mm
        self.width = new_width

    @inner_length.setter
    def inner_length(self, inner_length: float) -> None:
        self.validate_positive_float(inner_length, "Inner Length")
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        new_length = inner_length + 2 * wall_thickness_mm
        self.length = new_length

    @inner_height.setter
    def inner_height(self, inner_height: float) -> None:
        self.validate_positive_float(inner_height, "Inner Height")
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        new_height = inner_height + wall_thickness_mm
        self.height = new_height
    
    @rotated_z.setter
    def rotated_z(self, value: bool) -> None:
        """Set rotation state around z-axis. Setting to True triggers rotation, False unrotates."""
        self.validate_type(value, bool, "Rotated Z")
        if value and not self._rotated_z:
            self._rotate_z()
            self._rotated_z = True
            self._get_right_left_coordinates()  # Recalculate after rotation state changes
        elif not value and self._rotated_z:
            self._rotate_z(degrees=90)  # Note: PrismaticCanister uses -90 as default, so +90 unrotates
            self._rotated_z = False
            self._get_right_left_coordinates()  # Recalculate after rotation state changes


class PrismaticEncapsulation(_Container):
    """A prismatic encapsulation with rectangular geometry.
    
    This class combines a rectangular canister with a lid assembly and two
    terminal connectors (cathode and anode) positioned under the lid. Unlike
    the cylindrical encapsulation where connectors are at opposite ends, both
    connectors are under the lid in the prismatic design.
    """

    def __init__(
            self,
            cathode_terminal_connector: PrismaticTerminalConnector,
            anode_terminal_connector: PrismaticTerminalConnector,
            lid_assembly: PrismaticLidAssembly,
            canister: PrismaticCanister,
            connector_orientation: ConnectorOrientation = ConnectorOrientation.LONGITUDINAL,
            cathode_terminal_connector_position: float = None,
            anode_terminal_connector_position: float = None,
            name: str = "Prismatic Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):
        """Initialize a prismatic encapsulation.
        
        Parameters
        ----------
        cathode_terminal_connector : PrismaticTerminalConnector
            Cathode terminal connector component
        anode_terminal_connector : PrismaticTerminalConnector
            Anode terminal connector component
        lid_assembly : PrismaticLidAssembly
            Lid assembly component
        canister : PrismaticCanister
            Rectangular canister body
        connector_orientation : ConnectorOrientation, default=ConnectorOrientation.LONGITUDINAL
            Orientation of the terminal connectors
        cathode_terminal_connector_position : float, optional
            Position of cathode terminal connector from left edge of lid in mm
            (longitudinal mode only). If None, uses default centered position.
        anode_terminal_connector_position : float, optional
            Position of anode terminal connector from left edge of lid in mm
            (longitudinal mode only). If None, uses default centered position.
        name : str, default="Prismatic Encapsulation"
            Name identifier for the encapsulation
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        """
        self._update_properties = False
        self.connector_orientation = connector_orientation
        self.cathode_terminal_connector_position = cathode_terminal_connector_position
        self.anode_terminal_connector_position = anode_terminal_connector_position
        
        self.cathode_terminal_connector = cathode_terminal_connector
        self.anode_terminal_connector = anode_terminal_connector
        self.lid_assembly = lid_assembly
        self.canister = canister
        self.name = name
        self.datum = datum

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
        """Calculate all encapsulation properties."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_coordinates(self):
        """Position all components relative to the canister."""
        self._calculate_dimensions()
        self._position_canister()
        self._position_lid_assembly()
        self._position_cathode_terminal_connector()
        self._position_anode_terminal_connector()
        self._center_cavity_at_datum()

    def _position_canister(self):
        """Position and rotate canister based on connector orientation."""
        # Set canister at encapsulation datum
        self._canister.datum = (
            self._datum[0] * M_TO_MM,
            self._datum[1] * M_TO_MM,
            self._datum[2] * M_TO_MM
        )
        
        # Rotate canister based on connector orientation
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:         
            self._canister.rotated_z = False
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            self._canister.rotated_z = True

    def _position_lid_assembly(self):
        """Position lid assembly based on connector orientation."""
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            self._position_lid_longitudinal()
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            self._position_lid_transverse()
    
    def _position_lid_longitudinal(self):
        """Position lid for longitudinal connector orientation."""
        self._lid_assembly.datum = (
            self._canister._datum[0] * M_TO_MM,
            (self._canister._datum[1] + self._canister._height - self._lid_assembly._thickness / 2) * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._lid_assembly, x=True, y=False, z=False)
    
    def _position_lid_transverse(self):
        """Position lid for transverse connector orientation."""
        self._lid_assembly.datum = (
            (self._canister._datum[0] + self._canister._height - self._lid_assembly._thickness / 2) * M_TO_MM,
            self._canister._datum[1] * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._lid_assembly, x=True, y=False, z=True)

    def _set_component_rotation(self, component, x: bool, y: bool, z: bool):
        """Helper method to set rotation state for all three axes.
        
        Parameters
        ----------
        component : _PrismaticComponent
            Component to rotate
        x, y, z : bool
            Rotation states for each axis
        """
        component.rotated_x = x
        component.rotated_y = y
        component.rotated_z = z
    
    def _position_cathode_terminal_connector(self):
        """Position cathode terminal connector based on connector orientation."""
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            self._position_cathode_longitudinal()
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            self._position_cathode_transverse()
    
    def _position_cathode_longitudinal(self):
        """Position cathode connector for longitudinal orientation (left side)."""
        if self._cathode_terminal_connector_position is not None:
            # Use custom position from left edge
            left_edge = self._canister._datum[0] - self._canister._inner_width / 2
            x_position = left_edge + self._cathode_terminal_connector_position * MM_TO_M
        else:
            # Use default centered position (1/4 from left)
            cathode_offset = self._canister._inner_width / 4
            x_position = self._canister._datum[0] - cathode_offset
        
        y_position = (self._canister._datum[1] + self._canister._height - 
                     self._lid_assembly._thickness - 
                     self._cathode_terminal_connector._thickness / 2)
        
        self._cathode_terminal_connector.datum = (
            x_position * M_TO_MM,
            y_position * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._cathode_terminal_connector, x=True, y=False, z=False)
    
    def _position_cathode_transverse(self):
        """Position cathode connector for transverse orientation (front side)."""
        x_position = (self._canister._datum[0] + self._canister._height - 
                     self._lid_assembly._thickness - 
                     self._cathode_terminal_connector._length / 2)
        y_position = (self._canister._datum[1] + self._canister._inner_width / 2 - 
                     self._cathode_terminal_connector._thickness / 2)
        
        self._cathode_terminal_connector.datum = (
            x_position * M_TO_MM,
            y_position * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._cathode_terminal_connector, x=True, y=True, z=False)

    def _position_anode_terminal_connector(self):
        """Position anode terminal connector based on connector orientation."""
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            self._position_anode_longitudinal()
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            self._position_anode_transverse()
    
    def _position_anode_longitudinal(self):
        """Position anode connector for longitudinal orientation (right side)."""
        if self._anode_terminal_connector_position is not None:
            # Use custom position from left edge
            left_edge = self._canister._datum[0] - self._canister._inner_width / 2
            x_position = left_edge + self._anode_terminal_connector_position * MM_TO_M
        else:
            # Use default centered position (1/4 from right)
            anode_offset = self._canister._inner_width / 4
            x_position = self._canister._datum[0] + anode_offset
        
        y_position = (self._canister._datum[1] + self._canister._height - 
                     self._lid_assembly._thickness - 
                     self._anode_terminal_connector._thickness / 2)
        
        self._anode_terminal_connector.datum = (
            x_position * M_TO_MM,
            y_position * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._anode_terminal_connector, x=True, y=False, z=False)
    
    def _position_anode_transverse(self):
        """Position anode connector for transverse orientation (back side)."""
        x_position = (self._canister._datum[0] + self._canister._height - 
                     self._lid_assembly._thickness - 
                     self._anode_terminal_connector._length / 2)
        y_position = (self._canister._datum[1] - self._canister._inner_width / 2 + 
                     self._anode_terminal_connector._thickness / 2)
        
        self._anode_terminal_connector.datum = (
            x_position * M_TO_MM,
            y_position * M_TO_MM,
            self._canister._datum[2] * M_TO_MM
        )
        self._set_component_rotation(self._anode_terminal_connector, x=True, y=True, z=False)

    def _center_cavity_at_datum(self):
        """Move all components so the center of the internal cavity is at the datum."""
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            # Calculate where the cavity center currently is
            cavity_center_x = self._canister._datum[0]
            cavity_center_y = (self._canister._datum[1] + self._canister._wall_thickness + 
                             self._internal_height / 2)
            cavity_center_z = self._canister._datum[2]
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            # For transverse, the cavity center calculation differs due to rotation
            cavity_center_x = self._canister._datum[0] + self._canister._wall_thickness + self._internal_width / 2
            cavity_center_y = self._canister._datum[1]
            cavity_center_z = self._canister._datum[2]
        
        # Calculate offset needed to move cavity center to datum
        offset_x = self._datum[0] - cavity_center_x
        offset_y = self._datum[1] - cavity_center_y
        offset_z = self._datum[2] - cavity_center_z
        
        # Apply offset to all components (in mm)
        translation_vector = (offset_x, offset_y, offset_z)
        self._translate_all_components(translation_vector)
        
    def _calculate_dimensions(self):

        # Calculate midpoint for reference
        _max_connector_bottom = max(
            self._anode_terminal_connector._datum[1] - self._anode_terminal_connector._thickness / 2,
            self._cathode_terminal_connector._datum[1] - self._cathode_terminal_connector._thickness / 2
        )
        
        _min_canister_base = self._canister._datum[1] + self._canister._wall_thickness
        self._mid_y_point = (_max_connector_bottom + _min_canister_base) / 2

    def _calculate_bulk_properties(self):
        """Calculate dimensions and mass/cost properties."""
        self._set_component_dimensions()
        self._calculate_internal_dimensions()
        self._volume = self._canister._volume
        self._calculate_mass()
        self._calculate_cost()
    
    def _set_component_dimensions(self):
        """Set dimensions for lid assembly and terminal connectors based on canister."""
        connector_width = self._canister._inner_width * 0.3  # 30% of inner width
        connector_length = self._canister._inner_length * 0.8  # 80% of inner length
        
        self._lid_assembly.width = self._canister._inner_width * M_TO_MM
        self._lid_assembly.length = self._canister._inner_length * M_TO_MM

        if self._cathode_terminal_connector._width is None:
            self._cathode_terminal_connector.width = connector_width * M_TO_MM
        if self._cathode_terminal_connector._length is None:
            self._cathode_terminal_connector.length = connector_length * M_TO_MM
        if self._anode_terminal_connector._width is None:
            self._anode_terminal_connector.width = connector_width * M_TO_MM
        if self._anode_terminal_connector._length is None:
            self._anode_terminal_connector.length = connector_length * M_TO_MM
    
    def _calculate_internal_dimensions(self):
        """Calculate internal dimensions available for cell contents."""
        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            self._calculate_internal_dimensions_longitudinal()
        elif self._connector_orientation == ConnectorOrientation.TRANSVERSE:
            self._calculate_internal_dimensions_transverse()
    
    def _calculate_internal_dimensions_longitudinal(self):
        """Calculate internal dimensions for longitudinal connector orientation."""
        max_connector_thickness = max(
            self._anode_terminal_connector._thickness,
            self._cathode_terminal_connector._thickness
        )
        
        self._internal_height = (
            self._canister._inner_height - 
            self._lid_assembly._thickness - 
            max_connector_thickness
        )
        self._internal_width = self._canister._inner_width
        self._internal_length = self._canister._inner_length
    
    def _calculate_internal_dimensions_transverse(self):
        """Calculate internal dimensions for transverse connector orientation."""
        self._internal_height = (
            self._canister._inner_width - 
            self._cathode_terminal_connector._thickness - 
            self._anode_terminal_connector._thickness
        )
        self._internal_width = (
            self._canister._inner_height - 
            self._lid_assembly._thickness
        )
        self._internal_length = self._canister._inner_length

    def _calculate_mass(self):
        """Calculate total mass and mass breakdown."""
        self._mass = (
            self._cathode_terminal_connector._material._mass +
            self._anode_terminal_connector._material._mass +
            self._lid_assembly._material._mass +
            self._canister._material._mass
        )

        self._mass_breakdown = {
            "Cathode Terminal Connector": self._cathode_terminal_connector._material._mass,
            "Anode Terminal Connector": self._anode_terminal_connector._material._mass,
            "Lid Assembly": self._lid_assembly._material._mass,
            "Canister": self._canister._material._mass
        }

    def _calculate_cost(self):
        """Calculate total cost and cost breakdown."""
        self._cost = (
            self._cathode_terminal_connector._material._cost +
            self._anode_terminal_connector._material._cost +
            self._lid_assembly._material._cost +
            self._canister._material._cost
        )

        self._cost_breakdown = {
            "Cathode Terminal Connector": self._cathode_terminal_connector._material._cost,
            "Anode Terminal Connector": self._anode_terminal_connector._material._cost,
            "Lid Assembly": self._lid_assembly._material._cost,
            "Canister": self._canister._material._cost
        }

    def plot_mass_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        """Plot mass breakdown as sunburst chart."""
        fig = self.plot_breakdown_sunburst(
            self.mass_breakdown,
            title=title or f"{self.name} Mass Breakdown",
            unit="g",
            **kwargs,
        )
        return fig
    
    def plot_cost_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        """Plot cost breakdown as sunburst chart."""
        fig = self.plot_breakdown_sunburst(
            self.cost_breakdown,
            title=title or f"{self.name} Cost Breakdown",
            unit="currency units",
            **kwargs,
        )
        return fig
    
    def get_right_left_view(self, **kwargs) -> go.Figure:
        """Generate a side view plot showing all components."""
        figure = go.Figure()
        traces = []

        traces.append(self._canister.right_left_trace)
        traces.append(self._cathode_terminal_connector.right_left_trace)
        traces.append(self._anode_terminal_connector.right_left_trace)

        if self._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            traces.append(self._lid_assembly.right_left_trace)

        figure.add_traces(traces)

        figure.update_layout(
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            title=kwargs.get("title", f"{self.name} Side View"),
            **kwargs,
        )

        return figure
    
    def get_top_down_view(self, opacity=0.8, **kwargs) -> go.Figure:
        """Generate a top-down view plot showing all components."""
        figure = go.Figure()
        traces = []

        traces.append(self._canister.top_down_trace)
        traces.append(self._lid_assembly.top_down_trace)
        traces.append(self._cathode_terminal_connector.top_down_trace)
        traces.append(self._anode_terminal_connector.top_down_trace)

        for trace in traces:
            self.adjust_trace_opacity(trace, opacity)

        figure.add_traces(traces)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            title=kwargs.get("title", f"{self.name} Top-Down View"),
            **kwargs,
        )

        return figure
    
    @property
    def connector_orientation(self) -> ConnectorOrientation:
        return self._connector_orientation

    @property
    def volume(self) -> float:
        """Total volume in mm³."""
        return np.round(self._volume * M_TO_MM**3, DIMENSION_PRECISION)

    @property
    def internal_height(self) -> float:
        """Internal height available for cell contents in mm."""
        return np.round(self._internal_height * M_TO_MM, 2)

    @property
    def internal_height_range(self) -> Tuple[float, float]:
        """Valid internal height range in mm, rounded to 2 decimal places."""
        return (INTERNAL_HEIGHT_RANGE_MIN, INTERNAL_HEIGHT_RANGE_MAX)

    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[1] * M_TO_MM, DIMENSION_PRECISION), 
            np.round(self._datum[2] * M_TO_MM, DIMENSION_PRECISION)
        )
        
    @property
    def cost(self) -> float:
        """Total cost in currency units."""
        return np.round(self._cost, DIMENSION_PRECISION)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def cathode_terminal_connector(self) -> PrismaticTerminalConnector:
        return self._cathode_terminal_connector
    
    @property
    def anode_terminal_connector(self) -> PrismaticTerminalConnector:
        return self._anode_terminal_connector
    
    @property
    def lid_assembly(self) -> PrismaticLidAssembly:
        return self._lid_assembly
    
    @property
    def canister(self) -> PrismaticCanister:
        return self._canister
    
    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """Get the cost breakdown of the encapsulation."""
        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj, 2)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """Get the mass breakdown of the encapsulation."""
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj * KG_TO_G, 2)

        return _convert_and_round_recursive(self._mass_breakdown)
    
    @property
    def mass(self) -> float:
        """Total mass in grams."""
        return np.round(self._mass * KG_TO_G, DIMENSION_PRECISION)
    
    @property
    def width(self) -> float:
        """Outer width of the encapsulation in mm."""
        return self._canister.width
    
    @property
    def length(self) -> float:
        """Outer length of the encapsulation in mm."""
        return self._canister.length
    
    @property
    def height(self) -> float:
        """Total height of the encapsulation in mm."""
        return self._canister.height
    
    @property
    def cathode_terminal_connector_position(self) -> float:
        """Position of cathode terminal connector from left edge in mm (longitudinal mode)."""
        return self._cathode_terminal_connector_position
    
    @property
    def anode_terminal_connector_position(self) -> float:
        """Position of anode terminal connector from left edge in mm (longitudinal mode)."""
        return self._anode_terminal_connector_position
    
    @connector_orientation.setter
    @calculate_all_properties
    def connector_orientation(self, orientation) -> None:
        """Set connector orientation for the encapsulation.
        
        Parameters
        ----------
        orientation : ConnectorOrientation or str
            Either a ConnectorOrientation enum value or a string 
            ('transverse' or 'longitudinal')
        """
        if isinstance(orientation, str):
            try:
                orientation = ConnectorOrientation(orientation.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid orientation string: '{orientation}'. "
                    f"Must be 'transverse' or 'longitudinal'."
                )
        else:
            self.validate_type(orientation, ConnectorOrientation, "Connector Orientation")
            
        self._connector_orientation = orientation
    
    @cathode_terminal_connector_position.setter
    @calculate_all_properties
    def cathode_terminal_connector_position(self, position: float) -> None:
        """Set cathode terminal connector position from left edge in mm."""
        if position is not None:
            self.validate_positive_float(position, "Cathode Terminal Connector Position")
            self._cathode_terminal_connector_position = float(position)
        else:
            self._cathode_terminal_connector_position = None
    
    @anode_terminal_connector_position.setter
    @calculate_all_properties
    def anode_terminal_connector_position(self, position: float) -> None:
        """Set anode terminal connector position from left edge in mm."""
        if position is not None:
            self.validate_positive_float(position, "Anode Terminal Connector Position")
            self._anode_terminal_connector_position = float(position)
        else:
            self._anode_terminal_connector_position = None

    @internal_height.setter
    @calculate_all_properties
    def internal_height(self, internal_height: float) -> None:
        """Set internal height and adjust canister height accordingly."""
        self.validate_positive_float(internal_height, "Internal Height")
        _current_internal_height = self._internal_height
        _asked_for_height = internal_height * MM_TO_M
        _height_difference = _asked_for_height - _current_internal_height
        new_height = self._canister._height + _height_difference
        self._canister.height = new_height * M_TO_MM
    
    def _translate_component(self, component, translation_vector: Tuple[float, float, float]):
        """Apply translation vector to a component's datum.
        
        Parameters
        ----------
        component : _PrismaticComponent
            Component to translate
        translation_vector : Tuple[float, float, float]
            Translation in meters (dx, dy, dz)
        """
        component.datum = (
            (component._datum[0] + translation_vector[0]) * M_TO_MM,
            (component._datum[1] + translation_vector[1]) * M_TO_MM,
            (component._datum[2] + translation_vector[2]) * M_TO_MM,
        )
    
    def _translate_all_components(self, translation_vector: Tuple[float, float, float]):
        """Apply translation to all encapsulation components.
        
        Parameters
        ----------
        translation_vector : Tuple[float, float, float]
            Translation in meters (dx, dy, dz)
        """
        self._translate_component(self._canister, translation_vector)
        self._translate_component(self._lid_assembly, translation_vector)
        self._translate_component(self._cathode_terminal_connector, translation_vector)
        self._translate_component(self._anode_terminal_connector, translation_vector)
    
    @datum.setter
    def datum(self, value: Tuple[float, float, float]) -> None:
        """Set datum position for the encapsulation."""
        self.validate_datum(value)
        
        if self._update_properties:
            translation_vector = (
                float(value[0]) * MM_TO_M - self._datum[0],
                float(value[1]) * MM_TO_M - self._datum[1],
                float(value[2]) * MM_TO_M - self._datum[2],
            )
            self._translate_all_components(translation_vector)
        
        self._datum = (
            float(value[0]) * MM_TO_M,
            float(value[1]) * MM_TO_M,
            float(value[2]) * MM_TO_M,
        )

    @cathode_terminal_connector.setter
    @calculate_all_properties
    def cathode_terminal_connector(self, connector: PrismaticTerminalConnector) -> None:
        """Set cathode terminal connector."""

        self.validate_type(connector, PrismaticTerminalConnector, "Cathode Terminal Connector")

        if 'cathode' not in connector.name.lower():
            connector.name = f"{connector.name} (Cathode)"

        self._cathode_terminal_connector = connector

    @anode_terminal_connector.setter
    @calculate_all_properties
    def anode_terminal_connector(self, connector: PrismaticTerminalConnector) -> None:
        """Set anode terminal connector."""

        self.validate_type(connector, PrismaticTerminalConnector, "Anode Terminal Connector")

        if 'anode' not in connector.name.lower():
            connector.name = f"{connector.name} (Anode)"
            
        self._anode_terminal_connector = connector

    @lid_assembly.setter
    @calculate_all_properties
    def lid_assembly(self, lid: PrismaticLidAssembly) -> None:
        """Set lid assembly."""
        self.validate_type(lid, PrismaticLidAssembly, "Lid Assembly")
        self._lid_assembly = lid

    @canister.setter
    @calculate_all_properties
    def canister(self, canister: PrismaticCanister) -> None:
        """Set canister."""
        self.validate_type(canister, PrismaticCanister, "Canister")
        self._canister = canister

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set outer width of the encapsulation."""
        self.validate_positive_float(width, "Width")
        self._canister.width = width

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        """Set outer length of the encapsulation."""
        self.validate_positive_float(length, "Length")
        self._canister.length = length

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        """Set total height of the encapsulation."""
        self.validate_positive_float(height, "Height")
        self._canister.height = height

