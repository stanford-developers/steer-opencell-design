# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Direct tests for the static helpers in
``Constructions/ElectrodeAssemblies/SpiralUtils.py``.

The full SpiralCalculator pipeline is exercised end-to-end through cell
construction in ``test_cells.py`` and ``test_assembly.py``. These tests
target the lower-level building blocks that are easy to specify in
closed form:

  * ``calculate_simple_spiral`` (uniform-thickness Archimedean spiral)
    \u2014 input validation, ``n_turns`` vs ``target_length`` paths,
    radius-growth invariant.
  * ``racetrack_position`` (parametric scalar version) \u2014 known cardinal
    angles map to the expected (x, z) coordinates.
  * ``_racetrack_positions_batch`` (numba-compiled vectorised version)
    must agree with the scalar version everywhere.
  * ``racetrack_curvature`` \u2014 1/r on curves, 0 on straights.
  * ``get_thickness_of_racetrack`` / ``get_width_of_racetrack`` \u2014
    NaN-safe min/max span helpers.
  * ``_thickness_at_jit`` \u2014 boundary clamping plus interior
    interpolation accuracy.
"""

import unittest

import numpy as np
from steer_core.Constants.Universal import TWO_PI

from steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils import (
    SpiralCalculator,
    _racetrack_positions_batch,
    _thickness_at_jit,
)


class TestCalculateSimpleSpiralValidation(unittest.TestCase):
    def test_specifying_both_n_turns_and_target_length_raises(self):
        with self.assertRaises(ValueError):
            SpiralCalculator.calculate_simple_spiral(
                n_turns=5,
                target_length=1.0,
                start_radius=0.005,
                thickness=1e-4,
            )

    def test_specifying_neither_raises(self):
        with self.assertRaises(ValueError):
            SpiralCalculator.calculate_simple_spiral(
                start_radius=0.005,
                thickness=1e-4,
            )

    def test_missing_start_radius_raises(self):
        with self.assertRaises(ValueError):
            SpiralCalculator.calculate_simple_spiral(
                n_turns=5,
                thickness=1e-4,
            )

    def test_missing_thickness_raises(self):
        with self.assertRaises(ValueError):
            SpiralCalculator.calculate_simple_spiral(
                n_turns=5,
                start_radius=0.005,
            )


class TestCalculateSimpleSpiralOutput(unittest.TestCase):
    """Geometric invariants of a uniform-thickness Archimedean spiral."""

    def test_n_turns_path_returns_six_columns(self):
        spiral = SpiralCalculator.calculate_simple_spiral(
            n_turns=3,
            start_radius=0.005,
            thickness=2e-4,
            points_per_turn=50,
        )
        self.assertEqual(spiral.shape[1], 6)

    def test_radius_grows_by_thickness_per_turn(self):
        n_turns = 4
        thickness = 1e-4
        start_radius = 0.005
        spiral = SpiralCalculator.calculate_simple_spiral(
            n_turns=n_turns,
            start_radius=start_radius,
            thickness=thickness,
            points_per_turn=200,
        )
        # First sample is at the start radius.
        self.assertAlmostEqual(spiral[0, 2], start_radius, places=10)
        # Last sample radius = start_radius + thickness * n_turns (analytic).
        self.assertAlmostEqual(
            spiral[-1, 2], start_radius + thickness * n_turns, places=10
        )

    def test_target_length_truncates_to_exact_length(self):
        target_length = 0.05  # 50 mm.
        spiral = SpiralCalculator.calculate_simple_spiral(
            target_length=target_length,
            start_radius=0.005,
            thickness=1e-4,
            points_per_turn=100,
        )
        self.assertAlmostEqual(spiral[-1, 1], target_length, places=10)

    def test_x_unwrapped_is_monotonically_non_decreasing(self):
        spiral = SpiralCalculator.calculate_simple_spiral(
            n_turns=2,
            start_radius=0.005,
            thickness=2e-4,
            points_per_turn=50,
        )
        diffs = np.diff(spiral[:, 1])
        self.assertTrue(np.all(diffs >= -1e-15))

    def test_turns_column_matches_angle_traveled(self):
        spiral = SpiralCalculator.calculate_simple_spiral(
            n_turns=2.5,
            start_radius=0.005,
            thickness=1e-4,
            points_per_turn=80,
        )
        # Final turns count must equal the requested n_turns.
        self.assertAlmostEqual(spiral[-1, 5], 2.5, places=6)


class TestRacetrackPosition(unittest.TestCase):
    """Geometric invariants of the parametric racetrack position helper.

    Rather than pinning specific theta\u2192(x,z) mappings (which depend on
    the perimeter-fraction parameterisation and are easy to misread from
    the docstring), we lock down robust invariants:

      * Every (x, z) lies on the closed racetrack curve.
      * Theta is 2pi-periodic.
      * The bottom straight-section midpoint is at (0, -radius).
      * The top straight-section midpoint is at (0, +radius).
    """

    def setUp(self):
        self.radius = 0.01
        self.straight_length = 0.04
        self.semi_arc = np.pi * self.radius
        self.total_perimeter = 2 * self.semi_arc + 2 * self.straight_length

    def _theta_for_arc_fraction(self, fraction: float) -> float:
        """Return the theta whose clockwise-arc position is ``fraction`` of perimeter."""
        return TWO_PI * (1.0 - fraction)

    def _is_on_racetrack(self, x: float, z: float, tol: float = 1e-9) -> bool:
        """Point lies on the racetrack iff it is on a straight or a semicircle."""
        L_half = self.straight_length / 2.0
        # Top / bottom straights.
        on_top = abs(z - self.radius) < tol and -L_half - tol <= x <= L_half + tol
        on_bot = abs(z + self.radius) < tol and -L_half - tol <= x <= L_half + tol
        # Right semicircle is centred at (+L/2, 0); left at (-L/2, 0).
        on_right = abs((x - L_half) ** 2 + z ** 2 - self.radius ** 2) < tol
        on_left = abs((x + L_half) ** 2 + z ** 2 - self.radius ** 2) < tol
        return on_top or on_bot or on_right or on_left

    def test_returns_tuple_of_two_floats(self):
        result = SpiralCalculator.racetrack_position(
            theta=1.0, radius=self.radius, straight_length=self.straight_length
        )
        self.assertEqual(len(result), 2)
        x, z = result
        self.assertIsInstance(float(x), float)
        self.assertIsInstance(float(z), float)

    def test_every_point_lies_on_the_racetrack(self):
        for fraction in np.linspace(0.0, 1.0, 21, endpoint=False):
            theta = self._theta_for_arc_fraction(fraction)
            x, z = SpiralCalculator.racetrack_position(
                theta=theta,
                radius=self.radius,
                straight_length=self.straight_length,
            )
            self.assertTrue(
                self._is_on_racetrack(x, z),
                msg=(
                    f"point ({x:.6f}, {z:.6f}) is not on the racetrack at "
                    f"fraction={fraction:.3f}, theta={theta:.6f}"
                ),
            )

    def test_theta_is_two_pi_periodic(self):
        for theta in (0.0, np.pi / 4, 1.234, np.pi):
            base = SpiralCalculator.racetrack_position(
                theta=theta,
                radius=self.radius,
                straight_length=self.straight_length,
            )
            shifted = SpiralCalculator.racetrack_position(
                theta=theta + TWO_PI,
                radius=self.radius,
                straight_length=self.straight_length,
            )
            self.assertAlmostEqual(base[0], shifted[0], places=10)
            self.assertAlmostEqual(base[1], shifted[1], places=10)

    def test_bottom_straight_midpoint_is_zero_minus_radius(self):
        # First semicircle covers semi_arc; bottom straight covers next straight_length.
        # Midpoint of bottom straight is at arc_length = semi_arc + straight_length/2.
        target_arc = self.semi_arc + self.straight_length / 2.0
        theta = self._theta_for_arc_fraction(target_arc / self.total_perimeter)
        x, z = SpiralCalculator.racetrack_position(
            theta=theta,
            radius=self.radius,
            straight_length=self.straight_length,
        )
        self.assertAlmostEqual(x, 0.0, places=10)
        self.assertAlmostEqual(z, -self.radius, places=10)

    def test_top_straight_midpoint_is_zero_plus_radius(self):
        # Top straight runs after both semicircles + bottom straight; its midpoint
        # lies at arc_length = 2*semi_arc + straight_length + straight_length/2.
        target_arc = (
            2 * self.semi_arc + self.straight_length + self.straight_length / 2.0
        )
        theta = self._theta_for_arc_fraction(target_arc / self.total_perimeter)
        x, z = SpiralCalculator.racetrack_position(
            theta=theta,
            radius=self.radius,
            straight_length=self.straight_length,
        )
        self.assertAlmostEqual(x, 0.0, places=10)
        self.assertAlmostEqual(z, self.radius, places=10)


class TestRacetrackPositionsBatchMatchesScalar(unittest.TestCase):
    """The numba batch helper must agree with the scalar implementation."""

    def test_batch_matches_scalar_at_random_angles(self):
        rng = np.random.default_rng(seed=42)
        thetas = rng.uniform(0.0, TWO_PI, size=50)
        radius = 0.012
        straight_length = 0.06
        radii = np.full_like(thetas, radius)

        x_batch, z_batch = _racetrack_positions_batch(
            thetas, radii, straight_length
        )

        for i, theta in enumerate(thetas):
            x_scalar, z_scalar = SpiralCalculator.racetrack_position(
                theta=float(theta), radius=radius, straight_length=straight_length
            )
            self.assertAlmostEqual(x_batch[i], x_scalar, places=10)
            self.assertAlmostEqual(z_batch[i], z_scalar, places=10)


class TestRacetrackCurvature(unittest.TestCase):
    def setUp(self):
        self.radius = 0.01
        self.straight_length = 0.04

    def test_curvature_on_curve_is_one_over_radius(self):
        # theta in [0, semi_arc/total_perimeter * 2pi]: on first semicircle.
        # Pick something safely inside the curved section.
        kappa = SpiralCalculator.racetrack_curvature(
            theta=np.pi / 12,
            radius=self.radius,
            straight_length=self.straight_length,
        )
        self.assertAlmostEqual(kappa, 1.0 / self.radius, places=10)

    def test_curvature_on_straight_section_is_zero(self):
        # Compute a theta that lands in the straight section.
        semi_arc = np.pi * self.radius
        total_perimeter = 2 * semi_arc + 2 * self.straight_length
        target_arc = semi_arc + self.straight_length / 2.0
        # Internal mapping uses theta/(2pi), not the clockwise mapping.
        theta = (target_arc / total_perimeter) * TWO_PI
        kappa = SpiralCalculator.racetrack_curvature(
            theta=theta,
            radius=self.radius,
            straight_length=self.straight_length,
        )
        self.assertAlmostEqual(kappa, 0.0, places=10)

    def test_zero_radius_returns_zero(self):
        kappa = SpiralCalculator.racetrack_curvature(
            theta=np.pi / 4, radius=0.0, straight_length=0.04
        )
        self.assertEqual(kappa, 0.0)


class TestRacetrackSpanHelpers(unittest.TestCase):
    def test_thickness_is_z_span(self):
        coords = np.array(
            [[0.0, -2.0], [1.0, 0.0], [2.0, 3.0], [3.0, -1.0]]
        )
        self.assertAlmostEqual(
            SpiralCalculator.get_thickness_of_racetrack(coords), 5.0, places=10
        )

    def test_thickness_ignores_nan(self):
        coords = np.array(
            [[0.0, -2.0], [1.0, np.nan], [2.0, 3.0], [3.0, np.nan]]
        )
        self.assertAlmostEqual(
            SpiralCalculator.get_thickness_of_racetrack(coords), 5.0, places=10
        )

    def test_width_is_x_span(self):
        coords = np.array(
            [[-1.0, 0.0], [0.0, 1.0], [4.0, 2.0], [2.0, 3.0]]
        )
        self.assertAlmostEqual(
            SpiralCalculator.get_width_of_racetrack(coords), 5.0, places=10
        )

    def test_width_ignores_nan(self):
        coords = np.array(
            [[-1.0, 0.0], [np.nan, 1.0], [4.0, 2.0], [np.nan, 3.0]]
        )
        self.assertAlmostEqual(
            SpiralCalculator.get_width_of_racetrack(coords), 5.0, places=10
        )


class TestThicknessAtJit(unittest.TestCase):
    """``_thickness_at_jit`` is a uniform-grid linear interpolator.

    It must clamp at the endpoints and exactly reproduce the grid values.
    """

    def setUp(self):
        # 11-point grid on [0, 1] with t = x.
        self.t_grid = np.linspace(0.0, 1.0, 11).astype(np.float64)
        self.total_length = 1.0
        self.n_grid_m1 = len(self.t_grid) - 1
        self.dx_inv = float(self.n_grid_m1) / self.total_length

    def test_clamps_to_first_point_below_zero(self):
        value = _thickness_at_jit(
            -0.5, self.t_grid, self.n_grid_m1, self.dx_inv, self.total_length
        )
        self.assertAlmostEqual(value, self.t_grid[0], places=10)

    def test_clamps_to_last_point_above_total_length(self):
        value = _thickness_at_jit(
            2.0, self.t_grid, self.n_grid_m1, self.dx_inv, self.total_length
        )
        self.assertAlmostEqual(value, self.t_grid[-1], places=10)

    def test_interior_point_is_linear_interpolation(self):
        # On the t = x grid, interpolation is the identity.
        for x in (0.05, 0.27, 0.5, 0.83):
            value = _thickness_at_jit(
                x, self.t_grid, self.n_grid_m1, self.dx_inv, self.total_length
            )
            self.assertAlmostEqual(value, x, places=10, msg=f"x={x}")


if __name__ == "__main__":
    unittest.main()
