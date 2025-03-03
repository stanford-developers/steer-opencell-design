from SteerEnergyStorage.Materials.Salts import Salt
from SteerEnergyStorage.Materials.Solvents import Solvent

G_TO_KG = 0.001
CM_TO_M = 0.01
KG_TO_G = 1000
M_TO_CM = 100

class Electrolyte:

    def __init__(self, 
                 specific_cost: float, 
                 density: float,
                 name: str = 'Electrolyte'):   
        """
        Initialize an object that represents an electrolyte
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material $/kg
        :param density: float: density of the material in g/cm^3
        """
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * (G_TO_KG / CM_TO_M**3)

    @property
    def name(self):
        return self._name
    
    @property
    def formula(self):
        return self._formula
    
    @property
    def specific_cost(self):
        return self._specific_cost

    @property
    def mass(self):
        try:
            return round(self._mass, 2)
        except AttributeError:
            return AttributeError("Mass not calculated yet")

    @property
    def volume(self):
        try:
            return round(self._volume, 2)
        except AttributeError:
            return AttributeError("Volume not calculated yet")
        
    @property
    def cost(self):
        try:
            return self._cost
        except AttributeError:
            return AttributeError("Cost not calculated yet")
    
    @property
    def density(self):
        return round(self._density * (KG_TO_G/M_TO_CM**3), 2)

    def __str__(self):
        return f"{self.name}"
    
    def __repr__(self):
        return self.__str__()
    
