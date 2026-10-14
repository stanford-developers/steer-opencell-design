# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Regression tests for ranges that did not match what the setters enforce (1.3.3).

``test_range_contract`` checks every bound generically; these pin the specific
behaviours behind each fix, so a regression names what broke.
"""

import unittest
import warnings
from copy import deepcopy

from steer_opencell_design.Components.Electrodes import ElectrodeControlMode
from steer_opencell_design.Components.CurrentCollectors.Tabbed import (
    TAB_WELD_MIN_LENGTH,
)
from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment import (
    FlatMandrel,
)


def _load(name, table="cell_references"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _Cell.from_database(name, table_name=table)


class TestPouchTerminalFollowsItsTab(unittest.TestCase):
    """The reported bug: a narrowed pouch's terminal slider kept its old range."""

    @classmethod
    def setUpClass(cls):
        cls.base = _load("NMC811 Stacked Pouch Cell")

    def setUp(self):
        self.cell = deepcopy(self.base)

    def test_range_is_the_tab_width_after_narrowing(self):
        self.cell.width = self.cell.width_range[0] + 5
        terminal = self.cell.encapsulation.cathode_terminal
        tab_width = self.cell._terminal_tab_width("cathode") * 1e3
        self.assertLess(tab_width, 50.0)
        self.assertAlmostEqual(terminal.width_range[1], tab_width, places=9)
        self.assertAlmostEqual(terminal.width, tab_width, places=9)

    def test_a_wider_terminal_is_capped_at_the_tab(self):
        self.cell.width = self.cell.width_range[0] + 5
        terminal = self.cell.encapsulation.cathode_terminal
        terminal.width = 500
        self.assertAlmostEqual(terminal.width, terminal.width_range[1], places=9)

    def test_widening_the_cell_restores_the_requested_width(self):
        before = self.cell.encapsulation.cathode_terminal.width
        self.cell.width = self.cell.width_range[0] + 5
        self.cell.width = self.base.width
        self.assertAlmostEqual(
            self.cell.encapsulation.cathode_terminal.width, before, places=9
        )


class TestPunchedTabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load("NMC811 Stacked Pouch Cell")

    def setUp(self):
        layup = deepcopy(self.base)._reference_electrode_assembly._layup
        self.cathode = layup._cathode._current_collector
        self.anode = layup._anode._current_collector

    def test_tab_width_reaches_its_two_millimetre_minimum(self):
        self.assertEqual(self.cathode.tab_width_range[0], 2.0)
        self.cathode.tab_width = 2.0
        self.assertAlmostEqual(self.cathode.tab_width, 2.0, places=9)

    def test_the_edited_tab_yields_to_the_other_on_its_edge(self):
        anode_width = self.anode.tab_width
        room = self.cathode.tab_width_range[1]
        self.cathode.tab_width = room + 1  # past the room, still on the foil
        self.assertAlmostEqual(self.cathode.tab_width, room, places=6)
        self.assertAlmostEqual(self.anode.tab_width, anode_width, places=9)

    def test_tab_position_clamps_to_its_range(self):
        low, high = self.cathode.tab_position_range
        self.cathode.tab_position = high + 50
        self.assertAlmostEqual(self.cathode.tab_position, high, places=6)


class TestTabWeldedCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load("NMC811 Cylindrical Tabbed Cell")

    def setUp(self):
        cell = deepcopy(self.base)
        self.collector = (
            cell._reference_electrode_assembly._layup._cathode._current_collector
        )

    def test_overhang_leaves_the_tab_welded(self):
        length = self.collector.weld_tab.length
        self.assertEqual(
            self.collector.tab_overhang_hard_range[1], length - TAB_WELD_MIN_LENGTH
        )
        self.collector.tab_overhang = length  # was accepted: the check compared m to mm
        self.assertAlmostEqual(
            self.collector.tab_overhang, length - TAB_WELD_MIN_LENGTH, places=9
        )

    def test_tab_length_stays_past_the_overhang(self):
        self.assertAlmostEqual(
            self.collector.tab_length_range[0],
            self.collector.tab_overhang + TAB_WELD_MIN_LENGTH,
            places=9,
        )

    def test_skip_coat_is_never_narrower_than_the_tab(self):
        tab_width = self.collector.tab_width
        self.collector.skip_coat_width = (
            tab_width * 0.75
        )  # was kept: the check compared mm to m
        self.assertAlmostEqual(self.collector.skip_coat_width, tab_width, places=9)
        self.assertEqual(self.collector.skip_coat_width_range[0], tab_width)

    def test_tab_width_is_capped_by_the_skip_coat(self):
        self.collector.tab_width = self.collector.skip_coat_width + 10
        self.assertAlmostEqual(
            self.collector.tab_width, self.collector.skip_coat_width, places=9
        )


class TestCylindricalEncapsulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load("NMC811 Cylindrical Tabbed Cell")

    def setUp(self):
        self.encapsulation = deepcopy(self.base).encapsulation

    def test_a_radius_edit_keeps_the_connector_ratio(self):
        connector = self.encapsulation._cathode_terminal_connector
        ratio = connector.radius / self.encapsulation._canister.inner_radius
        self.encapsulation.radius = self.encapsulation.radius + 2
        self.assertAlmostEqual(
            connector.radius / self.encapsulation._canister.inner_radius,
            ratio,
            places=6,
        )

    def test_connector_radius_range_is_live(self):
        self.encapsulation.radius = self.encapsulation.radius + 2
        connector = self.encapsulation._cathode_terminal_connector
        self.assertAlmostEqual(
            connector.radius_range[1],
            self.encapsulation._canister.inner_radius,
            places=9,
        )

    def test_canister_keeps_room_inside(self):
        canister = self.encapsulation._canister
        canister.height = canister.height_hard_range[0]
        self.assertGreaterEqual(self.encapsulation.internal_height, 1.0 - 1e-9)
        canister.outer_radius = canister.outer_radius_hard_range[0]
        self.assertGreaterEqual(canister.inner_radius, 1.0 - 1e-9)


class TestPrismatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load("LFP Flat Wound Prismatic Cell")

    def setUp(self):
        self.cell = deepcopy(self.base)

    def test_canister_soft_ranges_lie_within_the_hard_ones(self):
        canister = self.cell.encapsulation._canister
        for name in ("width", "length", "height"):
            soft, hard = getattr(canister, f"{name}_range"), getattr(
                canister, f"{name}_hard_range"
            )
            self.assertLessEqual(hard[0], soft[0], name)
            self.assertLessEqual(soft[1], hard[1], name)

    def test_encapsulation_floors_keep_room_inside(self):
        encapsulation = self.cell.encapsulation
        for name in ("width", "height", "length"):
            copy = deepcopy(encapsulation)
            setattr(copy, name, getattr(copy, f"{name}_hard_range")[0])
            self.assertGreaterEqual(
                min(copy.internal_width, copy.internal_height, copy.internal_length),
                1.0 - 1e-9,
                name,
            )

    def test_flat_roll_cell_width_is_the_encapsulation_width(self):
        self.assertAlmostEqual(self.cell.width, self.cell.encapsulation.width, places=9)

    def test_flat_mandrel_reports_a_hard_width_range(self):
        mandrel = self.cell._reference_electrode_assembly._mandrel
        self.assertIsInstance(mandrel, FlatMandrel)
        self.assertEqual(
            mandrel.width_hard_range, (mandrel.height * 2, mandrel.height * 80)
        )


class TestClippedTab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load("NMC811 Stacked Pouch Cell")

    def test_the_clip_follows_a_shortened_tab_and_comes_back(self):
        cell = deepcopy(self.base)
        requested = cell.clipped_tab_length
        for name in ("_cathode", "_anode"):
            collector = getattr(
                cell._reference_electrode_assembly._layup, name
            )._current_collector
            collector._tab_height = (requested / 2) * 1e-3
        self.assertAlmostEqual(cell.clipped_tab_length, requested / 2, places=9)
        for name in ("_cathode", "_anode"):
            collector = getattr(
                cell._reference_electrode_assembly._layup, name
            )._current_collector
            collector._tab_height = (requested * 3) * 1e-3
        self.assertAlmostEqual(cell.clipped_tab_length, requested, places=9)


class TestCoatingRanges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = _load(
            "NMC811 Stacked Pouch Cell"
        )._reference_electrode_assembly._layup._cathode

    def test_fixed_thickness_loading_keeps_porosity_in_bounds(self):
        electrode = deepcopy(self.base)
        electrode.control_mode = ElectrodeControlMode.MAINTAIN_COATING_THICKNESS
        thickness = electrode.coating_thickness
        electrode.mass_loading = electrode.mass_loading_hard_range[1]
        self.assertAlmostEqual(electrode.coating_thickness, thickness, places=9)
        self.assertGreaterEqual(electrode.porosity, -1e-9)

    def test_fixed_density_loading_keeps_thickness_in_bounds(self):
        electrode = deepcopy(self.base)
        electrode.control_mode = ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY
        electrode.mass_loading = electrode.mass_loading_range[1]
        self.assertAlmostEqual(electrode.coating_thickness, 200.0, places=6)

    def test_porosity_range_is_the_density_range(self):
        electrode = deepcopy(self.base)
        low, high = electrode.porosity_range
        electrode.porosity = high
        self.assertAlmostEqual(
            electrode.calender_density, electrode.calender_density_range[0], places=9
        )


class TestOverhangsAndRatios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tesla = _load("TESLA 4680", table="teardowns")

    def test_np_ratio_bounds_are_reachable(self):
        layup = deepcopy(self.tesla)._reference_electrode_assembly._layup
        for bound in layup.np_ratio_range:
            copy = deepcopy(layup)
            copy.np_ratio = bound
            self.assertAlmostEqual(copy.np_ratio, bound, places=6)


if __name__ == "__main__":
    unittest.main()
