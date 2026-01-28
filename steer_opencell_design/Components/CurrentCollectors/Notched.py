# import core decorators
from steer_core.Decorators.General import calculate_all_properties

# import core units
from steer_core.Constants.Units import *

# import materials
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

from typing import Tuple, Optional
import numpy as np

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
    >>> print(f"Number of tabs: {collector.number_of_tabs}")
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
        """
        Function to calculate the positions of the tabs along the length of the current collector.
        """
        x_min = self._datum[0] - self._x_foil_length / 2
        x_max = self._datum[0] + self._x_foil_length / 2 + self._tab_spacing

        number_of_tabs = 1
        tab_positions = [x_min + self._tab_spacing / 2]
        tab_starts = [tab_positions[0] - self._tab_width / 2]
        tab_ends = [tab_positions[0] + self._tab_width / 2]

        while tab_positions[-1] < x_max:
            number_of_tabs += 1
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
        return [(round(start * M_TO_MM, 4), np.round(end * M_TO_MM, 4)) for start, end in self._tab_positions]

    @property
    def tab_spacing(self) -> float:
        return np.round(self._tab_spacing * M_TO_MM, 2)

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
        return np.round(self._tab_gap * M_TO_MM, 2)

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
        min = 0.01
        max = 0.5

        return (round(min * M_TO_MM, 2), np.round(max * M_TO_MM, 2))

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        return self.tab_width_hard_range

    @tab_spacing.setter
    @calculate_all_properties
    def tab_spacing(self, tab_spacing: float) -> None:
        self.validate_positive_float(tab_spacing, "tab_spacing")

        self._tab_spacing = float(tab_spacing) * MM_TO_M
        self._tab_gap = self._tab_spacing - self._tab_width

        if self._tab_gap < 0:
            raise ValueError("Tab spacing cannot be less than the tab width.")

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

        # Update internal values
        self._tab_gap = tab_gap_m
        self._tab_spacing = new_tab_spacing

