# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Prismatic battery cell implementation."""

from steer_opencell_design.Components.Containers.Prismatic import PrismaticEncapsulation, ConnectorOrientation
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import FlatWoundJellyRoll, WoundJellyRoll
from steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack, _Stack
from steer_opencell_design.Materials.Electrolytes import Electrolyte
from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Utils.Ranges import shifted_range

from steer_core.Decorators.General import calculate_all_properties, recalculate
from steer_core.Mixins.Propagation import propagating_setter
from steer_core.Constants.Units import *

from typing import Optional, Tuple
import plotly.graph_objects as go
import numpy as np


class PrismaticCell(_Cell):
    """Prismatic hard-case battery cell. Supports both stacked and flat-wound jelly roll internal constructions with a rigid metal canister."""

    _outline_shape = "box"

    @property
    def outline_dimensions(self) -> Optional[Tuple[float, float, float]]:
        """Outer ``(width, height, length)`` in mm: the thickness is the length."""
        try:
            return (float(self.width), float(self.height), float(self.length))
        except (AttributeError, TypeError, ValueError):
            return None

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

    def plot_top_down_view(self, opacity = 0.3, **kwargs) -> go.Figure:
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
        layup_traces = first_assembly.plot_top_down_view(opacity=opacity).data
        traces.extend(layup_traces)

        encapsulation_traces = self._encapsulation.plot_top_down_view(opacity=opacity).data
        
        # Apply opacity only to encapsulation traces
        for trace in encapsulation_traces:
            self.adjust_trace_opacity(trace, opacity)
        
        traces.extend(encapsulation_traces)

        figure.add_traces(traces)

        return self.apply_plot_layout(
            figure,
            defaults={
                "xaxis": self.SCHEMATIC_X_AXIS,
                "yaxis": self.SCHEMATIC_Y_AXIS,
                "paper_bgcolor": "white",
                "plot_bgcolor": "white",
            },
            overrides=kwargs,
        )

    def plot_side_view(self, **kwargs) -> go.Figure:
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
            assembly_traces = assembly.plot_side_view().data
            # Only show legend for first assembly
            if i > 0:
                for trace in assembly_traces:
                    trace.showlegend = False
            traces.extend(assembly_traces)

        encapsulation_traces = self.encapsulation.plot_right_left_view().data
        traces.extend(encapsulation_traces)

        figure.add_traces(traces)

        return self.apply_plot_layout(
            figure,
            defaults={
                "xaxis": self.SCHEMATIC_Y_AXIS,
                "yaxis": self.SCHEMATIC_Z_AXIS,
                "paper_bgcolor": "white",
                "plot_bgcolor": "white",
            },
            overrides=kwargs,
        )

    # ---- outer dimensions -------------------------------------------------
    # Each cell dimension has an assembly part and an encapsulation part, and its
    # setter moves both by the same amount. Width (x) and height (y) are the
    # encapsulation's own width / height in either connector orientation (the
    # encapsulation maps them onto its canister) and the assembly's extent along
    # the same axis; length (z) is the encapsulation's length and the assemblies'
    # total thickness. The ranges are where both parts can follow (shifted_range).

    def _assembly_extent(self, dimension: str) -> float:
        """The assemblies' extent (mm) along a cell dimension."""
        assembly = self._reference_electrode_assembly
        if dimension == "length":
            return assembly.thickness * self._n_electrode_assembly
        if isinstance(assembly, _Stack):
            return getattr(assembly.layup, dimension)
        return getattr(assembly, dimension)  # a flat-wound roll's own width / height

    def _assembly_extent_range(self, dimension: str, hard: bool) -> Tuple[float, float]:
        suffix = "_hard_range" if hard else "_range"
        assembly = self._reference_electrode_assembly
        if dimension == "length":
            low, high = getattr(assembly, "thickness" + suffix)
            return (low * self._n_electrode_assembly, high * self._n_electrode_assembly)
        owner = assembly.layup if isinstance(assembly, _Stack) else assembly
        return getattr(owner, dimension + suffix)

    def _cell_dimension(self, dimension: str) -> float:
        return max(self._assembly_extent(dimension), getattr(self._encapsulation, dimension))

    def _cell_dimension_range(self, dimension: str, hard: bool) -> Tuple[float, float]:
        encapsulation = self._encapsulation
        enclosure_range = getattr(encapsulation, dimension + ("_hard_range" if hard else "_range"), None)
        if enclosure_range is None:
            enclosure_range = getattr(encapsulation, dimension + "_range")
        return shifted_range(
            self._cell_dimension(dimension),
            [
                (self._assembly_extent(dimension), self._assembly_extent_range(dimension, hard)),
                (getattr(encapsulation, dimension), enclosure_range),
            ],
        )

    def _move_cell_dimension(self, dimension: str, delta: float) -> None:
        """Move the assembly and the encapsulation by ``delta`` (mm) along a cell
        dimension. A flat-wound roll's extents are coupled (its width follows its
        thickness), so the encapsulation also follows the roll along any other
        axis it moved, keeping its gaps."""
        assembly = self._reference_electrode_assembly
        before = {d: self._assembly_extent(d) for d in ("width", "height", "length")}
        if dimension == "length":
            assembly.thickness = assembly.thickness + delta / self._n_electrode_assembly
        elif isinstance(assembly, _Stack):
            layup = assembly.layup
            setattr(layup, dimension, getattr(layup, dimension) + delta)
            assembly.layup = layup
        else:
            setattr(assembly, dimension, getattr(assembly, dimension) + delta)
        self._reference_electrode_assembly = assembly

        encapsulation = self._encapsulation
        setattr(encapsulation, dimension, getattr(encapsulation, dimension) + delta)
        for other in ("width", "height", "length"):
            if other == dimension:
                continue
            moved = self._assembly_extent(other) - before[other]
            if abs(moved) > 1e-9:
                setattr(encapsulation, other, getattr(encapsulation, other) + moved)

    @property
    def length(self) -> float:
        """Get the cell length (depth) in mm."""
        return self._cell_dimension("length")

    @property
    def length_range(self) -> Tuple[float, float]:
        """The cell lengths (mm) the length setter can reach."""
        return self._cell_dimension_range("length", hard=False)

    @property
    def length_hard_range(self) -> Tuple[float, float]:
        return self._cell_dimension_range("length", hard=True)

    @property
    def width(self) -> float:
        """Get the cell width in mm."""
        return self._cell_dimension("width")

    @property
    def width_range(self) -> Tuple[float, float]:
        """The cell widths (mm) the width setter can reach."""
        return self._cell_dimension_range("width", hard=False)

    @property
    def width_hard_range(self) -> Tuple[float, float]:
        return self._cell_dimension_range("width", hard=True)

    @property
    def n_electrode_assembly(self) -> int:
        """Get the number of electrode assemblies in the cell."""
        return self._n_electrode_assembly

    @property
    def height(self) -> float:
        """Get the cell height in mm."""
        return self._cell_dimension("height")

    @property
    def height_range(self) -> Tuple[float, float]:
        """The cell heights (mm) the height setter can reach."""
        return self._cell_dimension_range("height", hard=False)

    @property
    def height_hard_range(self) -> Tuple[float, float]:
        return self._cell_dimension_range("height", hard=True)

    @height.setter
    @calculate_all_properties
    def height(self, value: float) -> None:
        """Set the cell height (mm): the assembly and the encapsulation move by the
        same amount (see ``_move_cell_dimension``)."""
        self.validate_positive_float(value, "height")
        self._move_cell_dimension("height", value - self.height)

    @property
    def clipped_tab_length(self) -> float:
        """Get clipped tab length."""
        clipped = self._effective_clipped_tab_length()
        return None if clipped is None else clipped * M_TO_MM
    
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
        """Set the cell length (mm): each assembly's thickness and the
        encapsulation move together (see ``_move_cell_dimension``)."""
        self.validate_positive_float(value, "length")
        self._move_cell_dimension("length", value - self.length)

    @width.setter
    @calculate_all_properties
    def width(self, value: float) -> None:
        """Set the cell width (mm): the assembly and the encapsulation move by the
        same amount (see ``_move_cell_dimension``)."""
        self.validate_positive_float(value, "width")
        self._move_cell_dimension("width", value - self.width)

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
                # Go through the public setter, not the private attribute: only
                # the setter flips the anode in y, which is what actually puts
                # the two tabs on the same or opposite edges. Writing the enum
                # alone leaves the orientation and the geometry disagreeing.
                layup = self._reference_electrode_assembly._layup
                if self._encapsulation._connector_orientation == ConnectorOrientation.LONGITUDINAL:
                    if layup._electrode_orientation != ElectrodeOrientation.LONGITUDINAL:
                        layup.electrode_orientation = ElectrodeOrientation.LONGITUDINAL
                elif self._encapsulation._connector_orientation == ConnectorOrientation.TRANSVERSE:
                    if layup._electrode_orientation != ElectrodeOrientation.TRANSVERSE:
                        layup.electrode_orientation = ElectrodeOrientation.TRANSVERSE
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

