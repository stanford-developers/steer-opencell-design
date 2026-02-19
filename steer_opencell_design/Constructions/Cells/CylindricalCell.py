"""Cylindrical battery cell implementation."""

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
TAB_ALIGNMENT_TOLERANCE = 2e-3  # 2 mm tolerance for tab-terminal alignment (meters)

# Dimension fit tolerance constant
DIMENSION_FIT_TOLERANCE = 1e-3  # 1 mm tolerance for assembly-encapsulation fit (meters)


class CylindricalCell(_Cell):
    """Complete cylindrical battery cell (e.g., 18650, 21700, 4680 format). Combines a wound jelly roll with a cylindrical canister encapsulation and electrolyte."""

    def __init__(
        self,
        reference_electrode_assembly: WoundJellyRoll,
        encapsulation: CylindricalEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        electrolyte_overfill: float = 20,
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
            Fractional overfill beyond pore volume (default: 20%)
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

    def _validate_assembly_height_fit(
        self, 
        assembly: WoundJellyRoll, 
        encapsulation: CylindricalEncapsulation
    ) -> None:
        """Validate that assembly height fits within encapsulation height.
        
        Parameters
        ----------
        assembly : WoundJellyRoll
            Electrode assembly to validate
        encapsulation : CylindricalEncapsulation
            Encapsulation to validate against
        """
        if assembly._total_height > encapsulation._internal_height + DIMENSION_FIT_TOLERANCE:

            warnings.warn(
                f"Assembly height ({assembly.total_height} mm) exceeds "
                f"encapsulation internal height ({encapsulation.internal_height} mm). "
                "Please ensure compatibility."
            )

    def _validate_assembly_radius_fit(
        self, 
        assembly: WoundJellyRoll, 
        encapsulation: CylindricalEncapsulation
    ) -> None:
        """Validate that assembly radius fits within encapsulation radius.
        
        Parameters
        ----------
        assembly : WoundJellyRoll
            Electrode assembly to validate
        encapsulation : CylindricalEncapsulation
            Encapsulation to validate against
        """
        if assembly._radius > encapsulation._canister._inner_radius + DIMENSION_FIT_TOLERANCE:

            warnings.warn(
                f"Assembly radius ({assembly.radius} mm) exceeds "
                f"encapsulation internal radius ({encapsulation._canister.inner_radius} mm). "
                "Please ensure compatibility."
            )

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
        self._validate_assembly_height_fit(assembly, encapsulation)
        self._validate_assembly_radius_fit(assembly, encapsulation)

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

    def fit_assembly_radius_to_canister(self) -> None:
        """Resize the jelly roll radius to match the canister inner radius."""
        target_radius = self._encapsulation._canister.inner_radius
        self._reference_electrode_assembly.radius = target_radius
        self.reference_electrode_assembly = self._reference_electrode_assembly
        return self
    
    def fit_assembly_height_to_canister(self) -> None:
        """Resize the jelly roll height to match the canister internal height."""
        target_height = self._encapsulation.internal_height
        self._reference_electrode_assembly.height = target_height
        self.reference_electrode_assembly = self._reference_electrode_assembly
        return self

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
        """Generate cross-section view showing the spiral winding and canister."""

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
    def radius(self) -> float:
        """Get the cell outer radius in mm."""
        assembly_radius = self._reference_electrode_assembly.radius
        encapsulation_radius = self._encapsulation.radius
        max_radius = max(assembly_radius, encapsulation_radius)
        return max_radius
    
    @property
    def radius_range(self) -> Tuple[float, float]:
        """Get the valid range for cell radius in mm."""
        assembly_radius_range = self._reference_electrode_assembly.radius_range
        encapsulation_radius_range = self._encapsulation.radius_range
        min_radius = max(assembly_radius_range[0], encapsulation_radius_range[0])
        max_radius = min(assembly_radius_range[1], encapsulation_radius_range[1])
        return (min_radius, max_radius)
    
    @property
    def radius_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell radius in mm."""
        return (0, 500)
    
    @property
    def diameter(self) -> float:
        """Get the cell outer diameter in mm."""
        return self.radius * 2
    
    @property
    def diameter_range(self) -> Tuple[float, float]:
        """Get the valid range for cell diameter in mm."""
        radius_range = self.radius_range
        return (radius_range[0] * 2, radius_range[1] * 2)
    
    @property
    def diameter_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell diameter in mm."""
        return (0, 1000)

    @property
    def height(self) -> float:
        """Get the cell height in mm."""
        assembly_height = self._reference_electrode_assembly.height
        encapsulation_height = self._encapsulation.canister.height
        max_height = max(assembly_height, encapsulation_height)
        return max_height
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Get the valid range for cell height in mm."""
        assembly_height_range = self._reference_electrode_assembly.height_range
        encapsulation_height_range = self._encapsulation.canister.height_range
        min_height = max(assembly_height_range[0], encapsulation_height_range[0])
        max_height = min(assembly_height_range[1], encapsulation_height_range[1])
        return (min_height, max_height)
    
    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell height in mm."""
        return (0, 1000)

    @property
    def reference_electrode_assembly(self) -> WoundJellyRoll:
        """Get the reference wound jelly roll electrode assembly."""
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> CylindricalEncapsulation:
        """Get the cylindrical encapsulation."""
        return self._encapsulation
    
    @property
    def n_electrode_assembly(self) -> int:
        """Get the number of electrode assemblies (always 1 for cylindrical)."""
        return 1

    @radius.setter
    def radius(self, value: float) -> None:
        current_radius = self.radius
        radius_diff = value - current_radius
        self._reference_electrode_assembly.radius = self._reference_electrode_assembly.radius + radius_diff
        self._encapsulation.radius = self._encapsulation.radius + radius_diff
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @diameter.setter
    def diameter(self, value: float) -> None:
        self.validate_positive_float(value, "Diameter")
        self.radius = value / 2

    @height.setter
    def height(self, value: float) -> None:
        current_height = self.height
        height_diff = value - current_height
        self._reference_electrode_assembly.height = self._reference_electrode_assembly.height + height_diff
        self._encapsulation.height = self._encapsulation.height + height_diff
        self.reference_electrode_assembly = self.reference_electrode_assembly

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
        # Clear parent reference on old assembly if exists
        if hasattr(self, '_reference_electrode_assembly') and self._reference_electrode_assembly is not None:
            self._reference_electrode_assembly._set_parent(None)
        self._reference_electrode_assembly = value
        # Set parent reference on new assembly
        value._set_parent(self)

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

        # Clear old parent reference
        if hasattr(self, '_encapsulation') and self._encapsulation is not None:
            if hasattr(self._encapsulation, '_set_parent'):
                self._encapsulation._set_parent(None)

        self._encapsulation = value

        # Set new parent reference for propagation
        if hasattr(value, '_set_parent'):
            value._set_parent(self)

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

