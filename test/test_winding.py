# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The turn-on-turn winding (``Winding.py``) and the rolls built on it.

Kernel tests wind synthetic stacks so each property can be checked exactly:
every turn rests on the one beneath it (no gap, no overlap, apart from the
short ramps over steps), the first turn rests on the mandrel, layers start and
stop exactly where they do on the strip, and the strip ends at its length.
Assembly tests check the same on reference cells, plus that the dimension
setters' objective measures exactly what the full rebuild does.
"""

import os
import unittest
from copy import deepcopy

import numpy as np

os.environ.setdefault("OPENCELL_ENV", "development")

from steer_opencell_design.Constructions.Cells.Base import _Cell  # noqa: E402
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import (  # noqa: E402
    TapeDriver,
)
from steer_opencell_design.Constructions.ElectrodeAssemblies.Winding import (  # noqa: E402
    RAMP_RUN_PER_RISE,
    TapeSpec,
    racetrack_template,
    round_template,
    wind,
)
from steer_opencell_design.Constructions.Layups.StackProfile import (  # noqa: E402
    build_stack_profile,
)

MM = 1e-3
UM = 1e-6


def _segment(x0, x1):
    """A centre line of one segment from x0 to x1 (m)."""
    return np.array([[x0, 0.0], [x1, 0.0]])


def _support(result):
    """The support under every sample: the turn beneath plus its thickness."""
    p = result.points_per_turn
    a, tc = result.a, result.tc
    sup = np.zeros_like(a)
    m = np.arange(p, a.shape[0])
    sup[p:] = a[m - p] + 0.5 * (tc[m - p] + np.minimum(tc[m - p + 1], np.inf))
    return sup


class TestStackProfile(unittest.TestCase):
    def setUp(self):
        # bottom separator 0-600 mm, electrode 100-500 mm with a skip coat at
        # 200-220 mm, top separator 20-580 mm
        self.profile = build_stack_profile(
            [
                ("electrode", np.array([[0.1, 0], [0.2, 0], [np.nan, np.nan], [0.22, 0], [0.5, 0]]), 150 * UM),
                ("bottom_separator", _segment(0.0, 0.6), 20 * UM),
                ("top_separator", _segment(0.02, 0.58), 20 * UM),
            ]
        )

    def test_breakpoints_are_exact(self):
        np.testing.assert_allclose(
            self.profile.edges, [0, 0.02, 0.1, 0.2, 0.22, 0.5, 0.58, 0.6], atol=1e-15
        )

    def test_thickness_and_offsets(self):
        p = self.profile
        np.testing.assert_allclose(
            p.thickness / UM, [20, 40, 190, 40, 190, 40, 20], atol=1e-9
        )
        # the bottom separator rests on the electrode where it exists
        c = p.names.index("bottom_separator")
        self.assertAlmostEqual(p.offset[c, 2] / UM, 160.0)
        self.assertAlmostEqual(p.offset[c, 3] / UM, 10.0)
        self.assertTrue(np.isnan(p.offset[p.names.index("electrode"), 3]))

    def test_a_layer_counts_up_to_its_end(self):
        p = self.profile
        self.assertAlmostEqual(p.thickness_at(np.array([0.2 - 1e-9]))[0] / UM, 190)
        self.assertAlmostEqual(p.thickness_at(np.array([0.2]))[0] / UM, 40)


class TestWindingKernel(unittest.TestCase):
    def setUp(self):
        # 150 mm separator-only lead-in, 400 mm of electrodes, 80 mm tail
        self.profile = build_stack_profile(
            [
                ("electrodes", _segment(0.15, 0.55), 300 * UM),
                ("bottom_separator", _segment(0.0, 0.63), 25 * UM),
                ("top_separator", _segment(0.0, 0.63), 25 * UM),
            ]
        )
        self.radius = 1.5 * MM
        self.round = wind(self.profile, round_template(self.radius))

    def test_no_turn_overlaps_the_one_beneath(self):
        for result in (self.round, wind(self.profile, racetrack_template(0.4 * MM, 20 * MM))):
            sup = _support(result)
            self.assertTrue(np.all(result.a >= sup - 1e-12))

    def test_turns_pack_tight_away_from_the_ramps(self):
        result = self.round
        sup = _support(result)
        gap = result.a - sup
        p = result.points_per_turn
        loose = np.count_nonzero(gap[p:] > 1 * UM)
        # only the few samples in each step's ramp may stand off their support
        self.assertLess(loose, 0.05 * (gap.shape[0] - p))
        self.assertLessEqual(gap.max(), self.profile.max_thickness + 1e-12)

    def test_the_first_turn_rests_on_the_mandrel(self):
        p = self.round.points_per_turn
        # the end of the first turn may ramp up onto the leading edge
        reach = int(np.ceil(RAMP_RUN_PER_RISE * 50 * UM / (2 * np.pi * self.radius / p))) + 1
        self.assertTrue(np.all(self.round.a[: p - reach] == 0.0))

    def test_the_strip_ends_exactly_at_its_length(self):
        base = self.round.base_path()
        self.assertAlmostEqual(base[-1, 1], self.profile.length, places=12)
        self.assertTrue(np.all(np.diff(base[:, 1]) > 0))

    def test_a_uniform_strip_winds_concentric_turns(self):
        uniform = build_stack_profile([("sep", _segment(0.0, 0.5), 40 * UM)])
        result = wind(uniform, round_template(self.radius))
        p = result.points_per_turn
        # one turn out is one thickness more, everywhere off the leading edge
        steps = result.a[2 * p :] - result.a[p : -p]
        self.assertTrue(np.allclose(np.median(steps), 40 * UM, atol=1e-12))

    def test_layers_start_and_stop_exactly(self):
        path, _ = self.round.layer_path("electrodes")
        finite = path[~np.isnan(path[:, 1]), 1]
        self.assertAlmostEqual(finite.min(), 0.15, places=12)
        self.assertAlmostEqual(finite.max(), 0.55, places=12)

    def test_racetrack_straights_stay_flat(self):
        result = wind(self.profile, racetrack_template(0.4 * MM, 20 * MM))
        t = result.template
        j = np.arange(result.a.shape[0]) % t.points_per_turn
        on_top = (t.nz[j] == 1.0) & (t.nx[j] == 0.0)
        z = t.z[j] + result.a * t.nz[j]
        np.testing.assert_allclose(z[on_top], 0.4 * MM + result.a[on_top], atol=1e-15)

    def test_tape_wraps_and_length(self):
        by_wraps = wind(self.profile, round_template(self.radius), TapeSpec(30 * UM, wraps=3))
        tape, _ = by_wraps.tape_path()
        self.assertAlmostEqual(tape[-1, 5] - tape[0, 5], 3.0, places=6)
        # the strip is wound identically with or without the tape
        np.testing.assert_array_equal(by_wraps.a[: self.round.a.shape[0] - 1], self.round.a[:-1])
        by_length = wind(self.profile, round_template(self.radius), TapeSpec(30 * UM, length=0.05))
        tape, _ = by_length.tape_path()
        self.assertAlmostEqual(tape[-1, 1] - tape[0, 1], 0.05, places=9)

    def test_winding_is_deterministic(self):
        again = wind(deepcopy(self.profile), round_template(self.radius))
        np.testing.assert_array_equal(again.a, self.round.a)
        np.testing.assert_array_equal(again.s, self.round.s)


class TestWoundRolls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.round = _Cell.from_database("TESLA 4680", table_name="teardowns").reference_electrode_assembly
        cls.flat = _Cell.from_database(
            "LFP Flat Wound Prismatic Cell", table_name="cell_references"
        ).reference_electrode_assembly

    def test_round_objective_measures_what_the_rebuild_does(self):
        roll = deepcopy(self.round)
        self.assertGreater(roll.additional_tape_wraps, 0)
        self.assertAlmostEqual(roll._radius_at_length(roll.layup.length), roll.radius, places=9)

    def test_flat_objective_measures_what_the_rebuild_does(self):
        roll = deepcopy(self.flat)
        thickness, width = roll._extents_at_length(roll.layup.length)
        self.assertAlmostEqual(thickness, roll.thickness, places=9)
        self.assertAlmostEqual(width, roll.width, places=9)

    def test_flat_width_setter_hits_its_target(self):
        """#99: the width setter used to land up to ~1.2 mm away."""
        roll = deepcopy(self.flat)
        low, high = roll.width_range
        target = low + 0.6 * (high - low)
        roll.width = target
        # a tightly wound roll's width steps with each wrap: land within a step
        self.assertAlmostEqual(roll.width, target, delta=0.2)

    def test_the_tape_lies_on_the_roll(self):
        roll = deepcopy(self.round)
        winding = roll._winding
        tape_rows = winding.s > winding.strip_length
        self.assertTrue(np.any(tape_rows))
        sup = _support(winding)
        self.assertTrue(np.all(winding.a[tape_rows] >= sup[tape_rows] - 1e-12))

    def test_a_tape_driven_roll_winds_its_tape(self):
        roll = deepcopy(self.round)
        tape = deepcopy(roll.tape)
        tape.length = 300.0
        roll._tape_length_driver = TapeDriver.TAPE_DRIVEN
        roll._additional_tape_wraps = 0
        roll._tape = tape
        roll._calculate_all_properties()
        self.assertIn("tape", roll._component_spirals)
        self.assertGreater(roll.additional_tape_wraps, 0)


if __name__ == "__main__":
    unittest.main()
