from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial
from App.styles import *
from SteerEnergyStorage.Constants import *
from abc import ABC, abstractmethod
from typing import Tuple, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from copy import deepcopy
from pathlib import Path


class _CurrentCollector(ABC):

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 thickness: float,
                 **kwargs):
        """
        Initialize an object that represents a current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param x_body_length: float: length of the current collector in mm
        :param y_body_length: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        """
        # Database values
        self._check_material(material)
        self._check_x_body_length(x_body_length)
        self._check_y_body_length(y_body_length)
        self._check_thickness(thickness)

        self._fill_pattern = dict(shape='/', size=20, solidity=0.6, fgcolor=self._material._color)

    def _check_material(self, material: CurrentCollectorMaterial):

        if not isinstance(material, CurrentCollectorMaterial):
            raise TypeError("Material must be an instance of CurrentCollectorMaterial.")
        
        self._material = material

    def _check_x_body_length(self, x_body_length: float):

        if not isinstance(x_body_length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if x_body_length <= 0:
            raise ValueError("Length cannot be negative or equal to 0.")
        
        self._x_body_length = float(x_body_length) * MM_TO_M

    def _check_y_body_length(self, y_body_length: float):

        if not isinstance(y_body_length, (int, float)):
            raise TypeError("Width must be a number.")
        
        if y_body_length <= 0:
            raise ValueError("Width cannot be negative or equal to 0.")
        
        self._y_body_length = float(y_body_length) * MM_TO_M

    def _check_thickness(self, thickness: float):

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M

    @property
    def x_body_length(self) -> float:
        return round(self._x_body_length * M_TO_MM, 2)
    
    @property
    def y_body_length(self) -> float:
        return round(self._y_body_length * M_TO_MM, 2)
    
    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @abstractmethod
    def _calculate_properties(self):
        pass

    @abstractmethod
    def get_a_side_view(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs):
        """
        Visualize the current collector.
        """
        pass

    @abstractmethod
    def get_b_side_view(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs):
        """
        Visualize the current collector from the B side.
        """
        pass

    @property
    @abstractmethod
    def coated_area(self) -> float:
        pass

    @property
    @abstractmethod
    def area(self) -> float:
        pass

    @property
    @abstractmethod
    def mass(self) -> float:
        pass

    @property
    @abstractmethod
    def cost(self) -> float:
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}"
    
    def __repr__(self):
        return self.__str__()


class _TabbedCurrentCollector(_CurrentCollector):

    def __init__(self,
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 tab_width: float,
                 tab_height: float,
                 coated_tab_height: float,
                 thickness: float,
                 **kwargs):
        """
        Initialize an object that represents a tabbed current collector.
        
        :param material: CurrentCollectorMaterial: material of the current collector
        :param x_body_length: float: length of the current collector in mm
        :param y_body_length: float: width of the current collector in mm
        :param thickness: float: thickness of the current collector in um
        :param tab_width: float: width of the tab in mm
        :param tab_height: float: height of the tab in mm
        :param coated_tab_height: float: height of the coated tab on the top side in mm
        """
        super().__init__(material=material,
                         x_body_length=x_body_length,
                         y_body_length=y_body_length,
                         thickness=thickness,
                         **kwargs)
        
        self._check_tab_width(tab_width)
        self._check_tab_height(tab_height)
        self._check_coated_tab_height(coated_tab_height)
        
    def _check_tab_width(self, tab_width: float):

        if not isinstance(tab_width, (int, float)):
            raise TypeError("Tab width must be a number.")
        
        if tab_width < 0:
            raise ValueError("Tab width cannot be negative.")
        
        self._tab_width = float(tab_width) * MM_TO_M

        if self._tab_width > self._x_body_length:
            raise ValueError("Tab width cannot be greater than the length of the current collector.")

    def _check_tab_height(self, tab_height: float):

        if not isinstance(tab_height, (int, float)):
            raise TypeError("Tab height must be a number.")
        
        if tab_height < 0:
            raise ValueError("Tab height cannot be negative.")
        
        self._tab_height = float(tab_height) * MM_TO_M

    def _check_coated_tab_height(self, coated_tab_height: float):

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


