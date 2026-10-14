# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Self-consistency and continuity of the winding kernels on the bench cases.

The cases are the ones ``test/perf/bench_spiral_utils.py`` times, so a
regression here also shows up in the bench harness. Winding the same laminate
twice must give identical output (no hidden state or in-place mutation), and
the wound paths must be continuous.
"""

from __future__ import annotations

import os
import sys
import unittest
from copy import deepcopy

import numpy as np

# Make the bench module importable as a sibling helper.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "perf"))

from bench_spiral_utils import _build_cases  # type: ignore  # noqa: E402

from steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils import (
    SpiralCalculator,
)


def _resample(
    sample_x: np.ndarray, sample_y: np.ndarray, query_x: np.ndarray
) -> np.ndarray:
    """np.interp wrapper that clips the query to the sample range."""
    qx = np.clip(query_x, sample_x[0], sample_x[-1])
    return np.interp(qx, sample_x, sample_y)


def _max_abs_diff_along_x(
    a: np.ndarray, b: np.ndarray, col_x: int, cols_y: tuple[int, ...]
) -> dict[int, float]:
    """Maximum |a_col - b_col| after resampling onto a common x-grid."""
    n = max(a.shape[0], b.shape[0])
    common_x = np.linspace(
        max(a[0, col_x], b[0, col_x]),
        min(a[-1, col_x], b[-1, col_x]),
        n,
    )
    out: dict[int, float] = {}
    for c in cols_y:
        ya = _resample(a[:, col_x], a[:, c], common_x)
        yb = _resample(b[:, col_x], b[:, c], common_x)
        out[c] = float(np.max(np.abs(ya - yb)))
    return out


class TestSpiralPerfRegression(unittest.TestCase):
    """Winding each bench case twice on a deepcopy must give identical
    output, which catches any accidental in-place mutation."""

    @classmethod
    def setUpClass(cls):
        cls.cases = _build_cases()

    def test_spiral_self_consistent(self):
        for case in self.cases:
            with self.subTest(case=case.name):
                a = SpiralCalculator.calculate_variable_thickness_spiral(
                    laminate=deepcopy(case.laminate),
                    start_radius=case.round_mandrel_radius_m,
                    dtheta=0.1,
                )
                b = SpiralCalculator.calculate_variable_thickness_spiral(
                    laminate=deepcopy(case.laminate),
                    start_radius=case.round_mandrel_radius_m,
                    dtheta=0.1,
                )
                # Identical inputs must produce identical outputs.
                np.testing.assert_array_equal(a, b)

    def test_racetrack_self_consistent(self):
        for case in self.cases:
            with self.subTest(case=case.name):
                a = SpiralCalculator.calculate_variable_thickness_racetrack(
                    laminate=deepcopy(case.laminate),
                    mandrel_radius=case.flat_mandrel_radius_m,
                    straight_length=case.flat_straight_length_m,
                    ds_target=1e-4,
                )
                b = SpiralCalculator.calculate_variable_thickness_racetrack(
                    laminate=deepcopy(case.laminate),
                    mandrel_radius=case.flat_mandrel_radius_m,
                    straight_length=case.flat_straight_length_m,
                    ds_target=1e-4,
                )
                np.testing.assert_array_equal(a, b)

    def test_spiral_cartesian_path_continuous(self):
        """The spiral curve must be smooth: no jump > 10 * mean_step."""
        for case in self.cases:
            with self.subTest(case=case.name):
                arr = SpiralCalculator.calculate_variable_thickness_spiral(
                    laminate=deepcopy(case.laminate),
                    start_radius=case.round_mandrel_radius_m,
                    dtheta=0.1,
                )
                xy = arr[:, [3, 4]]  # x_coord, z_coord
                d = np.linalg.norm(np.diff(xy, axis=0), axis=1)
                self.assertTrue(np.all(d > 0))
                self.assertLess(d.max(), 10.0 * d.mean())

    def test_racetrack_cartesian_path_continuous(self):
        # Straights and semicircles are sampled at different spacings, so the
        # per-row Cartesian step is bimodal; the unwrapped-length deltas are
        # what must stay bounded.
        for case in self.cases:
            with self.subTest(case=case.name):
                arr = SpiralCalculator.calculate_variable_thickness_racetrack(
                    laminate=deepcopy(case.laminate),
                    mandrel_radius=case.flat_mandrel_radius_m,
                    straight_length=case.flat_straight_length_m,
                    ds_target=1e-4,
                )
                d = np.diff(arr[:, 1])  # x_unwrapped column
                self.assertTrue(np.all(d >= 0))
                if d.size > 0 and d.max() > 0:
                    self.assertLess(d.max(), 50.0 * np.median(d[d > 0]))


if __name__ == "__main__":
    unittest.main()
