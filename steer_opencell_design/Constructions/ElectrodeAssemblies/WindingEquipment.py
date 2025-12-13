from copy import deepcopy
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Tuple


class _Mandrel(
    SerializerMixin,
    ValidationMixin,
    DunderMixin,
    CoordinateMixin,
    PlotterMixin
):
    
    def __init__(
            self, 
            length: float,
            datum: Tuple[float, float, float] = (0, 0, 0),
            material: CurrentCollectorMaterial = None,
            name: str = "Mandrel"
        ):

        self._update_properties = False

        self.length = length
        self.datum = datum
        self.material = material
        self.name = name

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        pass

    def _calculate_coordinates(self):
        pass

    def get_top_down_view(self, **kwargs) -> go.Figure:

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

    def get_bottom_up_view(self, **kwargs) -> go.Figure:

        figure = go.Figure()
        figure.add_trace(self.bottom_up_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def name(self) -> str:
        return self._name

    @property
    def material(self) -> CurrentCollectorMaterial:
        return self._material

    @property
    def coordinates(self) -> pd.DataFrame:
        return pd.DataFrame(
            self._coordinates,
            columns=["x", "y", "z"],
        ).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
        )
    
    @property
    def top_down_trace(self) -> go.Scatter:
        
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane='xy')
        
        # Add the first row to the end to close the circle
        if len(coordinates) > 0:
            first_row = coordinates.iloc[0:1].copy()
            coordinates = pd.concat([coordinates, first_row], ignore_index=True)
        
        # make the coated area trace
        trace = go.Scatter(
            x=coordinates["x"],
            y=coordinates["y"],
            mode="lines",
            name=self.name,
            line=dict(width=1, color="black"),
            fillcolor=self.material.color,
            fill="toself"
        )

        return trace

    @property
    def bottom_up_trace(self) -> go.Scatter:
        
        # Get only the first circle (first half of coordinates) for bottom-up view
        coords_df = (
            self
            .coordinates
            .query('y == y.min()')
        )
        
        # Order the circle coordinates clockwise
        first_circle_ordered = self.order_coordinates_clockwise(coords_df, plane='xz')

        # copy first row to end to close the circle
        first_row = first_circle_ordered.iloc[0:1].copy()
        first_circle_ordered = pd.concat([first_circle_ordered, first_row], ignore_index=True)

        # make the coated area trace using x and z coordinates (bottom-up view)
        trace = go.Scatter(
            x=first_circle_ordered["x"],
            y=first_circle_ordered["z"],  # Use z coordinate as y-axis for bottom-up view
            mode="lines",
            name=self.name,
            line=dict(width=1, color="black", shape="spline", smoothing=1.3),
            fillcolor=self.material.color,
            fill="toself"
        )

        return trace

    @name.setter
    def name(self, value: str):
        self.validate_string(value, "name")
        self._name = value

    @material.setter
    def material(self, value: CurrentCollectorMaterial):

        if value is None:
            self._material = CurrentCollectorMaterial.from_database("Aluminum")

        else:
            self.validate_type(value, CurrentCollectorMaterial, "material")
            self._material = deepcopy(value)

    @property
    def length(self) -> float:
        """Return the mandrel length in mm."""
        return np.round(self._length * M_TO_MM, 2)

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
    
    @datum.setter
    @calculate_coordinates
    def datum(self, value: Tuple[float, float, float]):
        
        self._datum = (
            np.round(value[0] * MM_TO_M, 6),
            np.round(value[1] * MM_TO_M, 6),
            np.round(value[2] * MM_TO_M, 6),
        )

    @length.setter
    @calculate_coordinates
    def length(self, value: float):
        self._length = np.round(value * MM_TO_M, 6)


class RoundMandrel(_Mandrel):

    def __init__(
            self, 
            diameter: float, 
            length: float, 
            datum: Tuple[float, float, float] = (0, 0, 0),
            material = None, 
            name = "Mandrel"
        ):

        super().__init__(
            length, datum, material, name
        )

        self.diameter = diameter

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_bulk_properties(self):
        self._radius = self._diameter / 2

    def _calculate_coordinates(self):
        """
        Calculate the 3D coordinates of the mandrel as two circles in the xz-plane.
        The circles are separated by the mandrel length along the y-axis.
        """
        # Parameters for coordinate generation
        n_circumferential = 32  # Number of points around circumference
        
        # Generate angular positions around circumference (include endpoint to close circle)
        theta = np.linspace(0, 2 * PI, n_circumferential + 1, endpoint=True)
        
        # Define the two y positions for the circles (start and end of mandrel)
        y_start = -self._length / 2
        y_end = self._length / 2
        
        # Create coordinate arrays
        coordinates = []
        
        # Generate coordinates for the first circle (at y_start)
        for t in theta:
            x = (self._diameter / 2) * np.cos(t)
            z = (self._diameter / 2) * np.sin(t)
            coordinates.append([
                x + self._datum[0],       # X position + datum offset
                y_start + self._datum[1], # Y position + datum offset  
                z + self._datum[2]        # Z position + datum offset
            ])
        
        # Generate coordinates for the second circle (at y_end)
        for t in theta:
            x = (self._diameter / 2) * np.cos(t)
            z = (self._diameter / 2) * np.sin(t)
            coordinates.append([
                x + self._datum[0],     # X position + datum offset
                y_end + self._datum[1], # Y position + datum offset  
                z + self._datum[2]      # Z position + datum offset
            ])
        
        # Convert to numpy array
        self._coordinates = np.array(coordinates)
        
        return self._coordinates

    @property
    def radius(self) -> float:
        """Return the mandrel radius in mm."""
        return np.round(self._radius * M_TO_MM, 2)

    @property
    def radius_range(self) -> Tuple[float, float]:
        """Return the mandrel radius range as a tuple (min, max) in mm."""
        return (self.diameter_range[0] / 2, self.diameter_range[1] / 2)

    @property
    def diameter(self) -> float:
        """Return the mandrel diameter in mm."""
        return np.round(self._diameter * M_TO_MM, 2)

    @property
    def diameter_range(self) -> Tuple[float, float]:
        """Return the mandrel diameter range as a tuple (min, max) in mm."""
        return (1, 50)

    @radius.setter
    def radius(self, value: float):
        self.diameter = value * 2

    @diameter.setter
    @calculate_all_properties
    def diameter(self, value: float):
        self._diameter = np.round(value * MM_TO_M, 6)