class _TapeCurrentCollector(_CurrentCollector):

    def __init__(self,
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 thickness: float,
                 bare_lengths_a_side: Tuple[float, float] = (0,0),
                 bare_lengths_b_side: Tuple[float, float] = (0,0),
                 **kwargs
                 ):
        
        super().__init__(material=material,
                         x_body_length=x_body_length,
                         y_body_length=y_body_length,
                         thickness=thickness)
        
        self._check_bare_lengths_a_side(bare_lengths_a_side)
        self._check_bare_lengths_b_side(bare_lengths_b_side)

    def _check_bare_lengths_a_side(self, bare_lengths_a_side: Tuple[float, float]):

        if not isinstance(bare_lengths_a_side, tuple) or len(bare_lengths_a_side) != 2:
            raise TypeError("Bare lengths on A side must be a tuple of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in bare_lengths_a_side):
            raise TypeError("Bare lengths on A side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_a_side):
            raise ValueError("Bare lengths on A side cannot be negative.")
        
        self._bare_lengths_a_side = tuple(float(length) * MM_TO_M for length in bare_lengths_a_side)

        if self._x_body_length < sum(self._bare_lengths_a_side):
            raise ValueError("Total bare lengths on A side cannot be greater than the length of the current collector.")

    def _check_bare_lengths_b_side(self, bare_lengths_b_side: Tuple[float, float]):

        if not isinstance(bare_lengths_b_side, tuple) or len(bare_lengths_b_side) != 2:
            raise TypeError("Bare lengths on B side must be a tuple of two floats.")
        
        if any(not isinstance(length, (int, float)) for length in bare_lengths_b_side):
            raise TypeError("Bare lengths on B side must be numbers.")
        
        if any(length < 0 for length in bare_lengths_b_side):
            raise ValueError("Bare lengths on B side cannot be negative.")
        
        self._bare_lengths_b_side = tuple(float(length) * MM_TO_M for length in bare_lengths_b_side)

        if self._x_body_length < sum(self._bare_lengths_b_side):
            raise ValueError("Total bare lengths on B side cannot be greater than the length of the current collector.")

    def _get_full_view(self):
        pass

    def get_view(self, aspect_ratio: float = 3, side: str = 'a', **kwargs):
        """
        Visualize the notched current collector.
        If the collector is long, split into two subplots for left and right ends with split indicators.
        The vertical datum is centered at y = self.width / 2.
        
        :param aspect_ratio: float: aspect ratio of the plot, default is 3
        :param side: str: 'a' or 'b' to indicate which side to visualize
        """
        if side.lower() not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")

        max_x = self.y_body_length * aspect_ratio

        if max_x > self.x_body_length:
            figure = self._get_full_view(side=side)

        else:
            figure = make_subplots(rows=2, cols=1, vertical_spacing=0.2, subplot_titles=[f"{side.upper()} side start", f"{side.upper()} side end"])
            figure1 = self._get_full_view(side=side)
            figure2 = self._get_full_view(side=side)
            for trace in figure1.data:
                figure.add_trace(trace, row=1, col=1)
            for trace in figure2.data:
                figure.add_trace(trace, row=2, col=1)
            top_row_range = [-self.x_body_length / 2, -self.x_body_length / 2 + max_x]
            bottom_row_range = [self.x_body_length / 2 - max_x, self.x_body_length / 2]
            figure.update_xaxes(range=top_row_range, row=1, col=1)
            figure.update_xaxes(range=bottom_row_range, row=2, col=1)

        figure.update_layout(
            xaxis=dict(scaleanchor='y', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            xaxis2=dict(scaleanchor='y', title='', showgrid=False, zeroline=False, showticklabels=False),
            yaxis2=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return figure

    def get_a_side_view(self, **kwargs):
        return self.get_view(aspect_ratio=3, side='a', **kwargs)
    
    def get_b_side_view(self, **kwargs):
        return self.get_view(aspect_ratio=3, side='b', **kwargs)

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

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 width: float,
                 height: float,
                 thickness: float,
                 tab_width: float,
                 tab_height: float,
                 tab_position: float,
                 coated_tab_height: float = 0
                 ):
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
                         thickness=thickness)
        
        self._check_tab_position(tab_position)
        self._calculate_properties()

    def _check_tab_position(self, tab_position: float):

        if not isinstance(tab_position, (int, float)):
            raise TypeError("Tab position must be a number.")
        
        self._tab_position = float(tab_position) * MM_TO_M
        
        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")
        
        if self._tab_position + self._tab_width / 2 > self.x_body_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")

    def _calculate_properties(self):
        """
        Calculate the properties of the punched current collector.
        """
        self._main_body_area = self._x_body_length * self._y_body_length
        self._tab_area = self._tab_width * self._tab_height
        self._area = self._main_body_area + self._tab_area
        self._volume = self._area * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost

        self._coated_area_a_side = (self._main_body_area + (self._tab_width * self._coated_tab_height)) * 2
        self._coated_area_b_side = (self._main_body_area + (self._tab_width * self._coated_tab_height)) * 2
        self._coated_area = self._coated_area_a_side + self._coated_area_b_side

    def _get_footprint(self, 
                       start_position: Tuple[float, float], 
                       notch_height: float = None
                       ) -> pd.DataFrame:
        """
        Get the footprint of the current collector.

        :param start_position: Tuple[float, float]: starting position of the current collector in mm, default is (-x_body_length/2, -y_body_length/2)
        :param notch_height: float: height of the notch in mm, default is self.tab_height
        """
        x_steps = [0, 
                   self.tab_position - self.tab_width/2, 
                   0, 
                   self.tab_width, 
                   0, 
                   self.x_body_length - self.tab_position - self.tab_width/2, 
                   0, 
                   -self.x_body_length]
        
        y_steps = [self.y_body_length,
                   0,
                   notch_height,
                   0,
                   -notch_height,
                   0,
                   -self.y_body_length,
                   0]
        
        coordinates = [start_position]
        for x, y in zip(x_steps, y_steps):
            new_x = coordinates[-1][0] + x
            new_y = coordinates[-1][1] + y
            coordinates.append((new_x, new_y))

        return pd.DataFrame(coordinates, columns=['x', 'y'])

    def _get_view(self, 
                  with_dimensions: bool = True,
                  paper_bgcolor='white', 
                  plot_bgcolor='white', 
                  **kwargs) -> go.Figure:
        
        start_point = (-self.x_body_length / 2, -self.y_body_length / 2)
        notch = self.coated_tab_height

        body = self._get_footprint(start_position=start_point, notch_height=self.tab_height)
        coated_area = self._get_footprint(start_position=start_point, notch_height=notch)

        # Basic shapes        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=body['x'], y=body['y'], mode='lines', name='Body', line=dict(width=1, color='black'), fillcolor=self._material._color, fill='toself'))
        fig.add_trace(go.Scatter(x=coated_area['x'], y=coated_area['y'], mode='lines', name='Coated Area', line=dict(width=1, color='black'), fillcolor='black', fill='toself', fillpattern=self._fill_pattern))

        if with_dimensions:
            # bounding area
            pad = 0.05

            # width line
            xmin = start_point[0]
            xmax = start_point[0] + self.x_body_length
            xmid = (xmin + xmax) / 2
            y = start_point[1] - pad*self.y_body_length
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=-12, text=f'Width: {self.x_body_length} mm')

            # height line
            x = start_point[0] - pad * self.x_body_length
            ymin = start_point[1]
            ymax = start_point[1] + self.y_body_length
            ymid = (ymin + ymax) / 2
            fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=-12, text=f'Height: {self.y_body_length} mm', textangle=-90)

            # tab position line
            y = start_point[1] + self.y_body_length + self.tab_height + (4 * pad * self.y_body_length)
            xmin = start_point[0]
            xmax = start_point[0] + self.tab_position
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Position: {self.tab_position} mm')           

            # tab width line
            y = start_point[1] + self.y_body_length + self.tab_height + (pad * self.y_body_length)
            xmin = start_point[0] + self.tab_position - self.tab_width / 2
            xmax = start_point[0] + self.tab_position + self.tab_width / 2
            xmid = (xmin + xmax) / 2
            fig.add_annotation(x=xmax, ax=xmin, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmin, ax=xmax, y=y, ay=y, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=xmid, y=y, xref='x', yref='y', showarrow=False, yshift=12, text=f'Tab Width: {self.tab_width} mm')

            # tab height line 
            if self.tab_position > self.width / 2:
                x = start_point[0] + self.tab_position - self.tab_width / 2 - (pad * self.x_body_length)
                xshift = -80
            else:
                x = start_point[0] + self.tab_position + self.tab_width / 2 + (pad * self.x_body_length)
                xshift = 80
            
            ymin = start_point[1] + self.y_body_length
            ymax = start_point[1] + self.y_body_length + self.tab_height
            ymid = (ymin + ymax) / 2
            fig.add_annotation(x=x, ax=x, y=ymax, ay=ymin, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=x, ax=x, y=ymin, ay=ymax, xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=2, arrowsize=1.2)
            fig.add_annotation(x=x, y=ymid, xref='x', yref='y', showarrow=False, xshift=xshift, text=f'Tab Height: {self.tab_height} mm')

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='', showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, title='', showticklabels=False),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            **kwargs
        )

        return fig
    
    def get_a_side_view(self,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        **kwargs) -> go.Figure:
        
        return self._get_view(paper_bgcolor=paper_bgcolor, plot_bgcolor=plot_bgcolor, **kwargs)

    def get_b_side_view(self,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        **kwargs) -> go.Figure:
        
        return self._get_view(paper_bgcolor=paper_bgcolor, plot_bgcolor=plot_bgcolor, **kwargs)
                        
    @property
    def tab_position(self) -> float:
        return round(self._tab_position * M_TO_MM, 2)

    @property
    def area(self) -> float:
        return round(self._area * M_TO_MM**2, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_MM**2, 2)

    @property
    def width(self) -> float:
        return self.x_body_length
    
    @property
    def height(self) -> float:
        return self.y_body_length


