from steer_core import CoordinateMixin, PlotterMixin, ValidationMixin, DunderMixin, SerializerMixin
from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Constants.Units import *

from steer_opencell_design.Materials.Other import FlexFrameMaterial
from steer_opencell_design.Components.Containers.Base import _Container
from steer_opencell_design.Components.Containers.Pouch import PouchTerminal, LaminateSheet

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from shapely.geometry import Polygon
from typing import Tuple
from copy import deepcopy

# Precision constants
COORDINATE_PRECISION = 10
DIMENSION_PRECISION = 2

# Plotting constants
PLOT_LINE_WIDTH = 0.5
PLOT_LINE_COLOR = "black"


class FlexFrame(
    CoordinateMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
    ):
    
    def __init__(
        self,
        material: FlexFrameMaterial,
        width: float,
        height: float,
        border_thickness: float,
        thickness: float,
        cutout_height: float,
        datum: tuple = (0, 0, 0),
        name: str = "Flex Frame",
        ):
        
        """
        Flex frame container for flex frame cells.

        Parameters
        ----------
        material : FlexFrameMaterial
            Material of the flex frame.
        width : float
            Width of the flex frame in mm.
        height : float
            Height of the flex frame in mm.
        border_thickness : float
            Thickness of the flex frame border in mm.
        thickness : float
            Thickness of the flex frame in mm.
        cutout_height : float
            Height of the cutout in mm.
        datum : tuple, optional
            Datum point for coordinates calculation, by default (0, 0, 0).
        name : str, optional
            Name of the flex frame, by default "Flex Frame".
        """
        self._update_properties = False
        
        self.material = material
        self.width = width
        self.height = height
        self.border_thickness = border_thickness
        self.thickness = thickness
        self.cutout_height = cutout_height
        self.datum = datum
        self.name = name

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        self._calculate_coordinates()
        self._calculate_bulk_properties()

    def _calculate_bulk_properties(self) -> None:
        self._calculate_mass()
        self._calculate_cost()

    def _calculate_cost(self) -> None:
        self._cost = self._material._cost
        return self._cost

    def _calculate_mass(self) -> None:
        # Get outer and inner rings separately
        x_outer, y_outer = self._calculate_outer_ring()
        x_inner, y_inner = self._calculate_inner_ring()
        
        # Create polygon with hole
        outer_coords = np.column_stack((x_outer, y_outer))
        inner_coords = np.column_stack((x_inner, y_inner))
        _polygon = Polygon(outer_coords, holes=[inner_coords])
        
        _area = _polygon.area
        _volume = _area * self._thickness
        self._material.volume = _volume * M_TO_CM**3
        self._volume = _volume
        self._mass = self._material._mass
        return self._mass

    def _calculate_coordinates(self) -> None:
        footprint = self._calculate_footprint()
        x, y, z, _ = self._extrude_single_footprint(x=footprint[:, 0], y=footprint[:, 1], datum=self._datum, thickness=self._thickness)
        self._coordinates = np.column_stack((x, y, z))

    def _calculate_outer_ring(self) -> tuple[np.ndarray, np.ndarray]:
        """Calculate the outer perimeter of the flex frame with rounded corners.
        
        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            x_coords, y_coords arrays for the outer ring (closed path)
        """
        # Corner radius in meters
        corner_radius = 1.0 * MM_TO_M
        
        # Number of points per corner arc
        n_arc_points = 10
        
        # Create outer rectangle with rounded corners (clockwise from bottom-left)
        x_outer_list = []
        y_outer_list = []
        
        # Bottom edge (left to right)
        x_outer_list.append(corner_radius)
        y_outer_list.append(0)
        
        x_outer_list.append(self._width - corner_radius)
        y_outer_list.append(0)
        
        # Bottom-right corner arc
        angles = np.linspace(-np.pi/2, 0, n_arc_points)
        x_outer_list.extend(self._width - corner_radius + corner_radius * np.cos(angles))
        y_outer_list.extend(corner_radius + corner_radius * np.sin(angles))
        
        # Right edge (bottom to top)
        x_outer_list.append(self._width)
        y_outer_list.append(self._height - corner_radius)
        
        # Top-right corner arc
        angles = np.linspace(0, np.pi/2, n_arc_points)
        x_outer_list.extend(self._width - corner_radius + corner_radius * np.cos(angles))
        y_outer_list.extend(self._height - corner_radius + corner_radius * np.sin(angles))
        
        # Top edge (right to left)
        x_outer_list.append(corner_radius)
        y_outer_list.append(self._height)
        
        # Top-left corner arc
        angles = np.linspace(np.pi/2, np.pi, n_arc_points)
        x_outer_list.extend(corner_radius + corner_radius * np.cos(angles))
        y_outer_list.extend(self._height - corner_radius + corner_radius * np.sin(angles))
        
        # Left edge (top to bottom)
        x_outer_list.append(0)
        y_outer_list.append(corner_radius)
        
        # Bottom-left corner arc
        angles = np.linspace(np.pi, 3*np.pi/2, n_arc_points)
        x_outer_list.extend(corner_radius + corner_radius * np.cos(angles))
        y_outer_list.extend(corner_radius + corner_radius * np.sin(angles))
        
        # Close outer path
        x_outer_list.append(corner_radius)
        y_outer_list.append(0)
        
        return np.array(x_outer_list), np.array(y_outer_list)
    
    def _calculate_inner_ring(self) -> tuple[np.ndarray, np.ndarray]:
        """Calculate the inner cutout rectangle.
        
        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            x_coords, y_coords arrays for the inner cutout (closed path)
        """
        # Calculate cutout dimensions
        cutout_width = self._width - 2 * self._border_thickness
        
        # Inner cutout vertices (counter-clockwise to create hole)
        # Starting from bottom-left of cutout
        x_inner = np.array([
            self._border_thickness,
            self._border_thickness,
            self._border_thickness + cutout_width,
            self._border_thickness + cutout_width,
            self._border_thickness  # Close inner path
        ])
        
        y_inner = np.array([
            self._border_thickness,
            self._border_thickness + self._cutout_height,
            self._border_thickness + self._cutout_height,
            self._border_thickness,
            self._border_thickness  # Close inner path
        ])
        
        return x_inner, y_inner
    
    def _calculate_footprint(self) -> np.ndarray:
        """Calculate the 2D footprint of the flex frame with cutout.
        
        Creates a frame shape with:
        - External dimensions: width (x) by height (y)
        - Rounded corners with 1mm inner radius
        - Internal cutout: positioned border_thickness from left, right, and bottom edges
        - Cutout dimensions: (width - 2*border_thickness) by cutout_height
        - Centered so that the inner ring (cavity) center is at (0, 0)
        
        Returns
        -------
        np.ndarray
            2D footprint coordinates as (N, 2) array of [x, y] points in meters.
            Path includes outer perimeter and inner cutout (creating a hole).
        """
        # Get outer ring coordinates
        x_outer, y_outer = self._calculate_outer_ring()
        
        # Get inner ring coordinates
        x_inner, y_inner = self._calculate_inner_ring()
        
        # Calculate the center of the inner ring (cavity)
        inner_center_x = self._width / 2
        inner_center_y = self._border_thickness + self._cutout_height / 2
        
        # Translate both rings so inner ring is centered at (0, 0)
        x_outer = x_outer - inner_center_x
        y_outer = y_outer - inner_center_y
        x_inner = x_inner - inner_center_x
        y_inner = y_inner - inner_center_y
        
        # Combine both closed paths
        x_coords = np.concatenate([x_outer, x_inner])
        y_coords = np.concatenate([y_outer, y_inner])
        
        footprint = np.column_stack((x_coords, y_coords))
        
        return footprint
    
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
        # order points clockwise
        coordinates = self.coordinates.copy()

        # set a tolerance and take the values with max z 
        tolerance = 1e-6
        max_z = coordinates["Z (mm)"].max()
        coordinates = coordinates[coordinates["Z (mm)"] >= max_z - tolerance]

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
    def datum(self) -> tuple:
        return (
            np.round(self._datum[0] * M_TO_MM, DIMENSION_PRECISION),
            np.round(self._datum[1] * M_TO_MM, DIMENSION_PRECISION),
            np.round(self._datum[2] * M_TO_MM, DIMENSION_PRECISION),
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def material(self) -> FlexFrameMaterial:
        return self._material
    
    @property
    def width(self) -> float:
        return self._width * M_TO_MM
    
    @property
    def height(self) -> float:
        return self._height * M_TO_MM
    
    @property
    def border_thickness(self) -> float:
        return self._border_thickness * M_TO_MM
    
    @property
    def thickness(self) -> float:
        return self._thickness * M_TO_MM
    
    @property
    def cutout_height(self) -> float:
        return self._cutout_height * M_TO_MM
    
    @property
    def mass(self) -> float:
        return np.round(self._mass * KG_TO_G, DIMENSION_PRECISION)
    
    @property
    def volume(self) -> float:
        return np.round(self._volume * M_TO_CM**3, DIMENSION_PRECISION)
    
    @property
    def cost(self) -> float:
        return np.round(self._cost, DIMENSION_PRECISION)
    
    @datum.setter
    @calculate_coordinates
    def datum(self, datum: tuple) -> None:
        self.validate_datum(datum)
        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )
    
    @material.setter
    @calculate_all_properties
    def material(self, material: FlexFrameMaterial) -> None:
        self.validate_type(material, FlexFrameMaterial, "Material")
        self._material = material

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        self._height = float(height) * MM_TO_M

    @border_thickness.setter
    @calculate_all_properties
    def border_thickness(self, border_thickness: float) -> None:
        self.validate_positive_float(border_thickness, "Border thickness")
        self._border_thickness = float(border_thickness) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * MM_TO_M

    @cutout_height.setter
    @calculate_all_properties
    def cutout_height(self, cutout_height: float) -> None:
        self.validate_positive_float(cutout_height, "Cutout height")
        self._cutout_height = float(cutout_height) * MM_TO_M

    @name.setter
    def name(self, name: str) -> None:
        self.validate_string(name, "Name")
        self._name = name


