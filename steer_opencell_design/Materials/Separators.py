from steer_opencell_design.Materials.RawMaterials import SeparatorMaterial

from plotly import graph_objects as go
from typing import Tuple
from copy import deepcopy

from App.styles import *
from steer_opencell_design.Constants import *
from steer_opencell_design.Decorators import *


class Separator:

    def __init__(
            self,  
            material: SeparatorMaterial,
            thickness: float, 
            width: float = None,
            length: float = None,
            name: str = 'Separator',
            datum: Tuple[float, float, float] = (0, 0, 0)
        ):
        """
        Initialize an object that represents a separator
        
        Parameters
        ----------
        material : SeparatorMaterial
            Material of the separator.
        thickness : float
            Thickness of the separator in um.
        width : float, optional
            Width of the separator in mm. Does not need to be provided as it can be calculated from the layup and stack.
        length : float, optional
            Length of the separator in mm. Does not need to be provided as it can be calculated from the layup and stack.
        name : str, optional
            Name of the separator. Defaults to 'Separator'.
        datum : Tuple[float, float, float], optional
            Datum point for the separator, used for positioning in 3D space. Defaults to (0, 0, 0).
        """
        self._folded = False

        self.datum = datum
        self.width = width
        self.length = length
        self.thickness = thickness
        self.material = material
        self.name = name
    
    def _calculate_areal_cost(self):
        
        if hasattr(self, "_material") and hasattr(self, "_thickness") and self._material and self._thickness:
            self._areal_cost = self._material._specific_cost * self._material._density * self._thickness
        else:
            self._areal_cost = None

    def _calculate_area(self):

        if hasattr(self, "_length") and hasattr(self, "_width") and self._length and self._width:
            self._area = self._length * self._width
        else:
            self._area = None

    def _calculate_mass(self):

        if hasattr(self, "_area") and hasattr(self, "_material") and self._area and self.material.density and self.thickness:
            self._mass = self._area * self._material._density * self._thickness
        else:
            self._mass = None

    def _calculate_cost(self):

        if hasattr(self, "_area") and hasattr(self, "_areal_cost") and self._area and self._areal_cost:
            self._cost = self._area * self._areal_cost
        else:
            self._cost = None

    def _calculate_pore_volume(self):

        if hasattr(self, "_area") and hasattr(self, '_material') and self._area and self.material.porosity:
            self._pore_volume = self._area * self._thickness * self._material._porosity
        else:
            self._pore_volume = None

    def _calculate_properties(self):
        """
        Calculate all properties of the separator.
        This method is called when length or width is set.
        """
        self._calculate_areal_cost()
        self._calculate_area()
        self._calculate_mass()
        self._calculate_cost()
        self._calculate_pore_volume()

    def _calculate_traces(self):
        self._get_top_down_trace()
        self._get_side_view_trace()

    def _get_top_down_trace(self) -> go.Scatter:
        """
        Create a trace for the top-down view of the separator.
        """
        if not hasattr(self, "_length") or self._length is None or \
           not hasattr(self, "_width") or self._width is None or \
           not hasattr(self, '_material') or self._material is None or \
           not hasattr(self, '_datum') or self._datum is None or \
           not hasattr(self, '_name') or self._name is None:

            return None
        
        if self._folded:
            length = self._fold_length
        else:
            length = self._length
        
        coordinates = CoordinateManager.build_square_df(
            x=self._datum[0] - length / 2,
            y=self._datum[1] - self._width / 2,
            x_width=length,
            y_width=self._width
        )

        trace = go.Scatter(
            x=coordinates['x'],
            y=coordinates['y'],
            mode='lines',
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor=self._material._color,
            name=self._name
        )

        self._top_down_trace = trace

    def _get_side_view_trace(self) -> go.Scatter:
        """        
        Create a trace for the side view of the separator.
        """
        if not hasattr(self, "_length") or self._length is None or \
           not hasattr(self, "_width") or self._width is None or \
           not hasattr(self, '_material') or self._material is None or \
           not hasattr(self, '_datum') or self._datum is None or \
           not hasattr(self, '_name') or self._name is None:

            return None
        
        if self._folded:
            return None # TODO: Implement side view for folded separators

        coordinates = CoordinateManager.build_square_df(
            x=self._datum[0] - self._length / 2,
            y=self._datum[2] - self._thickness / 2,
            x_width=self._length,
            y_width=self._thickness
        )

        trace = go.Scatter(
            x=coordinates['x'],
            y=coordinates['y'],
            mode='lines',
            line=dict(color='black', width=1),
            fill='toself',
            fillcolor=self._material._color,
            name=self._name
        )

        self._side_trace = trace

    @property
    def cost(self) -> float:

        if hasattr(self, '_cost') and self._cost is not None:
            return round(self._cost, 2)
        else:
            raise AttributeError("Cost has not been calculated. Ensure that length and width are set.")

    @property
    def mass(self) -> float:

        if hasattr(self, '_mass') and self._mass is not None:
            return round(self._mass * KG_TO_G, 2)
        else:
            raise AttributeError("Mass has not been calculated. Ensure that length and width are set.")

    @property
    def area(self) -> float:

        if hasattr(self, '_area') and self._area is not None:
            return round(self._area * M_TO_CM**2, 2)
        else:
            raise AttributeError("Area has not been calculated. Ensure that length and width are set.")

    @property
    def areal_cost(self) -> float:

        if hasattr(self, '_areal_cost') and self._areal_cost is not None:
            return round(self._areal_cost, 2)
        else:
            raise AttributeError("Areal cost has not been calculated. Ensure that length and width are set.")

    @areal_cost.setter
    def areal_cost(self, areal_cost: float) -> None:

        if not isinstance(areal_cost, (int, float)):
            raise TypeError("Areal cost must be a number.")

        if areal_cost < 0:
            raise ValueError("Areal cost cannot be negative.")

        self._areal_cost = float(areal_cost)
        self._material._specific_cost = self._areal_cost / (self.material.density * self.thickness)

        self._calculate_cost()

    @property
    def pore_volume(self) -> float:

        if hasattr(self, '_pore_volume') and self._pore_volume is not None:
            return round(self._pore_volume * M_TO_MM**3, 2)
        else:
            raise ValueError("Pore volume has not been calculated. Ensure that length and width are set.")

    @property
    def datum(self) -> Tuple[float, float, float]:
        return self._datum

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:

        if not isinstance(datum, tuple) or len(datum) != 3:
            raise TypeError("Datum must be a tuple of three floats (x, y, z).")

        if not all(isinstance(coord, (int, float)) for coord in datum):
            raise TypeError("All coordinates in the datum must be numbers.")

        self._datum = tuple(float(coord) for coord in datum)

        self._calculate_traces()

    @property
    def name(self) -> str:
        if hasattr(self, '_name'):
            return self._name
        else:
            return "Unnamed Separator"

    @name.setter
    def name(self, name: str) -> None:

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")

        if len(name) == 0:
            raise ValueError("Name cannot be an empty string.")

        self._name = name

    @property
    def length(self) -> float:

        if hasattr(self, '_length') and self._length is not None:
            return round(self._length * M_TO_MM, 2)
        else:
            return None
        
    @length.setter
    def length(self, length: float) -> None:

        if length is None:
            self._length = None
            return

        if not isinstance(length, (int, float)):
            raise TypeError("Length must be a number.")

        if length < 0:
            raise ValueError("Length cannot be negative.")

        self._length = float(length) * MM_TO_M

        self._calculate_properties()

    @property
    def width(self) -> float:
        
        if hasattr(self, '_width') and self._width is not None:
            return round(self._width * M_TO_MM, 2)
        else:
            return None

    @width.setter
    def width(self, width: float) -> None:

        if width is None:
            self._width = None
            return

        if not isinstance(width, (int, float)):
            raise TypeError("Width must be a number.")

        if width < 0:
            raise ValueError("Width cannot be negative.")

        self._width = float(width) * MM_TO_M
        self._calculate_properties()

    @property
    def material(self) -> SeparatorMaterial:
        return self._material
    
    @material.setter
    def material(self, material: SeparatorMaterial) -> None:

        if not isinstance(material, SeparatorMaterial):
            raise TypeError("Material must be an instance of SeparatorMaterial.")
        
        self._material = deepcopy(material)

        self._calculate_properties()
        self._calculate_traces()

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)

    @thickness.setter
    def thickness(self, thickness: float) -> None:

        if not isinstance(thickness, (int, float)):
            raise TypeError("Thickness must be a number.")

        if thickness < 0:
            raise ValueError("Thickness cannot be negative.")
        
        if thickness > 100:
            raise ValueError("This thickness is too high for a separator. Check the units, it should be in um.")
        
        self._thickness = float(thickness) * UM_TO_M

        self._calculate_properties()
        self._calculate_traces()

    def __str__(self):
        if self._name is not None:
            return f"{self._name}"
        else:
            return f"Separator"
    
    def __repr__(self):
        return self.__str__()
    
    