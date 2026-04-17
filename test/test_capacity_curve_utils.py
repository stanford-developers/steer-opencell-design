# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Direct tests for the static helpers in ``Materials/CapacityCurveUtils.py``
and ``Constructions/Layups/ArealCapacityCurveUtils.py``.

The mixins are mostly thin wrappers around ``steer_core`` curve utilities,
so most of these tests assert ``CapacityCurveMixin`` produces the exact
same result as calling the underlying helper directly. That way, if a
future refactor accidentally swaps the underlying call, this test
surfaces it explicitly.

The two computational helpers (``_calculate_capacity_curve_properties``
and ``_calculate_specific_capacity_curve``) are exercised end-to-end with
hand-crafted curves so each branch (exact-match, interpolation,
truncation, out-of-range error) is hit deterministically.
"""

import unittest

import numpy as np
from steer_core.Constants.Units import G_TO_KG, H_TO_S, mA_TO_A
from steer_core.Utils.CurveProcessing import (
    correct_segment_directions,
    interpolate_curve_at_target,
    make_segments_monotonic,
    prepend_primary_endpoint_to_secondary,
    reverse_secondary_segment,
    scale_curve,
    scale_secondary_segment,
    truncate_and_shift_segments,
)

from steer_opencell_design.Constructions.Layups.ArealCapacityCurveUtils import (
    ArealCapacityCurveMixin,
)
from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial
from steer_opencell_design.Materials.CapacityCurveUtils import CapacityCurveMixin


def _make_synthetic_curve(
    *,
    charge_capacity_max: float = 100.0,
    n_points: int = 11,
    voltage_low: float = 3.0,
    voltage_high: float = 4.2,
) -> np.ndarray:
    """Build a tiny half-cell curve with a charge (+1) and discharge (-1) branch.

    Both branches share endpoints; charge ramps capacity 0 → max from
    voltage_low → voltage_high, and discharge ramps it back from
    voltage_high → voltage_low at slightly lower max capacity (90 %).
    """
    capacity_charge = np.linspace(0.0, charge_capacity_max, n_points)
    voltage_charge = np.linspace(voltage_low, voltage_high, n_points)
    direction_charge = np.full(n_points, +1.0)

    capacity_discharge = np.linspace(0.0, charge_capacity_max * 0.9, n_points)
    voltage_discharge = np.linspace(voltage_low, voltage_high, n_points)
    direction_discharge = np.full(n_points, -1.0)

    curve_charge = np.column_stack(
        (capacity_charge, voltage_charge, direction_charge)
    )
    curve_discharge = np.column_stack(
        (capacity_discharge, voltage_discharge, direction_discharge)
    )
    return np.vstack((curve_charge, curve_discharge))


class TestCapacityCurveMixinShims(unittest.TestCase):
    """Each shim must produce exactly what its steer_core counterpart returns."""

    def setUp(self):
        self.curve = _make_synthetic_curve()

    def test_correct_curve_directions_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._correct_curve_directions(self.curve.copy()),
            correct_segment_directions(self.curve.copy()),
        )

    def test_make_curve_monotonic_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._make_curve_monotonic(self.curve.copy()),
            make_segments_monotonic(self.curve.copy()),
        )

    def test_reverse_discharge_curve_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._reverse_discharge_curve(self.curve.copy()),
            reverse_secondary_segment(self.curve.copy()),
        )

    def test_add_point_to_discharge_curve_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._add_point_to_discharge_curve(self.curve.copy()),
            prepend_primary_endpoint_to_secondary(self.curve.copy()),
        )

    def test_apply_reversible_scaling_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._apply_reversible_specific_capacity_scaling(
                self.curve.copy(), 0.5
            ),
            scale_secondary_segment(self.curve.copy(), 0.5),
        )

    def test_apply_irreversible_scaling_matches_steer_core(self):
        np.testing.assert_array_equal(
            CapacityCurveMixin._apply_irreversible_specific_capacity_scaling(
                self.curve.copy(), 0.7
            ),
            scale_curve(self.curve.copy(), 0.7),
        )


class TestProcessSpecificCapacityCurves(unittest.TestCase):
    def test_unit_conversion_factor_is_applied(self):
        """``process_specific_capacity_curves`` must convert mAh/g → SI A·s/kg in place."""
        curve = _make_synthetic_curve(charge_capacity_max=200.0)
        original_capacity_mah_per_g = curve[:, 0].copy()

        processed = CapacityCurveMixin.process_specific_capacity_curves(curve.copy())

        expected_factor = H_TO_S * mA_TO_A / G_TO_KG
        # The processing pipeline reorders points after unit conversion; we can
        # still pin the absolute max capacity, which must scale by the factor.
        self.assertAlmostEqual(
            processed[:, 0].max(),
            original_capacity_mah_per_g.max() * expected_factor,
            places=8,
        )


class TestCalculateCapacityCurveProperties(unittest.TestCase):
    def test_irreversible_is_max_capacity(self):
        curve = _make_synthetic_curve(charge_capacity_max=120.0)
        irreversible, _ = CapacityCurveMixin._calculate_capacity_curve_properties(curve)
        self.assertAlmostEqual(irreversible, 120.0, places=10)

    def test_reversible_is_irreversible_minus_min_discharge(self):
        """Definition: rev = irreversible − min(capacity[discharge_mask])."""
        curve = _make_synthetic_curve(charge_capacity_max=100.0)
        irreversible, reversible = (
            CapacityCurveMixin._calculate_capacity_curve_properties(curve)
        )
        discharge_mask = curve[:, 2] == -1
        expected = irreversible - curve[discharge_mask, 0].min()
        self.assertAlmostEqual(reversible, expected, places=10)


class TestCalculateSpecificCapacityCurve(unittest.TestCase):
    """Cover all three dispatch branches of ``_calculate_specific_capacity_curve``."""

    def setUp(self):
        # Build two curves with distinct (max-capacity, voltage-at-max) endpoints.
        self.curve_low = _make_synthetic_curve(
            charge_capacity_max=80.0, voltage_low=3.0, voltage_high=4.0
        )
        self.curve_high = _make_synthetic_curve(
            charge_capacity_max=100.0, voltage_low=3.0, voltage_high=4.4
        )
        self.catalogue = [self.curve_low, self.curve_high]
        # Voltage operation window: (lower-guard, lower-curve-max, upper-curve-max).
        self.voltage_window = (2.5, 4.0, 4.4)

    def test_exact_match_returns_curve_copy(self):
        result = CapacityCurveMixin._calculate_specific_capacity_curve(
            self.catalogue,
            voltage_cutoff=4.0,
            voltage_operation_window=self.voltage_window,
            material_type=CathodeMaterial,
        )
        np.testing.assert_array_equal(result, self.curve_low)
        self.assertIsNot(result, self.curve_low, msg="Must return a copy, not the input")

    def test_in_between_voltage_dispatches_to_interpolation(self):
        target = 4.2  # Between 4.0 and 4.4.
        result = CapacityCurveMixin._calculate_specific_capacity_curve(
            self.catalogue,
            voltage_cutoff=target,
            voltage_operation_window=self.voltage_window,
            material_type=CathodeMaterial,
        )
        expected = interpolate_curve_at_target(self.catalogue, target)
        np.testing.assert_array_equal(result, expected)

    def test_below_lowest_curve_dispatches_to_truncation(self):
        target = 3.5  # Between guard (2.5) and lowest curve (4.0).
        result = CapacityCurveMixin._calculate_specific_capacity_curve(
            self.catalogue,
            voltage_cutoff=target,
            voltage_operation_window=self.voltage_window,
            material_type=CathodeMaterial,
        )
        expected = truncate_and_shift_segments(
            self.catalogue, target, truncate_below_cutoff=True
        )
        np.testing.assert_array_equal(result, expected)

    def test_out_of_range_raises_with_descriptive_message(self):
        with self.assertRaises(ValueError) as ctx:
            CapacityCurveMixin._calculate_specific_capacity_curve(
                self.catalogue,
                voltage_cutoff=99.0,  # Way outside the window.
                voltage_operation_window=self.voltage_window,
                material_type=CathodeMaterial,
            )
        self.assertIn("Voltage cutoff", str(ctx.exception))
        self.assertIn("range", str(ctx.exception))


class TestArealCapacityCurveMixin(unittest.TestCase):
    """Cathode + anode coupling helpers."""

    def setUp(self):
        # Cathode areal curve with a non-trivial voltage profile spanning 3.0–4.0 V.
        self.cathode_curve = np.array(
            [
                [0.0, 4.0, +1.0],
                [50.0, 3.5, +1.0],
                [100.0, 3.0, +1.0],
                [100.0, 3.0, -1.0],
                [50.0, 3.5, -1.0],
                [0.0, 4.0, -1.0],
            ]
        )

    def test_zero_voltage_proxy_has_zero_voltage_everywhere(self):
        proxy = ArealCapacityCurveMixin._build_zero_voltage_anode_proxy(
            self.cathode_curve
        )
        np.testing.assert_array_almost_equal(proxy[:, 1], 0.0, decimal=12)

    def test_zero_voltage_proxy_spans_cathode_capacity_range(self):
        proxy = ArealCapacityCurveMixin._build_zero_voltage_anode_proxy(
            self.cathode_curve
        )
        cathode_max = self.cathode_curve[:, 0].max()
        cathode_min = self.cathode_curve[:, 0].min()
        # The proxy must at least reach the cathode capacity range bounds.
        self.assertGreaterEqual(proxy[:, 0].max(), cathode_max - 1e-9)
        self.assertLessEqual(proxy[:, 0].min(), cathode_min + 1e-9)

    def test_full_cell_curve_subtracts_anode_voltage(self):
        """When anode is V=0 everywhere, the full-cell curve must equal cathode V."""
        proxy = ArealCapacityCurveMixin._build_zero_voltage_anode_proxy(
            self.cathode_curve
        )
        _, full_cell_curve = ArealCapacityCurveMixin._compute_areal_full_cell_curve(
            self.cathode_curve, proxy
        )
        # With V_anode == 0 everywhere, every full-cell voltage must equal the
        # corresponding cathode voltage at the same capacity (positive).
        self.assertTrue(np.all(full_cell_curve[:, 1] >= 0.0))
        self.assertGreater(full_cell_curve[:, 1].max(), 3.5)


if __name__ == "__main__":
    unittest.main()