class FlexFrameEncapsulation(_Container):

    def __init__(
        self,
        flex_frame: FlexFrame,
        laminate_sheet: LaminateSheet,
        cathode_terminal: PouchTerminal,
        anode_terminal: PouchTerminal,
        name: str = "Flex Frame Encapsulation",
        datum: tuple = (0, 0, 0)
        ):
        
        self._update_properties = False
        self._terminals_positioned = False

        self._volume = None

        self.cathode_terminal = cathode_terminal
        self.anode_terminal = anode_terminal
        self.flex_frame = flex_frame
        self.laminate_sheet = laminate_sheet
        self.name = name
        self.datum = datum

        self._update_properties = True
        self._calculate_all_properties()
        
    def _calculate_all_properties(self):
        """Calculate all properties of the pouch encapsulation."""
        self._calculate_laminates()
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate bulk properties including volume, mass, and cost."""
        self._calculate_geometry()
        self._calculate_mass()
        self._calculate_cost()

    def _calculate_geometry(self):
        """Calculate total thickness of the encapsulation."""
        self._thickness = self._laminate_sheet._thickness * 2 + self._flex_frame._thickness
        self._width = self._laminate_sheet._thickness * 2 + self._flex_frame._width
        self._height = self._laminate_sheet._thickness * 2 + self._flex_frame._height
        self._volume = self._thickness * self._width * self._height

    def _calculate_coordinates(self):
        """Calculate coordinates for all components."""
        # Position laminate relative to datum
        self._laminate_sheet.datum = (
            self._datum[0] * M_TO_MM,
            (self._datum[1] - self._flex_frame._cutout_height / 2 - self._flex_frame._border_thickness + self._flex_frame._height / 2) * M_TO_MM,
            (self._datum[2] + self._laminate_sheet._thickness / 2) * M_TO_MM
        )

        # position flex frame relative to datum
        self._flex_frame.datum = (
            self._datum[0] * M_TO_MM,
            self._datum[1] * M_TO_MM,
            (self._datum[2] + self._laminate_sheet._thickness + self._flex_frame._thickness / 2) * M_TO_MM
        )
        
    def _calculate_mass(self):
        """Calculate total mass and mass breakdown."""
        cathode_mass = self._cathode_terminal._mass
        anode_mass = self._anode_terminal._mass
        laminate_mass = sum([laminate._mass for laminate in self._laminate_sheets])
        flex_frame_mass = self._flex_frame._mass
        
        self._mass = cathode_mass + anode_mass + laminate_mass + flex_frame_mass
        
        self._mass_breakdown = {
            "Cathode Terminal": cathode_mass,
            "Anode Terminal": anode_mass,
            "Laminates": laminate_mass,
            "Flex Frame": flex_frame_mass
        }

    def _calculate_cost(self):
        """Calculate total cost and cost breakdown."""
        cathode_cost = self._cathode_terminal._cost
        anode_cost = self._anode_terminal._cost
        laminate_cost = sum([laminate._cost for laminate in self._laminate_sheets])
        flex_frame_cost = self._flex_frame._cost
        
        self._cost = cathode_cost + anode_cost + laminate_cost + flex_frame_cost
        
        self._cost_breakdown = {
            "Cathode Terminal": cathode_cost,
            "Anode Terminal": anode_cost,
            "Laminates": laminate_cost,
            "Flex Frame": flex_frame_cost
        }
    
    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Get a Plotly Figure showing the top view of the pouch encapsulation."""        
        traces = []
        traces.append(self._cathode_terminal.top_down_trace)
        traces.append(self._anode_terminal.top_down_trace)
        traces.append(self._flex_frame.top_down_trace)
        traces.append(self._laminate_sheet.top_down_trace)

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
    
    def _calculate_laminates(self):
        # create list of top and bottom laminates and side laminates
        # top and bottom laminates
        self._laminate_sheets = []
        laminate_top = deepcopy(self._laminate_sheet)
        laminate_top.height = self._flex_frame.height + self._laminate_sheet._thickness * 2 * UM_TO_M
        laminate_top.width = self._flex_frame.width + self._laminate_sheet._thickness * 2 * UM_TO_M
        self._laminate_sheets.append(laminate_top)
        self._laminate_sheets.append(deepcopy(laminate_top))

        # right and left laminates
        laminate_side = deepcopy(self._laminate_sheet)
        laminate_side.height = self._flex_frame.height + self._laminate_sheet._thickness * 2 * UM_TO_M
        laminate_side.width = self._flex_frame.thickness + self._laminate_sheet._thickness * 2 * UM_TO_M
        self._laminate_sheets.append(laminate_side)
        self._laminate_sheets.append(deepcopy(laminate_side))

        # up and down laminates
        laminate_side = deepcopy(self._laminate_sheet)
        laminate_side.height = self._flex_frame.thickness
        laminate_side.width = self._flex_frame.width
        self._laminate_sheets.append(laminate_side)
        self._laminate_sheets.append(deepcopy(laminate_side))

        return self._laminate_sheets
    
    @property
    def flex_frame(self) -> FlexFrame:
        """Flex frame component."""
        return self._flex_frame

    @property
    def thickness(self) -> float:
        """Get thickness of the encapsulation in mm."""
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
    def laminate_sheet(self) -> LaminateSheet:
        """Top laminate sheet."""
        return self._laminate_sheet

    @property
    def width(self) -> float:
        """Width of the laminate sheets in mm."""
        return round(self._width * M_TO_MM, 2)

    @property
    def height(self) -> float:
        """Height of the laminate sheets in mm."""
        return round(self._height * M_TO_MM, 2)
    
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
    
    @flex_frame.setter
    @calculate_all_properties
    def flex_frame(self, flex_frame: FlexFrame) -> None:
        """Set flex frame component."""
        self.validate_type(flex_frame, FlexFrame, "Flex Frame")
        self._flex_frame = flex_frame

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        _new_thickness = thickness * MM_TO_M
        _laminate_thickness = self._laminate_sheet._thickness
        _new_flexframe_thickness = _new_thickness - 2 * _laminate_thickness
        new_flexframe_thickness = _new_flexframe_thickness * M_TO_MM
        self._flex_frame.thickness = new_flexframe_thickness

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        _new_width = width * MM_TO_M
        _laminate_thickness = self._laminate_sheet._thickness
        _new_flexframe_width = _new_width - 2 * _laminate_thickness
        new_flexframe_width = _new_flexframe_width * M_TO_MM
        self._flex_frame.width = new_flexframe_width

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        _new_height = height * MM_TO_M
        _laminate_thickness = self._laminate_sheet._thickness
        _new_flexframe_height = _new_height - 2 * _laminate_thickness
        new_flexframe_height = _new_flexframe_height * M_TO_MM
        self._flex_frame.height = new_flexframe_height
    
    @datum.setter
    @calculate_coordinates
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

    @laminate_sheet.setter
    @calculate_all_properties
    def laminate_sheet(self, laminate: LaminateSheet) -> None:
        """Set laminate sheet."""
        self.validate_type(laminate, LaminateSheet, "Laminate Sheet")
        laminate.width = self._flex_frame.width + laminate._thickness * 2 * UM_TO_M
        laminate.height = self._flex_frame.height + laminate._thickness * 2 * UM_TO_M
        self._laminate_sheet = laminate


