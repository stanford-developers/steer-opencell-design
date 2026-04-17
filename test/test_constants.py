# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Sanity checks for the named constants in ``Utils/Constants.py``.

These tests guard against accidentally breaking the import path or shipping
nonsensical values (negative tolerances, zero blend points, etc.) and
serve as documentation for what each constant must look like.
"""

import unittest

from steer_opencell_design.Utils import Constants


class TestConstantImportPaths(unittest.TestCase):
    """The module is small enough that we can spot-check every public name."""

    def test_module_exposes_expected_names(self):
        for name in (
            "MASS_FRACTION_SUM_TOLERANCE",
            "VOLTAGE_BLEND_GRID_POINTS",
            "MINIMUM_VOLTAGE_RANGE_FRACTION",
            "DIMENSION_FIT_TOLERANCE_M",
        ):
            self.assertTrue(
                hasattr(Constants, name),
                msg=f"Utils.Constants is missing public constant {name!r}",
            )


class TestConstantValues(unittest.TestCase):
    def test_mass_fraction_sum_tolerance_is_a_small_positive_fraction(self):
        self.assertGreater(Constants.MASS_FRACTION_SUM_TOLERANCE, 0.0)
        self.assertLess(Constants.MASS_FRACTION_SUM_TOLERANCE, 0.05)

    def test_voltage_blend_grid_points_is_resolved_enough(self):
        self.assertIsInstance(Constants.VOLTAGE_BLEND_GRID_POINTS, int)
        self.assertGreaterEqual(Constants.VOLTAGE_BLEND_GRID_POINTS, 50)

    def test_minimum_voltage_range_fraction_is_a_unit_fraction(self):
        self.assertGreater(Constants.MINIMUM_VOLTAGE_RANGE_FRACTION, 0.0)
        self.assertLessEqual(Constants.MINIMUM_VOLTAGE_RANGE_FRACTION, 1.0)

    def test_dimension_fit_tolerance_is_positive_metres(self):
        self.assertGreater(Constants.DIMENSION_FIT_TOLERANCE_M, 0.0)
        self.assertLess(
            Constants.DIMENSION_FIT_TOLERANCE_M,
            1e-1,
            msg="A dimensional fit tolerance > 100 mm is almost certainly wrong.",
        )


if __name__ == "__main__":
    unittest.main()
