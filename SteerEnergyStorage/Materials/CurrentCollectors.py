import numpy as np
from SteerEnergyStorage.Materials.core import Material


class CurrentCollector(Material):

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 specific_cost: float,
                 coated_area: float,
                 bare_tab_area: float,
                 thickness: float,
                 density: float
                 ):
        """
        Initialize an object that represents a current collector
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg
        :param coated_area: float: area of the current collector that is coated with the electrode material in cm^2
        :param bare_tab_area: float: area of the current collector that is not coated with the electrode material in cm^2
        :thickness: float: thickness of the current collector in um
        :density: float: density of the material in g/cm^3
        """
        super().__init__(name, formula, specific_cost)
        self._coated_area = coated_area
        self._bare_tab_area = bare_tab_area
        self._thickness = thickness
        self._density = density
        self._mass = (self._coated_area + self._bare_tab_area) * self._thickness/10000 * self._density
        self._cost = self._mass/1000 * self._specific_cost

    @property
    def cost(self):
        return np.round(self._cost, 2)

    @property
    def thickness(self):
        return np.round(self._thickness, 2)
    
    @property
    def density(self):
        return np.round(self._density, 2)
    
    @property
    def coated_area(self):
        return np.round(self._coated_area, 2)
    
    @property
    def bare_tab_area(self):
        return np.round(self._bare_tab_area, 2)
    
    @property
    def mass(self):
        return np.round(self._mass, 2)
    
    def __str__(self):
        return f"Current collector {self.name}"
    
    def __repr__(self):
        return f"Current collector {self.name}"

