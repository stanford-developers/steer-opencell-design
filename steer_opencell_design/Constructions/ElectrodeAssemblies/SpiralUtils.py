# SPDX-FileCopyrightText: 2024-2026 Nicholas Siemons and Adrian Yao
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Static utility methods for spiral and racetrack geometry calculations used in jelly roll winding."""

from steer_opencell_design.Constructions.Layups.Laminate import Laminate
from steer_core.Constants.Universal import PI, TWO_PI
from steer_core.Constants.Units import *
import numpy as np
import pandas as pd
import math
from typing import Optional


try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    # Provide a no-op decorator so the code still runs without numba
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

# Constants for array column indices
THETA_COL = 0
X_UNWRAPPED_COL = 1
RADIUS_COL = 2
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5

# Constants for calculations
TARGET_ERROR = 5e-5
MAX_ITERATIONS = 500000
MAX_POINTS = 120000

# ─── Numba-accelerated core loops ────────────────────────────────────────────

@njit(cache=True)
def _thickness_at_jit(x, t_grid, n_grid_m1, dx_inv, total_length):
    """Fast linear interpolation on a uniform grid (numba-compiled)."""
    if x <= 0.0:
        return t_grid[0]
    if x >= total_length:
        return t_grid[n_grid_m1]
    idx_f = x * dx_inv
    idx = int(idx_f)
    if idx >= n_grid_m1:
        return t_grid[n_grid_m1]
    frac = idx_f - idx
    return t_grid[idx] + frac * (t_grid[idx + 1] - t_grid[idx])


@njit(cache=True)
def _rk4_spiral_loop(t_grid, n_grid_m1, dx_inv, total_length,
                     r0, h_max_init, h_min_init, target_err,
                     max_iterations, max_points, dt_dx, x_grid, max_grad):
    """Adaptive RK4 integration loop for variable-thickness Archimedean spiral.

    Returns arrays (theta_arr, r_arr, x_arr) with the integrated spiral path.
    This is the hot inner loop, compiled with numba for ~10-30x speedup.
    """
    _TWO_PI = 2.0 * math.pi
    growth = 1.5
    shrink = 0.5

    # Pre-allocate output arrays (trimmed at the end)
    theta_out = np.empty(max_points, dtype=np.float64)
    r_out = np.empty(max_points, dtype=np.float64)
    x_out = np.empty(max_points, dtype=np.float64)

    theta = math.pi / 2.0
    r = r0
    x_unwrapped = 0.0
    h_max = h_max_init
    h_min = h_min_init
    h = h_max

    theta_out[0] = theta
    r_out[0] = r
    x_out[0] = x_unwrapped
    n_pts = 1
    iterations = 0

    while x_unwrapped < total_length and iterations < max_iterations and n_pts < max_points:
        iterations += 1

        # --- Adaptive h_max based on progress and radius ---
        progress_factor = x_unwrapped / total_length
        if progress_factor > 0.7:
            end_reduction = 1.0 - 0.6 * ((progress_factor - 0.7) / 0.3)
        else:
            end_reduction = 1.0
        radius_factor = min(1.0, r0 / max(r, r0))
        radius_reduction = 0.3 + 0.7 * radius_factor
        combined_factor = min(end_reduction, radius_reduction)
        current_h_max = h_max * combined_factor
        h = min(h, current_h_max)

        # Clamp step to avoid large overshoot
        remaining = total_length - x_unwrapped
        if r * h > 1.5 * remaining:
            h = max(remaining / (r + 1e-12), h_min)

        # --- RK4 full step ---
        t1 = _thickness_at_jit(x_unwrapped, t_grid, n_grid_m1, dx_inv, total_length)
        dr1 = t1 / _TWO_PI
        dx1 = math.sqrt(r * r + dr1 * dr1)

        r2_ = r + 0.5 * h * dr1
        x2_ = x_unwrapped + 0.5 * h * dx1
        t2 = _thickness_at_jit(x2_, t_grid, n_grid_m1, dx_inv, total_length)
        dr2 = t2 / _TWO_PI
        dx2 = math.sqrt(r2_ * r2_ + dr2 * dr2)

        r3_ = r + 0.5 * h * dr2
        x3_ = x_unwrapped + 0.5 * h * dx2
        t3 = _thickness_at_jit(x3_, t_grid, n_grid_m1, dx_inv, total_length)
        dr3 = t3 / _TWO_PI
        dx3 = math.sqrt(r3_ * r3_ + dr3 * dr3)

        r4_ = r + h * dr3
        x4_ = x_unwrapped + h * dx3
        t4 = _thickness_at_jit(x4_, t_grid, n_grid_m1, dx_inv, total_length)
        dr4 = t4 / _TWO_PI
        dx4 = math.sqrt(r4_ * r4_ + dr4 * dr4)

        r_full = r + (h / 6.0) * (dr1 + 2.0 * dr2 + 2.0 * dr3 + dr4)
        x_full = x_unwrapped + (h / 6.0) * (dx1 + 2.0 * dx2 + 2.0 * dx3 + dx4)

        # --- Two half-steps ---
        h2 = 0.5 * h
        # First half (reuse dr1, dx1)
        r2h = r + 0.5 * h2 * dr1
        x2h = x_unwrapped + 0.5 * h2 * dx1
        t2h = _thickness_at_jit(x2h, t_grid, n_grid_m1, dx_inv, total_length)
        dr2h = t2h / _TWO_PI
        dx2h = math.sqrt(r2h * r2h + dr2h * dr2h)

        r3h = r + 0.5 * h2 * dr2h
        x3h = x_unwrapped + 0.5 * h2 * dx2h
        t3h = _thickness_at_jit(x3h, t_grid, n_grid_m1, dx_inv, total_length)
        dr3h = t3h / _TWO_PI
        dx3h = math.sqrt(r3h * r3h + dr3h * dr3h)

        r4h = r + h2 * dr3h
        x4h = x_unwrapped + h2 * dx3h
        t4h = _thickness_at_jit(x4h, t_grid, n_grid_m1, dx_inv, total_length)
        dr4h = t4h / _TWO_PI
        dx4h = math.sqrt(r4h * r4h + dr4h * dr4h)

        r_half = r + (h2 / 6.0) * (dr1 + 2.0 * dr2h + 2.0 * dr3h + dr4h)
        x_half = x_unwrapped + (h2 / 6.0) * (dx1 + 2.0 * dx2h + 2.0 * dx3h + dx4h)

        # Second half
        ts1 = _thickness_at_jit(x_half, t_grid, n_grid_m1, dx_inv, total_length)
        dr1s = ts1 / _TWO_PI
        dx1s = math.sqrt(r_half * r_half + dr1s * dr1s)

        r2s = r_half + 0.5 * h2 * dr1s
        x2s = x_half + 0.5 * h2 * dx1s
        ts2 = _thickness_at_jit(x2s, t_grid, n_grid_m1, dx_inv, total_length)
        dr2s = ts2 / _TWO_PI
        dx2s = math.sqrt(r2s * r2s + dr2s * dr2s)

        r3s = r_half + 0.5 * h2 * dr2s
        x3s = x_half + 0.5 * h2 * dx2s
        ts3 = _thickness_at_jit(x3s, t_grid, n_grid_m1, dx_inv, total_length)
        dr3s = ts3 / _TWO_PI
        dx3s = math.sqrt(r3s * r3s + dr3s * dr3s)

        r4s = r_half + h2 * dr3s
        x4s = x_half + h2 * dx3s
        ts4 = _thickness_at_jit(x4s, t_grid, n_grid_m1, dx_inv, total_length)
        dr4s = ts4 / _TWO_PI
        dx4s = math.sqrt(r4s * r4s + dr4s * dr4s)

        r_two_half = r_half + (h2 / 6.0) * (dr1s + 2.0 * dr2s + 2.0 * dr3s + dr4s)
        x_two_half = x_half + (h2 / 6.0) * (dx1s + 2.0 * dx2s + 2.0 * dx3s + dx4s)

        # --- Error estimate ---
        err_r = abs(r_full - r_two_half)
        err_x = abs(x_full - x_two_half)
        scale_r = max(abs(r), abs(r_two_half), 1e-9)
        scale_x = max(abs(x_unwrapped), abs(x_two_half), 1e-9)
        rel_err = max(err_r / scale_r, err_x / scale_x)

        if rel_err > target_err and h > h_min * 1.01:
            h = max(h * shrink * max(0.2, (target_err / (rel_err + 1e-14)) ** 0.25), h_min)
            continue

        # Accept step (use the more-accurate two-half-steps result)
        r = r_two_half
        x_unwrapped = x_two_half
        theta -= h

        theta_out[n_pts] = theta
        r_out[n_pts] = r
        x_out[n_pts] = x_unwrapped
        n_pts += 1

        if rel_err < target_err / 8.0 and h < h_max / 0.6:
            h = min(h * growth * min(2.0, (target_err / (rel_err + 1e-14)) ** 0.20), h_max)

        # Gradient-based step modulation
        if 0.0 < x_unwrapped < total_length:
            # Manual linear interp for gradient lookup (avoid np.interp in numba)
            idx_f = x_unwrapped * (len(x_grid) - 1) / total_length
            idx = int(idx_f)
            if idx >= len(dt_dx) - 1:
                local_grad = abs(dt_dx[-1])
            else:
                frac = idx_f - idx
                local_grad = abs(dt_dx[idx] + frac * (dt_dx[idx + 1] - dt_dx[idx]))
        else:
            local_grad = 0.0
        grad_factor = 1.0 + 5.0 * (local_grad / max_grad)
        h = max(h / grad_factor, h_min)

    return theta_out[:n_pts], r_out[:n_pts], x_out[:n_pts]


@njit(cache=True)
def _rk4_racetrack_loop(t_grid, n_grid_m1, dx_inv, total_length,
                        mandrel_radius, straight_length,
                        r0, h_max_init, h_min_init, target_err,
                        max_iterations, max_points, dt_dx, x_grid, max_grad):
    """Adaptive RK4 integration loop for variable-thickness racetrack spiral.

    The ODE system for a racetrack:
        dr_accumulated/dtheta = t(x) / (2*pi)      (thickness buildup per full turn)
        ds/dtheta = perimeter(r) / (2*pi)           (arc length per radian)
    where perimeter(r) = 2*pi*r + 2*straight_length

    We parametrize by a "normalised angle" theta that increases by 2*pi per full turn.

    Returns arrays (theta_arr, r_arr, x_arr) with the integrated racetrack path.
    """
    _TWO_PI = 2.0 * math.pi
    _PI = math.pi
    growth = 1.5
    shrink = 0.5

    theta_out = np.empty(max_points, dtype=np.float64)
    r_out = np.empty(max_points, dtype=np.float64)
    x_out = np.empty(max_points, dtype=np.float64)

    theta = 0.0  # cumulative angle traveled (increases)
    accumulated_thickness = 0.0
    x_unwrapped = 0.0
    h_max = h_max_init
    h_min = h_min_init
    h = h_max

    theta_out[0] = theta
    r_out[0] = mandrel_radius + accumulated_thickness
    x_out[0] = x_unwrapped
    n_pts = 1
    iterations = 0

    while x_unwrapped < total_length and iterations < max_iterations and n_pts < max_points:
        iterations += 1

        current_radius = mandrel_radius + accumulated_thickness

        # Adaptive h_max
        progress_factor = x_unwrapped / total_length
        if progress_factor > 0.7:
            end_reduction = 1.0 - 0.6 * ((progress_factor - 0.7) / 0.3)
        else:
            end_reduction = 1.0
        radius_factor = min(1.0, mandrel_radius / max(current_radius, mandrel_radius))
        radius_reduction = 0.3 + 0.7 * radius_factor
        combined_factor = min(end_reduction, radius_reduction)
        current_h_max = h_max * combined_factor
        h = min(h, current_h_max)

        # Clamp step
        remaining = total_length - x_unwrapped
        perimeter_est = _TWO_PI * current_radius + 2.0 * straight_length
        ds_per_rad = perimeter_est / _TWO_PI
        if ds_per_rad * h > 1.5 * remaining:
            h = max(remaining / (ds_per_rad + 1e-12), h_min)

        # Curvature-aware step limit: ensure at least ~30 points per semicircle.
        # In normalised theta, one semicircle spans:
        #   delta_theta_semi = 2*pi * (pi*r) / (2*pi*r + 2*S)
        # We require h <= delta_theta_semi / min_pts_per_semi.
        if current_radius > 0.0 and straight_length > 0.0:
            theta_semi = _TWO_PI * _PI * current_radius / perimeter_est
            h_curvature = theta_semi / 30.0
            if h > h_curvature:
                h = max(h_curvature, h_min)

        # Derivative: given (accumulated_thickness, x_unwrapped) at some theta
        #   d(accum)/dtheta = t(x) / (2*pi)
        #   dx/dtheta = perimeter(mandrel_radius + accum) / (2*pi)
        # --- Using inline derivatives (numba doesn't support nested closures well) ---

        # Full RK4 step
        t1 = _thickness_at_jit(x_unwrapped, t_grid, n_grid_m1, dx_inv, total_length)
        da1 = t1 / _TWO_PI
        peri1 = _TWO_PI * (mandrel_radius + accumulated_thickness) + 2.0 * straight_length
        ds1 = peri1 / _TWO_PI

        a2 = accumulated_thickness + 0.5 * h * da1
        x2_ = x_unwrapped + 0.5 * h * ds1
        t2 = _thickness_at_jit(x2_, t_grid, n_grid_m1, dx_inv, total_length)
        da2 = t2 / _TWO_PI
        peri2 = _TWO_PI * (mandrel_radius + a2) + 2.0 * straight_length
        ds2 = peri2 / _TWO_PI

        a3 = accumulated_thickness + 0.5 * h * da2
        x3_ = x_unwrapped + 0.5 * h * ds2
        t3 = _thickness_at_jit(x3_, t_grid, n_grid_m1, dx_inv, total_length)
        da3 = t3 / _TWO_PI
        peri3 = _TWO_PI * (mandrel_radius + a3) + 2.0 * straight_length
        ds3 = peri3 / _TWO_PI

        a4 = accumulated_thickness + h * da3
        x4_ = x_unwrapped + h * ds3
        t4 = _thickness_at_jit(x4_, t_grid, n_grid_m1, dx_inv, total_length)
        da4 = t4 / _TWO_PI
        peri4 = _TWO_PI * (mandrel_radius + a4) + 2.0 * straight_length
        ds4 = peri4 / _TWO_PI

        a_full = accumulated_thickness + (h / 6.0) * (da1 + 2.0 * da2 + 2.0 * da3 + da4)
        x_full = x_unwrapped + (h / 6.0) * (ds1 + 2.0 * ds2 + 2.0 * ds3 + ds4)

        # Two half-steps
        h2 = 0.5 * h
        a2h = accumulated_thickness + 0.5 * h2 * da1
        x2h = x_unwrapped + 0.5 * h2 * ds1
        t2h = _thickness_at_jit(x2h, t_grid, n_grid_m1, dx_inv, total_length)
        da2h = t2h / _TWO_PI
        peri2h = _TWO_PI * (mandrel_radius + a2h) + 2.0 * straight_length
        ds2h = peri2h / _TWO_PI

        a3h = accumulated_thickness + 0.5 * h2 * da2h
        x3h = x_unwrapped + 0.5 * h2 * ds2h
        t3h = _thickness_at_jit(x3h, t_grid, n_grid_m1, dx_inv, total_length)
        da3h = t3h / _TWO_PI
        peri3h = _TWO_PI * (mandrel_radius + a3h) + 2.0 * straight_length
        ds3h = peri3h / _TWO_PI

        a4h = accumulated_thickness + h2 * da3h
        x4h = x_unwrapped + h2 * ds3h
        t4h = _thickness_at_jit(x4h, t_grid, n_grid_m1, dx_inv, total_length)
        da4h = t4h / _TWO_PI
        peri4h = _TWO_PI * (mandrel_radius + a4h) + 2.0 * straight_length
        ds4h = peri4h / _TWO_PI

        a_half = accumulated_thickness + (h2 / 6.0) * (da1 + 2.0 * da2h + 2.0 * da3h + da4h)
        x_half = x_unwrapped + (h2 / 6.0) * (ds1 + 2.0 * ds2h + 2.0 * ds3h + ds4h)

        # Second half
        ts1 = _thickness_at_jit(x_half, t_grid, n_grid_m1, dx_inv, total_length)
        da1s = ts1 / _TWO_PI
        peris1 = _TWO_PI * (mandrel_radius + a_half) + 2.0 * straight_length
        ds1s = peris1 / _TWO_PI

        a2s = a_half + 0.5 * h2 * da1s
        x2s = x_half + 0.5 * h2 * ds1s
        ts2 = _thickness_at_jit(x2s, t_grid, n_grid_m1, dx_inv, total_length)
        da2s = ts2 / _TWO_PI
        peris2 = _TWO_PI * (mandrel_radius + a2s) + 2.0 * straight_length
        ds2s = peris2 / _TWO_PI

        a3s = a_half + 0.5 * h2 * da2s
        x3s = x_half + 0.5 * h2 * ds2s
        ts3 = _thickness_at_jit(x3s, t_grid, n_grid_m1, dx_inv, total_length)
        da3s = ts3 / _TWO_PI
        peris3 = _TWO_PI * (mandrel_radius + a3s) + 2.0 * straight_length
        ds3s = peris3 / _TWO_PI

        a4s = a_half + h2 * da3s
        x4s = x_half + h2 * ds3s
        ts4 = _thickness_at_jit(x4s, t_grid, n_grid_m1, dx_inv, total_length)
        da4s = ts4 / _TWO_PI
        peris4 = _TWO_PI * (mandrel_radius + a4s) + 2.0 * straight_length
        ds4s = peris4 / _TWO_PI

        a_two_half = a_half + (h2 / 6.0) * (da1s + 2.0 * da2s + 2.0 * da3s + da4s)
        x_two_half = x_half + (h2 / 6.0) * (ds1s + 2.0 * ds2s + 2.0 * ds3s + ds4s)

        # Error estimate
        err_a = abs(a_full - a_two_half)
        err_x = abs(x_full - x_two_half)
        scale_a = max(abs(accumulated_thickness), abs(a_two_half), 1e-9)
        scale_x = max(abs(x_unwrapped), abs(x_two_half), 1e-9)
        rel_err = max(err_a / scale_a, err_x / scale_x)

        if rel_err > target_err and h > h_min * 1.01:
            h = max(h * shrink * max(0.2, (target_err / (rel_err + 1e-14)) ** 0.25), h_min)
            continue

        # Accept step
        accumulated_thickness = a_two_half
        x_unwrapped = x_two_half
        theta += h

        theta_out[n_pts] = theta
        r_out[n_pts] = mandrel_radius + accumulated_thickness
        x_out[n_pts] = x_unwrapped
        n_pts += 1

        if rel_err < target_err / 8.0 and h < h_max / 0.6:
            h = min(h * growth * min(2.0, (target_err / (rel_err + 1e-14)) ** 0.20), h_max)

        # Gradient-based step modulation
        if 0.0 < x_unwrapped < total_length:
            idx_f = x_unwrapped * (len(x_grid) - 1) / total_length
            idx = int(idx_f)
            if idx >= len(dt_dx) - 1:
                local_grad = abs(dt_dx[-1])
            else:
                frac = idx_f - idx
                local_grad = abs(dt_dx[idx] + frac * (dt_dx[idx + 1] - dt_dx[idx]))
        else:
            local_grad = 0.0
        grad_factor = 1.0 + 5.0 * (local_grad / max_grad)
        h = max(h / grad_factor, h_min)

    return theta_out[:n_pts], r_out[:n_pts], x_out[:n_pts]


@njit(cache=True)
def _racetrack_positions_batch(thetas, radii, straight_length):
    """Vectorised racetrack position calculation (numba-compiled).

    Maps parametric angles to (x, z) Cartesian coordinates on a racetrack shape.
    Operates on arrays for batch processing.
    """
    _TWO_PI = 2.0 * math.pi
    n = len(thetas)
    x_out = np.empty(n, dtype=np.float64)
    z_out = np.empty(n, dtype=np.float64)

    for i in range(n):
        theta = thetas[i] % _TWO_PI
        radius = radii[i]

        semi_arc = math.pi * radius
        total_perimeter = 2.0 * semi_arc + 2.0 * straight_length
        clockwise_fraction = (_TWO_PI - theta) / _TWO_PI
        arc_length = clockwise_fraction * total_perimeter

        if arc_length <= semi_arc:
            phi = arc_length / radius if radius > 0 else 0.0
            x_out[i] = straight_length / 2.0 + radius * math.cos(math.pi / 2.0 - phi)
            z_out[i] = radius * math.sin(math.pi / 2.0 - phi)
        elif arc_length <= semi_arc + straight_length:
            progress = (arc_length - semi_arc) / straight_length if straight_length > 0 else 0.0
            x_out[i] = straight_length / 2.0 - progress * straight_length
            z_out[i] = -radius
        elif arc_length <= 2.0 * semi_arc + straight_length:
            phi = (arc_length - semi_arc - straight_length) / radius if radius > 0 else 0.0
            angle = -math.pi / 2.0 - phi
            x_out[i] = -straight_length / 2.0 + radius * math.cos(angle)
            z_out[i] = radius * math.sin(angle)
        else:
            progress = (arc_length - 2.0 * semi_arc - straight_length) / straight_length if straight_length > 0 else 0.0
            x_out[i] = -straight_length / 2.0 + progress * straight_length
            z_out[i] = radius

    return x_out, z_out


class SpiralCalculator:
    """Utility class providing static methods for spiral and racetrack geometry calculations. Computes variable-thickness spirals, builds component-level spiral coordinates, and handles racetrack (flat-wound) geometry for FlatWoundJellyRoll assemblies."""

    @staticmethod
    def _insert_segment_gaps(
        data: np.ndarray,
        column_index: int,
        tolerance_multiplier: float = 10.0,
    ) -> np.ndarray:
        """Insert NaN rows at real discontinuities in a spiral array.

        Uses the **median** absolute step size (robust to the non-uniform
        spacing produced by adaptive RK4) instead of the mean that the
        generic ``CoordinateMixin.insert_gaps_with_nans`` method uses.
        A gap is declared when a step exceeds
        ``median(abs_steps) * tolerance_multiplier``.

        Parameters
        ----------
        data : np.ndarray
            2-D array of spiral data.
        column_index : int
            Column whose consecutive differences are tested for gaps.
        tolerance_multiplier : float, optional
            Factor applied to the median step to get the gap threshold
            (default 10.0).

        Returns
        -------
        np.ndarray
            Copy of *data* with NaN rows inserted at detected gaps.
        """
        if data.size == 0 or data.shape[0] < 2:
            return data.copy()

        col = data[:, column_index]
        valid = col[~np.isnan(col)]
        if len(valid) < 2:
            return data.copy()

        abs_steps = np.abs(np.diff(valid))
        median_step = np.median(abs_steps)
        if median_step == 0:
            return data.copy()

        threshold = median_step * tolerance_multiplier

        # Evaluate gaps on the original (possibly NaN-containing) column
        diffs = np.abs(np.diff(col))
        gap_mask = diffs > threshold  # True where a NaN row should follow
        gap_indices = np.flatnonzero(gap_mask)

        if gap_indices.size == 0:
            return data.copy()

        # Build result by interleaving original rows and NaN rows
        nan_row = np.full((1, data.shape[1]), np.nan)
        parts = []
        prev = 0
        for idx in gap_indices:
            parts.append(data[prev : idx + 1])  # rows up to and including the gap start
            parts.append(nan_row)
            prev = idx + 1
        parts.append(data[prev:])
        return np.vstack(parts)

    @staticmethod
    def calculate_variable_thickness_spiral(
        laminate: Laminate,
        start_radius: float,
        dtheta: Optional[float] = None,
        **kwargs
    ) -> np.ndarray:
        """Integrate a variable-thickness Archimedean-like spiral (clockwise) with adaptive RK4.

        Governing relations (parametrized by θ, clockwise so θ decreases from π/2):
            dr/dθ = t(x) / (2π)
            ds/dθ = sqrt(r² + (dr/dθ)²)         (local arc length rate)
            dx_unwrapped/dθ = ds/dθ              (treat unwrapped length x as accumulated arc length)

        With spatially varying thickness t(x) provided by layup.get_thickness_at_x(x).

        Improvements over prior implementation:
            - 4th order Runge–Kutta integration for coupled (r, x) system.
            - Adaptive step sizing via local Richardson error estimate (1 step h vs 2 half-steps).
            - Automatic fallback to analytic uniform-thickness solution when thickness variation is negligible.
            - Gradient-aware minimum step to avoid under-resolving rapid thickness changes.
            - Early termination and endpoint interpolation to land exactly on total unwrapped length.
            - Conservative iteration / memory limits to avoid runaway loops.

        Parameters
        ----------
        dtheta : float, optional
            Nominal (maximum) angular step magnitude (radians). Smaller steps are chosen adaptively as needed.
            If None, will look for 'dtheta' in kwargs, defaults to 0.5.
        **kwargs
            Additional keyword arguments. Can include 'dtheta' as alternative parameter specification.

        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z, turns]
            
        Raises
        ------
        ValueError
            If laminate total length is invalid or spiral calculation fails
        """
        # Handle dtheta parameter from kwargs if not explicitly provided
        if dtheta is None:
            dtheta = kwargs.get('dtheta', 0.5)
        assert dtheta is not None, "dtheta must be set from kwargs or argument"
        dtheta = float(dtheta)

        total_length = laminate._total_length
        r0 = start_radius
            
        # Build interpolation grid for thickness (vectorized)
        base_dl = max(dtheta * r0 / 8.0, 0.00025)
        n_grid = min(6000, max(400, int(total_length / base_dl) + 2))
        x_grid = np.linspace(0.0, total_length, n_grid)

        # Vectorized thickness grid: inline the laminate interpolation
        surface_xs = laminate._top_surface[:, 0]
        surface_zs = laminate._top_surface[:, 1]
        baseline_z = getattr(laminate, "_baseline_z", None)
        if baseline_z is None and hasattr(laminate, "_flattened_center_lines"):
            fcl = laminate._flattened_center_lines
            if "baseline" in fcl and len(fcl["baseline"]) > 0:
                baseline_z = fcl["baseline"][0, 1]
            else:
                baseline_z = 0.0
        top_z = np.interp(x_grid, surface_xs, surface_zs)
        t_grid = np.maximum(top_z - baseline_z, 0.0).astype(np.float64)

        t_min, t_max = float(t_grid.min()), float(t_grid.max())

        # ── Uniform-thickness fast path ──────────────────────────────────
        # When thickness variation is negligible, use the fully-vectorized
        # analytic Archimedean spiral (orders of magnitude faster).
        if t_max > 0 and (t_max - t_min) / t_max < 0.001:
            avg_thickness = float(t_grid.mean())
            simple = SpiralCalculator.calculate_simple_spiral(
                start_radius=r0,
                thickness=avg_thickness,
                target_length=total_length,
                points_per_turn=max(100, int(1.0 / dtheta * TWO_PI)),
            )
            return simple

        # ── Adaptive RK4 integration via numba-compiled loop ─────────────
        n_grid_m1 = n_grid - 1
        dx_inv = float(n_grid_m1 / total_length) if total_length > 0 else 0.0

        h_max = abs(dtheta)
        h_min = h_max / 64.0

        # Pre-compute rough gradient to modulate minimal step
        dt_dx = np.gradient(t_grid, x_grid).astype(np.float64)
        max_grad = float(np.max(np.abs(dt_dx))) + 1e-12

        theta_arr, r_arr, x_unwrapped_arr = _rk4_spiral_loop(
            t_grid, n_grid_m1, dx_inv, total_length,
            r0, h_max, h_min, TARGET_ERROR,
            MAX_ITERATIONS, MAX_POINTS,
            dt_dx, x_grid.astype(np.float64), max_grad,
        )

        # Interpolate final point if overshoot
        if len(x_unwrapped_arr) > 1 and x_unwrapped_arr[-1] > total_length:
            x_prev, x_curr = x_unwrapped_arr[-2], x_unwrapped_arr[-1]
            f = (total_length - x_prev) / (x_curr - x_prev + 1e-14)
            x_unwrapped_arr[-1] = total_length
            r_arr[-1] = r_arr[-2] + f * (r_arr[-1] - r_arr[-2])
            theta_arr[-1] = theta_arr[-2] + f * (theta_arr[-1] - theta_arr[-2])

        # Calculate number of turns: cumulative rotations from start (theta decreases from π/2)
        theta_start = np.pi / 2.0
        theta_traveled = theta_start - theta_arr  # positive
        turns_arr = theta_traveled / TWO_PI

        x_coords = r_arr * np.cos(theta_arr)
        z_coords = r_arr * np.sin(theta_arr)

        spiral = np.column_stack([theta_arr, x_unwrapped_arr, r_arr, x_coords, z_coords, turns_arr])

        return spiral

    @staticmethod
    def build_component_spirals(
        base_spiral: np.ndarray, 
        layup: Laminate, 
        mandrel_radius: float
        ) -> dict:
        """Build component spirals by mapping flattened center lines onto the wound spiral.
        
        Maps individual electrode and separator components from the layup onto the base
        spiral geometry, accounting for their specific thickness and positioning.
        
        Parameters
        ----------
        base_spiral : np.ndarray
            Base spiral coordinates [theta, x_unwrapped, r, x, z, turns]
        layup : Laminate
            The layup structure containing component center lines
        mandrel_radius : float
            Radius of the mandrel in meters
            
        Returns
        -------
        dict
            Component spirals keyed by component name
            
        Raises
        ------
        ValueError
            If component mapping fails or invalid geometry is encountered
        """
        component_spirals = {}

        # Component names in processing order
        component_names = [n for n in layup._flattened_center_lines.keys()]
        
        # Pre-compute all center line data to avoid repeated access
        center_line_data = {}
        for component_name in component_names:
            center_line = layup._flattened_center_lines[component_name]
            center_line_data[component_name] = {
                'x_coords': center_line[:, 0],
                'z_coords': center_line[:, 1],
                'x_min': np.min(center_line[:, 0]),
                'x_max': np.max(center_line[:, 0]),
            }
        
        # Process each component
        for component_name in component_names:
                
            # get the center line data
            cl_data = center_line_data[component_name]

            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, X_UNWRAPPED_COL]  # Extract x_unwrapped column

            # pad first and last row of cl_data with a row of NaNs
            component_x = cl_data['x_coords']
            component_x = np.concatenate(([np.nan], component_x, [np.nan]))

            # divide component x into groups based on the nan values
            isnan = np.isnan(component_x)
            edges = np.flatnonzero(np.diff(np.concatenate(([True], ~isnan, [True]))))
            segments = [component_x[start:end] for start, end in zip(edges[:-1], edges[1:]) if not np.isnan(component_x[start])]

            # create mask for each segment and combine them
            mask = np.zeros_like(x_unwrapped, dtype=bool)
            for segment in segments:
                x_min, x_max = np.min(segment), np.max(segment)
                mask |= (x_unwrapped >= x_min) & (x_unwrapped <= x_max)

            # Apply mask to get component spiral slice
            component_spiral = base_spiral[mask].copy()
            
            # Vectorized height calculation using numpy interpolation
            # This replaces the slow loop with a single vectorized operation
            x_vals = component_spiral[:, 1]
            z_unwrapped = np.interp(x_vals, cl_data['x_coords'], cl_data['z_coords'])
            height_adjustments = z_unwrapped - mandrel_radius
            
            # Update radius and coordinates in-place for efficiency
            component_spiral[:, 2] += height_adjustments  # Update radius
            
            # Vectorized coordinate recalculation
            theta_vals = component_spiral[:, 0]
            new_radii = component_spiral[:, 2]
            component_spiral[:, 3] = new_radii * np.cos(theta_vals)  # x coordinates
            component_spiral[:, 4] = new_radii * np.sin(theta_vals)  # z coordinates
            
            # Recalculate turns starting from 0 for this component
            theta_start_component = component_spiral[0, THETA_COL]  # Starting theta for this component
            theta_traveled_component = theta_start_component - component_spiral[:, THETA_COL]  # Angle traveled from component start
            component_spiral[:, TURNS_COL] = theta_traveled_component / TWO_PI  # Turns relative to component start

            # insert nan rows at real segment discontinuities
            component_spiral = SpiralCalculator._insert_segment_gaps(component_spiral, X_UNWRAPPED_COL)
            
            component_spirals[component_name] = component_spiral

        return component_spirals

    @staticmethod
    def build_extruded_component_spirals(
        component_spirals: dict, 
        component_thicknesses: dict,
        ) -> dict:
        """Build extruded component spirals by radially thickening center line spirals.
        
        For each component, creates a filled shape by:
        1. Taking the center line spiral from component_spirals
        2. Creating outer spiral by adding thickness/2 to radius
        3. Creating inner spiral by subtracting thickness/2 from radius
        4. Reversing inner spiral direction for proper winding
        5. Combining outer + inner spirals into a closed filled shape
        
        Parameters
        ----------
        component_spirals : dict
            Component spirals from build_component_spirals
        component_thicknesses : dict
            Thicknesses for each component
            
        Returns
        -------
        dict
            Extruded component spirals for 2D visualization
            
        Raises
        ------
        ValueError
            If extrusion calculation fails or invalid thickness values
        """
        extruded_spirals = {}

        components = [n for n in component_spirals.keys()]
        
        # Process each component that has a center line spiral
        for component_name in components:

            extruded_segments = []
            thickness = component_thicknesses.get(component_name, 0.0)
            center_spiral = component_spirals[component_name]
        
            # make into segments
            single_nan_row = np.array([[np.nan] * center_spiral.shape[1]])
            padded_spiral = np.vstack([single_nan_row, center_spiral, single_nan_row])
            isnan = np.isnan(padded_spiral[:, 1])
            edges = np.flatnonzero(np.diff(np.concatenate(([True], ~isnan, [True]))))
            segments = [padded_spiral[start:end] for start, end in zip(edges[:-1], edges[1:]) if not np.isnan(padded_spiral[start, 1])]

            for segment in segments:
                filled_spiral = SpiralCalculator._extrude_single_spiral(segment, thickness)
                filled_spiral = np.vstack([filled_spiral, single_nan_row])
                extruded_segments.append(filled_spiral)

            # remove last nan row if it exists to avoid trailing NaNs in the final spiral
            extruded_segments[-1] = extruded_segments[-1][:-1, :]
            extruded_spiral = np.vstack(extruded_segments)
            extruded_spirals[component_name] = extruded_spiral

        return extruded_spirals

    @staticmethod
    def _extrude_single_spiral(spiral, thickness) -> np.ndarray:

        half_thickness = thickness / 2.0
        outer_spiral = spiral.copy()
        outer_spiral[:, 2] += half_thickness  # Increase radius
        outer_spiral[:, 3] = outer_spiral[:, 2] * np.cos(outer_spiral[:, 0])  # x coordinates
        outer_spiral[:, 4] = outer_spiral[:, 2] * np.sin(outer_spiral[:, 0])  # z coordinates

        inner_spiral = spiral.copy()
        inner_spiral[:, 2] -= half_thickness  # Decrease radius
        inner_spiral[:, 3] = inner_spiral[:, 2] * np.cos(inner_spiral[:, 0])  # x coordinates
        inner_spiral[:, 4] = inner_spiral[:, 2] * np.sin(inner_spiral[:, 0])  # z coordinates

        inner_spiral_reversed = inner_spiral[::-1, :]

        # add transition padding points to smooth spline interpolation
        outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))
        inner_start_padding = np.tile(inner_spiral_reversed[0, :], (2, 1))

        # combine into filled shape: outer → padding → inner (reversed) → close
        if len(outer_spiral) > 0 and len(inner_spiral_reversed) > 0:
            filled_spiral = np.vstack([
                outer_spiral,           # Outer boundary
                outer_end_padding,      # Smooth transition
                inner_start_padding,    # Smooth transition  
                inner_spiral_reversed   # Inner boundary (reversed)
            ])
        else:
            filled_spiral = outer_spiral

        return filled_spiral

    @staticmethod
    def calculate_simple_spiral(
        n_turns: Optional[float] = None,
        start_radius: Optional[float] = None,
        thickness: Optional[float] = None,
        points_per_turn: int = 100,
        target_length: Optional[float] = None
    ) -> np.ndarray:
        """
        Calculate a simple uniform-thickness Archimedean spiral.
        
        This function generates a basic spiral with constant thickness increment
        per turn, useful for simple geometric calculations or as a baseline
        comparison for more complex variable-thickness spirals.
        
        Parameters
        ----------
        n_turns : float, optional
            Number of turns to generate. Either this or target_length must be provided, but not both.
        start_radius : float
            Starting radius in meters
        thickness : float 
            Constant thickness per turn in meters
        points_per_turn : int, optional
            Number of points per complete turn, by default 100
        target_length : float, optional
            Target unwrapped length in meters. Either this or n_turns must be provided, but not both.
            
        Returns
        -------
        np.ndarray
            Spiral coordinates with columns: [theta, x_unwrapped, r, x, z, turns]
            Same format as calculate_variable_thickness_spiral()
            
        Raises
        ------
        ValueError
            If both n_turns and target_length are provided, or if neither are provided,
            or if required parameters are missing.
        """
        # Validate input parameters
        if n_turns is not None and target_length is not None:
            raise ValueError("Cannot specify both n_turns and target_length. Please provide only one.")
        
        if n_turns is None and target_length is None:
            raise ValueError("Must specify either n_turns or target_length.")
        
        if start_radius is None or thickness is None:
            raise ValueError("start_radius and thickness are required parameters.")
        assert start_radius is not None and thickness is not None

        # Determine n_turns based on input
        if target_length is not None:
            # Rough overestimate: assume average radius is start_radius + some thickness buildup
            # For safety, use 50% more turns than the rough estimate
            avg_radius_estimate = start_radius + thickness * 2  # Conservative estimate
            rough_turns_estimate = target_length / (TWO_PI * avg_radius_estimate)
            n_turns = rough_turns_estimate * 1.5  # 50% overestimate for safety
        assert n_turns is not None, "n_turns must be set by here"

        # Calculate total angular span (clockwise, starting from π/2)
        total_angle = n_turns * TWO_PI
        n_points = int(n_turns * points_per_turn) + 1
        
        # Generate theta array (decreasing from π/2 for clockwise rotation)
        theta_start = np.pi/2
        theta_end = theta_start - total_angle
        theta_arr = np.linspace(theta_start, theta_end, n_points)
        
        # Calculate radius for uniform thickness spiral: r = start_radius + (thickness/(2π)) * angle_traveled
        angle_traveled = theta_start - theta_arr  # Positive angle traveled
        r_arr = start_radius + (thickness / TWO_PI) * angle_traveled
        
        # Calculate unwrapped length (arc length along spiral)
        # For Archimedean spiral: ds = sqrt(r² + (dr/dtheta)²) * dtheta
        # where dr/dtheta = thickness/(2π) = constant
        dr_dtheta = thickness / TWO_PI
        
        # Calculate incremental arc lengths
        ds_arr = np.zeros_like(theta_arr)
        dtheta = np.abs(np.diff(theta_arr))  # Angular increments (positive)
        r_mid = (r_arr[:-1] + r_arr[1:]) / 2  # Midpoint radii
        ds_increments = np.sqrt(r_mid**2 + dr_dtheta**2) * dtheta
        ds_arr[1:] = np.cumsum(ds_increments)
        
        # Calculate Cartesian coordinates
        x_coords = r_arr * np.cos(theta_arr)
        z_coords = r_arr * np.sin(theta_arr)
        
        # Calculate number of turns completed
        turns_arr = angle_traveled / TWO_PI
        
        # Assemble spiral array with same format as variable thickness spiral
        spiral = np.column_stack([
            theta_arr,      # Column 0: theta (radians)
            ds_arr,         # Column 1: x_unwrapped (arc length in meters)
            r_arr,          # Column 2: radius (meters) 
            x_coords,       # Column 3: x coordinate (meters)
            z_coords,       # Column 4: z coordinate (meters)
            turns_arr       # Column 5: turns completed
        ])
        
        # If target_length was specified, truncate spiral to exact length
        if target_length is not None:
            # Find points that exceed target length
            length_mask = ds_arr <= target_length
            
            if np.any(length_mask):
                # Get last point within target length
                last_valid_idx = np.where(length_mask)[0][-1]
                
                # Check if we need interpolation for exact length
                if last_valid_idx < len(ds_arr) - 1 and ds_arr[last_valid_idx] < target_length:
                    # Interpolate between last valid point and next point for exact target length
                    next_idx = last_valid_idx + 1
                    
                    # Linear interpolation factor
                    remaining_length = target_length - ds_arr[last_valid_idx]
                    segment_length = ds_arr[next_idx] - ds_arr[last_valid_idx]
                    
                    if segment_length > 1e-12:  # Avoid division by zero
                        interp_factor = remaining_length / segment_length
                        
                        # Interpolate all spiral parameters
                        interp_row = spiral[last_valid_idx] + interp_factor * (spiral[next_idx] - spiral[last_valid_idx])
                        interp_row[1] = target_length  # Set exact target length
                        
                        # Create truncated spiral with interpolated endpoint
                        spiral = np.vstack([spiral[:last_valid_idx+1], interp_row])
                    else:
                        # Edge case: just truncate at last valid point
                        spiral = spiral[:last_valid_idx+1]
                else:
                    # No interpolation needed, just truncate
                    spiral = spiral[:last_valid_idx+1]
            else:
                # Edge case: target length is very small, return just the first point
                spiral = spiral[:1]
        
        return spiral

    @staticmethod
    def calculate_variable_thickness_racetrack(
        laminate: Laminate,
        mandrel_radius: float,
        straight_length: float,
        ds_target: Optional[float] = None,
        **kwargs
    ) -> np.ndarray:
        """Calculate spiral path for given mandrel geometry parameters (clockwise direction).
        
        The racetrack consists of:
        - Two semicircular ends (radius = height/2)
        - Two straight sections (length = width - height)
        
        Calculates spiral in clockwise direction, consistent with WoundJellyRoll.
        
        Parameters
        ----------
        laminate : Laminate
            The layup structure containing thickness information
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters
        straight_length : float
            Length of straight sections (width - height) in meters
        ds_target : float, optional
            Target arc length step size in meters. If None, will look for 'ds_target' in kwargs, defaults to 0.5e-3.
        **kwargs
            Additional keyword arguments. Can include 'ds_target' as alternative parameter specification.
            
        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z, turns]
        """
        # Handle ds_target parameter from kwargs if not explicitly provided
        if ds_target is None:
            ds_target = kwargs.get('ds_target', 0.5e-3)
        assert ds_target is not None, "ds_target must be set from kwargs or argument"
        ds_target = float(ds_target)

        # Validate geometry for potential issues with squat (low aspect ratio) racetracks
        aspect_ratio = straight_length / mandrel_radius if mandrel_radius > 0 else float('inf')
        if aspect_ratio < 0.5:
            import warnings
            warnings.warn(
                f"Very squat racetrack geometry detected (aspect_ratio={aspect_ratio:.2f}, "
                f"straight_length={straight_length*1e3:.2f}mm, mandrel_radius={mandrel_radius*1e3:.2f}mm). "
                f"This may cause rendering issues with straight sections. Consider increasing mandrel width.",
                UserWarning
            )
        elif aspect_ratio < 2.0:
            import warnings
            warnings.warn(
                f"Squat racetrack geometry detected (aspect_ratio={aspect_ratio:.2f}). "
                f"Adaptive downsampling will be used to maintain straight section rendering quality.",
                UserWarning
            )

        total_length = laminate._total_length  # meters

        # Build fast thickness interpolator (vectorized, avoids per-step Python method calls)
        surface_xs = laminate._top_surface[:, 0]
        surface_zs = laminate._top_surface[:, 1]
        baseline_z = getattr(laminate, "_baseline_z", None)
        if baseline_z is None and hasattr(laminate, "_flattened_center_lines"):
            fcl = laminate._flattened_center_lines
            if "baseline" in fcl and len(fcl["baseline"]) > 0:
                baseline_z = fcl["baseline"][0, 1]
            else:
                baseline_z = 0.0

        n_t_grid = max(400, int(total_length / max(ds_target, 1e-6)) + 2)
        n_t_grid = min(6000, n_t_grid)
        t_x_grid = np.linspace(0.0, total_length, n_t_grid)
        t_z_interp = np.interp(t_x_grid, surface_xs, surface_zs)
        t_grid = np.maximum(t_z_interp - baseline_z, 0.0).astype(np.float64)

        t_min, t_max = float(t_grid.min()), float(t_grid.max())

        # ── Uniform-thickness fast path ──────────────────────────────────
        if t_max > 0 and (t_max - t_min) / t_max < 0.001:
            avg_thickness = float(t_grid.mean())
            simple = SpiralCalculator.calculate_simple_racetrack(
                start_radius=mandrel_radius,
                straight_length=straight_length,
                thickness=avg_thickness,
                target_length=total_length,
                points_per_turn=300,
            )
            return simple

        # ── Adaptive RK4 integration via numba-compiled loop ─────────────
        n_grid_m1 = n_t_grid - 1
        dx_inv = float(n_grid_m1 / total_length) if total_length > 0 else 0.0

        # Convert ds_target to an angular step for h_max
        perimeter_start = TWO_PI * mandrel_radius + 2.0 * straight_length
        h_max = min(0.5, ds_target * TWO_PI / (perimeter_start + 1e-12))
        h_min = h_max / 64.0

        dt_dx = np.gradient(t_grid, t_x_grid).astype(np.float64)
        max_grad = float(np.max(np.abs(dt_dx))) + 1e-12

        theta_arr, r_arr, x_unwrapped_arr = _rk4_racetrack_loop(
            t_grid, n_grid_m1, dx_inv, total_length,
            mandrel_radius, straight_length,
            mandrel_radius, h_max, h_min, TARGET_ERROR,
            MAX_ITERATIONS, MAX_POINTS,
            dt_dx, t_x_grid.astype(np.float64), max_grad,
        )

        # Interpolate final point if overshoot
        if len(x_unwrapped_arr) > 1 and x_unwrapped_arr[-1] > total_length:
            x_prev, x_curr = x_unwrapped_arr[-2], x_unwrapped_arr[-1]
            f = (total_length - x_prev) / (x_curr - x_prev + 1e-14)
            x_unwrapped_arr[-1] = total_length
            r_arr[-1] = r_arr[-2] + f * (r_arr[-1] - r_arr[-2])
            theta_arr[-1] = theta_arr[-2] + f * (theta_arr[-1] - theta_arr[-2])

        # theta_arr from the racetrack loop is cumulative angle traveled (positive, increasing)
        # Convert to racetrack parametric theta for position calculation
        # Use TWO_PI - (theta % TWO_PI) to get the racetrack angle
        turns_arr = theta_arr / TWO_PI

        # Calculate Cartesian coordinates using batch racetrack position
        # The racetrack_positions_batch expects parametric theta in [0, 2π], clockwise from 2π
        racetrack_thetas = TWO_PI - (theta_arr % TWO_PI)
        # Handle edge: when theta_arr % TWO_PI == 0, racetrack_theta = TWO_PI
        racetrack_thetas = np.where(racetrack_thetas < 1e-14, TWO_PI, racetrack_thetas)
        x_coords, z_coords = _racetrack_positions_batch(racetrack_thetas, r_arr, straight_length)

        spiral_array = np.column_stack([
            theta_arr, x_unwrapped_arr, r_arr, x_coords, z_coords, turns_arr
        ])

        # ── Vectorized downsampling ──────────────────────────────────────
        thetas_col = spiral_array[:, 0]
        radii_col = spiral_array[:, 2]

        thetas_mod = thetas_col % TWO_PI
        semi_arc_fractions = np.pi * radii_col
        total_perimeters = 2.0 * semi_arc_fractions + 2.0 * straight_length
        arc_lengths = (thetas_mod / TWO_PI) * total_perimeters

        is_curved = (
            (arc_lengths <= semi_arc_fractions) |
            ((semi_arc_fractions + straight_length <= arc_lengths) &
             (arc_lengths <= 2.0 * semi_arc_fractions + straight_length))
        )

        keep_mask = np.zeros(len(spiral_array), dtype=bool)
        keep_mask[0] = True
        keep_mask[-1] = True
        keep_mask[is_curved] = True

        straight_indices = np.where(~is_curved)[0]
        if len(straight_indices) > 0:
            num_straight_points = len(straight_indices)
            if len(spiral_array) > 0:
                max_turns = spiral_array[-1, TURNS_COL]
                total_straight_length = 2.0 * straight_length * max_turns if max_turns > 0 else straight_length
            else:
                total_straight_length = straight_length

            if total_straight_length > 0:
                actual_density = num_straight_points / total_straight_length
                if straight_length < 0.005:
                    target_density = 2000.0
                elif straight_length < 0.010:
                    target_density = 1500.0
                else:
                    target_density = 1000.0
                downsample_factor = max(1, int(actual_density / target_density))
            else:
                downsample_factor = 5

            keep_mask[straight_indices[::downsample_factor]] = True

        return spiral_array[keep_mask]

    @staticmethod
    def calculate_simple_racetrack(
        n_turns: Optional[float] = None,
        start_radius: Optional[float] = None,
        straight_length: Optional[float] = None,
        thickness: Optional[float] = None,
        points_per_turn: int = 300,
        target_length: Optional[float] = None
    ) -> np.ndarray:
        """
        Calculate a simple uniform-thickness racetrack spiral.
        
        This function generates a basic racetrack spiral with constant thickness increment
        per turn, useful for simple geometric calculations or as a baseline
        comparison for more complex variable-thickness racetracks.
        
        Parameters
        ----------
        n_turns : float, optional
            Number of turns to generate. Either this or target_length must be provided, but not both.
        start_radius : float
            Starting radius of semicircular ends in meters
        straight_length : float
            Length of straight sections in meters
        thickness : float
            Constant thickness per turn in meters
        points_per_turn : int, optional
            Number of points per complete turn, by default 100
        target_length : float, optional
            Target unwrapped length in meters. Either this or n_turns must be provided, but not both.
            
        Returns
        -------
        np.ndarray
            Racetrack coordinates with columns: [theta, x_unwrapped, r, x, z, turns]
            Same format as calculate_variable_thickness_racetrack()
            
        Raises
        ------
        ValueError
            If both n_turns and target_length are provided, or if neither are provided,
            or if required parameters are missing.
        """
        # Validate input parameters
        if n_turns is not None and target_length is not None:
            raise ValueError("Cannot specify both n_turns and target_length. Please provide only one.")
        
        if n_turns is None and target_length is None:
            raise ValueError("Must specify either n_turns or target_length.")
        
        if start_radius is None or straight_length is None or thickness is None:
            raise ValueError("start_radius, straight_length, and thickness are required parameters.")
        assert start_radius is not None and straight_length is not None and thickness is not None

        # Determine n_turns based on input
        if target_length is not None:
            # Estimate based on average perimeter
            avg_perimeter = TWO_PI * start_radius + 2 * straight_length
            # For safety, use 50% more turns than the rough estimate
            rough_turns_estimate = target_length / avg_perimeter
            n_turns = rough_turns_estimate * 1.5  # 50% overestimate for safety
        assert n_turns is not None, "n_turns must be set by here"

        # Calculate total perimeter for one complete turn at start radius
        perimeter_start = TWO_PI * start_radius + 2 * straight_length

        # Generate parametric coordinates
        n_points = int(n_turns * points_per_turn) + 1
        
        # For clockwise motion, start at theta=2π and decrease
        theta_start = TWO_PI
        total_angle = n_turns * TWO_PI
        theta_end = theta_start - total_angle
        theta_arr = np.linspace(theta_start, theta_end, n_points)
        
        # Calculate accumulated thickness based on turns completed
        angle_traveled = theta_start - theta_arr  # Positive angle traveled
        turns_completed = angle_traveled / TWO_PI
        accumulated_thickness = (thickness / TWO_PI) * angle_traveled
        current_radii = start_radius + accumulated_thickness
        
        # Calculate unwrapped length along racetrack path (vectorized)
        x_unwrapped_arr = np.zeros_like(theta_arr)
        if len(theta_arr) > 1:
            avg_radii = (current_radii[:-1] + current_radii[1:]) / 2.0
            dthetas = np.abs(np.diff(theta_arr))
            perimeters_avg = TWO_PI * avg_radii + 2.0 * straight_length
            ds_increments = (dthetas / TWO_PI) * perimeters_avg
            x_unwrapped_arr[1:] = np.cumsum(ds_increments)
        
        # Calculate Cartesian coordinates (vectorized batch)
        x_coords, z_coords = _racetrack_positions_batch(theta_arr, current_radii, straight_length)
        
        # Calculate number of turns completed
        turns_arr = turns_completed
        
        # Assemble racetrack array with same format as variable thickness racetrack
        racetrack = np.column_stack([
            theta_arr,          # Column 0: theta (parametric angle)
            x_unwrapped_arr,    # Column 1: x_unwrapped (arc length in meters)
            current_radii,      # Column 2: current radius (meters)
            x_coords,           # Column 3: x coordinate (meters)
            z_coords,           # Column 4: z coordinate (meters)
            turns_arr           # Column 5: turns completed
        ])
        
        # If target_length was specified, truncate racetrack to exact length
        if target_length is not None:
            # Find points that exceed target length
            length_mask = x_unwrapped_arr <= target_length
            
            if np.any(length_mask):
                # Get last point within target length
                last_valid_idx = np.where(length_mask)[0][-1]
                
                # Check if we need interpolation for exact length
                if last_valid_idx < len(x_unwrapped_arr) - 1 and x_unwrapped_arr[last_valid_idx] < target_length:
                    # Interpolate between last valid point and next point for exact target length
                    next_idx = last_valid_idx + 1
                    
                    # Linear interpolation factor
                    remaining_length = target_length - x_unwrapped_arr[last_valid_idx]
                    segment_length = x_unwrapped_arr[next_idx] - x_unwrapped_arr[last_valid_idx]
                    
                    if segment_length > 1e-12:  # Avoid division by zero
                        interp_factor = remaining_length / segment_length
                        
                        # Interpolate all racetrack parameters
                        interp_row = racetrack[last_valid_idx] + interp_factor * (racetrack[next_idx] - racetrack[last_valid_idx])
                        interp_row[1] = target_length  # Set exact target length
                        
                        # Create truncated racetrack with interpolated endpoint
                        racetrack = np.vstack([racetrack[:last_valid_idx+1], interp_row])
                    else:
                        # Edge case: just truncate at last valid point
                        racetrack = racetrack[:last_valid_idx+1]
                else:
                    # No interpolation needed, just truncate
                    racetrack = racetrack[:last_valid_idx+1]
            else:
                # Edge case: target length is very small, return just the first point
                racetrack = racetrack[:1]
        
        return racetrack

    @staticmethod
    def racetrack_position(theta: float, radius: float, straight_length: float) -> tuple:
        """Calculate x,z position on racetrack at given parametric angle (clockwise direction).
        
        For clockwise motion starting at top-right:
        - theta=2π: top of right semicircle 
        - theta=3π/2: right side
        - theta=π: bottom of right semicircle
        - theta=π/2: bottom of left semicircle
        - theta=0: top of left semicircle
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π), decreases clockwise from 2π
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (x_position, z_position) in meters
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate total perimeter proportions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        
        # For clockwise motion, map theta to arc_length position around perimeter
        # Start at theta=2π (top right) and go clockwise
        # Convert to arc position: theta=2π -> 0, theta=3π/2 -> π/4*perimeter, etc.
        clockwise_fraction = (2 * np.pi - theta) / (2 * np.pi)
        arc_length = clockwise_fraction * total_perimeter
        
        if arc_length <= semi_arc_length:
            # Right semicircle (starting from top, going clockwise)
            phi = arc_length / radius  # Actual geometric angle from top
            x = straight_length/2 + radius * np.cos(np.pi/2 - phi)  # Start at top (π/2), go clockwise
            z = radius * np.sin(np.pi/2 - phi)
            
        elif arc_length <= semi_arc_length + straight_length:
            # Bottom straight section (right to left)
            progress = (arc_length - semi_arc_length) / straight_length
            x = straight_length/2 - progress * straight_length
            z = -radius
            
        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle (bottom to top, clockwise)
            phi = (arc_length - semi_arc_length - straight_length) / radius
            # For left semicircle, start at bottom (-π/2) and go clockwise (decreasing angle)
            angle = -np.pi/2 - phi  # Start at -π/2, go clockwise (more negative)
            x = -straight_length/2 + radius * np.cos(angle)  # Center at -straight_length/2
            z = radius * np.sin(angle)
            
        else:
            # Top straight section (left to right)
            progress = (arc_length - 2 * semi_arc_length - straight_length) / straight_length
            x = -straight_length/2 + progress * straight_length
            z = radius
        
        return x, z

    @staticmethod
    def racetrack_curvature(theta: float, radius: float, straight_length: float) -> float:
        """Calculate curvature at given position on racetrack.
        
        Parameters
        ----------
        theta : float
            Parametric angle (0 to 2π)
        radius : float
            Current layer radius
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        float
            Curvature (1/radius on curves, 0 on straight sections)
        """
        # Normalize theta to [0, 2π)
        theta = theta % (2 * np.pi)
        
        # Calculate position fractions
        semi_arc_length = np.pi * radius
        total_perimeter = 2 * semi_arc_length + 2 * straight_length
        fraction = theta / (2 * np.pi)
        arc_length = fraction * total_perimeter
        
        # Determine if on curved or straight section
        if (arc_length <= semi_arc_length or 
            (semi_arc_length + straight_length <= arc_length <= 2 * semi_arc_length + straight_length)):
            # On semicircular sections
            return 1.0 / radius if radius > 0 else 0.0
        else:
            # On straight sections
            return 0.0

    @staticmethod
    def build_extruded_component_racetracks(
            component_spirals: dict, 
            component_thicknesses: dict,
            mandrel_radius: float, 
            straight_length: float) -> dict:
        """Build extruded component spirals for a given component spirals dictionary and mandrel geometry.
        
        This is a generalized version of build_extruded_component_spirals that can work with
        any component spirals dictionary and mandrel geometry parameters, used for hot-pressed spirals.
        
        Parameters
        ----------
        component_spirals : dict
            Component spirals dictionary to extrude
        component_thicknesses : dict
            Thicknesses for each component
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters
        straight_length : float
            Length of straight sections (width - height) in meters
            
        Returns
        -------
        dict
            Extruded component spirals dictionary
        """
        extruded_spirals = {}
        
        # Process each component that has a center line spiral
        for component_name, thickness in component_thicknesses.items():
            if component_name not in component_spirals:
                # Skip missing components
                extruded_spirals[component_name] = np.empty((0, 6))
                continue
                
            center_spiral = component_spirals[component_name]
            
            if len(center_spiral) == 0:
                # Skip empty components
                extruded_spirals[component_name] = np.empty((0, 6))
                continue

            extruded_segments = []
            
            # make into segments
            single_nan_row = np.array([[np.nan] * center_spiral.shape[1]])
            padded_spiral = np.vstack([single_nan_row, center_spiral, single_nan_row])
            isnan = np.isnan(padded_spiral[:, 1])
            edges = np.flatnonzero(np.diff(np.concatenate(([True], ~isnan, [True]))))
            segments = [padded_spiral[start:end] for start, end in zip(edges[:-1], edges[1:]) if not np.isnan(padded_spiral[start, 1])]

            for segment in segments:
                filled_spiral = SpiralCalculator._extrude_single_racetrack(segment, thickness, mandrel_radius, straight_length)
                filled_spiral = np.vstack([filled_spiral, single_nan_row])
                extruded_segments.append(filled_spiral)

            # remove last nan row if it exists to avoid trailing NaNs in the final spiral
            extruded_segments[-1] = extruded_segments[-1][:-1, :]
            extruded_spiral = np.vstack(extruded_segments)
            extruded_spirals[component_name] = extruded_spiral

        return extruded_spirals

    @staticmethod
    def _extrude_single_racetrack(spiral, thickness, mandrel_radius, straight_length) -> np.ndarray:

        half_thickness = thickness / 2.0
        
        # Create outer and inner spirals with proper flat mandrel thickness application
        outer_spiral, inner_spiral = SpiralCalculator.create_flat_mandrel_thickness_spirals(
            spiral, half_thickness, mandrel_radius, straight_length
        )
        
        # Reverse inner spiral direction for proper winding (creates closed shape)
        inner_spiral_reversed = inner_spiral[::-1, :]
        
        # Add transition padding points to smooth spline interpolation
        # Duplicate end points to create smooth transitions
        outer_end_padding = np.tile(outer_spiral[-1, :], (2, 1))
        inner_start_padding = np.tile(inner_spiral_reversed[0, :], (2, 1))
        
        # Combine into filled shape: outer → padding → inner (reversed) → close
        if len(outer_spiral) > 0 and len(inner_spiral_reversed) > 0:
            filled_spiral = np.vstack([
                outer_spiral,           # Outer boundary
                outer_end_padding,      # Smooth transition
                inner_start_padding,    # Smooth transition  
                inner_spiral_reversed   # Inner boundary (reversed)
            ])
        else:
            # Fallback for edge cases
            filled_spiral = outer_spiral

        return filled_spiral

    @staticmethod
    def create_flat_mandrel_thickness_spirals(center_spiral: np.ndarray, half_thickness: float,
                                             mandrel_radius: float, straight_length: float) -> tuple:
        """Create outer and inner spirals by applying thickness in correct directions.
        
        Parameters
        ----------
        center_spiral : np.ndarray
            Center line spiral coordinates
        half_thickness : float
            Half of the component thickness
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple
            (outer_spiral, inner_spiral) as numpy arrays
        """
        outer_spiral = center_spiral.copy()
        inner_spiral = center_spiral.copy()
        
        xs = center_spiral[:, 3]
        zs = center_spiral[:, 4]
        
        # Vectorized direction computation
        dir_x, dir_z = SpiralCalculator._get_adjustment_directions_batch(
            xs, zs, mandrel_radius, straight_length
        )
        
        # Apply thickness offset in batch
        outer_spiral[:, 3] = xs + half_thickness * dir_x
        outer_spiral[:, 4] = zs + half_thickness * dir_z
        outer_spiral[:, 2] = np.sqrt(outer_spiral[:, 3]**2 + outer_spiral[:, 4]**2)
        
        inner_spiral[:, 3] = xs - half_thickness * dir_x
        inner_spiral[:, 4] = zs - half_thickness * dir_z
        inner_spiral[:, 2] = np.sqrt(inner_spiral[:, 3]**2 + inner_spiral[:, 4]**2)
        
        return outer_spiral, inner_spiral

    @staticmethod
    def get_coordinate_based_adjustment_direction(x: float, z: float, mandrel_radius: float,
                                                 straight_length: float) -> np.ndarray:
        """Get the direction vector for height adjustment based on actual coordinates.
        
        This method determines the adjustment direction by analyzing the actual position
        rather than using parametric angles, which avoids bunching issues on curved sections.
        
        Parameters
        ----------
        x : float
            Current x coordinate
        z : float
            Current z coordinate  
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        np.ndarray
            Unit vector [dx, dz] indicating direction for height adjustment
        """
        # Delegate to batch function for a single point
        dx, dz = SpiralCalculator._get_adjustment_directions_batch(
            np.array([x]), np.array([z]), mandrel_radius, straight_length
        )
        return np.array([dx[0], dz[0]])

    @staticmethod
    def _get_adjustment_directions_batch(xs: np.ndarray, zs: np.ndarray,
                                         mandrel_radius: float,
                                         straight_length: float):
        """Vectorized direction computation for all points at once.
        
        Classifies each point into right-semicircle, left-semicircle,
        top-straight, or bottom-straight using boolean masks and computes
        the outward-normal direction vector in one pass.
        
        Parameters
        ----------
        xs : np.ndarray
            X coordinates of all points
        zs : np.ndarray
            Z coordinates of all points
        mandrel_radius : float
            Radius of semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        tuple of (np.ndarray, np.ndarray)
            (direction_x, direction_z) arrays
        """
        n = len(xs)
        dir_x = np.zeros(n)
        dir_z = np.zeros(n)
        
        right_center_x = straight_length / 2.0
        left_center_x = -straight_length / 2.0
        straight_tolerance = mandrel_radius * 0.1
        
        # Right semicircle
        right_mask = xs > (straight_length / 2.0 - straight_tolerance)
        if np.any(right_mask):
            dx_r = xs[right_mask] - right_center_x
            dz_r = zs[right_mask]
            dist_r = np.sqrt(dx_r**2 + dz_r**2)
            safe_r = np.where(dist_r > 1e-12, dist_r, 1.0)
            dir_x[right_mask] = np.where(dist_r > 1e-12, dx_r / safe_r, 0.0)
            dir_z[right_mask] = np.where(dist_r > 1e-12, dz_r / safe_r, 1.0)
        
        # Left semicircle
        left_mask = (~right_mask) & (xs < (-straight_length / 2.0 + straight_tolerance))
        if np.any(left_mask):
            dx_l = xs[left_mask] - left_center_x
            dz_l = zs[left_mask]
            dist_l = np.sqrt(dx_l**2 + dz_l**2)
            safe_l = np.where(dist_l > 1e-12, dist_l, 1.0)
            dir_x[left_mask] = np.where(dist_l > 1e-12, dx_l / safe_l, 0.0)
            dir_z[left_mask] = np.where(dist_l > 1e-12, dz_l / safe_l, 1.0)
        
        # Straight sections (everything else)
        straight_mask = (~right_mask) & (~left_mask)
        if np.any(straight_mask):
            top = straight_mask & (zs > 0)
            bottom = straight_mask & (zs <= 0)
            dir_z[top] = 1.0
            dir_z[bottom] = -1.0
            # dir_x stays 0.0 for straight sections
        
        return dir_x, dir_z

    @staticmethod
    def get_thickness_of_racetrack(coords: np.ndarray) -> float:
        """Calculate the thickness of a racetrack given its coordinates.
        
        Parameters
        ----------
        coords : np.ndarray
            Array of shape (N, 2) with columns [x, z]
            
        Returns
        -------
        float
            Thickness (z-dimension span) in meters
        """
        # Filter out NaN values before computing min/max
        z_coords = coords[:, 1]
        valid_z = z_coords[~np.isnan(z_coords)]
        max_z = valid_z.max()
        min_z = valid_z.min()
        return max_z - min_z

    @staticmethod
    def get_width_of_racetrack(coords: np.ndarray) -> float:
        """Calculate the width of a racetrack given its coordinates.
        
        Parameters
        ----------
        coords : np.ndarray
            Array of shape (N, 2) with columns [x, z]
            
        Returns
        -------
        float
            Width (x-dimension span) in meters
        """
        # Filter out NaN values before computing min/max
        x_coords = coords[:, 0]
        valid_x = x_coords[~np.isnan(x_coords)]
        max_x = valid_x.max()
        min_x = valid_x.min()
        return max_x - min_x

    @staticmethod
    def format_np_spiral_for_df(np_array: np.ndarray) -> pd.DataFrame:
        """Format numpy spiral array into pandas DataFrame with proper units and column names.

        Parameters
        ----------
        np_array : np.ndarray
            Spiral array with columns [theta, x_unwrapped, r, x, z, turns]
            
        Returns
        -------
        pd.DataFrame
            Formatted DataFrame with columns: theta (degrees), x_unwrapped (mm), 
            r (mm), x (mm), z (mm), turns
            
        Raises
        ------
        ValueError
            If input array has incorrect shape or invalid data
        """   
        # Pre-compute all conversions in numpy (much faster than pandas operations)
        # Handle NaN values properly during conversions
        theta_raw = np_array[:, THETA_COL]
        theta_deg = np.where(np.isnan(theta_raw), np.nan, np.abs(theta_raw * (180.0 / PI) - 90))
        
        x_unwrapped_raw = np_array[:, X_UNWRAPPED_COL]
        # Calculate min only from non-NaN values for proper offset
        valid_x_unwrapped = x_unwrapped_raw[~np.isnan(x_unwrapped_raw)]
        x_min = np.min(valid_x_unwrapped) if len(valid_x_unwrapped) > 0 else 0.0
        length_mm = np.where(np.isnan(x_unwrapped_raw), np.nan, (x_unwrapped_raw - x_min) * M_TO_MM)
        
        r_mm = np.where(np.isnan(np_array[:, RADIUS_COL]), np.nan, np_array[:, RADIUS_COL] * M_TO_MM)
        x_mm = np.where(np.isnan(np_array[:, X_COORD_COL]), np.nan, np_array[:, X_COORD_COL] * M_TO_MM)
        z_mm = np.where(np.isnan(np_array[:, Z_COORD_COL]), np.nan, np_array[:, Z_COORD_COL] * M_TO_MM)
        turns = np.where(np.isnan(np_array[:, TURNS_COL]), np.nan, np_array[:, TURNS_COL])
        
        # Create DataFrame with NaN values preserved (pandas will convert NaN to None where appropriate)
        df = pd.DataFrame({
            "Theta (degrees)": theta_deg,
            "Unwrapped Length (mm)": length_mm,
            "Radius (mm)": r_mm,
            "X (mm)": x_mm,
            "Z (mm)": z_mm,
            "Turns": turns,
        })
        
        # Convert NaN to None for better representation in pandas
        df = df.where(pd.notna(df), None)
        
        return df

    @staticmethod  
    def build_component_racetracks(base_spiral, layup, mandrel_radius, straight_length, original_mandrel_radius):
        """
        Build component spirals for racetrack geometry based on a base spiral.
        
        This is a generalized version that can work with any mandrel geometry parameters,
        used for hot-pressed spirals in flat wound jelly rolls.
        
        Parameters
        ----------
        base_spiral : np.ndarray
            Base spiral to map components onto
        layup : Laminate
            Layup object containing component names and flattened center lines
        mandrel_radius : float
            Radius of semicircular ends (height/2) in meters (pressed radius)
        straight_length : float
            Length of straight sections (width - height) in meters
        original_mandrel_radius : float
            Original mandrel radius before pressing in meters
            
        Returns
        -------
        dict 
            Component spirals dictionary mapping component names to their spiral arrays
        """
        component_spirals = {}
        
        # Component names in processing order
        component_names = [n for n in layup._flattened_center_lines.keys()]
        
        # Pre-compute all center line data to avoid repeated access
        center_line_data = {}
        for component_name in component_names:
            center_line = layup._flattened_center_lines[component_name]
            center_line_data[component_name] = {
                'x_coords': center_line[:, 0],
                'z_coords': center_line[:, 1],
                'x_min': np.min(center_line[:, 0]),
                'x_max': np.max(center_line[:, 0])
            }
    
        # Process each component
        for component_name in component_names:

            cl_data = center_line_data[component_name]
            
            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, 1]  # Extract x_unwrapped column

            # pad first and last row of cl_data with a row of NaNs
            component_x = cl_data['x_coords']
            component_x = np.concatenate(([np.nan], component_x, [np.nan]))

            # divide component x into groups based on the nan values
            isnan = np.isnan(component_x)
            edges = np.flatnonzero(np.diff(np.concatenate(([True], ~isnan, [True]))))
            segments = [component_x[start:end] for start, end in zip(edges[:-1], edges[1:]) if not np.isnan(component_x[start])]

            # create mask for each segment and combine them
            mask = np.zeros_like(x_unwrapped, dtype=bool)
            for segment in segments:
                x_min, x_max = np.min(segment), np.max(segment)
                mask |= (x_unwrapped >= x_min) & (x_unwrapped <= x_max)
            
            # Apply mask to get component spiral slice
            component_spiral = base_spiral[mask].copy()
            
            # Vectorized height calculation using numpy interpolation
            x_vals = component_spiral[:, 1]
            z_unwrapped = np.interp(x_vals, cl_data['x_coords'], cl_data['z_coords'])
            height_adjustments = z_unwrapped - original_mandrel_radius
            
            # Apply height adjustments in correct direction based on racetrack position
            component_spiral = SpiralCalculator.apply_flat_mandrel_height_adjustments(
                component_spiral, height_adjustments, mandrel_radius, straight_length
            )
            
            # Recalculate turns starting from 0 for this component
            theta_start_component = component_spiral[0, 0]  # Starting theta for this component
            theta_traveled_component = component_spiral[:, 0] - theta_start_component  # Angle traveled from component start
            component_spiral[:, 5] = theta_traveled_component / (2 * np.pi)  # Turns relative to component start

            # insert nan rows at real segment discontinuities
            component_spiral = SpiralCalculator._insert_segment_gaps(component_spiral, X_UNWRAPPED_COL)
        
            component_spirals[component_name] = component_spiral

        return component_spirals

    @staticmethod
    def apply_flat_mandrel_height_adjustments(spiral, height_adjustments, mandrel_radius, straight_length):
        """Apply height adjustments to spiral points based on their position on the racetrack.
        
        Parameters
        ----------
        spiral : np.ndarray
            Component spiral array (modified in-place)
        height_adjustments : np.ndarray
            Height adjustments to apply at each point
        mandrel_radius : float
            Radius of the semicircular ends
        straight_length : float
            Length of straight sections
            
        Returns
        -------
        np.ndarray
            Modified spiral array
        """
        xs = spiral[:, 3]
        zs = spiral[:, 4]
        
        dir_x, dir_z = SpiralCalculator._get_adjustment_directions_batch(
            xs, zs, mandrel_radius, straight_length
        )
        
        spiral[:, 3] = xs + height_adjustments * dir_x
        spiral[:, 4] = zs + height_adjustments * dir_z
        spiral[:, 2] = np.sqrt(spiral[:, 3]**2 + spiral[:, 4]**2)

        return spiral

    @staticmethod
    def rotate_spiral_to_minimize_thickness(
        spiral_data,
        x_col: int = X_COORD_COL,
        z_col: int = Z_COORD_COL
    ):
        """Rotate spiral data in x-z plane to minimize overall thickness.

        Uses Brent's method to find the rotation angle that minimizes the
        vertical extent (thickness = max(z) - min(z)). The rotation is applied
        in-place to the spiral data.

        Parameters
        ----------
        spiral_data : Union[np.ndarray, Dict[str, np.ndarray]]
            Either a single spiral array or a dictionary of spiral arrays.
            Each array should have columns including x and z coordinates.
        x_col : int, optional
            Column index for x coordinates (default: X_COORD_COL)
        z_col : int, optional
            Column index for z coordinates (default: Z_COORD_COL)

        Returns
        -------
        Tuple[Union[np.ndarray, Dict[str, np.ndarray]], float]
            (rotated_spiral_data, optimal_angle) where optimal_angle is in radians

        Notes
        -----
        - Rotation is performed about the centroid of all points.
        - Optimization searches over [0, π) since thickness is symmetric about π.
        - Modifies spiral_data in-place and returns it for convenience.
        """
        from scipy.optimize import minimize_scalar
        
        # Collect all x-z points, filtering out NaN values
        if isinstance(spiral_data, dict):
            arrays = [arr[:, [x_col, z_col]] for arr in spiral_data.values() if arr is not None and arr.size > 0]
            if len(arrays) == 0:
                return spiral_data, 0.0
            points = np.vstack(arrays)
        elif isinstance(spiral_data, np.ndarray):
            if spiral_data.size == 0:
                return spiral_data, 0.0
            points = spiral_data[:, [x_col, z_col]]
        else:
            raise TypeError(f"spiral_data must be np.ndarray or dict, got {type(spiral_data)}")

        # Filter out rows with NaN values for centroid calculation
        valid_mask = ~(np.isnan(points[:, 0]) | np.isnan(points[:, 1]))
        valid_points = points[valid_mask]
        
        if len(valid_points) == 0:
            # All points are NaN, nothing to rotate
            return spiral_data, 0.0

        # Compute centroid from valid points only
        centroid = valid_points.mean(axis=0)
        valid_points_centered = valid_points - centroid

        def compute_thickness_at_angle(angle: float) -> float:
            """Compute thickness (z-extent) for a given rotation angle."""
            c, s = np.cos(angle), np.sin(angle)
            R = np.array([[c, -s], [s, c]])
            rotated = valid_points_centered @ R.T
            z_rotated = rotated[:, 1]
            thickness = np.max(z_rotated) - np.min(z_rotated)
            return thickness

        # Use Brent's method (via minimize_scalar) to find angle that minimizes thickness
        result = minimize_scalar(compute_thickness_at_angle, bounds=(0, np.pi), method='bounded')
        optimal_angle = float(result.x)  # type: ignore[union-attr]

        # Apply the optimal rotation to the spiral data
        c, s = np.cos(optimal_angle), np.sin(optimal_angle)
        R = np.array([[c, -s], [s, c]])

        def rotate_inplace(arr: np.ndarray) -> None:
            """Rotate x-z coordinates in array in-place, preserving NaN values."""
            if arr is None or arr.size == 0:
                return
            
            # Get x-z coordinates
            xz = arr[:, [x_col, z_col]]
            
            # Identify valid (non-NaN) rows
            valid_mask = ~(np.isnan(xz[:, 0]) | np.isnan(xz[:, 1]))
            
            if not np.any(valid_mask):
                # All values are NaN, nothing to rotate
                return
            
            # Only rotate valid points
            xz_valid = xz[valid_mask]
            xz_centered = xz_valid - centroid
            xz_rot = xz_centered @ R.T + centroid
            
            # Update only the valid points, preserving NaN where they existed
            arr[valid_mask, x_col] = xz_rot[:, 0]
            arr[valid_mask, z_col] = xz_rot[:, 1]

        if isinstance(spiral_data, dict):
            for arr in spiral_data.values():
                rotate_inplace(arr)
        else:
            rotate_inplace(spiral_data)

        return spiral_data, optimal_angle

    @staticmethod
    def translate_spirals_xz(
        spiral_data,
        x_shift: float,
        z_shift: float,
        x_col: int = X_COORD_COL,
        z_col: int = Z_COORD_COL
    ):
        """Translate spiral coordinates by specified amounts in x and z directions.
        
        This function applies a rigid body translation to spiral geometries.
        Commonly used for centering spirals or aligning them to a coordinate system.
        
        Parameters
        ----------
        spiral_data : Union[np.ndarray, Dict[str, np.ndarray]]
            Either a single spiral array or a dictionary of spiral arrays.
            Each array should have columns including x and z coordinates.
        x_shift : float
            Translation distance in x-direction (meters)
        z_shift : float
            Translation distance in z-direction (meters)
        x_col : int, optional
            Column index for x coordinates (default: X_COORD_COL)
        z_col : int, optional
            Column index for z coordinates (default: Z_COORD_COL)
            
        Returns
        -------
        Union[np.ndarray, Dict[str, np.ndarray]]
            Translated spiral data (modified in-place and returned)
            
        Notes
        -----
        - Modifies spiral_data in-place and returns it for convenience
        - Works with both single arrays and dictionaries of arrays
        """
        if isinstance(spiral_data, dict):
            for spiral in spiral_data.values():
                if spiral is not None and spiral.size > 0:
                    spiral[:, x_col] += x_shift
                    spiral[:, z_col] += z_shift
        elif isinstance(spiral_data, np.ndarray):
            if spiral_data.size > 0:
                spiral_data[:, x_col] += x_shift
                spiral_data[:, z_col] += z_shift
        else:
            raise TypeError(f"spiral_data must be np.ndarray or dict, got {type(spiral_data)}")
        
        return spiral_data
    


