from typing import Tuple

from steer_opencell_design.Components.Containers.Base import _Container
from steer_core.Constants.Units import *

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_core.Decorators.General import calculate_all_properties

from steer_opencell_design.Materials.Other import LaminateMaterial, TapeMaterial, PrismaticContainerMaterial

from typing import Tuple
from copy import deepcopy
import numpy as np


class LaminateSheet(
    CoordinateMixin, 
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
    ):
    def __init__(
        self,
        areal_cost: float,
        density: float,
        thickness: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Laminate Sheet"
    ):
        """
        Initialize an object that represents a laminate sheet

        Parameters
        ----------
        areal_cost : float
            Areal cost of the laminate in $/m².
        density : float
            Density of the laminate in kg/m³.
        thickness : float
            Thickness of the laminate in um.
        datum : Tuple[float, float, float], optional
            Reference point (x, y, z) in mm. Defaults to (0.0, 0.0, 0.0).
        name : str, optional
            Name of the laminate sheet. Defaults to 'Laminate Sheet'.
        """
        self._update_properties = False

        self.areal_cost = areal_cost
        self.density = density
        self.thickness = thickness
        self.datum = datum
        self.name = name

        # Initialize width and height as None
        self._width = None
        self._height = None

        self._calculate_all_properties()

        self._update_properties = True

    def _calculate_all_properties(self):
        """
        Calculate all properties of the laminate sheet.
        This method is called when height or width is set.
        """
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """
        Calculate bulk properties of the laminate sheet.
        Only calculates if both height and width are available.
        """
        if self._height is None or self._width is None:
            self._area = None
            self._mass = None
            self._cost = None
            return

        self._area = self._height * self._width
        self._mass = self._area * self._density * self._thickness
        self._cost = self._areal_cost * self._area

    def _calculate_coordinates(self):

        if self._width is None or self._height is None:
            return
        
        self._calculate_top_down_coordinates()
        self._calculate_side_cross_section_coordinates()

    def _calculate_side_cross_section_coordinates(self):
        pass

    def _calculate_top_down_coordinates(self):
        
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._height / 2,
            self._width, 
            self._height
        )

        self._top_down_coordinates = np.column_stack((x, y))

        return self._top_down_coordinates

    @property
    def cost(self) -> float:
        if self._cost is None:
            return None
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        if self._mass is None:
            return None
        return round(self._mass * KG_TO_G, 2)

    @property
    def area(self) -> float:
        if self._area is None:
            return None
        return round(self._area * M_TO_CM**2, 2)

    @property
    def areal_cost(self) -> float:
        return round(self._areal_cost, 2)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Get the datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        return self._name

    @property
    def height(self) -> float:
        if self._height is None:
            return None
        return round(self._height * M_TO_MM, 2)
    
    @property
    def height_range(self):
        return (0, 1000)

    @property
    def width(self) -> float:
        if self._width is None:
            return None
        return round(self._width * M_TO_MM, 2)

    @property
    def width_range(self):

        if hasattr(self, "_width_range"):
            return (
                round(self._width_range[0] * M_TO_MM, 2),
                round(self._width_range[1] * M_TO_MM, 2),
            )
        else:
            return (0, 500)

    @property
    def density(self) -> float:
        """Density in kg/m³."""
        return round(self._density, 2)

    @property
    def thickness(self):
        return round(self._thickness * M_TO_UM, 2)

    @property
    def thickness_range(self):
        return (0, 100)

    @areal_cost.setter
    @calculate_all_properties
    def areal_cost(self, areal_cost: float) -> None:
        self.validate_positive_float(areal_cost, "Areal Cost")
        self._areal_cost = float(areal_cost)

    @density.setter
    @calculate_all_properties
    def density(self, density: float) -> None:
        self.validate_positive_float(density, "Density")
        self._density = float(density)

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """Set the datum position in mm."""
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @name.setter
    def name(self, name: str) -> None:
        self.validate_string(name, "Name")
        self._name = name

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "Height")
        self._height = float(height) * MM_TO_M

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "Thickness")
        self._thickness = float(thickness) * UM_TO_M


