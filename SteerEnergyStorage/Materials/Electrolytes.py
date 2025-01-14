from SteerEnergyStorage.Materials.core import Material
from SteerEnergyStorage.Materials.Ions import Cation
from SteerEnergyStorage.Materials.Ions import Anion
from SteerEnergyStorage.Materials.Solvents import Solvent


class Electrolyte(Material):

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 specific_cost: float = 8.94, 
                 solvent: Solvent = None, 
                 cation: dict[Cation, float] = None,
                 anion: dict[Anion, float] = None,
                 density: float = 1.2):
        """
        Initialize an object that represents an electrolyte
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg
        :param solvent: Solvent: solvent used in the electrolyte
        :param cation: dict: cation used in the electrolyte and its concentration in mol/L
        :param anion: dict: anion used in the electrolyte and its concentration in mol/L
        :param density: float: density of the material in g/cm^3
        """
        super().__init__(name, formula, specific_cost)
        self._cation = cation
        self._anion = anion
        self._solvent = solvent
        self._density = density

    @property
    def solvent(self):
        return self._solvent
    
    @property
    def cation(self):
        return self._cation
    
    @property
    def anion(self):
        return self._anion
    
    @property
    def density(self):
        return self._density

    def __str__(self):
        return f"Electrolyte {self.name}"
    
    def __repr__(self):
        return f"Electrolyte {self.name}"