"""Prismatic battery cell implementation."""

from steer_opencell_design.Components.Containers.Prismatic import PrismaticEncapsulation, ConnectorOrientation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import FlatWoundJellyRoll, WoundJellyRoll
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack, _Stack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Mixins.Propagation import propagating_setter
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


class PrismaticCell(_Cell):
    """Prismatic hard-case battery cell. Supports both stacked and flat-wound jelly roll internal constructions with a rigid metal canister."""

    def __init__(
        self,
        reference_electrode_assembly: FlatWoundJellyRoll | ZFoldStack | PunchedStack,
        n_electrode_assembly: int,
        encapsulation: PrismaticEncapsulation,
        electrolyte: Electrolyte,
        operating_voltage_window: Tuple[float, float] = (None, None),
        clipped_tab_length: float = None,
        electrolyte_overfill: float = 20,
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
        self._sync_connector_orientation()
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
        """Get top-down view figure of the prismatic cell.

        Parameters
        ----------
        opacity : float
            Opacity level for all traces (0.0 to 1.0)
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the top-down view of the prismatic cell
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
        """Get side view figure of the prismatic cell.

        Parameters
        ----------
        kwargs : dict
            Additional keyword arguments for figure customization

        Returns
        -------
        go.Figure
            Plotly figure object representing the side view of the prismatic cell
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
    def length(self) -> float:
        """Get the cell length (depth) in mm."""
        _assemblies_length = self._reference_electrode_assembly._thickness * self._n_electrode_assembly
        _encapsulation_length = self._encapsulation._canister._length
        _largest_length = max(_assemblies_length, _encapsulation_length)
        return np.round(_largest_length * M_TO_MM, 2)
    
    @property
    def length_range(self) -> float:
        """Get the valid range for cell length in mm."""
        assemblies_thickness_range = self._reference_electrode_assembly.thickness_range
        assemblies_minimum_length = assemblies_thickness_range[0] * self._n_electrode_assembly + self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        assemblies_maximum_length = assemblies_thickness_range[1] * self._n_electrode_assembly + self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        return (
            np.round(assemblies_minimum_length, 2), 
            np.round(assemblies_maximum_length, 2)
        )
    
    @property
    def length_hard_range(self) -> float:
        """Get the hard limit range for cell length in mm."""
        assemblies_thickness_range = self._reference_electrode_assembly.thickness_hard_range
        assemblies_minimum_length = assemblies_thickness_range[0] * self._n_electrode_assembly + self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        assemblies_maximum_length = assemblies_thickness_range[1] * self._n_electrode_assembly + self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        return (
            np.round(assemblies_minimum_length, 2), 
            np.round(assemblies_maximum_length, 2)
        )
    
    @property
    def width(self) -> float:
        """Get the cell width in mm."""

        _layup_width = self._reference_electrode_assembly._layup._width
        
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            _canister_width = self._encapsulation._canister._width
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            _canister_width = self._encapsulation._canister._height
        
        _largest_width = max(_layup_width, _canister_width)
        
        return np.round(_largest_width * M_TO_MM, 2)
    
    @property
    def width_range(self) -> Tuple[float, float]:
        """Get the valid range for cell width in mm."""

        # get the width range of the layup
        layup_width_range = self._reference_electrode_assembly.layup.width_range

        # additional factor for encapsulation
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            additional_width = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            additional_width = self._encapsulation._lid_assembly._thickness * M_TO_MM

        minimum_width = layup_width_range[0] + additional_width
        maximum_width = layup_width_range[1] + additional_width

        return (
            np.round(minimum_width, 2), 
            np.round(maximum_width, 2)
        )

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell width in mm."""

        # get the width range of the layup
        layup_width_range = self._reference_electrode_assembly.layup.width_hard_range

        # additional factor for encapsulation
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            additional_width = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            additional_width = self._encapsulation._lid_assembly._thickness * M_TO_MM

        minimum_width = layup_width_range[0] + additional_width
        maximum_width = layup_width_range[1] + additional_width

        return (
            np.round(minimum_width, 2), 
            np.round(maximum_width, 2)
        )
    
    @property
    def n_electrode_assembly(self) -> int:
        """Get the number of electrode assemblies in the cell."""
        return self._n_electrode_assembly

    @property
    def height(self) -> float:
        """Get the cell height in mm."""
        from steer_opencell_design.Constructions.Layups.Laminate import Laminate

        # Laminate uses _width for y-dimension, MonoLayer uses _height
        layup = self._reference_electrode_assembly._layup
        if isinstance(layup, Laminate):
            _layup_height = layup._width
        else:
            _layup_height = layup._height
        
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            _canister_height = self._encapsulation._canister._height
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            _canister_height = self._encapsulation._canister._width

        _largest_height = max(_layup_height, _canister_height)
        
        return np.round(_largest_height * M_TO_MM, 2)
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Get the valid range for cell height in mm."""
        from steer_opencell_design.Constructions.Layups.Laminate import Laminate
        
        # Laminate uses width_range for y-dimension, MonoLayer uses height_range
        layup = self._reference_electrode_assembly.layup
        if isinstance(layup, Laminate):
            layup_height_range = layup.width_range
        else:
            layup_height_range = layup.height_range

        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            additional_height = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            additional_height = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM

        minimum_height = layup_height_range[0] + additional_height
        maximum_height = layup_height_range[1] + additional_height

        return (
            np.round(minimum_height, 2), 
            np.round(maximum_height, 2)
        )
    
    @property
    def height_hard_range(self) -> Tuple[float, float]:
        """Get the hard limit range for cell height in mm."""
        from steer_opencell_design.Constructions.Layups.Laminate import Laminate
        
        # Laminate uses width_hard_range for y-dimension, MonoLayer uses height_hard_range
        layup = self._reference_electrode_assembly.layup
        if isinstance(layup, Laminate):
            layup_height_range = layup.width_hard_range
        else:
            layup_height_range = layup.height_hard_range

        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            additional_height = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            additional_height = self._encapsulation._canister._wall_thickness * 2 * M_TO_MM

        minimum_height = layup_height_range[0] + additional_height
        maximum_height = layup_height_range[1] + additional_height

        return (
            np.round(minimum_height, 2), 
            np.round(maximum_height, 2)
        )

    @height.setter
    @calculate_all_properties
    def height(self, value: float) -> None:
        """Set the cell height by adjusting the layup and encapsulation dimensions.

        Parameters
        ----------
        value : float
            Desired cell height in millimeters
        """
        from steer_opencell_design.Constructions.Layups.Laminate import Laminate

        # validate input
        self.validate_positive_float(value, "height")

        # get the height difference
        current_height = self.height
        height_difference = value - current_height

        if isinstance(self._reference_electrode_assembly, _Stack):
            # For stacked assemblies, update layup height directly
            layup = self._reference_electrode_assembly.layup
            if isinstance(layup, Laminate):
                # Laminate uses width for y-dimension
                new_layup_width = layup.width + height_difference
                layup.width = new_layup_width
            else:
                # MonoLayer uses height
                new_layup_height = layup.height + height_difference
                layup.height = new_layup_height
            self._reference_electrode_assembly.layup = self._reference_electrode_assembly.layup

        elif type(self._reference_electrode_assembly) == FlatWoundJellyRoll:
            # For flat wound jelly rolls, use the assembly's height setter
            # which internally adjusts layup.width and tape width
            _original_assembly_thickness = self._reference_electrode_assembly._thickness
            new_assembly_height = self._reference_electrode_assembly.height + height_difference
            self._reference_electrode_assembly.height = new_assembly_height
            _new_assembly_thickness = self._reference_electrode_assembly._thickness
            encapsulation_length_difference = (_new_assembly_thickness - _original_assembly_thickness) * self._n_electrode_assembly * M_TO_MM
            self._encapsulation.length += encapsulation_length_difference

        # update the encapsulation height or width depending on connector orientation
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            new_canister_height = self._encapsulation.height + height_difference
            self._encapsulation.height = new_canister_height
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            new_canister_width = self._encapsulation.width + height_difference
            self._encapsulation.width = new_canister_width

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

    @length.setter
    @calculate_all_properties
    def length(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "length")

        # get the length difference
        current_length = self.length
        length_difference = value - current_length
        length_difference_per_assembly = length_difference / self._n_electrode_assembly

        # record width values incase the width needs to be updated to maintain fit with flat wound jelly rolls
        if type(self._reference_electrode_assembly) == FlatWoundJellyRoll:
            assembly_width = self._reference_electrode_assembly.width

        # update the reference electrode assembly thickness
        new_thickness = self._reference_electrode_assembly.thickness + length_difference_per_assembly
        self._reference_electrode_assembly.thickness = new_thickness
        self._encapsulation.length = value
        self._reference_electrode_assembly = self._reference_electrode_assembly

        # if the reference electrode assembly is a flat wound jelly roll, also update the encapsulation width or height to maintain fit with the new assembly thickness
        if type(self._reference_electrode_assembly) == FlatWoundJellyRoll:
            new_assembly_width = self._reference_electrode_assembly.width
            width_difference = new_assembly_width - assembly_width
            if width_difference > 1e-4:
                self._encapsulation.height += width_difference

    @width.setter
    @calculate_all_properties
    def width(self, value: float) -> None:

        # validate input
        self.validate_positive_float(value, "width")

        # get the width difference
        current_width = self.width
        width_difference = value - current_width

        if isinstance(self._reference_electrode_assembly, _Stack):

            # update the reference electrode assembly width
            new_layup_width = self._reference_electrode_assembly.layup.width + width_difference
            self._reference_electrode_assembly.layup.width = new_layup_width
            self._reference_electrode_assembly.layup = self._reference_electrode_assembly.layup

        elif type(self._reference_electrode_assembly) == FlatWoundJellyRoll:
        
            _original_assembly_thickness = self._reference_electrode_assembly._thickness
            new_assembly_width = self._reference_electrode_assembly.width + width_difference
            self._reference_electrode_assembly.width = new_assembly_width
            _new_assembly_thickness = self._reference_electrode_assembly._thickness
            encapsulation_length_difference = (_new_assembly_thickness - _original_assembly_thickness) * self._n_electrode_assembly * M_TO_MM
            self._encapsulation.length += encapsulation_length_difference

        # update the encapsulation width or height depending on connector orientation
        if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
            new_canister_width = self._encapsulation.width + width_difference
            self._encapsulation.width = new_canister_width
        elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
            new_canister_height = self._encapsulation.height + width_difference
            self._encapsulation.height = new_canister_height

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

    def _sync_connector_orientation(self) -> None:
        """Synchronize encapsulation connector orientation with electrode assembly orientation.
        
        This method ensures the encapsulation's connector_orientation matches the
        electrode assembly's layup electrode_orientation. If they differ, it updates
        the connector_orientation and swaps the canister's height and width dimensions.
        """
        from steer_opencell_design.Constructions.Layups.MonoLayers import ElectrodeOrientation
        from steer_opencell_design.Components.Containers.Prismatic import ConnectorOrientation
        
        if not self._update_properties:
            return
            
        layup_orientation = self._reference_electrode_assembly._layup._electrode_orientation
        
        if layup_orientation == ElectrodeOrientation.LONGITUDINAL:
            if self._encapsulation._connector_orientation != ConnectorOrientation.LONGITUDINAL:
                self._encapsulation.connector_orientation = ConnectorOrientation.LONGITUDINAL
                # Swap height and width to match orientation change
                _original_height = self._encapsulation._canister._height
                _original_width = self._encapsulation._canister._width
                self._encapsulation._canister.height = _original_width * M_TO_MM
                self._encapsulation._canister.width = _original_height * M_TO_MM
                self._encapsulation.canister = self._encapsulation.canister
                
        elif layup_orientation == ElectrodeOrientation.TRANSVERSE:
            if self._encapsulation._connector_orientation != ConnectorOrientation.TRANSVERSE:
                self._encapsulation.connector_orientation = ConnectorOrientation.TRANSVERSE
                # Swap height and width to match orientation change
                _original_height = self._encapsulation._canister._height
                _original_width = self._encapsulation._canister._width
                self._encapsulation._canister.height = _original_width * M_TO_MM
                self._encapsulation._canister.width = _original_height * M_TO_MM
                self._encapsulation.canister = self._encapsulation.canister

    @reference_electrode_assembly.setter
    @calculate_all_properties
    @propagating_setter()
    def reference_electrode_assembly(self, value: ZFoldStack | PunchedStack | FlatWoundJellyRoll | WoundJellyRoll) -> None:
        """Set reference electrode assembly with validation.
        
        If a WoundJellyRoll is provided, the cell will be automatically converted
        to a CylindricalCell with an appropriately sized encapsulation.
        
        Parameters
        ----------
        value : ZFoldStack | PunchedStack | FlatWoundJellyRoll | WoundJellyRoll
            New electrode assembly to set. If WoundJellyRoll, cell converts to CylindricalCell.
        """
        self.validate_type(value, (ZFoldStack, PunchedStack, FlatWoundJellyRoll, WoundJellyRoll), "reference_electrode_assembly")
        
        # If WoundJellyRoll is provided, convert to CylindricalCell
        if isinstance(value, WoundJellyRoll):
            self._convert_to_cylindrical_cell(value)
            return
        
        self._reference_electrode_assembly = value

        # Ensure encapsulation connector orientation matches electrode orientation
        self._sync_connector_orientation()

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
        from steer_opencell_design.Components.Containers.Base import _Container
        from steer_opencell_design.Components.Containers.Pouch import PouchEncapsulation
        from steer_opencell_design.Components.Containers.Cylindrical import CylindricalEncapsulation
        
        # Only allow PrismaticEncapsulation or PouchEncapsulation
        self.validate_type(value, (PrismaticEncapsulation, PouchEncapsulation), "encapsulation")
        
        # Check if encapsulation type matches cell type
        if isinstance(value, PrismaticEncapsulation):
            # Same type, proceed normally
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
        else:
            # Different type, convert cell
            self._convert_to_cell_type(value)

    @n_electrode_assembly.setter
    @calculate_all_properties
    def n_electrode_assembly(self, value: int) -> None:

        # validate input
        value = int(np.round(value))
        
        if self._update_properties:

            # difference in number of assemblies
            assembly_difference = value - self._n_electrode_assembly

            # modify encapsulation length by the same amount to maintain fit
            new_length = self._encapsulation.length + assembly_difference * self._reference_electrode_assembly._thickness * M_TO_MM
            self._encapsulation.length = new_length

        # update the reference electrode assembly thickness by the same ratio to maintain fit
        self._n_electrode_assembly = value

    def fit_encapsulation_height_to_assemblies(self, clearance: float = 0) -> None:
        """Fit the encapsulation height to the electrode assemblies.
        
        Delegates to PrismaticEncapsulation.fit_height() using the first
        electrode assembly (which has clipped tabs).
        
        Parameters
        ----------
        clearance : float, optional
            Additional clearance in mm (default: 0)
        """
        self._encapsulation.fit_height(self.electrode_assemblies[0], clearance)
    
    def fit_encapsulation_width_to_assemblies(self, clearance: float = 0) -> None:
        """Fit the encapsulation width to the electrode assemblies.
        
        Delegates to PrismaticEncapsulation.fit_width() using the reference
        electrode assembly.
        
        Parameters
        ----------
        clearance : float, optional
            Additional clearance in mm (default: 0)
        """
        self._encapsulation.fit_width(self._reference_electrode_assembly, clearance)
    
    def fit_encapsulation_length_to_assemblies(self, clearance: float = 0) -> None:
        """Fit the encapsulation length to the electrode assemblies.
        
        Delegates to PrismaticEncapsulation.fit_length() using the reference
        electrode assembly and n_electrode_assembly.
        
        Parameters
        ----------
        clearance : float, optional
            Additional clearance in mm (default: 0)
        """
        self._encapsulation.fit_length(
            self._reference_electrode_assembly, 
            clearance, 
            n_electrode_assembly=self._n_electrode_assembly
        )

    def _convert_to_cylindrical_cell(self, wound_jelly_roll: WoundJellyRoll) -> None:
        """Convert this PrismaticCell to a CylindricalCell with the given WoundJellyRoll.
        
        Parameters
        ----------
        wound_jelly_roll : WoundJellyRoll
            The wound jelly roll to use as the reference electrode assembly
        """
        from steer_opencell_design.Components.Containers.Cylindrical import CylindricalEncapsulation
        from steer_opencell_design.Constructions.Cells.CylindricalCell import CylindricalCell
        
        # Convert encapsulation to CylindricalEncapsulation
        cylindrical_encapsulation = CylindricalEncapsulation.from_prismatic(self._encapsulation)
        
        # Fit the cylindrical container to the wound jelly roll
        cylindrical_encapsulation.fit_to_electrode_assembly(wound_jelly_roll)
        
        # Create new CylindricalCell with the wound jelly roll
        new_cell = CylindricalCell(
            reference_electrode_assembly=wound_jelly_roll,
            encapsulation=cylindrical_encapsulation,
            electrolyte=self._electrolyte,
            operating_voltage_window=self._operating_voltage_window,
            electrolyte_overfill=self._electrolyte_overfill,
            name=self._name,
        )
        
        # Copy all attributes from new cell to self (in-place conversion)
        self.__class__ = CylindricalCell
        self.__dict__.update(new_cell.__dict__)
        
        # Restore parent references so children point to self, not new_cell
        self._restore_child_parent_refs()

