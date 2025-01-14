from SteerEnergyStorage.Materials.core import Material


class Ion(Material):

    def __init__(self, name: str, formula: str, specific_cost: float = None, charge: int = None):
        """
        Initialize an object that represents an ion
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :charge: int: charge of the ion
        """
        super().__init__(name, formula, specific_cost)
        self._charge = charge
    
    @property
    def charge(self):
        return self._charge

    def __str__(self):
        return f"Ion {self.name}"
    
    def __repr__(self):
        return f"Ion {self.name}"
    

class Cation(Ion):

    def __init__(self, name: str, formula: str, specific_cost: float = None, charge: int = None):
        """
        Initialize an object that represents a cation
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        """
        super().__init__(name, formula, specific_cost)

    def __str__(self):
        return f"Cation {self.name}"
    
    def __repr__(self):
        return f"Cation {self.name}"
    

class Anion(Ion):

    def __init__(self, name: str, formula: str, specific_cost: float = None):
        """
        Initialize an object that represents an anion
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        """
        super().__init__(name, formula, specific_cost)

    def __str__(self):
        return f"Anion {self.name}"
    
    def __repr__(self):
        return f"Anion {self.name}"
    