class NotchedCurrentCollector(_TabbedCurrentCollector, _TapeCurrentCollector):

    def __init__(self, 
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
                 ):
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
                         bare_lengths_b_side=bare_lengths_b_side)

        self._check_tab_spacing(tab_spacing)
        self._calculate_properties()

    def _check_tab_spacing(self, tab_spacing: float):

        if not isinstance(tab_spacing, (int, float)):
            raise TypeError("Tab spacing must be a number.")
        
        if tab_spacing < 0:
            raise ValueError("Tab spacing cannot be negative.")
        
        self._tab_spacing = float(tab_spacing) * MM_TO_M
        self._tab_gap = self._tab_spacing - self._tab_width

        if self._tab_gap < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")
        
    def _calculate_properties(self):
        self._calculate_tab_positions()
        self._calculate_covered_area()
        self._calculate_area()
        self._volume = self._area * self._thickness
        self._mass = self._volume * self._material._density
        self._cost = self._mass * self._material._specific_cost
        self._total_height = self._y_body_length + self._tab_height

    def _calculate_tab_positions(self):
        """
        Function to calculate the positions of the tabs along the length of the current collector.
        """
        number_of_tabs = int(self._x_body_length // self._tab_spacing) + 1
        tab_positions = [self._tab_spacing * i + self._tab_spacing/2 for i in range(number_of_tabs) if self._tab_spacing * i + self._tab_spacing/2 - self._tab_width / 2 < self._x_body_length]
        tab_start_positions = [pos - self._tab_width / 2 for pos in tab_positions]
        tab_end_positions = [pos + self._tab_width / 2 if pos + self._tab_width / 2 < self._x_body_length else self._x_body_length for pos in tab_positions]
        self._tab_positions = [(s, e) for s, e in zip(tab_start_positions, tab_end_positions)]

    def _calculate_area(self):
        """
        Calculate the area of the current collector.
        """
        area = self._x_body_length * self._y_body_length
        
        for tab_start, tab_end in self._tab_positions:
            tab_length = tab_end - tab_start
            area += tab_length * self._tab_height

        self._area = area

    def _calculate_covered_area(self):
        """
        Calculate the area of the current collector that is coated with the electrode material.
        """
        a_side_covered_length = self._x_body_length - sum(self._bare_lengths_a_side)
        a_side_covered_area = (a_side_covered_length * self._y_body_length)

        for tab_start, tab_end in self._tab_positions:
            tab_length = tab_end - tab_start
            a_side_covered_area += tab_length * self._coated_tab_height

        b_side_covered_length = self._x_body_length - sum(self._bare_lengths_b_side)
        b_side_covered_area = (b_side_covered_length * self._y_body_length)

        for tab_start, tab_end in self._tab_positions:
            tab_length = tab_end - tab_start
            b_side_covered_area += tab_length * self._coated_tab_height

        self._coated_area_a_side = a_side_covered_area
        self._coated_area_b_side = b_side_covered_area
        self._coated_area = a_side_covered_area + b_side_covered_area
    
    def _get_footprint(self,
                       start_position: Tuple[float, float],
                       notch_height: Optional[float] = None,
                       bare_lengths: Tuple[float, float] = (0, 0),
                       ) -> pd.DataFrame:
        """
        Return a closed polyline (as a DataFrame of x/y points) for the
        notched current collector “footprint.”  The rectangle is traced from
        left to right, with vertical “tabs” (notches) added along the top edge.

        Parameters
        ----------
        start_position : Tuple[float, float]
            The (x, y) offset to add to every point at the very end.
            (For example, if you want the shape to be centered at some other origin.)

        notch_height : Optional[float]
            The vertical height of each notch (i.e. how far above y_body_length
            the tab pokes).  If None, we default to self.tab_height.

        bare_lengths : Tuple[float, float]
            (bare_left, bare_right), in the same units as self.x_body_length.  This
            enforces that the footprint does not draw any tabs (or vertical edges)
            for the first `bare_left` mm on the left, and the last `bare_right` mm
            on the right.  In other words, the top edge will run horizontally from
            x = bare_left to x = x_body_length − bare_right, with tabs only in between.
        """
        notch_height = self.tab_height if notch_height is None else notch_height

        bare_left, bare_right = bare_lengths
        x_min = bare_left
        x_max = self.x_body_length - bare_right
        y_top = self.y_body_length

        points = []

        # --------------------------------------------
        # 3. Start at the bottom‐left corner: (x_min, 0)
        # --------------------------------------------
        points.append((x_min, 0))

        # --------------------------------------------
        # 4. Go straight up to the top edge at x = x_min
        # --------------------------------------------
        points.append((x_min, y_top))

        # --------------------------------------------
        # 5. Now loop over each (start, end) in self.tab_positions,
        #    but skip any tab lying entirely outside [x_min, x_max].
        #    Also clip the tab footprint to [x_min, x_max].
        # --------------------------------------------
        for tab_start, tab_end in self.tab_positions:
            # If this tab is completely to the left or right of [x_min, x_max], skip it
            if tab_end < x_min or tab_start > x_max:
                continue

            # Clip the tab footprint to stay within [x_min, x_max]
            clipped_start = max(tab_start, x_min)
            clipped_end = min(tab_end, x_max)

            # 5a. If our last appended point isn't already at (clipped_start, y_top),
            #     then draw the horizontal run up to clipped_start.
            last_x, last_y = points[-1]
            if not (last_x == clipped_start and last_y == y_top):
                points.append((clipped_start, y_top))

            # 5b. Draw the “vertical leg” of the notch up from y_top → y_top + notch_height
            points.append((clipped_start, y_top))
            points.append((clipped_start, y_top + notch_height))

            # 5c. Draw across the top of the notch (from clipped_start → clipped_end)
            points.append((clipped_end, y_top + notch_height))

            # 5d. Draw down from (clipped_end, y_top + notch_height) to (clipped_end, y_top)
            points.append((clipped_end, y_top))

            # 5e. Now move horizontally from clipped_end → either (clipped_end + tab_gap)
            #     or x_max, whichever is smaller.
            next_horiz = min(clipped_end + self.tab_gap, x_max)
            points.append((next_horiz, y_top))

        # --------------------------------------------
        # 6. After looping all tabs, our “current point” should be somewhere on the
        #    top edge.  If that x < x_max, draw one last segment to (x_max, y_top).
        # --------------------------------------------
        last_x, last_y = points[-1]
        if last_y == y_top and last_x < x_max:
            points.append((x_max, y_top))

        # --------------------------------------------
        # 7. Drop down from (x_max, y_top) straight to (x_max, 0)
        # --------------------------------------------
        points.append((x_max, 0))

        # --------------------------------------------
        # 8. Finally, close the loop by returning to (x_min, 0)
        # --------------------------------------------
        points.append((x_min, 0))

        # --------------------------------------------
        # 9. Convert to DataFrame and apply `start_position` offset
        # --------------------------------------------
        df = (pd
              .DataFrame(points, columns=["x", "y"])
              .assign(x=lambda df: df["x"] + start_position[0], y=lambda df: df["y"] + start_position[1])
              .reset_index(drop=True)
              )

        return df

    def _get_full_view(self, side: str = 'a') -> go.Figure:
        """
        Visualize the notched current collector from the A side.
        """
        if side.lower() not in ['a', 'b']:
            raise ValueError("Side must be 'a' or 'b'.")
        
        start_point = (-self.x_body_length / 2, -self.y_body_length / 2)
        main_body = self._get_footprint(start_point, notch_height=self.tab_height)
        bare_lengths = self.bare_lengths_a_side if side.lower() == 'a' else self.bare_lengths_b_side
        coated_area = self._get_footprint(start_point, notch_height=self.coated_tab_height, bare_lengths=bare_lengths)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=main_body['x'], y=main_body['y'], mode='lines', name='Main Body', line=dict(width=1, color='black'), fillcolor=self._material._color, fill='toself'))
        fig.add_trace(go.Scatter(x=coated_area['x'], y=coated_area['y'], mode='lines', name='Coated Area', line=dict(width=1, color='black'), fillcolor='black', fill='toself', fillpattern=self._fill_pattern))

        return fig
    
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
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def area(self) -> float:
        return round(self._area * M_TO_MM**2, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_MM**2, 2)
    
    @property
    def coated_area_a_side(self) -> float:
        return round(self._coated_area_a_side * M_TO_MM**2, 2)
    
    @property
    def coated_area_b_side(self) -> float:
        return round(self._coated_area_b_side * M_TO_MM**2, 2)

    @property
    def total_height(self) -> float:
        return round(self._total_height * M_TO_MM, 2)


