from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial

from SteerEnergyStorage.Utils import get_area_from_trace
from SteerEnergyStorage.Utils import build_square_df
from SteerEnergyStorage.Constants import *
from App.styles import *

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Iterable
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from copy import deepcopy


class _CurrentCollector(ABC):

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 thickness: float,
                 insulation_width: Optional[float] = 0,
                 datum: Optional[Tuple[float, float]] = (0, 0),
                 **kwargs):
        """
        Initialize an object that represents a current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param x_body_length: float: length of the current collector in mm
        :param y_body_length: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param insulation_width: float: width of the insulation in mm
        :param datum: Optional[Tuple[float, float]]: starting position of the current collector in mm, default is (0, 0)
        """
        self._check_datum(datum)
        self._check_material(material)
        self._check_x_body_length(x_body_length)
        self._check_y_body_length(y_body_length)
        self._check_thickness(thickness)
        self._check_insulation_width(insulation_width)

        # Shading patterns
        self._am_fill_pattern = dict(shape='/', size=20, solidity=0.6, fgcolor=self._material._color)
        self._in_fill_pattern = dict(shape='\\', size=10, solidity=0.6, fgcolor=self._material._color)

    def _check_datum(self, datum: Optional[Tuple[float, float]]) -> None:
        """
        Check if the datum is a tuple of two floats.
        If not, set it to (0, 0).
        """
        if not isinstance(datum, tuple) or len(datum) != 2:
            raise TypeError("Datum must be a tuple of two floats.")
        
        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("Both coordinates in datum must be numbers.")
        
        self._datum = (float(datum[0]) * MM_TO_M, float(datum[1]) * MM_TO_M)

    def _calculate_properties(self) -> None:
        """
        Calculate the properties of the punched current collector.
        """
        self._body_trace, self._body_area = self._get_body_trace()

        self._a_side_coated_area_trace, self._a_side_coated_area = self._get_a_side_coated_area_trace()
        self._b_side_coated_area_trace, self._b_side_coated_area = self._get_b_side_coated_area_trace()
        self._coated_area = self._a_side_coated_area + self._b_side_coated_area

        self._a_side_insulation_area_trace, self._a_side_insulation_area = self._get_a_side_insulation_area_trace()
        self._b_side_insulation_area_trace, self._b_side_insulation_area = self._get_b_side_insulation_area_trace()
        self._insulation_area = self._a_side_insulation_area + self._b_side_insulation_area

        self._volume = self._body_area * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost     

    def _check_material(self, material: CurrentCollectorMaterial) -> None:

        if not isinstance(material, CurrentCollectorMaterial):
            raise TypeError("Material must be an instance of CurrentCollectorMaterial.")
        
        self._material = material

    def _check_x_body_length(self, x_body_length: float) -> None:

        if not isinstance(x_body_length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if x_body_length <= 0:
            raise ValueError("Length cannot be negative or equal to 0.")
        
        self._x_body_length = float(x_body_length) * MM_TO_M

    def _check_y_body_length(self, y_body_length: float) -> None:

        if not isinstance(y_body_length, (int, float)):
            raise TypeError("Width must be a number.")
        
        if y_body_length <= 0:
            raise ValueError("Width cannot be negative or equal to 0.")
        
        self._y_body_length = float(y_body_length) * MM_TO_M

    def _check_thickness(self, thickness: float) -> None:

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M

    def _check_insulation_width(self, insulation_width: Optional[float]) -> None:

        if not isinstance(insulation_width, (int, float)):
            raise TypeError("Insulation width must be a number.")
        if insulation_width < 0:
            raise ValueError("Insulation width cannot be negative or equal to 0.")
        
        self._insulation_width = float(insulation_width) * MM_TO_M

    @abstractmethod
    def get_a_side_view(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs) -> go.Figure:
        """
        Visualize the current collector.
        """
        pass

    @abstractmethod
    def get_b_side_view(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs) -> go.Figure:
        """
        Visualize the current collector from the B side.
        """
        pass

    @abstractmethod
    def _get_body_trace(self) -> go.Scatter:
        """
        Get the body trace of the current collector.
        """
        pass

    @abstractmethod
    def _get_a_side_coated_area_trace(self) -> go.Scatter:
        """
        Get the coated area trace of the current collector.
        """
        pass

    @abstractmethod
    def _get_b_side_coated_area_trace(self) -> go.Scatter:
        """
        Get the coated area trace of the current collector.
        """
        pass

    @abstractmethod
    def _get_a_side_insulation_area_trace(self) -> go.Scatter:
        """
        Get the insulation area trace of the current collector.
        """
        pass

    @abstractmethod
    def _get_b_side_insulation_area_trace(self) -> go.Scatter:
        """
        Get the insulation area trace of the current collector.
        """
        pass

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
        return round(self._coated_area * M_TO_CM**2, 2)

    @property
    def a_side_coated_area(self) -> float:
        return round(self._a_side_coated_area * M_TO_CM**2, 2)
    
    @property
    def b_side_coated_area(self) -> float:
        return round(self._b_side_coated_area * M_TO_CM**2, 2)

    @property
    def body_area(self) -> float:
        return round(self._body_area * M_TO_CM**2, 2)

    @property
    def a_side_insulation_area(self) -> float:
        return round(self._a_side_insulation_area * M_TO_CM**2, 2)
    
    @property
    def b_side_insulation_area(self) -> float:
        return round(self._b_side_insulation_area * M_TO_CM**2, 2)

    @property
    def insulation_area(self) -> float:
        return round(self._insulation_area * M_TO_CM**2, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def datum(self) -> Tuple[float, float]:
        return self._datum

    @property
    def x_body_length(self) -> float:
        return round(self._x_body_length * M_TO_MM, 2)
    
    @property
    def y_body_length(self) -> float:
        return round(self._y_body_length * M_TO_MM, 2)
    
    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    def __str__(self):
        return f"{self.__class__.__name__}"
    
    def __repr__(self):
        return self.__str__()


class _TabbedCurrentCollector(_CurrentCollector):

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
            **kwargs
        ):
        """
        Initialize an object that represents a tabbed current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param x_body_length: float: length of the current collector in mm
        :param y_body_length: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param tab_width: float: width of the tab in mm
        :param tab_height: float: height of the tab in mm
        :param coated_tab_height: float: height of the coated tab on the top side in mm
        :param insulation_width: Optional[float]: width of the insulation in mm, default is 0
        """
        super().__init__(material=material,
                         x_body_length=x_body_length,
                         y_body_length=y_body_length,
                         thickness=thickness,
                         insulation_width=insulation_width,
                         **kwargs)
        
        self._check_tab_width(tab_width)
        self._check_tab_height(tab_height)
        self._check_coated_tab_height(coated_tab_height)

        self._total_height = self._y_body_length + self._tab_height
        
    def _check_tab_width(self, tab_width: float) -> None:

        if not isinstance(tab_width, (int, float)):
            raise TypeError("Tab width must be a number.")
        
        if tab_width < 0:
            raise ValueError("Tab width cannot be negative.")
        
        self._tab_width = float(tab_width) * MM_TO_M

        if self._tab_width > self._x_body_length:
            raise ValueError("Tab width cannot be greater than the length of the current collector.")

    def _check_tab_height(self, tab_height: float) -> None:

        if not isinstance(tab_height, (int, float)):
            raise TypeError("Tab height must be a number.")
        
        if tab_height < 0:
            raise ValueError("Tab height cannot be negative.")
        
        self._tab_height = float(tab_height) * MM_TO_M

    def _check_coated_tab_height(self, coated_tab_height: float) -> None:

        if not isinstance(coated_tab_height, (int, float)):
            raise TypeError("Covered tab height on the top side must be a number.")
        
        if coated_tab_height < 0:
            raise ValueError("Covered tab height on the top side cannot be negative.")
        
        self._coated_tab_height = float(coated_tab_height) * MM_TO_M

        if self._coated_tab_height > self._tab_height:
            raise ValueError("Covered tab height on the top side cannot be greater than the tab height.")

    @property
    def tab_width(self) -> float:
        return round(self._tab_width * M_TO_MM, 2)

    @property
    def tab_height(self) -> float:
        return round(self._tab_height * M_TO_MM, 2)

    @property
    def coated_tab_height(self) -> float:
        return round(self._coated_tab_height * M_TO_MM, 2)

    @property
    def total_height(self) -> float:
        return round(self._total_height * M_TO_MM, 2)


class _TapeCurrentCollector(_CurrentCollector):

    def __init__(
            self,
            material: CurrentCollectorMaterial,
            x_body_length: float,
            y_body_length: float,
            thickness: float,
            bare_lengths_a_side: Tuple[float, float] = (0,0),
            bare_lengths_b_side: Tuple[float, float] = (0,0),
            insulation_width: Optional[float] = 0,
            **kwargs
        ) -> None:
        
        super().__init__(material=material,
                         x_body_length=x_body_length,
                         y_body_length=y_body_length,
                         insulation_width=insulation_width,
                         thickness=thickness)
        
        self._check_bare_lengths_a_side(bare_lengths_a_side)
        self._check_bare_lengths_b_side(bare_lengths_b_side)

    def _check_bare_lengths_a_side(self, bare_lengths_a_side: Tuple[float, float]) -> None:

        if not isinstance(bare_lengths_a_side, tuple) or len(bare_lengths_a_side) != 2:
            raise TypeError("Bare lengths on A side must be a tuple of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in bare_lengths_a_side):
            raise TypeError("Bare lengths on A side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_a_side):
            raise ValueError("Bare lengths on A side cannot be negative.")
        
        self._bare_lengths_a_side = tuple(float(length) * MM_TO_M for length in bare_lengths_a_side)

        if self._x_body_length < sum(self._bare_lengths_a_side):
            raise ValueError("Total bare lengths on A side cannot be greater than the length of the current collector.")

    def _check_bare_lengths_b_side(self, bare_lengths_b_side: Tuple[float, float]) -> None:

        if not isinstance(bare_lengths_b_side, tuple) or len(bare_lengths_b_side) != 2:
            raise TypeError("Bare lengths on B side must be a tuple of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in bare_lengths_b_side):
            raise TypeError("Bare lengths on B side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_b_side):
            raise ValueError("Bare lengths on B side cannot be negative.")
        
        self._bare_lengths_b_side = tuple(float(length) * MM_TO_M for length in bare_lengths_b_side)

        if self._x_body_length < sum(self._bare_lengths_b_side):
            raise ValueError("Total bare lengths on B side cannot be greater than the length of the current collector.")

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

    def _get_view(
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

        max_x = self._y_body_length * aspect_ratio

        figure = self._get_full_view(
            side=side, 
            with_dimensions=with_dimensions,
            aspect_ratio=aspect_ratio
        )

        if max_x < self._x_body_length:

            figure_subplot = make_subplots(
                rows=2, 
                cols=1, 
                vertical_spacing=0.1, 
                subplot_titles=[f"{side.upper()} side start", f"{side.upper()} side end"]
            )

            for trace in figure.data:
                figure_subplot.add_trace(trace, row=1, col=1)
                figure_subplot.add_trace(trace, row=2, col=1)

            if with_dimensions:
                orig = figure.layout.annotations or []
                for ann in orig:
                    props = ann.to_plotly_json()
                    # nuk e the old axis‐refs
                    for key in ('xref','yref','axref','ayref'):
                        props.pop(key, None)

                    # now re‐add on each subplot, explicitly setting both head & tail refs
                    for row in (1, 2):
                        suffix = '' if row==1 else '2'
                        props['xref']  = f'x{suffix}'
                        props['yref']  = f'y{suffix}'
                        # if this is an arrow, force the tail refs too
                        if props.get('showarrow', False):
                            props['axref'] = props['xref']
                            props['ayref'] = props['yref']
                        figure_subplot.add_annotation(row=row, col=1, **props)

            top_row_range = [
                -self._x_body_length / 2, 
                -self._x_body_length / 2 + max_x
            ]

            bottom_row_range = [
                self._x_body_length / 2 - max_x, 
                self._x_body_length / 2
            ]

            figure_subplot.update_xaxes(range=top_row_range, row=1, col=1)
            figure_subplot.update_xaxes(range=bottom_row_range, row=2, col=1)
            figure = figure_subplot

        figure.update_layout(
            xaxis=dict(scaleanchor='y', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            xaxis2=dict(scaleanchor='y2', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis2=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure

    def _get_full_view(
            self, 
            side: str = 'a', 
            with_dimensions: bool = True, 
            aspect_ratio: float = 3
        ) -> go.Figure:
        """
        Visualize the notched current collector from the A side.
        """
        if side.lower() not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")
        
        fig = go.Figure()
        fig.add_trace(self._body_trace)
        
        if side.lower() == 'a':
            fig.add_trace(self._a_side_coated_area_trace)
            fig.add_trace(self._a_side_insulation_area_trace)
        else:
            fig.add_trace(self._b_side_coated_area_trace)
            fig.add_trace(self._b_side_insulation_area_trace)

        if with_dimensions:
            fig = self._add_dimensions(fig=fig, aspect_ratio=aspect_ratio)

        return fig

    def get_a_side_view(self, **kwargs) -> go.Figure:
        return self._get_view(side='a', **kwargs)
    
    def get_b_side_view(self, **kwargs) -> go.Figure:
        return self._get_view(side='b', **kwargs)

    @property
    def bare_lengths_a_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_a_side)
    
    @property
    def bare_lengths_b_side(self) -> Tuple[float, float]:
        return tuple(round(length * M_TO_MM, 2) for length in self._bare_lengths_b_side)

    @property
    def length(self) -> float:
        return self.x_body_length
    
    @property
    def width(self) -> float:
        return self.y_body_length

        
class PunchedCurrentCollector(_TabbedCurrentCollector):

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
        ) -> None:
        """
        Initialize an object that represents a punched current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param x_body_length: float: length of the current collector in mm
        :param y_body_length: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param tab_width: float: width of the tab in mm
        :param tab_height: float: height of the tab in mm
        :param tab_position: float: position of the tab in mm, measured from the left edge of the current collector
        :param coated_tab_height: float: height of the coated tab on the top side in mm
        """
        super().__init__(material=material,
                         x_body_length=width,
                         y_body_length=height,
                         tab_width=tab_width,
                         tab_height=tab_height,
                         coated_tab_height=coated_tab_height,
                         thickness=thickness,
                         insulation_width=insulation_width,
                         )
        
        self._check_tab_position(tab_position)
        self._calculate_properties()

    def _check_tab_position(self, tab_position: float) -> None:

        if not isinstance(tab_position, (int, float)):
            raise TypeError("Tab position must be a number.")
        
        self._tab_position = float(tab_position) * MM_TO_M
        
        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")
        
        if self._tab_position + self._tab_width / 2 > self.x_body_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")

    def _get_footprint(
            self, 
            notch_height: float = None, 
            y_depth: float = None,
            y_start: float = 0,
        ) -> pd.DataFrame:
        """
        Get the footprint of the current collector.

        :param start_position: Tuple[float, float]: starting position of the current collector in mm, default is (-x_body_length/2, -y_body_length/2)
        :param notch_height: float: height of the notch in mm, default is self.tab_height
        """
        y_depth = self._y_body_length if y_depth is None else y_depth
        
        x_steps = [0, 
                   self._tab_position - self._tab_width/2, 
                   0, 
                   self._tab_width, 
                   0, 
                   self._x_body_length - self._tab_position - self._tab_width/2, 
                   0, 
                   -self._x_body_length]
        
        y_steps = [y_depth,
                   0,
                   notch_height,
                   0,
                   -notch_height,
                   0,
                   -y_depth,
                   0]
        
        start_position = (self._datum[0] - self._x_body_length / 2, self._datum[1] - self._y_body_length / 2 + y_start)
        coordinates = [start_position]
        
        for x, y in zip(x_steps, y_steps):
            new_x = coordinates[-1][0] + x
            new_y = coordinates[-1][1] + y
            coordinates.append((new_x, new_y))

        return pd.DataFrame(coordinates, columns=['x', 'y'])

    def _add_dimensions(self, fig: go.Figure, pad: float = 0.05) -> go.Figure:

        # width line
        xmin = self._datum[0] - self._x_body_length / 2
        xmax = xmin + self._x_body_length
        xmid = (xmin + xmax) / 2
        y = self._datum[1] - self._y_body_length/2 - pad * self._y_body_length
        fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'Width: {self.x_body_length} mm')

        # height line
        x = self._datum[0] - self._x_body_length / 2 - pad * self._x_body_length
        ymin = self._datum[1] - self._y_body_length / 2
        ymax = ymin + self._y_body_length
        ymid = (ymin + ymax) / 2
        fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=-12, text=f'Height: {self.y_body_length} mm', textangle=-90)

        # tab position line
        y = self._datum[1] - self._y_body_length/2 + self._y_body_length + self._tab_height + (4 * pad * self._y_body_length)
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
        fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
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
        fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
        fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=xshift, text=f'Tab Height: {self.tab_height} mm')

        return fig

    def _get_body_trace(self) -> go.Scatter:

        body_coordinates = self._get_footprint(notch_height=self._tab_height)

        trace = go.Scatter(
            x=body_coordinates['x'], 
            y=body_coordinates['y'], 
            mode='lines', 
            name='Body', 
            line=dict(width=1, color='black'), 
            fillcolor=self._material._color, 
            fill='toself'
            )
        
        area = get_area_from_trace(trace)

        return trace, area

    def _get_coated_area_trace(self) -> go.Scatter:

        _y_coat_end = self._y_body_length + self._coated_tab_height - self._insulation_width

        if _y_coat_end > self._y_body_length:
            notch = self._coated_tab_height - (self._insulation_width)
            y_depth = self._y_body_length
        else:
            notch = 0
            y_depth = _y_coat_end

        coated_area = self._get_footprint(
            notch_height=notch, 
            y_depth=y_depth
            )

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

        area =            get_area_from_trace(trace)
        
        return trace, area

    def _get_insulation_area_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the insulation area.
        The shape depends on whether the insulation is entirely above, below,
        or straddling the body length.
        """
        _y_insulation_start = self._datum[1] + self._y_body_length/2 + self._coated_tab_height - self._insulation_width
        _y_insulation_end = _y_insulation_start + self._insulation_width

        # Case 1: Insulation strip is above the body
        if _y_insulation_start > self._datum[1] + self._y_body_length/2:
            x = self._datum[0] - self._x_body_length/2 + self._tab_position - self._tab_width/2 
            y = _y_insulation_start
            
            insulation_area = build_square_df(
                x_width=self._tab_width,
                y_width=self._insulation_width,
                x = x,
                y = y
            )

        # Case 2: Entire insulation below body
        elif round(_y_insulation_end, 10) <= round(self._datum[1] + self._y_body_length/2, 10):

            insulation_area = build_square_df(
                x_width=self._x_body_length,
                y_width=self._insulation_width,
                x = self._datum[0] - self._x_body_length/2,
                y = _y_insulation_start
            )

        # Case 3: Straddling the body
        else:
            notch_height = (_y_insulation_end - (self._datum[1] + self._y_body_length/2))

            y_depth = (self._datum[1] + self._y_body_length/2) - _y_insulation_start

            insulation_area = self._get_footprint(
                notch_height=notch_height,
                y_depth=y_depth,
                y_start=self._y_body_length + self._coated_tab_height - self._insulation_width
            )

        trace = go.Scatter(
            x=insulation_area['x'],
            y=insulation_area['y'],
            mode='lines',
            name='Insulation Strip',
            line=dict(width=1, color='black'),
            fill='toself',
            fillcolor='white',
            fillpattern=self._in_fill_pattern
        )

        area = get_area_from_trace(trace)

        return trace, area

    def _get_a_side_insulation_area_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the insulation area on the B side.
        The B side is the same as the A side in this case.
        """
        return self._get_insulation_area_trace()
    
    def _get_b_side_insulation_area_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the insulation area on the B side.
        The B side is the same as the A side in this case.
        """
        return self._get_insulation_area_trace()

    def _get_a_side_coated_area_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the coated area on the A side.
        """
        return self._get_coated_area_trace()
    
    def _get_b_side_coated_area_trace(self) -> go.Scatter:
        """
        Returns a Plotly Scatter trace representing the coated area on the B side.
        The B side is the same as the A side in this case.
        """
        return self._get_coated_area_trace()

    def _get_view(self, with_dimensions: bool = True, **kwargs) -> go.Figure:

        fig = go.Figure()
        fig.add_trace(self._body_trace)
        fig.add_trace(self._a_side_coated_area_trace)
        fig.add_trace(self._a_side_insulation_area_trace)

        if with_dimensions:
            fig = self._add_dimensions(fig=fig)

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return fig
    
    def get_a_side_view(self, **kwargs) -> go.Figure:
        return self._get_view(**kwargs)

    def get_b_side_view(self, **kwargs) -> go.Figure:
        return self._get_view(**kwargs)

    @property
    def width(self) -> float:
        return self.x_body_length
    
    @property
    def height(self) -> float:
        return self.y_body_length

    @property
    def tab_position(self) -> float:
        return round(self._tab_position * M_TO_MM, 2)


class NotchedCurrentCollector(_TabbedCurrentCollector, _TapeCurrentCollector):

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
        ) -> None:
        """
        Initialize an object that represents a notched current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param length: float: length of the current collector in mm
        :param width: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param tab_width: float: width of the tabs in mm
        :param tab_length: float: length of the tabs in mm
        :param tab_spacing: float: spacing between the tabs in mm
        :param bare_lengths_a_side: Tuple[float, float]: lengths of the bare area on the A side in mm (left, right)
        :param bare_lengths_b_side: Tuple[float, float]: lengths of the bare area on the B side in mm (left, right)
        """
        super().__init__(material=material,
                         x_body_length=length,
                         y_body_length=width,
                         tab_width=tab_width,
                         tab_height=tab_height,
                         thickness=thickness,
                         coated_tab_height=coated_tab_height,
                         bare_lengths_a_side=bare_lengths_a_side,
                         bare_lengths_b_side=bare_lengths_b_side,
                         insulation_width=insulation_width,
                         )

        self._check_tab_spacing(tab_spacing)
        self._calculate_tab_positions()
        self._calculate_properties()

    def _check_tab_spacing(self, tab_spacing: float) -> None:

        if not isinstance(tab_spacing, (int, float)):
            raise TypeError("Tab spacing must be a number.")
        
        if tab_spacing < 0:
            raise ValueError("Tab spacing cannot be negative.")
        
        self._tab_spacing = float(tab_spacing) * MM_TO_M
        self._tab_gap = self._tab_spacing - self._tab_width

        if self._tab_gap < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")
        
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

        self._tab_positions = list(zip(tab_starts, tab_ends))

    def _get_footprint(
            self,
            notch_height: Optional[float] = None,
            bare_lengths: Tuple[float, float] = (0, 0),
            y_depth: Optional[float] = None,
            y_start: Optional[float] = None,
            x_start: Optional[float] = None,
            x_end: Optional[float] = None,
        ) -> pd.DataFrame:
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

        # pack to DataFrame, then apply global datum offset
        df = pd.DataFrame(pts, columns=("x", "y"))
        df["x"] += self._datum[0]
        df["y"] += self._datum[1]

        return df.reset_index(drop=True)

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
    
    def _get_body_trace(self) -> go.Scatter:

        coordinates = self._get_footprint(
            notch_height=self._tab_height
        )

        trace = go.Scatter(
            x=coordinates['x'], 
            y=coordinates['y'], 
            mode='lines', 
            name='Body', 
            line=dict(width=1, color='black'), 
            fillcolor=self._material._color, 
            fill='toself'
        )

        area = get_area_from_trace(trace)

        return trace, area

    def _get_coated_area_trace(self, bare_lengths: Tuple[float, float]) -> Tuple[go.Scatter, float]:

        _y_coat_end = self._y_body_length + self._coated_tab_height - self._insulation_width

        if _y_coat_end > self._y_body_length:
            notch = self._coated_tab_height - (self._insulation_width)
            y_depth = self._y_body_length
        else:
            notch = 0
            y_depth = _y_coat_end

        coated_area = self._get_footprint(
            notch_height=notch, 
            y_depth=y_depth,
            bare_lengths=bare_lengths
            )

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

        area = get_area_from_trace(trace)
        
        return trace, area

    def _get_a_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(bare_lengths=self._bare_lengths_a_side)

    def _get_b_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(bare_lengths=self._bare_lengths_b_side)

    def _get_insulation_area_trace(self, side: str = 'a') -> Tuple[go.Scatter, float]:
        """
        Return insulation trace and area for a given side ('a' or 'b').
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
            insulation_area = pd.DataFrame(columns=['x', 'y'])
            for idx, (ts, te) in enumerate(self._tab_positions):
                # Clip tab to coated region
                if te < x_start or ts > x_end:
                    continue
                s = max(ts, x_start)
                e = min(te, x_end)

                tab_df = build_square_df(
                    x_width=e - s,
                    y_width=self._insulation_width,
                    x=s,
                    y=y_ins_start
                )
                
                tab_df = tab_df.assign(tab_number=idx + 1)

                # Concatenate with spacer row for plotly breaks
                insulation_area = pd.concat(
                    [insulation_area, tab_df, pd.DataFrame([[None]*len(tab_df.columns)],
                                                        columns=tab_df.columns)],
                    ignore_index=True
                )

        # Case 2: Insulation entirely below the body
        elif round(y_ins_end, 10) <= round(y_body_top, 10):

            insulation_area = build_square_df(
                x_width = x_end - x_start,
                y_width = self._insulation_width,
                x = x_start,
                y = y_ins_start
            )

        # Case 3: Insulation straddles the top of the body
        else:
            notch = y_ins_end - y_body_top
            depth = y_body_top - y_ins_start
            insulation_area = self._get_footprint(
                notch_height=notch,
                y_depth=depth,
                y_start=y_ins_start,
                x_start=x_start,
                x_end=x_end
            )

        # Helper for converting area df to go.Scatter
        def get_trace(area_df: pd.DataFrame) -> go.Scatter:
            return go.Scatter(
                x=area_df['x'],
                y=area_df['y'],
                mode='lines',
                name='Insulation Area',
                line=dict(width=1, color='black'),
                fill='toself',
                fillcolor='white',
                fillpattern=self._in_fill_pattern
            )

        trace = get_trace(insulation_area)

        if 'tab_number' not in insulation_area.columns:
            area = get_area_from_trace(trace)
        else:
            area = (insulation_area
                    .dropna()
                    .groupby('tab_number')
                    .apply(lambda df: get_area_from_trace(get_trace(df[['x', 'y']])))
                    .sum()
                    )

        return trace, area
    
    def _get_a_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace(side='a')

    def _get_b_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace(side='b')

    @property
    def tab_positions(self) -> list:
        return [(round(start * M_TO_MM, 4), round(end * M_TO_MM, 4)) for start, end in self._tab_positions]
    
    @property
    def tab_spacing(self) -> float:
        return round(self._tab_spacing * M_TO_MM, 2)

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
            ) -> None:
        """
        Initialize an object that represents a tabless current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param length: float: length of the current collector in mm
        :param width: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param bare_lengths_a_side: Tuple[float, float]: lengths of the bare area on the A side in mm (left, right)
        :param bare_lengths_b_side: Tuple[float, float]: lengths of the bare area on the B side in mm (left, right)
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
        )

        self._check_coated_width(coated_width)

    def _check_coated_width(self, coated_width: float) -> None:

        if not isinstance(coated_width, (int, float)):
            raise TypeError("Coated width must be a number.")
        
        if coated_width < 0:
            raise ValueError("Coated width cannot be negative.")
        
        self._coated_width = float(coated_width) * MM_TO_M
        
        if self._coated_width > self._y_body_length:
            raise ValueError("Coated width cannot be greater than the width of the current collector.")
    
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
    def width(self) -> float:
        return round((self._y_body_length + self._tab_height) * M_TO_MM, 2)


class WeldTab:

    def __init__(
            self,
            material: CurrentCollectorMaterial,
            width: float,
            length: float,
            thickness: float,
            datum: Tuple[float, float] = (0, 0)
        ) -> None:
        """
        Initialize an object that represents a weld tab used on current collectors

        :param material: CurrentCollectorMaterial: material of the weld tab
        :param width: float: width of the weld tab in mm
        :param length: float: length of the weld tab in mm
        :param thickness: float: thickness of the weld tab in um
        """
        self._check_datum(datum)
        self._check_material(material)
        self._check_width(width)
        self._check_length(length)
        self._check_thickness(thickness)
        self._calculate_properties()

    def _check_datum(self, datum: Tuple[float, float]) -> None:

        if not isinstance(datum, tuple) or len(datum) != 2:
            raise TypeError("Datum must be a tuple of two numbers (x, y).")
        
        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("Both coordinates in the datum must be numbers.")
        
        self._datum = (float(datum[0]) * MM_TO_M, float(datum[1]) * MM_TO_M)

    def _check_material(self, material: CurrentCollectorMaterial) -> None:

        if not isinstance(material, CurrentCollectorMaterial):
            raise TypeError("Material must be an instance of CurrentCollectorMaterial.")
        
        self._material = material

    def _check_width(self, width: float) -> None:
        
        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        self._width = float(width) * MM_TO_M

    def _check_length(self, length: float) -> None:

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if length < 0:
            raise ValueError("Length cannot be negative.")
        
        self._length = float(length) * MM_TO_M

    def _check_thickness(self, thickness: float) -> None:

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M

    def _calculate_properties(self) -> None:
        """
        Calculate the properties of the tab.
        """
        self._trace, self._area = self._get_trace()
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

        area = get_area_from_trace(trace)

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
    def area(self) -> float:
        return round(self._area * M_TO_MM**2, 2)

    @property
    def datum(self) -> Tuple[float, float]:
        return (round(self._datum[0] * M_TO_MM, 2), round(self._datum[1] * M_TO_MM, 2))
    
    @datum.setter
    def datum(self, value: Tuple[float, float]):
        self._check_datum(value)
        self._calculate_properties()


class TabWeldedCurrentCollector(_TapeCurrentCollector):

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
            bare_lengths_b_side: Tuple[float, float] = (0, 0)
        ) -> None:
        """
        Initialize an object that represents a current collector with tabs welded on it.

        :param material: CurrentCollectorMaterial: material of the current collector
        :param length: float: length of the current collector in mm
        :param width: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param weld_tab: WeldTab: the weld tab to be used on the current collector
        :param weld_tab_positions: Iterable[float]: positions of the weld tabs along the length of the current collector in mm
        :param skip_coat_width: float: width of the skip coat area in mm
        :param tab_weld_side: str: side of the current collector where the weld tabs are located ('a' or 'b')
        :param bare_lengths_a_side: Tuple[float, float]: lengths of the bare area on the A side in mm (left, right)
        :param bare_lengths_b_side: Tuple[float, float]: lengths of the bare area on the B side in mm (left, right)
        :param tab_overhang: float: overhang of the weld tab on the current collector in mm
        """
        super().__init__(
            material=material,
            x_body_length=length,
            y_body_length=width,
            thickness=thickness,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side
        )
        
        self._check_weld_tab_positions(weld_tab_positions, weld_tab)
        self._check_tab_overhang(tab_overhang)
        self._check_and_copy_weld_tab(weld_tab)
        self._check_skip_coat_width(skip_coat_width)
        self._check_tab_weld_side(tab_weld_side)
        self._calculate_properties()

    def _calculate_properties(self) -> None:
        super()._calculate_properties()
        self._cost += sum(tab._cost for tab in self._weld_tabs)

    def _check_weld_tab_positions(self, weld_tab_positions: Iterable[float], weld_tab: WeldTab) -> None:

        if not isinstance(weld_tab_positions, Iterable):
            raise TypeError("Weld tab positions must be an iterable of numbers.")
        
        if len(weld_tab_positions) == 0:
            raise ValueError("Weld tab positions cannot be empty. Please provide at least one position.")
        
        self._weld_tab_positions = [float(pos) * MM_TO_M for pos in sorted(weld_tab_positions)]

        if min(self._weld_tab_positions) < weld_tab._width / 2:
            raise ValueError("Weld tab positions cannot be less than half the width of the weld tab.")

        if any(pos < 0 for pos in self._weld_tab_positions):
            raise ValueError("Weld tab positions cannot be negative.")
        
        if any(pos > self._x_body_length for pos in self._weld_tab_positions):
            raise ValueError("Weld tab positions cannot be greater than the length of the current collector.")
        
    def _check_and_copy_weld_tab(self, weld_tab: WeldTab) -> None:

        if not isinstance(weld_tab, WeldTab):
            raise TypeError("Weld tab must be an instance of WeldTab.")
        
        self._weld_tabs = [deepcopy(weld_tab) for _ in self._weld_tab_positions]
        tab_y_center = (self._y_body_length / 2 + self._tab_overhang - self._weld_tabs[0]._length / 2) * M_TO_MM

        for _pos, _tab in zip(self._weld_tab_positions, self._weld_tabs):
            pos = (_pos - self._x_body_length / 2) * M_TO_MM
            _tab.datum = (pos, tab_y_center)

    def _check_tab_overhang(self, tab_overhang: float) -> None:
        
        if not isinstance(tab_overhang, (int, float)):
            raise TypeError("Tab overhang must be a number.")
        
        if tab_overhang < 0:
            raise ValueError("Tab overhang cannot be negative.")
        
        self._tab_overhang = float(tab_overhang) * MM_TO_M

    def _check_skip_coat_width(self, skip_coat_width: float) -> None:

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

    def _check_tab_weld_side(self, tab_weld_side: str) -> None:

        if tab_weld_side not in ['a', 'b']:
            raise ValueError("Tab weld side must be either 'a' or 'b'.")
        
        self._tab_weld_side = tab_weld_side

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
            tr.name = 'Weld Tabs' if i == 0 else ''
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

        area = get_area_from_trace(trace)
        
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
            name='A Side Coated Area',
            line=dict(width=1, color='black'),
            fillcolor='black',
            fill='toself',
            fillpattern=self._am_fill_pattern
        )

        if 'tab_number' in coated_area.columns:
            area = (coated_area
                           .dropna()
                           .groupby('tab_number')
                           .apply(lambda df: get_area_from_trace(go.Scatter(x=df['x'], y=df['y'], mode='lines')))
                           .sum()
                           )
        else:
            area = get_area_from_trace(trace)

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














