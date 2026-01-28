
# import core decorators
from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_areas

# import core units
from steer_core.Constants.Units import *

# import materials
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

# import other current collector types for class methods
from steer_opencell_design.Components.CurrentCollectors.Notched import NotchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector

# import base functions
from typing import Tuple, Optional
import numpy as np


class TablessCurrentCollector(NotchedCurrentCollector):
    """
    Streamlined current collector without protruding tabs.

    The tabless current collector represents the most space-efficient design,`
    eliminating protruding tabs entirely in favor of edge-based connections.
    This design is particularly advantageous for cylindrical cells, flatwound
    configurations, and applications where minimizing cell volume and complexity
    are paramount.

    Key advantages of the tabless design:
    - Simplified manufacturing with fewer cutting/forming operations
    - Reduced risk of tab damage during handling and assembly
    - Better suitability for automated winding and stacking processes
    - Lower material waste during production
    - Enhanced mechanical robustness

    This design is especially well-suited for:
    - Cylindrical cells (18650, 21700, 4680 formats)
    - Flatwound rectangular cells
    - High-volume consumer applications
    - Cells requiring consistent cylindrical geometry
    - Applications where tab damage is a reliability concern

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition for electrical and mechanical properties
        Typically aluminum for cathodes, copper for anodes
    length : float
        Total length of the collector in the primary direction (mm)
        For cylindrical cells, this determines the winding length
    width : float
        Total width of the collector (mm)
        For cylindrical cells, this affects the electrode height
    coated_width : float
        Width of the region available for active material coating (mm)
        Must be less than total width to provide bare connection strips
    thickness : float
        Material thickness in micrometers (μm)
        Affects cell internal resistance and energy density
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated lengths on a-side for connections (mm)
        Provides flexibility for different cell termination strategies
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated lengths on b-side for connections (mm)
        Enables asymmetric designs for specific applications
    insulation_width : float, optional
        Width of insulation strip around edges (mm, default: 0)
        Critical for preventing short circuits in tabless designs
    name : str, optional
        Descriptive identifier for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Design a tabless collector for a 21700 cylindrical cell:

    >>> from steer_materials import CurrentCollectorMaterial
    >>> collector = TablessCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Aluminum'),
    ...     length=650.0,        # mm - enough for multiple winds
    ...     width=65.0,          # mm - fits 21700 height
    ...     coated_width=60.0,   # mm - 2.5mm bare strips on edges
    ...     thickness=15.0,      # μm
    ...     bare_lengths_a_side=(10.0, 10.0),  # mm
    ...     bare_lengths_b_side=(10.0, 10.0),  # mm
    ...     insulation_width=0.5 # mm - prevent shorts
    ... )
    >>> print(f"Coated fraction: {collector.coated_fraction:.2%}")
    >>> print(f"Connection strip width: {collector.connection_strip_width:.1f} mm")

    See Also
    --------
    PunchedCurrentCollector : Simple tabbed alternative
    NotchedCurrentCollector : Multi-tab design with more connection points
    TabWeldedCurrentCollector : Separate welded tab approach
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        coated_width: float,
        thickness: float,
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Tabless Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a tabless current collector.

        Parameters
        ----------
        material: CurrentCollectorMaterial:
            Material of the current collector.
        length: float:
            Length of the current collector in mm.
        width: float:
            Width of the current collector in mm.
        coated_width: float:
            Width of the coated area in mm.
        thickness: float:
            Thickness of the current collector in um.
        bare_lengths_a_side: Tuple[float, float]:
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side: Tuple[float, float]:
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        insulation_width: Optional[float]:
            Width of the insulation strip in mm, default is 0.
        name: Optional[str]:
            Name of the current collector, default is 'Tabless Current Collector'.
        """
        tab_height = width - coated_width
        width = width - tab_height

        super().__init__(
            material=material,
            length=length,
            width=width,
            thickness=thickness,
            tab_height=tab_height,
            tab_width=length,
            tab_spacing=length,
            coated_tab_height=0,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self._update_properties = False
        self.coated_width = coated_width
        self._update_properties = True

    @classmethod
    def from_notched(cls, notched: "NotchedCurrentCollector") -> "TablessCurrentCollector":
        """
        Create a TablessCurrentCollector from a NotchedCurrentCollector.
        """
        new_current_collector = cls(
            material=notched.material,
            length=notched.x_foil_length,
            width=notched.y_foil_length + notched.tab_height,
            coated_width=notched.y_foil_length,
            thickness=notched.thickness,
            bare_lengths_a_side=notched.bare_lengths_a_side,
            bare_lengths_b_side=notched.bare_lengths_b_side,
            insulation_width=notched.insulation_width,
            datum=notched.datum,
        )

        # perform actions if needed
        if notched._flipped_x:
            new_current_collector._flip("x")
        if notched._flipped_y:
            new_current_collector._flip("y")
        if notched._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @classmethod
    def from_tab_welded(cls, tab_welded: "TabWeldedCurrentCollector") -> "TablessCurrentCollector":
        """
        Create a TablessCurrentCollector from a TabWeldedCurrentCollector.
        """
        new_current_collector = cls(
            material=tab_welded.material,
            length=tab_welded.x_foil_length,
            width=tab_welded.y_foil_length,
            coated_width=tab_welded.y_foil_length - 10,
            thickness=tab_welded.thickness,
            bare_lengths_a_side=tab_welded.bare_lengths_a_side,
            bare_lengths_b_side=tab_welded.bare_lengths_b_side,
            insulation_width=0,
            datum=tab_welded.datum,
        )

        # perform actions if needed
        if tab_welded._flipped_x:
            new_current_collector._flip("x")
        if tab_welded._flipped_y:
            new_current_collector._flip("y")
        if tab_welded._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @property
    def coated_width(self) -> float:
        return np.round(self._coated_width * M_TO_MM, 2)

    @property
    def coated_width_range(self) -> Tuple[float, float]:
        """
        Get the coated width range in mm.
        """
        if hasattr(self, "_y_foil_length_range") and self._y_foil_length_range is not None:
            min = self.y_foil_length_range[0]
        else:
            min = self.width - self.tab_height_range[1]

        max = self.width - self.tab_height_range[0]

        return (min, max)

    @property
    def coated_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the coated width range in mm.
        """
        return (0, self.width)

    @property
    def tab_height_range(self) -> Tuple[float, float]:
        return (1, self.width * 1 / 4)

    @property
    def width(self) -> float:
        return np.round((self._y_foil_length + self._tab_height) * M_TO_MM, 2)

    @property
    def width_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_foil_length_range") and self._y_foil_length_range is not None:
            min_width = self.y_foil_length_range[0] + self.tab_height
            max_width = self.y_foil_length_range[1] + self.tab_height
            return (round(min_width, 2), np.round(max_width, 2))
        else:
            return (0, 1000)

    @property
    def tab_height(self) -> float:
        return np.round(self._tab_height * M_TO_MM, 2)

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")

        new_y_length = width - self.tab_height
        self._coated_width = new_y_length * MM_TO_M
        self.y_foil_length = new_y_length

        # Automatically adjust coated_width if it's now too large
        _max_coated_width = self._y_foil_length

        if self._coated_width > _max_coated_width:
            self.coated_width = _max_coated_width * M_TO_MM

    @coated_width.setter
    @calculate_areas
    def coated_width(self, coated_width: float) -> None:
        self.validate_positive_float(coated_width, "coated_width")

        # Store the current total width
        current_total_width = self.width

        # Set the new coated width
        self._coated_width = float(coated_width) * MM_TO_M

        # Calculate new tab height to maintain total width
        new_tab_height = current_total_width - coated_width

        # Validate the new tab height is positive
        if new_tab_height < 0:
            raise ValueError(f"Coated width {coated_width} mm is too large. Maximum allowed is {current_total_width} mm.")

        # Update tab height and y_foil_length
        self._tab_height = new_tab_height * MM_TO_M
        self._y_foil_length = self._coated_width  # y_foil_length equals coated_width

    @tab_height.setter
    @calculate_all_properties
    def tab_height(self, tab_height: float) -> None:
        self.validate_positive_float(tab_height, "tab_height")
        self._tab_height = float(tab_height) * MM_TO_M

