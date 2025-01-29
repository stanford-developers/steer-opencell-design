
class Salt:

    def __init__(self, name: str, formula: str, specific_cost: float = None, stoichiometry: dict = None):
        """
        Initialize an object that represents an ion
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :stoichiometry: dict: stoichiometry of the ion
        """
        self._name = name
        self._formula = formula
        self._specific_cost = specific_cost
        self._stoichiometry = stoichiometry
    
    @property
    def stoichiometry(self):
        return self._stoichiometry

    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"Salt"
        
    def __repr__(self):
        return self.__str__()
            
    