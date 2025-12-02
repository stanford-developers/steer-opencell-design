from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Components.Containers.Cylindrical import CylindricalEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import WoundJellyRoll

from steer_opencell_design.Materials.Electrolytes import Electrolyte

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Constants.Units import *

import warnings
import plotly.graph_objects as go


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

    def _calculate_all_properties(self):
        super()._calculate_all_properties()
        self._position_encapsulation()

    def _position_encapsulation(self) -> None:

        jelly_roll_mid_y_point = self._reference_electrode_assembly._mid_y_point
        encapsulation_mid_y_point = self._encapsulation._mid_y_point

        y_offset = jelly_roll_mid_y_point - encapsulation_mid_y_point

        self._encapsulation.datum = (
            self._encapsulation._datum[0] * M_TO_MM,
            (self._encapsulation._datum[1] + y_offset) * M_TO_MM,
            self._encapsulation._datum[2] * M_TO_MM,
        )

    def _check_assembly_dimensions(self, assembly) -> None:

        if assembly._total_height > self._encapsulation._internal_height:
            warnings.warn(
                f"The height of the provided electrode assembly ({assembly.total_height} mm) "
                f"exceeds the internal height of the encapsulation ({self._encapsulation.internal_height} mm). "
                "Please ensure compatibility between components."
            )

        if assembly._radius > self._encapsulation._cannister._inner_radius:
            warnings.warn(
                f"The radius of the provided electrode assembly ({assembly.radius} mm) "
                f"exceeds the internal radius of the encapsulation ({self._encapsulation._cannister.inner_radius} mm). "
                "Please ensure compatibility between components."
            )

    def _check_encapsulation_dimensions(self, encapsulation) -> None:

        jellyroll = self._reference_electrode_assembly

        if jellyroll._total_height > encapsulation._internal_height:
            warnings.warn(
                f"The height of the provided electrode assembly ({jellyroll.total_height} mm) "
                f"exceeds the internal height of the encapsulation ({encapsulation.internal_height} mm). "
                "Please ensure compatibility between components."
            )

        if jellyroll._radius > encapsulation._cannister._inner_radius:
            warnings.warn(
                f"The radius of the provided electrode assembly ({jellyroll.radius} mm) "
                f"exceeds the internal radius of the encapsulation ({encapsulation._cannister.inner_radius} mm). "
                "Please ensure compatibility between components."
            )

    def get_top_down_view(self, **kwargs) -> None:
        encapsulation_plot = self._encapsulation.plot_side_view()
        jellyroll_plot = self._reference_electrode_assembly.get_top_down_view()
        encapsulation_traces = encapsulation_plot['data']
        jellyroll_traces = jellyroll_plot['data']
        traces = encapsulation_traces + jellyroll_traces

        figure = go.Figure(data=traces)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            title=kwargs.get("title", f"{self.name} Side View"),
            **kwargs,
        )

        return figure

    @property
    def reference_electrode_assembly(self) -> WoundJellyRoll:
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> CylindricalEncapsulation:
        return self._encapsulation
    
    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: WoundJellyRoll):

        # validate type
        self.validate_type(value, WoundJellyRoll, "reference_electrode_assembly")

        # check dimensions
        if hasattr(self, "_encapsulation"):
            self._check_assembly_dimensions(value)

        # set value
        self._reference_electrode_assembly = value

        # recalculate voltage limits
        self._calculate_voltage_limits()
    
    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: CylindricalEncapsulation):

        # validate input type
        self.validate_type(value, CylindricalEncapsulation, "encapsulation")

        # check dimensions
        if hasattr(self, "_reference_electrode_assembly"):
            self._check_encapsulation_dimensions(value)

        # set value
        self._encapsulation = value