class TablessCurrentCollector(NotchedCurrentCollector):

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 length: float,
                 width: float,
                 coated_width: float,
                 thickness: float,
                 bare_lengths_a_side: Tuple[float, float] = (0, 0),
                 bare_lengths_b_side: Tuple[float, float] = (0, 0)):
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

        super().__init__(material=material,
                         length=length,
                         width=width,
                         thickness=thickness,
                         tab_height=tab_height,
                         tab_width=length,
                         tab_spacing=length,
                         coated_tab_height=0,
                         bare_lengths_a_side=bare_lengths_a_side,
                         bare_lengths_b_side=bare_lengths_b_side)
        
        self._check_coated_width(coated_width)

    def _check_coated_width(self, coated_width: float):

        if not isinstance(coated_width, (int, float)):
            raise TypeError("Coated width must be a number.")
        
        if coated_width < 0:
            raise ValueError("Coated width cannot be negative.")
        
        self._coated_width = float(coated_width) * MM_TO_M
        
        if self._coated_width > self._y_body_length:
            raise ValueError("Coated width cannot be greater than the width of the current collector.")
        
    @property
    def coated_width(self) -> float:
        return round(self._coated_width * M_TO_MM, 2)
    
    @property
    def width(self) -> float:
        return round((self._y_body_length + self._tab_height) * M_TO_MM, 2)

