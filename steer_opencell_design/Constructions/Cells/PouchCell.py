from steer_opencell_design.Components.Containers.Pouch import PouchEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import FlatWoundJellyRoll
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Constants.Units import *

from typing import Tuple
import warnings
import plotly.graph_objects as go
from functools import wraps



# Tab alignment tolerance constant
TAB_ALIGNMENT_TOLERANCE = 5e-6  # 5 micron tolerance for tab-terminal alignment (meters)


def calculate_encapsulation_properties(func):
    """
    Decorator to recalculate both spatial and bulk properties after a method call.
    This is useful for methods that modify both geometry and material properties.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, "_update_properties") and self._update_properties:
            self._calculate_encapsulation_properties()
        return result

    return wrapper


class PouchCell(_Cell):

    def __init__(
        self,
        reference_electrode_assembly: ZFoldStack | PunchedStack,
        n_electrode_assembly: int,
        encapsulation: PouchEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        side_seal_thickness: float = 5,
        top_seal_thickness: float = 5,
        bottom_seal_thickness: float = 5,
        clipped_tab_length: float = 0.0,
        electrolyte_overfill: float = 0.2,
        name: str = "Pouch Cell",
    ):
        """Create a cylindrical cell with wound jelly roll electrode assembly.

        Parameters
        ----------
        reference_electrode_assembly : WoundJellyRoll
            Electrochemical stack defining cell capacity and voltage behavior
        encapsulation : PouchEncapsulation
            Mechanical housing (canister, lid, terminals) defining external geometry
        electrolyte : Electrolyte
            Bulk electrolyte material with density and cost properties
        operating_voltage_window : Tuple[float, float]
            Operating voltage window (min_voltage, max_voltage) in volts
        electrolyte_overfill : float, optional
            Fractional overfill beyond pore volume (default: 0.2 = 20%)
        name : str, optional
            Display name for the cell (default: "Pouch Cell")
        n_electrode_assembly : int, optional
            Number of parallel electrode assemblies (default: 1)
        """
        
        super().__init__(
            reference_electrode_assembly=reference_electrode_assembly,
            encapsulation=encapsulation,
            n_electrode_assembly=n_electrode_assembly,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            operating_voltage_window=operating_voltage_window,
            name=name,
        )

        self.side_seal_thickness = side_seal_thickness
        self.top_seal_thickness = top_seal_thickness
        self.bottom_seal_thickness = bottom_seal_thickness
        self.clipped_tab_length = clipped_tab_length

        self._update_properties = True
        self._clip_tabs()
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """Calculate all cell properties and position encapsulation."""
        self._calculate_encalpsulation_properties()
        super()._calculate_all_properties()

    def _calculate_encalpsulation_properties(self) -> None:
        self._position_terminals()
        self._size_encapsulation()
        self._position_encapsulation()
        self._hot_press_encapsulation()

    def _clip_tabs(self) -> None:
        pass

    def _position_terminals(self) -> None:
        pass

    def _hot_press_encapsulation(self) -> None:
        pass

    def _size_encapsulation(self) -> None:

        _encapsulation_width = self._reference_electrode_assembly._layup._width + 2 * self._side_seal_thickness
        _encapsulation_height = self._reference_electrode_assembly._layup._height + self._top_seal_thickness + self._bottom_seal_thickness + self._clipped_tab_length
        _encapsulation_thickness = self._reference_electrode_assembly._thickness * self._n_electrode_assembly + self._encapsulation._top_laminate._thickness + self._encapsulation._bottom_laminate._thickness

        encapsulation_width = _encapsulation_width * M_TO_MM
        encapsulation_height = _encapsulation_height * M_TO_MM
        encapsulation_thickness = _encapsulation_thickness * M_TO_MM

        self._encapsulation.width = encapsulation_width
        self._encapsulation.height = encapsulation_height
        self._encapsulation.thickness = encapsulation_thickness

    def _position_encapsulation(self) -> None:
        pass

    @property
    def side_seal_thickness(self) -> float:
        """Get side seal thickness."""
        return self._side_seal_thickness
    
    @property
    def top_seal_thickness(self) -> float:
        """Get top seal thickness."""
        return self._top_seal_thickness
    
    @property
    def bottom_seal_thickness(self) -> float:
        """Get bottom seal thickness."""
        return self._bottom_seal_thickness

    @property
    def reference_electrode_assembly(self) -> ZFoldStack | PunchedStack:
        """Get reference electrode assembly."""
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> PouchEncapsulation:
        """Get encapsulation."""
        return self._encapsulation
    
    @property
    def clipped_tab_length(self) -> float:
        """Get clipped tab length."""
        return self._clipped_tab_length
    
    @property
    def clipped_tab_length_range(self) -> Tuple[float, float]:
        _cathode_tab_length = self._reference_electrode_assembly._layup._cathode._current_collector._tab_height
        _cathode_coated_tab_length = self._reference_electrode_assembly._layup._cathode._current_collector._coated_tab_height
        _free_cathode_tab_length = _cathode_tab_length - _cathode_coated_tab_length
        _anode_tab_length = self._reference_electrode_assembly._layup._anode._current_collector._tab_height
        _anode_coated_tab_length = self._reference_electrode_assembly._layup._anode._current_collector._coated_tab_height
        _free_anode_tab_length = _anode_tab_length - _anode_coated_tab_length
        max_clipped_tab_length = min(_free_cathode_tab_length, _free_anode_tab_length) * M_TO_MM
        return (0.0, max_clipped_tab_length)

    @clipped_tab_length.setter
    @calculate_encapsulation_properties
    def clipped_tab_length(self, value: float) -> None:
        """Set clipped tab length with validation.
        
        Parameters
        ----------
        value : float
            New clipped tab length in mm
        """
        # Validate input
        self.validate_positive_float(value, "clipped_tab_length")

        # clipped tab length must be less than the cathode or anode tab length
        min_length, max_length = self.clipped_tab_length_range
        if not (min_length <= value <= max_length):
            raise ValueError(f"clipped_tab_length must be between {min_length:.2f} mm and {max_length:.2f} mm.")

        self._clipped_tab_length = float(value) * MM_TO_M
    
    @side_seal_thickness.setter
    @calculate_bulk_properties
    @calculate_encapsulation_properties
    def side_seal_thickness(self, value: float) -> None:
        """Set side seal thickness with validation.
        
        Parameters
        ----------
        value : float
            New side seal thickness in mm
        """
        self.validate_positive_float(value, "side_seal_thickness")
        self._side_seal_thickness = float(value) * MM_TO_M

    @top_seal_thickness.setter
    @calculate_bulk_properties
    @calculate_encapsulation_properties
    def top_seal_thickness(self, value: float) -> None:
        """Set top seal thickness with validation.
        
        Parameters
        ----------
        value : float
            New top seal thickness in mm
        """
        self.validate_positive_float(value, "top_seal_thickness")
        self._top_seal_thickness = float(value) * MM_TO_M

    @bottom_seal_thickness.setter
    @calculate_bulk_properties
    @calculate_encapsulation_properties
    def bottom_seal_thickness(self, value: float) -> None:
        """Set bottom seal thickness with validation.
        
        Parameters
        ----------
        value : float
            New bottom seal thickness in mm
        """
        self.validate_positive_float(value, "bottom_seal_thickness")
        self._bottom_seal_thickness = float(value) * MM_TO_M

    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: ZFoldStack | PunchedStack) -> None:
        """Set reference electrode assembly with validation.
        
        Parameters
        ----------
        value : ZFoldStack | PunchedStack
            New electrode assembly to set
        """
        self.validate_type(value, (ZFoldStack, PunchedStack), "reference_electrode_assembly")
        self._reference_electrode_assembly = value

    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: PouchEncapsulation) -> None:
        """Set encapsulation with validation.
        
        Parameters
        ----------
        value : PouchEncapsulation
            New encapsulation to set
        """
        self.validate_type(value, PouchEncapsulation, "encapsulation")
        self._encapsulation = value


