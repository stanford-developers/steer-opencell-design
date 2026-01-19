from typing import Tuple

from steer_opencell_design.Components.Containers.Base import _Container
from steer_core.Constants.Units import *

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_opencell_design.Materials.Other import PrismaticContainerMaterial

from typing import Tuple
from copy import deepcopy
import numpy as np
import pandas as pd
import plotly.graph_objects as go


class LaminateSheet(
    CoordinateMixin, 
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    SerializerMixin,
    ):

    def __init__(
        self,
        areal_cost: float,
        density: float,
        thickness: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Laminate Sheet"
    ):
        """
        Initialize an object that represents a laminate sheet

        Parameters
        ----------
        areal_cost : float
            Areal cost of the laminate in $/m².
        density : float
            Density of the laminate in g/cm^3.
        thickness : float
            Thickness of the laminate in um.
        datum : Tuple[float, float, float], optional
            Reference point (x, y, z) in mm. Defaults to (0.0, 0.0, 0.0).
        name : str, optional
            Name of the laminate sheet. Defaults to 'Laminate Sheet'.
        """
        self._update_properties = False

        self._hot_pressed = False

        self.areal_cost = areal_cost
        self.density = density
        self.thickness = thickness
        self.datum = datum
        self.name = name

        # Initialize width and height as None
        self._width = None
        self._height = None

        self._calculate_all_properties()

        self._update_properties = True

    # Private functions
    def _calculate_all_properties(self):
        """
        Calculate all properties of the laminate sheet.
        This method is called when height or width is set.
        """
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """
        Calculate bulk properties of the laminate sheet.
        Only calculates if both height and width are available.
        """
        if self._height is None or self._width is None:
            self._area = None
            self._mass = None
            self._cost = None
            return

        self._area = self._height * self._width
        self._mass = self._area * self._density * self._thickness
        self._cost = self._areal_cost * self._area

    def _calculate_coordinates(self):

        if self._width is None or self._height is None:
            return
        
        self._calculate_top_down_coordinates()
        self._calculate_right_left_coordinates()
        self._calculate_bottom_up_coordinates()

    def _calculate_top_down_coordinates(self):
        
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._height / 2,
            self._width, 
            self._height
        )

        self._top_down_coordinates = np.column_stack((x, y))

        return self._top_down_coordinates

    def _generate_bucket_cross_section(self, axis: int, start: float, end: float, perpendicular_pos: float) -> np.ndarray:
        """Generate a bucket-shaped cross-section with smooth rounded corners.
        
        Creates a centerline path following the bucket profile, then extrudes it
        to create top and bottom surfaces with constant thickness.
        """
        cavity_min = self._cavity_coordinates[:, axis].min()
        cavity_max = self._cavity_coordinates[:, axis].max()

        # Determine horizontal offset for the cavity based on depth direction
        offset = self._thickness if self._cavity_depth > 0 else -self._thickness

        # Smoothing parameters
        smooth_width = max(self._thickness * 0.5, abs(self._cavity_depth) * 0.2)
        k = 8.0 / smooth_width  # steepness of sigmoid

        def sigmoid(coord_array: np.ndarray, z0: float, z1: float, center: float) -> np.ndarray:
            """Smooth transition from z0 to z1 centered at 'center'."""
            t = 1.0 / (1.0 + np.exp(-k * (coord_array - center)))
            return z0 + (z1 - z0) * t

        # Number of points per segment
        n_pts = 30

        # CENTERLINE PATH - defines the middle of the laminate sheet
        centerline_z = perpendicular_pos - self._thickness / 2
        
        # Segment 1: Left flat region
        left_flat = np.linspace(start, cavity_min - smooth_width, n_pts)
        z_left_flat = np.full(n_pts, centerline_z)

        # Segment 2: Left corner transition (rounding down into cavity)
        # Transition starts at cavity edge and ends smooth_width beyond it
        left_corner = np.linspace(cavity_min - smooth_width, cavity_min + smooth_width, n_pts)
        # Center the sigmoid at cavity_min - smooth_width/2 so transition begins at cavity edge
        z_left_corner = sigmoid(left_corner, centerline_z, centerline_z - self._cavity_depth, cavity_min - smooth_width / 2)

        # Segment 3: Cavity flat bottom (with lateral offset)
        cavity_flat = np.linspace(cavity_min + smooth_width, cavity_max - smooth_width, n_pts)
        z_cavity_flat = np.full(n_pts, centerline_z - self._cavity_depth)
        cavity_flat_offset = cavity_flat + offset / 2  # Half offset on centerline

        # Segment 4: Right corner transition (rounding up out of cavity)
        # Transition starts smooth_width before cavity edge and ends at cavity edge
        right_corner = np.linspace(cavity_max - smooth_width, cavity_max + smooth_width, n_pts)
        # Center the sigmoid at cavity_max + smooth_width/2 so transition completes at cavity edge
        z_right_corner = sigmoid(right_corner, centerline_z - self._cavity_depth, centerline_z, cavity_max + smooth_width / 2)

        # Segment 5: Right flat region
        right_flat = np.linspace(cavity_max + smooth_width, end, n_pts)
        z_right_flat = np.full(n_pts, centerline_z)

        # Assemble centerline coordinates
        centerline_coords = np.concatenate([left_flat, left_corner, cavity_flat_offset, right_corner, right_flat])
        centerline_z_all = np.concatenate([z_left_flat, z_left_corner, z_cavity_flat, z_right_corner, z_right_flat])

        # EXTRUDE: Create top and bottom surfaces by offsetting perpendicular to centerline
        # Top surface: +thickness/2 in z
        top_coords = centerline_coords.copy()
        top_z = centerline_z_all + self._thickness / 2

        # Bottom surface: -thickness/2 in z (reversed for polygon closure)
        bot_coords = centerline_coords[::-1].copy()
        bot_z = centerline_z_all[::-1] - self._thickness / 2

        # Close the polygon
        all_coords = np.concatenate([top_coords, bot_coords, [top_coords[0]]])
        all_z = np.concatenate([top_z, bot_z, [top_z[0]]])

        return np.column_stack((all_coords, all_z))

    def _calculate_right_left_coordinates(self):
        """Calculate the side cross-section coordinates (right/left view)."""
        
        if not self._hot_pressed:
            # Simple flat sheet - rectangular cross-section
            y, z = self.build_square_array(
                self._datum[1] - self._height / 2,
                self._datum[2] - self._thickness / 2,
                self._height,
                self._thickness
            )
            self._right_left_coordinates = np.column_stack((y, z))
        else:
            # Hot-pressed sheet with bucket-shaped dip
            start = self._datum[1] - self._height / 2
            end = self._datum[1] + self._height / 2
            top_z = self._datum[2] + self._thickness / 2
            
            self._right_left_coordinates = self._generate_bucket_cross_section(
                axis=1,  # y-axis
                start=start,
                end=end,
                perpendicular_pos=top_z
            )

        return self._right_left_coordinates

    def _calculate_bottom_up_coordinates(self):
        """Calculate the front/back cross-section coordinates (bottom-up view)."""
        
        if not self._hot_pressed:
            # Simple flat sheet - rectangular cross-section
            x, z = self.build_square_array(
                self._datum[0] - self._width / 2,
                self._datum[2] - self._thickness / 2,
                self._width,
                self._thickness
            )
            self._bottom_up_coordinates = np.column_stack((x, z))
        else:
            # Hot-pressed sheet with bucket-shaped dip
            start = self._datum[0] - self._width / 2
            end = self._datum[0] + self._width / 2
            top_z = self._datum[2] + self._thickness / 2
            
            self._bottom_up_coordinates = self._generate_bucket_cross_section(
                axis=0,  # x-axis
                start=start,
                end=end,
                perpendicular_pos=top_z
            )

        return self._bottom_up_coordinates
    
    @calculate_coordinates
    def _hot_press(
        self, 
        _depth: float, 
        _width: float, 
        _height: float,
        _datum: Tuple[float, float] = (0.0, 0.0)
    ) -> None:
        """Set the laminate as hot-pressed."""

        if _width > self._width or _height > self._height:
            raise ValueError("Cavity dimensions exceed laminate dimensions.")

        if _depth == 0:
            self._hot_pressed = False
            return 

        self._hot_pressed = True
        self._cavity_depth = _depth

        _cavity_x = self._datum[0] + _datum[0]
        _cavity_y = self._datum[1] + _datum[1]

        x, y = self.build_square_array(
            _cavity_x - _width / 2,
            _cavity_y - _height / 2,
            _width,
            _height
        )

        if min(y) < min(self._top_down_coordinates[:, 1]) or max(y) > max(self._top_down_coordinates[:, 1]):
            raise ValueError("Cavity height exceeds laminate height.")
        if min(x) < min(self._top_down_coordinates[:, 0]) or max(x) > max(self._top_down_coordinates[:, 0]):
            raise ValueError("Cavity width exceeds laminate width.")

        self._cavity_coordinates = np.column_stack((x, y))

    # Public functions
    def get_top_down_view(self, **kwargs):
        """Get a Plotly Figure showing the top-down view of the laminate sheet.
        
        Returns a go.Figure with the laminate sheet footprint.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_top_down_coordinates') or self._top_down_coordinates is None:
            return go.Figure()
        
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
        """Get a Plotly Figure showing the right-left (side) view of the laminate sheet.
        
        Returns a go.Figure with the laminate sheet cross-section.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_right_left_coordinates') or self._right_left_coordinates is None:
            return go.Figure()
        
        fig = go.Figure()
        fig.add_trace(self.right_left_trace)
        
        fig.update_layout(
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )
        
        return fig

    def get_bottom_up_view(self, **kwargs):
        """Get a Plotly Figure showing the bottom-up view of the laminate sheet.
        
        Returns a go.Figure with the laminate sheet cross-section.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_bottom_up_coordinates') or self._bottom_up_coordinates is None:
            return go.Figure()
        
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

    # Properties
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
    def areal_cost_range(self):
        return (0, 0.1)
    
    @property
    def areal_cost_hard_range(self):
        return (0, 1)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Get the datum position in mm."""
        return tuple(np.round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        return self._name

    @property
    def height(self) -> float:
        if self._height is None:
            return None
        return np.round(self._height * M_TO_MM, 2)
    
    @property
    def height_range(self):
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
    def density(self) -> float:
        """Density in kg/m³."""
        return np.round(self._density * KG_TO_G / M_TO_CM**3, 2)
    
    @property
    def density_range(self):
        return (0, 5)

    @property
    def thickness(self):
        return np.round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        return (0, 100)

    @property
    def top_down_coordinates(self):
        """Get the top-down coordinates in mm.
        
        Returns coordinates as a DataFrame with 'x' and 'y' columns.
        """
        if not hasattr(self, '_top_down_coordinates') or self._top_down_coordinates is None:
            return None
        
        # Perform operations on numpy array first for speed
        coords_mm = self._top_down_coordinates * M_TO_MM
        coords_rounded = np.round(coords_mm, 5)
        return pd.DataFrame(coords_rounded, columns=['X (mm)', 'Y (mm)'])

    @property
    def right_left_coordinates(self):
        """Get the right-left (side) cross-section coordinates in mm.
        
        Returns coordinates as a DataFrame with 'y' and 'z' columns.
        """
        if not hasattr(self, '_right_left_coordinates') or self._right_left_coordinates is None:
            return None
        
        # Perform operations on numpy array first for speed
        coords_mm = self._right_left_coordinates * M_TO_MM
        coords_rounded = np.round(coords_mm, 2)
        return pd.DataFrame(coords_rounded, columns=['y', 'z'])

    @property
    def bottom_up_coordinates(self):
        """Get the bottom-up cross-section coordinates in mm.
        
        Returns coordinates as a DataFrame with 'x' and 'z' columns.
        """
        if not hasattr(self, '_bottom_up_coordinates') or self._bottom_up_coordinates is None:
            return None
        
        # Perform operations on numpy array first for speed
        coords_mm = self._bottom_up_coordinates * M_TO_MM
        coords_rounded = np.round(coords_mm, 2)
        return pd.DataFrame(coords_rounded, columns=['x', 'z'])

    @property
    def right_left_trace(self):
        """Get a Plotly Scatter trace for the right-left (side) view.
        
        Returns a go.Scatter trace showing the cross-section of the laminate sheet.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_right_left_coordinates') or self._right_left_coordinates is None:
            return None
        
        coords = self.right_left_coordinates
        
        trace = go.Scatter(
            x=coords['y'],
            y=coords['z'],
            mode='lines',
            name=self._name,
            line=dict(color='rgb(128, 128, 128)', width=1),
            fill='toself',
            fillcolor='rgba(211, 211, 211, 1.0)',
            legendgroup='Laminate Sheet',
            showlegend=True,
        )
        
        return trace

    @property
    def bottom_up_trace(self):
        """Get a Plotly Scatter trace for the bottom-up view.
        
        Returns a go.Scatter trace showing the cross-section of the laminate sheet.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_bottom_up_coordinates') or self._bottom_up_coordinates is None:
            return None
        
        coords = self.bottom_up_coordinates
        
        trace = go.Scatter(
            x=coords['x'],
            y=coords['z'],
            mode='lines',
            name=self._name,
            line=dict(color='rgb(128, 128, 128)', width=1),
            fill='toself',
            fillcolor='rgba(211, 211, 211, 1.0)',
            legendgroup='Laminate Sheet',
            showlegend=True,
        )
        
        return trace

    @property
    def top_down_trace(self):
        """Get a Plotly Scatter trace for the top-down view.
        
        Returns a go.Scatter trace showing the laminate sheet footprint.
        """
        import plotly.graph_objects as go
        
        if not hasattr(self, '_top_down_coordinates') or self._top_down_coordinates is None:
            return None
        
        coords = self.top_down_coordinates
        
        trace = go.Scatter(
            x=coords['X (mm)'],
            y=coords['Y (mm)'],
            mode='lines',
            name=self._name,
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor='rgba(211, 211, 211, 1.0)',
            legendgroup='Laminate Sheet',
            showlegend=True,
        )
        
        return trace

    # Setters
    @areal_cost.setter
    @calculate_all_properties
    def areal_cost(self, areal_cost: float) -> None:
        self.validate_positive_float(areal_cost, "Areal Cost")
        self._areal_cost = float(areal_cost)

    @density.setter
    @calculate_all_properties
    def density(self, density: float) -> None:
        self.validate_positive_float(density, "Density")
        self._density = float(density) * G_TO_KG / CM_TO_M**3

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """Set the datum position in mm."""
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @name.setter
    def name(self, name: str) -> None:
        self.validate_string(name, "Name")
        self._name = name

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        self._height = float(height) * MM_TO_M

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * UM_TO_M


class PouchTerminal(
    CoordinateMixin,
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    SerializerMixin
):
    """
    A pouch terminal connector component with rectangular prismatic geometry.
    
    The PouchTerminal represents a terminal tab that extends from a pouch cell,
    typically made from metal materials like aluminum or copper. It has a 
    rectangular cross-section defined by width, length, and height.
    """

    def __init__(
        self,
        material,
        width: float,
        length: float,
        thickness: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Pouch Terminal",
    ):
        """
        Initialize a pouch terminal connector.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Material for the terminal (typically metal).
        width : float
            Width of the terminal in mm. Must be positive.
        length : float
            Length of the terminal in mm. Must be positive.
        thickness : float
            Thickness of the terminal in mm. Must be positive.
        datum : Tuple[float, float, float], optional
            Center position in mm as (x, y, z) coordinates. Defaults to (0.0, 0.0, 0.0).
        name : str, optional
            Component identifier name. Defaults to "Pouch Terminal".
            
        Raises
        ------
        ValueError
            If width, length, or thickness <= 0 when provided.
        """
        self._update_properties = False

        self.material = material
        self.width = width
        self.length = length
        self.thickness = thickness
        self.datum = datum
        self.name = name

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):
        """Calculate all properties of the terminal."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate volume, mass, and cost of the terminal."""
        # Volume in m³
        _volume = self._width * self._length * self._thickness
        volume = _volume * M_TO_CM**3
        self._material.volume = volume

        self._volume = self._material._volume
        self._mass = self._material._mass
        self._cost = self._material._cost

    def _calculate_coordinates(self):
        """Calculate the 3D coordinates of the terminal."""
        self._calculate_top_down_coordinates()
        self._calculate_right_left_coordinates()

    def _calculate_top_down_coordinates(self):
        """Calculate top-down view coordinates."""
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._length / 2,
            self._width,
            self._length
        )
        self._top_down_coordinates = np.column_stack((x, y))
        return self._top_down_coordinates

    def _calculate_right_left_coordinates(self):
        """Calculate right-left view coordinates."""
        x, z = self.build_square_array(
            self._datum[1] - self._length / 2,
            self._datum[2] - self._thickness / 2,
            self._length,
            self._thickness
        )
        self._right_left_coordinates = np.column_stack((x, z))
        return self._right_left_coordinates

    # Properties
    @property
    def right_left_coordinates(self):
        """Get the right-left coordinates in mm.
        
        Returns coordinates as a DataFrame with 'x' and 'z' columns.
        """
        # Perform operations on numpy array first for speed
        coords_mm = self._right_left_coordinates * M_TO_MM
        coords_rounded = np.round(coords_mm, 5)
        return pd.DataFrame(coords_rounded, columns=['X (mm)', 'Z (mm)'])
    
    @property
    def right_left_trace(self):
        """Get a Plotly Scatter trace for the right-left view.
        
        Returns a go.Scatter trace showing the terminal cross-section.
        """
        import plotly.graph_objects as go
        
        coords = self.right_left_coordinates
        
        trace = go.Scatter(
            x=coords['X (mm)'],
            y=coords['Z (mm)'],
            mode='lines',
            name=self._name,
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor=self._material._color,
            legendgroup='Pouch Terminal',
            showlegend=True,
        )
        
        return trace

    @property
    def volume(self) -> float:
        """Volume in cm³."""
        return np.round(self._volume * M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        """Mass in g."""
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        """Cost in $."""
        return np.round(self._cost, 2)

    @property
    def width(self) -> float:
        """Width in mm."""
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self):
        """Width range in mm."""
        return (0, 100)

    @property
    def length(self) -> float:
        """Length in mm."""
        return np.round(self._length * M_TO_MM, 2)

    @property
    def length_range(self):
        """Length range in mm."""
        return (0, 200)

    @property
    def thickness(self) -> float:
        """Thickness in mm."""
        return np.round(self._thickness * M_TO_MM, 2)

    @property
    def thickness_range(self):
        """Thickness range in mm."""
        return (0, 50)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        """Component name."""
        return self._name

    @property
    def material(self) -> PrismaticContainerMaterial:
        """Get material."""
        return self._material
    
    @property
    def top_down_coordinates(self):
        """Get the top-down coordinates in mm.
        
        Returns coordinates as a DataFrame with 'x' and 'y' columns.
        """
        # Perform operations on numpy array first for speed
        coords_mm = self._top_down_coordinates * M_TO_MM
        coords_rounded = np.round(coords_mm, 5)
        return pd.DataFrame(coords_rounded, columns=['X (mm)', 'Y (mm)'])
    
    @property
    def top_down_trace(self):
        """Get a Plotly Scatter trace for the top-down view.
        
        Returns a go.Scatter trace showing the terminal footprint.
        """
        import plotly.graph_objects as go
        
        coords = self.top_down_coordinates
        
        trace = go.Scatter(
            x=coords['X (mm)'],
            y=coords['Y (mm)'],
            mode='lines',
            name=self._name,
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor=self._material._color,
            legendgroup='Pouch Terminal',
            showlegend=True,
        )
        
        return trace

    @material.setter
    def material(self, material: PrismaticContainerMaterial) -> None:
        """Set material."""
        self._material = material

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set width in mm."""
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        """Set length in mm."""
        self.validate_positive_float(length, "Length")
        self._length = float(length) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        """Set thickness in mm."""
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * MM_TO_M

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """Set datum position in mm."""
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @name.setter
    def name(self, name: str) -> None:
        """Set component name."""
        self.validate_string(name, "Name")
        self._name = name


class PouchEncapsulation(_Container):

    def __init__(
            self,
            cathode_terminal: PouchTerminal,
            anode_terminal: PouchTerminal,
            top_laminate: LaminateSheet,
            bottom_laminate: LaminateSheet,
            width: float = None,
            height: float = None,
            thickness: float = None,
            name: str = "Pouch Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):

        self._update_properties = False
        self._terminals_positioned = False
        
        # Initialize volume to None
        self._volume = None
        
        self.cathode_terminal = cathode_terminal
        self.anode_terminal = anode_terminal
        self.top_laminate = top_laminate
        self.bottom_laminate = bottom_laminate
        self.name = name
        self.datum = datum
        
        self.width = width
        self.height = height
        self.thickness = thickness

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):
        """Calculate all properties of the pouch encapsulation."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        
        """Calculate bulk properties including volume, mass, and cost."""

        if self._top_laminate._mass is not None and self._bottom_laminate._mass is not None:
            self._calculate_mass()
        if self._top_laminate._cost is not None and self._bottom_laminate._cost is not None:
            self._calculate_cost()
        if self._top_laminate._mass is not None and self._bottom_laminate._mass is not None and self._thickness is not None and self._terminals_positioned:
            self._calculate_volume()

    def _calculate_coordinates(self):
        """Calculate coordinates for all components."""
        # Position laminates relative to datum
        # Top laminate above datum
        if self.top_laminate.width is not None and self.top_laminate.height is not None:

            self._top_laminate.datum = (
                self._datum[0] * M_TO_MM,
                self._datum[1] * M_TO_MM,
                (self._datum[2] + self._top_laminate._thickness / 2) * M_TO_MM
            )
        
        # Bottom laminate below datum
        if self.bottom_laminate.width is not None and self.bottom_laminate.height is not None:

            self._bottom_laminate.datum = (
                self._datum[0] * M_TO_MM,
                self._datum[1] * M_TO_MM,
                (self._datum[2] - self._bottom_laminate._thickness / 2) * M_TO_MM
            )

    def _calculate_mass(self):
        """Calculate total mass and mass breakdown."""
        cathode_mass = self._cathode_terminal._mass
        anode_mass = self._anode_terminal._mass
        
        top_laminate_mass = self._top_laminate._mass
        bottom_laminate_mass = self._bottom_laminate._mass
        
        self._mass = cathode_mass + anode_mass + top_laminate_mass + bottom_laminate_mass
        
        self._mass_breakdown = {
            "Cathode Terminal": cathode_mass,
            "Anode Terminal": anode_mass,
            "Laminates": top_laminate_mass + bottom_laminate_mass
        }

    def _calculate_cost(self):
        """Calculate total cost and cost breakdown."""
        cathode_cost = self._cathode_terminal._cost
        anode_cost = self._anode_terminal._cost
        
        top_laminate_cost = self._top_laminate._cost
        bottom_laminate_cost = self._bottom_laminate._cost
        
        self._cost = cathode_cost + anode_cost + top_laminate_cost + bottom_laminate_cost
        
        self._cost_breakdown = {
            "Cathode Terminal": cathode_cost,
            "Anode Terminal": anode_cost,
            "Top Laminate": top_laminate_cost,
            "Bottom Laminate": bottom_laminate_cost
        }

    def _calculate_volume(self):
        """Calculate the volume of the encapsulation."""

        if self._thickness is None or not self._terminals_positioned:
            self._volume = None
            return
        
        # aggregate the coordinates to find max width and height
        _coordinates = np.vstack((
            self._top_laminate._top_down_coordinates,
            self._bottom_laminate._top_down_coordinates,
            self._cathode_terminal._top_down_coordinates,
            self._anode_terminal._top_down_coordinates
        ))

        _max_x = np.max(_coordinates[:, 0])
        _min_x = np.min(_coordinates[:, 0])
        _max_y = np.max(_coordinates[:, 1])
        _min_y = np.min(_coordinates[:, 1])

        _width = _max_x - _min_x
        _height = _max_y - _min_y

        self._volume = _width * _height * self._thickness

    def get_side_view(self, **kwargs) -> go.Figure:
        """Get a Plotly Figure showing the side view of the pouch encapsulation."""        
        traces = []
        traces.append(self._cathode_terminal.right_left_trace)
        traces.append(self._anode_terminal.right_left_trace)
        traces.append(self._top_laminate.right_left_trace)
        traces.append(self._bottom_laminate.right_left_trace)

        fig = go.Figure(data=traces)

        # Apply layout
        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig
    
    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Get a Plotly Figure showing the top view of the pouch encapsulation."""        
        traces = []
        traces.append(self._bottom_laminate.top_down_trace)
        traces.append(self._cathode_terminal.top_down_trace)
        traces.append(self._anode_terminal.top_down_trace)
        traces.append(self._top_laminate.top_down_trace)

        fig = go.Figure(data=traces)

        # Apply layout
        fig.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return fig

    @property
    def thickness(self) -> float:
        """Get thickness of the encapsulation in mm."""
        if self._thickness is None:
            return None
        return np.round(self._thickness * M_TO_MM, 2)
    
    @property
    def volume(self) -> float:
        """Total volume in cm³."""
        if self._volume is None:
            return None
        return np.round(self._volume * M_TO_CM**3, 2)
    
    @property
    def mass(self) -> float:
        """Total mass in g."""
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        """Total cost in $."""
        return np.round(self._cost, 2)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        """Encapsulation name."""
        return self._name

    @property
    def cathode_terminal(self) -> PouchTerminal:
        """Cathode terminal component."""
        return self._cathode_terminal

    @property
    def anode_terminal(self) -> PouchTerminal:
        """Anode terminal component."""
        return self._anode_terminal

    @property
    def top_laminate(self) -> LaminateSheet:
        """Top laminate sheet."""
        return self._top_laminate

    @property
    def bottom_laminate(self) -> LaminateSheet:
        """Bottom laminate sheet."""
        return self._bottom_laminate

    @property
    def width(self) -> float:
        """Width of the laminate sheets in mm."""
        return self._top_laminate.width

    @property
    def height(self) -> float:
        """Height of the laminate sheets in mm."""
        return self._top_laminate.height

    @property
    def mass_breakdown(self) -> dict:
        """Mass breakdown by component in g."""
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj * KG_TO_G, 2)
        
        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def cost_breakdown(self) -> dict:
        """Cost breakdown by component in $."""
        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return np.round(obj, 2)
        
        return _round_recursive(self._cost_breakdown)

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        """Set thickness of both laminate sheets in mm."""
        if thickness is None:
            self._thickness = None
            return
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * MM_TO_M
    
    @datum.setter
    @calculate_all_properties
    def datum(self, value: Tuple[float, float, float]) -> None:
        """Set datum position in mm."""
        self.validate_datum(value)
        self._datum = tuple(coord * MM_TO_M for coord in value)

    @name.setter
    def name(self, name: str) -> None:
        """Set encapsulation name."""
        self.validate_string(name, "Name")
        self._name = name

    @cathode_terminal.setter
    @calculate_all_properties
    def cathode_terminal(self, terminal: PouchTerminal) -> None:
        """Set cathode terminal."""

        self.validate_type(terminal, PouchTerminal, "Cathode Terminal")

        if 'cathode' not in terminal.name.lower():
            terminal.name = f"{terminal.name} (Cathode)"

        self._cathode_terminal = terminal

    @anode_terminal.setter
    @calculate_all_properties
    def anode_terminal(self, terminal: PouchTerminal) -> None:
        """Set anode terminal."""

        self.validate_type(terminal, PouchTerminal, "Anode Terminal")

        if 'anode' not in terminal.name.lower():
            terminal.name = f"{terminal.name} (Anode)"

        self._anode_terminal = terminal

    @top_laminate.setter
    @calculate_all_properties
    def top_laminate(self, laminate: LaminateSheet) -> None:
        """Set top laminate sheet."""
        self.validate_type(laminate, LaminateSheet, "Top Laminate")
        self._top_laminate = laminate

    @bottom_laminate.setter
    @calculate_all_properties
    def bottom_laminate(self, laminate: LaminateSheet) -> None:
        """Set bottom laminate sheet."""
        self.validate_type(laminate, LaminateSheet, "Bottom Laminate")
        self._bottom_laminate = laminate

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set width of both laminate sheets in mm."""
        if width is None:
            self._width = None
            return
        self.validate_positive_float(width, "Width")
        self._top_laminate.width = width
        self._bottom_laminate.width = width

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        """Set height of both laminate sheets in mm."""
        if height is None:
            self._height = None
            return
        self.validate_positive_float(height, "Height")
        self._top_laminate.height = height
        self._bottom_laminate.height = height



