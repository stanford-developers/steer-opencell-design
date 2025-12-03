from copy import copy, deepcopy
from enum import Enum
from typing import Tuple
import numpy as np

from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator

from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import calculate_bulk_properties

from steer_core.Constants.Units import *

# Module-level constants for overhang ranges and plotting parameters
OVERHANG_MIN = 0.0  # Minimum overhang value in mm
OVERHANG_MAX_DEFAULT = 20.0  # Maximum overhang for non-Laminate classes in mm
OVERHANG_MAX_LAMINATE = 500.0  # Maximum overhang for Laminate class in mm

class OverhangControlMode(Enum):
    """Control modes for anode overhang adjustments."""
    FIXED_COMPONENT = "fixed_component"
    FIXED_OVERHANGS = "fixed_overhangs"


class OverhangMixin:

    def __init__(
            self,
        ):

        self.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

    def _calculate_coordinates(self):
        self._calculate_anode_overhangs()
        self._calculate_bottom_separator_overhangs()
        self._calculate_top_separator_overhangs()

    def _calculate_anode_overhangs(self):
        """Calculate anode overhangs relative to cathode.

        Overhang sign convention:
          left  = cathode_left - anode_left
          right = anode_right - cathode_right
          bottom= cathode_bottom - anode_bottom
          top   = anode_top - cathode_top

        Positive values mean the anode extends beyond the cathode in that direction.
        Values stored in internal SI units (meters).
        """
        left, right, bottom, top = self._compute_electrode_overhangs(self._cathode, self._anode)

        self._anode_overhang_left = left
        self._anode_overhang_right = right
        self._anode_overhang_bottom = bottom
        self._anode_overhang_top = top

    
    def _calculate_bottom_separator_overhangs(self):
        """Calculate bottom separator overhangs relative to cathode.

        Positive values mean the separator extends beyond the cathode in the given direction.
        """
        left, right, bottom, top = self._compute_separator_overhangs(self._cathode, self._bottom_separator)

        self._bottom_separator_overhang_left = left
        self._bottom_separator_overhang_right = right
        self._bottom_separator_overhang_bottom = bottom
        self._bottom_separator_overhang_top = top

    def _calculate_top_separator_overhangs(self):
        """Calculate top separator overhangs relative to cathode.

        Positive values mean the separator extends beyond the cathode in the given direction.
        """
        left, right, bottom, top = self._compute_separator_overhangs(self._cathode, self._top_separator)
        self._top_separator_overhang_left = left
        self._top_separator_overhang_right = right
        self._top_separator_overhang_bottom = bottom
        self._top_separator_overhang_top = top

    def _compute_electrode_overhangs(self, ref_electrode: Cathode, target_electrode: Anode) -> Tuple[float, float, float, float]:
        """Return (left, right, bottom, top) overhangs for rectangular current collectors.

        A positive component means target extends beyond reference in that direction.
        """
        # Reference edges
        ref_left = ref_electrode._current_collector._datum[0] - ref_electrode._current_collector._x_body_length / 2
        ref_right = ref_electrode._current_collector._datum[0] + ref_electrode._current_collector._x_body_length / 2
        ref_bottom = ref_electrode._current_collector._datum[1] - ref_electrode._current_collector._y_body_length / 2
        ref_top = ref_electrode._current_collector._datum[1] + ref_electrode._current_collector._y_body_length / 2

        # Target edges
        tgt_left = target_electrode._current_collector._datum[0] - target_electrode._current_collector._x_body_length / 2
        tgt_right = target_electrode._current_collector._datum[0] + target_electrode._current_collector._x_body_length / 2
        tgt_bottom = target_electrode._current_collector._datum[1] - target_electrode._current_collector._y_body_length / 2
        tgt_top = target_electrode._current_collector._datum[1] + target_electrode._current_collector._y_body_length / 2

        return ref_left - tgt_left, tgt_right - ref_right, ref_bottom - tgt_bottom, tgt_top - ref_top


    def _compute_separator_overhangs(self, ref_electrode: Cathode, separator: Separator) -> Tuple[float, float, float, float]:
        """Return (left, right, bottom, top) overhangs for polygon separator relative to electrode.

        A positive component means separator extends beyond cathode in that direction.
        """
        ref_left = ref_electrode._current_collector._datum[0] - ref_electrode._current_collector._x_body_length / 2
        ref_right = ref_electrode._current_collector._datum[0] + ref_electrode._current_collector._x_body_length / 2
        ref_bottom = ref_electrode._current_collector._datum[1] - ref_electrode._current_collector._y_body_length / 2
        ref_top = ref_electrode._current_collector._datum[1] + ref_electrode._current_collector._y_body_length / 2

        sep_left = float(np.min(separator._coordinates[:, 0]))
        sep_right = float(np.max(separator._coordinates[:, 0]))
        sep_bottom = float(np.min(separator._coordinates[:, 1]))
        sep_top = float(np.max(separator._coordinates[:, 1]))

        return ref_left - sep_left, sep_right - ref_right, ref_bottom - sep_bottom, sep_top - ref_top

    def _set_overhang(
        self, component: str, direction: str, overhang: float
    ) -> None:
        """Generic helper to set overhang for any component and direction.
        
        Parameters
        ----------
        component : str
            Component name ('anode', 'bottom_separator', 'top_separator')
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        overhang : float
            Target overhang value in mm
        """
        self.validate_positive_float(overhang, f"{component}_overhang_{direction}")
        
        if self._overhang_control_mode == OverhangControlMode.FIXED_COMPONENT:
            self._adjust_overhang_fixed_component(component, overhang, direction)
        elif self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            self._adjust_overhang_fixed_overhangs(component, overhang, direction)

    
    def _adjust_overhang_fixed_component(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust overhang by moving the component position (fixed component mode).

        Parameters
        ----------
        component : str
            Component name ('anode', 'bottom_separator', 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        current_overhang = getattr(self, f"{component}_overhang_{direction}")
        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        # get component datum
        datum = component_obj.datum

        if direction == "left":
            datum = (datum[0] - overhang_difference, datum[1], datum[2])
        elif direction == "right":
            datum = (datum[0] + overhang_difference, datum[1], datum[2])
        elif direction == "bottom":
            datum = (datum[0], datum[1] - overhang_difference, datum[2])
        elif direction == "top":
            datum = (datum[0], datum[1] + overhang_difference, datum[2])

        component_obj.datum = datum

        # Special handling for ZFoldMonoLayer: when anode moves left/right, top separator should follow
        if hasattr(self, "__class__") and self.__class__.__name__ == "ZFoldMonoLayer" and component == "anode" and direction in ["left", "right"]:

            # Get the top separator and adjust its position by the same amount
            top_separator_datum = self._top_separator.datum

            if direction == "left":
                top_separator_datum = (top_separator_datum[0] - overhang_difference, top_separator_datum[1], top_separator_datum[2])
            elif direction == "right":
                top_separator_datum = (top_separator_datum[0] + overhang_difference, top_separator_datum[1], top_separator_datum[2])

            self._top_separator.datum = top_separator_datum

    def _adjust_overhang_fixed_overhangs(self, component: str, target_overhang: float, direction: str) -> None:
        """
        Adjust overhang by extending the component dimensions (fixed overhangs mode).

        Parameters
        ----------
        component : str
            Component name ('anode', 'bottom_separator', 'top_separator')
        target_overhang : float
            Target overhang value in mm
        direction : str
            Direction of overhang ('left', 'right', 'bottom', 'top')
        """
        target_overhang = target_overhang * MM_TO_M
        current_overhang = getattr(self, f"_{component}_overhang_{direction}")
        overhang_difference = target_overhang - current_overhang

        # Get the component object
        component_obj = getattr(self, f"_{component}")

        if component == "anode":
            # Determine which dimension and position to adjust
            if direction in ["left", "right"]:
                self.anode.current_collector.x_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == "left":
                    self.anode.current_collector.datum_x -= position_adjustment
                else:  # right
                    self.anode.current_collector.datum_x += position_adjustment
            else:  # bottom or top
                self.anode.current_collector.y_body_length += overhang_difference * M_TO_MM
                position_adjustment = (overhang_difference / 2) * M_TO_MM
                if direction == "bottom":
                    self.anode.current_collector.datum_y -= position_adjustment
                else:  # top
                    self.anode.current_collector.datum_y += position_adjustment

            # Trigger setters
            self.anode.current_collector = self.anode.current_collector
            self.anode = self.anode

        elif isinstance(component_obj, Separator):
            # Create mapping for dimension and position adjustments
            position_adjustment = (overhang_difference / 2) * M_TO_MM

            # Determine which dimension to adjust based on rotation and direction
            is_horizontal = direction in ["left", "right"]
            is_rotated = component_obj._rotated_xy

            # Logic: if rotated, horizontal directions affect width, vertical affects length
            # If not rotated, horizontal directions affect length, vertical affects width
            if (is_horizontal and not is_rotated) or (not is_horizontal and is_rotated):
                # Adjust length
                component_obj.length += overhang_difference * M_TO_MM
            else:
                # Adjust width
                component_obj.width += overhang_difference * M_TO_MM

            # Adjust position
            if direction == "left":
                component_obj.datum_x -= position_adjustment
            elif direction == "right":
                component_obj.datum_x += position_adjustment
            elif direction == "bottom":
                component_obj.datum_y -= position_adjustment
            else:  # top
                component_obj.datum_y += position_adjustment

            # Trigger setter
            setattr(self, component, component_obj)

    @property
    def overhang_control_mode(self) -> OverhangControlMode:
        """Get the current overhang control mode."""
        return self._overhang_control_mode

    @overhang_control_mode.setter
    def overhang_control_mode(self, mode: OverhangControlMode):

        if isinstance(mode, OverhangControlMode):
            self._overhang_control_mode = mode
            return
        
        elif isinstance(mode, str):
            for enum_member in OverhangControlMode:
                if mode.lower().replace(" ", "_") == enum_member.value:
                    self._overhang_control_mode = enum_member
                    return
                

    #### ANODE OVERHANG PROPERTY/SETTERS ####

    @property
    def anode_overhang_left(self) -> float:
        """
        Get the left overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_left * M_TO_MM, 2)

    @property
    def anode_overhang_right(self) -> float:
        """
        Get the right overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_right * M_TO_MM, 2)

    @property
    def anode_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_bottom * M_TO_MM, 2)

    @property
    def anode_overhang_top(self) -> float:
        """
        Get the top overhang of the anode relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        return round(self._anode_overhang_top * M_TO_MM, 2)

    @property
    def anode_overhangs(self) -> dict:
        """
        Get all anode overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.anode_overhang_left,
            "right": self.anode_overhang_right,
            "bottom": self.anode_overhang_bottom,
            "top": self.anode_overhang_top,
        }

    @anode_overhang_left.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def anode_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self._set_overhang("anode", "left", overhang)

    @anode_overhang_right.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def anode_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self._set_overhang("anode", "right", overhang)

    @anode_overhang_bottom.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def anode_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self._set_overhang("anode", "bottom", overhang)

    @anode_overhang_top.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def anode_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the anode relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate anode extends beyond cathode.
        """
        self._set_overhang("anode", "top", overhang)

    #### ANODE OVERHANG RANGE PROPERTIES ####

    @property
    def anode_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (OVERHANG_MIN, self.anode_overhang_left + self.anode_overhang_right)

    @property
    def anode_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (OVERHANG_MIN, self.anode_overhang_left + self.anode_overhang_right)

    @property
    def anode_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (OVERHANG_MIN, self.anode_overhang_bottom + self.anode_overhang_top)

    @property
    def anode_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top anode overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (OVERHANG_MIN, self.anode_overhang_bottom + self.anode_overhang_top)

    #### BOTTOM SEPARATOR OVERHANG PROPERTY/SETTERS ####

    @property
    def bottom_separator_overhang_left(self) -> float:
        """
        Get the left overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_left * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_right(self) -> float:
        """
        Get the right overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_right * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_bottom * M_TO_MM, 3)

    @property
    def bottom_separator_overhang_top(self) -> float:
        """
        Get the top overhang of the bottom separator relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._bottom_separator_overhang_top * M_TO_MM, 3)

    @property
    def bottom_separator_overhangs(self) -> dict:
        """
        Get all bottom separator overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.bottom_separator_overhang_left,
            "right": self.bottom_separator_overhang_right,
            "bottom": self.bottom_separator_overhang_bottom,
            "top": self.bottom_separator_overhang_top,
        }

    @bottom_separator_overhang_left.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def bottom_separator_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("bottom_separator", "left", overhang)

    @bottom_separator_overhang_right.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def bottom_separator_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("bottom_separator", "right", overhang)

    @bottom_separator_overhang_bottom.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def bottom_separator_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("bottom_separator", "bottom", overhang)

    @bottom_separator_overhang_top.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def bottom_separator_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the bottom separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("bottom_separator", "top", overhang)

    #### BOTTOM SEPARATOR OVERHANG RANGE PROPERTIES ####

    @property
    def bottom_separator_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20) or (0, 500) for Laminate
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self).__name__ == "Laminate":
                return (OVERHANG_MIN, OVERHANG_MAX_LAMINATE)
            else:
                return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            max_val = (self._bottom_separator_overhang_left + self._bottom_separator_overhang_right) * M_TO_MM
            return (OVERHANG_MIN, max_val)

    @property
    def bottom_separator_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20) or (0, 500) for Laminate
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self).__name__ == "Laminate":
                return (OVERHANG_MIN, OVERHANG_MAX_LAMINATE)
            else:
                return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            max_val = (self._bottom_separator_overhang_left + self._bottom_separator_overhang_right) * M_TO_MM
            return (OVERHANG_MIN, max_val)

    @property
    def bottom_separator_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            max_val = (self._bottom_separator_overhang_bottom + self._bottom_separator_overhang_top) * M_TO_MM
            return (OVERHANG_MIN, max_val)

    @property
    def bottom_separator_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top bottom separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            max_val = (self._bottom_separator_overhang_bottom + self._bottom_separator_overhang_top) * M_TO_MM
            return (OVERHANG_MIN, max_val)

    #### TOP SEPARATOR OVERHANG PROPERTY/SETTERS ####

    @property
    def top_separator_overhang_left(self) -> float:
        """
        Get the left overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_left * M_TO_MM, 3)

    @property
    def top_separator_overhang_right(self) -> float:
        """
        Get the right overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_right * M_TO_MM, 3)

    @property
    def top_separator_overhang_bottom(self) -> float:
        """
        Get the bottom overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_bottom * M_TO_MM, 3)

    @property
    def top_separator_overhang_top(self) -> float:
        """
        Get the top overhang of the top separator relative to the cathode in mm.

        Returns
        -------
        float
            Top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        return round(self._top_separator_overhang_top * M_TO_MM, 3)

    @property
    def top_separator_overhangs(self) -> dict:
        """
        Get all top separator overhangs as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys 'left', 'right', 'bottom', 'top' and overhang values in mm.
        """
        return {
            "left": self.top_separator_overhang_left,
            "right": self.top_separator_overhang_right,
            "bottom": self.top_separator_overhang_bottom,
            "top": self.top_separator_overhang_top,
        }

    @top_separator_overhang_left.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def top_separator_overhang_left(self, overhang: float) -> None:
        """
        Set the left overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target left overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("top_separator", "left", overhang)

    @top_separator_overhang_right.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def top_separator_overhang_right(self, overhang: float) -> None:
        """
        Set the right overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target right overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("top_separator", "right", overhang)

    @top_separator_overhang_bottom.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def top_separator_overhang_bottom(self, overhang: float) -> None:
        """
        Set the bottom overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target bottom overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("top_separator", "bottom", overhang)

    @top_separator_overhang_top.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def top_separator_overhang_top(self, overhang: float) -> None:
        """
        Set the top overhang of the top separator relative to the cathode.

        Parameters
        ----------
        overhang : float
            Target top overhang in mm. Positive values indicate separator extends beyond cathode.
        """
        self._set_overhang("top_separator", "top", overhang)

    #### TOP SEPARATOR OVERHANG RANGE PROPERTIES ####

    @property
    def top_separator_overhang_left_range(self) -> tuple:
        """
        Get the valid range for left top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20) or (0, 500) for Laminate
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self).__name__ == "Laminate":
                return (OVERHANG_MIN, OVERHANG_MAX_LAMINATE)
            else:
                return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (
                OVERHANG_MIN,
                self.top_separator_overhang_left + self.top_separator_overhang_right,
            )

    @property
    def top_separator_overhang_right_range(self) -> tuple:
        """
        Get the valid range for right top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20) or (0, 500) for Laminate
            FIXED_COMPONENT: (0, left + right overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            if type(self).__name__ == "Laminate":
                return (OVERHANG_MIN, OVERHANG_MAX_LAMINATE)
            else:
                return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (
                OVERHANG_MIN,
                self.top_separator_overhang_left + self.top_separator_overhang_right,
            )

    @property
    def top_separator_overhang_bottom_range(self) -> tuple:
        """
        Get the valid range for bottom top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (
                OVERHANG_MIN,
                self.top_separator_overhang_bottom + self.top_separator_overhang_top,
            )

    @property
    def top_separator_overhang_top_range(self) -> tuple:
        """
        Get the valid range for top top separator overhang based on control mode.

        Returns
        -------
        tuple
            (min, max) overhang range in mm.
            FIXED_OVERHANGS: (0, 20)
            FIXED_COMPONENT: (0, bottom + top overhang total)
        """
        if self._overhang_control_mode == OverhangControlMode.FIXED_OVERHANGS:
            return (OVERHANG_MIN, OVERHANG_MAX_DEFAULT)
        else:  # FIXED_COMPONENT
            return (
                OVERHANG_MIN,
                self.top_separator_overhang_bottom + self.top_separator_overhang_top,
            )
        
                
