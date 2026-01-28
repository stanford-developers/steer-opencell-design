from steer_opencell_design.Components.Containers.Cylindrical import CylindricalEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import WoundJellyRoll
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Constants.Units import *

from typing import Tuple
import warnings
import plotly.graph_objects as go

# Tab alignment tolerance constant
TAB_ALIGNMENT_TOLERANCE = 3e-3  # 3 mm tolerance for tab-terminal alignment (meters)


class CylindricalCell(_Cell):

    def __init__(
        self,
        reference_electrode_assembly: WoundJellyRoll,
        encapsulation: CylindricalEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        electrolyte_overfill: float = 0.2,
        name: str = "Cylindrical Cell",
    ):
        """Create a cylindrical cell with wound jelly roll electrode assembly.

        Parameters
        ----------
        reference_electrode_assembly : WoundJellyRoll
            Electrochemical stack defining cell capacity and voltage behavior
        encapsulation : CylindricalEncapsulation
            Mechanical housing (canister, lid, terminals) defining external geometry
        electrolyte : Electrolyte
            Bulk electrolyte material with density and cost properties
        operating_voltage_window : Tuple[float, float]
            Operating voltage window (min_voltage, max_voltage) in volts
        electrolyte_overfill : float, optional
            Fractional overfill beyond pore volume (default: 0.2 = 20%)
        name : str, optional
            Display name for the cell (default: "Cylindrical Cell")
        n_electrode_assembly : int, optional
            Number of parallel electrode assemblies (default: 1)
        """
        
        super().__init__(
            reference_electrode_assembly=reference_electrode_assembly,
            encapsulation=encapsulation,
            n_electrode_assembly=1,
            electrolyte=electrolyte,
            electrolyte_overfill=electrolyte_overfill,
            operating_voltage_window=operating_voltage_window,
            name=name,
        )

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """Calculate all cell properties and position encapsulation."""
        self._make_assemblies()
        self._position_assemblies()
        super()._calculate_all_properties()
        self._position_encapsulation()
        self._validate_assembly_encapsulation_fit(self._reference_electrode_assembly, self._encapsulation)
        
    def _position_encapsulation(self) -> None:
        """Align encapsulation vertically to match jelly roll mid-point."""
        jelly_roll_mid_y_point = self._reference_electrode_assembly._mid_y_point
        encapsulation_mid_y_point = self._encapsulation._mid_y_point

        y_offset = jelly_roll_mid_y_point - encapsulation_mid_y_point

        self._encapsulation.datum = (
            self._encapsulation._datum[0] * M_TO_MM,
            (self._encapsulation._datum[1] + y_offset) * M_TO_MM,
            self._encapsulation._datum[2] * M_TO_MM,
        )

    def _get_cathode_terminal_y_position(self, encapsulation: CylindricalEncapsulation) -> float:
        """Extract cathode terminal connector Y position from encapsulation.
        
        Parameters
        ----------
        encapsulation : CylindricalEncapsulation
            Encapsulation to extract position from
            
        Returns
        -------
        float
            Minimum Y coordinate of cathode terminal connector (meters)
        """
        return encapsulation._cathode_terminal_connector._coordinates[:, 1].min()

    def _get_anode_terminal_y_position(self, encapsulation: CylindricalEncapsulation) -> float:
        """Extract anode terminal connector Y position from encapsulation.
        
        Parameters
        ----------
        encapsulation : CylindricalEncapsulation
            Encapsulation to extract position from
            
        Returns
        -------
        float
            Maximum Y coordinate of anode terminal connector (meters)
        """
        return encapsulation._anode_terminal_connector._coordinates[:, 1].max()

    def _is_within_tolerance(self, value1: float, value2: float, tolerance: float) -> bool:
        """Check if two values are within tolerance of each other.
        
        Parameters
        ----------
        value1 : float
            First value to compare
        value2 : float
            Second value to compare
        tolerance : float
            Maximum allowed difference
            
        Returns
        -------
        bool
            True if values are within tolerance
        """
        return abs(value1 - value2) <= tolerance

    def _validate_assembly_encapsulation_fit(
        self, 
        assembly: WoundJellyRoll, 
        encapsulation: CylindricalEncapsulation
    ) -> None:
        """Validate that assembly fits within encapsulation and tabs align with terminals.
        
        Parameters
        ----------
        assembly : WoundJellyRoll
            Electrode assembly to validate
        encapsulation : CylindricalEncapsulation
            Encapsulation to validate against
        """
        # Height validation
        if assembly._total_height > encapsulation._internal_height:
            warnings.warn(
                f"Assembly height ({assembly.total_height} mm) exceeds "
                f"encapsulation internal height ({encapsulation.internal_height} mm). "
                "Please ensure compatibility."
            )

        # Radius validation
        if assembly._radius > encapsulation._canister._inner_radius:
            warnings.warn(
                f"Assembly radius ({assembly.radius} mm) exceeds "
                f"encapsulation internal radius ({encapsulation._canister.inner_radius} mm). "
                "Please ensure compatibility."
            )

        # Cathode tab alignment validation
        cathode_cc_max_y = assembly._get_cathode_tab_y_position()
        cathode_terminal_min_y = self._get_cathode_terminal_y_position(encapsulation)
        
        if not self._is_within_tolerance(cathode_cc_max_y, cathode_terminal_min_y, TAB_ALIGNMENT_TOLERANCE):
            warnings.warn(
                f"Cathode tab position ({cathode_cc_max_y * M_TO_MM:.1f} mm) "
                f"not aligned with terminal ({cathode_terminal_min_y * M_TO_MM:.1f} mm)."
            )
        
        # Anode tab alignment validation
        anode_cc_min_y = assembly._get_anode_tab_y_position()
        anode_terminal_max_y = self._get_anode_terminal_y_position(encapsulation)
        
        if not self._is_within_tolerance(anode_cc_min_y, anode_terminal_max_y, TAB_ALIGNMENT_TOLERANCE):
            warnings.warn(
                f"Anode tab position ({anode_cc_min_y * M_TO_MM:.1f} mm) "
                f"not aligned with terminal ({anode_terminal_max_y * M_TO_MM:.1f} mm)."
            )

    def _check_assembly_dimensions(self, assembly: WoundJellyRoll) -> None:
        """Validate assembly dimensions against current encapsulation.
        
        Parameters
        ----------
        assembly : WoundJellyRoll
            Assembly to validate
        """
        self._validate_assembly_encapsulation_fit(assembly, self._encapsulation)

    def _check_encapsulation_dimensions(self, encapsulation: CylindricalEncapsulation) -> None:
        """Validate encapsulation dimensions against current assembly.
        
        Parameters
        ----------
        encapsulation : CylindricalEncapsulation
            Encapsulation to validate
        """
        self._validate_assembly_encapsulation_fit(self._reference_electrode_assembly, encapsulation)

    def get_top_down_view(self, **kwargs) -> go.Figure:
        """Generate top down view plot showing encapsulation and jelly roll cross-section.
        
        Parameters
        ----------
        **kwargs
            Additional layout options (paper_bgcolor, plot_bgcolor, title, etc.)
            
        Returns
        -------
        go.Figure
            Plotly figure with combined encapsulation and jelly roll traces
        """
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
            **kwargs,
        )

        return figure
    
    def get_cross_section(self, **kwargs) -> go.Figure:

        spiral_plot = self._reference_electrode_assembly.get_spiral_plot()
        spiral_traces = spiral_plot['data']
        encapsulation_trace = self._encapsulation._canister.top_down_cross_section_trace
        traces = spiral_traces + (encapsulation_trace,)

        figure = go.Figure(data=traces)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure
        
    @property
    def reference_electrode_assembly(self) -> WoundJellyRoll:
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> CylindricalEncapsulation:
        return self._encapsulation
    
    @property
    def n_electrode_assembly(self) -> int:
        return 1

    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: WoundJellyRoll) -> None:
        """Set reference electrode assembly with validation.
        
        Parameters
        ----------
        value : WoundJellyRoll
            New electrode assembly to set
        """
        self.validate_type(value, WoundJellyRoll, "reference_electrode_assembly")
        self._reference_electrode_assembly = value

    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: CylindricalEncapsulation) -> None:
        """Set encapsulation with validation.
        
        Parameters
        ----------
        value : CylindricalEncapsulation
            New encapsulation to set
        """
        self.validate_type(value, CylindricalEncapsulation, "encapsulation")
        self._encapsulation = value

    @n_electrode_assembly.setter
    def n_electrode_assembly(self, value: int) -> None:
        """Set number of electrode assemblies with validation.
        
        Parameters
        ----------
        value : int
            Number of parallel electrode assemblies (must be 1 for cylindrical cells)
        """
        if value != 1:
            raise ValueError("Cylindrical cells can only have 1 electrode assembly.")
        
        self._n_electrode_assembly = value

