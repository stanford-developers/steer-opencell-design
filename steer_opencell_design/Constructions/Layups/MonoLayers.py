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
    def __init__(
        self,
        cathode: Cathode,
        anode: Anode,
        separator: Separator,
        electrode_orientation: ElectrodeOrientation = ElectrodeOrientation.LONGITUDINAL,
        name: str = "MonoLayer",
    ):
        """
        Initialize the MonoLayer with the given components and offsets.

        Parameters
        ----------
        anode : Anode
            The anode component of the monolayer.
        cathode : Cathode
            The cathode component of the monolayer.
        separator : Separator
            The separator component of the monolayer.
        anode_offset : tuple
            The (x, y) offset for the anode in mm.
        bottom_separator_offset : float
            The (x, y) offset for the bottom separator in mm.
        top_separator_offset : float
            The (x, y) offset for the top separator in mm.
        electrode_orientation : ElectrodeOrientation
            The orientation of the electrode (default: ElectrodeOrientation.LONGITUDINAL).
        """
        # rotate the separator
        if separator._rotated_xy == False:
            separator._rotate_90_xy()

        # Store canonical separator for unified API
        self._canonical_separator = deepcopy(separator)

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

        # Ensure bottom and top separators are not rotated in xy-plane
        if not self._bottom_separator._rotated_xy:
            self._bottom_separator._rotate_90_xy()
        if not self._top_separator._rotated_xy:
            self._top_separator._rotate_90_xy()

        super()._calculate_all_properties()

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._top_separator._set_length_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_width_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_length_range(self._anode, extended_range=0.1)

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
        """
        bottom_separator = deepcopy(zfold_monolayer._bottom_separator)
        bottom_separator.width = zfold_monolayer.anode.current_collector.x_foil_length + 4
        bottom_separator.length = zfold_monolayer.anode.current_collector.y_foil_length + 4
        
        return cls(
            cathode=deepcopy(zfold_monolayer.cathode),
            anode=deepcopy(zfold_monolayer.anode),
            separator=bottom_separator,
            electrode_orientation=deepcopy(zfold_monolayer.electrode_orientation)
        )

    def _calculate_bulk_properties(self):
        self._calculate_height()
        self._calculate_width()

    def _calculate_height(self) -> float:
        """
        Calculate the height of the laminate based on the anode and cathode heights.

        Returns
        -------
        float
            The height of the laminate in meters.
        """
        anode_height = self._anode._current_collector._y_foil_length
        cathode_height = self._cathode._current_collector._y_foil_length

        # The laminate height is determined by the longer of the two electrodes
        monolayer_height = max(anode_height, cathode_height)

        self._height = monolayer_height

        return self._height

    def _calculate_width(self) -> float:
        """
        Calculate the width of the laminate based on the anode and cathode widths.

        Returns
        -------
        float
            The width of the laminate in meters.
        """
        anode_width = self._anode._current_collector._x_foil_length
        cathode_width = self._cathode._current_collector._x_foil_length

        # The laminate width is determined by the wider of the two electrodes
        monolayer_width = max(anode_width, cathode_width)

        self._width = monolayer_width

        return self._width
    
    @property
    def width(self) -> float:
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self) -> tuple:
        return self.cathode.current_collector.width_range
    
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

        # Validate input type
        self.validate_type(value, Separator, "Separator")

        # Deep copy into both
        base = deepcopy(value)
        top = deepcopy(value)

        # Preserve existing z positions if already initialized
        base.datum = (self._bottom_separator.datum[0], self._bottom_separator.datum[1], self._bottom_separator.datum[2])
        top.datum = (self._top_separator.datum[0], self._top_separator.datum[1], self._top_separator.datum[2])

        self._bottom_separator = base
        self._top_separator = top
        self._canonical_separator = deepcopy(value)

    @property
    def separator_overhangs(self) -> dict:

        return {
            "left": self.bottom_separator_overhang_left,
            "right": self.bottom_separator_overhang_right,
            "top": self.bottom_separator_overhang_top,
            "bottom": self.bottom_separator_overhang_bottom,
        }

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

        # Validate input
        self.validate_positive_float(value, "Laminate Width")
        
        # get the current width
        current_width = self.width

        # get the difference in the widths
        width_diff = value - current_width

        # Update the width property of the bottom separator
        self.bottom_separator.width = self.bottom_separator.width + width_diff
        self.bottom_separator = self.bottom_separator

        # Update the width property of the top separator
        self.top_separator.width = self.top_separator.width + width_diff 
        self.top_separator = self.top_separator

        # Update the width property of the anode
        self.anode.current_collector.width = self.anode.current_collector.width + width_diff
        self.anode.current_collector.tab_position = self.anode.current_collector.tab_position + width_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the width property of the cathode
        self.cathode.current_collector.width = self.cathode.current_collector.width + width_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode

    @height.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def height(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Height")
        
        # get the current height
        current_height = self.height

        # get the difference in the heights
        height_diff = value - current_height

        # Update the height property of the bottom separator
        self.bottom_separator.length = self.bottom_separator.length + height_diff
        self.bottom_separator = self.bottom_separator

        # Update the height property of the top separator
        self.top_separator.length = self.top_separator.length + height_diff
        self.top_separator = self.top_separator

        # Update the height property of the anode
        self.anode.current_collector.height = self.anode.current_collector.height + height_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the height property of the cathode
        self.cathode.current_collector.height = self.cathode.current_collector.height + height_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode


class ZFoldMonoLayer(MonoLayer):
    """Z-fold variant of `MonoLayer` with constrained separator geometry.

    Differences from `MonoLayer`:
    - Canonical separator is NOT rotated; keep original orientation.
    - Bottom separator length = cathode current collector width + 2 * canonical thickness.
    - Top separator length = anode current collector width + 2 * canonical thickness.
    - Unified separator API identical to `MonoLayer` (use `separator` property).
    - Overhang setters behave the same; left/right still adjustable if needed.
    """

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
        )

        # Electrode orientation behavior same as MonoLayer
        self.electrode_orientation = electrode_orientation
        self._update_properties = True
        self._calculate_all_properties()

    def _calculate_all_properties(self):

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

        # Ensure bottom and top separators are not rotated in xy-plane
        if self._bottom_separator._rotated_xy:
            self._bottom_separator._rotate_90_xy()
        if self._top_separator._rotated_xy:
            self._top_separator._rotate_90_xy()

        super(MonoLayer, self)._calculate_all_properties()

        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._bottom_separator._set_width_range(self._anode, extended_range=0.1)

        self._calculate_bulk_properties()
        self._constrain_separator_geometry()

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
    def width(self) -> float:
        return np.round(self._width * M_TO_MM, 2)

    @property
    def height(self) -> float:
        return np.round(self._height * M_TO_MM, 2)

    @property
    def separator(self) -> Separator:
        return self._bottom_separator

    @separator.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def separator(self, value: Separator):

        # Validate input type
        self.validate_type(value, Separator, "Separator")
        
        # Set canonical separator
        self._canonical_separator = deepcopy(value)

        # Deep copy into both top and bottom
        bottom = deepcopy(value)
        top = deepcopy(value)

        bottom.datum = (
            self._bottom_separator.datum[0],
            self._bottom_separator.datum[1],
            bottom.datum[2],
        )

        top.datum = (
            self._top_separator.datum[0],
            self._top_separator.datum[1],
            top.datum[2],
        )

        self._bottom_separator = bottom
        self._top_separator = top

        self._constrain_separator_geometry()

    @classmethod
    def from_monolayer(cls, monolayer: MonoLayer) -> "ZFoldMonoLayer":

        return cls(
            cathode=deepcopy(monolayer.cathode),
            anode=deepcopy(monolayer.anode),
            separator=deepcopy(monolayer.separator),
            electrode_orientation=monolayer.electrode_orientation,
        )

    @width.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def width(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Width")
        
        # get the current width
        current_width = self.width

        # get the difference in the widths
        width_diff = value - current_width

        # Update the width property of the anode
        self.anode.current_collector.width = self.anode.current_collector.width + width_diff
        self.anode.current_collector.tab_position = self.anode.current_collector.tab_position + width_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the width property of the cathode
        self.cathode.current_collector.width = self.cathode.current_collector.width + width_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode

    @height.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def height(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Height")
        
        # get the current height
        current_height = self.height

        # get the difference in the heights
        height_diff = value - current_height

        # Update the height property of the bottom separator
        self.bottom_separator.width = self.bottom_separator.width + height_diff
        self.bottom_separator = self.bottom_separator

        # Update the height property of the top separator
        self.top_separator.width = self.top_separator.width + height_diff
        self.top_separator = self.top_separator

        # Update the height property of the anode
        self.anode.current_collector.height = self.anode.current_collector.height + height_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the height property of the cathode
        self.cathode.current_collector.height = self.cathode.current_collector.height + height_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode


