# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Single-separator layup configurations for stacked electrode assemblies."""

from copy import copy, deepcopy
from enum import Enum
import numpy as np

from steer_core.Constants.Units import *
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import calculate_bulk_properties

from steer_opencell_design.Components.CurrentCollectors.Punched import PunchedCurrentCollector
from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups.Base import _Layup, ElectrodeOrientation


class MonoLayer(_Layup):
    """
    Class for a MonoLayer, which is a combination of anode, cathode, and separator. This class represents the
    item which will be repeated in space to form a z-fold stack.
    """
    
    # Class-level behavioral attributes for separator handling
    _sync_separator_length: bool = True  # Whether to sync length from canonical separator
    _require_rotated_separator: bool = True  # Whether separators should be rotated (90° in xy-plane)

    # _canonical_separator is stored internally but exposed via the 'separator' property
    _propagation_attr_map = {"_canonical_separator": "separator"}

    def __init__(
        self,
        cathode: Cathode,
        anode: Anode,
        separator: Separator,
        electrode_orientation: ElectrodeOrientation = ElectrodeOrientation.LONGITUDINAL,
        name: str = "MonoLayer",
    ):
        """
        Initialize the MonoLayer with the given components.

        Parameters
        ----------
        cathode : Cathode
            The cathode component of the monolayer.
        anode : Anode
            The anode component of the monolayer.
        separator : Separator
            The separator component of the monolayer.
        electrode_orientation : ElectrodeOrientation
            The orientation of the electrode (default: ElectrodeOrientation.LONGITUDINAL).
        name : str, optional
            Name of the monolayer (default: "MonoLayer").
        """
        # rotate the separator
        if separator._rotated_xy == False:
            separator._rotate_90_xy()

        # Store canonical separator for unified API
        self._canonical_separator = deepcopy(separator)

        # Set parent reference for propagation
        if hasattr(self._canonical_separator, '_set_parent'):
            self._canonical_separator._set_parent(self, "separator")

        # call the general layup init
        super().__init__(
            cathode=cathode,
            bottom_separator=deepcopy(separator),
            anode=anode,
            top_separator=deepcopy(separator),
            electrode_orientation=electrode_orientation,
            name=name,
        )

        # Add MonoLayer-specific components and properties

        # Recalculate properties now that separator is set
        self._calculate_all_properties()
        self._update_properties = True

        # set voltage operating limits
        self._minimum_operating_voltage = min(self._minimum_operating_voltage_range)
        self._maximum_operating_voltage = max(self._maximum_operating_voltage_range)

    def _calculate_all_properties(self):

        self._validate_punched_current_collectors()

        # Sync canonical separator properties to internal separators
        self._sync_separator_from_canonical()

        # Ensure separators have the required rotation state
        self._ensure_separator_rotation()

        super()._calculate_all_properties()

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._top_separator._set_length_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_width_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_length_range(self._anode, extended_range=0.1)

        # Set canonical separator ranges based on anode current collector dimensions
        # For rotated separator: width -> x_foil_length, length -> y_foil_length
        _x_foil_length = self._anode._current_collector._x_foil_length
        _y_foil_length = self._anode._current_collector._y_foil_length
        self._canonical_separator._width_range = (_x_foil_length, _x_foil_length * 1.2)
        self._canonical_separator._length_range = (_y_foil_length, _y_foil_length * 1.2)

    def _validate_punched_current_collectors(self):
        """Validate that both anode and cathode use PunchedCurrentCollector."""
        self.validate_type(
            self.anode.current_collector,
            PunchedCurrentCollector,
            "Anode Current Collector",
        )
        self.validate_type(
            self.cathode.current_collector,
            PunchedCurrentCollector,
            "Cathode Current Collector",
        )

    def _ensure_separator_rotation(self):
        """Ensure separators have the required rotation state based on `_require_rotated_separator`."""
        for sep in [self._bottom_separator, self._top_separator]:
            if sep is None:
                continue
            # Rotate if current state doesn't match required state
            if sep._rotated_xy != self._require_rotated_separator:
                sep._rotate_90_xy()

    def _update_electrode_dimensions(self, width_diff: float = 0, height_diff: float = 0, update_tab_position: bool = True):
        """Propagate dimension changes to anode and cathode current collectors.
        
        Parameters
        ----------
        width_diff : float
            Change in width to apply (in mm)
        height_diff : float  
            Change in height to apply (in mm)
        update_tab_position : bool
            Whether to also update tab position (only for width changes)
        """
        for electrode_attr in ['anode', 'cathode']:
            electrode = getattr(self, electrode_attr)
            cc = electrode.current_collector
            if width_diff:
                cc.width = cc.width + width_diff
                if update_tab_position:
                    cc.tab_position = cc.tab_position + width_diff
            if height_diff:
                cc.height = cc.height + height_diff
            electrode.current_collector = cc
            setattr(self, electrode_attr, electrode)

    def _update_separator_dimensions(self, width_diff: float = 0, length_diff: float = 0, include_canonical: bool = True):
        """Propagate dimension changes to separators.
        
        Parameters
        ----------
        width_diff : float
            Change in separator width to apply (in mm)
        length_diff : float
            Change in separator length to apply (in mm)
        include_canonical : bool
            Whether to also update the canonical separator
        """
        separators = [self._bottom_separator, self._top_separator]
        if include_canonical and hasattr(self, '_canonical_separator'):
            separators.append(self._canonical_separator)
        for sep in separators:
            if sep is None:
                continue
            if width_diff:
                sep.width = sep.width + width_diff
            if length_diff:
                sep.length = sep.length + length_diff

    def _sync_separator_from_canonical(self):
        """Sync separator properties from canonical separator to internal top/bottom separators.
        
        This method propagates changes made to the unified separator API to both
        internal separator instances, while preserving their individual z-positions.
        
        Note: Length syncing is controlled by the `_sync_separator_length` class attribute.
        ZFoldMonoLayer sets this to False since its separator lengths are constrained by electrode geometry.
        """
        if not hasattr(self, '_canonical_separator') or self._canonical_separator is None:
            return
            
        # Properties to sync from canonical to internal separators
        # Note: we preserve z-datum and rotation state
        for sep in [self._bottom_separator, self._top_separator]:
            if sep is None:
                continue
            # Sync dimensions (stored in internal units - meters)
            sep._width = self._canonical_separator._width
            if self._sync_separator_length:
                sep._length = self._canonical_separator._length
            sep._thickness = self._canonical_separator._thickness
            # Sync material
            sep._material = deepcopy(self._canonical_separator._material)
            # Recalculate separator properties with new values
            sep._calculate_bulk_properties()
            sep._calculate_coordinates()

    @classmethod
    def from_zfold_monolayer(cls, zfold_monolayer: "ZFoldMonoLayer") -> "MonoLayer":
        """
        Create a MonoLayer instance from a ZFoldMonoLayer instance.

        Parameters
        ----------
        zfold_monolayer : ZFoldMonoLayer
            The ZFoldMonoLayer instance to convert.

        Returns
        -------
        MonoLayer
            A new MonoLayer instance with the same properties as the input ZFoldMonoLayer.
            
        Notes
        -----
        ZFoldMonoLayer uses non-rotated separators (_rotated_xy=False) where width -> y-direction.
        MonoLayer uses rotated separators (_rotated_xy=True) where width -> x-direction.
        This method swaps width and length values and rotates to match MonoLayer's coordinate system.
        """
        separator = deepcopy(zfold_monolayer._canonical_separator)
        
        # ZFoldMonoLayer's canonical separator is non-rotated: width -> y-direction, length -> x-direction
        # MonoLayer expects rotated separator: width -> x-direction, length -> y-direction
        # Swap the values so after MonoLayer rotates the separator, dimensions are correct
        if not separator._rotated_xy:
            # Swap the values (in internal units - meters)
            old_width = separator._width
            old_length = separator._length
            separator._width = old_length  # old length (x-dir) becomes new width (x-dir after rotation)
            separator._length = old_width  # old width (y-dir) becomes new length (y-dir after rotation)
            # Recalculate coordinates with new dimensions
            separator._calculate_coordinates()
        
        # Set appropriate dimensions based on electrode geometry
        # MonoLayer's __init__ will rotate this separator, so set dimensions accordingly
        # width (will become x-dir after rotation) = x_foil_length + overhang
        # length (will become y-dir after rotation) = y_foil_length + overhang
        separator.width = zfold_monolayer.anode.current_collector.x_foil_length + 4
        separator.length = zfold_monolayer.anode.current_collector.y_foil_length + 4
        
        return cls(
            cathode=deepcopy(zfold_monolayer.cathode),
            anode=deepcopy(zfold_monolayer.anode),
            separator=separator,
            electrode_orientation=deepcopy(zfold_monolayer.electrode_orientation)
        )

    def _calculate_bulk_properties(self):
        self._calculate_height()
        self._calculate_width()

    def _calculate_height(self) -> float:
        """
        Calculate the height of the monolayer based on the anode, cathode, and separator heights.

        Returns
        -------
        float
            The height of the monolayer in meters.
        """
        anode_height = self._anode._current_collector._y_foil_length
        cathode_height = self._cathode._current_collector._y_foil_length

        # Get separator height contribution, accounting for rotation
        # If rotated: separator's length contributes to layup height
        # If not rotated: separator's width contributes to layup height
        if self._bottom_separator._rotated_xy:
            separator_height = max(self._bottom_separator._length, self._top_separator._length)
        else:
            separator_height = max(self._bottom_separator._width, self._top_separator._width)

        # The laminate height is determined by the longest of electrodes and separator
        monolayer_height = max(anode_height, cathode_height, separator_height)

        self._height = monolayer_height

        return self._height

    def _calculate_width(self) -> float:
        """
        Calculate the width of the monolayer based on the anode, cathode, and separator widths.

        Returns
        -------
        float
            The width of the monolayer in meters.
        """
        anode_width = self._anode._current_collector._x_foil_length
        cathode_width = self._cathode._current_collector._x_foil_length

        # Get separator width contribution, accounting for rotation
        # If rotated: separator's width contributes to layup width
        # If not rotated: separator's length contributes to layup width
        if self._bottom_separator._rotated_xy:
            separator_width = max(self._bottom_separator._width, self._top_separator._width)
        else:
            separator_width = max(self._bottom_separator._length, self._top_separator._length)

        # The laminate width is determined by the widest of electrodes and separator
        monolayer_width = max(anode_width, cathode_width, separator_width)

        self._width = monolayer_width

        return self._width
    
    @property
    def width(self) -> float:
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self) -> tuple:
        _anode_tab_width = self.anode.current_collector._tab_width
        _cathode_tab_width = self.cathode.current_collector._tab_width
        _max_tab_width = max(_anode_tab_width, _cathode_tab_width)
        _min_width = _max_tab_width * 1.2
        return (
            np.round(_min_width, 2),
            self.cathode.current_collector.width_range[1],
        )
    
    @property
    def width_hard_range(self) -> tuple:
        return self.cathode.current_collector.width_hard_range

    @property
    def height(self) -> float:
        return np.round(self._height * M_TO_MM, 2)

    @property
    def height_range(self) -> tuple:
        return self.cathode.current_collector.height_range

    @property
    def height_hard_range(self) -> tuple:
        return self.cathode.current_collector.height_hard_range

    # === Unified separator API ===

    @property
    def separator(self) -> Separator:
        """Unified separator interface (canonical); setting updates both top and bottom separators.

        Returns the canonical separator (bottom instance for consistency).
        """
        return self._canonical_separator

    @separator.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def separator(self, value: Separator):
        self._set_separator_common(value)

    def _set_separator_common(self, value: Separator):
        """Common logic for setting the separator on both MonoLayer and ZFoldMonoLayer.
        
        Handles validation, parent reference management, deep copying, datum preservation,
        and parent reference setup. Subclasses can call this and add additional behavior.
        """
        # Validate input type
        self.validate_type(value, Separator, "Separator")

        # Clear old parent references (only if different objects)
        for attr in ['_bottom_separator', '_top_separator', '_canonical_separator']:
            sep = getattr(self, attr, None)
            if sep is not None and sep is not value:
                sep._set_parent(None)

        # Deep copy into both separators, preserving existing z positions
        bottom_datum = self._bottom_separator.datum
        top_datum = self._top_separator.datum

        self._bottom_separator = deepcopy(value)
        self._top_separator = deepcopy(value)
        self._canonical_separator = deepcopy(value)

        self._bottom_separator.datum = bottom_datum
        self._top_separator.datum = top_datum

        # Set new parent references for propagation
        self._bottom_separator._set_parent(self, "bottom_separator")
        self._top_separator._set_parent(self, "top_separator")
        self._canonical_separator._set_parent(self, "separator")

    @property
    def separator_overhangs(self) -> dict:
        return {direction: getattr(self, f"separator_overhang_{direction}") for direction in ['left', 'right', 'top', 'bottom']}

    @property
    def separator_overhang_left(self) -> float:
        return self.bottom_separator_overhang_left

    @property
    def separator_overhang_left_range(self) -> tuple:
        return self.bottom_separator_overhang_left_range

    @separator_overhang_left.setter
    def separator_overhang_left(self, overhang: float) -> None:
        self.bottom_separator_overhang_left = overhang
        self.top_separator_overhang_left = overhang

    @property
    def separator_overhang_right(self) -> float:
        return self.bottom_separator_overhang_right

    @property
    def separator_overhang_right_range(self) -> tuple:
        return self.bottom_separator_overhang_right_range

    @separator_overhang_right.setter
    def separator_overhang_right(self, overhang: float) -> None:
        self.bottom_separator_overhang_right = overhang
        self.top_separator_overhang_right = overhang

    @property
    def separator_overhang_top(self) -> float:
        return self.bottom_separator_overhang_top

    @property
    def separator_overhang_top_range(self) -> tuple:
        return self.bottom_separator_overhang_top_range

    @separator_overhang_top.setter
    def separator_overhang_top(self, overhang: float) -> None:
        self.bottom_separator_overhang_top = overhang
        self.top_separator_overhang_top = overhang

    @property
    def separator_overhang_bottom(self) -> float:
        return self.bottom_separator_overhang_bottom

    @property
    def separator_overhang_bottom_range(self) -> tuple:
        return self.bottom_separator_overhang_bottom_range

    @separator_overhang_bottom.setter
    def separator_overhang_bottom(self, overhang: float) -> None:
        self.bottom_separator_overhang_bottom = overhang
        self.top_separator_overhang_bottom = overhang

    @width.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def width(self, value: float):
        self.validate_positive_float(value, "Laminate Width")
        width_diff = value - self.width
        self._update_separator_dimensions(width_diff=width_diff)
        self._update_electrode_dimensions(width_diff=width_diff)

    @height.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def height(self, value: float):
        self.validate_positive_float(value, "Laminate Height")
        height_diff = value - self.height
        self._update_separator_dimensions(length_diff=height_diff)
        self._update_electrode_dimensions(height_diff=height_diff, update_tab_position=False)


