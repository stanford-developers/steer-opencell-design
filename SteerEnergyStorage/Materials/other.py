


class Laminate():

    def __init__(self, 
                 thickness: float = 113, 
                 areal_mass: float = 18,
                 specific_cost: float = 4.64
                 ):
        """
        Laminate object for encapsulation of the cell
        :param thickness: float: thickness of the laminate in um
        :param areal_mass: float: the areal mass of the laminate in mg/cm^2
        :param specific_cost: float: specific cost of the laminate $/kg
        """
        self._thickness = thickness
        self._areal_mass = areal_mass
        self._specific_cost = specific_cost

    @property
    def thickness(self):
        return self._thickness
    
    @property
    def areal_mass(self):
        return self._areal_mass
    
    @property
    def specific_cost(self):
        return self._specific_cost
    
    def __str__(self):
        return f"Laminate with a thickness of {self.thickness} um and an areal mass of {self.areal_mass} mg/cm^2"
    
    def __repr__(self):
        return f"Laminate with a thickness of {self.thickness} um and an areal mass of {self.areal_mass} mg/cm^2"
    

class Terminal():

    def __init__(self, 
                 mass: float = 1,
                 specific_cost: float = 16
                 ):
        """
        Terminal object for a cell
        :param mass: float: mass of the terminal in g
        :param cost: float: cost of the terminal $/kg
        """
        self._mass = mass
        self._specific_cost = specific_cost

    @property
    def mass(self):
        return self._mass
    
    @property
    def specific_cost(self):
        return self._specific_cost
    
    def __str__(self):
        return f"Terminal with a mass of {self.mass} g"
    
    def __repr__(self):
        return f"Terminal with a mass of {self.mass} g"
    

class Seal():

    def __init__(self,
                 length: float = 22
                 ):
        """
        Seal object for a cell
        :param length: float: length of the seal in mm
        """
        self._length = length

    @property
    def length(self):
        return self._length
    
    def __str__(self):
        return f"Seal with a length of {self.length} mm"
    
    def __repr__(self):
        return f"Seal with a length of {self.length} mm"
    
