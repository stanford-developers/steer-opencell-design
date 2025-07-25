from datetime import datetime as dt
from pickle import dumps, loads

from OpenCell.Constants import *
from OpenCell.DataManager import DataManager

from pathlib import Path
from copy import deepcopy
import numpy as np


class _RawMaterial:

    def __init__(
            self, 
            name: str,
            density: float, 
            specific_cost: float,
            color: str
        ):
        """
        Metal object for encapsulation of the cell
        
        Parameters
        ----------
        name : str
            Name of the material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        self._update_ranges = True

        self.density = density
        self.specific_cost = specific_cost
        self.name = name
        self.color = color

        self._update_ranges = False

        self._last_updated = dt.now()

    @property
    def density(self):
        return round(self._density * (KG_TO_G / M_TO_CM**3), 2)
    
    @density.setter
    def density(self, density: float) -> None:
        
        if not isinstance(density, (int, float)):
            raise TypeError("Density must be a number.")
        if density <= 0:
            raise ValueError("Density must be greater than zero.")
        if density > 10000:
            raise ValueError("Density must be less than or equal to 10,000 g/cm^3.")
        
        self._density = density * G_TO_KG / CM_TO_M**3

        if self._update_ranges:
            self._density_range = (self._density * 0.8, self._density * 1.2)
            min = np.ceil(self._density_range[0])
            max = np.floor(self._density_range[1])
            self._density_marks = {i: '' for i in range(int(min), int(max) + 1, 200)}

    @property
    def density_range(self):
        min = self._density_range[0]
        max = self._density_range[1]
        return (round(min * (KG_TO_G / M_TO_CM**3), 2), round(max * (KG_TO_G / M_TO_CM**3), 2))

    @property
    def density_marks(self):
        return {i * (KG_TO_G / M_TO_CM**3): '' for i in self._density_marks.keys()}

    @property
    def specific_cost(self):
        return self._specific_cost
    
    @specific_cost.setter
    def specific_cost(self, specific_cost: float) -> None:
        
        if not isinstance(specific_cost, (int, float)):
            raise TypeError("Specific cost must be a number.")
        if specific_cost <= 0:
            raise ValueError("Specific cost must be greater than zero.")
        
        self._specific_cost = specific_cost

        if self._update_ranges:
            self._specific_cost_range = (self._specific_cost * 0.5, self._specific_cost * 3)
            min = np.ceil(self._specific_cost_range[0])
            max = np.floor(self._specific_cost_range[1])
            self._specific_cost_marks = {i: '' for i in np.arange(min, max + 0.2, 0.2)}

    @property
    def specific_cost_range(self):
        min = self._specific_cost_range[0]
        max = self._specific_cost_range[1]
        return (round(min, 2), round(max, 2))

    @property
    def specific_cost_marks(self):
        min = np.ceil(self.specific_cost_range[0])
        max = np.floor(self.specific_cost_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 2)}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        
        if name is not None:
            if not isinstance(name, str):
                raise TypeError("Name must be a string.")
            if len(name) == 0:
                raise ValueError("Name cannot be an empty string.")
        
        self._name = name

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color: str) -> None:

        if not isinstance(color, str):
            raise TypeError("Color must be a string.")
        if len(color) == 0:
            raise ValueError("Color cannot be an empty string.")
        
        self._color = color if color else "Unknown"
    
    @property
    def last_updated(self):
        return self._last_updated.strftime("%Y-%m-%d %H:%M:%S")

    def pickle(self):
        """
        Serializes the object to a byte stream.
        
        :return: bytes: Serialized byte stream of the object.
        """
        return dumps(self)

    def __str__(self):
        return f"{self.name}, {self.__class__.__name__}, {self.last_updated}"
    
    def __repr__(self):
        return self.__str__()
    

class CurrentCollectorMaterial(_RawMaterial):
    """
    Materials from which current collectors are made.
    """
    def __init__(
            self,
            name: str,
            density: float,
            specific_cost: float,
            color: str
        ):
        """
        Current collector material for encapsulation of the cell
        
        Parameters
        ----------
        name : str
            Name of the current collector material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

    @staticmethod
    def from_database(name) -> 'CurrentCollectorMaterial':
        """
        Pull object from the database.
        
        Parameters
        ----------
        name : str
            Name of the current collector material.

        Returns
        -------
        CurrentCollectorMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('current_collector_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = (
            database
            .get_current_collector_materials(most_recent=True)
            .query(f"name == '{name}'")
        )
        
        material = deepcopy(loads(data['object'].iloc[0]))

        return material


class InsulationMaterial(_RawMaterial):
    """
    Materials from which insulation is made.
    """
    def __init__(
            self,
            name: str,
            density: float,
            specific_cost: float,
            color: str
        ):
        """
        Insulation material for encapsulation of the cell
        
        Parameters
        ----------
        name : str
            Name of the insulation material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

    @staticmethod
    def from_database(name) -> 'InsulationMaterial':
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the insulation material.

        Returns
        -------
        InsulationMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('insulation_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = (
            database
            .get_data(table_name='insulation_materials')
            .query(f"name == '{name}'")
        )
        
        material = deepcopy(loads(data['object'].iloc[0]))

        return material

    
class SeparatorMaterial(_RawMaterial):
    """
    Materials from which separators are made.
    """
    def __init__(
            self,
            name: str,
            density: float,
            specific_cost: float,
            porosity: float,
            color: str
        ):
        """
        Separator material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the separator material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        porosity : float
            Porosity of the separator material in %.
        color : str
            Color of the material.
        """
        super().__init__(
            name,
            density,
            specific_cost,
            color
        )

        self.porosity = porosity

    @property
    def porosity(self):
        return round(self._porosity * 100, 2)
    
    @porosity.setter
    def porosity(self, porosity: float) -> None:

        if not isinstance(porosity, (int, float)):
            raise TypeError("Porosity must be a number.")
        if porosity < 0 or porosity > 100:
            raise ValueError("Porosity must be between 0 and 100%.")
        
        self._porosity = porosity / 100.0

    @staticmethod
    def from_database(name) -> 'SeparatorMaterial':
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the separator material.

        Returns
        -------
        SeparatorMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('separator_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")

        data = (
            database
            .get_data(table_name='separator_materials')
            .query(f"name == '{name}'")
        )

        material = deepcopy(loads(data['object'].iloc[0]))

        return material


