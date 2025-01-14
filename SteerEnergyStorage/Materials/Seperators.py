

class Separator():
    
    def __init__(self, 
                 name: str, 
                 specific_cost: float = 0.2, 
                 thickness: float = 16, 
                 density: float = 0.4,
                 porosity: float = 47,
                 slit_width: float = 100,
                 fold_length: float = 186
                 ):
        """
        Initialize an object that represents a separator
        :param name: str: name of the material
        :param formula: str: chemical formula of the material
        :param specific_cost: float: specific cost of the material per kg
        :param thickness: float: thickness of the separator in mm
        :param density: float: density of the material in g/cm^3
        :param porosity: float: porosity of the separator in %
        :param slit_width: float: width of the slit in the separator in mm,
        :param fold_length: float: length of the fold in the separator in mm
        """
        self._name = name
        self._specific_cost = specific_cost
        self._thickness = thickness
        self._density = density
        self._porosity = porosity
        self._slit_width = slit_width
        self._fold_length = fold_length

    @property
    def slit_width(self):
        return self._slit_width
    
    @property
    def fold_length(self):
        return self._fold_length

    @property
    def specific_cost(self):
        return self._specific_cost
    
    @property
    def name(self):
        return self._name

    @property
    def porosity(self):
        return self._porosity

    @property
    def density(self):
        return self._density

    @property
    def thickness(self):
        return self._thickness

    def __str__(self):
        return f"Separator {self.name}"
    
    def __repr__(self):
        return f"Separator {self.name}"