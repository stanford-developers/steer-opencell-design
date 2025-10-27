from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial

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
        self._calculate_coordinates()
        self._calculate_bulk_properties()

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
            self._material = value

    @property
    def length(self) -> float:
        """Return the mandrel length in mm."""
        return round(self._length * M_TO_MM, 2)

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
    
    @datum.setter
    @calculate_coordinates
    def datum(self, value: Tuple[float, float, float]):
        
        self._datum = (
            round(value[0] * MM_TO_M, 6),
            round(value[1] * MM_TO_M, 6),
            round(value[2] * MM_TO_M, 6),
        )

    @length.setter
    @calculate_coordinates
    def length(self, value: float):
        self._length = round(value * MM_TO_M, 6)


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
        return round(self._radius * M_TO_MM, 2)

    @property
    def diameter(self) -> float:
        """Return the mandrel diameter in mm."""
        return round(self._diameter * M_TO_MM, 2)

    @radius.setter
    @calculate_coordinates
    def radius(self, value: float):
        self._diameter = value * MM_TO_M * 2

    @diameter.setter
    @calculate_coordinates
    def diameter(self, value: float):
        self._diameter = round(value * MM_TO_M, 6)


class FlatMandrel(_Mandrel):
    
    def __init__(
            self, 
            length: float,
            long_diameter: float,
            short_diameter: float,
            datum: Tuple[float, float, float] = (0, 0, 0),
            material: CurrentCollectorMaterial = None,
            name: str = "Flat Mandrel"
        ):

        super().__init__(
            length, datum, material, name
        )

        self.long_diameter = long_diameter
        self.short_diameter = short_diameter

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_bulk_properties(self):
        self._long_radius = self._long_diameter / 2
        self._short_radius = self._short_diameter / 2

    def _calculate_coordinates(self):
        """
        Calculate the 3D coordinates of the flat mandrel as two ellipses in the xz-plane.
        The ellipses are separated by the mandrel length along the y-axis.
        """
        # Parameters for coordinate generation
        n_circumferential = 128  # Number of points around circumference
        
        # Generate angular positions around circumference (include endpoint to close ellipse)
        theta = np.linspace(0, 2 * PI, n_circumferential + 1, endpoint=True)
        
        # Define the two y positions for the ellipses (start and end of mandrel)
        y_start = -self._length / 2
        y_end = self._length / 2
        
        # Semi-major and semi-minor axes
        a = self._long_diameter / 2   # Semi-major axis (x-direction)
        b = self._short_diameter / 2  # Semi-minor axis (z-direction)
        
        # Create coordinate arrays
        coordinates = []
        
        # Generate coordinates for the first ellipse (at y_start)
        for t in theta:
            x = a * np.cos(t)
            z = b * np.sin(t)
            coordinates.append([
                x + self._datum[0],       # X position + datum offset
                y_start + self._datum[1], # Y position + datum offset  
                z + self._datum[2]        # Z position + datum offset
            ])
        
        # Generate coordinates for the second ellipse (at y_end)
        for t in theta:
            x = a * np.cos(t)
            z = b * np.sin(t)
            coordinates.append([
                x + self._datum[0],     # X position + datum offset
                y_end + self._datum[1], # Y position + datum offset  
                z + self._datum[2]      # Z position + datum offset
            ])
        
        # Convert to numpy array
        self._coordinates = np.array(coordinates)
        
        return self._coordinates

    @property
    def long_radius(self) -> float:
        """Return the mandrel long radius in mm."""
        return round(self._long_radius * M_TO_MM, 2)

    @property
    def short_radius(self) -> float:
        """Return the mandrel short radius in mm."""
        return round(self._short_radius * M_TO_MM, 2)

    @property
    def long_diameter(self) -> float:
        """Return the mandrel long diameter in mm."""
        return round(self._long_diameter * M_TO_MM, 2)

    @property
    def short_diameter(self) -> float:
        """Return the mandrel short diameter in mm."""
        return round(self._short_diameter * M_TO_MM, 2)

    @long_diameter.setter
    @calculate_coordinates
    def long_diameter(self, value: float):
        self._long_diameter = round(value * MM_TO_M, 6)

    @short_diameter.setter
    @calculate_coordinates
    def short_diameter(self, value: float):
        self._short_diameter = round(value * MM_TO_M, 6)

    @long_radius.setter
    @calculate_coordinates
    def long_radius(self, value: float):
        self._long_diameter = value * MM_TO_M * 2

    @short_radius.setter
    @calculate_coordinates
    def short_radius(self, value: float):
        self._short_diameter = value * MM_TO_M, 6

        