class FlatMandrel(_Mandrel):
    
    def __init__(
            self, 
            length: float,
            width: float,
            height: float,
            datum: Tuple[float, float, float] = (0, 0, 0),
            material: CurrentCollectorMaterial = None,
            name: str = "Flat Mandrel"
        ):

        super().__init__(
            length, datum, material, name
        )

        self.width = width
        self.height = height

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_bulk_properties(self):
        self._radius = self._height / 2
        self._straight_length = self._width - self._height

    def _calculate_coordinates(self):
        """
        Calculate the 3D coordinates of the flat mandrel with a racetrack profile.
        Top view (x,y): rectangular (width x length)
        Cross-section (x,z): racetrack with flat middle and rounded ends
        """
        # Parameters for coordinate generation
        n_circumferential = 16  # Points per semicircle
        n_straight = 8  # Points along straight sections
        
        # Calculate geometry
        radius = self._height / 2
        straight_length = self._width - self._height  # Flat section length
        
        coordinates = []
        
        # Generate y positions (length direction) - two cross-sections
        y_positions = [-self._length / 2, self._length / 2]
        
        for y_pos in y_positions:
            # Generate racetrack profile in x-z plane
            profile_coords = []
            
            # Right semicircle (positive x side)
            center_x_right = straight_length / 2
            theta_right = np.linspace(-np.pi/2, np.pi/2, n_circumferential + 1)
            for t in theta_right:
                x = center_x_right + radius * np.cos(t)
                z = radius * np.sin(t)
                profile_coords.append([x, z])
            
            # Top straight section
            x_straight_top = np.linspace(straight_length / 2, -straight_length / 2, n_straight + 1)[1:-1]  # Exclude endpoints
            for x in x_straight_top:
                profile_coords.append([x, radius])
            
            # Left semicircle (negative x side)
            center_x_left = -straight_length / 2
            theta_left = np.linspace(np.pi/2, 3*np.pi/2, n_circumferential + 1)
            for t in theta_left:
                x = center_x_left + radius * np.cos(t)
                z = radius * np.sin(t)
                profile_coords.append([x, z])
            
            # Bottom straight section
            x_straight_bottom = np.linspace(-straight_length / 2, straight_length / 2, n_straight + 1)[1:-1]  # Exclude endpoints
            for x in x_straight_bottom:
                profile_coords.append([x, -radius])
            
            # Add all profile coordinates with current y position and datum offset
            for x, z in profile_coords:
                coordinates.append([
                    x + self._datum[0],        # X position + datum offset
                    y_pos + self._datum[1],    # Y position + datum offset
                    z + self._datum[2]         # Z position + datum offset
                ])
        
        # Convert to numpy array
        self._coordinates = np.array(coordinates)
        
        return self._coordinates

    @property
    def radius(self) -> float:
        """Return the mandrel radius (half of height) in mm."""
        return np.round(self._radius * M_TO_MM, 2)

    @property
    def straight_length(self) -> float:
        """Return the straight segment length in mm."""
        return np.round(self._straight_length * M_TO_MM, 2)

    @property
    def width(self) -> float:
        """Return the mandrel width in mm."""
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self) -> Tuple[float, float]:
        """Return the mandrel width range as a tuple (min, max) in mm."""
        return (1, 100)

    @property
    def height(self) -> float:
        """Return the mandrel height in mm."""
        return np.round(self._height * M_TO_MM, 2)
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Return the mandrel height range as a tuple (min, max) in mm."""
        return (1, 30)

    @width.setter
    @calculate_all_properties
    def width(self, value: float):
        self.validate_positive_float(value, "width")
        self._width = np.round(value * MM_TO_M, 6)

    @height.setter
    @calculate_all_properties
    def height(self, value: float):
        self.validate_positive_float(value, "height")
        self._height = np.round(value * MM_TO_M, 6)

    @radius.setter
    @calculate_all_properties
    def radius(self, value: float):
        self.validate_positive_float(value, "radius")
        self._height = value * MM_TO_M * 2

        