# class TabWeldedCurrentCollector(CurrentCollector):

#     def __init__(self,
#                  formula: str,
#                  length: float,
#                  width: float,
#                  thickness: float,
#                  weld_tab: WeldTab,
#                  weld_tab_spacing: float,
#                  first_tab_spacing: float,
#                  bare_length: float,
#                  specific_cost: float = None,
#                  density: float = None):
#         """
#         Initialize an object that represents a current collector with tabs welded on it.

#         :param formula: str: chemical formula of the material
#         :param length: float: length of the current collector in mm
#         :param width: float: width of the current collector in mm
#         :param thickness: float: thickness of the current collector in um
#         :param weld_tab: WeldTab: object representing the weld tab
#         :param weld_tab_spacing: float: spacing between the tabs in mm
#         :param first_tab_spacing: float: spacing between the first tab and the edge of the current collector in mm
#         :param bare_length: float: length of the current collector that is not coated with the electrode material in mm
#         :param specific_cost: float: specific cost of the material $/kg.
#         :param density: float: density of the material in g/cm^3
#         """
#         self._check_weld_tab_spacing(weld_tab_spacing, weld_tab)
#         self._check_width(width)
#         self._check_length(length)
#         self._check_first_tab_spacing(first_tab_spacing, weld_tab)
#         self._check_bare_length(bare_length)
#         self._check_and_copy_weld_tab(weld_tab)

