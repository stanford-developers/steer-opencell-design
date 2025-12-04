from steer_opencell_design.Components.Containers.Pouch import PouchEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import FlatWoundJellyRoll
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Constants.Units import *

from typing import Tuple
import warnings
import plotly.graph_objects as go


# Tab alignment tolerance constant
TAB_ALIGNMENT_TOLERANCE = 5e-6  # 5 micron tolerance for tab-terminal alignment (meters)


class PouchCell(_Cell):

    def __init__(
        self,
        reference_electrode_assembly: FlatWoundJellyRoll | ZFoldStack | PunchedStack,
        n_electrode_assembly: int,
        encapsulation: PouchEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
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

        self._update_properties = True
        self._calculate_all_properties()

