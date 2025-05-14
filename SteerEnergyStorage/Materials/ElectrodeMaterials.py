from SteerEnergyStorage.DataManager import DataManager

import pandas as pd
import datetime as dt
import os

G_TO_KG = 1e-3
CM_TO_M = 1e-2
KG_TO_G = 1e3
M_TO_CM = 1e2
mA_TO_A = 1e-3
A_TO_mA = 1e3
H_TO_S = 3600
S_TO_H = 1/3600


class _ActiveMaterial:

    def __init__(self, 
                 name: str,
                 specific_cost: float, 
                 density: float,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 half_cell_path: str = None
                 ):
        """
        Initialize an object that represents an active material.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.5)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        self._name = name.lower()
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3
        self._irreversible_capacity_scaling = irreversible_capacity_scaling
        self._reversible_capacity_scaling = reversible_capacity_scaling

        self._half_cell_path = half_cell_path
        self._time_stamp = dt.datetime.now()

    @property
    def half_cell_curve(self) -> pd.DataFrame:
        if hasattr(self, '_half_cell_curve'):
            data = (self
                    ._half_cell_curve
                    .assign(specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G))
                    .rename(columns={'specific_capacity': 'Specific Capacity (mAh/g)', 
                                     'voltage': 'Voltage (V)', 
                                     'direction': 'Direction',
                                     'step_id': 'Step ID'})
                    )
            return data
        else:
            raise ValueError("No half cell curve has been loaded for this material")
    
    @property
    def time_stamp(self) -> str:
        return self._time_stamp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def half_cell_path(self) -> str:
        return self._half_cell_path

    @property
    def irreversible_capacity_scaling(self) -> float:
        return self._irreversible_capacity_scaling
    
    @property
    def reversible_capacity_scaling(self) -> float:
        return self._reversible_capacity_scaling

    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def specific_cost(self) -> float:
        return self._specific_cost
    
    @property
    def name(self) -> str:
        return self._name
    
    def __lt__(self, other):

        if not isinstance(other, _ActiveMaterial):
            raise ValueError("Can only compare ActiveMaterial objects together")
        
        if self._name is not None and other._name is not None:
            if self._name < other._name:
                return True
            elif self._name > other._name:
                return False
            
        return self._time_stamp < other._time_stamp
    
    def __gt__(self, other):

        if not isinstance(other, _ActiveMaterial):
            raise ValueError("Can only compare ActiveMaterial objects together")
        
        if self._name is not None and other._name is not None:
            if self._name > other._name:
                return True
            elif self._name < other._name:
                return False
            
        return self._time_stamp > other._time_stamp
    
    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        else:
            return "active material"
        
    def __repr__(self) -> str:
        return self.__str__()
    

class CathodeMaterial(_ActiveMaterial):

    def __init__(self, 
                 name: str,
                 specific_cost: float, 
                 density: float,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 half_cell_path: str = None
                 ):
        """
        Initialize an object that represents a cathode material.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 4.0)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        super().__init__(name=name,
                         specific_cost=specific_cost, 
                         density=density,
                         irreversible_capacity_scaling=irreversible_capacity_scaling,
                         reversible_capacity_scaling=reversible_capacity_scaling,
                         half_cell_path=half_cell_path)
        
        self._half_cell_curve = self._get_half_cell_curve()

    @staticmethod
    def get_available_materials() -> list:
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('cathode_half_cell_curves', 'name')
        return available_materials
        
    def _get_half_cell_curve(self) -> pd.DataFrame:
        """
        Function to determine whether the curve is a discharge or charge curve
        """
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('cathode_half_cell_curves', 'name')

        if self._name not in available_materials:
            raise ValueError(f"Could not find the half cell curve for {self._name}. Available materials are: {available_materials}")
        
        data = materials_database.get_data(table_name='cathode_half_cell_curves', condition=f"name='{self._name}'")

        half_cell_curve = (data
                           .groupby(['step_id'], group_keys=False)
                           .apply(lambda df: (df
                                              .assign(dv = lambda x: x['voltage'].diff().mean())
                                              .assign(direction = lambda x: x['dv'].apply(lambda x: 'discharge' if x < 0 else 'charge'))
                                              ))
                            .filter(['specific_capacity', 'voltage', 'direction'])
                            )
        
        return half_cell_curve

    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        else:
            return "cathode material"
        
    def __repr__(self) -> str:
        return self.__str__()
    

class AnodeMaterial(_ActiveMaterial):

    def __init__(self, 
                 name: str,
                 specific_cost: float, 
                 density: float,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 half_cell_path: str = None
                 ):
        """
        Initialize an object that represents an anode material.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.5)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        super().__init__(name=name,
                         specific_cost=specific_cost, 
                         density=density,
                         irreversible_capacity_scaling=irreversible_capacity_scaling,
                         reversible_capacity_scaling=reversible_capacity_scaling,
                         half_cell_path=half_cell_path)
        
        self._half_cell_curve = self._get_half_cell_curve()

    @staticmethod
    def get_available_materials() -> list:
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('anode_half_cell_curves', 'name')
        return available_materials

    def _get_half_cell_curve(self) -> pd.DataFrame:
        """
        Function to determine whether the curve is a discharge or charge curve
        """
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('anode_half_cell_curves', 'name')

        if self._name not in available_materials:
            raise ValueError(f"Could not find the half cell curve for {self._name}. Available materials are: {available_materials}")
        
        data = materials_database.get_data(table_name='anode_half_cell_curves', condition=f"name='{self._name}'")

        half_cell_curve = (data
                           .groupby(['step_id'], group_keys=False)
                           .apply(lambda df: (df
                                                .assign(dv = lambda x: x['voltage'].diff().mean())
                                                .assign(direction = lambda x: x['dv'].apply(lambda x: 'charge' if x < 0 else 'discharge'))
                                                ))
                            .filter(['specific_capacity', 'voltage', 'direction'])
                            )
        
        return half_cell_curve

    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        else:
            return "anode material"
        
    def __repr__(self) -> str:
        return self.__str__()
    

class Binder:
    def __init__(self, 
                 specific_cost: float, 
                 density: float,
                 name: str = 'Binder'):
        """
        Initialize an object that represents a binder.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.7)
        """
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3

    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def specific_cost(self) -> float:
        return self._specific_cost
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        else:
            return "binder"
        
    def __repr__(self) -> str:
        return self.__str__()
    
    
class ConductiveAdditive:
    def __init__(self, 
                 specific_cost: float, 
                 density: float,
                 name: str = 'Conductive Additive'):
        """
        Initialize an object that represents a conductive additive.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3
        """
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        if self._name is not None:
            return self.name
        else:
            return "conductive additive"
        
    def __repr__(self) -> str:
        return self.__str__()