#         bare_area = self._calculate_bare_area()

#         super().__init__(formula=formula,
#                          length=length,
#                          width=width,
#                          bare_area=bare_area,
#                          thickness=thickness,
#                          specific_cost=specific_cost,
#                          density=density)

#     def _check_weld_tab_spacing(self, weld_tab_spacing: float, weld_tab: WeldTab):

#         if not isinstance(weld_tab_spacing, (int, float)):
#             raise TypeError("Weld tab spacing must be a number.")
        
#         if weld_tab_spacing < 0:
#             raise ValueError("Weld tab spacing cannot be negative.")
        
#         self._weld_tab_spacing = float(weld_tab_spacing) * MM_TO_M

#     def _check_first_tab_spacing(self, first_tab_spacing: float, weld_tab: WeldTab):
        
#         if not isinstance(first_tab_spacing, (int, float)):
#             raise TypeError("First tab spacing must be a number.")
        
#         if first_tab_spacing < 0:
#             raise ValueError("First tab spacing cannot be negative.")
                
#         self._first_tab_spacing = float(first_tab_spacing) * MM_TO_M

#         if self._first_tab_spacing + weld_tab._width > self._length:
#             raise ValueError("First tab spacing cannot be greater than the length of the current collector.")

#     def _check_bare_length(self, bare_length: float):
        
#         if not isinstance(bare_length, (int, float)):
#             raise TypeError("Bare length must be a number.")
        
#         if bare_length < 0:
#             raise ValueError("Bare length cannot be negative.")
        
#         self._bare_length = float(bare_length) * MM_TO_M

#     def _check_and_copy_weld_tab(self, weld_tab: WeldTab):

#         if not isinstance(weld_tab, WeldTab):
#             raise TypeError("Weld tab must be a WeldTab object.")
        
