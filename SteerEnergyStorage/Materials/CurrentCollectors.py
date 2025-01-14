from SteerEnergyStorage.Materials.core import Material


class CurrentCollector(Material):

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 specific_cost: float = 6.30,
                 thickness: float = 15,
                 density: float = 2.70
                 ):
        """
        Initialize an object that represents a current collector
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg
        :thickness: float: thickness of the current collector in um
        :density: float: density of the material in g/cm^3
        """
        super().__init__(name, formula, specific_cost)
        self._thickness = thickness
        self._density = density

    @property
    def thickness(self):
        return self._thickness
    
    @property
    def density(self):
        return self._density
    
    @property
    def mass(self):
        try:
            return self._mass
        except AttributeError:
            raise AttributeError("The mass of the current collector has not been calculated. You need to create a stack with an anode and Cathode to do so.")
    
    def __str__(self):
        return f"Current collector {self.name}"
    
    def __repr__(self):
        return f"Current collector {self.name}"

