UM_TO_M = 1e-6
M_TO_UM = 1e6
G_TO_KG = 1e-3
CM_TO_M = 1e-2
KG_TO_G = 1e3
M_TO_CM = 1e2
MM_TO_M = 1e-3
M_TO_MM = 1e3

class Separator:

    def __init__(self,  
                 areal_cost: float, 
                 thickness: float, 
                 density: float,
                 porosity: float,
                 slit_width: float,
                 fold_length: float,
                 name: str = 'Seperator'
                 ):
        """
        Initialize an object that represents a separator
        :param name: str: name of the material
        :param areal_cost: float: areal cost of the material per m^2
        :param thickness: float: thickness of the separator in um
        :param density: float: density of the material in g/cm^3
        :param porosity: float: porosity of the separator in %
        :param slit_width: float: width of the slit in the separator in cm,
        :param fold_length: float: length of the fold in the separator in cm
        """
        self._name = name
        self._areal_cost = areal_cost
        self._thickness = thickness * UM_TO_M
        self._density = density * (G_TO_KG / CM_TO_M**3)
        self._porosity = porosity / 100
        self._slit_width = slit_width * CM_TO_M
        self._fold_length = fold_length * CM_TO_M
        self._used = False

    @property
    def pore_volume(self):
        if hasattr(self, '_pore_volume'):
            return round(self._pore_volume * M_TO_CM**3, 2)
        else:
            return AttributeError("Pore volume not calculated yet. Put in a stack to calculate.")

    @property
    def cost(self):
        if hasattr(self, '_cost'):
            return round(self._cost, 2)
        else:
            return AttributeError("Cost not calculated yet. Put in a stack to calculate.")

    @property
    def mass(self):
        if hasattr(self, '_mass'):
            return round(self._mass * KG_TO_G, 2)
        else:
            return AttributeError("Mass not calculated yet. Put in a stack to calculate.")

    @property
    def area(self):
        if hasattr(self, '_area'):
            return round(self._area * M_TO_CM**2, 2)
        else:
            return AttributeError("Area not calculated yet. Put in a stack to calculate.")

    @property
    def slit_width(self):
        return round(self._slit_width * M_TO_CM, 2)
    
    @property
    def fold_length(self):
        return round(self._fold_length * M_TO_CM, 2)

    @property
    def areal_cost(self):
        return round(self._areal_cost, 2)
    
    @property
    def name(self):
        return self._name

    @property
    def porosity(self):
        return self._porosity * 100

    @property
    def density(self):
        return round(self._density * (KG_TO_G/M_TO_CM**3), 2)

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)

    def __str__(self):
        if self._name is not None:
            return f"{self._name} Separator"
        else:
            return f"Separator"
    
    def __repr__(self):
        return self.__str__()