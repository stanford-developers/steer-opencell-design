# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities for computing full-cell areal capacity curves from half-cell data."""

import numpy as np
from typing import Tuple, Optional

from steer_core.Utils.CurveComposition import (
    build_zero_value_proxy,
    compute_paired_curve_difference,
    DEFAULT_INTERPOLATION_POINTS,
)


CAPACITY_INTERPOLATION_POINTS = DEFAULT_INTERPOLATION_POINTS


class ArealCapacityCurveMixin:
    """Mixin for computing full-cell areal capacity curves by combining cathode and anode half-cell curves with N/P ratio adjustments."""

    @staticmethod
    def _build_zero_voltage_anode_proxy(cathode_areal_curve: np.ndarray) -> np.ndarray:
        """Build a synthetic V=0 anode half-cell curve that spans the cathode capacity range."""
        return build_zero_value_proxy(cathode_areal_curve, CAPACITY_INTERPOLATION_POINTS)

    @staticmethod
    def _compute_areal_full_cell_curve(cathode_areal_curve: np.ndarray, anode_areal_curve: np.ndarray) -> Tuple[float, np.ndarray]:
        """Compute the full-cell areal capacity curve from cathode and anode half-cell curves."""
        return compute_paired_curve_difference(
            cathode_areal_curve, anode_areal_curve, CAPACITY_INTERPOLATION_POINTS
        )

