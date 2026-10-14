# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The turn-on-turn winding (``Winding.py``) and the rolls built on it.

Kernel tests wind synthetic stacks so each property can be checked exactly:
every turn rests on the one beneath it (no gap, no overlap, apart from where it
spans taut over a step), a span over a step touches down at the step's horizon,
the first turn rests on the mandrel, layers drape over the layers beneath them
instead of jumping, layers start and stop exactly where they do on the strip,
and the strip ends at its length.
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
    """The support under every sample: the turn beneath plus its stack top."""
    p = result.points_per_turn
    sup = np.zeros_like(result.a)
    sup[p:] = result.a[:-p] + result.H[:-p]
    return sup


def _horizon_run(radius, rise):
    """Arc (on the surface) from a step of height ``rise`` to where a taut strip
    leaving its top touches a surface of radius ``radius``."""
    return radius * np.arccos(radius / (radius + rise))


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
        # the end of the first turn spans taut up onto the leading edge
        spacing = 2 * np.pi * self.radius / p
        reach = int(np.ceil(_horizon_run(self.radius, 50 * UM) / spacing)) + 1
        self.assertTrue(np.all(self.round.a[: p - reach] == 0.0))
        self.assertGreater(self.round.a[p - 1], 0.0)

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

    def test_a_span_touches_down_at_the_steps_horizon(self):
        """A layer starting on top of the stack is a step the next turn spans;
        it leaves the surface at the horizon, closer to the step near the core."""
        for radius in (1.5 * MM, 12 * MM):
            profile = build_stack_profile(
                [("base", _segment(0.0, 0.8), 50 * UM), ("top", _segment(0.4, 0.8), 200 * UM)]
            )
            result = wind(profile, round_template(radius))
            p = result.points_per_turn
            sup = _support(result)
            corner = result.corner_f[0] + p  # where the next turn meets the step
            i_c = int(np.ceil(corner))
            lifted = np.flatnonzero(result.a[:i_c] > sup[:i_c] + 1e-9)
            first = lifted[lifted > i_c - p // 2].min()
            rho = radius + sup[i_c - 1]
            spacing = 2 * np.pi * rho / p
            run = (corner - first) * spacing
            self.assertAlmostEqual(run, _horizon_run(rho, 200 * UM), delta=1.5 * spacing)

    def test_a_span_over_a_step_on_a_straight_reaches_the_curve(self):
        """On a racetrack's straight the horizon is the straight's end: the span
        from a step up on a straight starts back on the preceding curve."""
        profile = build_stack_profile(
            [("base", _segment(0.0, 0.9), 50 * UM), ("top", _segment(0.5, 0.9), 200 * UM)]
        )
        template = racetrack_template(0.5 * MM, 30 * MM)
        result = wind(profile, template)
        p = result.points_per_turn
        sup = _support(result)
        corner = result.corner_f[0] + p
        i_c = int(np.ceil(corner))
        j = (i_c - 1) % p
        self.assertEqual(abs(template.nz[j]), 1.0)  # the step lies on a straight
        n_c = template.n_curve
        # walk back along the straight to its start: every sample is lifted
        k = i_c - 1
        while abs(template.nz[k % p]) == 1.0 and template.nx[k % p] == 0.0:
            self.assertGreater(result.a[k], sup[k] + 1e-9)
            k -= 1
        self.assertLess(k, i_c - 1)
        self.assertGreaterEqual(n_c, 4)

    def test_layers_drape_over_a_layer_starting_beneath_them(self):
        """Where the cathode starts inside the anode overhang, the anode above it
        bends over the step instead of jumping (the 1.1 paths stepped there)."""
        profile = build_stack_profile(
            [
                ("cathode", _segment(0.2, 0.5), 120 * UM),
                ("separator", _segment(0.0, 0.6), 20 * UM),
                ("anode", _segment(0.05, 0.55), 100 * UM),
                ("top_separator", _segment(0.0, 0.6), 20 * UM),
            ]
        )
        for template in (round_template(2 * MM), racetrack_template(1 * MM, 20 * MM)):
            result = wind(profile, template)
            path, _ = result.layer_path("anode")
            path = path[~np.isnan(path[:, 1])]
            ds = np.diff(path[:, 1])
            self.assertTrue(np.all(ds >= -1e-12))
            # offsets above the strip's bottom face are continuous along the path
            f = result._index_at(path[:, 1])
            base = result._interp(result.a, f)
            x0, z0, nx, nz = result._template_at(f)
            height = (path[:, 3] - x0) * nx + (path[:, 4] - z0) * nz - base
            jumps = np.abs(np.diff(height))[ds < 1e-9]
            self.assertTrue(np.all(jumps < 1e-9))
            # no steeper than 1:1 anywhere (the 1.1 paths jumped 120 um at no length)
            moving = ds > 1e-9
            self.assertTrue(np.all(np.abs(np.diff(height))[moving] <= ds[moving]))
            # and it ends exactly at its ends
            self.assertAlmostEqual(path[0, 1], 0.05, places=12)
            self.assertAlmostEqual(path[-1, 1], 0.55, places=12)

    def test_no_layer_sinks_into_the_layers_beneath_it(self):
        profile = build_stack_profile(
            [
                ("cathode", np.array([[0.2, 0], [0.3, 0], [np.nan, np.nan], [0.32, 0], [0.5, 0]]), 120 * UM),
                ("separator", _segment(0.0, 0.6), 20 * UM),
                ("anode", _segment(0.05, 0.55), 100 * UM),
                ("top_separator", _segment(0.01, 0.6), 20 * UM),
            ]
        )
        for template in (round_template(2 * MM), racetrack_template(1 * MM, 20 * MM)):
            result = wind(profile, template)
            below_top = np.zeros(result.a.shape[0])
            for c in range(len(profile.names)):
                bottom = result.layer_bottom(c)
                here = ~np.isnan(bottom)
                self.assertTrue(np.all(bottom[here] >= below_top[here] - 1e-12))
                below_top[here] = np.maximum(below_top[here], bottom[here] + profile.layer_thickness[c])
            inside = result.iv < profile.thickness.shape[0]
            np.testing.assert_allclose(result.H[inside], below_top[inside], atol=1e-12)

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

    def test_symmetric_coatings_keep_their_interfacial_area(self):
        """With identical a and b side coatings, pairing the sides the wrong way
        round (before 1.2.1) cost nothing: the reference cells barely move."""
        self.assertAlmostEqual(self.round.interfacial_area / 4443.1, 1.0, delta=5e-4)
        self.assertAlmostEqual(self.flat.interfacial_area / 7651.6, 1.0, delta=5e-4)

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

    def test_an_older_design_is_rewound_when_loaded(self):
        """The reference cells were saved before 1.1.0: loading one re-winds
        its roll, so its radius is the new model's, not the stored one."""
        roll = deepcopy(self.round)
        fresh = deepcopy(roll)
        fresh._calculate_all_properties()
        self.assertIsNotNone(getattr(roll, "_winding", None))
        self.assertAlmostEqual(roll.radius, fresh.radius, places=9)

    def test_a_rewound_cell_round_trips(self):
        """A re-wound cell saves to the same bytes as that save reloaded: the
        recompute must leave its parts linked as deserialization does."""
        import lz4.frame
        import msgpack
        from steer_core.Mixins.Serializer import SerializerMixin

        def strip_versions(value):
            if isinstance(value, dict):
                return {k: strip_versions(v) for k, v in value.items() if k != "__schema_version__"}
            if isinstance(value, list):
                return [strip_versions(v) for v in value]
            return value

        cell = _Cell.from_database("LFP Cylindrical Tabless Cell", table_name="cell_references")
        blob = cell.serialize(compress=True)
        payload = msgpack.unpackb(lz4.frame.decompress(blob[1:]), raw=False)
        old = blob[:1] + lz4.frame.compress(
            msgpack.packb(strip_versions(payload), use_bin_type=True)
        )
        rewound = SerializerMixin.deserialize(old)
        blob = rewound.serialize(compress=True)
        self.assertEqual(SerializerMixin.deserialize(blob).serialize(compress=True), blob)


class TestWeldTabs(unittest.TestCase):
    """A tab-welded collector's tabs are a layer of the stack, against the foil
    on the weld side inside their skip-coat gaps, so they are wound into the
    roll and drawn in its cross-section."""

    @classmethod
    def setUpClass(cls):
        cls.roll = _Cell.from_database(
            "NMC811 Cylindrical Tabbed Cell", table_name="cell_references"
        ).reference_electrode_assembly
        thick = deepcopy(cls.roll)
        for electrode in ("cathode", "anode"):
            collector = getattr(thick.layup, electrode).current_collector
            tab = deepcopy(collector.weld_tab)
            tab.thickness = 150  # um, thicker than either coating
            collector.weld_tab = tab
            collector.propagate_changes()
        cls.thick = thick

    def test_tabs_are_a_layer_against_the_foil(self):
        profile = self.roll.layup.get_stack_profile()
        names = list(profile.names)
        for electrode in ("cathode", "anode"):
            collector = getattr(self.roll.layup, electrode).current_collector
            self.assertEqual(collector._tab_weld_side, "a")
            i = names.index(f"{electrode}_weld_tabs")
            self.assertEqual(names[i - 1], f"{electrode}_current_collector")
            self.assertEqual(names[i + 1], f"{electrode}_a_side_coating")
            edges = sorted(
                (t._datum[0] - t._width / 2, t._datum[0] + t._width / 2) for t in collector._weld_tabs
            )
            np.testing.assert_allclose(
                profile.segments[f"{electrode}_weld_tabs"] + profile.x_origin, edges, atol=1e-12
            )
            # inside its skip-coat gap the stack is a tab thicker on the tab
            tab = collector._weld_tabs[0]
            on_tab = tab._datum[0] - profile.x_origin
            beside = on_tab + tab._width / 2 + (collector._skip_coat_width - tab._width) / 4
            self.assertAlmostEqual(
                profile.thickness_at(np.array([on_tab]))[0]
                - profile.thickness_at(np.array([beside]))[0],
                tab._thickness,
                places=12,
            )

    def test_a_tabless_laminate_has_no_tab_layer(self):
        tabless = _Cell.from_database("TESLA 4680", table_name="teardowns").reference_electrode_assembly
        self.assertFalse(any("weld_tabs" in n for n in tabless.layup.get_stack_profile().names))

    def test_tab_paths_start_and_stop_at_the_tab_edges(self):
        for electrode in ("cathode", "anode"):
            collector = getattr(self.roll.layup, electrode).current_collector
            path = self.roll._component_spirals[f"{electrode}_weld_tabs"]
            segments = np.split(path, np.flatnonzero(np.isnan(path[:, 1])))
            ends = sorted(
                (seg[~np.isnan(seg[:, 1]), 1].min(), seg[~np.isnan(seg[:, 1]), 1].max())
                for seg in segments
            )
            edges = sorted(
                (t._datum[0] - t._width / 2, t._datum[0] + t._width / 2) for t in collector._weld_tabs
            )
            np.testing.assert_allclose(ends, edges, atol=1e-12)

    def test_a_thick_tab_bumps_the_roll_and_everything_drapes_over_it(self):
        self.assertGreater(self.thick.radius, self.roll.radius + 0.05)
        winding = self.thick._winding
        profile = winding.profile
        below_top = np.zeros(winding.a.shape[0])
        for c in range(len(profile.names)):
            bottom = winding.layer_bottom(c)
            here = ~np.isnan(bottom)
            self.assertTrue(np.all(bottom[here] >= below_top[here] - 1e-12))
            below_top[here] = np.maximum(below_top[here], bottom[here] + profile.layer_thickness[c])
        sup = _support(winding)
        self.assertTrue(np.all(winding.a >= sup - 1e-12))

    def test_the_cross_section_draws_the_tabs(self):
        names = {trace.name for trace in self.roll.plot_spiral().data}
        self.assertIn("Cathode Weld Tabs", names)
        self.assertIn("Anode Weld Tabs", names)

    def test_objective_measures_what_the_rebuild_does(self):
        roll = deepcopy(self.thick)
        self.assertAlmostEqual(roll._radius_at_length(roll.layup.length), roll.radius, places=9)

if __name__ == "__main__":
    unittest.main()
