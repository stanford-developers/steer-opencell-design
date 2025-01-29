CM_TO_M = 1e-2
M_TO_CM = 1e2
UM_TO_M = 1e-6
M_TO_UM = 1e6
G_TO_KG = 1e-3
KG_TO_G = 1e3

class CurrentCollector:

    def __init__(self, 
                 name: str, 
                 formula: str, 
                 specific_cost: float,
                 length: float,
                 width: float,
                 bare_tab_area: float,
                 thickness: float,
                 density: float):
        """
        Initialize an object that represents a current collector.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg
        :param length: float: length of the current collector in cm
        :param width: float: width of the current collector in cm
        :param coated_area: float: area of the current collector that is coated with the electrode material in cm^2
        :param bare_tab_area: float: area of the current collector that is not coated with the electrode material in cm^2
        :param thickness: float: thickness of the current collector in um
        :param density: float: density of the material in g/cm^3
        """
        self._name = name
        self._formula = formula
        self._specific_cost = specific_cost
        self._length = length * CM_TO_M
        self._width = width * CM_TO_M
        self._coated_area = self._length * self._width
        self._bare_tab_area = bare_tab_area * CM_TO_M**2
        self._thickness = thickness * UM_TO_M
        self._density = density * G_TO_KG / CM_TO_M**3
        self._mass = (self._coated_area + self._bare_tab_area) * self._thickness * self._density
        self._cost = self._mass * self._specific_cost

    @property
    def length(self) -> float:
        return round(self._length * M_TO_CM, 2)
    
    @property
    def width(self) -> float:
        return round(self._width * M_TO_CM, 2)
    
    @property
    def coated_area(self) -> float:
        return round(self._coated_area * M_TO_CM**2, 2)

    @property
    def name(self) -> str:
        return self._name

    @property
    def formula(self) -> str:
        return self._formula

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def bare_tab_area(self) -> float:
        return round(self._bare_tab_area * M_TO_CM**2, 2)

    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_UM, 2)

    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return self._cost

