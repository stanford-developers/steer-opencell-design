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

from steer_core import (
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
)


class _CylindricalComponent(
    ABC,
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
):
    """Base class for cylindrical components with common functionality.
    
    This abstract base class provides shared functionality for cylindrical
    components including bulk property calculations, coordinate management,
    plotting capabilities, and property handling. Subclasses need only
    implement the `_calculate_footprint` method to define their specific geometry.
    
    Attributes
    ----------
    material : PrismaticContainerMaterial
        The material properties of the component
    radius : float
        Radius of the component in mm
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
        radius: float = None,
        fill_factor: float = 0.7,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Cylindrical Component",
    ):
        """Initialize a cylindrical component.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Material for the component
        thickness : float
            Thickness of the component in mm. Must be positive.
        radius : float, optional
            Radius of the component in mm. Must be positive when provided.
            If None, bulk properties and coordinates won't be calculated until set.
        fill_factor : float, default=0.7
            Fraction for material calculations.
            Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Position of component center in mm as (x, y, z) coordinates
        name : str, default="Cylindrical Component"
            Name identifier for the component
            
        Raises
        ------
        ValueError
            If fill_factor is not between 0.0 and 1.0, or if radius/thickness <= 0 when provided
        TypeError
            If material is not a PrismaticContainerMaterial instance
        """
        self._update_properties = False

        self.material = material
        self.thickness = thickness
        self.fill_factor = fill_factor
        self.datum = datum
        self.name = name
        
        # Set radius using setter (handles None and conversion)
        self.radius = radius

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate volume, mass, and cost if radius is available."""
        if self._radius is None:
            self._volume = None
            self._mass = None
            self._cost = None
            return
            
        _volume = np.pi * (self._radius) ** 2 * (self._thickness) * self._fill_factor
        _mass = _volume * self._material._density
        mass = _mass * KG_TO_G
        self._material.mass = mass

        self._mass = self._material._mass
        self._volume = self._material._volume
        self._cost = self._material._cost

    def _calculate_coordinates(self):
        """Calculate 3D coordinates if radius is available."""
        if self._radius is None:
            self._coordinates = None
            return
            
        footprint = self._calculate_footprint()
        coordinates = self._extrude_footprint(footprint)
        coordinates = self.rotate_coordinates(coordinates, axis='x', angle=90, center=self._datum)
        self._coordinates = coordinates

    def _extrude_footprint(self, footprint):

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
        """Calculate the 2D footprint of the cylindrical component.
        
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

    def _set_radius_range(self, canister: 'CylindricalCanister') -> None:
        """Set the valid radius range based on canister dimensions.
        
        Parameters
        ----------
        canister : CylindricalCanister
            The canister instance to use for determining radius constraints
        """
        self._radius_range = (0.0, canister._inner_radius)

    def get_bottom_up_plot(self, **kwargs) -> go.Figure:
        """Generate a bottom-up view plot of the component.
        
        Creates a Plotly figure showing the component profile from below,
        displaying the x-z plane cross-section.
        
        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to figure.update_layout().
            
        Returns
        -------
        go.Figure
            Interactive Plotly figure with bottom-up view
        """
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
    
    def get_top_down_plot(self, **kwargs) -> go.Figure:
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

    @property
    def coordinates(self) -> pd.DataFrame:
        """Get 3D coordinates of the component in mm."""
        if self._coordinates is None:
            return pd.DataFrame(columns=["x", "y", "z"])
            
        x = np.round(self._coordinates[:, 0] * M_TO_MM, 10)
        y = np.round(self._coordinates[:, 1] * M_TO_MM, 10)
        z = np.round(self._coordinates[:, 2] * M_TO_MM, 10)

        return pd.DataFrame(
            np.column_stack((x, y, z)),
            columns=["x", "y", "z"]
        )

    @property
    def bottom_up_trace(self) -> go.Scatter:
        """Get bottom-up view trace for plotting (x-z plane)."""
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="xz")
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["x"],
            y=coordinates["z"],
            mode="lines",
            name=self.name,
            line=dict(color="black", width=0.5),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )
    
    @property
    def top_down_trace(self) -> go.Scatter:
        """Get top-down view trace for plotting (x-y plane)."""
        coordinates = self.order_coordinates_clockwise(self.coordinates, plane="xy")
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["x"],
            y=coordinates["y"],
            mode="lines",
            name=self.name,
            line=dict(color="black", width=0.5),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, 2), 
            np.round(self._datum[1] * M_TO_MM, 2), 
            np.round(self._datum[2] * M_TO_MM, 2)
        )

    @property
    def material(self) -> PrismaticContainerMaterial:
        return self._material
    
    @property
    def radius(self) -> float:
        """Component radius in mm, rounded to 2 decimal places. None if not set."""
        if self._radius is None:
            return None
        return np.round(self._radius * M_TO_MM, 2)
    
    @property
    def radius_range(self) -> Tuple[float, float]:
        """Valid radius range in mm, rounded to 2 decimal places."""
        if not hasattr(self, '_radius_range'):
            return None
        return (
            np.round(self._radius_range[0] * M_TO_MM, 2),
            np.round(self._radius_range[1] * M_TO_MM, 2)
        )
    
    @property
    def thickness(self) -> float:
        """Component thickness in mm, rounded to 2 decimal places."""
        return np.round(self._thickness * M_TO_MM, 2)
    
    @property
    def fill_factor(self) -> float:
        """Fill factor (0.0-1.0) for material calculations."""
        return np.round(self._fill_factor, 2)
    
    @property
    def fill_factor_range(self) -> Tuple[float, float]:
        """Valid fill factor range (0.0-1.0)."""
        return (0.0, 1.0)

    @property
    def mass(self) -> float:
        """Total mass in grams, accounting for fill factor. None if radius not set."""
        if self._mass is None:
            return None
        return np.round(self._mass * KG_TO_G, 2)
    
    @property
    def mass_range(self) -> Tuple[float, float]:
        """Valid mass range in grams (0 to max with fill_factor=1.0). None if radius not set."""
        if self._radius is None:
            return None
        
        # Calculate maximum mass with fill_factor = 1.0
        _max_volume = np.pi * (self._radius) ** 2 * (self._thickness) * 1.0
        _max_mass = _max_volume * self._material._density
        max_mass = _max_mass * KG_TO_G
        
        return (0.0, np.round(max_mass, 2))
    
    @property
    def cost(self) -> float:
        """Material cost in currency units. None if radius not set."""
        if self._cost is None:
            return None
        return np.round(self._cost, 2)
    
    @property
    def volume(self) -> float:
        """Effective volume in mm³, accounting for fill factor. None if radius not set."""
        if self._volume is None:
            return None
        return np.round(self._volume * M_TO_MM**3, 2)
    
    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @material.setter
    @calculate_bulk_properties
    def material(self, material: PrismaticContainerMaterial) -> None:
        self.validate_type(material, PrismaticContainerMaterial, "Material")
        self._material = deepcopy(material)

    @radius.setter
    def radius(self, radius: float) -> None:
        """Set radius and trigger property calculations."""
        if radius is not None:
            self.validate_positive_float(radius, "Radius")
            self._radius = float(radius) * MM_TO_M
            if self._update_properties:
                self._calculate_all_properties()
        else:
            self._radius = None
            if hasattr(self, '_update_properties'):
                self._volume = None
                self._mass = None
                self._cost = None
                self._coordinates = None

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

    @mass.setter
    @calculate_bulk_properties
    def mass(self, mass: float) -> None:
        """Set mass by calculating and adjusting fill factor."""
        self.validate_positive_float(mass, "Mass")
        
        if self._radius is None:
            raise ValueError("Cannot set mass: radius is not set")
        
        # Convert mass from grams to kg
        _mass = mass * G_TO_KG
        
        # Calculate required fill factor: mass = pi * r^2 * t * fill_factor * density
        # So: fill_factor = mass / (pi * r^2 * t * density)
        _volume_without_fill = np.pi * (self._radius) ** 2 * (self._thickness)
        required_fill_factor = _mass / (_volume_without_fill * self._material._density)
        
        if required_fill_factor > 1.0:
            raise ValueError(f"Cannot achieve mass of {mass} g with current dimensions. Maximum possible mass is {np.round(_volume_without_fill * self._material._density * KG_TO_G, 2)} g")
        
        self._fill_factor = float(required_fill_factor)


class CylindricalTerminalConnector(_CylindricalComponent):
    """A cylindrical terminal connector with triangular tab cutouts.

    The CylindricalTerminalConnector creates a circular footprint with 
    triangular cutouts at the edges to accommodate terminal tabs. The main
    body maintains a circular profile while providing precise cutout 
    geometries for tab connections.

    The footprint consists of:
    - Main circular body (approximately 94.2% arc coverage)  
    - Two precise triangular cutouts positioned symmetrically
    - Closed path suitable for 3D extrusion and area calculations

    All coordinate calculations maintain millimeter precision for 
    manufacturing compatibility.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        thickness: float,
        radius: float = None,
        fill_factor: float = 0.7,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Cylindrical Terminal Connector",
    ):
        """Initialize a cylindrical terminal connector.
        
        Creates a terminal connector with circular footprint and triangular
        tab cutouts. All bulk properties and coordinates are calculated if
        radius is provided, otherwise calculations are deferred until radius
        is set.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        thickness : float
            Component thickness in mm. Must be positive.
        radius : float, optional
            Component radius in mm. Must be positive when provided.
            If None, bulk properties and coordinates won't be calculated until set.
        fill_factor : float, default=0.7
            Material density factor for calculations.
            Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Cylindrical Terminal Connector"
            Component identifier name
            
        Raises
        ------
        ValueError
            If fill_factor not in [0.0, 1.0] or radius/thickness <= 0 when provided
        TypeError
            If material is not a PrismaticContainerMaterial instance
        """
        super().__init__(material, thickness, radius, fill_factor, datum, name)
        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_footprint(self):
        """Calculate the 2D footprint of the cylindrical terminal connector.
        
        Creates a circular outline with four triangular cutouts positioned at
        diagonal angles (45°, 135°, 225°, 315°). The cutouts radiate from a
        solid center circle to the outer edge, with the total removed area
        calculated to achieve the specified fill factor.
        
        Algorithm:
        1. Define solid center radius (15% of total radius)
        2. Calculate required triangle area based on fill factor
        3. Generate circular outline with 200+ points for smoothness
        4. Apply triangular cutouts using linear interpolation
        5. Translate to datum position
        6. Ensure closed path
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
            Path is closed (first and last points are identical).
            
        Notes
        -----
        - Coordinates are in meters (internal units)
        - Solid center ensures structural integrity
        - Four triangular cutouts at diagonal positions
        - Area relationship: final_area = circle_area * fill_factor
        
        Raises
        ------
        ValueError
            If radius is not set (is None)
        """
        if self._radius is None:
            raise ValueError("Cannot calculate footprint: radius is not set")
            
        radius = self._radius
        
        # Define minimum radius for solid center (typically 10-20% of total radius)
        center_radius = radius * 0.15  # 15% of radius for solid center
        
        # Calculate triangle size based on fill factor
        # Area to remove = circle_area * (1 - fill_factor)
        # But account for the solid center area that can't be removed
        circle_area = np.pi * radius**2
        center_area = np.pi * center_radius**2
        removable_area = circle_area - center_area
        area_to_remove = min(circle_area * (1 - self._fill_factor), removable_area)
        triangle_area = area_to_remove / 4
        
        # For triangles radiating from center_radius to circle edge:
        # Triangle height = (radius - center_radius), so base = 2 * triangle_area / height
        triangle_height = radius - center_radius
        triangle_base = 2 * triangle_area / triangle_height
        triangle_half_angle = np.arctan(triangle_base / (2 * radius))  # Half angle of triangle
        
        # Create triangle cutouts at diagonal positions
        cutout_angles = [np.pi/4, 3*np.pi/4, 5*np.pi/4, 7*np.pi/4]  # 45°, 135°, 225°, 315°
        
        # Generate the footprint by tracing around the circle and cutting into triangular regions
        footprint_points = []
        n_points = 200  # Higher resolution for smooth curves
        
        for i in range(n_points + 1):
            angle = 2 * np.pi * i / n_points
            
            # Default position on circle
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Check if this angle falls within any triangular cutout
            for cutout_angle in cutout_angles:
                # Normalize angle difference to [-π, π]
                angle_diff = (angle - cutout_angle + np.pi) % (2 * np.pi) - np.pi
                
                # Check if we're within the triangular cutout region
                if abs(angle_diff) <= triangle_half_angle:
                    # Calculate distance from center for triangular cutout
                    # Linear interpolation from center_radius at center angle to radius at edge angles
                    distance_factor = abs(angle_diff) / triangle_half_angle
                    cut_radius = center_radius + (radius - center_radius) * distance_factor
                    x = cut_radius * np.cos(angle)
                    y = cut_radius * np.sin(angle)
                    break
            
            # Translate to datum position
            x += self._datum[0]
            y += self._datum[1]
            
            footprint_points.append([x, y])
        
        # Convert to numpy array
        footprint = np.array(footprint_points)
        
        # Ensure the footprint is closed (first and last points are the same)
        if not np.allclose(footprint[0], footprint[-1]):
            footprint = np.vstack([footprint, footprint[0]])

        return footprint

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Valid thickness range in mm, rounded to 2 decimal places."""
        return (0.1, 5)
    
    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Hard limits for thickness in mm, rounded to 2 decimal places."""
        return (0.05, 10)


