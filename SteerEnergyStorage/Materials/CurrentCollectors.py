from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial
from App.styles import *
from SteerEnergyStorage.Constants import *
from abc import ABC, abstractmethod
from typing import Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from copy import deepcopy
from pathlib import Path


class CurrentCollector(ABC):

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 thickness: float):
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


class PunchedCurrentCollector(CurrentCollector):

    def __init__(self, 
                 material: CurrentCollectorMaterial,
                 x_body_length: float,
                 y_body_length: float,
                 thickness: float,
                 tab_width: float,
                 tab_height: float,
                 tab_position: float,
                 coated_tab_height_a_side: float = 0,
                 coated_tab_height_b_side: float = 0
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
        :param coated_tab_height_a_side: float: height of the covered tab on the top side in mm
        :param coated_tab_height_b_side: float: height of the covered tab on the bottom side in mm
        """
        super().__init__(material=material,
                         x_body_length=x_body_length,
                         y_body_length=y_body_length,
                         thickness=thickness)
        
        self._check_tab_width(tab_width)
        self._check_tab_position(tab_position)
        self._check_tab_height(tab_height)
        self._check_coated_tab_height_a_side(coated_tab_height_a_side)
        self._check_coated_tab_height_b_side(coated_tab_height_b_side)
        self._calculate_properties()

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

    def _check_tab_position(self, tab_position: float):

        if not isinstance(tab_position, (int, float)):
            raise TypeError("Tab position must be a number.")
        
        self._tab_position = float(tab_position) * MM_TO_M
        
        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")
        
        if self._tab_position + self._tab_width / 2 > self.x_body_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")

    def _check_coated_tab_height_a_side(self, coated_tab_height_a_side: float):

        if not isinstance(coated_tab_height_a_side, (int, float)):
            raise TypeError("Covered tab height on the top side must be a number.")
        
        if coated_tab_height_a_side < 0:
            raise ValueError("Covered tab height on the top side cannot be negative.")
        
        self._coated_tab_height_a_side = float(coated_tab_height_a_side) * MM_TO_M

        if self._coated_tab_height_a_side > self._tab_height:
            raise ValueError("Covered tab height on the top side cannot be greater than the tab height.")

    def _check_coated_tab_height_b_side(self, coated_tab_height_b_side: float):

        if not isinstance(coated_tab_height_b_side, (int, float)):
            raise TypeError("Covered tab height on the bottom side must be a number.")
        
        if coated_tab_height_b_side < 0:
            raise ValueError("Covered tab height on the bottom side cannot be negative.")
        
        self._coated_tab_height_b_side = float(coated_tab_height_b_side) * MM_TO_M

        if self._coated_tab_height_b_side > self._tab_height:
            raise ValueError("Covered tab height on the bottom side cannot be greater than the tab height.")

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

        self._coated_area_a_side = self._main_body_area + (self._tab_width * self._coated_tab_height_a_side)
        self._coated_area_b_side = self._main_body_area + (self._tab_width * self._coated_tab_height_b_side)
        self._coated_area = self._coated_area_a_side + self._coated_area_b_side

    def _get_footprint(self, 
                       start_position: Tuple[float, float], 
                       notch_height: float = None):
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
                  side: chr,
                  paper_bgcolor='white', 
                  plot_bgcolor='white', 
                  **kwargs):
        
        fill_pattern = dict(shape='/', size=20, solidity=0.6, fgcolor=self._material._color)
        start_point = (-self.x_body_length / 2, -self.y_body_length / 2)
        notch = self.coated_tab_height_a_side if side == 'a' else self.coated_tab_height_b_side

        body = self._get_footprint(start_position=start_point, notch_height=self.tab_height)
        covered_area = self._get_footprint(start_position=start_point, notch_height=notch)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=body['x'], y=body['y'], mode='lines', name='Body', line=dict(width=1, color='black'), fillcolor=self._material._color, fill='toself'))
        fig.add_trace(go.Scatter(x=covered_area['x'], y=covered_area['y'], mode='lines', name='Covered Area', line=dict(width=1, color='black'), fillcolor='black', fill='toself', fillpattern=fill_pattern))

        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title='x (mm)'),
            yaxis=dict(showgrid=False, zeroline=False, title='y (mm)'),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            **kwargs
        )

        return fig
    
    def get_a_side_view(self,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        **kwargs) -> go.Figure:
        
        return self._get_view(side='a', paper_bgcolor=paper_bgcolor, plot_bgcolor=plot_bgcolor, **kwargs)

    def get_b_side_view(self,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        **kwargs) -> go.Figure:
        
        return self._get_view(side='b', paper_bgcolor=paper_bgcolor, plot_bgcolor=plot_bgcolor, **kwargs)

    @property
    def tab_position(self) -> float:
        return round(self._tab_position * M_TO_MM, 2)

    @property
    def tab_width(self) -> float:
        return round(self._tab_width * M_TO_MM, 2)

    @property
    def tab_height(self) -> float:
        return round(self._tab_height * M_TO_MM, 2)

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
    def coated_tab_height_a_side(self) -> float:
        return round(self._coated_tab_height_a_side * M_TO_MM, 2)
    
    @property
    def coated_tab_height_b_side(self) -> float:
        return round(self._coated_tab_height_b_side * M_TO_MM, 2)

















class WeldTab:

    def __init__(self,
                 formula: str,
                 width: float,
                 length: float,
                 thickness: float,
                 specific_cost: float = None,
                 name: str = 'Tab'):
        """
        Initialize an object that represents a weld tab used on current collectors

        :param formula: str: chemical formula of the material
        :param width: float: width of the tab in mm
        :param length: float: length of the tab in mm
        :param thickness: float: thickness of the tab in um
        :param specific_cost: float: specific cost of the material $/kg.
        :param name: str: name of the material
        """
        self._check_name(name)
        self._check_formula(formula)
        self._check_width(width)
        self._check_length(length)
        self._check_thickness(thickness)
        self._calculate_properties()
        self._check_specific_cost(specific_cost)

    def _check_name(self, name: str):
        
        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        
        self._name = name

    def _check_formula(self, formula: str):
        """
        Check if the formula is a string.
        """
        if not isinstance(formula, str):
            raise TypeError("Formula must be a string.")
        
        self._formula = formula

    def _check_width(self, width: float):
        
        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        self._width = float(width) * MM_TO_M

    def _check_length(self, length: float):

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if length < 0:
            raise ValueError("Length cannot be negative.")
        
        self._length = float(length) * MM_TO_M

    def _check_thickness(self, thickness: float):

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M

    def _calculate_properties(self):
        """
        Calculate the properties of the tab.
        """
        self._volume = self._width * self._length * self._thickness
        self._mass = self._volume * self._density
        self._cost = self._mass * self._specific_cost

    def _check_specific_cost(self, specific_cost: float):

        if specific_cost is not None:
            if not isinstance(specific_cost, (int, float)):
                raise TypeError("Specific cost must be a number.")
            
            if specific_cost < 0:
                raise ValueError("Specific cost cannot be negative.")
            
            self._specific_cost = float(specific_cost)

    @property
    def formula(self) -> str:
        return self._formula
    
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
    def name(self) -> str:
        return self._name.title()
        
    @property
    def specific_cost(self) -> float:
        return self._specific_cost
    
    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / M_TO_CM**3, 2)

    @property
    def position(self) -> float:
        if hasattr(self, '_position'):
            return self._position * M_TO_MM
        else:
            raise AttributeError("The position of the tab has not been set. Put in a TabWeldedCurrentCollector object to calculate the position.")

    @property
    def volume(self) -> float:
        return round(self._volume * M_TO_CM**3, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)








# class NotchedCurrentCollector(CurrentCollector):

#     def __init__(self, 
#                  formula: str, 
#                  length: float,
#                  width: float,
#                  thickness: float,
#                  tab_width: float,
#                  tab_length: float,
#                  tab_spacing: float,
#                  bare_length: float,
#                  specific_cost: float,
#                  density: float
#                  ):
#         """
#         Initialize an object that represents a notched current collector.
        
#         :param name: str: name of the material
#         :param formula: str: chemical formula of the material
#         :param length: float: length of the current collector in mm
#         :param width: float: width of the current collector in mm
#         :param bare_length: float: length of the current collector that is not coated with the electrode material in mm
#         :param thickness: float: thickness of the current collector in um
#         :param density: float: density of the material in g/cm^3
#         :param tab_width: float: width of the notch in mm
#         :param tab_length: float: length of the notch in mm
#         :param tab_spacing: float: spacing between the notches in mm
#         :param specific_cost: float: specific cost of the material $/kg. 
#         :param density: float: density of the material in g/cm^3
#         """
#         self._check_tab_width(tab_width)
#         self._check_tab_length(tab_length)
#         self._check_tab_spacing(tab_spacing)
#         self._check_bare_length(bare_length)
#         self._check_length(length)
#         self._check_width(width)

#         bare_area = self._calculate_bare_tab_area(tab_width, tab_length, tab_spacing, length, bare_length, width)

#         super().__init__(formula=formula,
#                          length=length,
#                          width=width,
#                          bare_area=bare_area,
#                          thickness=thickness,
#                          specific_cost=specific_cost,
#                          density=density)

#     def _check_tab_width(self, tab_width: float):

#         if not isinstance(tab_width, (int, float)):
#             raise TypeError("Tab width must be a number.")
        
#         if tab_width < 0:
#             raise ValueError("Tab width cannot be negative.")
        
#         self._tab_width = float(tab_width) * MM_TO_M

#     def _check_tab_length(self, tab_length: float):

#         if not isinstance(tab_length, (int, float)):
#             raise TypeError("Tab length must be a number.")
        
#         if tab_length < 0:
#             raise ValueError("Tab length cannot be negative.")
        
#         self._tab_length = float(tab_length) * MM_TO_M

#     def _check_tab_spacing(self, tab_spacing: float):

#         if not isinstance(tab_spacing, (int, float)):
#             raise TypeError("Tab spacing must be a number.")
        
#         if tab_spacing < 0:
#             raise ValueError("Tab spacing cannot be negative.")
        
#         self._tab_spacing = float(tab_spacing) * MM_TO_M

#     def _check_bare_length(self, bare_length: float):
        
#         if not isinstance(bare_length, (int, float)):
#             raise TypeError("Bare length must be a number.")
        
#         if bare_length < 0:
#             raise ValueError("Bare length cannot be negative.")
        
#         self._bare_length = float(bare_length) * MM_TO_M

#     def _calculate_bare_tab_area(self, tab_width: float, tab_length: float, tab_spacing: float, length: float, bare_length: float, width: float):
#         """
#         Function to calculate the area of the current collector that is not coated with the electrode material. All inputs are in cm.
#         :param tab_width: float: width of the tabs in cm
#         :param tab_length: float: length of the tabs in cm
#         :param tab_spacing: float: spacing between the tabs in cm
#         :param length: float: length of the current collector in cm
#         :param bare_length: float: length of the current collector that is not coated with the electrode material in cm
#         """
#         if tab_spacing + tab_length > length:
#             raise ValueError("The tab spacing and length cannot be greater than the length of the current collector.")
        
#         tab_position = tab_spacing / 2 + tab_length / 2
#         tab_positions = [tab_position]
#         tab_lengths = [tab_length]

#         while tab_position < length:
#             tab_position += tab_spacing + tab_length
#             if tab_position + tab_length/2 < length:
#                 tab_positions.append(tab_position)
#                 tab_lengths.append(tab_length)
#             elif tab_position - tab_length/2 > length:
#                 pass
#             elif tab_position + tab_length/2 >= length and tab_position - tab_length/2 <= length:
#                 tab_start = tab_position - tab_length/2
#                 tab_length = length - tab_start
#                 tab_position = tab_start + tab_length/2
#                 tab_positions.append(tab_position)
#                 tab_lengths.append(tab_length)
#                 break

#         tab_areas = [l * tab_width for l in tab_lengths]

#         self._tab_positions = [t * MM_TO_M for t in tab_positions]
#         self._tab_lengths = [l * MM_TO_M for l in tab_lengths]
#         self._tab_areas = [a * MM_TO_M**2 for a in tab_areas]

#         bare_area = sum(tab_areas) + (bare_length * width)

#         return bare_area

#     def _calculate_properties(self):

#         self._coated_area = (self._length - self._bare_length) * self._width
#         self._area = self._length * self._width + sum(self._tab_areas)
#         self._volume = self._area * self._thickness
#         self._mass = self._volume * self._density
#         self._cost = self._mass * self._specific_cost
#         self._total_width = self._width + self._tab_width

#     def _make_top_down_shapes(self):

#         fig = go.Figure()
#         y_shift = -self.width / 2
#         x_shift = self.length / 2  # Shift value

#         # Main body
#         x = [0, self.length, self.length, 0, 0]
#         x = [xi - x_shift for xi in x]
#         y = [0, 0, self.width, self.width, 0]
#         y = [yi + y_shift for yi in y]
#         fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(width=1, color='black'), fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself', name='Main Body'))

#         # Covered area
#         x = [0, self.length - self.bare_length, self.length - self.bare_length, 0, 0]
#         x = [xi - x_shift for xi in x]
#         y = [0, 0, self.width, self.width, 0]
#         y = [yi + y_shift for yi in y]
#         fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(width=1, color='black'), fillcolor='black', fill='toself', name='Covered Area'))

#         # Tabs
#         for (pos, length) in zip(self._tab_positions, self._tab_lengths):
#             pos = pos * M_TO_MM
#             length = length * M_TO_MM
#             x = [pos - length/2, pos + length/2, pos + length/2, pos - length/2, pos - length/2]
#             x = [xi - x_shift for xi in x]
#             y = [self.width, self.width, self.width + self.tab_width, self.width + self.tab_width, self.width]
#             y = [yi + y_shift for yi in y]
#             y = [yi for yi in y]
#             fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(width=1, color='black'), fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself', name='Tab'))

#         return fig

#     def get_top_down_view(self, paper_bgcolor='white', plot_bgcolor='white', title=None, split=True, **kwargs):
#         """
#         Visualize the notched current collector.
#         If the collector is long, split into two subplots for left and right ends with split indicators.
#         The vertical datum is centered at y = self.width / 2.
#         """
#         split_threshold = 2
#         aspect_ratio = self.length / self.total_width
#         n_cols = 2 if aspect_ratio >= split_threshold else 1
    
#         if aspect_ratio < split_threshold or not split:
#             fig = self._make_top_down_shapes()
#             fig.update_layout(xaxis=dict(scaleanchor='y'))

#         else:
#             fig = make_subplots(rows=1, cols=n_cols, shared_yaxes=True, horizontal_spacing=0.02)
#             for trace in self._make_top_down_shapes().data:
#                 fig.add_trace(trace, row=1, col=1)
#                 fig.add_trace(trace, row=1, col=2)

#             half_window = self.total_width
#             left_xlim = [-self.length/2, -self.length/2 + half_window]
#             right_xlim = [self.length/2 - half_window, self.length/2]
#             fig.update_xaxes(range=left_xlim, row=1, col=1)
#             fig.update_xaxes(range=right_xlim, row=1, col=2)

#             # Add vertical split indicators
#             bottom_y_lim = -(self.width / 2) * 1.1
#             top_y_lim = (self.width / 2 + self.tab_width) * 1.1
#             line = dict(color="#864C39", width=6)
#             fig.add_shape(type='line', x0=left_xlim[1], x1=left_xlim[1], y0=bottom_y_lim, y1=top_y_lim, line=line, xref='x', yref='y')
#             fig.add_shape(type='line', x0=right_xlim[0], x1=right_xlim[0], y0=bottom_y_lim, y1=top_y_lim, line=line, xref='x2', yref='y2')

#             fig.update_layout(xaxis=dict(scaleanchor='y'), xaxis2=dict(scaleanchor='y'))

#         if title is None:
#             title = f'{self._name} Current Collector'

#         fig.update_layout(
#             title=title,
#             paper_bgcolor=paper_bgcolor,
#             plot_bgcolor=plot_bgcolor,
#             showlegend=False,
#             xaxis_title='x (mm)',
#             yaxis_title='y (mm)',
#             **kwargs
#         )

#         return fig

#     @property
#     def total_width(self) -> float:
#         return round(self._total_width * M_TO_MM, 2)

#     @property
#     def tab_width(self) -> float:
#         return round(self._tab_width * M_TO_MM, 2)
    
#     @property
#     def tab_length(self) -> float:
#         return round(self._tab_length * M_TO_MM, 2)
    
#     @property
#     def tab_spacing(self) -> float:
#         return round(self._tab_spacing * M_TO_MM, 2)
    
#     @property
#     def bare_length(self) -> float:
#         return round(self._bare_length * M_TO_MM, 2)


# class TablessCurrentCollector(NotchedCurrentCollector):

#     def __init__(self, 
#                  formula: str, 
#                  length: float,
#                  width: float,
#                  thickness: float,
#                  tab_width: float,
#                  bare_length: float,
#                  specific_cost: float,
#                  density: float):
#         """
#         Initialize an object that represents a tabless current collector.

#         :param name: str: name of the material
#         :param formula: str: chemical formula of the material
#         :param length: float: length of the current collector in mm
#         :param width: float: width of the current collector in mm
#         :param thickness: float: thickness of the current collector in um
#         :param tab_width: float: width of the tab in mm
#         :param bare_length: float: length of the current collector that is not coated with the electrode material in mm
#         :param specific_cost: float: specific cost of the material $/kg.
#         :param density: float: density of the material in g/cm^3
#         """

#         super().__init__(formula=formula, 
#                          length=length,
#                          width=width,
#                          thickness=thickness,
#                          tab_width=tab_width,
#                          tab_length=length,
#                          tab_spacing=0,
#                          bare_length=bare_length,
#                          specific_cost=specific_cost,
#                          density=density)


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


