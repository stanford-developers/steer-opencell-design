from SteerEnergyStorage.Materials.core import Material


class ActiveMaterial(Material):

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 cost: float = None, 
                 density: float = 1.5,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 ):
        """
        Initialize an object that represents an active material
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param cost: float: cost of the material per kg
        :param capacity: float: capacity of the material in Ah/kg
        :param density: float: density of the material in g/cm^3
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity
        """
        super().__init__(name, formula, cost)
        self._density = density
        self._irreversible_capacity_scaling = irreversible_capacity_scaling
        self._reversible_capacity_scaling = reversible_capacity_scaling

    @property
    def irreversible_capacity_scaling(self):
        return self._irreversible_capacity_scaling
    
    @property
    def reversible_capacity_scaling(self):
        return self._reversible_capacity_scaling

    @property
    def density(self):
        return self._density

    def __str__(self):
        return f"Active material {self.name}"
    
    def __repr__(self):
        return f"Active material {self.name}"
    

class Binder(Material):

    def __init__(self, name: str, cost: float = None, density: float = 1.7):
        """
        Initialize an object that represents a binder
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param cost: float: cost of the material per kg
        :param density: float: density of the material in g/cm^3
        """
        super().__init__(name, formula=None, cost=cost)
        self._density = density

    @property
    def density(self):
        return self._density

    def __str__(self):
        return f"Binder {self.name}"
    
    def __repr__(self):
        return f"Binder {self.name}"
    
    
class ConductiveAdditive(Material):

    def __init__(self, name: str, cost: float = None, density: float = 2.0):
        """
        Initialize an object that represents a conductive additive
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param cost: float: cost of the material per kg
        """
        super().__init__(name, formula=None, cost=cost)
        self._density = density

    @property
    def density(self):
        return self._density

    def __str__(self):
        return f"Conductive additive {self.name}"
    
    def __repr__(self):
        return f"Conductive additive {self.name}"
    
