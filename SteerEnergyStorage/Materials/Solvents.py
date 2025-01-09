from SteerEnergyStorage.Materials.core import Material


class Solvent(Material):

    def __init__(self, name: str, formula: str, cost: float = None):
        """
        Initialize an object that represents a solvent
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param cost: float: cost of the material per kg
        """
        super().__init__(name, formula, cost)

    def __str__(self):
        return f"Solvent {self.name}"
    
    def __repr__(self):
        return f"Solvent {self.name}"