#         if weld_tab._length < self._width:
#             raise ValueError("The length of the weld tab must be greater than the width of the current collector.")
        
#         tab = deepcopy(weld_tab)
#         tab._position = self._first_tab_spacing + tab._width/2
#         tab._name = f'{weld_tab._name}_1'
#         self._weld_tabs = [tab]
#         _remaining_length = self._length - self._first_tab_spacing - weld_tab._width


#         while _remaining_length > weld_tab._width:
#             if _remaining_length > self._weld_tab_spacing + weld_tab._width:
#                 tab = deepcopy(weld_tab)
#                 tab._position = self._weld_tabs[-1]._position + self._weld_tab_spacing + tab._width
#                 tab._name = f'{weld_tab._name}_{len(self._weld_tabs) + 1}'
#                 self._weld_tabs.append(tab)
#                 _remaining_length -= self._weld_tab_spacing + weld_tab._width
#             else:
#                 break

#         self._weld_tab_positions = [tab._position for tab in self._weld_tabs]

#     def _calculate_bare_area(self):
#         """
#         Function to calculate the area of the current collector that is not coated with the electrode material. All inputs are in cm.
#         """
#         bare_area = self._width * self._bare_length

#         for tab in self._weld_tabs:
#             coat_point = self._length - self._bare_length
#             tab_start = tab._position - tab._width/2
#             tab_end = tab._position + tab._width/2

#             if tab_end < coat_point:
#                 bare_area += tab._width * self._width
#             elif tab_start > coat_point:
#                 bare_area += 0
#             elif tab_end > coat_point and tab_start < coat_point:
#                 bare_area += (coat_point - tab_start) * self._width
        
#         return bare_area * M_TO_MM**2

#     def _calculate_properties(self):
#         self._coated_area = (self._length * self._width) - self._bare_area
#         self._area = self._length * self._width
#         self._volume = self._length * self._width * self._thickness + sum([tab._volume for tab in self._weld_tabs])
#         self._mass = self._volume * self._density + sum([tab._mass for tab in self._weld_tabs])
#         self._cost = self._mass * self._specific_cost + sum([tab._cost for tab in self._weld_tabs])

#     def get_top_down_view(self, width = None, height = None):
#         """
#         Visualize the tab welded current collector.
#         """
#         fig = go.Figure()

#         bottom_left = (0, 0)
#         bottom_right = (self.length, 0)
#         top_right = (self.length, self.width)
#         top_left = (0, self.width)
#         x = [bottom_left[0], bottom_right[0], top_right[0], top_left[0], bottom_left[0]]
#         y = [bottom_left[1], bottom_right[1], top_right[1], top_left[1], bottom_left[1]]
#         main_body = pd.DataFrame({'x': x, 'y': y})
#         fig.add_trace(go.Scatter(x=main_body['x'], y=main_body['y'], mode='lines', name='Main Body', line=dict(width=0), fillcolor='grey', fill='toself'))

#         covered_bottom_left = (0, 0)
#         covered_bottom_right = (self.length - self.bare_length, 0)
#         covered_top_right = (self.length - self.bare_length, self.width)
#         covered_top_left = (0, self.width)
#         x = [covered_bottom_left[0], covered_bottom_right[0], covered_top_right[0], covered_top_left[0], covered_bottom_left[0]]
#         y = [covered_bottom_left[1], covered_bottom_right[1], covered_top_right[1], covered_top_left[1], covered_bottom_left[1]]
#         covered_area = pd.DataFrame({'x': x, 'y': y})
#         fig.add_trace(go.Scatter(x=covered_area['x'], y=covered_area['y'], mode='lines', name='Covered Area', line=dict(width=0), fillcolor='black', fill='toself'))

#         for tab in self._weld_tabs:
#             tab_bottom_left = (tab.position - tab.width/2, 0)
#             tab_bottom_right = (tab.position + tab.width/2, 0)
#             tab_top_right = (tab.position + tab.width/2, tab.length)
#             tab_top_left = (tab.position - tab.width/2, tab.length)
#             x = [tab_bottom_left[0], tab_bottom_right[0], tab_top_right[0], tab_top_left[0], tab_bottom_left[0]]
#             y = [tab_bottom_left[1], tab_bottom_right[1], tab_top_right[1], tab_top_left[1], tab_bottom_left[1]]
#             tab_plot = pd.DataFrame({'x': x, 'y': y})
#             fig.add_trace(go.Scatter(x=tab_plot['x'], y=tab_plot['y'], mode='lines', name=tab.name, line=dict(width=0), fillcolor='silver', fill='toself'))

