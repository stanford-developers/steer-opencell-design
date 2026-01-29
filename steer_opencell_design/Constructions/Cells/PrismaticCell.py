from steer_opencell_design.Components.Containers.Prismatic import PrismaticEncapsulation
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
import numpy as np

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


class PrismaticCell(_Cell):

    def __init__(
        self,
        reference_electrode_assembly: FlatWoundJellyRoll | ZFoldStack | PunchedStack,
        n_electrode_assembly: int,
        encapsulation: PrismaticEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        clipped_tab_length: float = None,
        electrolyte_overfill: float = 0.2,
        name: str = "Prismatic Cell",
    ):
        """Create a prismatic cell with wound jelly roll or stacked electrode assembly.

        Parameters
        ----------
        reference_electrode_assembly : FlatWoundJellyRoll | ZFoldStack | PunchedStack
            Electrochemical stack defining cell capacity and voltage behavior
        n_electrode_assembly : int
            Number of parallel electrode assemblies
        encapsulation : PrismaticEncapsulation
            Mechanical housing (canister, lid, terminals) defining external geometry
        electrolyte : Electrolyte
            Bulk electrolyte material with density and cost properties
        operating_voltage_window : Tuple[float, float]
            Operating voltage window (min_voltage, max_voltage) in volts
        clipped_tab_length : float, optional
            Length of clipped tabs in mm (default: None, uses full tab length)
        electrolyte_overfill : float, optional
            Fractional overfill beyond pore volume (default: 0.2 = 20%)
        name : str, optional
            Display name for the cell (default: "Prismatic Cell")
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

        self.clipped_tab_length = clipped_tab_length

        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """Calculate all cell properties and position encapsulation."""
        self._make_assemblies()
        self._position_assemblies()
        self._clip_tabs()
        self._calculate_encapsulation_properties()
        super()._calculate_all_properties()

    def _calculate_encapsulation_properties(self) -> None:
        """Calculate and update all encapsulation-related properties.
        
        Orchestrates encapsulation sizing and positioning in the correct sequence.
        """
        self._position_encapsulation()

    def _clip_tabs(self) -> None:
        """Clip current collector tabs to specified length.
        
        Applies the clipped tab length to all electrode assemblies if a clipped
        tab length has been specified. Otherwise, leaves tabs at full length.
        """
        if self._clipped_tab_length is None:
            return
        
        for assembly in self._electrode_assemblies:
            assembly._clip_current_collector_tabs(self._clipped_tab_length)

    def get_top_down_view(self, opacity = 0.3, **kwargs) -> go.Figure:
        """Get top-down view figure of the pouch cell.

        Parameters
        ----------
        opacity : float
            Opacity level for all traces (0.0 to 1.0)
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the top-down view of the pouch cell
        """
        figure = go.Figure()

        traces = []

        first_assembly = self._electrode_assemblies[0]
        layup_traces = first_assembly.get_top_down_view(opacity=opacity).data
        traces.extend(layup_traces)

        encapsulation_traces = self._encapsulation.get_top_down_view(opacity=opacity).data
        
        # Apply opacity only to encapsulation traces
        for trace in encapsulation_traces:
            self.adjust_trace_opacity(trace, opacity)
        
        traces.extend(encapsulation_traces)

        figure.add_traces(traces)

        # Apply layout
        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure
    
    def get_side_view(self, **kwargs) -> go.Figure:
        """Get side view figure of the pouch cell.

        Parameters
        ----------
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the side view of the pouch cell
        """
        figure = go.Figure()

        traces = []

        for i, assembly in enumerate(self.electrode_assemblies):
            assembly_traces = assembly.get_side_view().data
            # Only show legend for first assembly
            if i > 0:
                for trace in assembly_traces:
                    trace.showlegend = False
            traces.extend(assembly_traces)

        encapsulation_traces = self.encapsulation.get_right_left_view().data
        traces.extend(encapsulation_traces)

        figure.add_traces(traces)

        # Apply layout
        figure.update_layout(
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def clipped_tab_length(self) -> float:
        """Get clipped tab length."""
        if self._clipped_tab_length is None:
            return None
        return np.round(self._clipped_tab_length * M_TO_MM, 2)
    
    @property
    def clipped_tab_length_range(self) -> Tuple[float, float]:
        """Get valid range for clipped tab length.
        
        Returns
        -------
        Tuple[float, float]
            (min, max) clipped tab length in mm. Maximum is limited by the
            shortest free (uncoated) tab length among cathode and anode.
        """
        ref_assembly = self._reference_electrode_assembly
        _cathode_cc = ref_assembly._layup._cathode._current_collector
        _cathode_tab_length = _cathode_cc._tab_height
        _cathode_coated_tab_length = _cathode_cc._coated_tab_height
        _free_cathode_tab_length = _cathode_tab_length - _cathode_coated_tab_length
        
        _anode_cc = ref_assembly._layup._anode._current_collector
        _anode_tab_length = _anode_cc._tab_height
        _anode_coated_tab_length = _anode_cc._coated_tab_height
        _free_anode_tab_length = _anode_tab_length - _anode_coated_tab_length
        
        max_clipped_tab_length = min(_free_cathode_tab_length, _free_anode_tab_length) * M_TO_MM
        return (0.0, max_clipped_tab_length)

    @property
    def reference_electrode_assembly(self) -> FlatWoundJellyRoll | ZFoldStack | PunchedStack:
        """Get reference electrode assembly."""
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> PrismaticEncapsulation:
        """Get encapsulation."""
        return self._encapsulation

    @clipped_tab_length.setter
    @calculate_encapsulation_properties
    def clipped_tab_length(self, value: float) -> None:
        """Set clipped tab length with validation.
        
        Parameters
        ----------
        value : float
            New clipped tab length in mm
        """
        if value is None:
            self._clipped_tab_length = None
            return
        
        # Validate input
        self.validate_positive_float(value, "clipped_tab_length")

        # clipped tab length must be less than the cathode or anode tab length
        min_length, max_length = self.clipped_tab_length_range
        if not (min_length <= value <= max_length):
            raise ValueError(f"clipped_tab_length must be between {min_length:.2f} mm and {max_length:.2f} mm.")

        self._clipped_tab_length = float(value) * MM_TO_M

    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: ZFoldStack | PunchedStack) -> None:
        """Set reference electrode assembly with validation.
        
        Parameters
        ----------
        value : ZFoldStack | PunchedStack
            New electrode assembly to set
        """
        self.validate_type(value, (ZFoldStack, PunchedStack, FlatWoundJellyRoll), "reference_electrode_assembly")
        self._reference_electrode_assembly = value

        # Ensure encapsulation connector orientation matches electrode orientation
        from steer_opencell_design.Constructions.Layups.MonoLayers import ElectrodeOrientation
        from steer_opencell_design.Components.Containers.Prismatic import ConnectorOrientation
        
        if self._update_properties:
            if self._reference_electrode_assembly._layup._electrode_orientation == ElectrodeOrientation.LONGITUDINAL:
                if self._encapsulation._connector_orientation != ConnectorOrientation.LONGITUDINAL:
                    self._encapsulation.connector_orientation = ConnectorOrientation.LONGITUDINAL

                    # Swap height and length to match orientation change
                    _original_height = self._encapsulation._canister._height
                    _original_width = self._encapsulation._canister._width
                    self._encapsulation._canister.height = _original_width * M_TO_MM
                    self._encapsulation._canister.width = _original_height * M_TO_MM
                    self._encapsulation.canister = self._encapsulation.canister

            elif self._reference_electrode_assembly._layup._electrode_orientation == ElectrodeOrientation.TRANSVERSE:
                if self._encapsulation._connector_orientation != ConnectorOrientation.TRANSVERSE:
                    self._encapsulation.connector_orientation = ConnectorOrientation.TRANSVERSE
                    
                    # Swap height and length to match orientation change
                    _original_height = self._encapsulation._canister._height
                    _original_width = self._encapsulation._canister._width
                    self._encapsulation._canister.height = _original_width * M_TO_MM
                    self._encapsulation._canister.width = _original_height * M_TO_MM
                    self._encapsulation.canister = self._encapsulation.canister

    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: PrismaticEncapsulation) -> None:
        """Set encapsulation with validation.
        
        Parameters
        ----------
        value : PrismaticEncapsulation
            New encapsulation to set
        """
        self.validate_type(value, PrismaticEncapsulation, "encapsulation")
        self._encapsulation = value

        # Ensure encapsulation connector orientation matches electrode orientation
        from steer_opencell_design.Constructions.Layups.MonoLayers import ElectrodeOrientation
        from steer_opencell_design.Components.Containers.Prismatic import ConnectorOrientation
        if self._update_properties:
            if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
                if self._reference_electrode_assembly._layup._electrode_orientation != ElectrodeOrientation.LONGITUDINAL:
                    self._reference_electrode_assembly._layup._electrode_orientation = ElectrodeOrientation.LONGITUDINAL
            elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
                if self._reference_electrode_assembly._layup._electrode_orientation != ElectrodeOrientation.TRANSVERSE:
                    self._reference_electrode_assembly._layup._electrode_orientation = ElectrodeOrientation.TRANSVERSE


