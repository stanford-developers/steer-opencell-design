import pandas as pd
import datetime as dt
import numpy as np

G_TO_KG = 1e-3
CM_TO_M = 1e-2
KG_TO_G = 1e3
M_TO_CM = 1e2
mA_TO_A = 1e-3
A_TO_mA = 1e3
H_TO_S = 3600
S_TO_H = 1/3600

class ActiveMaterial:
    def __init__(self, 
                 formula: str, 
                 specific_cost: float, 
                 density: float,
                 name: str,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 half_cell_path: str = None
                 ):
        """
        Initialize an object that represents an active material.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.5)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        self._formula = formula
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3
        self._irreversible_capacity_scaling = irreversible_capacity_scaling
        self._reversible_capacity_scaling = reversible_capacity_scaling
        self._half_cell_path = half_cell_path
        self._half_cell_curve = self._read_half_cell_curve()
        self._time_stamp = dt.datetime.now()

    def _read_half_cell_curve(self) -> pd.DataFrame:
        """
        Function to read in a half cell curve for this active material
        """
        try:
            data = pd.read_csv(self._half_cell_path)
        except:
            raise FileNotFoundError(f"Could not find the file at {self._half_cell_path}")
        
        if 'Specific Capacity (mAh/g)' not in data.columns:
            raise ValueError("The file must have a column named 'Specific Capacity (mAh/g)'")
        
        if 'Voltage (V)' not in data.columns:
            raise ValueError("The file must have a column named 'Voltage (V)'")
        
        if 'Step_ID' not in data.columns:
            raise ValueError("The file must have a column named 'Step_ID'")
        
        data = (data
                .rename(columns={'Specific Capacity (mAh/g)': 'specific_capacity', 'Voltage (V)': 'voltage', 'Step_ID': 'step_id'})
                .assign(specific_capacity=lambda x: x['specific_capacity'] * (H_TO_S * mA_TO_A / G_TO_KG))
                .filter(['specific_capacity', 'voltage', 'step_id'])
                .groupby(['specific_capacity', 'step_id'], group_keys=False)['voltage'].max()
                .reset_index()
                .sort_values(['step_id', 'specific_capacity'])
                )

        return data
    
    def _determine_half_cell_direction(self, electrode: 'str') -> pd.DataFrame:
        """
        Function to determine whether the curve is a discharge or charge curve
        """
        if electrode == 'cathode':
            """Determine the direction if its a cathode material"""
            half_cell_curve = (self
                               ._half_cell_curve
                               .copy()
                               .groupby(['step_id'], group_keys=False)
                               .apply(lambda df: (df
                                                  .assign(dv = lambda x: x['voltage'].diff().mean())
                                                  .assign(direction = lambda x: x['dv'].apply(lambda x: 'discharge' if x < 0 else 'charge'))
                                                  ))
                               .filter(['specific_capacity', 'voltage', 'direction'])
                               )
            
        elif electrode == 'anode':
            """Determine the direction if its an anode material"""
            half_cell_curve = (self
                               ._half_cell_curve
                               .copy()
                               .groupby(['step_id'], group_keys=False)
                               .apply(lambda df: (df
                                                  .assign(dv = lambda x: x['voltage'].diff().mean())
                                                  .assign(direction = lambda x: x['dv'].apply(lambda x: 'charge' if x < 0 else 'discharge'))
                                                  ))
                               .filter(['specific_capacity', 'voltage', 'direction'])
                               )
        
        return half_cell_curve

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        data = (self
                ._half_cell_curve
                .assign(specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G))
                .rename(columns={'specific_capacity': 'Specific Capacity (mAh/g)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction',
                                 'step_id': 'Step ID'})
                )
        
        return data
    
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
    def formula(self) -> str:
        return self._formula
    
    @property
    def name(self) -> str:
        return self._name
    
    def __lt__(self, other):

        if not isinstance(other, ActiveMaterial):
            raise ValueError("Can only compare ActiveMaterial objects together")
        
        if self._name is not None and other._name is not None:
            if self._name < other._name:
                return True
            elif self._name > other._name:
                return False
            
        return self._time_stamp < other._time_stamp
    
    def __gt__(self, other):

        if not isinstance(other, ActiveMaterial):
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
    

class Binder:
    def __init__(self, 
                 specific_cost: float, 
                 density: float,
                 name: str = None):
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
                 name: str = None):
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

