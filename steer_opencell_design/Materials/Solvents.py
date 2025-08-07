
class Solvent:

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 specific_cost: float = None, 
                 density: float = None):
        """
        Initialize an object that represents a solvent
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3
        """
        self._name = name
        self._formula = formula
        self._specific_cost = specific_cost
        self._density = density

    @property
    def density(self):
        return self._density

    def __str__(self):
        return f"Solvent {self.name}"
    
    def __repr__(self):
        return f"Solvent {self.name}"
    