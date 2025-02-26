from SteerEnergyStorage.DataManager import DataManager
import os

CM_TO_M = 1e-2
M_TO_CM = 1e2
UM_TO_M = 1e-6
M_TO_UM = 1e6
G_TO_KG = 1e-3
KG_TO_G = 1e3

class CurrentCollector:

    def __init__(self, 
                 formula: str, 
                 length: float,
                 width: float,
                 bare_tab_area: float,
                 thickness: float,
                 specific_cost: float = None):
        """
        Initialize an object that represents a current collector.
        
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material $/kg. By default it will pull this from the database
        :param length: float: length of the current collector in cm
        :param width: float: width of the current collector in cm
        :param bare_tab_area: float: area of the current collector that is not coated with the electrode material in cm^2
        :param thickness: float: thickness of the current collector in um
        :param density: float: density of the material in g/cm^3
        """
        # Database values
        self._formula = formula.capitalize()
        self.set_properties_from_database()

        # update the cost if a specific cost is provided
        self._specific_cost = specific_cost if specific_cost is not None else self._specific_cost

        # User values
        self._length = length * CM_TO_M
        self._width = width * CM_TO_M
        self._bare_tab_area = bare_tab_area * CM_TO_M**2
        self._thickness = thickness * UM_TO_M

        # Calculated values
        self._coated_area = self._length * self._width
        self._mass = (self._coated_area + self._bare_tab_area) * self._thickness * self._density
        self._cost = self._mass * self._specific_cost

    def set_properties_from_database(self):
        """
        Retrieve the properties of the current collector from the database.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material $/kg
        :param density: float: density of the material in g/cm^3
        """
        data_path = os.path.join(os.path.dirname(__file__), '../../Data/materials_properties.db')
        materials_database = DataManager(data_path)
        available_materials = materials_database.get_unique_values('current_collectors', 'formula')

        if self._formula not in available_materials:
            raise ValueError(f'{self._formula} is not available in the materials database. Allowed values are: {available_materials}')
        
        data = materials_database.get_data('current_collectors', condition=f"formula='{self._formula}'", latest_column='date')
        
        self._name = data['name'].values[0]
        self._specific_cost = data['specific_cost'].values[0]
        self._density = data['density'].values[0]
        
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
        if self._name is not None:
            return self._name
        else:
            return "Current Collector"

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
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()