class CylindricalLidAssembly(_CylindricalComponent):
    """A cylindrical lid assembly with circular footprint.
    
    This class represents a circular lid assembly for cylindrical containers.
    Unlike the terminal connector, the lid has a simple circular footprint
    without visible cutouts, though it still respects the fill factor for
    material calculations.
    
    The lid assembly maintains structural simplicity while allowing for
    material optimization through the fill factor parameter.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        thickness: float,
        radius: float = None,
        fill_factor: float = 0.7,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Cylindrical Lid Assembly",
    ):
        """Initialize a cylindrical lid assembly.
        
        Creates a lid assembly with simple circular footprint. All bulk 
        properties and coordinates are calculated if radius is provided, 
        otherwise calculations are deferred until radius is set.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        thickness : float
            Component thickness in mm. Must be positive.
        radius : float, optional
            Component radius in mm. Must be positive when provided.
            If None, bulk properties and coordinates won't be calculated until set.
        fill_factor : float, default=0.7
            Material density factor for calculations.
            Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Cylindrical Lid Assembly"
            Component identifier name
            
        Raises
        ------
        ValueError
            If fill_factor not in [0.0, 1.0] or radius/thickness <= 0 when provided
        TypeError
            If material is not a PrismaticContainerMaterial instance
        """
        super().__init__(material, thickness, radius, fill_factor, datum, name)
        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_footprint(self):
        """Calculate the 2D footprint of the cylindrical lid assembly.
        
        Creates a simple circular outline without any cutouts or modifications.
        The footprint is a perfect circle centered at the datum position.
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
            Path is closed (first and last points are identical).
            
        Notes
        -----
        - Coordinates are in meters (internal units)
        - Simple circular geometry without cutouts
        - Fill factor affects material calculations but not footprint shape
        
        Raises
        ------
        ValueError
            If radius is not set (is None)
        """
        if self._radius is None:
            raise ValueError("Cannot calculate footprint: radius is not set")
            
        radius = self._radius
        
        # Generate circular footprint
        footprint_points = []
        n_points = 100  # Sufficient resolution for a circle
        
        for i in range(n_points + 1):
            angle = 2 * np.pi * i / n_points
            
            # Position on circle
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Translate to datum position
            x += self._datum[0]
            y += self._datum[1]
            
            footprint_points.append([x, y])
        
        # Convert to numpy array
        footprint = np.array(footprint_points)
        
        # Ensure the footprint is closed (first and last points are the same)
        if not np.allclose(footprint[0], footprint[-1]):
            footprint = np.vstack([footprint, footprint[0]])

        return footprint

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Valid thickness range in mm, rounded to 2 decimal places."""
        return (0.5, 10)
    
    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Hard limits for thickness in mm, rounded to 2 decimal places."""
        return (0.1, 20)


class CylindricalCanister(
    CoordinateMixin, 
    SerializerMixin,
    ValidationMixin,
    PlotterMixin,
    DunderMixin
):
    """A cylindrical can with concentric circular walls.
    
    This class represents a cylindrical container with walls defined by 
    two concentric circles. The footprint shows both the outer perimeter
    and inner cavity, separated by the wall thickness. Unlike other 
    components, the radius parameter is required and cannot be None.
    
    The footprint consists of:
    - Outer circular wall at the specified radius
    - Inner circular cavity at (radius - wall_thickness)
    - Closed paths for both outer and inner boundaries
    
    The height parameter defines the vertical extent of the can,
    while wall_thickness defines the radial wall thickness.
    """

    def __init__(
        self,
        material: PrismaticContainerMaterial,
        outer_radius: float,
        height: float,
        wall_thickness: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Cylindrical Canister",
    ):
        """Initialize a cylindrical can.
        
        Creates a cylindrical can with concentric walls. The radius parameter
        is required and must be greater than the wall thickness.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Container material for physical properties
        radius : float
            Outer radius of the can in mm. Must be positive and greater than wall_thickness.
        height : float
            Height of the can in mm. Must be positive.
        wall_thickness : float
            Radial wall thickness in mm. Must be positive and less than radius.
        fill_factor : float, default=0.7
            Material density factor for calculations.
            Must be between 0.0 and 1.0.
        datum : Tuple[float, float, float], default=(0.0, 0.0, 0.0)
            Center position in mm as (x, y, z) coordinates
        name : str, default="Cylindrical Can"
            Component identifier name
            
        Raises
        ------
        ValueError
            If fill_factor not in [0.0, 1.0], radius <= 0, height <= 0, 
            wall_thickness <= 0, or wall_thickness >= radius
        TypeError
            If material is not a PrismaticContainerMaterial instance
        """
        self._update_properties = False

        self.material = material
        self.outer_radius = outer_radius
        self.height = height
        self.wall_thickness = wall_thickness
        self.datum = datum
        self.name = name

        self._update_properties = True
        self._calculate_all_properties()
        
    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        
        # get the inner radius
        self._inner_radius = self._outer_radius - self._wall_thickness
        self._inner_diameter = 2 * self._inner_radius
        self._outer_diameter = 2 * self._outer_radius

        # get the mass
        _wall_height = self._height - self._wall_thickness
        _outer_volume = np.pi * self._outer_radius**2 * _wall_height
        _inner_volume = np.pi * self._inner_radius**2 * _wall_height
        _wall_volume = _outer_volume - _inner_volume
        _base_volume = np.pi * self._outer_radius**2 * self._wall_thickness
        _volume = _wall_volume + _base_volume
        _mass = _volume * self._material._density
        mass = _mass * KG_TO_G
        self._material.mass = mass

        # set the properties
        self._mass = self._material._mass
        self._cost = self._material._cost

        # get other dimensions
        self._inner_height = self._height - self._wall_thickness

        # get the volume
        self._volume = self._height * np.pi * (self._outer_radius**2)

    def _calculate_coordinates(self):
        self._get_top_down_cross_section_coordinates()
        self._get_side_cross_section_coordinates()

    def _get_side_cross_section_coordinates(self):
        """Calculate the side cross-section coordinates showing U-shaped profile."""
        # Calculate outer diameter
        outer_diameter = 2 * self._outer_radius
        
        # Define the U-shape profile points (clockwise from bottom-left)
        # Bottom-left outer corner
        x1 = self._datum[0] - self._outer_radius
        y1 = self._datum[1]
        
        # Bottom-left inner corner  
        x2 = self._datum[0] - self._outer_radius + self._wall_thickness
        y2 = self._datum[1] + self._wall_thickness
        
        # Top-left inner corner
        x3 = self._datum[0] - self._outer_radius + self._wall_thickness
        y3 = self._datum[1] + self._height
        
        # Top-right inner corner
        x4 = self._datum[0] + self._outer_radius - self._wall_thickness
        y4 = self._datum[1] + self._height
        
        # Bottom-right inner corner
        x5 = self._datum[0] + self._outer_radius - self._wall_thickness
        y5 = self._datum[1] + self._wall_thickness
        
        # Bottom-right outer corner
        x6 = self._datum[0] + self._outer_radius
        y6 = self._datum[1]
        
        # Top-right outer corner
        x7 = self._datum[0] + self._outer_radius
        y7 = self._datum[1] + self._height
        
        # Top-left outer corner
        x8 = self._datum[0] - self._outer_radius
        y8 = self._datum[1] + self._height
        
        # Create the U-shaped profile
        x_coords = np.array([x1, x8, x3, x2, x5, x4, x7, x6, x1])  # Close the path
        y_coords = np.array([y1, y8, y3, y2, y5, y4, y7, y6, y1])  # Close the path
        
        self._side_cross_section_coordinates = np.column_stack((x_coords, y_coords))
        
    def _get_top_down_cross_section_coordinates(self):
        """Calculate the top-down view coordinates for the can."""
        x_outer, z_outer = self.build_circle_array(self._datum[0], self._datum[2], self._outer_radius)
        x_outer = np.append(x_outer, x_outer[-1])
        x_outer = np.append(x_outer[0], x_outer)
        z_outer = np.append(z_outer, z_outer[-1])
        z_outer = np.append(z_outer[0], z_outer)

        x_inner, z_inner = self.build_circle_array(self._datum[0], self._datum[2], self._inner_radius, anticlockwise=False)
        x_inner = np.append(x_inner[0], x_inner)
        x_inner = np.append(x_inner, x_inner[-1])
        z_inner = np.append(z_inner[0], z_inner)
        z_inner = np.append(z_inner, z_inner[-1])
        
        self._top_down_coordinates = np.vstack((np.column_stack((x_outer, z_outer)), np.column_stack((x_inner, z_inner))))

    def get_top_down_plot(self, **kwargs) -> go.Figure:
        """Generate a top-down view plot of the can."""
        figure = go.Figure()
        figure.add_trace(self.top_down_cross_section_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure
    
    def get_side_cross_section_plot(self, **kwargs) -> go.Figure:
        """Generate a side cross-section plot of the can."""
        figure = go.Figure()
        figure.add_trace(self.side_cross_section_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure
    
    @property
    def inner_diameter(self) -> float:
        """Inner diameter of the can in mm, rounded to 2 decimal places."""
        return np.round(self._inner_diameter * M_TO_MM, 2)
    
    @property
    def outer_diameter(self) -> float:
        """Outer diameter of the can in mm, rounded to 2 decimal places."""
        return np.round(self._outer_diameter * M_TO_MM, 2)

    @property
    def side_cross_section_coordinates(self) -> pd.DataFrame:
        """Get side cross-section coordinates of the can in mm."""
        x = np.round(self._side_cross_section_coordinates[:, 0] * M_TO_MM, 10)
        y = np.round(self._side_cross_section_coordinates[:, 1] * M_TO_MM, 10)

        return pd.DataFrame(
            np.column_stack((x, y)),
            columns=["x", "y"]
        )
    
    @property
    def side_cross_section_trace(self) -> go.Scatter:
        """Get side cross-section trace for plotting (x-y plane)."""
        coordinates = self.side_cross_section_coordinates
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["x"],
            y=coordinates["y"],
            mode="lines",
            name=self.name,
            line=dict(color="black", width=0.5),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )

    @property
    def top_down_cross_section_coordinates(self) -> pd.DataFrame:
        """Get top-down view coordinates of the can in mm."""
        x = np.round(self._top_down_coordinates[:, 0] * M_TO_MM, 10)
        y = np.round(self._top_down_coordinates[:, 1] * M_TO_MM, 10)

        return pd.DataFrame(
            np.column_stack((x, y)),
            columns=["x", "z"]
        )

    @property
    def top_down_cross_section_trace(self) -> go.Scatter:
        """Get top-down view trace for plotting (x-y plane)."""
        coordinates = self.top_down_cross_section_coordinates
        coordinates = pd.concat([coordinates, coordinates.iloc[[0]]], ignore_index=True)

        return go.Scatter(
            x=coordinates["x"],
            y=coordinates["z"],
            mode="lines",
            name=self.name,
            line=dict(color="black", width=0.5, shape="spline"),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Body",
            showlegend=True,
        )
    
    @property
    def inner_height(self) -> float:
        """Inner height of the can in mm, rounded to 2 decimal places."""
        return np.round(self._inner_height * M_TO_MM, 2)

    @property
    def cost(self) -> float:
        """Total cost of the can in currency units, rounded to 2 decimal places."""
        return np.round(self._cost, 2)

    @property
    def mass(self) -> float:
        """Total mass of the can in grams, rounded to 2 decimal places."""
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def volume(self) -> float:
        """Total volume of the can in mm³, rounded to 2 decimal places."""
        return np.round(self._volume * M_TO_MM**3, 2)

    @property
    def inner_radius(self) -> float:
        """Inner radius of the can in mm, rounded to 2 decimal places."""
        return np.round(self._inner_radius * M_TO_MM, 2)

    @property
    def inner_radius_range(self) -> Tuple[float, float]:
        outer_radius_min = self.outer_radius_range[0]
        outer_radius_max = self.outer_radius_range[1]
        wall_thickness = self.wall_thickness
        return (outer_radius_min - wall_thickness, outer_radius_max - wall_thickness)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, 2), 
            np.round(self._datum[1] * M_TO_MM, 2), 
            np.round(self._datum[2] * M_TO_MM, 2)
        )
    
    @property
    def material(self) -> PrismaticContainerMaterial:
        return self._material
    
    @property
    def outer_radius(self) -> float:
        """Outer radius of the can in mm, rounded to 2 decimal places."""
        return np.round(self._outer_radius * M_TO_MM, 2)
    
    @property
    def outer_radius_range(self) -> Tuple[float, float]:
        """Valid outer radius range in mm, rounded to 2 decimal places."""
        return (5, 80)
    
    @property
    def outer_radius_hard_range(self) -> Tuple[float, float]:
        """Hard limits for outer radius in mm, rounded to 2 decimal places."""
        return (1, 500)
    
    @property
    def height(self) -> float:
        """Height of the can in mm, rounded to 2 decimal places."""
        return np.round(self._height * M_TO_MM, 2)
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Valid height range in mm, rounded to 2 decimal places."""
        return (20, 500)

    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Hard limits for height in mm, rounded to 2 decimal places."""
        return (10, 1000)

    @property
    def inner_height_range(self) -> Tuple[float, float]:
        """Valid inner height range in mm (height_range minus wall thickness), rounded to 2 decimal places."""
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        min_height, max_height = self.height_range
        return (
            np.round(min_height - wall_thickness_mm, 2),
            np.round(max_height - wall_thickness_mm, 2)
        )

    @property
    def wall_thickness(self) -> float:
        """Wall thickness of the can in mm, rounded to 2 decimal places."""
        return np.round(self._wall_thickness * M_TO_MM, 2)
    
    @property
    def wall_thickness_range(self) -> Tuple[float, float]:
        """Valid wall thickness range in mm, rounded to 2 decimal places."""
        return (0.1, 3)

    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @material.setter
    @calculate_bulk_properties
    def material(self, material: PrismaticContainerMaterial) -> None:
        self.validate_type(material, PrismaticContainerMaterial, "Material")
        self._material = deepcopy(material)

    @outer_radius.setter
    @calculate_all_properties
    def outer_radius(self, radius: float) -> None:
        self.validate_positive_float(radius, "Outer Radius")
        self._outer_radius = float(radius) * MM_TO_M

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

    @inner_radius.setter
    def inner_radius(self, inner_radius: float) -> None:
        self.validate_positive_float(inner_radius, "Inner Radius")
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        new_outer_radius = inner_radius + wall_thickness_mm
        self.outer_radius = new_outer_radius

    @outer_diameter.setter
    def outer_diameter(self, outer_diameter: float) -> None:
        self.validate_positive_float(outer_diameter, "Outer Diameter")
        new_outer_radius = outer_diameter / 2
        self.outer_radius = new_outer_radius

    @inner_diameter.setter
    def inner_diameter(self, inner_diameter: float) -> None:
        self.validate_positive_float(inner_diameter, "Inner Diameter")
        new_inner_radius = inner_diameter / 2
        self.inner_radius = new_inner_radius

    @inner_height.setter
    def inner_height(self, inner_height: float) -> None:
        self.validate_positive_float(inner_height, "Inner Height")
        wall_thickness_mm = self._wall_thickness * M_TO_MM
        new_height = inner_height + wall_thickness_mm
        self.height = new_height


class CylindricalEncapsulation(_Container):

    def __init__(
            self,
            cathode_terminal_connector: CylindricalTerminalConnector,
            anode_terminal_connector: CylindricalTerminalConnector,
            lid_assembly: CylindricalLidAssembly,
            canister: CylindricalCanister,
            name: str = "Cylindrical Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):

        self._update_properties = False
        
        self.cathode_terminal_connector = cathode_terminal_connector
        self.anode_terminal_connector = anode_terminal_connector
        self.lid_assembly = lid_assembly
        self.canister = canister
        self.name = name
        self.datum = datum

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_coordinates(self):
        
        self._lid_assembly.datum = (
            self._datum[0] * M_TO_MM,
            (self._datum[1] + self._canister._height - self._lid_assembly._thickness / 2) * M_TO_MM ,
            self._datum[2] * M_TO_MM
        )

        self._anode_terminal_connector.datum = (
            self._datum[0] * M_TO_MM,
            (self._datum[1] + self._canister._wall_thickness + self._anode_terminal_connector._thickness / 2) * M_TO_MM,
            self._datum[2] * M_TO_MM
        )

        self._cathode_terminal_connector.datum = (
            self._datum[0] * M_TO_MM,
            (self._datum[1] + self._canister._height - self._lid_assembly._thickness - self._cathode_terminal_connector._thickness / 2) * M_TO_MM,
            self._datum[2] * M_TO_MM
        )

        _max_anode_side_coords = self._anode_terminal_connector._coordinates[:, 1].max()
        _min_cathode_side_coords = self._cathode_terminal_connector._coordinates[:, 1].min()
        _midpoint = (_max_anode_side_coords + _min_cathode_side_coords) / 2
        self._mid_y_point = _midpoint

    def _calculate_bulk_properties(self):

        self._lid_assembly.radius = self._canister._inner_radius * M_TO_MM

        if self._cathode_terminal_connector._radius is None or self._cathode_terminal_connector._radius > self._canister._inner_radius:
            self._cathode_terminal_connector.radius = self._canister._inner_radius * M_TO_MM * 0.9

        if self._anode_terminal_connector._radius is None or self._anode_terminal_connector._radius > self._canister._inner_radius:
            self._anode_terminal_connector.radius = self._canister._inner_radius * M_TO_MM * 0.9
        
        self._internal_height = (
            self._canister._height - \
            self._lid_assembly._thickness - \
            self._anode_terminal_connector._thickness - \
            self._cathode_terminal_connector._thickness
        )

        self._volume = self._canister._volume

        self._calculate_mass()
        self._calculate_cost()

    def _calculate_mass(self):

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

        fig = self.plot_breakdown_sunburst(
            self.mass_breakdown,
            title=title or f"{self.name} Mass Breakdown",
            unit="g",
            **kwargs,
        )

        return fig
    
    def plot_cost_breakdown(self, title: str = None, **kwargs) -> go.Figure:

        fig = self.plot_breakdown_sunburst(
            self.cost_breakdown,
            title=title or f"{self.name} Cost Breakdown",
            unit="currency units",
            **kwargs,
        )

        return fig
    
    def plot_side_view(self, **kwargs) -> go.Figure:
        
        figure = go.Figure()
        traces = []

        traces.append(self._canister.side_cross_section_trace)
        traces.append(self._lid_assembly.top_down_trace)
        traces.append(self._cathode_terminal_connector.top_down_trace)
        traces.append(self._anode_terminal_connector.top_down_trace)

        figure.add_traces(traces)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            title=kwargs.get("title", f"{self.name} Side View"),
            **kwargs,
        )

        return figure
    
    @property
    def volume(self) -> float:
        return np.round(self._volume * M_TO_MM**3, 2)

    @property
    def internal_height(self) -> float:
        return np.round(self._internal_height * M_TO_MM, 2)
    
    @property
    def internal_height_range(self) -> Tuple[float, float]:
        min_height = (
            self._canister.height_range[0] - 
            self._lid_assembly.thickness_hard_range[1] - 
            self._anode_terminal_connector.thickness_hard_range[1] - 
            self._cathode_terminal_connector.thickness_hard_range[1]
        )
        max_height = (
            self._canister.height_range[1] - 
            self._lid_assembly.thickness_hard_range[0] - 
            self._anode_terminal_connector.thickness_hard_range[0] - 
            self._cathode_terminal_connector.thickness_hard_range[0]
        )
        return (np.round(min_height, 2), np.round(max_height, 2))
    
    @property
    def internal_height_hard_range(self) -> Tuple[float, float]:
        min_height = (
            self._canister.height_hard_range[0] - 
            self._lid_assembly.thickness_hard_range[1] - 
            self._anode_terminal_connector.thickness_hard_range[1] - 
            self._cathode_terminal_connector.thickness_hard_range[1]
        )
        max_height = (
            self._canister.height_hard_range[1] - 
            self._lid_assembly.thickness_hard_range[0] - 
            self._anode_terminal_connector.thickness_hard_range[0] - 
            self._cathode_terminal_connector.thickness_hard_range[0]
        )
        return (np.round(min_height, 2), np.round(max_height, 2))

    @property
    def datum(self) -> Tuple[float, float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, 2), 
            np.round(self._datum[1] * M_TO_MM, 2), 
            np.round(self._datum[2] * M_TO_MM, 2)
        )
        
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def cathode_terminal_connector(self) -> CylindricalTerminalConnector:
        return self._cathode_terminal_connector
    
    @property
    def anode_terminal_connector(self) -> CylindricalTerminalConnector:
        return self._anode_terminal_connector
    
    @property
    def lid_assembly(self) -> CylindricalLidAssembly:
        return self._lid_assembly
    
    @property
    def canister(self) -> CylindricalCanister:
        return self._canister
    
    @name.setter
    def name(self, name: str) -> None:
        self.validate_type(name, str, "Name")
        self._name = name

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """

        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj, 2)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """

        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj * KG_TO_G, 2)

        return _convert_and_round_recursive(self._mass_breakdown)
    
    @property
    def radius(self) -> float:
        return self._canister.outer_radius
    
    @property
    def radius_range(self) -> Tuple[float, float]:
        return self._canister.outer_radius_range
    
    @property
    def radius_hard_range(self) -> Tuple[float, float]:
        return self._canister.outer_radius_hard_range

    @property
    def diameter(self) -> float:
        return self._canister.outer_diameter
    
    @property
    def diameter_range(self) -> Tuple[float, float]:
        min_radius, max_radius = self.radius_range
        return (min_radius * 2, max_radius * 2)
    
    @property
    def diameter_hard_range(self) -> Tuple[float, float]:
        min_radius, max_radius = self.radius_hard_range
        return (min_radius * 2, max_radius * 2)

    @property
    def height(self) -> float:
        return self._canister.height
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Valid height range in mm based on canister."""
        return self._canister.height_range
    
    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Hard limits for height in mm based on canister."""
        return self._canister.height_hard_range
    
    @internal_height.setter
    @calculate_all_properties
    def internal_height(self, internal_height: float) -> None:
        self.validate_positive_float(internal_height, "Internal Height")
        _current_internal_height = self._internal_height
        _asked_for_height = internal_height * MM_TO_M
        _height_difference = _asked_for_height - _current_internal_height
        new_height = self._canister._height + _height_difference
        self._canister.height = new_height * M_TO_MM
    
    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        self._canister.height = height
    
    @datum.setter
    @calculate_coordinates
    def datum(self, value: Tuple[float, float, float]) -> None:

        # validate input
        self.validate_datum(value)

        # set datum to self
        self._datum = tuple(coord * MM_TO_M for coord in value)

        # set the datum to the canister
        self._canister.datum = value

    @cathode_terminal_connector.setter
    @calculate_all_properties
    def cathode_terminal_connector(self, connector: CylindricalTerminalConnector) -> None:
        
        self.validate_type(connector, CylindricalTerminalConnector, "Cathode Terminal Connector")

        if 'cathode' not in connector.name.lower():
            connector.name = f"{connector.name} (Cathode)"
        
        self._cathode_terminal_connector = connector

    @anode_terminal_connector.setter
    @calculate_all_properties
    def anode_terminal_connector(self, connector: CylindricalTerminalConnector) -> None:

        self.validate_type(connector, CylindricalTerminalConnector, "Anode Terminal Connector")

        if 'anode' not in connector.name.lower():
            connector.name = f"{connector.name} (Anode)"
            
        self._anode_terminal_connector = connector

    @lid_assembly.setter
    @calculate_all_properties
    def lid_assembly(self, lid: CylindricalLidAssembly) -> None:
        self.validate_type(lid, CylindricalLidAssembly, "Lid Assembly")
        self._lid_assembly = lid

    @canister.setter
    @calculate_all_properties
    def canister(self, canister: CylindricalCanister) -> None:
        self.validate_type(canister, CylindricalCanister, "Canister")
        self._canister = canister
        
        # Set radius ranges for components based on canister dimensions
        if hasattr(self, '_cathode_terminal_connector'):
            self._cathode_terminal_connector._set_radius_range(canister)
        if hasattr(self, '_anode_terminal_connector'):
            self._anode_terminal_connector._set_radius_range(canister)
        if hasattr(self, '_lid_assembly'):
            self._lid_assembly._set_radius_range(canister)

    @radius.setter
    @calculate_all_properties
    def radius(self, radius: float) -> None:
        self.validate_positive_float(radius, "Radius")
        self._canister.outer_radius = radius

    @diameter.setter
    def diameter(self, diameter: float) -> None:
        self.radius = diameter / 2

    


