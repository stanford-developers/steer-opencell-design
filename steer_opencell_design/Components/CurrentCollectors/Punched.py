# import core units
from steer_core.Constants.Units import *

# import materials
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

# import base packages
import plotly.graph_objects as go
from typing import Tuple, Optional
import numpy as np

from steer_opencell_design.Components.CurrentCollectors.Base import _TabbedCurrentCollector


class PunchedCurrentCollector(_TabbedCurrentCollector):
    """
    Simple rectangular current collector with a single integrated tab.

    The punched current collector is the most common and straightforward
    collector design, featuring a rectangular foil with a single tab
    extending from one edge. This design is widely used in
    prismatic and pouch cell formats due to its simplicity,
    manufacturing efficiency, and reliable electrical performance.

    Key characteristics:
    - Simple rectangular geometry with minimal complexity
    - Single tab for electrical connection
    - Configurable tab position along the width
    - Suitable for high-volume manufacturing
    - Compatible with standard coating and assembly processes

    This collector type is particularly well-suited for:
    - Z-fold electrode assemblies
    - Flat sheet cell constructions
    - Applications requiring simple, cost-effective designs
    - Automated manufacturing processes

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material composition defining electrical and mechanical properties
        Common materials: aluminum foil (cathode), copper foil (anode)
    width : float
        Total width of the collector foil in mm
        Typical range: 50-300 mm depending on cell capacity
    height : float
        Total height of the collector foil in mm
        Typical range: 50-500 mm depending on cell format
    thickness : float
        Material thickness in micrometers (μm)
        Typical range: 6-20 μm (Al), 8-35 μm (Cu)
    tab_width : float
        Width of the protruding tab in mm
        Typical range: 10-50 mm based on current requirements
        Should be optimized for current density and welding requirements
    tab_height : float
        Extension height of the tab beyond the foil in mm
        Typical range: 5-25 mm for manufacturing and assembly accessibility
    tab_position : float
        Horizontal position of the tab center from the left edge in mm
        Range: tab_width/2 to (width - tab_width/2)
        Central positioning (width/2) provides optimal current distribution
    coated_tab_height : float, optional
        Height of active material coating on the tab in mm (default: 0)
        Must be less than tab_height to provide bare connection area
        Set to 0 for completely uncoated tabs
    insulation_width : float, optional
        Width of insulation strip around the perimeter in mm (default: 0)
        Helps prevent short circuits and improves safety
    name : str, optional
        Descriptive name for identification
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Attributes
    ----------
    foil_area : float
        Surface area of the rectangular foil excluding tab (mm²)
    tab_area : float
        Surface area of the tab extension (mm²)
    total_area : float
        Combined surface area of foil and tab (mm²)
    coated_area : float
        Area available for active material coating (mm²)
    current_density : float
        Current density through the tab connection (A/mm²)
    resistance : float
        Electrical resistance from foil center to tab (Ω)

    Methods
    -------
    get_footprint()
        Returns the 2D outline coordinates of the collector
    get_a_side_view()
        Generates plotly figure of the collector from above
    get_properties()
        Returns dictionary of all geometric and electrical properties

    Examples
    --------
    Create a standard punched cathode current collector:

    >>> from steer_materials import aluminum_foil_12um
    >>> collector = PunchedCurrentCollector(
    ...     material=aluminum_foil_12um,
    ...     width=150.0,      # mm
    ...     height=200.0,     # mm
    ...     thickness=12.0,   # μm
    ...     tab_width=25.0,   # mm
    ...     tab_height=10.0,  # mm
    ...     tab_position=75.0 # mm (centered)
    ... )
    >>> print(f"Coated area: {collector.coated_area:.1f} mm²")
    >>> print(f"Tab current density at 10A: {10/collector.tab_area:.2f} A/mm²")

    Create an anode collector with coated tab:

    >>> from steer_materials import CurrentCollectorMaterial
    >>> anode_collector = PunchedCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Aluminum'),
    ...     width=152.0,      # Slightly larger than cathode
    ...     height=202.0,
    ...     thickness=10.0,
    ...     tab_width=20.0,
    ...     tab_height=12.0,
    ...     tab_position=74.0,
    ...     coated_tab_height=8.0  # Partial coating on tab
    ... )

    Visualize the collector geometry:

    >>> fig = collector.get_a_side_view()
    >>> fig.show()  # Interactive plotly visualization

    See Also
    --------
    NotchedCurrentCollector : Collector with cutout features for tape connections
    TablessCurrentCollector : Collector without protruding tabs
    TabWeldedCurrentCollector : Collector with separately welded tabs
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        width: float,
        height: float,
        thickness: float,
        tab_width: float,
        tab_height: float,
        tab_position: float,
        coated_tab_height: float = 0,
        insulation_width: Optional[float] = 0,
        name: Optional[str] = "Punched Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a punched current collector.

        Parameters
        ----------
        material: CurrentCollectorMaterial
            Material of the current collector.
        width: float
            Length of the current collector in mm.
        height: float
            Width of the current collector in mm.
        tab_width: float
            Width of the tab in mm.
        tab_height: float
            Height of the tab in mm.
        tab_position: float
            Position of the tab in mm, relative to the left edge of the current collector.
        coated_tab_height: float
            Height of the coated tab on the top side in mm, default is 0.
        thickness: float
            Thickness of the current collector in um.
        insulation_width: Optional[float]
            Width of the insulation in mm, default is 0.
        name: Optional[str]
            Name of the current collector, default is 'Punched Current Collector'.
        datum: Optional[Tuple[float, float, float]]
            Datum of the current collector in mm, default is (0, 0, 0).
        """
        super().__init__(
            material=material,
            x_foil_length=width,
            y_foil_length=height,
            tab_width=tab_width,
            tab_height=tab_height,
            coated_tab_height=coated_tab_height,
            thickness=thickness,
            insulation_width=insulation_width,
            name=name,
            datum=datum,
        )

        self.tab_position = tab_position
        self._calculate_all_properties()
        self._update_properties = True

    def _get_footprint(
        self,
        notch_height: float = None,
        y_depth: float = None,
        y_start: float = 0,
    ) -> np.ndarray:
        """
        Get the footprint of the current collector as a NumPy array of shape (N, 2).
        Each row is a (x, y) coordinate.
        """
        # Cache attribute access
        x_len = self._x_foil_length
        y_len = self._y_foil_length
        tab_pos = self._tab_position
        tab_width = self._tab_width
        datum_x, datum_y, _ = self._datum

        y_depth = y_len if y_depth is None else y_depth
        notch_height = self._tab_height if notch_height is None else notch_height

        start_x = datum_x - x_len / 2
        start_y = datum_y - y_len / 2 + y_start

        x_steps = np.array(
            [
                0,
                tab_pos - tab_width / 2,
                0,
                tab_width,
                0,
                x_len - tab_pos - tab_width / 2,
                0,
                -x_len,
            ]
        )

        y_steps = np.array([y_depth, 0, notch_height, 0, -notch_height, 0, -y_depth, 0])

        # Cumulative sum to get coordinates
        x_coords = np.cumsum(np.insert(x_steps, 0, start_x))
        y_coords = np.cumsum(np.insert(y_steps, 0, start_y))

        return x_coords, y_coords

    def _get_insulation_coordinates(self, side: str) -> np.ndarray:
        """
        Returns a NumPy array representing the insulation area.
        The shape depends on whether the insulation is entirely above, below,
        or straddling the foil length. Output columns are ['x', 'y', 'z', 'side'].
        """
        if self._insulation_width == 0:
            return np.empty((0, 3))

        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        _y_insulation_start = self._datum[1] + self._y_foil_length / 2 + self._coated_tab_height - self._insulation_width
        _y_insulation_end = _y_insulation_start + self._insulation_width

        # Determine which case applies
        if _y_insulation_start > self._datum[1] + self._y_foil_length / 2:
            x0 = self._datum[0] - self._x_foil_length / 2 + self._tab_position - self._tab_width / 2
            y0 = _y_insulation_start

            x, y = self.build_square_array(x=x0, y=y0, x_width=self._tab_width, y_width=self._insulation_width)

        elif np.round(_y_insulation_end, 10) <= np.round(self._datum[1] + self._y_foil_length / 2, 10):
            x0 = self._datum[0] - self._x_foil_length / 2
            y0 = _y_insulation_start

            x, y = self.build_square_array(x=x0, y=y0, x_width=self._x_foil_length, y_width=self._insulation_width)

        else:
            notch_height = _y_insulation_end - (self._datum[1] + self._y_foil_length / 2)
            y_depth = (self._datum[1] + self._y_foil_length / 2) - _y_insulation_start
            y_start = self._y_foil_length + self._coated_tab_height - self._insulation_width

            x, y = self._get_footprint(notch_height=notch_height, y_depth=y_depth, y_start=y_start)

        # Get z-coordinate from foil coordinates for this side
        idx = np.where(self._foil_coordinates_side == side)[0]

        if len(idx) == 0:
            raise ValueError(f"No foil coordinates found for side '{side}'")

        z_val = self._foil_coordinates[idx[0], 2]

        # Create z and side columns
        z = np.full_like(x, z_val)

        # Stack into final (N, 4) array
        return np.column_stack((x, y, z))

    def rotate_90(self) -> None:
        """
        Rotate the current collector by 90 degrees in the clockwise direction.
        """
        # Keep datum as the center of rotation - don't move it to origin
        # Rotate coordinates around the current datum position
        self._foil_coordinates = self.rotate_coordinates(self._foil_coordinates, "z", -90, center=self._datum)
        self._a_side_coated_coordinates = self.rotate_coordinates(self._a_side_coated_coordinates, "z", -90, center=self._datum)
        self._b_side_coated_coordinates = self.rotate_coordinates(self._b_side_coated_coordinates, "z", -90, center=self._datum)

        if hasattr(self, "_a_side_insulation_coordinates"):
            self._a_side_insulation_coordinates = self.rotate_coordinates(self._a_side_insulation_coordinates, "z", -90, center=self._datum)
        if hasattr(self, "_b_side_insulation_coordinates"):
            self._b_side_insulation_coordinates = self.rotate_coordinates(self._b_side_insulation_coordinates, "z", -90, center=self._datum)

        if hasattr(self, "_weld_tabs"):
            for tab in self._weld_tabs:
                tab._foil_coordinates = self.rotate_coordinates(tab._foil_coordinates, "z", -90, center=self._datum)
                tab_datum_array = np.array([[tab._datum[0], tab._datum[1], tab._datum[2]]])
                rotated_datum = self.rotate_coordinates(tab_datum_array, "z", -90, center=self._datum)
                tab._datum = tuple(rotated_datum[0])

        return self

    @property
    def x_foil_length_range(self) -> Tuple[float, float]:

        if hasattr(self, "_x_foil_length_range") and self._x_foil_length_range is not None:

            return (
                np.round(self._x_foil_length_range[0] * M_TO_MM, 2),
                np.round(self._x_foil_length_range[1] * M_TO_MM, 2),
            )

        else:
            return (10, 500)

    @property
    def y_foil_length_range(self) -> Tuple[float, float]:
        if hasattr(self, "_y_foil_length_range") and self._y_foil_length_range is not None:
            return (
                np.round(self._y_foil_length_range[0] * M_TO_MM, 2),
                np.round(self._y_foil_length_range[1] * M_TO_MM, 2),
            )
        else:
            return (10, 500)

    @property
    def mass_range(self) -> Tuple[float, float]:
        min = 0
        hyp_max = 0.1
        max = hyp_max * (1 - np.exp(-0.5 / self._mass))

        return (round(min * KG_TO_G, 2), np.round(max * KG_TO_G, 2))

    @property
    def width(self) -> float:
        return self.x_foil_length

    @property
    def width_range(self) -> Tuple[float, float]:
        return self.x_foil_length_range

    @property
    def height(self) -> float:
        return self.y_foil_length

    @property
    def height_range(self) -> Tuple[float, float]:
        return self.y_foil_length_range

    @property
    def height_hard_range(self) -> Tuple[float, float]:
        return (0, 5000)

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        min = 0.01
        max = self._x_foil_length - 0.01

        return (round(min * M_TO_MM, 2), np.round(max * M_TO_MM, 2))

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        return self.tab_width_hard_range

    @property
    def tab_position(self) -> float:
        return np.round(self._tab_position * M_TO_MM, 1)

    @tab_position.setter
    def tab_position(self, tab_position: float) -> None:
        self.validate_positive_float(tab_position, "tab_position")

        self._tab_position = float(tab_position) * MM_TO_M

        if self._tab_position - self._tab_width / 2 < 0:
            raise ValueError("Tab position cannot be less than half the tab width.")

        if self._tab_position + self._tab_width / 2 > self.x_foil_length:
            raise ValueError("Tab position plus half the tab width cannot be greater than the length of the current collector.")

        if self._update_properties:
            self._calculate_coordinates()

    @width.setter
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self.x_foil_length = width

    @height.setter
    def height(self, height: float) -> None:
        self.validate_positive_float(height, "height")
        self.y_foil_length = height

