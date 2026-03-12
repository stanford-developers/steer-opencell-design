"""Pouch (soft-pack) battery cell implementation."""

from steer_opencell_design.Components.Containers.Pouch import PouchEncapsulation
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import FlatWoundJellyRoll
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties, recalculate
from steer_core.Constants.Units import *
from steer_core.Mixins.Propagation import propagating_setter

from typing import Tuple
import warnings
import plotly.graph_objects as go
import numpy as np


# Tab alignment tolerance constant
TAB_ALIGNMENT_TOLERANCE = 5e-6  # 5 micron tolerance for tab-terminal alignment (meters)


calculate_encapsulation_properties = recalculate("encapsulation_properties")


class PouchCell(_Cell):
    """Pouch (soft-pack) battery cell. Combines stacked electrode assemblies with laminate film encapsulation, terminals, and electrolyte."""

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
        clipped_tab_length: float = None,
        electrolyte_overfill: float = 20,
        name: str = "Pouch Cell",
    ):
        """Create a pouch cell with stacked electrode assembly.

        Parameters
        ----------
        reference_electrode_assembly : ZFoldStack | PunchedStack
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
        self._calculate_all_properties()

    def _calculate_all_properties(self) -> None:
        """Calculate all cell properties and position encapsulation."""
        self._make_assemblies()
        self._clip_tabs()
        self._position_assemblies()
        self._calculate_encapsulation_properties()
        super()._calculate_all_properties()

    def _calculate_encapsulation_properties(self) -> None:
        """Calculate and update all encapsulation-related properties.
        
        Orchestrates terminal positioning, encapsulation sizing, positioning,
        and hot-pressing operations in the correct sequence.
        """
        self._position_terminals()
        self._size_encapsulation()
        self._position_encapsulation()
        self._hot_press_encapsulation()

    def _clip_tabs(self) -> None:
        """Clip current collector tabs to specified length.
        
        Applies the clipped tab length to all electrode assemblies if a clipped
        tab length has been specified. Otherwise, leaves tabs at full length.
        """
        if self._clipped_tab_length is None:
            return
        
        for assembly in self._electrode_assemblies:
            assembly._clip_current_collector_tabs(self._clipped_tab_length)

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
        self._encapsulation._calculate_volume()

    def _hot_press_encapsulation(self) -> None:
        """Apply hot-pressing to top and bottom laminate sheets.
        
        Creates indentation cavities in both laminates to accommodate the electrode
        assembly stack. The cavity depth is half the total stack thickness, width
        matches the layup width, and height accounts for seal thicknesses. Top
        laminate is pressed inward (negative depth), bottom laminate outward
        (positive depth).
        """
        ref_assembly = self._reference_electrode_assembly
        _hot_press_depth_thickness = ref_assembly._thickness * self._n_electrode_assembly / 2
        _hot_press_width = ref_assembly._layup._width
        _hot_press_height = self._encapsulation._top_laminate._height - self._top_seal_thickness - self._bottom_seal_thickness

        _datum_x = ref_assembly._layup._cathode._datum[0]
        _datum_y = ref_assembly._layup._cathode._datum[1]
        _datum = (_datum_x, _datum_y)

        self._encapsulation._top_laminate._set_hot_press_state(
            -_hot_press_depth_thickness,
            _hot_press_width,
            _hot_press_height,
            _datum
        )

        self._encapsulation._bottom_laminate._set_hot_press_state(
            _hot_press_depth_thickness,
            _hot_press_width,
            _hot_press_height,
            _datum
        )

        self._encapsulation._top_laminate._calculate_coordinates()
        self._encapsulation._bottom_laminate._calculate_coordinates()

    def _size_encapsulation(self) -> None:
        """Calculate and set encapsulation dimensions.
        
        Determines the required width, height, and thickness of the encapsulation
        based on the electrode assembly dimensions plus seal thicknesses. Height is
        calculated from the current collector foil extents, width includes side
        seals, and thickness accounts for the stack and laminate thicknesses.
        """
        top_assembly = self._electrode_assemblies[0]
        cathodes = [c for c in top_assembly._stack if isinstance(c, Cathode)]
        anodes = [a for a in top_assembly._stack if isinstance(a, Anode)]
        max_y = cathodes[0]._current_collector._foil_coordinates[:, 1].max()
        min_y = anodes[0]._current_collector._foil_coordinates[:, 1].min()
        _encapsulation_height = max_y - min_y + self._top_seal_thickness + self._bottom_seal_thickness

        ref_assembly = self._reference_electrode_assembly
        _encapsulation_width = ref_assembly._layup._width + 2 * self._side_seal_thickness
        _encapsulation_thickness = ref_assembly._thickness * self._n_electrode_assembly + self._encapsulation._top_laminate._thickness + self._encapsulation._bottom_laminate._thickness

        encapsulation_width = _encapsulation_width * M_TO_MM
        encapsulation_height = _encapsulation_height * M_TO_MM
        encapsulation_thickness = _encapsulation_thickness * M_TO_MM

        with self._encapsulation.batch_updates():
            self._encapsulation.width = encapsulation_width
            self._encapsulation.height = encapsulation_height
            self._encapsulation.thickness = encapsulation_thickness

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
    def side_seal_thickness(self) -> float:
        """Get side seal thickness."""
        return np.round(self._side_seal_thickness * M_TO_MM, 2)
    
    @property
    def side_seal_thickness_range(self) -> Tuple[float, float]:
        """Get the valid range for side seal thickness in mm."""
        return (0.1, 20.0)
    
    @property
    def side_seal_thickness_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for side seal thickness in mm."""
        return (0.1, 50.0)
    
    @property
    def top_seal_thickness(self) -> float:
        """Get top seal thickness."""
        return np.round(self._top_seal_thickness * M_TO_MM, 2)
    
    @property
    def top_seal_thickness_range(self) -> Tuple[float, float]:
        """Get the valid range for top seal thickness in mm."""
        return (0.1, 20.0)
    
    @property
    def top_seal_thickness_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for top seal thickness in mm."""
        return (0.1, 50.0)
    
    @property
    def bottom_seal_thickness(self) -> float:
        """Get bottom seal thickness."""
        return np.round(self._bottom_seal_thickness * M_TO_MM, 2)
    
    @property
    def bottom_seal_thickness_range(self) -> Tuple[float, float]:
        """Get the valid range for bottom seal thickness in mm."""
        return (0.1, 20.0)
    
    @property
    def bottom_seal_thickness_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for bottom seal thickness in mm."""
        return (0.1, 50.0)

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
    def height(self) -> float:
        """Get the total cell height in mm (assembly + seals)."""
        assembly_height = self._reference_electrode_assembly._layup.height
        top_seal_height = self.top_seal_thickness
        bottom_seal_height = self.bottom_seal_thickness
        total_height = assembly_height + top_seal_height + bottom_seal_height
        return total_height
    
    @property
    def height_range(self) -> float:
        """Get the valid range for cell height in mm."""
        assembly_height_range = self._reference_electrode_assembly._layup.height_range
        top_seal_height = self.top_seal_thickness
        bottom_seal_height = self.bottom_seal_thickness
        min_height = assembly_height_range[0] + top_seal_height + bottom_seal_height
        max_height = assembly_height_range[1] + top_seal_height + bottom_seal_height
        return (min_height, max_height)
    
    @property
    def height_hard_range(self) -> float:
        """Get the hard limit range for cell height in mm."""
        assembly_height_hard_range = self._reference_electrode_assembly._layup.height_hard_range
        top_seal_height = self.top_seal_thickness
        bottom_seal_height = self.bottom_seal_thickness
        min_height = assembly_height_hard_range[0] + top_seal_height + bottom_seal_height
        max_height = assembly_height_hard_range[1] + top_seal_height + bottom_seal_height
        return (min_height, max_height)
    
    @property
    def width(self) -> float:
        """Get the total cell width in mm (assembly + side seals)."""
        assembly_width = self._reference_electrode_assembly._layup.width
        side_seal_width = 2 * self.side_seal_thickness
        total_width = assembly_width + side_seal_width
        return total_width
    
    @property
    def width_range(self) -> float:
        """Get the valid range for cell width in mm."""
        assembly_width_range = self._reference_electrode_assembly._layup.width_range
        side_seal_width = 2 * self.side_seal_thickness
        min_width = assembly_width_range[0] + side_seal_width
        max_width = assembly_width_range[1] + side_seal_width
        return (min_width, max_width)
    
    @property
    def width_hard_range(self) -> float:
        """Get the hard limit range for cell width in mm."""
        assembly_width_hard_range = self._reference_electrode_assembly._layup.width_hard_range
        side_seal_width = 2 * self.side_seal_thickness
        min_width = assembly_width_hard_range[0] + side_seal_width
        max_width = assembly_width_hard_range[1] + side_seal_width
        return (min_width, max_width)
    
    @property
    def thickness(self) -> float:
        """Get the total cell thickness in mm (assemblies + laminates)."""
        _assembly_thickness = self._reference_electrode_assembly._thickness * self._n_electrode_assembly
        _laminate_thickness = self._encapsulation._top_laminate._thickness + self._encapsulation._bottom_laminate._thickness
        _total_thickness = _assembly_thickness + _laminate_thickness
        total_thickness = np.round(_total_thickness * M_TO_MM, 2)
        return total_thickness
    
    @property
    def thickness_range(self) -> float:
        """Get the valid range for cell thickness in mm."""
        assembly_thickness_range = self._reference_electrode_assembly.thickness_range
        laminate_thickness = (self._encapsulation._top_laminate._thickness + self._encapsulation._bottom_laminate._thickness) * M_TO_MM
        min_thickness = np.round(assembly_thickness_range[0] * self._n_electrode_assembly + laminate_thickness, 2)
        max_thickness = np.round(assembly_thickness_range[1] * self._n_electrode_assembly + laminate_thickness, 2)
        return (min_thickness, max_thickness)
    
    @property
    def thickness_hard_range(self) -> float:
        """Get the hard limit range for cell thickness in mm."""
        assembly_thickness_hard_range = self._reference_electrode_assembly.thickness_hard_range
        laminate_thickness = self._encapsulation._top_laminate._thickness + self._encapsulation._bottom_laminate._thickness
        min_thickness = assembly_thickness_hard_range[0] * self._n_electrode_assembly + laminate_thickness
        max_thickness = assembly_thickness_hard_range[1] * self._n_electrode_assembly + laminate_thickness
        return (min_thickness, max_thickness)

    @height.setter
    def height(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "height")

        # get change in height
        current_height = self.height
        height_diff = value - current_height

        # adjust the layup height by the height difference
        new_layup_height = self._reference_electrode_assembly._layup.height + height_diff
        self._reference_electrode_assembly._layup.height = new_layup_height
        self._reference_electrode_assembly.layup = self._reference_electrode_assembly._layup
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @width.setter
    def width(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "width")

        # get change in width
        current_width = self.width
        width_diff = value - current_width

        # adjust the layup width by the width difference
        new_layup_width = self._reference_electrode_assembly._layup.width + width_diff
        self._reference_electrode_assembly._layup.width = new_layup_width
        self._reference_electrode_assembly.layup = self._reference_electrode_assembly._layup
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @thickness.setter
    def thickness(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "thickness")

        # get change in thickness
        current_thickness = self.thickness
        thickness_diff = value - current_thickness

        # adjust the layup thickness by the thickness difference
        new_layup_thickness = (self._reference_electrode_assembly._thickness * M_TO_MM) + thickness_diff / self._n_electrode_assembly

        self._reference_electrode_assembly.thickness = new_layup_thickness
        self.reference_electrode_assembly = self.reference_electrode_assembly

    @clipped_tab_length.setter
    @calculate_all_properties
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
    @propagating_setter()
    def reference_electrode_assembly(self, value: ZFoldStack | PunchedStack | FlatWoundJellyRoll) -> None:
        """Set reference electrode assembly with validation.
        
        Parameters
        ----------
        value : ZFoldStack | PunchedStack | FlatWoundJellyRoll
            New electrode assembly to set
        """
        self.validate_type(value, (ZFoldStack, PunchedStack, FlatWoundJellyRoll), "reference_electrode_assembly")
        self._reference_electrode_assembly = value

    @encapsulation.setter
    @calculate_all_properties
    @propagating_setter()
    def encapsulation(self, value) -> None:
        """Set encapsulation with validation. Automatically converts cell type if encapsulation type changes.
        
        Parameters
        ----------
        value : _Container
            New encapsulation to set. Can be any container type (Prismatic, Pouch, Cylindrical).
            If type differs from current cell type, cell will be automatically converted.
        """
        from steer_opencell_design.Components.Containers.Prismatic import PrismaticEncapsulation
        
        # Only allow PouchEncapsulation or PrismaticEncapsulation
        self.validate_type(value, (PouchEncapsulation, PrismaticEncapsulation), "encapsulation")
        
        # Check if encapsulation type matches cell type
        if isinstance(value, PouchEncapsulation):
            # Same type, proceed normally
            self._encapsulation = value
        else:
            # Different type, convert cell
            self._convert_to_cell_type(value)


