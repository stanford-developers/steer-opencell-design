from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial

from SteerEnergyStorage.Utils import get_area_from_points, build_square_array, rotate_coordinates, order_coordinates_clockwise
from SteerEnergyStorage.Constants import *
from App.styles import *

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Iterable, Dict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from copy import deepcopy
from pickle import dumps, loads
import base64
import numpy as np
import time


class _CurrentCollector(ABC):
    """
    Abstract base class for current collectors.
    """
    def __init__(
            self, 
            material: CurrentCollectorMaterial,
            x_body_length: float,
            y_body_length: float,
            thickness: float,
            insulation_width: Optional[float] = 0,
            datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
            name: Optional[str] = 'Current Collector',
            **kwargs
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

        self.datum = datum
        self.material = material
        self.x_body_length = x_body_length
        self.y_body_length = y_body_length
        self.thickness = thickness
        self.insulation_width = insulation_width
        self.name = name

        # Shading patterns
        self._a_am_fill_pattern = dict(shape='/', size=20, solidity=0.6, fgcolor=self._material._color)
        self._b_am_fill_pattern = dict(shape='\\', size=20, solidity=0.6, fgcolor=self._material._color)
        self._a_in_fill_pattern = dict(shape='\\', size=10, solidity=0.6, fgcolor=self._material._color)
        self._b_in_fill_pattern = dict(shape='/', size=10, solidity=0.6, fgcolor=self._material._color)

    def _calculate_coordinates(self) -> None:

        self._get_body_coordinates()
        self._get_a_side_coated_coordinates()
        self._get_b_side_coated_coordinates()
        self._get_a_side_insulation_coordinates()
        self._get_b_side_insulation_coordinates()

    def _calculate_areas(self) -> None:

        # calculate the area of the a side
        body_a_side_area = get_area_from_points(
            self._body_coordinates[self._body_coordinates_side == 'a'][:,0],
            self._body_coordinates[self._body_coordinates_side == 'a'][:,1]
        )

        # calculate the total upper and lower area of the body
        self._body_area = body_a_side_area * 2

        # calculate the area of the a side coated area
        self._a_side_coated_area = get_area_from_points(
            self._a_side_coated_coordinates[:, 0],
            self._a_side_coated_coordinates[:, 1]
        )

        # calculate the area of the b side coated area
        self._b_side_coated_area = get_area_from_points(
            self._b_side_coated_coordinates[:, 0],
            self._b_side_coated_coordinates[:, 1]
        )

        self._coated_area = self._a_side_coated_area + self._b_side_coated_area

        # calculate the area of the a side insulation area
        self._a_side_insulation_area = get_area_from_points(
            self._a_side_insulation_coordinates[:, 0],
            self._a_side_insulation_coordinates[:, 1]
        )

        # calculate the area of the b side insulation area
        self._b_side_insulation_area = get_area_from_points(
            self._b_side_insulation_coordinates[:, 0],
            self._b_side_insulation_coordinates[:, 1]
        )

        self._insulation_area = self._a_side_insulation_area + self._b_side_insulation_area

    def _calculate_bulk_properties(self) -> None:
        self._volume = self._body_area/2 * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost     

    def _calculate_all_properties(self) -> None:

        self._calculate_coordinates()
        self._calculate_areas()
        self._calculate_bulk_properties()

    def _extrude_footprint(
            self, 
            x: np.ndarray, 
            y: np.ndarray
        ) -> Tuple[
            np.ndarray, 
            np.ndarray, 
            np.ndarray, 
            np.ndarray
        ]:
        """
        Extrude the 2D footprint to 3D and label each point with its side ('a' or 'b').

        Parameters
        ----------
        x : np.ndarray
            Array of x coordinates (length N)
        y : np.ndarray
            Array of y coordinates (length N)

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            Arrays of x, y, z, and side for both A and B sides (each of length 2N)
        """
        z_a = self._datum[2] + self._thickness / 2
        z_b = self._datum[2] - self._thickness / 2

        # Repeat x and y coordinates for both sides
        x_full = np.concatenate([x, x])
        y_full = np.concatenate([y, y])
        z_full = np.concatenate([np.full_like(x, z_a), np.full_like(x, z_b)])
        side_full = np.array(['a'] * len(x) + ['b'] * len(x))

        return x_full, y_full, z_full, side_full

    def _get_end_trace(self) -> go.Scatter:
        
        coordinates = build_square_array(
            x=self._datum[1] - self._y_body_length / 2,
            y=self._datum[2] - self._thickness / 2,
            x_width=self._y_body_length,
            y_width=self._thickness
        )

        trace = go.Scatter(
            x=coordinates['x'], 
            y=coordinates['y'], 
            mode='lines', 
            name='End', 
            line=dict(width=0.5, color='black'), 
            fillcolor=self._material._color, 
            fill='toself'
        )

        return trace

    def _get_full_top_down_view(self, with_dimensions: bool = False, **kwargs) -> go.Figure:

        # initiate figure
        fig = go.Figure()

        # get the side with the maximum z value
        body_coordinates = self.body_coordinates.query('z == z.max()')

        # make the body trace
        body_trace = go.Scatter(
            x=body_coordinates['x'],
            y=body_coordinates['y'],
            mode='lines',
            name='Body',
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor=self._material.color,
            legendgroup='Body',
            showlegend=True
        )

        # figure out which side that is
        side = body_coordinates['side'].values[0]

        # get the coordinates for the coated area and insulation area
        if side == 'a':
            coated_area_coordinates = self.a_side_coated_coordinates
            insulation_area_coordinates = self.a_side_insulation_coordinates
        else:
            coated_area_coordinates = self.b_side_coated_coordinates
            insulation_area_coordinates = self.b_side_insulation_coordinates

        # make the coated area trace
        coated_area_trace = go.Scatter(
            x=coated_area_coordinates['x'], 
            y=coated_area_coordinates['y'], 
            mode='lines', 
            name='A Side Coated Area' if side == 'a' else 'B Side Coated Area', 
            line=dict(width=1, color='black'), 
            fillcolor='black', 
            fill='toself', 
            fillpattern=self._a_am_fill_pattern if side == 'a' else self._b_am_fill_pattern,
        )

        # make the insulation area trace
        insulation_area_trace = go.Scatter(
            x=insulation_area_coordinates['x'],
            y=insulation_area_coordinates['y'],
            mode='lines',
            name='A Side Insulation Area' if side == 'a' else 'B Side Insulation Area',
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor='white',
            legendgroup='Insulation Area',
            showlegend=True,
            fillpattern=self._a_in_fill_pattern if side == 'a' else self._b_in_fill_pattern,
        )

        # add traces to the figure
        fig.add_trace(body_trace)
        fig.add_trace(coated_area_trace)
        fig.add_trace(insulation_area_trace)

        if with_dimensions:
            fig = self._add_dimensions(fig=fig)

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='X (mm)'),
            yaxis=dict(showgrid=False, zeroline=False, title='Y (mm)'),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return fig

    def _get_body_coordinates(self) -> go.Scatter:
        x, y = self._get_footprint(notch_height=self._tab_height)
        x, y, z, side = self._extrude_footprint(x, y)
        self._body_coordinates = np.column_stack((x, y, z))
        self._body_coordinates_side = side

    def _get_a_side_coated_coordinates(self) -> Tuple[go.Scatter, float]:
        self._a_side_coated_coordinates = self._get_coated_area_coordinates(side='a')

    def _get_b_side_coated_coordinates(self) -> Tuple[go.Scatter, float]:
        self._b_side_coated_coordinates = self._get_coated_area_coordinates(side='b')

    def _get_a_side_insulation_coordinates(self) -> go.Scatter:
        self._a_side_insulation_coordinates = self._get_insulation_coordinates(side='a')

    def _get_b_side_insulation_coordinates(self) -> go.Scatter:
        self._b_side_insulation_coordinates = self._get_insulation_coordinates(side='b')

    def get_a_side_view(self, **kwargs) -> go.Figure:

        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == 'a'].mean()
        z_b = z_coords[self._body_coordinates_side == 'b'].mean()

        top_side = 'a' if z_a > z_b else 'b'

        if top_side == 'a':
            return self.get_top_down_view(**kwargs)
        else:
            self.flip('y')
            figure = self.get_top_down_view(**kwargs)
            self.flip('y')
            return figure

    def get_b_side_view(self, **kwargs) -> go.Figure:

        z_coords = self._body_coordinates[:, 2]
        z_a = z_coords[self._body_coordinates_side == 'a'].mean()
        z_b = z_coords[self._body_coordinates_side == 'b'].mean()

        top_side = 'a' if z_a > z_b else 'b'

        if top_side == 'b':
            return self.get_top_down_view(**kwargs)
        else:
            self.flip('y')
            figure = self.get_top_down_view(**kwargs)
            self.flip('y')
            return figure

    def flip(self, axis: str) -> pd.DataFrame:
        """
        Function to rotate the current collector around a specified axis by 180 degrees.

        Parameters
        ----------
        axis : str
            The axis to rotate around. Must be 'x', 'y', or 'z'.
        """
        if axis not in ['x', 'y']:
            raise ValueError("Axis must be 'x' or 'y'.")

        axis_map = {
            'x': 'y',
            'y': 'x',
        }

        rotation_axis = axis_map[axis]

        # shift the datum to the origin
        old_datum = self._datum
        self._datum = (0, 0, 0)

        # rotate the coordinates around the specified axis
        self._body_coordinates = rotate_coordinates(self._body_coordinates, rotation_axis, 180)
        self._a_side_coated_coordinates = rotate_coordinates(self._a_side_coated_coordinates, rotation_axis, 180)
        self._b_side_coated_coordinates = rotate_coordinates(self._b_side_coated_coordinates, rotation_axis, 180)
        self._a_side_insulation_coordinates = rotate_coordinates(self._a_side_insulation_coordinates, rotation_axis, 180)
        self._b_side_insulation_coordinates = rotate_coordinates(self._b_side_insulation_coordinates, rotation_axis, 180)

        # shift the datum back to its original position
        self._datum = old_datum

        return self

    def get_end_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the end view of the punched current collector.
        The end view is a rectangle representing the end of the current collector.
        """
        body_coordinates = order_coordinates_clockwise(self.body_coordinates, plane='yz')
        a_side_coated_coordinates = order_coordinates_clockwise(self.a_side_coated_coordinates, plane='yz')
        b_side_coated_coordinates = order_coordinates_clockwise(self.b_side_coated_coordinates, plane='yz')
        a_side_insulation_coordinates = order_coordinates_clockwise(self.a_side_insulation_coordinates, plane='yz')
        b_side_insulation_coordinates = order_coordinates_clockwise(self.b_side_insulation_coordinates, plane='yz')

        names = [
            'Body',
            'A Side Coated',
            'B Side Coated',
            'A Side Insulation',
            'B Side Insulation'
        ]

        fill_colors = [
            self._material.color,
            'black',
            'black',
            'white',
            'white'
        ]

        fill_patterns = [
            None,
            self._a_am_fill_pattern,
            self._b_am_fill_pattern,
            self._a_in_fill_pattern,
            self._b_in_fill_pattern
        ]

        figure = go.Figure()
        for co, name, fill_color, fill_pattern in zip([body_coordinates, a_side_coated_coordinates, b_side_coated_coordinates, a_side_insulation_coordinates, b_side_insulation_coordinates], names, fill_colors, fill_patterns):

            trace = go.Scatter(
                x=co['y'],
                y=co['z'],
                mode='lines',
                line=dict(width=1, color='black'),
                fill='toself',
                fillcolor=fill_color,
                fillpattern=fill_pattern,
                showlegend=True,
                name=name
            )

            figure.add_trace(trace)

        figure.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False, scaleanchor="y"),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure
    
    def pickle(self) -> bytes:
        """
        Serialize the current collector object to bytes.
        """
        pickled = dumps(self)
        based = base64.b64encode(pickled).decode('utf-8')
        return based

    @abstractmethod
    def _get_coated_area_coordinates(self, side: str = 'a') -> np.ndarray:
        """
        Get the coordinates of the coated area for a given side ('a' or 'b').
        """
        pass

    @abstractmethod
    def _get_insulation_coordinates(self, side: str = 'a') -> np.ndarray:
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
    def datum(self) -> Tuple[float, float, float]:
        """
        Get the datum of the current collector.
        """
        return (
            round(self._datum[0] * M_TO_MM, 2),
            round(self._datum[1] * M_TO_MM, 2),
            round(self._datum[2] * M_TO_MM, 2)
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
    def datum_x_marks(self) -> Dict[int, str]:
        """
        Get the x-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_x_range[0])
        max_datum = np.floor(self.datum_x_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

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
    def datum_y_marks(self) -> Dict[int, str]:
        """
        Get the y-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_y_range[0])
        max_datum = np.floor(self.datum_y_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

    @property
    def datum_z(self) -> float:
        """
        Get the z-coordinate of the datum in mm.
        """
        return round(self._datum[2] * M_TO_MM, 2)

    @property
    def datum_z_range(self) -> Tuple[float, float]:
        """
        Get the z-coordinate range of the datum in mm.
        """
        return (-100, 100)
    
    @property
    def datum_z_marks(self) -> Dict[int, str]:
        """
        Get the z-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_z_range[0])
        max_datum = np.floor(self.datum_z_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """
        Set the datum, converting mm to m.
        """
        if not isinstance(datum, tuple) or len(datum) != 3:
            raise TypeError("Datum must be a tuple of three floats, (x, y, z).")
        
        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("All coordinates in datum must be numbers.")
        
        self._datum = (
            float(datum[0]) * MM_TO_M, 
            float(datum[1]) * MM_TO_M, 
            float(datum[2]) * MM_TO_M
        )

        if self._update_properties:
            self._calculate_coordinates()

    @datum_x.setter
    def datum_x(self, x: float) -> None:
        """
        Set the x-coordinate of the datum, converting mm to m.
        """
        self.datum = (
            x,
            self.datum_y,
            self.datum_z
        )

    @datum_y.setter
    def datum_y(self, y: float) -> None:
        """
        Set the y-coordinate of the datum, converting mm to m.
        """
        self.datum = (
            self.datum_x,
            y,
            self.datum_z
        )

    @datum_z.setter
    def datum_z(self, z: float) -> None:
        """
        Set the z-coordinate of the datum, converting mm to m.
        """
        self.datum = (
            self.datum_x,
            self.datum_y,
            z
        )

    @property
    def material(self) -> CurrentCollectorMaterial:
        """
        Get the material of the current collector.
        """
        return self._material
    
    @material.setter
    def material(self, material: CurrentCollectorMaterial) -> None:

        if not isinstance(material, CurrentCollectorMaterial):
            raise TypeError("Material must be an instance of CurrentCollectorMaterial.")
        
        self._material = material

        if self._update_properties:
            self._calculate_bulk_properties()

    @property
    def x_body_length(self) -> float:
        return round(self._x_body_length * M_TO_MM, 2)
    
    @x_body_length.setter
    def x_body_length(self, x_body_length: float) -> None:

        if not isinstance(x_body_length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if x_body_length <= 0:
            raise ValueError("Length cannot be negative or equal to 0.")
        
        self._x_body_length = float(x_body_length) * MM_TO_M

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def y_body_length(self) -> float:
        return round(self._y_body_length * M_TO_MM, 2)
    
    @y_body_length.setter
    def y_body_length(self, y_body_length: float) -> None:

        if not isinstance(y_body_length, (int, float)):
            raise TypeError("Length must be a number.")

        if y_body_length <= 0:
            raise ValueError("Length cannot be negative or equal to 0.")

        self._y_body_length = float(y_body_length) * MM_TO_M

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)
    
    @thickness.setter
    def thickness(self, thickness: float) -> None:

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")

        if thickness <= 0:
            raise ValueError("Thickness cannot be negative or equal to 0.")
        
        self._thickness = float(thickness) * UM_TO_M

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def thickness_range(self):
        min = 1e-6
        max = 20e-6
        return (round(min * M_TO_UM, 2), round(max * M_TO_UM, 2))

    @property
    def thickness_marks(self) -> Dict[int, str]:
        """
        Get the thickness marks for the slider.
        """
        min_thickness = np.ceil(self.thickness_range[0])
        max_thickness = np.floor(self.thickness_range[1])
        return {i: '' for i in range(int(min_thickness), int(max_thickness) + 1, 10)}

    @property
    def insulation_width(self) -> float:
        return round(self._insulation_width * M_TO_MM, 2)

    @insulation_width.setter
    def insulation_width(self, insulation_width: float) -> None:

        if not isinstance(insulation_width, (int, float)):
            raise TypeError("Insulation width must be a number.")

        if insulation_width < 0:
            raise ValueError("Insulation width cannot be negative.")

        self._insulation_width = float(insulation_width) * MM_TO_M

        if self._update_properties:
            self._calculate_coordinates()
            self._calculate_areas()

    @property
    def insulation_width_range(self) -> Tuple[float, float]:
        """
        Get the insulation width range in mm.
        """
        min = 0
        max = self._y_body_length / 2 - 0.001
        
        return (
            round(min * M_TO_MM, 1), 
            round(max * M_TO_MM, 1)
            )

    @property
    def insulation_width_marks(self) -> Dict[int, str]:
        """
        Get the insulation width marks for the slider.
        """
        min_insulation = np.ceil(self.insulation_width_range[0])
        max_insulation = np.floor(self.insulation_width_range[1])
        return {i: '' for i in range(int(min_insulation), int(max_insulation) + 1, 10)}

    @property
    def name(self) -> str:
        """
        Get the name of the current collector.
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set the name of the current collector.
        """
        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        
        self._name = name

    @property
    def properties(self) -> dict:
        """
        Get the properties of the current collector.
        """
        return {
            'Mass': f"{self.mass} g",
            'Cost': f"{self.cost} $",
            'Total single sided area': f"{self.body_area} cm²",
            'Total coated area': f"{self.coated_area} cm²",
            'Total insulation area': f"{self.insulation_area} cm²"
        }

    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_CM**2, 1)

    @property
    def coated_area_range(self):

        return (
            round(0 * M_TO_CM**2, 1), 
            round(self._body_area * M_TO_CM**2, 1)
        )

    @property
    def coated_area_marks(self) -> Dict[int, str]:
        """
        Get the coated area marks for the slider.
        """
        min_coated = np.ceil(self.coated_area_range[0])
        max_coated = np.floor(self.coated_area_range[1])
        return {i: '' for i in range(int(min_coated), int(max_coated) + 1, 1000)}

    @property
    def insulation_area_range(self):

        return (
            round(0 * M_TO_CM**2, 1), 
            round(self._body_area * M_TO_CM**2, 1)
        )

    @property
    def insulation_area_marks(self) -> Dict[int, str]:
        """
        Get the insulation area marks for the slider.
        """
        min_insulation = np.ceil(self.insulation_area_range[0])
        max_insulation = np.floor(self.insulation_area_range[1])
        return {i: '' for i in range(int(min_insulation), int(max_insulation) + 1, 1000)}

    @property
    def a_side_coated_area(self) -> float:
        return round(self._a_side_coated_area * M_TO_CM**2, 2)
    
    @property
    def a_side_coated_coordinates(self) -> pd.DataFrame:
        """
        Get the A side coated coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._a_side_coated_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'] * M_TO_MM).round(10),
                y = lambda x: (x['y'] * M_TO_MM).round(10),
                z = lambda x: (x['z'] * M_TO_MM).round(10)
            )
        ) 

    @property
    def b_side_coated_area(self) -> float:
        return round(self._b_side_coated_area * M_TO_CM**2, 2)

    @property
    def b_side_coated_coordinates(self) -> pd.DataFrame:
        """
        Get the B side coated coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._b_side_coated_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'] * M_TO_MM).round(10),
                y = lambda x: (x['y'] * M_TO_MM).round(10),
                z = lambda x: (x['z'] * M_TO_MM).round(10)
            )
        )

    @property
    def body_area(self) -> float:
        return round(self._body_area * M_TO_CM**2, 2)

    @property
    def body_coordinates(self) -> pd.DataFrame:
        
        return pd.DataFrame(
            np.column_stack((self._body_coordinates, self._body_coordinates_side)),
            columns=['x', 'y', 'z', 'side']
        ).assign(
            x=lambda df: (df['x'].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df['y'].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df['z'].astype(float) * M_TO_MM).round(10),
            side=lambda df: df['side'].astype(str)
        )

    @property
    def a_side_insulation_area(self) -> float:
        return round(self._a_side_insulation_area * M_TO_CM**2, 2)

    @property
    def a_side_insulation_coordinates(self) -> pd.DataFrame:
        """
        Get the A side insulation coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._a_side_insulation_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'] * M_TO_MM).round(10),
                y = lambda x: (x['y'] * M_TO_MM).round(10),
                z = lambda x: (x['z'] * M_TO_MM).round(10)
            ).astype(
                {'x': float, 'y': float, 'z': float}
            )
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
            pd.DataFrame(
                self._b_side_insulation_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'] * M_TO_MM).round(10),
                y = lambda x: (x['y'] * M_TO_MM).round(10),
                z = lambda x: (x['z'] * M_TO_MM).round(10)
            ).astype(
                {'x': float, 'y': float, 'z': float}
            )
        )

    @property
    def insulation_area(self) -> float:
        return round(self._insulation_area * M_TO_CM**2, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def mass_marks(self) -> Dict[int, str]:
        min_mass = self.mass_range[0]
        max_mass = self.mass_range[1]
        delta = 10
        num_steps = int(round((max_mass - min_mass) / delta)) + 1
        values = np.linspace(min_mass, max_mass, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @property
    def cost(self) -> float:
        return round(self._cost, 3)
    
    @property
    def cost_range(self):
        min = 0
        max = self._cost + (1/self._cost)/20
        return (min, max)

    @property
    def cost_marks(self) -> Dict[int, str]:
        min_cost = self.cost_range[0]
        max_cost = self.cost_range[1]
        delta = 0.1
        num_steps = int(round((max_cost - min_cost) / delta)) + 1
        values = np.linspace(min_cost, max_cost, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @property
    def width_range(self) -> Tuple[float, float]:
        min = 0.03
        max = 1
        return (
            round(min * M_TO_MM, 2), 
            round(max * M_TO_MM, 2)
        )

    @property
    def width_marks(self) -> Dict[int, str]:
        min_width = np.ceil(self.width_range[0])
        max_width = np.floor(self.width_range[1])
        return {i: '' for i in range(int(min_width), int(max_width) + 1, 30)}

    def __str__(self):
        return f"{self.__class__.__name__}"
    
    def __repr__(self):
        return self.__str__()


class _TabbedCurrentCollector(_CurrentCollector):
    """
    A class representing a tabbed current collector.
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
            name: Optional[str] = 'Tabbed Current Collector',
            datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
            **kwargs
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
            **kwargs
        )
        
        self.tab_width = tab_width
        self.tab_height = tab_height
        self.coated_tab_height = coated_tab_height
        self._total_height = self._y_body_length + self._tab_height

    def _get_coated_area_coordinates(self, side: str) -> np.ndarray:
        """
        Return coated area coordinates for the specified side as a regular NumPy array [x, y, z].
        """
        if side not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_coat_end = self._y_body_length + self._coated_tab_height - self._insulation_width

        if _y_coat_end > self._y_body_length:
            notch = self._coated_tab_height - self._insulation_width
            y_depth = self._y_body_length
        else:
            notch = 0
            y_depth = _y_coat_end

        # Get x, y coordinates as separate 1D arrays
        if hasattr(self, '_bare_lengths_a_side') or hasattr(self, '_bare_lengths_b_side'):
            initial_skip_coat = self._bare_lengths_a_side[0] if side == 'a' else self._bare_lengths_b_side[0]
            final_skip_coat = self._bare_lengths_a_side[1] if side == 'a' else self._bare_lengths_b_side[1]
            x_start = self._datum[0] - self._x_body_length / 2 + initial_skip_coat
            x_end = self._datum[0] + self._x_body_length / 2 - final_skip_coat
            x, y = self._get_footprint(
                notch_height=notch,
                y_depth=y_depth,
                x_start=x_start,
                x_end=x_end
            )
        else:
            x, y = self._get_footprint(
                notch_height=notch, 
                y_depth=y_depth
            )  # each of shape (N,)

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

    @tab_width.setter
    def tab_width(self, tab_width: float) -> None:

        if not isinstance(tab_width, (int, float)):
            raise TypeError("Tab width must be a number.")

        if tab_width < 0:
            raise ValueError("Tab width cannot be negative.")

        self._tab_width = float(tab_width) * MM_TO_M

        if self._tab_width > self._x_body_length:
            raise ValueError("Tab width cannot be greater than the length of the current collector.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        
        min = 0.01
        max = 0.5
        
        return (
            round(min * M_TO_MM, 2), 
            round(max * M_TO_MM, 2)
        )

    @property
    def tab_width_marks(self) -> Dict[int, str]:
        """
        Get the tab width marks for the slider.
        """
        min_tab_width = np.ceil(self.tab_width_range[0])
        max_tab_width = np.floor(self.tab_width_range[1])
        return {i: '' for i in range(int(min_tab_width), int(max_tab_width) + 1, 40)}

    @property
    def tab_height(self) -> float:
        return round(self._tab_height * M_TO_MM, 2)

    @tab_height.setter
    def tab_height(self, tab_height: float) -> None:

        if not isinstance(tab_height, (int, float)):
            raise TypeError("Tab height must be a number.")

        if tab_height < 0:
            raise ValueError("Tab height cannot be negative.")

        self._tab_height = float(tab_height) * MM_TO_M

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def tab_height_range(self) -> Tuple[float, float]:

        min = 0.01
        max = self._y_body_length / 4 - 0.01

        return (
            round(min * M_TO_MM, 1), 
            round(max * M_TO_MM, 1)
        )

    @property
    def tab_height_marks(self) -> Dict[int, str]:
        """
        Get the tab height marks for the slider.
        """
        min_tab_height = np.ceil(self.tab_height_range[0])
        max_tab_height = np.floor(self.tab_height_range[1])
        return {i: '' for i in range(int(min_tab_height), int(max_tab_height) + 1, 40)}

    @property
    def coated_tab_height(self) -> float:
        return round(self._coated_tab_height * M_TO_MM, 2)

    @coated_tab_height.setter
    def coated_tab_height(self, coated_tab_height: float) -> None:

        if not isinstance(coated_tab_height, (int, float)):
            raise TypeError("Covered tab height on the top side must be a number.")

        if coated_tab_height < 0:
            raise ValueError("Covered tab height on the top side cannot be negative.")

        self._coated_tab_height = float(coated_tab_height) * MM_TO_M

        if self._coated_tab_height > self._tab_height:
            raise ValueError("Covered tab height on the top side cannot be greater than the tab height.")
        
        if self._update_properties:
            self._calculate_coordinates()
            self._calculate_areas()

    @property
    def coated_tab_height_range(self) -> Tuple[float, float]:

        min = 0
        max = self._tab_height / 2 - 0.1*MM_TO_M

        return (
            round(min * M_TO_MM, 1), 
            round(max * M_TO_MM, 1)
        )

    @property
    def coated_tab_height_marks(self) -> Dict[int, str]:
        """
        Get the coated tab height marks for the slider.
        """
        min_coated_tab_height = np.ceil(self.coated_tab_height_range[0])
        max_coated_tab_height = np.floor(self.coated_tab_height_range[1])
        return {i: '' for i in range(int(min_coated_tab_height), int(max_coated_tab_height) + 1, 5)}

    @property
    def total_height(self) -> float:
        return round(self._total_height * M_TO_MM, 2)

    @property
    def tab_position(self) -> float:
        return round(self._tab_position * M_TO_MM, 1)

    @tab_position.setter
    def tab_position(self, tab_position: float) -> None:

        if not isinstance(tab_position, (int, float)):
            raise TypeError("Tab position must be a number.")
        
        self._tab_position = float(tab_position) * MM_TO_M
        
        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")
        
        if self._tab_position + self._tab_width / 2 > self.x_body_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")
        
        if self._update_properties:
            self._calculate_coordinates()

    @property
    def tab_position_range(self) -> Tuple[float, float]:
        min = self._tab_width/2 + 0.1*MM_TO_M
        max = self._x_body_length - self._tab_width/2 - 0.1*MM_TO_M
        return (round(min * M_TO_MM, 1), round(max * M_TO_MM, 1))

    @property
    def tab_position_marks(self) -> Dict[int, str]:
        """
        Get the tab position marks for the slider.
        """
        min_tab_position = np.ceil(self.tab_position_range[0])
        max_tab_position = np.floor(self.tab_position_range[1])
        return {i: '' for i in range(int(min_tab_position), int(max_tab_position) + 1, 40)}


class _TapeCurrentCollector(_CurrentCollector):
    """
    Abstract base class for tape current collectors.
    """
    def __init__(
            self,
            material: CurrentCollectorMaterial,
            x_body_length: float,
            y_body_length: float,
            thickness: float,
            bare_lengths_a_side: Tuple[float, float] = (0,0),
            bare_lengths_b_side: Tuple[float, float] = (0,0),
            insulation_width: Optional[float] = 0,
            name: Optional[str] = 'Tape Current Collector',
            datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
            **kwargs
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
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'Length: {self.length} mm')
            xmin = self._datum[0] + self._x_body_length / 2 - aspect_ratio * self._y_body_length
            xmax = self._datum[0] + self._x_body_length / 2
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'\u00A0')
        else:
            xmin = self._datum[0] - self._x_body_length / 2
            xmax = xmin + self._x_body_length
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'Length: {self.length} mm')

        return fig

    def _add_height_dimension(self, fig: go.Figure, pad: float = 0.05) -> go.Figure:

        # Height line
        x = self._datum[0] - self._x_body_length / 2 - pad * self._y_body_length
        ymin = self._datum[1] - self._y_body_length / 2
        ymax = ymin + self._y_body_length
        ymid = (ymin + ymax) / 2
        fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=-12, text=f'Height: {self.y_body_length} mm', textangle=-90)

        return fig

    def get_top_down_view(
        self, 
        aspect_ratio: float = 3, 
        side: str = 'a',
        with_dimensions: bool = True, 
        **kwargs
    ) -> go.Figure:
        """
        Visualize the notched current collector.
        If the collector is long, split into two subplots for left and right ends with split indicators.
        The vertical datum is centered at y = self.width / 2.
        
        :param aspect_ratio: float: aspect ratio of the plot, default is 3
        :param side: str: 'a' or 'b' to indicate which side to visualize
        :param with_dimensions: bool: whether to add dimensions to the plot, default is True
        """
        if side not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")

        max_x = self.y_body_length * aspect_ratio

        figure = self._get_full_top_down_view(with_dimensions=with_dimensions, **kwargs)

        if max_x < self.x_body_length:

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

            if with_dimensions:
                orig = figure.layout.annotations or []
                for ann in orig:
                    props = ann.to_plotly_json()
                    # Remove the old axis references
                    for key in ('xref', 'yref', 'axref', 'ayref'):
                        props.pop(key, None)

                    # Re-add annotations for each subplot
                    for row in (1, 2):
                        suffix = '' if row == 1 else '2'
                        props['xref'] = f'x{suffix}'
                        props['yref'] = f'y{suffix}'
                        if props.get('showarrow', False):
                            props['axref'] = props['xref']
                            props['ayref'] = props['yref']
                        figure_subplot.add_annotation(row=row, col=1, **props)

            top_row_range = [
                (self.datum[0] - self.x_body_length / 2) - 300, 
                self.datum[0] - self.x_body_length / 2 + max_x
            ]

            bottom_row_range = [
                self.datum[0] + self.x_body_length / 2 - max_x, 
                self.datum[0] + self.x_body_length / 2 + 300
            ]

            # Set x-axis ranges
            figure_subplot.update_xaxes(range=top_row_range, row=1, col=1)
            figure_subplot.update_xaxes(range=bottom_row_range, row=2, col=1)

            # Set y-axis ranges to match the aspect ratio
            y_range = [
                self.datum[1] - self.y_body_length / 2,
                self.datum[1] + self.y_body_length / 2
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
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='X (mm)'),
            yaxis=dict(showgrid=False, zeroline=False, title='Y (mm)'),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure

    @property
    def bare_lengths_a_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_a_side)
    
    @bare_lengths_a_side.setter
    def bare_lengths_a_side(self, bare_lengths_a_side: Iterable[float]) -> None:

        if not isinstance(bare_lengths_a_side, tuple) or len(bare_lengths_a_side) != 2:
                raise TypeError("Bare lengths on A side must be a tuple of two floats.")
            
        if any(not isinstance(length, (int, float)) for length in bare_lengths_a_side):
            raise TypeError("Bare lengths on A side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_a_side):
            raise ValueError("Bare lengths on A side cannot be negative.")
        
        self._bare_lengths_a_side = tuple(float(length) * MM_TO_M for length in bare_lengths_a_side)

        if self._x_body_length < sum(self._bare_lengths_a_side):
            raise ValueError("Total bare lengths on A side cannot be greater than the length of the current collector.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def bare_lengths_b_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_b_side)

    @bare_lengths_b_side.setter
    def bare_lengths_b_side(self, bare_lengths_b_side: Iterable[float]) -> None:

        if not isinstance(bare_lengths_b_side, tuple) or len(bare_lengths_b_side) != 2:
            raise TypeError("Bare lengths on B side must be a tuple of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in bare_lengths_b_side):
            raise TypeError("Bare lengths on B side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_b_side):
            raise ValueError("Bare lengths on B side cannot be negative.")
        
        self._bare_lengths_b_side = tuple(float(length) * MM_TO_M for length in bare_lengths_b_side)

        if self._x_body_length < sum(self._bare_lengths_b_side):
            raise ValueError("Total bare lengths on B side cannot be greater than the length of the current collector.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def a_side_coated_section(self):
        """
        Property inidcating the length of the current collector that is coated on the A side. Given as a tuple, with the first float being the start point along the tape of the 
        coated area, and the second float being the end point along the tape of the coated area.
        """
        return (
            round(self._bare_lengths_a_side[0] * M_TO_MM, 1),
            round((self._x_body_length - self._bare_lengths_a_side[1]) * M_TO_MM, 1)
        )
    
    @property
    def a_side_coated_section_range(self) -> Tuple[float, float]:
        """
        Get the range of the A side coated section in mm.
        """
        return (0, self.x_body_length)
    
    @property
    def a_side_coated_section_marks(self) -> Dict[int, str]:
        """
        Get the A side coated section markers for the slider.
        """
        min_section = np.ceil(self.a_side_coated_section_range[0])
        max_section = np.floor(self.a_side_coated_section_range[1])
        return {i: '' for i in range(int(min_section), int(max_section) + 1, 500)}

    @a_side_coated_section.setter
    def a_side_coated_section(self, section: Tuple[float, float]) -> None:
        """
        Set the A side coated section.
        
        Parameters:
        ----------
        section: Tuple[float, float]
            A tuple containing the start and end points of the coated section along the tape in mm.
        """
        if not isinstance(section, (tuple, list)) or len(section) != 2:
            raise TypeError("A side coated section must be a tuple or list of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in section):
            raise TypeError("A side coated section must contain numbers.")
        
        if any(length < 0 for length in section):
            raise ValueError("A side coated section cannot have negative values.")
        
        self._bare_lengths_a_side = (
            float(section[0]) * MM_TO_M,
            self._x_body_length - float(section[1]) * MM_TO_M
        )
        
        if self._update_properties:
            self._calculate_all_properties()
    
    @property
    def b_side_coated_section(self):
        """
        Property inidcating the length of the current collector that is coated on the B side. Given as a tuple, with the first float being the start point along the tape of the 
        coated area, and the second float being the end point along the tape of the coated area.
        """
        return (
            round(self._bare_lengths_b_side[0] * M_TO_MM, 1),
            round((self._x_body_length - self._bare_lengths_b_side[1]) * M_TO_MM, 1)
        )

    @property
    def b_side_coated_section_range(self) -> Tuple[float, float]:
        """
        Get the range of the B side coated section in mm.
        """
        return (0, self.x_body_length)

    @property
    def b_side_coated_section_marks(self) -> Dict[int, str]:
        """
        Get the B side coated section markers for the slider.
        """
        min_section = np.ceil(self.b_side_coated_section_range[0])
        max_section = np.floor(self.b_side_coated_section_range[1])
        return {i: '' for i in range(int(min_section), int(max_section) + 1, 500)}

    @b_side_coated_section.setter
    def b_side_coated_section(self, section: Tuple[float, float]) -> None:
        """
        Set the B side coated section.

        Parameters:
        ----------
        section: Tuple[float, float]
            A tuple containing the start and end points of the coated section along the tape in mm.
        """
        if not isinstance(section, (tuple, list)) or len(section) != 2:
            raise TypeError("B side coated section must be a tuple or list of two floats.")

        if any(not isinstance(length, (int, float)) for length in section):
            raise TypeError("B side coated section must contain numbers.")

        if any(length < 0 for length in section):
            raise ValueError("B side coated section cannot have negative values.")

        self._bare_lengths_b_side = (
            float(section[0]) * MM_TO_M,
            self._x_body_length - float(section[1]) * MM_TO_M
        )

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def length(self) -> float:
        return self.x_body_length
    
    @length.setter
    def length(self, length: float) -> None:

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if length <= 0:
            raise ValueError("Length cannot be negative or equal to 0.")
        
        self.x_body_length = length

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def length_range(self) -> Tuple[float, float]:
        """
        Get the length range in mm.
        """
        return (0, 8000)

    @property
    def length_marks(self) -> Dict[int, str]:
        min_length = np.ceil(self.length_range[0])
        max_length = np.floor(self.length_range[1])
        return {i: '' for i in range(int(min_length), int(max_length) + 1, 500)}

    @property
    def mass_marks(self) -> Dict[int, str]:
        min_mass = self.mass_range[0]
        max_mass = self.mass_range[1]
        delta = 100
        num_steps = int(round((max_mass - min_mass) / delta)) + 1
        values = np.linspace(min_mass, max_mass, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @property
    def width(self) -> float:
        return self.y_body_length
    
    @width.setter
    def width(self, width: float) -> None:

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width <= 0:
            raise ValueError("Width cannot be negative or equal to 0.")
        
        self.y_body_length = width

    @property
    def mass_range(self) -> Tuple[float, float]:

        min = 0
        hyp_max = 1
        max = hyp_max * (1 - np.exp(-0.5/self._mass))

        return (
            round(min * KG_TO_G, 2), 
            round(max * KG_TO_G, 2)
        )


        
class PunchedCurrentCollector(_TabbedCurrentCollector):
    """
    A class representing a punched current collector used in z-fold and flat sheet cells
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
            name: Optional[str] = 'Punched Current Collector',
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
            datum=datum
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

        x_steps = np.array([
            0,
            tab_pos - tab_width / 2,
            0,
            tab_width,
            0,
            x_len - tab_pos - tab_width / 2,
            0,
            -x_len
        ])

        y_steps = np.array([
            y_depth,
            0,
            notch_height,
            0,
            -notch_height,
            0,
            -y_depth,
            0
        ])

        # Cumulative sum to get coordinates
        x_coords = np.cumsum(np.insert(x_steps, 0, start_x))
        y_coords = np.cumsum(np.insert(y_steps, 0, start_y))

        return x_coords, y_coords

    def _add_dimensions(self, fig: go.Figure, pad: float = 0.05) -> go.Figure:

        # width line
        xmin = self._datum[0] - self._x_body_length / 2
        xmax = xmin + self._x_body_length
        xmid = (xmin + xmax) / 2
        y = self._datum[1] - self._y_body_length/2 - pad * self._y_body_length
        fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'Width: {self.x_body_length} mm')

        # height line
        x = self._datum[0] - self._x_body_length / 2 - pad * self._x_body_length
        ymin = self._datum[1] - self._y_body_length / 2
        ymax = ymin + self._y_body_length
        ymid = (ymin + ymax) / 2
        fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=-12, text=f'Height: {self.y_body_length} mm', textangle=-90)

        # tab position line
        y = self._datum[1] - self._y_body_length/2 + self._y_body_length + self._tab_height + (3 * pad * self._y_body_length)
        xmin = self._datum[0] - self._x_body_length / 2
        xmax = xmin + self._tab_position
        xmid = (xmin + xmax) / 2
        fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Position: {self.tab_position} mm')           

        # tab width line
        y = self._datum[1] - self._y_body_length/2 + self._y_body_length + self._tab_height + (pad * self._y_body_length)
        xmin = self._datum[0] - self._x_body_length/2 + self._tab_position - self._tab_width / 2
        xmax = xmin + self._tab_width
        xmid = (xmin + xmax) / 2
        fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Width: {self.tab_width} mm')

        # tab height line 
        if self._tab_position > self._x_body_length / 2:
            x = self._datum[0] - self._x_body_length/2 + self._tab_position - self._tab_width / 2 - (pad * self._x_body_length)
            xshift = -80
        else:
            x = self._datum[0] - self._x_body_length/2 + self._tab_position + self._tab_width / 2 + (pad * self._x_body_length)
            xshift = 80
        
        ymin = self._datum[1] + self._y_body_length/2
        ymax = ymin + self._tab_height
        ymid = (ymin + ymax) / 2
        fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=xshift, text=f'Tab Height: {self.tab_height} mm')

        return fig

    def _get_insulation_coordinates(self, side: str) -> np.ndarray:
        """
        Returns a NumPy array representing the insulation area.
        The shape depends on whether the insulation is entirely above, below,
        or straddling the body length. Output columns are ['x', 'y', 'z', 'side'].
        """
        if side not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_insulation_start = (
            self._datum[1]
            + self._y_body_length / 2
            + self._coated_tab_height
            - self._insulation_width
        )
        _y_insulation_end = _y_insulation_start + self._insulation_width

        # Determine which case applies
        if _y_insulation_start > self._datum[1] + self._y_body_length / 2:
            x0 = self._datum[0] - self._x_body_length / 2 + self._tab_position - self._tab_width / 2
            y0 = _y_insulation_start

            x, y = build_square_array(
                x=x0,
                y=y0,
                x_width=self._tab_width,
                y_width=self._insulation_width
            )

        elif round(_y_insulation_end, 10) <= round(self._datum[1] + self._y_body_length / 2, 10):
            x0 = self._datum[0] - self._x_body_length / 2
            y0 = _y_insulation_start

            x, y = build_square_array(
                x=x0,
                y=y0,
                x_width=self._x_body_length,
                y_width=self._insulation_width
            )

        else:
            notch_height = _y_insulation_end - (self._datum[1] + self._y_body_length / 2)
            y_depth = (self._datum[1] + self._y_body_length / 2) - _y_insulation_start
            y_start = self._y_body_length + self._coated_tab_height - self._insulation_width

            x, y = self._get_footprint(
                notch_height=notch_height,
                y_depth=y_depth,
                y_start=y_start
            )

        # Get z-coordinate from body coordinates for this side
        idx = np.where(self._body_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No body coordinates found for side '{side}'")
        
        z_val = self._body_coordinates[idx[0], 2]

        # Create z and side columns
        z = np.full_like(x, z_val)

        # Stack into final (N, 4) array
        return np.column_stack((x, y, z))

    def get_top_down_view(self, with_dimensions: bool = False, **kwargs) -> go.Figure:
        return self._get_full_top_down_view(with_dimensions=with_dimensions, **kwargs)

    @property
    def mass_range(self) -> Tuple[float, float]:

        min = 0
        hyp_max = 0.1
        max = hyp_max * (1 - np.exp(-0.5/self._mass))

        return (
            round(min * KG_TO_G, 2), 
            round(max * KG_TO_G, 2)
        )

    @property
    def width(self) -> float:
        return self.x_body_length
    
    @width.setter
    def width(self, width: float) -> None:

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width <= 0:
            raise ValueError("Width cannot be negative or equal to 0.")
        
        self.x_body_length = width

    @property
    def height(self) -> float:
        return self.y_body_length

    @height.setter
    def height(self, height: float) -> None:

        if not isinstance(height, (int, float)):
            raise TypeError("Height must be a number.")

        if height <= 0:
            raise ValueError("Height cannot be negative or equal to 0.")

        self.y_body_length = height

    @property
    def height_marks(self) -> Dict[int, str]:
        min_height = np.ceil(self.height_range[0])
        max_height = np.floor(self.height_range[1])
        return {i: '' for i in range(int(min_height), int(max_height) + 1, 30)}

    @property
    def height_range(self) -> Tuple[float, float]:
        min = 0
        max = 0.5
        return (
            round(min * M_TO_MM, 2), 
            round(max * M_TO_MM, 2)
        )


class NotchedCurrentCollector(_TabbedCurrentCollector, _TapeCurrentCollector):
    """
    A notched current collector with tabs along the length.
    Inherits from _TabbedCurrentCollector and _TapeCurrentCollector.
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
            bare_lengths_a_side: Tuple[float, float] = (0,0),
            bare_lengths_b_side: Tuple[float, float] = (0,0),
            insulation_width: Optional[float] = 0,
            name: Optional[str] = 'Notched Current Collector',
            datum: Optional[Tuple[float, float, float]] = (0, 0, 0)
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
            datum=datum
        )

        self.tab_spacing = tab_spacing
        self._calculate_all_properties()
        self._update_properties = True
        
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
        # default y_depth to full body length if not passed in
        y_depth = self._y_body_length if y_depth is None else y_depth

        # default y_start to center-bottom if not passed in
        y_start = self._datum[1] - self._y_body_length / 2 if y_start is None else y_start

        # default notch to tab_height if not passed in
        notch = self._tab_height if notch_height is None else notch_height

        # bare lengths in m
        bare_left, bare_right = (b for b in bare_lengths)

        # x bounds
        default_x0 = self._datum[0] - self._x_body_length / 2 + bare_left
        default_x1 = self._datum[0] + self._x_body_length / 2 - bare_right
        x0 = default_x0 if x_start is None else x_start
        x1 = default_x1 if x_end is None else x_end

        y0 = y_start
        y1 = y_start + y_depth

        pts = []
        # bottom‐left
        pts.append((x0, y0))
        # up to top‐edge
        pts.append((x0, y1))

        # insert notches along the clipped range [x0, x1]
        for ts, te in self._tab_positions:
            if te < x0 or ts > x1:
                continue
            s = max(ts, x0)
            e = min(te, x1)

            # horizontal run to start of notch
            if pts[-1] != (s, y1):
                pts.append((s, y1))

            # draw the notch
            pts.append((s, y1 + notch))
            pts.append((e, y1 + notch))
            pts.append((e, y1))

            # advance to next horizontal
            next_x = min(e + self._tab_gap, x1)
            if next_x > pts[-1][0]:  # prevent duplicate point
                pts.append((next_x, y1))

        # finish the top edge
        if pts[-1][1] == y1 and pts[-1][0] < x1:
            pts.append((x1, y1))

        # down & close
        pts.append((x1, y0))
        pts.append((x0, y0))

        x = np.array([p[0] for p in pts], dtype=float)
        y = np.array([p[1] for p in pts], dtype=float)

        return x, y

    def _add_dimensions(self, fig: go.Figure, pad: float = 0.05, aspect_ratio: float = 3) -> go.Figure:
        """
        Add dimension annotations to the figure.
        
        :param fig: go.Figure: the figure to add dimensions to
        :param start_point: Tuple[float, float]: starting point of the current collector
        :param pad: float: padding for the dimensions
        """
        fig = self._add_length_dimension(fig, pad=pad, aspect_ratio=aspect_ratio)
        fig = self._add_height_dimension(fig, pad=pad)

        # Add tab spacing
        if len(self._tab_positions) > 1:
            y = self._datum[1] - self._y_body_length / 2 + self._total_height + (pad * self._total_height)
            xmin = self._tab_positions[0][0] + self._tab_width / 2
            xmax = xmin + self._tab_spacing
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Spacing: {self.tab_spacing} mm')

        # Add tab width
        if len(self._tab_positions) > 0:
            y = self._datum[1] - self._y_body_length / 2 + self._total_height + (pad * self._total_height)
            xmin = self._tab_positions[-2][0]
            xmax = xmin + self._tab_width
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Width: {self.tab_width} mm')

        return fig

    def _get_insulation_coordinates(self, side: str = 'a') -> np.ndarray:
        """
        Return insulation coordinates for a given side ('a' or 'b') as numpy array.
        Handles three cases: (1) above body, (2) below body, (3) straddling edge.
        """
        # Compute insulation Y-range
        y_body_top = self._datum[1] + self._y_body_length / 2
        y_ins_start = y_body_top + self._coated_tab_height - self._insulation_width
        y_ins_end = y_ins_start + self._insulation_width

        # Compute x bounds of coated region
        bare_left, bare_right = (
            self._bare_lengths_a_side if side == 'a' else self._bare_lengths_b_side
        )
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
                tab_x, tab_y = build_square_array(
                    x_width=e - s,
                    y_width=self._insulation_width,
                    x=s,
                    y=y_ins_start
                )
                
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
            x, y = build_square_array(
                x_width=x_end - x_start,
                y_width=self._insulation_width,
                x=x_start,
                y=y_ins_start
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
                x_end=x_end
            )

        # Get z-coordinate from body coordinates for this side
        idx = np.where(self._body_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No body coordinates found for side '{side}'")
        
        z_val = self._body_coordinates[idx[0], 2]

        # Create z array (handle None values in x/y arrays)
        z = np.full_like(x, z_val, dtype=object)
        z[x == None] = None  # Keep None values as None

        # Stack into final (N, 3) array
        return np.column_stack((x, y, z))

    @property
    def tab_positions(self) -> list:
        return [(round(start * M_TO_MM, 4), round(end * M_TO_MM, 4)) for start, end in self._tab_positions]
    
    @property
    def tab_spacing(self) -> float:
        return round(self._tab_spacing * M_TO_MM, 2)

    @tab_spacing.setter
    def tab_spacing(self, tab_spacing: float) -> None:

        if not isinstance(tab_spacing, (int, float)):
            raise TypeError("Tab spacing must be a number.")
        
        if tab_spacing < 0:
            raise ValueError("Tab spacing cannot be negative.")
        
        self._tab_spacing = float(tab_spacing) * MM_TO_M
        self._tab_gap = self._tab_spacing - self._tab_width

        if self._tab_gap < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def tab_spacing_range(self) -> Tuple[float, float]:
        """
        Get the tab spacing range in mm.
        """
        return (
            round(self.tab_width + 0.1, 2),
            1000
        )

    @property
    def tab_spacing_marks(self) -> Dict[int, str]:
        """
        Get the tab spacing marks in mm.
        """
        min_spacing = self.tab_spacing_range[0]
        max_spacing = self.tab_spacing_range[1]
        delta = 200
        num_steps = int(round((max_spacing - min_spacing) / delta)) + 1
        values = np.linspace(min_spacing, max_spacing, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @property
    def tab_gap(self) -> float:
        return round(self._tab_gap * M_TO_MM, 2)

    @property
    def coated_area_a_side(self) -> float:
        return round(self._coated_area_a_side * M_TO_MM**2, 2)
    
    @property
    def coated_area_b_side(self) -> float:
        return round(self._coated_area_b_side * M_TO_MM**2, 2)


class TablessCurrentCollector(NotchedCurrentCollector):
    """
    A tabless current collector used in cylindrical and flatwound cells.
    Inherits from NotchedCurrentCollector.
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
            name: Optional[str] = 'Tabless Current Collector',
            datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
            ) -> None:
        """
        Initialize an object that represents a tabless current collector.
        
        Parameters:
        -----------
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
            datum=datum
        )

        self._update_properties = False
        self.coated_width = coated_width
        self._update_properties = True
    
    def _add_height_dimension(self, fig: go.Figure, pad: float = 0.05) -> go.Figure:

        # Height line
        x = self._datum[0] - self._x_body_length / 2 - pad * self._y_body_length
        ymin = self._datum[1] - self._y_body_length / 2
        ymax = ymin + self._y_body_length + self._tab_height
        ymid = (ymin + ymax) / 2
        fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=-12, text=f'Height: {self.y_body_length} mm', textangle=-90)

        return fig

    def _add_dimensions(
            self, 
            fig: go.Figure, 
            pad: float = 0.05,
            aspect_ratio: float = 3
        ) -> go.Figure:
        """
        Add dimension annotations to the figure.
        
        :param fig: go.Figure: the figure to add dimensions to
        :param start_point: Tuple[float, float]: starting point of the current collector
        :param pad: float: padding for the dimensions
        """
        fig = self._add_length_dimension(fig, pad=pad, aspect_ratio=aspect_ratio)
        fig = self._add_height_dimension(fig, pad=pad)
        return fig

    @property
    def coated_width(self) -> float:
        return round(self._coated_width * M_TO_MM, 2)
    
    @property
    def coated_width_range(self) -> Tuple[float, float]:
        """
        Get the coated width range in mm.
        """
        min = (self._y_body_length + self._tab_height) * (4/5)
        max = self._y_body_length + self._tab_height

        return (
            round(min * M_TO_MM, 2), 
            round(max * M_TO_MM, 2)
        )
    
    @property
    def coated_width_marks(self) -> Dict[int, str]:
        """
        Get the coated width marks in mm.
        """
        min_width = self.coated_width_range[0]
        max_width = self.coated_width_range[1]
        delta = 5
        num_steps = int(round((max_width - min_width) / delta)) + 1
        values = np.linspace(min_width, max_width, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @coated_width.setter
    def coated_width(self, coated_width: float) -> None:

        if not isinstance(coated_width, (int, float)):
            raise TypeError("Coated width must be a number.")
        
        if coated_width < 0:
            raise ValueError("Coated width cannot be negative.")

        # Calculate the change in coated width (in mm)
        delta_coated_width_mm = self.coated_width - float(coated_width)

        print(delta_coated_width_mm)

        # Adjust body length and tab height (these setters expect mm)
        self.y_body_length = self.y_body_length - delta_coated_width_mm
        self.tab_height = self.tab_height + delta_coated_width_mm
        
        # Store the internal value in meters
        self._coated_width = float(coated_width) * MM_TO_M

    @property
    def width(self) -> float:
        return round((self._y_body_length + self._tab_height) * M_TO_MM, 2)

    @width.setter
    def width(self, width: float) -> None:
        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width <= 0:
            raise ValueError("Width cannot be negative or equal to 0.")

        new_y_length = width - self.tab_height
        self.y_body_length = new_y_length
        
        # Automatically adjust coated_width if it's now too large
        max_coated_width = self._y_body_length
        if self._coated_width > max_coated_width:
            self._coated_width = max_coated_width
            if self._update_properties:
                self._calculate_all_properties()


class WeldTab:

    def __init__(
            self,
            material: CurrentCollectorMaterial,
            width: float,
            length: float,
            thickness: float,
            datum: Tuple[float, float] = (0, 0, 0)
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
        """
        Calculate the properties of the tab.
        """
        self._trace, self._area = self._get_trace()
        self._side_trace, self._side_area = self._get_side_trace()
        self._volume = self._area * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost

    def _get_footprint(self) -> pd.DataFrame:

        x_coords = [self._datum[0] - self._width / 2,
                    self._datum[0] + self._width / 2,
                    self._datum[0] + self._width / 2,
                    self._datum[0] - self._width / 2,
                    self._datum[0] - self._width / 2]
        
        y_coords = [self._datum[1] - self._length / 2,
                    self._datum[1] - self._length / 2,
                    self._datum[1] + self._length / 2,
                    self._datum[1] + self._length / 2,
                    self._datum[1] - self._length / 2]
    
        return pd.DataFrame({'x': x_coords, 'y': y_coords})

    def _get_sideprint(self) -> pd.DataFrame:

        x_coords = [self._datum[1] - self._length / 2,
                    self._datum[1] + self._length / 2,
                    self._datum[1] + self._length / 2,
                    self._datum[1] - self._length / 2,
                    self._datum[1] - self._length / 2]
        
        y_coords = [self._datum[2] - self._thickness / 2,
                    self._datum[2] - self._thickness / 2,
                    self._datum[2] + self._thickness / 2,
                    self._datum[2] + self._thickness / 2,
                    self._datum[2] - self._thickness / 2]
    
        return pd.DataFrame({'x': x_coords, 'y': y_coords})

    def _get_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the weld tab area.
        """
        coordinates = self._get_footprint()

        trace = go.Scatter(
            x=coordinates['x'], 
            y=coordinates['y'], 
            mode='lines', 
            name='Weld Tab', 
            line=dict(width=1, color='black'), 
            fillcolor=self._material._color, 
            fill='toself'
        )

        area = get_area_from_points(trace)

        return trace, area
    
    def _get_side_trace(self) -> go.Scatter:

        coordinates = self._get_sideprint()

        trace = go.Scatter(
            x=coordinates['x'], 
            y=coordinates['y'], 
            mode='lines', 
            name='Weld Tab', 
            line=dict(width=0.5, color='black'), 
            fillcolor=self._material._color, 
            fill='toself'
        )

        area = get_area_from_points(trace)

        return trace, area
    
    def get_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self._trace)

        figure.update_layout(
            xaxis=dict(scaleanchor='y', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure
    
    def get_side_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the side view of the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self._side_trace)

        figure.update_layout(
            xaxis=dict(scaleanchor='y', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure

    @property
    def datum(self) -> Tuple[float, float]:
        return (round(self._datum[0] * M_TO_MM, 2), round(self._datum[1] * M_TO_MM, 2))
    
    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        
        if not isinstance(datum, tuple) or len(datum) != 3:
            raise TypeError("Datum must be a tuple of three numbers (x, y, z).")
        
        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("Both coordinates in the datum must be numbers.")
        
        self._datum = (float(datum[0]) * MM_TO_M, float(datum[1]) * MM_TO_M, float(datum[2]) * MM_TO_M)

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def material(self) -> CurrentCollectorMaterial:
        return self._material
    
    @material.setter
    def material(self, material: CurrentCollectorMaterial) -> None:

        if not isinstance(material, CurrentCollectorMaterial):
            raise TypeError("Material must be an instance of CurrentCollectorMaterial.")
        
        self._material = material
    
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def width(self) -> float:
        return round(self._width * M_TO_MM, 2)
    
    @width.setter
    def width(self, width: float) -> None:

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        self._width = float(width) * MM_TO_M
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def length(self) -> float:
        return round(self._length * M_TO_MM, 2)
    
    @length.setter
    def length(self, length: float) -> None:

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if length < 0:
            raise ValueError("Length cannot be negative.")
        
        self._length = float(length) * MM_TO_M
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @thickness.setter
    def thickness(self, thickness: float) -> None:

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M
        
        if self._update_properties:
            self._calculate_all_properties()
    
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
    def area(self) -> float:
        return round(self._area * M_TO_MM**2, 2)


class TabWeldedCurrentCollector(_TapeCurrentCollector):
    """
    A current collector with tabs welded on it.
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
            tab_weld_side: str = 'a',
            bare_lengths_a_side: Tuple[float, float] = (0, 0),
            bare_lengths_b_side: Tuple[float, float] = (0, 0),
            name: Optional[str] = 'Tab Welded Current Collector',
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
            datum=datum
        )
        
        self.weld_tab_positions = weld_tab_positions
        self.tab_overhang = tab_overhang
        self.weld_tab = weld_tab
        self.skip_coat_width = skip_coat_width
        self.tab_weld_side = tab_weld_side

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self) -> None:
        super()._calculate_all_properties()
        self._cost += sum(tab._cost for tab in self._weld_tabs)

    def _get_full_view(
            self, 
            side='a', 
            aspect_ratio: float = 3, 
            with_dimensions: bool = True, 
            **kwargs
        ) -> go.Figure:
        
        # Get the base figure from the parent class
        figure = super()._get_full_view(
            side=side,
            aspect_ratio=aspect_ratio,
            with_dimensions=with_dimensions,
            **kwargs
        )
    
        # Add the weld‐tab traces but group them under one legend entry
        for i, tab in enumerate(self._weld_tabs):
            tr = tab._trace
            tr.legendgroup = 'Weld Tabs'
            tr.name = 'Weld Tabs'
            tr.showlegend = True if i == 0 else False
            figure.add_trace(tr)

        if side != self._tab_weld_side:
            n = len(self._weld_tabs)
            traces = list(figure.data)
            figure.data = traces[n:] + traces[:n]

        return figure

    def _get_footprint(self, left_x: Optional[float] = None, right_x: Optional[float] = None) -> pd.DataFrame:

        left_x = self._datum[0] - self._x_body_length / 2 if left_x is None else left_x
        right_x = self._datum[0] + self._x_body_length / 2 if right_x is None else right_x
        bottom_y = self._datum[1] - self._y_body_length / 2
        top_y = self._datum[1] + self._y_body_length / 2

        x_coords = [left_x, right_x, right_x, left_x, left_x]
        y_coords = [bottom_y, bottom_y, top_y, top_y, bottom_y]

        return pd.DataFrame({'x': x_coords, 'y': y_coords})

    def _get_body_trace(self) -> Tuple[go.Scatter, float]:
        
        coordinates = self._get_footprint()
        
        trace = go.Scatter(
            x=coordinates['x'],
            y=coordinates['y'],
            mode='lines',
            name='Body',
            line=dict(width=1, color='black'),
            fillcolor=self._material._color,
            fill='toself'
        )

        area = get_area_from_points(trace)
        
        return trace, area

    def _remove_skip_coat_area(self, coordinates: pd.DataFrame) -> pd.DataFrame:

        x_min, xmax = coordinates['x'].min(), coordinates['x'].max()
        y_min, ymax = coordinates['y'].min(), coordinates['y'].max()
        
        # 1) sort the weld‐tab cut positions, convert to meters
        cuts = sorted(t._datum[0] for t in self._weld_tabs)
        half = self._skip_coat_width / 2

        # 2) build the "kept" horiz segments by chopping out [c-half, c+half] around each cut
        segments = []
        start = x_min
        for c in cuts:
            end = c - half
            if end > start:
                segments.append((start, end))
            start = c + half
        if start < xmax:
            segments.append((start, xmax))

        # 3) for each kept segment make a little rectangle, then append a None‐row to separate
        dfs = []
        for idx, (a, b) in enumerate(segments, start=1):
            rect = [(a, y_min), (b, y_min), (b, ymax), (a, ymax), (a, y_min)]
            df_rect = pd.DataFrame(rect, columns=['x','y'])
            df_rect['tab_number'] = idx
            dfs.append(df_rect)
            # insert a blank row so Plotly breaks the fill
            dfs.append(pd.DataFrame({'x':[None], 'y':[None], 'tab_number':[None]}))

        return pd.concat(dfs, ignore_index=True)

    def _get_coated_area_trace(self, side: str = 'a') -> Tuple[go.Scatter, float]:

        coated_area = self._get_footprint(
            left_x=self._datum[0] - self._x_body_length / 2 + self._bare_lengths_a_side[0],
            right_x=self._datum[0] + self._x_body_length / 2 - self._bare_lengths_a_side[1]
        )

        coated_area = self._remove_skip_coat_area(coated_area)
        
        trace = go.Scatter(
            x=coated_area['x'],
            y=coated_area['y'],
            mode='lines',
            name='Coated Area',
            line=dict(width=1, color='black'),
            fillcolor='black',
            fill='toself',
            fillpattern=self._am_fill_pattern
        )

        if 'tab_number' in coated_area.columns:

            area = (
                coated_area
                .dropna()
                .groupby('tab_number')
                .apply(lambda df: get_area_from_points(go.Scatter(x=df['x'], y=df['y'], mode='lines')))
                .sum()
            )

        else:
            area = get_area_from_points(trace)

        return trace, area

    def _get_a_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side='a')

    def _get_b_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side='b')

    def _get_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return go.Scatter(x=[], y=[]), 0
    
    def _get_a_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()
    
    def _get_b_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()

    def _add_dimensions(
            self, 
            fig: go.Figure, 
            pad: float = 0.05,
            aspect_ratio: float = 3
        ) -> go.Figure:
        """
        Add dimension annotations to the figure.
        
        :param fig: go.Figure: the figure to add dimensions to
        :param pad: float: padding for the dimensions
        """
        fig = self._add_length_dimension(fig, pad=pad, aspect_ratio=aspect_ratio)
        fig = self._add_height_dimension(fig, pad=pad)
        return fig

    def get_end_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the end view of the punched current collector.
        The end view is a rectangle representing the end of the current collector.
        """
        fig = go.Figure()
        
        fig.add_trace(self._get_end_trace())
        fig.add_trace(self._weld_tabs[0]._side_trace)

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return fig

    @property
    def weld_tab_positions(self) -> list:
        """
        Returns the positions of the weld tabs along the length of the current collector in mm.
        """
        return [round(pos * M_TO_MM, 2) for pos in self._weld_tab_positions]
    
    @weld_tab_positions.setter
    def weld_tab_positions(self, weld_tab_positions: Iterable[float]) -> None:

        if not isinstance(weld_tab_positions, Iterable):
            raise TypeError("Weld tab positions must be an iterable of numbers.")
        
        if len(weld_tab_positions) == 0:
            raise ValueError("Weld tab positions cannot be empty. Please provide at least one position.")
        
        self._weld_tab_positions = [float(pos) * MM_TO_M for pos in sorted(weld_tab_positions)]

        if any(pos < 0 for pos in self._weld_tab_positions):
            raise ValueError("Weld tab positions cannot be negative.")
        
        if any(pos > self._x_body_length for pos in self._weld_tab_positions):
            raise ValueError("Weld tab positions cannot be greater than the length of the current collector.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def skip_coat_width(self) -> float:
        """
        Returns the width of the skip coat area in mm.
        """
        return round(self._skip_coat_width * M_TO_MM, 2)

    @skip_coat_width.setter
    def skip_coat_width(self, skip_coat_width: float) -> None:

        if not isinstance(skip_coat_width, (int, float)):
            raise TypeError("Skip coat width must be a number.")
        
        if skip_coat_width < 0:
            raise ValueError("Skip coat width cannot be negative.")
        
        if skip_coat_width < self._weld_tabs[0]._width / 2:
            self._skip_coat_width = self._weld_tabs[0]._width
        else:
            self._skip_coat_width = float(skip_coat_width) * MM_TO_M

        if self._skip_coat_width > self._y_body_length:
            raise ValueError("Skip coat width cannot be greater than the width of the current collector.")
        
        if self._update_properties:
            self._calculate_all_properties()

    @property
    def tab_weld_side(self) -> str:
        """
        Returns the side of the current collector where the weld tabs are located ('a' or 'b').
        """
        return self._tab_weld_side
    
    @tab_weld_side.setter
    def tab_weld_side(self, tab_weld_side: str) -> None:

        if tab_weld_side not in ['a', 'b']:
            raise ValueError("Tab weld side must be either 'a' or 'b'.")
        
        self._tab_weld_side = tab_weld_side

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def tab_overhang(self) -> float:
        """
        Returns the overhang of the weld tab on the current collector in mm.
        """
        return round(self._tab_overhang * M_TO_MM, 2)

    @tab_overhang.setter
    def tab_overhang(self, tab_overhang: float) -> None:

        if not isinstance(tab_overhang, (int, float)):
            raise TypeError("Tab overhang must be a number.")
        
        if tab_overhang < 0:
            raise ValueError("Tab overhang cannot be negative.")
        
        self._tab_overhang = float(tab_overhang) * MM_TO_M

        if self._update_properties:
            self._calculate_all_properties()

    @property
    def weld_tab(self) -> list:
        """
        Returns a list of WeldTab objects representing the weld tabs on the current collector.
        """
        return self._weld_tabs[0]
    
    @weld_tab.setter
    def weld_tab(self, weld_tab: WeldTab) -> None:

        if not isinstance(weld_tab, WeldTab):
            raise TypeError("Weld tab must be an instance of WeldTab.")
        
        self._weld_tabs = [deepcopy(weld_tab) for _ in self._weld_tab_positions]
        tab_y_center = (self._y_body_length / 2 + self._tab_overhang - self._weld_tabs[0]._length / 2) * M_TO_MM

        for _pos, _tab in zip(self._weld_tab_positions, self._weld_tabs):
            pos = (_pos - self._x_body_length / 2) * M_TO_MM
            _tab.datum = (pos, tab_y_center, self.datum[2] + self.thickness/2*UM_TO_MM + _tab.thickness/2*UM_TO_MM)

        if self._update_properties:
            self._calculate_all_properties()