#         if width is not None:
#             fig.update_layout(width=width)
#         if height is not None:
#             fig.update_layout(height=height)

#         fig.update_layout(title=f'{self._name} Current Collector',
#                           xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='Length (mm)'),
#                           yaxis=dict(showgrid=False, zeroline=False, title='Width (mm)'),
#                           paper_bgcolor='white',
#                           plot_bgcolor='white',
#                           showlegend=False)

#         return fig

#     @property
#     def weld_tab_spacing(self) -> float:
#         return round(self._weld_tab_spacing * M_TO_MM, 2)
    
#     @property
#     def first_tab_spacing(self) -> float:
#         return round(self._first_tab_spacing * M_TO_MM, 2)
    
#     @property
#     def bare_length(self) -> float:
#         return round(self._bare_length * M_TO_MM, 2)










# class WeldTab:

#     def __init__(self,
#                  formula: str,
#                  width: float,
#                  length: float,
#                  thickness: float,
#                  specific_cost: float = None,
#                  name: str = 'Tab'):
#         """
#         Initialize an object that represents a weld tab used on current collectors

#         :param formula: str: chemical formula of the material
#         :param width: float: width of the tab in mm
#         :param length: float: length of the tab in mm
#         :param thickness: float: thickness of the tab in um
#         :param specific_cost: float: specific cost of the material $/kg.
#         :param name: str: name of the material
#         """
#         self._check_name(name)
#         self._check_formula(formula)
#         self._check_width(width)
#         self._check_length(length)
#         self._check_thickness(thickness)
#         self._calculate_properties()
#         self._check_specific_cost(specific_cost)

#     def _check_name(self, name: str):
        
#         if not isinstance(name, str):
#             raise TypeError("Name must be a string.")
        
#         self._name = name

#     def _check_formula(self, formula: str):
#         """
#         Check if the formula is a string.
#         """
#         if not isinstance(formula, str):
#             raise TypeError("Formula must be a string.")
        
#         self._formula = formula

#     def _check_width(self, width: float):
        
#         if not isinstance(width, (int, float)):
#             raise TypeError("Width must be a number.")
        
#         if width < 0:
#             raise ValueError("Width cannot be negative.")
        
#         self._width = float(width) * MM_TO_M

#     def _check_length(self, length: float):

#         if not isinstance(length, (int, float)):
#             raise TypeError("Length must be a number.")
        
#         if length < 0:
#             raise ValueError("Length cannot be negative.")
        
#         self._length = float(length) * MM_TO_M

#     def _check_thickness(self, thickness: float):

#         if not isinstance(thickness, (int, float)):
#             raise TypeError("Thickness must be a number.")
        
#         if thickness < 0:
#             raise ValueError("Thickness cannot be negative.")
        
#         self._thickness = float(thickness) * UM_TO_M

#     def _calculate_properties(self):
#         """
#         Calculate the properties of the tab.
#         """
#         self._volume = self._width * self._length * self._thickness
#         self._mass = self._volume * self._density
#         self._cost = self._mass * self._specific_cost

#     def _check_specific_cost(self, specific_cost: float):

#         if specific_cost is not None:
#             if not isinstance(specific_cost, (int, float)):
#                 raise TypeError("Specific cost must be a number.")
            
#             if specific_cost < 0:
#                 raise ValueError("Specific cost cannot be negative.")
            
#             self._specific_cost = float(specific_cost)

#     @property
#     def formula(self) -> str:
#         return self._formula
    
#     @property
#     def width(self) -> float:
#         return round(self._width * M_TO_MM, 2)
    
#     @property
#     def length(self) -> float:
#         return round(self._length * M_TO_MM, 2)
    
#     @property
#     def thickness(self) -> float:
#         return round(self._thickness * M_TO_UM, 2)

#     @property
#     def name(self) -> str:
#         return self._name.title()
        
#     @property
#     def specific_cost(self) -> float:
#         return self._specific_cost
    
#     @property
#     def density(self) -> float:
#         return round(self._density * KG_TO_G / M_TO_CM**3, 2)

#     @property
#     def position(self) -> float:
#         if hasattr(self, '_position'):
#             return self._position * M_TO_MM
#         else:
#             raise AttributeError("The position of the tab has not been set. Put in a TabWeldedCurrentCollector object to calculate the position.")

#     @property
#     def volume(self) -> float:
#         return round(self._volume * M_TO_CM**3, 2)
    
#     @property
#     def mass(self) -> float:
#         return round(self._mass * KG_TO_G, 2)
    
#     @property
#     def cost(self) -> float:
#         return round(self._cost, 2)





