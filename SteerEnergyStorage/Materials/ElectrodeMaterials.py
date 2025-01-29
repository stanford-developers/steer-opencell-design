G_TO_KG = 1e-3
CM_TO_M = 1e-2
KG_TO_G = 1e3
M_TO_CM = 1e2

class ActiveMaterial:
    def __init__(self, 
                 formula: str, 
                 specific_cost: float, 
                 density: float,
                 irreversible_capacity_scaling: float = 1.0,
                 reversible_capacity_scaling: float = 1.0,
                 name: str = None):
        """
        Initialize an object that represents an active material.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.5)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        """
        self._formula = formula
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3
        self._irreversible_capacity_scaling = irreversible_capacity_scaling
        self._reversible_capacity_scaling = reversible_capacity_scaling

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

    def __str__(self) -> str:
        if self._name is not None:
            return self._name
        else:
            return "conductive additive"
        
    def __repr__(self) -> str:
        return self.__str__()

