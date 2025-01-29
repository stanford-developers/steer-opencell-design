UM_TO_M = 1e-6
M_TO_UM = 1e6
MG_TO_KG = 1e-6
KG_TO_MG = 1e6
CM_TO_M = 1e-2
M_TO_CM = 1e2
G_TO_KG = 1e-3
KG_TO_G = 1e3

class Laminate():

    def __init__(self, 
                 thickness: float = 113, 
                 areal_mass: float = 18,
                 areal_cost: float = 4.64
                 ):
        """
        Laminate object for encapsulation of the cell
        :param thickness: float: thickness of the laminate in um
        :param areal_mass: float: the areal mass of the laminate in mg/cm^2
        :param specific_cost: float: specific cost of the laminate $/m^2
        """
        self._thickness = thickness * UM_TO_M
        self._areal_mass = areal_mass * (MG_TO_KG / CM_TO_M**2)
        self._areal_cost = areal_cost

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)
    
    @property
    def areal_mass(self):
        return round(self._areal_mass * (KG_TO_MG / M_TO_CM**2), 2)
    
    @property
    def areal_cost(self):
        return self._areal_cost
    
    def __str__(self):
        return f"Laminate with a thickness of {self.thickness} um and an areal mass of {self.areal_mass} mg/cm^2"
    
    def __repr__(self):
        return f"Laminate with a thickness of {self.thickness} um and an areal mass of {self.areal_mass} mg/cm^2"
    

class Terminal():

    def __init__(self, 
                 mass: float,
                 specific_cost: float,
                 name: str = None
                 ):
        """
        Terminal object for a cell
        :param mass: float: mass of the terminal in g
        :param specific_cost: float: specific cost of the terminal $/kg
        :param name: str: name of the terminal
        """
        self._mass = mass * G_TO_KG
        self._specific_cost = specific_cost
        self._name = name
        self._cost = self._mass * self._specific_cost

    @property
    def cost(self):
        return self._cost
    
    @property
    def name(self):
        return self._name

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def specific_cost(self):
        return self._specific_cost
    
    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"Cell terminal"
    
    def __repr__(self):
        return self.__str__()
    

class Tape():

    def __init__(self, 
                 mass: float,
                 name: str = None
                 ):
        """
        Tape object for a cell
        :param mass: float: mass of the tape in g
        :param name: str: name of the tape
        """
        self._mass = mass * G_TO_KG
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)
    
    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"Tape with a mass of {self.mass} g"
        
    def __repr__(self):
        return self.__str__()
    
