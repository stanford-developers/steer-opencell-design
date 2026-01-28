# import core mixins
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Serializer import SerializerMixin

# import core decorators
from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_areas
from steer_core.Decorators.Objects import calculate_weld_tab_properties

# import core units
from steer_core.Constants.Units import *

# import materials
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial

# import other current collector types for class methods
from steer_opencell_design.Components.CurrentCollectors.Base import _TapeCurrentCollector

# import base functions
from typing import Tuple, Optional, Iterable
from copy import deepcopy

# import base packages
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class WeldTab(ValidationMixin, CoordinateMixin, DunderMixin, PlotterMixin, SerializerMixin):
    """
    Specification and modeling class for separately manufactured welded tabs.

    The WeldTab class represents individual tab components that are manufactured
    separately and subsequently welded to current collectors. This design approach
    enables independent optimization of tab materials, geometry, and properties
    while providing sophisticated control over electrical and mechanical
    performance characteristics.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Material specification for the tab component
        Defines electrical, thermal, and mechanical properties
        Must be compatible with welding processes and base collector material
    width : float
        Tab width dimension in mm
        Affects current carrying capacity and mechanical strength
        Typical range: 10-100 mm depending on application requirements
    length : float
        Tab length dimension in mm
        Determines contact area and current distribution characteristics
        Typical range: 5-50 mm for most battery applications
    thickness : float
        Tab thickness in μm
        Critical for electrical resistance and mechanical robustness
        Typical range: 50-500 μm based on current requirements
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm
        Default: (0, 0, 0) - places tab at coordinate system origin

    Examples
    --------
    Create a high-performance copper tab for EV applications:

    >>> from steer_materials import CurrentCollectorMaterial
    >>>
    >>> # Design a robust tab for high current applications
    >>> heavy_duty_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=50.0,          # mm - wide for high current
    ...     length=25.0,         # mm - substantial contact area
    ...     thickness=200.0,     # μm - thick for low resistance
    ...     datum=(0, 0, 0)      # Centered reference
    ... )
    >>>
    >>> print(f"Tab resistance: {heavy_duty_tab.electrical_resistance:.6f} Ω")
    >>> print(f"Tab mass: {heavy_duty_tab.mass:.3f} g")
    >>> print(f"Current capacity: {heavy_duty_tab.current_density_limit * heavy_duty_tab.foil_area/2:.1f} A")

    Create a compact tab for space-constrained applications:

    >>> # Design for minimal size while maintaining performance
    >>> compact_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=20.0,          # mm - compact width
    ...     length=15.0,         # mm - minimal length
    ...     thickness=150.0,     # μm - optimized thickness
    ...     datum=(10, 5, 0)     # Offset positioning
    ... )

    Visualize tab geometry and validate design:

    >>> # Generate visualization plots
    >>> top_view = heavy_duty_tab.get_view(
    ...     title="Heavy Duty Tab - Top View",
    ...     paper_bgcolor='lightgray'
    ... )
    >>> side_view = heavy_duty_tab.get_side_view(
    ...     title="Heavy Duty Tab - Side View"
    ... )
    >>>
    >>> # Validate welding compatibility
    >>> from steer_materials import aluminum_1235_foil
    >>> compatibility = heavy_duty_tab.validate_welding_compatibility(
    ...     aluminum_1235_foil
    ... )
    >>> if not compatibility['suitable']:
    ...     print("Warning: Material incompatibility detected")

    See Also
    --------
    TabWeldedCurrentCollector : Current collector using welded tabs
    CurrentCollectorMaterial : Material specification class
    PunchedCurrentCollector : Alternative integrated tab design
    NotchedCurrentCollector : Multiple integrated tab approach
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        width: float,
        length: float,
        thickness: float,
        datum: Tuple[float, float] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a weld tab used on current collectors

        :param material: CurrentCollectorMaterial: material of the weld tab
        :param width: float: width of the weld tab in mm
        :param length: float: length of the weld tab in mm
        :param thickness: float: thickness of the weld tab in um
        """
        self._update_properties = False

        self.datum = datum
        self.material = material
        self.width = width
        self.length = length
        self.thickness = thickness

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self) -> None:
        self._calculate_coordinates()
        self._calculate_areas()
        self._calculate_bulk_properties()

    def _calculate_bulk_properties(self) -> None:
        """
        Calculate the bulk properties of the tab.
        """
        self._volume = self._foil_area * self._thickness
        volume = self._volume * M_TO_CM**3
        self._material.volume = volume

        self._mass = self._material._mass
        self._cost = self._material._cost

    def _calculate_coordinates(self) -> None:
        """
        Calculate the coordinates of the weld tab based on its dimensions and datum.
        """
        x, y = self.build_square_array(
            self._datum[0] - self._width / 2,
            self._datum[1] - self._length / 2,
            self._width,
            self._length,
        )

        x, y, z, side = self.extrude_footprint(x, y, self._datum, self._thickness)

        self._foil_coordinates = np.column_stack((x, y, z))
        self._foil_coordinates_side = side

    def _calculate_areas(self) -> None:
        # calculate the area of the a side
        foil_a_side_area = self.get_area_from_points(
            self._foil_coordinates[self._foil_coordinates_side == "a"][:, 0],
            self._foil_coordinates[self._foil_coordinates_side == "a"][:, 1],
        )

        # calculate the total upper and lower area of the foil
        self._foil_area = foil_a_side_area * 2

    def _translate(self, vector: Tuple[float, float, float]) -> None:
        self._foil_coordinates += np.array(vector)

    def get_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self.top_down_foil_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    def get_side_view(self, **kwargs) -> go.Figure:
        """
        Returns a Plotly Figure representing the side view of the weld tab.
        """
        figure = go.Figure()
        figure.add_trace(self.right_left_foil_trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def foil_coordinates(self) -> pd.DataFrame:
        return pd.DataFrame(
            np.column_stack((self._foil_coordinates, self._foil_coordinates_side)),
            columns=["x", "y", "z", "side"],
        ).assign(
            x=lambda df: (df["x"].astype(float) * M_TO_MM).round(10),
            y=lambda df: (df["y"].astype(float) * M_TO_MM).round(10),
            z=lambda df: (df["z"].astype(float) * M_TO_MM).round(10),
            side=lambda df: df["side"].astype(str),
        )

    @property
    def right_left_foil_trace(self) -> go.Scatter:
        # get the coordinates of the foil, ordered clockwise
        foil_coordinates = self.order_coordinates_clockwise(self.foil_coordinates, plane="yz")

        # make the foil trace
        foil_trace = go.Scatter(
            x=foil_coordinates["y"],
            y=foil_coordinates["z"],
            mode="lines",
            name="Foil",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Foil",
            showlegend=True,
        )

        return foil_trace

    @property
    def top_down_foil_trace(self) -> go.Scatter:
        # get the side with the maximum z value
        foil_coordinates = self.foil_coordinates.query("z == z.max()")

        # make the foil trace
        foil_trace = go.Scatter(
            x=foil_coordinates["x"],
            y=foil_coordinates["y"],
            mode="lines",
            name="Tab",
            line=dict(color="black", width=1),
            fill="toself",
            fillcolor=self._material.color,
            legendgroup="Tabs",
            showlegend=True,
        )

        return foil_trace

    @property
    def datum(self) -> Tuple[float, float]:
        return (
            np.round(self._datum[0] * M_TO_MM, 2),
            np.round(self._datum[1] * M_TO_MM, 2),
            np.round(self._datum[2] * M_TO_MM, 2),
        )

    @property
    def material(self) -> CurrentCollectorMaterial:
        return self._material

    @property
    def width(self) -> float:
        return np.round(self._width * M_TO_MM, 2)

    @property
    def length(self) -> float:
        return np.round(self._length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        return np.round(self._thickness * M_TO_UM, 2)

    @property
    def volume(self) -> float:
        return np.round(self._volume * M_TO_CM**3, 2)

    @property
    def mass(self) -> float:
        return np.round(self._mass * KG_TO_G, 2)

    @property
    def cost(self) -> float:
        return np.round(self._cost, 2)

    @property
    def foil_area(self) -> float:
        return np.round(self._foil_area * M_TO_MM**2, 2)

    @datum.setter
    def datum(self, datum: Tuple[float, float, float]) -> None:
        # validate the datum
        self.validate_datum(datum)

        if self._update_properties:
            # calculate the translation vector in m
            translation_vector = (
                float(datum[0]) * MM_TO_M - self._datum[0],
                float(datum[1]) * MM_TO_M - self._datum[1],
                float(datum[2]) * MM_TO_M - self._datum[2],
            )

            # translate all coordinates
            self._translate(translation_vector)

        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )

    @material.setter
    @calculate_all_properties
    def material(self, material: CurrentCollectorMaterial) -> None:
        self.validate_type(material, CurrentCollectorMaterial, "material")
        self._material = deepcopy(material)

    @width.setter
    @calculate_all_properties
    def width(self, width: float) -> None:
        self.validate_positive_float(width, "width")
        self._width = float(width) * MM_TO_M

    @thickness.setter
    @calculate_all_properties
    def thickness(self, thickness: float) -> None:
        self.validate_positive_float(thickness, "thickness")
        self._thickness = float(thickness) * UM_TO_M

    @length.setter
    @calculate_all_properties
    def length(self, length: float) -> None:
        self.validate_positive_float(length, "length")
        self._length = float(length) * MM_TO_M


class TabWeldedCurrentCollector(_TapeCurrentCollector):
    """
    Current collector with separately manufactured and welded tabs.

    The tab-welded current collector represents a design approach
    where tabs are manufactured separately and then welded to the main collector
    foil.

    Parameters
    ----------
    material : CurrentCollectorMaterial
        Base material for the current collector foil
        Can be optimized independently from tab material
    length : float
        Total length of the collector foil in mm
        Defines the available space for tab positioning
    width : float
        Width of the collector foil in mm
        Affects current distribution and tab placement options
    thickness : float
        Thickness of the base collector material in μm
        May differ from tab thickness for optimized performance
    weld_tab : WeldTab
        Specification object defining tab geometry, material, and properties
        Encapsulates all tab-specific design parameters
    weld_tab_positions : Iterable[float]
        Array of tab center positions along the length in mm
        Enables precise, flexible tab placement for optimal current distribution
    skip_coat_width : float
        Width of uncoated area around each tab in mm
        Prevents coating interference with welding and ensures reliable connections
    tab_overhang : float
        Distance tabs extend beyond the collector foil edge in mm
        Provides access for external connections and welding operations
    tab_weld_side : str, optional
        Side of collector for tab welding ('a' or 'b', default: 'a')
        Determines which surface receives the welded tabs
    bare_lengths_a_side : tuple of float, optional
        (start, end) uncoated regions on a-side in mm
        Enables hybrid connection strategies combining tabs and tape methods
    bare_lengths_b_side : tuple of float, optional
        (start, end) uncoated regions on b-side in mm
        Provides additional connection flexibility
    name : str, optional
        Descriptive identifier for the collector assembly
    datum : tuple of float, optional
        Reference coordinate system origin (x, y, z) in mm

    Examples
    --------
    Create a high-performance tab-welded collector for an EV application:

    >>> from steer_materials import CurrentCollectorMaterial
    >>>
    >>> # Define the weld tab specification
    >>> weld_tab = WeldTab(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     width=40.0,          # mm - wide for high current
    ...     height=20.0,         # mm
    ...     thickness=100.0      # μm - thick for low resistance
    ... )
    >>>
    >>> # Create collector with optimally positioned tabs
    >>> collector = TabWeldedCurrentCollector(
    ...     material=CurrentCollectorMaterial.from_database('Copper'),
    ...     length=300.0,        # mm
    ...     width=200.0,         # mm
    ...     thickness=15.0,      # μm
    ...     weld_tab=weld_tab,
    ...     weld_tab_positions=[75.0, 150.0, 225.0],  # 3 evenly spaced tabs
    ...     skip_coat_width=45.0,    # mm - larger than tab width
    ...     tab_overhang=18.0,       # mm - accessible for connections
    ...     tab_weld_side='a',
    ...     bare_lengths_a_side=(20.0, 20.0)  # Additional tape connection option
    ... )

    See Also
    --------
    PunchedCurrentCollector : Simpler integrated tab design
    NotchedCurrentCollector : Multiple integrated tabs
    TablessCurrentCollector : No-tab edge connection design
    WeldTab : Specification class for welded tab components
    """

    def __init__(
        self,
        material: CurrentCollectorMaterial,
        length: float,
        width: float,
        thickness: float,
        weld_tab: WeldTab,
        weld_tab_positions: Iterable[float],
        skip_coat_width: float,
        tab_overhang: float,
        tab_weld_side: str = "a",
        bare_lengths_a_side: Tuple[float, float] = (0, 0),
        bare_lengths_b_side: Tuple[float, float] = (0, 0),
        name: Optional[str] = "Tab Welded Current Collector",
        datum: Optional[Tuple[float, float, float]] = (0, 0, 0),
    ) -> None:
        """
        Initialize an object that represents a current collector with tabs welded on it.

        Parameters
        ----------
        material: CurrentCollectorMaterial:
            Material of the current collector.
        length: float:
            Length of the current collector in mm.
        width: float:
            Width of the current collector in mm.
        thickness: float:
            Thickness of the current collector in um.
        weld_tab: WeldTab:
            Weld tab to be used on the current collector.
        weld_tab_positions: Iterable[float]:
            Positions of the weld tabs along the length of the current collector in mm.
        skip_coat_width: float:
            Width of the skip coat area in mm.
        tab_overhang: float:
            Overhang of the weld tab in mm.
        tab_weld_side: str:
            Side of the current collector where the weld tabs are welded ('a' or 'b').
        bare_lengths_a_side: Tuple[float, float]:
            Bare lengths on the A side in mm, as a tuple of two floats (left, right).
        bare_lengths_b_side: Tuple[float, float]:
            Bare lengths on the B side in mm, as a tuple of two floats (left, right).
        name: Optional[str]:
            Name of the current collector, default is 'Tab Welded Current Collector'.
        datum: Optional[Tuple[float, float, float]]:
            Datum of the current collector in mm, default is (0, 0, 0).
        """
        super().__init__(
            material=material,
            x_foil_length=length,
            y_foil_length=width,
            thickness=thickness,
            bare_lengths_a_side=bare_lengths_a_side,
            bare_lengths_b_side=bare_lengths_b_side,
            name=name,
            datum=datum,
        )

        self.weld_tab = weld_tab
        self.tab_overhang = tab_overhang
        self.weld_tab_positions = weld_tab_positions
        self.skip_coat_width = skip_coat_width
        self.tab_weld_side = tab_weld_side

        self._calculate_all_properties()
        self._update_properties = True

    @classmethod
    def from_notched(cls, notched) -> "TabWeldedCurrentCollector":
        """
        Create a TabWeldedCurrentCollector from a NotchedCurrentCollector.
        """
        from steer_opencell_design.Components.CurrentCollectors.Notched import NotchedCurrentCollector

        # validate type
        cls.validate_type(notched, NotchedCurrentCollector, "notched")

        tab = WeldTab(
            material=notched.material,
            width=10,
            length=notched.y_foil_length + notched.tab_height,
            thickness=notched.thickness,
        )

        new_current_collector = cls(
            material=notched.material,
            length=notched.x_foil_length,
            width=notched.y_foil_length + notched.tab_height,
            thickness=notched.thickness,
            weld_tab=tab,
            weld_tab_positions=[
                10,
                notched.x_foil_length / 2,
                notched.x_foil_length - 10,
            ],
            tab_overhang=20,
            skip_coat_width=30,
            tab_weld_side="a",
            bare_lengths_a_side=notched.bare_lengths_a_side,
            bare_lengths_b_side=notched.bare_lengths_b_side,
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
    def from_tabless(cls, tabless) -> "TabWeldedCurrentCollector":
        """
        Create a TabWeldedCurrentCollector from a TablessCurrentCollector.
        """
        from steer_opencell_design.Components.CurrentCollectors.Tabless import TablessCurrentCollector

        # validate type
        cls.validate_type(tabless, TablessCurrentCollector, "tabless")

        tab = WeldTab(
            material=tabless.material,
            width=10,
            length=tabless.y_foil_length + tabless.tab_height,
            thickness=tabless.thickness,
        )

        new_current_collector = cls(
            material=tabless.material,
            length=tabless.x_foil_length,
            width=tabless.y_foil_length + tabless.tab_height,
            thickness=tabless.thickness,
            weld_tab=tab,
            weld_tab_positions=[
                10,
                tabless.x_foil_length / 2,
                tabless.x_foil_length - 10,
            ],
            tab_overhang=20,
            skip_coat_width=30,
            tab_weld_side="a",
            bare_lengths_a_side=tabless.bare_lengths_a_side,
            bare_lengths_b_side=tabless.bare_lengths_b_side,
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

    def _calculate_all_properties(self) -> None:
        self._calculate_weld_tab_properties()
        super()._calculate_all_properties()

    def _calculate_bulk_properties(self) -> None:

        self._volume = self._foil_area / 2 * self._thickness
        volume = self._volume * M_TO_CM**3
        self._material.volume = volume

        self._mass = self._material._mass + sum([t._mass for t in self._weld_tabs])
        self._cost = self._material._cost + sum([t._cost for t in self._weld_tabs])

    def _calculate_weld_tab_properties(self) -> None:
        # copy the weld tabs and set their datums
        self._weld_tabs = []
        for x in self._weld_tab_positions:
            new_weld_tab = deepcopy(self._weld_tab)
            x_datum = (self._datum[0] - self._x_foil_length / 2 + x) * M_TO_MM
            y_datum = (self._datum[1] + self._y_foil_length / 2 + self._tab_overhang - new_weld_tab._length / 2) * M_TO_MM

            if self._tab_weld_side == "a":
                z_datum = (self._datum[2] + self._thickness * UM_TO_MM / 2 + new_weld_tab._thickness * UM_TO_MM / 2) * M_TO_MM
            elif self._tab_weld_side == "b":
                z_datum = (self._datum[2] - self._thickness * UM_TO_MM / 2 - new_weld_tab._thickness * UM_TO_MM / 2) * M_TO_MM

            new_weld_tab.datum = (x_datum, y_datum, z_datum)
            self._weld_tabs.append(new_weld_tab)

    def _get_full_view(self, side="a", aspect_ratio: float = 3, **kwargs) -> go.Figure:
        # Get the base figure from the parent class
        figure = super()._get_full_view(side=side, aspect_ratio=aspect_ratio, **kwargs)

        # Add the weld‐tab traces but group them under one legend entry
        for i, tab in enumerate(self._weld_tabs):
            tr = tab._trace
            tr.legendgroup = "Weld Tabs"
            tr.name = "Weld Tabs"
            tr.showlegend = True if i == 0 else False
            figure.add_trace(tr)

        if side != self._tab_weld_side:
            n = len(self._weld_tabs)
            traces = list(figure.data)
            figure.data = traces[n:] + traces[:n]

        return figure

    def _get_footprint(self, x_indent_start: float = 0, x_indent_end: float = 0) -> Tuple[np.ndarray, np.ndarray]:
        return self.build_square_array(
            x_width=self._x_foil_length - x_indent_start - x_indent_end,
            y_width=self._y_foil_length,
            x=self._datum[0] - self._x_foil_length / 2 + x_indent_start,
            y=self._datum[1] - self._y_foil_length / 2,
        )

    def _get_coated_area_coordinates(self, side: str = "a") -> Tuple[go.Scatter, float]:
        if side not in ["a", "b"]:
            raise ValueError("Side must be 'a' or 'b'.")

        x_indent_start = self._bare_lengths_a_side[0] if side == "a" else self._bare_lengths_b_side[0]
        x_indent_end = self._bare_lengths_a_side[1] if side == "a" else self._bare_lengths_b_side[1]
        x, y = self._get_footprint(x_indent_start=x_indent_start, x_indent_end=x_indent_end)

        weld_tab_positions = np.array([t._datum[0] for t in self._weld_tabs])

        x, y = self.remove_skip_coat_area(x, y, weld_tab_positions, self._skip_coat_width)

        # Get the indices of the foil coordinates for the specified side
        idx = np.where(self._foil_coordinates_side == side)[0]

        # get the z value from the foil coordinates for this side
        z_value = self._foil_coordinates[idx[0], 2]

        # Create z array
        z = np.full_like(x, z_value)

        # Combine into (N, 3) array
        coated_area = np.column_stack((x, y, z))

        return coated_area

    def _get_a_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side="a")

    def _get_b_side_coated_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_coated_area_trace(side="b")

    def _get_insulation_coordinates(self, side: str = "a") -> np.ndarray:
        """
        Return empty insulation coordinates for TabWeldedCurrentCollector.

        TabWeldedCurrentCollectors don't have traditional insulation areas
        since they use welded tabs instead.

        Parameters
        ----------
        side : str
            Side of the current collector ('a' or 'b')

        Returns
        -------
        np.ndarray
            Empty array with shape (0, 3) representing no insulation coordinates
        """
        return np.empty((0, 3))

    def _get_a_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()

    def _get_b_side_insulation_area_trace(self) -> Tuple[go.Scatter, float]:
        return self._get_insulation_area_trace()

    @property
    def weld_tab_positions(self) -> list:
        """
        Returns the positions of the weld tabs along the length of the current collector in mm.
        """
        return [round(pos * M_TO_MM, 2) for pos in self._weld_tab_positions]

    @property
    def skip_coat_width(self) -> float:
        """
        Returns the width of the skip coat area in mm.
        """
        return np.round(self._skip_coat_width * M_TO_MM, 2)

    @property
    def skip_coat_width_range(self) -> Tuple[float, float]:
        """
        Get the skip coat width range in mm.
        """
        return (self._weld_tabs[0].width, 100)

    @property
    def skip_coat_width_hard_range(self) -> Tuple[float, float]:
        """
        Get the skip coat width range in mm.
        """
        return (self._weld_tabs[0].width, 1000)

    @property
    def tab_weld_side(self) -> str:
        """
        Returns the side of the current collector where the weld tabs are located ('a' or 'b').
        """
        return self._tab_weld_side

    @property
    def tab_overhang(self) -> float:
        """
        Returns the overhang of the weld tab on the current collector in mm.
        """
        return np.round(self._tab_overhang * M_TO_MM, 2)

    @property
    def tab_overhang_range(self) -> Tuple[float, float]:
        """
        Returns the overhang range of the weld tab in mm.
        """
        return (0, self.weld_tab.length / 2)

    @property
    def tab_overhang_hard_range(self) -> Tuple[float, float]:
        return (0, self.weld_tab.length)

    @property
    def weld_tab(self) -> list:
        """
        Returns a list of WeldTab objects representing the weld tabs on the current collector.
        """
        return self._weld_tab

    @property
    def weld_tabs(self) -> list:
        """
        Returns a list of WeldTab objects representing the weld tabs on the current collector.
        """
        return self._weld_tabs

    @property
    def tab_width(self) -> float:
        """
        Returns the width of the weld tab in mm.
        """
        return self.weld_tab.width

    @property
    def tab_width_range(self) -> Tuple[float, float]:
        """
        Returns the width range of the weld tab in mm.
        """
        return (1, self.skip_coat_width)

    @property
    def tab_width_hard_range(self) -> Tuple[float, float]:
        return self.tab_width_range

    @property
    def tab_length(self) -> float:
        """
        Returns the length of the weld tab in mm.
        """
        return self.weld_tab.length

    @property
    def tab_length_range(self) -> Tuple[float, float]:
        """
        Returns the length range of the weld tab in mm.
        """
        return (self.tab_overhang, self.y_foil_length + self.tab_overhang)

    @property
    def tab_length_hard_range(self) -> Tuple[float, float]:
        return self.tab_length_range

    @property
    def tab_positions_text(self) -> str:
        """
        Returns the weld tab positions as a formatted string in mm.

        Returns
        -------
        str
            Comma-separated string of tab positions (e.g., "75.0, 150.0, 225.0")
        """
        positions = [str(round(pos * M_TO_MM, 2)) for pos in self._weld_tab_positions]
        return ", ".join(positions)

    @tab_positions_text.setter
    def tab_positions_text(self, positions_text: str) -> None:
        """
        Set weld tab positions from a formatted string.

        Parameters
        ----------
        positions_text : str
            Comma-separated string of tab positions in mm
            Examples: "75.0, 150.0, 225.0" or "10,50,100" or "25.5, 75.25, 125"

        Raises
        ------
        ValueError
            If the string cannot be parsed into valid numbers
        """
        try:
            # Split by comma and strip whitespace
            position_strings = [s.strip() for s in positions_text.split(",")]

            # Filter out empty strings
            position_strings = [s for s in position_strings if s]

            if not position_strings:
                raise ValueError("No valid positions found in the input string")

            # Convert to float list
            positions_list = [float(pos) for pos in position_strings]

            # Use the existing setter for validation and conversion
            self.weld_tab_positions = positions_list

        except ValueError as e:
            if "could not convert string to float" in str(e):
                raise ValueError(f"Invalid number format in tab positions: '{positions_text}'. Use comma-separated numbers like '75.0, 150.0, 225.0'")
            else:
                raise  # Re-raise other ValueError from weld_tab_positions setter

    @tab_overhang.setter
    @calculate_weld_tab_properties
    def tab_overhang(self, tab_overhang: float) -> None:
        """
        Set the overhang of the weld tab on the current collector.

        Parameters
        ----------
        tab_overhang : float
            The overhang of the weld tab in mm.
        """
        self.validate_positive_float(tab_overhang, "tab_overhang")

        # Convert to internal units (meters)
        self._tab_overhang = float(tab_overhang) * MM_TO_M

        if self._tab_overhang > self.weld_tab.length / 2:
            raise ValueError("Tab overhang cannot be greater than half the length of the weld tab.")

    @tab_width.setter
    @calculate_all_properties
    def tab_width(self, tab_width: float) -> None:
        self.validate_positive_float(tab_width, "tab_width")
        self.weld_tab.width = tab_width

    @tab_length.setter
    @calculate_all_properties
    def tab_length(self, tab_length: float) -> None:
        self.validate_positive_float(tab_length, "tab_length")

        if tab_length < self.tab_overhang:
            raise ValueError("Tab length cannot be less than the tab overhang.")

        self.weld_tab.length = tab_length

    @weld_tab.setter
    @calculate_all_properties
    def weld_tab(self, weld_tab: WeldTab) -> None:
        self.validate_type(weld_tab, WeldTab, "weld_tab")
        self._weld_tab = weld_tab

    @weld_tab_positions.setter
    @calculate_all_properties
    def weld_tab_positions(self, weld_tab_positions: Iterable[float]) -> None:

        self.validate_type(weld_tab_positions, Iterable, "weld_tab_positions")

        if any(pos > self.x_foil_length for pos in weld_tab_positions):
            raise ValueError("Weld tab positions cannot be greater than the length of the current collector.")

        self._weld_tab_positions = [float(pos) * MM_TO_M for pos in sorted(weld_tab_positions)]

    @tab_overhang.setter
    @calculate_weld_tab_properties
    def tab_overhang(self, tab_overhang: float) -> None:
        self.validate_positive_float(tab_overhang, "tab_overhang")
        self._tab_overhang = float(tab_overhang) * MM_TO_M

    @skip_coat_width.setter
    @calculate_areas
    def skip_coat_width(self, skip_coat_width: float) -> None:
        self.validate_positive_float(skip_coat_width, "skip_coat_width")

        if skip_coat_width < self._weld_tab._width / 2:
            self._skip_coat_width = self._weld_tab._width
        else:
            self._skip_coat_width = float(skip_coat_width) * MM_TO_M

        if self._skip_coat_width > self._x_foil_length:
            raise ValueError("Skip coat width cannot be greater than the length of the current collector.")

    @tab_weld_side.setter
    @calculate_weld_tab_properties
    def tab_weld_side(self, tab_weld_side: str) -> None:
        if tab_weld_side not in ["a", "b"]:
            raise ValueError("Tab weld side must be either 'a' or 'b'.")

        self._tab_weld_side = tab_weld_side