class ZFoldMonoLayer(MonoLayer):
    """Z-fold variant of `MonoLayer` with constrained separator geometry.

    Differences from `MonoLayer`:
    - Canonical separator is NOT rotated; keep original orientation.
    - Bottom separator length = cathode current collector width + 2 * canonical thickness.
    - Top separator length = anode current collector width + 2 * canonical thickness.
    - Unified separator API identical to `MonoLayer` (use `separator` property).
    - Overhang setters behave the same; left/right still adjustable if needed.
    """
    
    # Override behavioral attributes for Z-fold separator handling
    _sync_separator_length: bool = False  # Don't sync length - it's constrained by electrode geometry
    _require_rotated_separator: bool = False  # Z-fold uses non-rotated separators

    def __init__(
        self,
        cathode: Cathode,
        anode: Anode,
        separator: Separator,
        electrode_orientation: ElectrodeOrientation = ElectrodeOrientation.LONGITUDINAL,
        name: str = "ZFoldMonoLayer",
    ):
        
        # Store canonical (do NOT rotate for Z-fold)
        self._canonical_separator = deepcopy(separator)
        # Set parent reference for propagation
        if hasattr(self._canonical_separator, '_set_parent'):
            self._canonical_separator._set_parent(self, "separator")

        # Create specialized separator copies (no rotation enforced)
        bottom_separator = deepcopy(separator)
        top_separator = deepcopy(separator)

        # Set lengths using electrode WIDTHs (x_foil_length) + 2*thickness
        bottom_separator.length = (
            (cathode.current_collector._x_foil_length + 2 * self._canonical_separator._thickness) * M_TO_MM
        )

        top_separator.length = (
            (anode.current_collector._x_foil_length + 2 * self._canonical_separator._thickness) * M_TO_MM
        )

        # Call base _Layup initializer directly (skip MonoLayer rotation logic)
        super(MonoLayer, self).__init__(
            cathode=cathode,
            bottom_separator=bottom_separator,
            anode=anode,
            top_separator=top_separator,
            name=name,
            electrode_orientation=electrode_orientation,
        )

        # Electrode orientation behavior same as MonoLayer
        self.electrode_orientation = electrode_orientation
        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):

        self._validate_punched_current_collectors()

        # Sync canonical separator properties to internal separators (length handled via class attribute)
        self._sync_separator_from_canonical()

        # Ensure separators have the required rotation state
        self._ensure_separator_rotation()

        super(MonoLayer, self)._calculate_all_properties()

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_width_range(self._anode, extended_range=0.1)

        self._calculate_bulk_properties()
        self._constrain_separator_geometry()
        
        # Ensure canonical separator has valid length for external use
        # Use bottom separator's length as reference since it's tied to cathode geometry
        if hasattr(self, '_canonical_separator') and self._canonical_separator is not None:
            self._canonical_separator._length = self._bottom_separator._length
            self._canonical_separator._calculate_coordinates()
            
            # Set canonical separator width range based on anode current collector dimensions
            # For non-rotated separator: width -> y_foil_length
            _y_foil_length = self._anode._current_collector._y_foil_length
            self._canonical_separator._width_range = (_y_foil_length, _y_foil_length * 1.2)

    def _constrain_separator_geometry(self):
        """Enforce Z-fold separator geometry constraints."""
        # Bottom separator length
        self._bottom_separator.length = (
            (self.cathode.current_collector._x_foil_length + 2 * self._canonical_separator._thickness) * M_TO_MM
        )

        # Top separator length
        self._top_separator.length = (
            (self.anode.current_collector._x_foil_length + 2 * self._canonical_separator._thickness) * M_TO_MM
        )

    @property
    def separator(self) -> Separator:
        """Unified separator interface (canonical); setting updates both top and bottom separators."""
        return self._canonical_separator

    @separator.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def separator(self, value: Separator):
        self._set_separator_common(value)
        self._constrain_separator_geometry()

    @classmethod
    def from_monolayer(cls, monolayer: MonoLayer) -> "ZFoldMonoLayer":
        """Create a ZFoldMonoLayer instance from a MonoLayer instance.
        
        Parameters
        ----------
        monolayer : MonoLayer
            The MonoLayer instance to convert.
            
        Returns
        -------
        ZFoldMonoLayer
            A new ZFoldMonoLayer instance with the same properties as the input MonoLayer.
            
        Notes
        -----
        MonoLayer uses rotated separators (_rotated_xy=True) where width -> x-direction.
        ZFoldMonoLayer uses non-rotated separators (_rotated_xy=False) where width -> y-direction.
        This method swaps width and length values when the source separator is rotated
        to preserve the physical dimensions correctly.
        """
        separator = deepcopy(monolayer.separator)
        
        # If source separator is rotated, swap width/length to match ZFold's non-rotated coordinate system
        # MonoLayer rotated: width -> x-direction, length -> y-direction
        # ZFoldMonoLayer non-rotated: length -> x-direction, width -> y-direction
        if separator._rotated_xy:
            # Swap the values (in internal units - meters)
            old_width = separator._width
            old_length = separator._length
            separator._width = old_length
            separator._length = old_width
            # Reset rotation flag since ZFoldMonoLayer expects non-rotated
            separator._rotated_xy = False
            # Recalculate coordinates with new dimensions
            separator._calculate_coordinates()
        
        return cls(
            cathode=deepcopy(monolayer.cathode),
            anode=deepcopy(monolayer.anode),
            separator=separator,
            electrode_orientation=monolayer.electrode_orientation,
        )

    @MonoLayer.width.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def width(self, value: float):
        self.validate_positive_float(value, "Laminate Width")
        width_diff = value - self.width
        # ZFold: separators have constrained length, don't update them for width changes
        self._update_electrode_dimensions(width_diff=width_diff)

    @MonoLayer.height.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def height(self, value: float):
        self.validate_positive_float(value, "Laminate Height")
        height_diff = value - self.height
        # ZFold non-rotated: height maps to separator width (not length)
        self._update_separator_dimensions(width_diff=height_diff)
        self._update_electrode_dimensions(height_diff=height_diff, update_tab_position=False)


