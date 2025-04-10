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
                 width: float,
                 fold_length: float,
                 name: str = 'Separator'
                 ):
        """
        Initialize an object that represents a separator
        
        :param name: str: name of the material
        :param areal_cost: float: areal cost of the material per m^2
        :param thickness: float: thickness of the separator in um
        :param density: float: density of the material in g/cm^3
        :param porosity: float: porosity of the separator in %
        :param width: float: width of the separator in cm
        :param length: float: length of the separator in cm
        :param fold_length: float: length of the fold in the separator in cm
        """
        self._check_areal_cost(areal_cost)
        self._check_thickness(thickness)
        self._check_density(density)
        self._check_porosity(porosity)
        self._check_width(width)
        self._check_fold_length(fold_length)
        self._check_name(name)

    def _check_areal_cost(self, areal_cost: float):

        if not isinstance(areal_cost, (int, float)):
            raise TypeError("Areal cost must be a number.")
        
        if areal_cost < 0:
            raise ValueError("Areal cost cannot be negative.")
        
        if areal_cost > 10:
            raise ValueError("This areal cost is too high. Check the units, it should be in $/m^2.")
        
        self._areal_cost = float(areal_cost)

    def _check_thickness(self, thickness: float):

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")

        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        if thickness > 100:
            raise ValueError("This thickness is too high for a separator. Check the units, it should be in um.")
        
        self._thickness = float(thickness) * UM_TO_M

    def _check_density(self, density: float):

        if not isinstance(density, (int, float)):
            raise TypeError("Density must be a number.")

        if density < 0:
            raise ValueError("Density cannot be negative.")
        
        if density > 3:
            raise ValueError("This density is too high for a separator. Check the units, it should be in g/cm^3.")
        
        self._density = float(density) * (G_TO_KG / CM_TO_M**3)

    def _check_porosity(self, porosity: float):

        if not isinstance(porosity, (int, float)):
            raise TypeError("Porosity must be a number.")

        if porosity < 0:
            raise ValueError("Porosity cannot be negative.")
        
        if porosity > 100:
            raise ValueError("This porosity is too high. Check the units, it should be in %.")
        
        if porosity < 1:
            raise ValueError("This porosity is very low. Check the units, it should be in %.")
        
        self._porosity = float(porosity) / 100

    def _check_width(self, width: float):

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")

        if width < 0:
            raise ValueError("Width cannot be negative.")
        
        if width > 100:
            raise ValueError("This width is too high. Check the units, it should be in cm.")
        
        self._width = float(width) * CM_TO_M

    def _check_fold_length(self, fold_length: float):

        if not isinstance(fold_length, (int, float)):
            raise TypeError("Fold length must be a number.")

        if fold_length < 0:
            raise ValueError("Fold length cannot be negative.")
        
        if fold_length > 1000:
            raise ValueError("This fold length is too high. Check the units, it should be in cm.")
        
        self._fold_length = float(fold_length) * CM_TO_M

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        
        self._name = name

    def _calculate_area_properties(self):

        if not hasattr(self, '_length'):
            raise AttributeError("Length not calculated defined. Put in an electrochemical assembly to calculate it.")

        self._area = self._width * self._length
        self._mass = self._thickness * self._area * self._density
        self._cost = self._area * self._areal_cost
        self._pore_volume = self._thickness * self._area * self._porosity
        
    @property
    def length(self):
        if hasattr(self, '_length'):
            return round(self._length * M_TO_CM, 2)

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
    def width(self):
        if hasattr(self, '_width'):
            return round(self._width * M_TO_CM, 2)
    
    @property
    def fold_length(self):
        if hasattr(self, '_fold_length'):
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