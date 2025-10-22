from steer_core.Constants.Units import *


class Laminate:

    def __init__(self, thickness: float = 113, areal_mass: float = 18, areal_cost: float = 4.64):
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


class Terminal:

    def __init__(
        self,
        mass: float,
        specific_cost: float,
        name: str = None,
        thickness: float = 0,
    ):
        """
        Terminal object for a cell

        :param mass: float: mass of the terminal in g
        :param specific_cost: float: specific cost of the terminal $/kg
        :param name: str: name of the terminal
        :param thickness: float: thickness of the terminal in mm
        """
        self._check_mass(mass)
        self._check_specific_cost(specific_cost)
        self._check_thickness(thickness)
        self._check_name(name)
        self._check_mass(mass)
        self._calculate_properties()

    def _check_mass(self, mass):
        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass <= 0:
            raise ValueError("Mass must be greater than 0")

        self._mass = mass * G_TO_KG

    def _check_specific_cost(self, specific_cost):
        if not isinstance(specific_cost, (int, float)):
            raise TypeError("Specific cost must be a number")

        if specific_cost <= 0:
            raise ValueError("Specific cost must be greater than 0")

        self._specific_cost = specific_cost

    def _check_thickness(self, thickness):
        if thickness is not None:
            if not isinstance(thickness, (int, float)):
                raise TypeError("Thickness must be a number")

            if thickness < 0:
                raise ValueError("Thickness must be greater than 0")

        self._thickness = thickness * MM_TO_M if thickness else None

    def _check_name(self, name):
        if name is not None:
            if not isinstance(name, str):
                raise TypeError("Name must be a string")

        self._name = name

    def _calculate_properties(self):
        if self._thickness is not None:
            self._volume = self._mass / self._thickness
            self._area = self._volume / self._thickness
        else:
            self._volume = None
            self._area = None

        self._cost = self._mass * self._specific_cost

    @property
    def thickness(self):
        return round(self._thickness * M_TO_MM, 2) if self._thickness else None

    @property
    def cost(self):
        return round(self._cost, 2)

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


class Tape:
    
    def __init__(self, mass: float, name: str = None):
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
