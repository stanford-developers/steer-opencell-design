from steer_opencell_design.Components.Containers.Flexframe import FlexFrameEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import PunchedStack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Components.Electrodes import Cathode, Anode

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Constants.Units import *

from typing import Tuple
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


class FlexFrameCell(_Cell):

    def __init__(
        self,
        electrode_assembly: PunchedStack,
        encapsulation: FlexFrameEncapsulation,
        catholyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        clipped_tab_length: float = None,
        name: str = "FlexFrame Solid State Cell",
    ):
        """Create a flex frame cell with stacked electrode assembly.

        Parameters
        ----------
        electrode_assembly : PunchedStack
            Electrochemical stack defining cell capacity and voltage behavior
        encapsulation : FlexFrameEncapsulation
            Mechanical housing (canister, lid, terminals) defining external geometry
        catholyte : Electrolyte
            Bulk electrolyte material with density and cost properties
        operating_voltage_window : Tuple[float, float]
            Operating voltage window (min_voltage, max_voltage) in volts
        name : str, optional
            Display name for the cell (default: "FlexFrame Cell")
        """
        super().__init__(
            reference_electrode_assembly=electrode_assembly,
            encapsulation=encapsulation,
            n_electrode_assembly=1,
            electrolyte=catholyte,
            electrolyte_overfill=0.0,
            operating_voltage_window=operating_voltage_window,
            name=name,
        )

        self.clipped_tab_length = clipped_tab_length
        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """Calculate all cell properties and position encapsulation."""
        self._make_assemblies()
        self._clip_tabs()
        self._calculate_encapsulation_properties()
        super()._calculate_all_properties()

    def _calculate_encapsulation_properties(self) -> None:
        """Calculate and update all encapsulation-related properties.
        
        Orchestrates terminal positioning, encapsulation sizing, positioning,
        and hot-pressing operations in the correct sequence.
        """
        self._position_terminals()
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

    def _position_encapsulation(self) -> None:
        """Position encapsulation centered around electrode assemblies.
        
        Uses the _get_center_point method from each assembly to calculate the
        geometric center, then positions the encapsulation accordingly.
        """
        # Calculate z-position as midpoint between all assemblies
        assembly_z_datums = [assembly._datum[2] for assembly in self._electrode_assemblies]
        max_z = max(assembly_z_datums) + (self._reference_electrode_assembly._thickness) / 2
        min_z = min(assembly_z_datums) - (self._reference_electrode_assembly._thickness) / 2
        mid_z = (max_z + min_z) / 2 * M_TO_MM

        # Position the encapsulation centered around the electrode assembly stack
        self._encapsulation.datum = (
            self._reference_electrode_assembly._layup._cathode._current_collector._datum[0] * M_TO_MM,
            self._reference_electrode_assembly._layup._cathode._current_collector._datum[1] * M_TO_MM,
            mid_z
        )

    def _position_terminals(self) -> None:
        """Position cathode and anode terminals at tab locations.
        
        Calculates terminal positions based on current collector tab positions
        and clipped tab lengths. Terminals are centered at the average z-position
        of all electrode assemblies. Terminal positions account for electrode
        orientation (transverse vs parallel).
        """
        from steer_opencell_design.Constructions.Layups.MonoLayers import ElectrodeOrientation
        
        # cathode get the tab position
        _current_collector = self._electrode_assemblies[0]._layup._cathode._current_collector
        _terminal = self._encapsulation._cathode_terminal
        _cathode_connector_position_x = _current_collector._tab_position - _current_collector._x_foil_length / 2
        _cathode_connector_position_y = _current_collector._datum[1] + _current_collector._y_foil_length / 2 + self._clipped_tab_length + _terminal._length / 2

        _current_collector = self._electrode_assemblies[0]._layup._anode._current_collector
        _terminal = self._encapsulation._anode_terminal
        _anode_connector_position_x = _current_collector._tab_position - _current_collector._x_foil_length / 2
        _anode_connector_position_y = _current_collector._datum[1]

        if self._reference_electrode_assembly._layup._electrode_orientation == ElectrodeOrientation.TRANSVERSE:
            _anode_connector_position_y -= _current_collector._y_foil_length / 2 + self._clipped_tab_length + _terminal._length / 2
        else:
            _anode_connector_position_y += _current_collector._y_foil_length / 2 + self._clipped_tab_length + _terminal._length / 2

        # get average z position of assemblies
        assembly_z_datums = [assembly._datum[2] for assembly in self._electrode_assemblies]
        avg_assembly_z = np.mean(assembly_z_datums)

        self._encapsulation._cathode_terminal.datum = (
            _cathode_connector_position_x * M_TO_MM,
            _cathode_connector_position_y * M_TO_MM,
            avg_assembly_z * M_TO_MM
        )

        self._encapsulation._anode_terminal.datum = (
            _anode_connector_position_x * M_TO_MM,
            _anode_connector_position_y * M_TO_MM,
            avg_assembly_z * M_TO_MM
        )

        self._encapsulation._terminals_positioned = True

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

        encapsulation_traces = self.encapsulation.get_side_view().data
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

        # Pass opacity to layup's get_top_down_view
        first_assembly = self._electrode_assemblies[0]
        layup_traces = first_assembly._layup.get_top_down_view(opacity=opacity).data
        traces.extend(layup_traces)

        encapsulation_traces = self.encapsulation.get_top_down_view().data
        
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

    @property
    def electrode_assembly(self) -> PunchedStack:
        """Get electrode assembly."""
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> FlexFrameEncapsulation:
        """Get encapsulation."""
        return self._encapsulation
    
    @property
    def clipped_tab_length(self) -> float:
        """Get clipped tab length."""
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

    @electrode_assembly.setter
    @calculate_all_properties
    def electrode_assembly(self, value: PunchedStack) -> None:
        """Set electrode assembly with validation.
        
        Parameters
        ----------
        value : ZFoldStack | PunchedStack
            New electrode assembly to set
        """
        self.validate_type(value, (PunchedStack), "electrode_assembly")
        self._reference_electrode_assembly = value

    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: FlexFrameEncapsulation) -> None:
        """Set encapsulation with validation.
        
        Parameters
        ----------
        value : PouchEncapsulation
            New encapsulation to set
        """
        self.validate_type(value, FlexFrameEncapsulation, "encapsulation")
        self._encapsulation = value


