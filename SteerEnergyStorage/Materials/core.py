

class Material():

    def __init__(self, name: str, formula: str, cost: float = None):
        """
        Initialize an object that represents a general material
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param cost: float: cost of the material per kg
        """
        self._name = name
        self._formula = formula.lower()
        self._cost = cost

    @property
    def cost(self):
        return self._cost

    @property
    def name(self):
        return self._name
    
    @property
    def formula(self):
        return self._formula

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name