class PouchTerminal(
    CoordinateMixin,
    ValidationMixin,
    DunderMixin,
    PlotterMixin,
):
    """
    A pouch terminal connector component with rectangular prismatic geometry.
    
    The PouchTerminal represents a terminal tab that extends from a pouch cell,
    typically made from metal materials like aluminum or copper. It has a 
    rectangular cross-section defined by width, length, and height.
    """

    def __init__(
        self,
        material,
        width: float,
        length: float,
        height: float,
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        name: str = "Pouch Terminal",
    ):
        """
        Initialize a pouch terminal connector.
        
        Parameters
        ----------
        material : PrismaticContainerMaterial
            Material for the terminal (typically metal).
        width : float
            Width of the terminal in mm. Must be positive.
        length : float
            Length of the terminal in mm. Must be positive.
        height : float
            Height of the terminal in mm. Must be positive.
        datum : Tuple[float, float, float], optional
            Center position in mm as (x, y, z) coordinates. Defaults to (0.0, 0.0, 0.0).
        name : str, optional
            Component identifier name. Defaults to "Pouch Terminal".
            
        Raises
        ------
        ValueError
            If width, length, or height <= 0 when provided.
        """
        self._update_properties = False

        self.material = material
        self.width = width
        self.length = length
        self.height = height
        self.datum = datum
        self.name = name

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):
        """Calculate all properties of the terminal."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate volume, mass, and cost of the terminal."""
        # Volume in m³
        self._volume = self._width * self._length * self._height
        
        # Mass in kg
        self._mass = self._volume * self.material.density
        
        # Cost in $
        self._cost = self._mass * self.material.specific_cost

    def _calculate_coordinates(self):
        """Calculate the 3D coordinates of the terminal."""
        self._calculate_top_down_coordinates()
        self._calculate_side_cross_section_coordinates()

    def _calculate_top_down_coordinates(self):
        """Calculate top-down view coordinates."""
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._length / 2,
            self._width,
            self._length
        )
        self._top_down_coordinates = np.column_stack((x, y))
        return self._top_down_coordinates

    def _calculate_side_cross_section_coordinates(self):
        """Calculate side cross-section coordinates."""
        x, z = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[2] - self._height / 2,
            self._width,
            self._height
        )
        self._side_cross_section_coordinates = np.column_stack((x, z))
        return self._side_cross_section_coordinates

    # Properties
    @property
    def volume(self) -> float:
        """Volume in cm³."""
        return round(self._volume * M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        """Mass in g."""
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        """Cost in $."""
        return round(self._cost, 2)

    @property
    def width(self) -> float:
        """Width in mm."""
        return round(self._width * M_TO_MM, 2)

    @property
    def width_range(self):
        """Width range in mm."""
        return (0, 100)

    @property
    def length(self) -> float:
        """Length in mm."""
        return round(self._length * M_TO_MM, 2)

    @property
    def length_range(self):
        """Length range in mm."""
        return (0, 200)

    @property
    def height(self) -> float:
        """Height in mm."""
        return round(self._height * M_TO_MM, 2)

    @property
    def height_range(self):
        """Height range in mm."""
        return (0, 50)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        """Component name."""
        return self._name

    # Setters
    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set width in mm."""
        self.validate_positive_float(width, "Width")
        self._width = float(width) * MM_TO_M

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        """Set length in mm."""
        self.validate_positive_float(length, "Length")
        self._length = float(length) * MM_TO_M

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        """Set height in mm."""
        self.validate_positive_float(height, "Height")
        self._height = float(height) * MM_TO_M

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        """Set datum position in mm."""
        self.validate_datum(datum)
        self._datum = tuple(coord * MM_TO_M for coord in datum)

    @name.setter
    def name(self, name: str) -> None:
        """Set component name."""
        self.validate_string(name, "Name")
        self._name = name


class PouchEncapsulation(_Container):

    def __init__(
            self,
            cathode_terminal: PouchTerminal,
            anode_terminal: PouchTerminal,
            top_laminate: LaminateSheet,
            bottom_laminate: LaminateSheet,
            width: float = None,
            height: float = None,
            name: str = "Pouch Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):

        self._update_properties = False
        
        self.cathode_terminal = cathode_terminal
        self.anode_terminal = anode_terminal
        self.top_laminate = top_laminate
        self.bottom_laminate = bottom_laminate
        self.name = name
        self.datum = datum
        
        # Set width and height on laminates if provided
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):
        """Calculate all properties of the pouch encapsulation."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    def _calculate_bulk_properties(self):
        """Calculate bulk properties including volume, mass, and cost."""
        self._calculate_mass()
        self._calculate_cost()

    def _calculate_coordinates(self):
        """Calculate coordinates for all components."""
        # Position laminates relative to datum
        # Top laminate above datum
        if self.top_laminate.width is not None and self.top_laminate.height is not None:
            self._top_laminate.datum = (
                self._datum[0] * M_TO_MM,
                self._datum[1] * M_TO_MM,
                (self._datum[2] + self._top_laminate._thickness / 2) * M_TO_MM
            )
        
        # Bottom laminate below datum
        if self.bottom_laminate.width is not None and self.bottom_laminate.height is not None:
            self._bottom_laminate.datum = (
                self._datum[0] * M_TO_MM,
                self._datum[1] * M_TO_MM,
                (self._datum[2] - self._bottom_laminate._thickness / 2) * M_TO_MM
            )

    def _calculate_mass(self):
        """Calculate total mass and mass breakdown."""
        cathode_mass = self._cathode_terminal._mass
        anode_mass = self._anode_terminal._mass
        
        # Laminate masses (might be None if dimensions not set)
        top_laminate_mass = self._top_laminate._mass if self._top_laminate._mass is not None else 0
        bottom_laminate_mass = self._bottom_laminate._mass if self._bottom_laminate._mass is not None else 0
        
        self._mass = cathode_mass + anode_mass + top_laminate_mass + bottom_laminate_mass
        
        self._mass_breakdown = {
            "Cathode Terminal": cathode_mass,
            "Anode Terminal": anode_mass,
            "Laminates": top_laminate_mass + bottom_laminate_mass
        }

    def _calculate_cost(self):
        """Calculate total cost and cost breakdown."""
        cathode_cost = self._cathode_terminal._cost
        anode_cost = self._anode_terminal._cost
        
        # Laminate costs (might be None if dimensions not set)
        top_laminate_cost = self._top_laminate._cost if self._top_laminate._cost is not None else 0
        bottom_laminate_cost = self._bottom_laminate._cost if self._bottom_laminate._cost is not None else 0
        
        self._cost = cathode_cost + anode_cost + top_laminate_cost + bottom_laminate_cost
        
        self._cost_breakdown = {
            "Cathode Terminal": cathode_cost,
            "Anode Terminal": anode_cost,
            "Top Laminate": top_laminate_cost,
            "Bottom Laminate": bottom_laminate_cost
        }

    # Properties
    @property
    def mass(self) -> float:
        """Total mass in g."""
        return round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        """Total cost in $."""
        return round(self._cost, 2)

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @property
    def name(self) -> str:
        """Encapsulation name."""
        return self._name

    @property
    def cathode_terminal(self) -> PouchTerminal:
        """Cathode terminal component."""
        return self._cathode_terminal

    @property
    def anode_terminal(self) -> PouchTerminal:
        """Anode terminal component."""
        return self._anode_terminal

    @property
    def top_laminate(self) -> LaminateSheet:
        """Top laminate sheet."""
        return self._top_laminate

    @property
    def bottom_laminate(self) -> LaminateSheet:
        """Bottom laminate sheet."""
        return self._bottom_laminate

    @property
    def width(self) -> float:
        """Width of the laminate sheets in mm."""
        return self._top_laminate.width

    @property
    def height(self) -> float:
        """Height of the laminate sheets in mm."""
        return self._top_laminate.height

    @property
    def mass_breakdown(self) -> dict:
        """Mass breakdown by component in g."""
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj * KG_TO_G, 2)
        
        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def cost_breakdown(self) -> dict:
        """Cost breakdown by component in $."""
        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj, 2)
        
        return _round_recursive(self._cost_breakdown)

    # Setters
    @datum.setter
    @calculate_all_properties
    def datum(self, value: Tuple[float, float, float]) -> None:
        """Set datum position in mm."""
        self.validate_datum(value)
        self._datum = tuple(coord * MM_TO_M for coord in value)

    @name.setter
    def name(self, name: str) -> None:
        """Set encapsulation name."""
        self.validate_string(name, "Name")
        self._name = name

    @cathode_terminal.setter
    @calculate_all_properties
    def cathode_terminal(self, terminal: PouchTerminal) -> None:
        """Set cathode terminal."""
        self.validate_type(terminal, PouchTerminal, "Cathode Terminal")
        terminal.name = f"{terminal.name} (Cathode)"
        self._cathode_terminal = terminal

    @anode_terminal.setter
    @calculate_all_properties
    def anode_terminal(self, terminal: PouchTerminal) -> None:
        """Set anode terminal."""
        self.validate_type(terminal, PouchTerminal, "Anode Terminal")
        terminal.name = f"{terminal.name} (Anode)"
        self._anode_terminal = terminal

    @top_laminate.setter
    @calculate_all_properties
    def top_laminate(self, laminate: LaminateSheet) -> None:
        """Set top laminate sheet."""
        self.validate_type(laminate, LaminateSheet, "Top Laminate")
        self._top_laminate = laminate

    @bottom_laminate.setter
    @calculate_all_properties
    def bottom_laminate(self, laminate: LaminateSheet) -> None:
        """Set bottom laminate sheet."""
        self.validate_type(laminate, LaminateSheet, "Bottom Laminate")
        self._bottom_laminate = laminate

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        """Set width of both laminate sheets in mm."""
        self.validate_positive_float(width, "Width")
        self._top_laminate.width = width
        self._bottom_laminate.width = width

    @height.setter
    @calculate_all_properties
    def height(self, height: float) -> None:
        """Set height of both laminate sheets in mm."""
        self.validate_positive_float(height, "Height")
        self._top_laminate.height = height
        self._bottom_laminate.height = height



