# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Named numeric constants used across the steer-opencell-design package.

Centralising these values avoids "magic numbers" sprinkled through the code
and makes each constant's physical meaning, units, and expected range
self-documenting.

All tolerances are given in SI base units (metres, fraction-of-unity, etc.).
"""


# -----------------------------------------------------------------------------
# Formulation-level numerical parameters
# -----------------------------------------------------------------------------

MASS_FRACTION_SUM_TOLERANCE: float = 0.01
"""Allowed deviation of the sum of mass fractions from 1.0 in an electrode
formulation before a ``UserWarning`` is issued. Active materials, binders
and conductive additives must therefore sum to ``1.0 ± MASS_FRACTION_SUM_TOLERANCE``.
"""

VOLTAGE_BLEND_GRID_POINTS: int = 100
"""Number of points on the common voltage grid used when blending multiple
active-material half-cell curves into a single formulation-level specific
capacity curve. See ``_ElectrodeFormulation._calculate_specific_capacity_curve``.
"""


# -----------------------------------------------------------------------------
# Layup / electrochemical parameters
# -----------------------------------------------------------------------------

MINIMUM_VOLTAGE_RANGE_FRACTION: float = 0.5
"""Upper edge of the "lower voltage limit" range, expressed as a fraction of
the discharge voltage span:

    V_top = V_min + MINIMUM_VOLTAGE_RANGE_FRACTION * (V_max - V_min)

At 0.5 the UI allows the lower operating voltage to vary within the lower
half of the discharge curve.
"""


# -----------------------------------------------------------------------------
# Cell-level geometric tolerances (metres)
# -----------------------------------------------------------------------------

DIMENSION_FIT_TOLERANCE_M: float = 1e-3
"""Allowed oversize of the electrode assembly over the encapsulation's
internal cavity, in metres. Used by cylindrical cells to validate
"assembly fits inside canister".
"""
