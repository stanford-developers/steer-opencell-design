# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Notched current collector for tabless wound cells."""

# import core decorators
from steer_core.Decorators.General import calculate_all_properties

# import core units
from steer_core.Constants.Units import *

# import materials
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

from collections.abc import Iterable
from typing import Tuple, Optional
import numpy as np

# Generic tab-width limits in meters, used when the collector is not wound into
# a flat roll whose racetrack would bound it.
TAB_WIDTH_MIN = 0.01
TAB_WIDTH_MAX = 0.5

# Collector -> electrode -> layup -> assembly: how far to look for the roll.
_RACETRACK_LOOKUP_DEPTH = 4

from steer_opencell_design.Components.CurrentCollectors.Base import _TabbedCurrentCollector, _TapeCurrentCollector


class NotchedCurrentCollector(_TabbedCurrentCollector, _TapeCurrentCollector):
    """
    The notched current collector combines features from both tabbed and tape
    connection methods. It features multiple tabs along its length for improved
    current distribution and configurable bare regions for tape-style connections,
    offering excellent flexibility for various cell architectures and connection
    strategies.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical, thermal, and mechanical properties
        Selection impacts resistance, cost, and compatibility with active materials
    length : float
        Total length of the collector in the primary direction (mm)
        Determines the number of tabs that can be accommodated
    width : float
        Width of the collector perpendicular to the length (mm)
        Affects current path lengths and collector resistance
    thickness : float
        Material thickness in micrometers (μm)
        Impacts electrical resistance and mechanical stiffness
    tab_width : float
        Width of each individual tab (mm)
        Should be optimized for current density and manufacturing constraints
    tab_spacing : float
        Center-to-center distance between adjacent tabs (mm)
        Determines current distribution uniformity
    tab_height : float
        Extension height of tabs beyond the foil (mm)
        Must provide adequate access for welding and connections
    coated_tab_height : float, optional
        Height of active material coating on each tab (mm, default: 0)
        Allows for energy density optimization while maintaining connections
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated lengths on a-side for tape connections (mm)
        Enables hybrid connection strategies
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated lengths on b-side for tape connections (mm)
        Provides flexibility for asymmetric designs
    insulation_width : float, optional
        Width of insulation strip around perimeter (mm, default: 0)
    name : str, optional
        Descriptive identifier for the collector
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Create a high-performance notched collector for an EV battery:

    >>> from steer_materials import copper_foil_12um
    >>> collector = NotchedCurrentCollector(
    ...     material=copper_foil_12um,
    ...     length=2500.0,        # mm - large format cell
    ...     width=180.0,         # mm
    ...     thickness=12.0,      # μm
    ...     tab_width=30.0,      # mm - wide tabs for high current
    ...     tab_spacing=50.0,    # mm - 5 tabs total
    ...     tab_height=15.0,     # mm
    ...     coated_tab_height=10.0,  # Partially coated tabs
    ...     bare_lengths_a_side=(15.0, 15.0),  # Tape connection option
    ...     bare_lengths_b_side=(10.0, 10.0)
    ... )
    >>> print(f"Number of tabs: {collector.n_tabs}")
    >>> print(f"Total tab area: {collector.total_tab_area:.1f} mm²")
    >>> print(f"Effective resistance: {collector.effective_resistance:.6f} Ω")

    >>> thermal_fig = collector.get_thermal_map()
    >>> thermal_fig.show()

    Compare connection strategies:

    >>> print("Available connections:", collector.connection_flexibility.keys())
    >>> # Output: ['tab_welding', 'tape_welding_a', 'tape_welding_b', 'hybrid']

    See Also
    --------
    PunchedCurrentCollector : Simple single-tab design
    TablessCurrentCollector : Tape-only connection without tabs
    TabWeldedCurrentCollector : Separate welded tab approach
    _TabbedCurrentCollector : Base class for tab functionality
    _TapeCurrentCollector : Base class for tape functionality
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        thickness: float,
        tab_width: float,
        tab_spacing: float,
        tab_height: float,
        coated_tab_height: float = 0,
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Notched Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
        tab_center_positions: Optional[Iterable[float]] = None,
    ) -> None:
        """
        Initialize an object that represents a notched current collector.

        Parameters
        ----------
        material : CurrentCollectorMaterial
            Material of the current collector.
        length : float
            Length of the current collector in mm.
        width : float
            Width of the current collector in mm.
        thickness : float
            Thickness of the current collector in µm.
        tab_width : float
            Width of the tabs in mm.
        tab_spacing : float
            Spacing between the tabs in mm.
        tab_height : float
            Height of the tabs in mm.
        tab_center_positions : iterable of float, optional
            Explicit tab center positions measured from the leading edge of the
            foil in mm. When provided, these thickness-aware or otherwise
            custom positions take precedence over ``tab_spacing``.
        coated_tab_height : float
            Height of the coated tab on the top side in mm.
        bare_lengths_a_side : Tuple[float, float]
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side : Tuple[float, float]
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        insulation_width : Optional[float], default=0
            Width of the insulation strip in mm.
        name : Optional[str], default='Notched Current Collector'
            Name of the current collector.
        datum : Optional[Tuple[float, float, float]], default=(0, 0, 0)
            Datum of the current collector in mm.
        """
        # Must exist before the base-class initialization invokes coordinate
        # hooks through this class's MRO.
        self._requested_tab_center_positions = None
        self._assembly_tab_center_positions = None
        self._active_tab_center_positions = None

        super().__init__(
            material=material,
            x_foil_length=length,
            y_foil_length=width,
            tab_width=tab_width,
            tab_height=tab_height,
            thickness=thickness,
            coated_tab_height=coated_tab_height,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self.tab_spacing = tab_spacing
        self.tab_center_positions = tab_center_positions
        self._calculate_all_properties()
        self._update_properties = True

    @classmethod
    def from_tabless(cls, tabless) -> "NotchedCurrentCollector":
        """
        Create a NotchedCurrentCollector from a TablessCurrentCollector.
        """
        from steer_opencell_design.Components.CurrentCollectors.Tabless import TablessCurrentCollector

        # validate type
        cls.validate_type(tabless, TablessCurrentCollector, "tabless")

        new_current_collector = cls(
            material=tabless.material,
            length=tabless.x_foil_length,
            width=tabless.y_foil_length,
            thickness=tabless.thickness,
            tab_width=50,
            tab_spacing=100,
            tab_height=tabless.tab_height,
            coated_tab_height=0,
            bare_lengths_a_side=tabless.bare_lengths_a_side,
            bare_lengths_b_side=tabless.bare_lengths_b_side,
            insulation_width=tabless.insulation_width,
            datum=tabless.datum,
        )

        # perform actions if needed
        if tabless._flipped_x:
            new_current_collector._flip("x")
        if tabless._flipped_y:
            new_current_collector._flip("y")
        if tabless._flipped_z:
            new_current_collector._flip("z")

        return new_current_collector

    @classmethod
    def from_tab_welded(cls, tab_welded) -> "NotchedCurrentCollector":
        """
        Create a NotchedCurrentCollector from a TabWeldedCurrentCollector.
        """
        from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector

        # validate type
        cls.validate_type(tab_welded, TabWeldedCurrentCollector, "tab_welded")

        new_current_collector = cls(
            material=tab_welded.material,
            length=tab_welded.x_foil_length,
            width=tab_welded.y_foil_length - 10,
            thickness=tab_welded.thickness,
            tab_width=50,
            tab_spacing=100,
            tab_height=10,
            coated_tab_height=0,
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

    def _calculate_tab_positions(self) -> None:
        """Calculate tab positions for the currently active notch pattern."""
        self._sync_tab_center_positions()

        centers = self._active_tab_center_positions
        if centers is not None:
            self._calculate_explicit_tab_positions(centers)
            return

        self._calculate_regular_tab_positions()

    def _sync_tab_center_positions(self) -> None:
        """Derive the active tab centers from the requested and generated patterns.

        Assembly-generated centers take precedence over a user-supplied pattern,
        which in turn takes precedence over uniform ``tab_spacing``. Centers that
        no longer fit the current foil length or tab width are inactive but
        retained, so re-growing the foil (or re-narrowing the tab) restores them.
        This mirrors ``_TabbedCurrentCollector._sync_weld_tab_positions``.
        """
        # Objects rebuilt by SerializerMixin._from_dict never run __init__, so
        # payloads written before these attributes existed carry neither.
        requested = getattr(self, "_requested_tab_center_positions", None)
        generated = getattr(self, "_assembly_tab_center_positions", None)

        source = generated if generated is not None else requested
        if source is None or len(source) == 0:
            self._active_tab_center_positions = None
            return

        active = self._select_fitting_tab_centers(np.asarray(source, dtype=float))
        # A notched collector always needs a current path, so fall back to the
        # uniform pattern rather than leaving the foil without any notches.
        self._active_tab_center_positions = active if len(active) else None

    def _select_fitting_tab_centers(self, positions: np.ndarray) -> np.ndarray:
        """Return the centers that keep a full, non-overlapping tab on the foil."""
        half_width = self._tab_width / 2
        on_foil = positions[
            (positions >= half_width)
            & (positions <= self._x_foil_length - half_width)
        ]
        if len(on_foil) < 2:
            return on_foil

        # Drop the later member of each overlapping pair so the retained pattern
        # stays an ordered subset of what was requested.
        kept = [on_foil[0]]
        for position in on_foil[1:]:
            if position - kept[-1] >= self._tab_width:
                kept.append(position)
        return np.asarray(kept, dtype=float)

    def _calculate_explicit_tab_positions(
        self, centers_from_leading_edge: np.ndarray
    ) -> None:
        """Calculate tab edges from active centers in internal meter units."""
        # Collector coordinates are centered on the datum, while tab centers are
        # measured from the foil's leading (minimum-x) edge.
        x_min = self._datum[0] - self._x_foil_length / 2
        centers = x_min + np.asarray(centers_from_leading_edge, dtype=float)
        self._tab_positions = np.column_stack(
            (
                centers - self._tab_width / 2,
                centers + self._tab_width / 2,
            )
        )

    def _calculate_regular_tab_positions(self) -> None:
        """Calculate tab edges using the configured uniform center spacing."""
        # Convert the datum-centered foil bounds into absolute x-coordinates.
        x_min = self._datum[0] - self._x_foil_length / 2

        # Search one spacing beyond the trailing edge; the clipping logic below
        # then retains or trims the final tab according to the legacy behavior.
        x_max = self._datum[0] + self._x_foil_length / 2 + self._tab_spacing

        tab_positions = [x_min + self._tab_spacing / 2]
        tab_starts = [tab_positions[0] - self._tab_width / 2]
        tab_ends = [tab_positions[0] + self._tab_width / 2]

        while tab_positions[-1] < x_max:
            next_tab_position = tab_positions[-1] + self._tab_spacing

            if next_tab_position + self._tab_width / 2 > x_max:
                break

            tab_positions.append(next_tab_position)
            tab_starts.append(next_tab_position - self._tab_width / 2)
            tab_ends.append(next_tab_position + self._tab_width / 2)

        if tab_starts[-1] > self._datum[0] + self._x_foil_length / 2:
            tab_starts = tab_starts[:-1]
            tab_ends = tab_ends[:-1]

        if tab_ends[-1] > self._datum[0] + self._x_foil_length / 2:
            tab_ends[-1] = self._datum[0] + self._x_foil_length / 2

        self._tab_positions = np.column_stack((tab_starts, tab_ends))

    def _validate_explicit_tab_center_positions(self, positions: np.ndarray) -> None:
        """Validate requested tab centers expressed in internal meter units.

        Called from the ``tab_center_positions`` setter before anything is
        written, so a rejected pattern leaves the collector untouched. Later
        geometry changes deactivate centers rather than raising; see
        ``_sync_tab_center_positions``.
        """
        if positions.ndim != 1:
            raise ValueError("tab_center_positions must be a one-dimensional sequence.")
        if not np.all(np.isfinite(positions)):
            raise ValueError("tab_center_positions must contain only finite values.")
        if len(positions) == 0:
            raise ValueError(
                "tab_center_positions must contain at least one position; pass "
                "None to return to uniform tab spacing."
            )

        minimum_center = self._tab_width / 2
        maximum_center = self._x_foil_length - self._tab_width / 2
        if positions[0] < minimum_center or positions[-1] > maximum_center:
            raise ValueError(
                "Each tab center must keep the full tab within the foil length."
            )

        pitches = np.diff(positions)
        if np.any(pitches <= 0):
            raise ValueError("tab_center_positions must be strictly increasing.")
        if np.any(pitches < self._tab_width):
            raise ValueError("Explicit tabs cannot overlap.")

    def _is_assembly_aligned(self) -> bool:
        """Return whether a containing assembly currently owns the centers."""
        return getattr(self, "_assembly_tab_center_positions", None) is not None

    def _set_assembly_tab_center_positions(
        self, positions: Optional[np.ndarray]
    ) -> None:
        """Install or clear assembly-generated centers in internal meter units.

        The generated pattern is a cache derived from the wound geometry, so it
        never overwrites the user's requested pattern: clearing it restores that
        pattern without needing a saved snapshot.
        """
        if positions is None:
            self._assembly_tab_center_positions = None
        else:
            positions = np.asarray(positions, dtype=float)
            if positions.ndim != 1 or len(positions) == 0:
                raise ValueError(
                    "Assembly-generated tab centers must be a non-empty "
                    "one-dimensional sequence."
                )
            self._assembly_tab_center_positions = positions.copy()

        if getattr(self, "_update_properties", False):
            self._calculate_all_properties()

    def _calculate_coordinates(self):
        self._calculate_tab_positions()
        super()._calculate_coordinates()

    def _get_footprint(
        self,
        notch_height: Optional[float] = None,
        bare_lengths: Tuple[float, float] = (0, 0),
        y_depth: Optional[float] = None,
        y_start: Optional[float] = None,
        x_start: Optional[float] = None,
        x_end: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return a closed polyline (DataFrame of x/y) for the notched collector.
        All internal units in meters; bare_lengths come in mm.
        Optional x_start and x_end can restrict the x-bounds of the shape.
        """
        # Default values
        y_depth = self._y_foil_length if y_depth is None else y_depth
        y_start = self._datum[1] - self._y_foil_length / 2 if y_start is None else y_start
        notch = self._tab_height if notch_height is None else notch_height

        # Convert bare lengths to meters (they come in mm according to docstring)
        bare_left = bare_lengths[0] * MM_TO_M if bare_lengths[0] != 0 else 0
        bare_right = bare_lengths[1] * MM_TO_M if bare_lengths[1] != 0 else 0

        # X bounds
        default_x0 = self._datum[0] - self._x_foil_length / 2 + bare_left
        default_x1 = self._datum[0] + self._x_foil_length / 2 - bare_right
        x0 = default_x0 if x_start is None else x_start
        x1 = default_x1 if x_end is None else x_end

        y0 = y_start
        y1 = y_start + y_depth

        pts = []

        # Start at bottom-left
        pts.append((x0, y0))
        # Go up to top edge
        pts.append((x0, y1))

        # Get valid tab positions within the x-range and sort them
        valid_tabs = []
        for ts, te in self._tab_positions:
            # Check if tab overlaps with our x-range
            if te > x0 and ts < x1:
                # Clip tab to our x-range
                s = max(ts, x0)
                e = min(te, x1)
                if e > s:  # Valid tab after clipping
                    valid_tabs.append((s, e))

        # Sort tabs by start position
        valid_tabs.sort(key=lambda tab: tab[0])

        # Process each valid tab
        current_x = x0

        for tab_start, tab_end in valid_tabs:
            # Horizontal run to start of notch (if needed)
            if current_x < tab_start:
                if pts[-1] != (current_x, y1):
                    pts.append((current_x, y1))
                pts.append((tab_start, y1))

            # Draw the notch
            pts.append((tab_start, y1 + notch))
            pts.append((tab_end, y1 + notch))
            pts.append((tab_end, y1))

            # Update current position
            current_x = tab_end

        # Finish the top edge to x1
        if current_x < x1:
            if pts[-1] != (current_x, y1):
                pts.append((current_x, y1))
            pts.append((x1, y1))

        # Close the shape
        pts.append((x1, y0))
        pts.append((x0, y0))

        # Convert to numpy arrays
        x = np.array([p[0] for p in pts], dtype=float)
        y = np.array([p[1] for p in pts], dtype=float)

        return x, y

    def _get_insulation_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Return insulation coordinates for a given side ('a' or 'b') as numpy array.
        Handles three cases: (1) above foil, (2) below foil, (3) straddling edge.
        """
        if self._insulation_width == 0:
            return np.empty((0, 3))

        # Compute insulation Y-range
        y_foil_top = self._datum[1] + self._y_foil_length / 2
        y_ins_start = y_foil_top + self._coated_tab_height - self._insulation_width
        y_ins_end = y_ins_start + self._insulation_width

        # Compute x bounds of coated region
        bare_left, bare_right = self._bare_lengths_a_side if side == "a" else self._bare_lengths_b_side
        
        # Check if bare lengths exceed foil length - return empty arrays if so
        if bare_left + bare_right >= self._x_foil_length:
            return np.empty((0, 3))
            
        x_start = self._datum[0] - self._x_foil_length / 2 + bare_left
        x_end = self._datum[0] + self._x_foil_length / 2 - bare_right

        # Case 1: Insulation entirely above the foil
        if np.round(y_ins_start, 5) >= np.round(y_foil_top, 5):
            all_x = []
            all_y = []

            for idx, (ts, te) in enumerate(self._tab_positions):
                ts = float(ts)
                te = float(te)

                # Clip tab to coated region
                if te < x_start or ts > x_end:
                    continue

                s = max(ts, x_start)
                e = min(te, x_end)

                # Get coordinates for this tab's insulation rectangle
                tab_x, tab_y = self.build_square_array(x_width=e - s, y_width=self._insulation_width, x=s, y=y_ins_start)

                # Add to lists
                all_x.extend(tab_x)
                all_y.extend(tab_y)

                # Add None values to break the fill for multiple rectangles
                if idx < len(self._tab_positions) - 1:  # Don't add break after last tab
                    all_x.append(None)
                    all_y.append(None)

            x = np.array(all_x)
            y = np.array(all_y)

        # Case 2: Insulation entirely below the foil
        elif np.round(y_ins_end, 10) <= np.round(y_foil_top, 10):
            x, y = self.build_square_array(
                x_width=x_end - x_start,
                y_width=self._insulation_width,
                x=x_start,
                y=y_ins_start,
            )

        # Case 3: Insulation straddles the top of the foil
        else:
            notch = y_ins_end - y_foil_top
            depth = y_foil_top - y_ins_start
            x, y = self._get_footprint(
                notch_height=notch,
                y_depth=depth,
                y_start=y_ins_start,
                x_start=x_start,
                x_end=x_end,
            )

        # Get z-coordinate from foil coordinates for this side
        idx = np.where(self._foil_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No foil coordinates found for side '{side}'")

        z_val = self._foil_coordinates[idx[0], 2]

        # Create z array with proper numeric dtype
        z = np.full_like(x, z_val, dtype=float)
        
        # Handle None values by converting to NaN for numeric arrays
        none_mask = np.array([val is None for val in x])
        if np.any(none_mask):
            z[none_mask] = np.nan

        # Stack into final (N, 3) array
        return np.column_stack((x, y, z))

    @property
    def tab_positions(self) -> list:
        return [(start * M_TO_MM, end * M_TO_MM) for start, end in self._tab_positions]

    @property
    def tab_center_positions(self) -> Optional[list]:
        """Return the active explicit centers from the foil leading edge in mm.

        ``None`` means the uniform ``tab_spacing`` pattern is in use. As with
        ``weld_tab_positions``, this reports the centers actually in effect:
        assembly-generated centers while notch alignment is active, otherwise
        the requested centers that still fit the current geometry.
        """
        positions = getattr(self, "_active_tab_center_positions", None)
        if positions is None:
            return None
        return (positions * M_TO_MM).tolist()

    @property
    def requested_tab_center_positions(self) -> Optional[list]:
        """Return the explicit centers as requested, in mm, including inactive ones."""
        positions = getattr(self, "_requested_tab_center_positions", None)
        if positions is None:
            return None
        return (positions * M_TO_MM).tolist()

    @property
    def n_tabs(self) -> int:
        """Return the number of tab segments in the current pattern."""
        return len(self._tab_positions)

    @property
    def tab_spacing(self) -> float:
        return self._tab_spacing * M_TO_MM

    @property
    def tab_spacing_range(self) -> Tuple[float, float]:
        """
        Get the tab spacing range in mm.
        """
        return (round(self.tab_width + 0.1, 2), 1000)

    @property
    def tab_spacing_hard_range(self) -> Tuple[float, float]:
        return self.tab_spacing_range

    @property
    def tab_gap(self) -> float:
        return self._tab_gap * M_TO_MM

    @property
    def tab_gap_range(self) -> Tuple[float, float]:
        """
        Get the tab gap range in mm.
        """
        return (
            0.1,  # Minimum gap
            1000 - self.tab_width,  # Maximum gap (based on max spacing minus tab width)
        )

    @property
    def tab_gap_hard_range(self) -> Tuple[float, float]:
        return self.tab_gap_range

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        """Same as ``tab_width_range``: the racetrack limit is not negotiable."""
        return self.tab_width_range

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        """Valid tab width in mm, capped by the racetrack when flat-wound.

        A notch has to sit on a flat face of the wound profile, so it can never
        be wider than the pressed mandrel's straight section. Outside a
        flat-wound roll -- standalone, or in a cylindrical one, which has no
        straight section -- the generic component limit applies.
        """
        lower, upper = TAB_WIDTH_MIN * M_TO_MM, TAB_WIDTH_MAX * M_TO_MM
        straight_length = self._racetrack_straight_length()
        if straight_length is not None:
            upper = min(upper, straight_length)
        return (lower, upper)

    def _racetrack_straight_length(self) -> Optional[float]:
        """Straight-section length in mm of the flat-wound roll this is wound into.

        Walks up the ownership chain (collector -> electrode -> layup ->
        assembly) looking for something that reports a pressed straight length,
        rather than importing ``FlatWoundJellyRoll`` here, which would be a
        circular import. ``None`` when there is no such ancestor.
        """
        node = self
        for _ in range(_RACETRACK_LOOKUP_DEPTH):
            node = node._get_parent() if hasattr(node, "_get_parent") else None
            if node is None:
                return None
            straight_length = getattr(node, "pressed_straight_length", None)
            if straight_length is not None:
                return straight_length
        return None

    @tab_spacing.setter
    @calculate_all_properties
    def tab_spacing(self, tab_spacing: float) -> None:

        self.validate_positive_float(tab_spacing, "tab_spacing")
        tab_spacing_m = float(tab_spacing) * MM_TO_M
        tab_gap_m = tab_spacing_m - self._tab_width
        if tab_gap_m < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")

        self._tab_spacing = tab_spacing_m
        self._tab_gap = tab_gap_m
        self._requested_tab_center_positions = None

    @tab_gap.setter
    @calculate_all_properties
    def tab_gap(self, tab_gap: float) -> None:
        """
        Set the tab gap by adjusting the tab spacing.

        Parameters
        ----------
        tab_gap : float
            The gap between tabs in mm.
        """
        self.validate_positive_float(tab_gap, "tab_gap")

        # Convert to internal units (meters)
        tab_gap_m = float(tab_gap) * MM_TO_M

        # Calculate new tab spacing: gap + tab width
        new_tab_spacing = tab_gap_m + self._tab_width

        self._tab_gap = tab_gap_m
        self._tab_spacing = new_tab_spacing
        self._requested_tab_center_positions = None

    @tab_center_positions.setter
    @calculate_all_properties
    def tab_center_positions(
        self, tab_center_positions: Optional[Iterable[float]]
    ) -> None:
        """Set explicit centers from the foil leading edge, in millimeters."""
        if tab_center_positions is None:
            self._requested_tab_center_positions = None
            return
        if isinstance(tab_center_positions, (str, bytes)) or not isinstance(
            tab_center_positions, Iterable
        ):
            raise TypeError(
                "tab_center_positions must be an iterable of numbers or None."
            )

        try:
            positions = np.asarray(list(tab_center_positions), dtype=float) * MM_TO_M
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "tab_center_positions must be an iterable of numbers or None."
            ) from exc

        # Validated before anything is written, so a rejected pattern leaves the
        # previously requested centers in place.
        self._validate_explicit_tab_center_positions(positions)
        self._requested_tab_center_positions = positions.copy()
