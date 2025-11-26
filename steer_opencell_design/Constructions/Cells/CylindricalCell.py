from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Components.Containers.Cylindrical import CylindricalEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import WoundJellyRoll

from steer_opencell_design.Materials.Electrolytes import Electrolyte

from steer_core.Decorators.General import calculate_all_properties



class CylindricalCell(_Cell):

    def __init__(
        self,
        reference_electrode_assembly: WoundJellyRoll,
        encapsulation: CylindricalEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: tuple[float, float],
        electrolyte_overfill: float = 0.2,
        name: str = "Cylindrical Cell",
        n_electrode_assembly: int = 1,
    ):
        """Create a cylindrical cell composed of a wound jelly roll and canister.

        Parameters
        ----------
        reference_electrode_assembly : WoundJellyRoll
            Fully defined jelly-roll electrode assembly that serves as the
            electrochemical stack for the cell.
        encapsulation : CylindricalEncapsulation
            Mechanical enclosure (cannister, lid, terminals) that houses the
            jelly roll and defines external geometry.
        electrolyte : Electrolyte
            Bulk electrolyte model providing density, cost, and chemistry data.
        electrolyte_overfill : float
            Fractional overfill (0-1) applied to the calculated void volume to
            determine required electrolyte mass.
        operating_voltage_window : tuple[float, float]
            Operating voltage window for the cell (typically in volts).
        name : str, optional
            Human-readable identifier for the cell, defaults to "Cylindrical Cell".
        n_electrode_assembly : int, optional
            Number of identical jelly-roll assemblies contained in the cell,
            defaults to one.
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

    @property
    def reference_electrode_assembly(self) -> WoundJellyRoll:
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> CylindricalEncapsulation:
        return self._encapsulation
    
    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: WoundJellyRoll):
        self.validate_type(value, WoundJellyRoll, "reference_electrode_assembly")
        self._reference_electrode_assembly = value
        self._calculate_voltage_limits()
    
    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: CylindricalEncapsulation):
        self.validate_type(value, CylindricalEncapsulation, "encapsulation")
        self._encapsulation = value


