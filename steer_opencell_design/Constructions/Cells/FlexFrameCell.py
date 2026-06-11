# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Flex-frame battery cell implementation."""

from steer_opencell_design.Components.Containers.Flexframe import FlexFrameEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import PunchedStack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell

from steer_core.Decorators.General import calculate_all_properties, recalculate
from steer_core.Constants.Units import *
from steer_core.Mixins.Propagation import propagating_setter

from typing import Tuple
import plotly.graph_objects as go
import numpy as np


class FlexFrameCell(_Cell):
    """Flex-frame battery cell for solid-state or specialized designs. Uses a rigid polymer frame with laminate sealing instead of a metal canister."""

    def __init__(
        self,
        reference_electrode_assembly: PunchedStack,
        encapsulation: FlexFrameEncapsulation,
        catholyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        clipped_tab_length: float = None,
        name: str = "FlexFrame Solid State Cell",
    ):
        """Create a flex frame cell with stacked electrode assembly.

        Parameters
        ----------
        reference_electrode_assembly : PunchedStack
            Electrochemical stack defining cell capacity and voltage behavior
        encapsulation : FlexFrameEncapsulation
            Mechanical housing (canister, lid, terminals) defining external geometry
        catholyte : Electrolyte
            Bulk electrolyte material with density and cost properties
        operating_voltage_window : Tuple[float, float]
            Operating voltage window (min_voltage, max_voltage) in volts
        name : str, optional
            Display name for the cell (default: "FlexFrame Solid State Cell")
        """
        super().__init__(
            reference_electrode_assembly=reference_electrode_assembly,
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
        self._position_assemblies()
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

    def _position_assemblies(self) -> None:
        """Position electrode assemblies with datum at the origin.
        
        For flex frame cells, assemblies are positioned with their datum at
        (0, 0, 0) since there is always exactly one assembly.
        """
        for assembly in self._electrode_assemblies:
            assembly.datum = (0, 0, 0)

    def _position_encapsulation(self) -> None:
        """Position encapsulation so the cutout center aligns with the assembly.
        
        The FlexFrame footprint is already constructed with the cutout center at
        the frame's datum origin. Setting the encapsulation datum to (0, 0, mid_z)
        aligns the cutout center with the assembly at the origin.
        """
        # Calculate z-position as midpoint between all assemblies
        assembly_z_datums = [assembly._datum[2] for assembly in self._electrode_assemblies]
        max_z = max(assembly_z_datums) + (self._reference_electrode_assembly._thickness) / 2
        min_z = min(assembly_z_datums) - (self._reference_electrode_assembly._thickness) / 2
        mid_z = (max_z + min_z) / 2 * M_TO_MM

        # Position the encapsulation with cutout center at (0, 0)
        self._encapsulation.datum = (0, 0, mid_z)

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

    def plot_side_view(self, **kwargs) -> go.Figure:
        """Get side view figure of the flex frame cell.

        Parameters
        ----------
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the side view of the flex frame cell
        """
        figure = go.Figure()

        traces = []

        for i, assembly in enumerate(self.electrode_assemblies):
            assembly_traces = assembly.plot_side_view().data
            # Only show legend for first assembly
            if i > 0:
                for trace in assembly_traces:
                    trace.showlegend = False
            traces.extend(assembly_traces)

        encapsulation_traces = self.encapsulation.plot_side_view().data
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
    
    def plot_top_down_view(self, opacity = 0.3, **kwargs) -> go.Figure:
        """Get top-down view figure of the flex frame cell.

        Parameters
        ----------
        opacity : float
            Opacity level for all traces (0.0 to 1.0)
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the top-down view of the flex frame cell
        """
        figure = go.Figure()

        traces = []

        # Pass opacity to layup's plot_top_down_view
        first_assembly = self._electrode_assemblies[0]
        layup_traces = first_assembly._layup.plot_top_down_view(opacity=opacity).data
        traces.extend(layup_traces)

        encapsulation_traces = self.encapsulation.plot_top_down_view().data
        
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
    def reference_electrode_assembly(self) -> PunchedStack:
        """Get reference electrode assembly."""
        return self._reference_electrode_assembly
    
    @property
    def encapsulation(self) -> FlexFrameEncapsulation:
        """Get encapsulation."""
        return self._encapsulation

    @property
    def n_electrode_assembly(self) -> int:
        """Get the number of electrode assemblies (always 1 for flex frame)."""
        return 1

    @n_electrode_assembly.setter
    def n_electrode_assembly(self, value: int) -> None:
        """Set number of electrode assemblies with validation."""
        if value != 1:
            raise ValueError("FlexFrame cells can only have 1 electrode assembly.")
        self._n_electrode_assembly = value

    @property
    def height(self) -> float:
        """Get the total cell height in mm (encapsulation height)."""
        return self._encapsulation.height

    @property
    def height_range(self) -> Tuple[float, float]:
        """Get the valid range for cell height in mm."""
        layup_height_range = self._reference_electrode_assembly._layup.height_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * M_TO_MM
        overhead = 2 * laminate_thickness
        return (layup_height_range[0] + overhead, layup_height_range[1] + overhead)

    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell height in mm."""
        layup_height_hard_range = self._reference_electrode_assembly._layup.height_hard_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * M_TO_MM
        overhead = 2 * laminate_thickness
        return (layup_height_hard_range[0] + overhead, layup_height_hard_range[1] + overhead)

    @property
    def width(self) -> float:
        """Get the total cell width in mm (encapsulation width)."""
        return self._encapsulation.width

    @property
    def width_range(self) -> Tuple[float, float]:
        """Get the valid range for cell width in mm."""
        layup_width_range = self._reference_electrode_assembly._layup.width_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * M_TO_MM
        overhead = 2 * laminate_thickness
        return (layup_width_range[0] + overhead, layup_width_range[1] + overhead)

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell width in mm."""
        layup_width_hard_range = self._reference_electrode_assembly._layup.width_hard_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * M_TO_MM
        overhead = 2 * laminate_thickness
        return (layup_width_hard_range[0] + overhead, layup_width_hard_range[1] + overhead)

    @property
    def thickness(self) -> float:
        """Get the total cell thickness in mm (assembly + laminates)."""
        _assembly_thickness = self._reference_electrode_assembly._thickness
        _laminate_thickness = self._encapsulation._laminate_sheet._thickness * 2
        _total_thickness = _assembly_thickness + _laminate_thickness
        return _total_thickness * M_TO_MM

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Get the valid range for cell thickness in mm."""
        assembly_thickness_range = self._reference_electrode_assembly.thickness_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * 2 * M_TO_MM
        min_thickness = assembly_thickness_range[0] + laminate_thickness
        max_thickness = assembly_thickness_range[1] + laminate_thickness
        return (min_thickness, max_thickness)

    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell thickness in mm."""
        assembly_thickness_hard_range = self._reference_electrode_assembly.thickness_hard_range
        laminate_thickness = self._encapsulation._laminate_sheet._thickness * 2 * M_TO_MM
        min_thickness = assembly_thickness_hard_range[0] + laminate_thickness
        max_thickness = assembly_thickness_hard_range[1] + laminate_thickness
        return (min_thickness, max_thickness)

    @height.setter
    def height(self, value: float) -> None:
        """Set cell height by adjusting the layup height."""
        self.validate_positive_float(value, "height")
        current_height = self.height
        height_diff = value - current_height
        new_layup_height = self._reference_electrode_assembly._layup.height + height_diff
        self._reference_electrode_assembly._layup.height = new_layup_height
        self._reference_electrode_assembly.layup = self._reference_electrode_assembly._layup
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @width.setter
    def width(self, value: float) -> None:
        """Set cell width by adjusting the layup width."""
        self.validate_positive_float(value, "width")
        current_width = self.width
        width_diff = value - current_width
        new_layup_width = self._reference_electrode_assembly._layup.width + width_diff
        self._reference_electrode_assembly._layup.width = new_layup_width
        self._reference_electrode_assembly.layup = self._reference_electrode_assembly._layup
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @thickness.setter
    def thickness(self, value: float) -> None:
        """Set cell thickness by adjusting the assembly thickness."""
        self.validate_positive_float(value, "thickness")
        current_thickness = self.thickness
        thickness_diff = value - current_thickness
        new_assembly_thickness = (self._reference_electrode_assembly._thickness * M_TO_MM) + thickness_diff
        self._reference_electrode_assembly.thickness = new_assembly_thickness
        self.reference_electrode_assembly = self.reference_electrode_assembly
    
    @property
    def clipped_tab_length(self) -> float:
        """Get clipped tab length."""
        return self._clipped_tab_length * M_TO_MM
    
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
    @recalculate("encapsulation_properties")
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
    @propagating_setter()
    def reference_electrode_assembly(self, value: PunchedStack) -> None:
        """Set reference electrode assembly with validation.
        
        Parameters
        ----------
        value : PunchedStack
            New electrode assembly to set
        """
        self.validate_type(value, (PunchedStack), "reference_electrode_assembly")
        self._reference_electrode_assembly = value

    @encapsulation.setter
    @calculate_all_properties
    @propagating_setter()
    def encapsulation(self, value: FlexFrameEncapsulation) -> None:
        """Set encapsulation with validation.
        
        Parameters
        ----------
        value : FlexFrameEncapsulation
            New encapsulation to set
        """
        self.validate_type(value, FlexFrameEncapsulation, "encapsulation")
        self._encapsulation = value


