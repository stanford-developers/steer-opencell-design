import numpy as np


class Separator():
    
    def __init__(self, 
                 name: str, 
                 specific_cost: float, 
                 n_stacks: int,
                 thickness: float, 
                 density: float,
                 porosity: float,
                 slit_width: float,
                 fold_length: float
                 ):
        """
        Initialize an object that represents a separator
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per m^2
        :param n_stacks: int: number of stacks
        :param thickness: float: thickness of the separator in mm
        :param density: float: density of the material in g/cm^3
        :param porosity: float: porosity of the separator in %
        :param slit_width: float: width of the slit in the separator in mm,
        :param fold_length: float: length of the fold in the separator in mm
        """
        self._name = name
        self._specific_cost = specific_cost
        self._n_stacks = n_stacks
        self._thickness = thickness
        self._density = density
        self._porosity = porosity
        self._slit_width = slit_width
        self._fold_length = fold_length

        self._area = self._slit_width/10 * self._fold_length/10 * (self._n_stacks*2 + 3)
        self._mass = (self._thickness/10000) * self._area * self._density
        self._cost = (self._area/10000) * self._specific_cost

        self._pore_volume = self._area * self._thickness/10000 * self._porosity/100

    @property
    def pore_volume(self):
        return np.round(self._pore_volume, 2)

    @property
    def n_stacks(self):
        return self._n_stacks

    @property
    def cost(self):
        return np.round(self._cost, 2)

    @property
    def mass(self):
        return np.round(self._mass, 2)

    @property
    def area(self):
        return np.round(self._area, 2)

    @property
    def slit_width(self):
        return np.round(self._slit_width, 2)
    
    @property
    def fold_length(self):
        return np.round(self._fold_length, 2)

    @property
    def specific_cost(self):
        return np.round(self._specific_cost, 2)
    
    @property
    def name(self):
        return self._name

    @property
    def porosity(self):
        return self._porosity

    @property
    def density(self):
        return np.round(self._density, 2)

    @property
    def thickness(self):
        return np.round(self._thickness, 2)

    def __str__(self):
        return f"Separator {self.name}"
    
    def __repr__(self):
        return f"Separator {self.name}"