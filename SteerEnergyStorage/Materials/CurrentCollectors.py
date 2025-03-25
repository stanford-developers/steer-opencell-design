from SteerEnergyStorage.DataManager import DataManager

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

CM_TO_M = 1e-2
M_TO_CM = 1e2
UM_TO_M = 1e-6
M_TO_UM = 1e6
G_TO_KG = 1e-3
KG_TO_G = 1e3

class CurrentCollector:

    def __init__(self, 
                 formula: str, 
                 length: float,
                 width: float,
                 bare_area: float,
                 thickness: float,
                 specific_cost: float = None):
        """
        Initialize an object that represents a current collector.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg. By default it will pull this from the database
        :param length: float: length of the current collector in cm
        :param width: float: width of the current collector in cm
        :param bare_area: float: area of the current collector that is not coated with the electrode material in cm^2
        :param thickness: float: thickness of the current collector in um
        :param density: float: density of the material in g/cm^3
        """
        # Database values
        self._formula = formula.capitalize()
        self.set_properties_from_database()
        self._check_formula(formula)
        self._check_specific_cost(specific_cost)
        self._check_length(length)
        self._check_width(width)
        self._check_bare_area(bare_area)
        self._check_thickness(thickness)
        self._calculate_properties()

    def _calculate_properties(self):

        self._coated_area = self._length * self._width
        self._area = (self._coated_area + self._bare_area)
        self._volume = self._area * self._thickness
        self._mass = self._volume * self._density
        self._cost = self._mass * self._specific_cost

    def _check_formula(self, formula: str):
        """
        Check if the formula is a string.
        """
        if not isinstance(formula, str):
            raise TypeError("Formula must be a string.")
        
        self._formula = formula

    def _check_specific_cost(self, specific_cost: float):

        if specific_cost is not None:
            if not isinstance(specific_cost, (int, float)):
                raise TypeError("Specific cost must be a number.")
            
            if specific_cost < 0:
                raise ValueError("Specific cost cannot be negative.")
            
            self._specific_cost = float(specific_cost)

    def _check_length(self, length: float):

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")
        
        if length < 0:
            raise ValueError("Length cannot be negative.")
        
        self._length = float(length) * CM_TO_M

    def _check_width(self, width: float):

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")
        
        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        self._width = float(width) * CM_TO_M

    def _check_bare_area(self, bare_area: float):

        if not isinstance(bare_area, (int, float)):
            raise TypeError("Bare area must be a number.")
        
        if bare_area < 0:
            raise ValueError("Bare area cannot be negative.")
        
        self._bare_area = float(bare_area) * CM_TO_M**2

    def _check_thickness(self, thickness: float):

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")
        
        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        self._thickness = float(thickness) * UM_TO_M

    def set_properties_from_database(self):
        """
        Retrieve the properties of the current collector from the database.
        """
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('current_collectors', 'formula')

        if self._formula not in available_materials:
            raise ValueError(f'{self._formula} is not available in the materials database. Allowed values are: {available_materials}')
        
        data = materials_database.get_data('current_collectors', condition=f"formula='{self._formula}'", latest_column='date')
        
        self._name = data['name'].values[0]
        self._specific_cost = data['specific_cost'].values[0]
        self._density = data['density'].values[0]
        
    def show(self):
        """
        Visualize the current collector.
        """
        bottom_left = (0, 0)
        bottom_right = (self._length, 0)
        top_right = (self._length, self._width)
        top_left = (0, self._width)

        tab_side_length = self._bare_area**0.5
        tab_bottom_left = ( self._length/2 - tab_side_length/2, self._width)
        tab_bottom_right = ( self._length/2 + tab_side_length/2, self._width)
        tab_top_right = ( self._length/2 + tab_side_length/2, self._width + tab_side_length)
        tab_top_left = ( self._length/2 - tab_side_length/2, self._width + tab_side_length)

        main_plot = pd.DataFrame({'x': [bottom_left[0], bottom_right[0], top_right[0], top_left[0], bottom_left[0]],
                                  'y': [bottom_left[1], bottom_right[1], top_right[1], top_left[1], bottom_left[1]]})

        tab_plot = pd.DataFrame({'x': [tab_bottom_left[0], tab_bottom_right[0], tab_top_right[0], tab_top_left[0], tab_bottom_left[0]],
                                 'y': [tab_bottom_left[1], tab_bottom_right[1], tab_top_right[1], tab_top_left[1], tab_bottom_left[1]]})
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=main_plot['x'], y=main_plot['y'], mode='lines', name='Main Body', line=dict(color='black'), fillcolor='black', fill='toself'))
        fig.add_trace(go.Scatter(x=tab_plot['x'], y=tab_plot['y'], mode='lines', name='Tab', line=dict(color='black')))
        fig.update_layout(title=f'{self._name} Current Collector',
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y"),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          paper_bgcolor='white',
                          plot_bgcolor='white',
                          showlegend=False)
        fig.show()

    @property
    def length(self) -> float:
        return round(self._length * M_TO_CM, 2)
    
    @property
    def width(self) -> float:
        return round(self._width * M_TO_CM, 2)
    
    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_CM**2, 2)

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        else:
            return "Current Collector"

    @property
    def formula(self) -> str:
        return self._formula

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def bare_area(self) -> float:
        return round(self._bare_area * M_TO_CM**2, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return self._cost
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()


class NotchedCurrentCollector(CurrentCollector):

    def __init__(self, 
                 formula: str, 
                 length: float,
                 width: float,
                 thickness: float,
                 tab_width: float,
                 tab_length: float,
                 tab_spacing: float,
                 bare_length: float,
                 specific_cost: float = None
                 ):
        """
        Initialize an object that represents a notched current collector.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg. By default it will pull this from the database
        :param length: float: length of the current collector in cm
        :param width: float: width of the current collector in cm
        :param bare_length: float: length of the current collector that is not coated with the electrode material in cm
        :param thickness: float: thickness of the current collector in um
        :param density: float: density of the material in g/cm^3
        :param tab_width: float: width of the notch in cm
        :param tab_length: float: length of the notch in cm
        :param tab_spacing: float: spacing between the notches in cm
        """
        self._check_tab_width(tab_width)
        self._check_tab_length(tab_length)
        self._check_tab_spacing(tab_spacing)
        self._check_bare_length(bare_length)
        self._check_length(length)
        self._check_width(width)

        bare_area = self._calculate_bare_tab_area(tab_width, tab_length, tab_spacing, length, bare_length, width)

        super().__init__(formula=formula,
                         length=length,
                         width=width,
                         bare_area=bare_area,
                         thickness=thickness,
                         specific_cost=specific_cost)

    def _check_tab_width(self, tab_width: float):

        if not isinstance(tab_width, (int, float)):
            raise TypeError("Tab width must be a number.")
        
        if tab_width < 0:
            raise ValueError("Tab width cannot be negative.")
        
        self._tab_width = float(tab_width) * CM_TO_M

    def _check_tab_length(self, tab_length: float):

        if not isinstance(tab_length, (int, float)):
            raise TypeError("Tab length must be a number.")
        
        if tab_length < 0:
            raise ValueError("Tab length cannot be negative.")
        
        self._tab_length = float(tab_length) * CM_TO_M

    def _check_tab_spacing(self, tab_spacing: float):

            if not isinstance(tab_spacing, (int, float)):
                raise TypeError("Tab spacing must be a number.")
            
            if tab_spacing < 0:
                raise ValueError("Tab spacing cannot be negative.")
            
            self._tab_spacing = float(tab_spacing) * CM_TO_M

    def _check_bare_length(self, bare_length: float):
        
        if not isinstance(bare_length, (int, float)):
            raise TypeError("Bare length must be a number.")
        
        if bare_length < 0:
            raise ValueError("Bare length cannot be negative.")
        
        self._bare_length = float(bare_length) * CM_TO_M

    def _calculate_bare_tab_area(self, tab_width: float, tab_length: float, tab_spacing: float, length: float, bare_length: float, width: float):
        """
        Function to calculate the area of the current collector that is not coated with the electrode material. All inputs are in cm.
        :param tab_width: float: width of the tabs in cm
        :param tab_length: float: length of the tabs in cm
        :param tab_spacing: float: spacing between the tabs in cm
        :param length: float: length of the current collector in cm
        :param bare_length: float: length of the current collector that is not coated with the electrode material in cm
        """
        if tab_spacing + tab_length > length:
            raise ValueError("The tab spacing and length cannot be greater than the length of the current collector.")
        
        tab_positions = [tab_spacing / 2 + tab_length / 2]
        tab_lengths = [tab_length]
        remaining_length = length - tab_length - tab_spacing

        while remaining_length > tab_length + tab_spacing:
            tab_positions.append(tab_positions[-1] + tab_spacing + tab_length)
            tab_lengths.append(tab_length)
            remaining_length -= tab_spacing + tab_length

        if remaining_length > tab_spacing/2 and remaining_length > tab_length + tab_spacing/2:
            tab_positions.append(tab_positions[-1] + tab_spacing + tab_length)
            tab_lengths.append(tab_length)

        if remaining_length > tab_spacing/2 and remaining_length < tab_length + tab_spacing/2:
            end_tab_length = remaining_length - tab_spacing/2
            tab_positions.append(tab_positions[-1] + tab_spacing + tab_length/2 + end_tab_length/2)
            tab_lengths.append(end_tab_length)

        tab_areas = [l * tab_width for l in tab_lengths]

        self._tab_positions = [t * CM_TO_M for t in tab_positions]
        self._tab_lengths = [l * CM_TO_M for l in tab_lengths]
        self._tab_areas = [a * CM_TO_M**2 for a in tab_areas]

        bare_area = sum(tab_areas) + (bare_length * width)

        return bare_area

    def _calculate_properties(self):

        self._coated_area = (self._length - self._bare_length) * self._width
        self._area = self._length * self._width + sum(self._tab_areas)
        self._volume = self._area * self._thickness
        self._mass = self._volume * self._density
        self._cost = self._mass * self._specific_cost

    def show(self):
        """
        Visualize the notched current collector.
        """
        fig = go.Figure()

        bottom_left = (0, 0)
        bottom_right = (self._length, 0)
        top_right = (self._length, self._width)
        top_left = (0, self._width)
        x = [bottom_left[0], bottom_right[0], top_right[0], top_left[0], bottom_left[0]]
        y = [bottom_left[1], bottom_right[1], top_right[1], top_left[1], bottom_left[1]]
        main_body = pd.DataFrame({'x': x, 'y': y})
        fig.add_trace(go.Scatter(x=main_body['x'], y=main_body['y'], mode='lines', name='Main Body', line=dict(width=0), fillcolor='grey', fill='toself'))

        covered_bottom_left = (0, 0)
        covered_bottom_right = (self._length - self._bare_length, 0)
        covered_top_right = (self._length - self._bare_length, self._width)
        covered_top_left = (0, self._width)
        x = [covered_bottom_left[0], covered_bottom_right[0], covered_top_right[0], covered_top_left[0], covered_bottom_left[0]]
        y = [covered_bottom_left[1], covered_bottom_right[1], covered_top_right[1], covered_top_left[1], covered_bottom_left[1]]
        covered_area = pd.DataFrame({'x': x, 'y': y})
        fig.add_trace(go.Scatter(x=covered_area['x'], y=covered_area['y'], mode='lines', name='Covered Area', line=dict(width=0), fillcolor='black', fill='toself'))

        for (pos, len) in zip(self._tab_positions, self._tab_lengths):
            tab_bottom_left = (pos-len/2, self._width)
            tab_bottom_right = (pos+len/2, self._width)
            tab_top_right = (pos+len/2, self._width + self._tab_width)
            tab_top_left = (pos-len/2, self._width + self._tab_width)
            x = [tab_bottom_left[0], tab_bottom_right[0], tab_top_right[0], tab_top_left[0], tab_bottom_left[0]]
            y = [tab_bottom_left[1], tab_bottom_right[1], tab_top_right[1], tab_top_left[1], tab_bottom_left[1]]
            tab = pd.DataFrame({'x': x, 'y': y})
            fig.add_trace(go.Scatter(x=tab['x'], y=tab['y'], mode='lines', name='Tab', line=dict(width=0), fillcolor='grey', fill='toself'))

        fig.update_layout(title=f'{self._name} Current Collector',
                          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y"),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          paper_bgcolor='white',
                          plot_bgcolor='white',
                          showlegend=False)
        fig.show()        

    @property
    def tab_width(self) -> float:
        return round(self._tab_width * M_TO_CM, 2)
    
    @property
    def tab_length(self) -> float:
        return round(self._tab_length * M_TO_CM, 2)
    
    @property
    def tab_spacing(self) -> float:
        return round(self._tab_spacing * M_TO_CM, 2)
    
    @property
    def bare_length(self) -> float:
        return round(self._bare_length * M_TO_CM, 2)
