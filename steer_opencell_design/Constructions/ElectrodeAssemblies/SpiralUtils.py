# SPDX-FileCopyrightText: 2024-2026 Stanford University
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

_NJIT_KW = {
    "cache": True,
    # ``fastmath=True`` allows FP reordering on the remaining numba helpers;
    # the winding kernel itself lives in ``Winding.py``.
    "fastmath": True,
    "error_model": "numpy",
    "boundscheck": False,
}



@njit(**_NJIT_KW)
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
            progress = (
                (arc_length - semi_arc) / straight_length
                if straight_length > 0
                else 0.0
            )
            x_out[i] = straight_length / 2.0 - progress * straight_length
            z_out[i] = -radius
        elif arc_length <= 2.0 * semi_arc + straight_length:
            phi = (
                (arc_length - semi_arc - straight_length) / radius
                if radius > 0
                else 0.0
            )
            angle = -math.pi / 2.0 - phi
            x_out[i] = -straight_length / 2.0 + radius * math.cos(angle)
            z_out[i] = radius * math.sin(angle)
        else:
            progress = (
                (arc_length - 2.0 * semi_arc - straight_length) / straight_length
                if straight_length > 0
                else 0.0
            )
            x_out[i] = -straight_length / 2.0 + progress * straight_length
            z_out[i] = radius

    return x_out, z_out



# ─── Phase 3: segmented analytic integrator ─────────────────────────────────
#
# The thickness function ``t(x)`` is built by ``Laminate.calculate_flattened_
# center_lines`` as a sum of per-layer indicator masks, so the underlying
# function has only O(few) distinct levels (in our 3 bench cases, 5 runs of
# constant thickness). Within each constant-thickness segment the spiral and
# racetrack ODEs admit a closed-form integral, so we can integrate the *whole
# laminate* in just a handful of analytic solves and then sample inside each
# segment for visualization fidelity. This makes the per-segment cost O(1)
# instead of "adaptive RK23 until total_length", and the output sampling
# becomes a deterministic vectorized ``np.linspace`` inside each segment.
#
# Spiral (constant ``t``):
#   dr/dθ = a, where a = t / (2π); for the clockwise convention θ decreases
#   while r increases, so r(θ) = r_s + a * (θ_s - θ).
#   ds/dθ = sqrt(r² + a²) ⇒ s(θ) - s_s = (1/a) * [F(r) - F(r_s)] where
#   F(v) = (v/2)·sqrt(v² + a²) + (a²/2)·ln(v + sqrt(v² + a²)).
#   Inverting F(r_target) = K is a single Newton iteration (F' = sqrt(v²+a²),
#   monotonic, converges in 2-3 steps from a linear initial guess).
#
# Racetrack (constant ``t``):
#   da/dθ = a' = t / (2π); ds/dθ = (R + a) + S/π is linear in θ ⇒ s is
#   quadratic in (θ - θ_s). Closed-form root via the quadratic formula.



# Module-level toggle so the bench harness and regression test can swap
# implementations for an apples-to-apples comparison without re-importing.

class SpiralCalculator:
    """Utility class providing static methods for spiral and racetrack geometry calculations. Computes variable-thickness spirals, builds component-level spiral coordinates, and handles racetrack (flat-wound) geometry for FlatWoundJellyRoll assemblies."""


    @staticmethod
    def aligned_positions_at_x(
        spiral: np.ndarray,
        target_x: float,
        tab_width: float = 0.0,
    ) -> np.ndarray:
        """Return two unwrapped centers per complete turn at a fixed x-coordinate.

        Length inputs and outputs use meters. ``target_x`` is expressed in the
        supplied spiral's unrotated racetrack coordinate system. The turn
        column, which is derived from winding phase, separates successive
        turns. A complete turn crosses ``target_x`` once on each straight
        branch, producing one notch on either side of the racetrack's z-axis.
        Partial turns without both crossings are omitted.

        Keeping ``target_x`` far enough inside a straight racetrack section for
        the whole tab is the caller's responsibility (see
        ``FlatWoundJellyRoll._notch_alignment_target_x``). On a straight branch
        z is constant, so unwrapped distance and x-distance are identical there
        and no separate endpoint projection is needed.
        """
        spiral = np.asarray(spiral, dtype=float)
        if spiral.ndim != 2 or spiral.shape[1] <= TURNS_COL:
            raise ValueError(
                "spiral must be a two-dimensional array containing unwrapped "
                "length, x-coordinate, and turn columns."
            )
        if not np.isfinite(target_x):
            raise ValueError("target_x must be finite.")
        if not np.isfinite(tab_width) or tab_width < 0:
            raise ValueError("tab_width must be a finite non-negative value.")
        if len(spiral) < 2:
            return np.empty(0, dtype=float)

        x_unwrapped = spiral[:, X_UNWRAPPED_COL]
        x_coordinate = spiral[:, X_COORD_COL]
        turns = spiral[:, TURNS_COL]

        finite = (
            np.isfinite(x_unwrapped) & np.isfinite(x_coordinate) & np.isfinite(turns)
        )
        x_start = x_coordinate[:-1]
        x_end = x_coordinate[1:]

        # Each interior x-coordinate occurs on both straight sections. Their
        # opposite traversal directions distinguish the +z and -z crossings.
        crossings = (
            (finite[:-1] & finite[1:])
            & (x_end != x_start)
            & (np.minimum(x_start, x_end) <= target_x)
            & (target_x <= np.maximum(x_start, x_end))
        )
        index = np.flatnonzero(crossings)
        if len(index) == 0:
            return np.empty(0, dtype=float)

        fraction = (target_x - x_start[index]) / (x_end[index] - x_start[index])
        centers = x_unwrapped[index] + fraction * (
            x_unwrapped[index + 1] - x_unwrapped[index]
        )
        turn_ids = np.floor((turns[index] + turns[index + 1]) / 2 + 1e-12).astype(
            np.int64
        )
        branch = (x_end[index] > x_start[index]).astype(np.int64)

        # A sample landing exactly on ``target_x`` makes two adjacent segments
        # register the same crossing, so keep the first hit per turn and branch.
        _, first_hit = np.unique(turn_ids * 2 + branch, return_index=True)
        first_hit = np.sort(first_hit)
        centers = centers[first_hit]
        turn_ids = turn_ids[first_hit]

        # Keep only the turns that crossed on both branches.
        unique_turns, counts = np.unique(turn_ids, return_counts=True)
        complete = np.isin(turn_ids, unique_turns[counts == 2])
        centers = centers[complete]
        turn_ids = turn_ids[complete]
        if len(centers) == 0:
            return np.empty(0, dtype=float)

        # Both notches of a turn are punched from the same sheet, so drop a turn
        # outright unless the complete tab fits at both of its centers.
        finite_unwrapped = x_unwrapped[np.isfinite(x_unwrapped)]
        if len(finite_unwrapped) == 0:
            return np.empty(0, dtype=float)
        half_width = tab_width / 2
        fits = (centers - half_width >= float(np.min(finite_unwrapped))) & (
            centers + half_width <= float(np.max(finite_unwrapped))
        )
        incomplete_turns = np.unique(turn_ids[~fits])
        centers = centers[~np.isin(turn_ids, incomplete_turns)]

        return np.sort(centers)

    @staticmethod
    def calculate_variable_thickness_spiral(
        laminate: Laminate,
        start_radius: float,
        dtheta: Optional[float] = None,
        **kwargs,
    ) -> np.ndarray:
        """Wind ``laminate`` turn on turn around a round mandrel of ``start_radius`` (m).

        A thin wrapper over :func:`Winding.wind` on a round template (see that
        module for the model): each turn sits on the one beneath it, the first
        on the mandrel, with exact layer breakpoints.

        Parameters
        ----------
        dtheta : float, optional
            Angular sample spacing in radians (also accepted in ``kwargs``);
            at least 100 samples per turn.

        Returns
        -------
        np.ndarray
            The strip's bottom-face path, columns [theta, x_unwrapped, r, x, z,
            turns], clockwise from θ = π/2, ending exactly at the strip's length.
        """
        from steer_opencell_design.Constructions.ElectrodeAssemblies.Winding import (
            ROUND_POINTS_PER_TURN,
            round_template,
            wind,
        )

        if dtheta is None:
            dtheta = kwargs.get("dtheta")
        points = ROUND_POINTS_PER_TURN
        if dtheta is not None and dtheta > 0:
            points = max(ROUND_POINTS_PER_TURN, int(round(TWO_PI / float(dtheta))))
        template = round_template(float(start_radius), points)
        return wind(laminate.get_stack_profile(), template).base_path()


    @staticmethod
    def calculate_simple_spiral(
        n_turns: Optional[float] = None,
        start_radius: Optional[float] = None,
        thickness: Optional[float] = None,
        points_per_turn: int = 100,
        target_length: Optional[float] = None,
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
            raise ValueError(
                "Cannot specify both n_turns and target_length. Please provide only one."
            )

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
        theta_start = np.pi / 2
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
        spiral = np.column_stack(
            [
                theta_arr,  # Column 0: theta (radians)
                ds_arr,  # Column 1: x_unwrapped (arc length in meters)
                r_arr,  # Column 2: radius (meters)
                x_coords,  # Column 3: x coordinate (meters)
                z_coords,  # Column 4: z coordinate (meters)
                turns_arr,  # Column 5: turns completed
            ]
        )

        # If target_length was specified, truncate spiral to exact length
        if target_length is not None:
            # Find points that exceed target length
            length_mask = ds_arr <= target_length

            if np.any(length_mask):
                # Get last point within target length
                last_valid_idx = np.where(length_mask)[0][-1]

                # Check if we need interpolation for exact length
                if (
                    last_valid_idx < len(ds_arr) - 1
                    and ds_arr[last_valid_idx] < target_length
                ):
                    # Interpolate between last valid point and next point for exact target length
                    next_idx = last_valid_idx + 1

                    # Linear interpolation factor
                    remaining_length = target_length - ds_arr[last_valid_idx]
                    segment_length = ds_arr[next_idx] - ds_arr[last_valid_idx]

                    if segment_length > 1e-12:  # Avoid division by zero
                        interp_factor = remaining_length / segment_length

                        # Interpolate all spiral parameters
                        interp_row = spiral[last_valid_idx] + interp_factor * (
                            spiral[next_idx] - spiral[last_valid_idx]
                        )
                        interp_row[1] = target_length  # Set exact target length

                        # Create truncated spiral with interpolated endpoint
                        spiral = np.vstack([spiral[: last_valid_idx + 1], interp_row])
                    else:
                        # Edge case: just truncate at last valid point
                        spiral = spiral[: last_valid_idx + 1]
                else:
                    # No interpolation needed, just truncate
                    spiral = spiral[: last_valid_idx + 1]
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
        **kwargs,
    ) -> np.ndarray:
        """Wind ``laminate`` turn on turn around a racetrack mandrel.

        A thin wrapper over :func:`Winding.wind` on a racetrack template of
        semicircle radius ``mandrel_radius`` and straight length
        ``straight_length`` (m), clockwise from the top of the right semicircle.

        Parameters
        ----------
        ds_target : float, optional
            Sample spacing along the straights in m (also accepted in
            ``kwargs``); ``curve_points`` in ``kwargs`` sets samples per
            semicircle.

        Returns
        -------
        np.ndarray
            The strip's bottom-face path, columns [theta, x_unwrapped, r, x, z,
            turns] (theta is the winding phase, 2π per turn), ending exactly at
            the strip's length.
        """
        from steer_opencell_design.Constructions.ElectrodeAssemblies.Winding import (
            RACETRACK_CURVE_POINTS,
            RACETRACK_STRAIGHT_SPACING,
            racetrack_template,
            wind,
        )

        if ds_target is None:
            ds_target = kwargs.get("ds_target")
        template = racetrack_template(
            float(mandrel_radius),
            float(straight_length),
            curve_points=kwargs.get("curve_points") or RACETRACK_CURVE_POINTS,
            straight_spacing=ds_target or RACETRACK_STRAIGHT_SPACING,
        )
        return wind(laminate.get_stack_profile(), template).base_path()

    @staticmethod
    def calculate_simple_racetrack(
        n_turns: Optional[float] = None,
        start_radius: Optional[float] = None,
        straight_length: Optional[float] = None,
        thickness: Optional[float] = None,
        points_per_turn: int = 300,
        target_length: Optional[float] = None,
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
            raise ValueError(
                "Cannot specify both n_turns and target_length. Please provide only one."
            )

        if n_turns is None and target_length is None:
            raise ValueError("Must specify either n_turns or target_length.")

        if start_radius is None or straight_length is None or thickness is None:
            raise ValueError(
                "start_radius, straight_length, and thickness are required parameters."
            )
        assert (
            start_radius is not None
            and straight_length is not None
            and thickness is not None
        )

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
        x_coords, z_coords = _racetrack_positions_batch(
            theta_arr, current_radii, straight_length
        )

        # Calculate number of turns completed
        turns_arr = turns_completed

        # Assemble racetrack array with same format as variable thickness racetrack
        racetrack = np.column_stack(
            [
                theta_arr,  # Column 0: theta (parametric angle)
                x_unwrapped_arr,  # Column 1: x_unwrapped (arc length in meters)
                current_radii,  # Column 2: current radius (meters)
                x_coords,  # Column 3: x coordinate (meters)
                z_coords,  # Column 4: z coordinate (meters)
                turns_arr,  # Column 5: turns completed
            ]
        )

        # If target_length was specified, truncate racetrack to exact length
        if target_length is not None:
            # Find points that exceed target length
            length_mask = x_unwrapped_arr <= target_length

            if np.any(length_mask):
                # Get last point within target length
                last_valid_idx = np.where(length_mask)[0][-1]

                # Check if we need interpolation for exact length
                if (
                    last_valid_idx < len(x_unwrapped_arr) - 1
                    and x_unwrapped_arr[last_valid_idx] < target_length
                ):
                    # Interpolate between last valid point and next point for exact target length
                    next_idx = last_valid_idx + 1

                    # Linear interpolation factor
                    remaining_length = target_length - x_unwrapped_arr[last_valid_idx]
                    segment_length = (
                        x_unwrapped_arr[next_idx] - x_unwrapped_arr[last_valid_idx]
                    )

                    if segment_length > 1e-12:  # Avoid division by zero
                        interp_factor = remaining_length / segment_length

                        # Interpolate all racetrack parameters
                        interp_row = racetrack[last_valid_idx] + interp_factor * (
                            racetrack[next_idx] - racetrack[last_valid_idx]
                        )
                        interp_row[1] = target_length  # Set exact target length

                        # Create truncated racetrack with interpolated endpoint
                        racetrack = np.vstack(
                            [racetrack[: last_valid_idx + 1], interp_row]
                        )
                    else:
                        # Edge case: just truncate at last valid point
                        racetrack = racetrack[: last_valid_idx + 1]
                else:
                    # No interpolation needed, just truncate
                    racetrack = racetrack[: last_valid_idx + 1]
            else:
                # Edge case: target length is very small, return just the first point
                racetrack = racetrack[:1]

        return racetrack

    @staticmethod
    def racetrack_position(
        theta: float, radius: float, straight_length: float
    ) -> tuple:
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
            x = straight_length / 2 + radius * np.cos(
                np.pi / 2 - phi
            )  # Start at top (π/2), go clockwise
            z = radius * np.sin(np.pi / 2 - phi)

        elif arc_length <= semi_arc_length + straight_length:
            # Bottom straight section (right to left)
            progress = (arc_length - semi_arc_length) / straight_length
            x = straight_length / 2 - progress * straight_length
            z = -radius

        elif arc_length <= 2 * semi_arc_length + straight_length:
            # Left semicircle (bottom to top, clockwise)
            phi = (arc_length - semi_arc_length - straight_length) / radius
            # For left semicircle, start at bottom (-π/2) and go clockwise (decreasing angle)
            angle = -np.pi / 2 - phi  # Start at -π/2, go clockwise (more negative)
            x = -straight_length / 2 + radius * np.cos(
                angle
            )  # Center at -straight_length/2
            z = radius * np.sin(angle)

        else:
            # Top straight section (left to right)
            progress = (
                arc_length - 2 * semi_arc_length - straight_length
            ) / straight_length
            x = -straight_length / 2 + progress * straight_length
            z = radius

        return x, z

    @staticmethod
    def racetrack_curvature(
        theta: float, radius: float, straight_length: float
    ) -> float:
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
        if arc_length <= semi_arc_length or (
            semi_arc_length + straight_length
            <= arc_length
            <= 2 * semi_arc_length + straight_length
        ):
            # On semicircular sections
            return 1.0 / radius if radius > 0 else 0.0
        else:
            # On straight sections
            return 0.0


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
        theta_deg = np.where(
            np.isnan(theta_raw), np.nan, np.abs(theta_raw * (180.0 / PI) - 90)
        )

        x_unwrapped_raw = np_array[:, X_UNWRAPPED_COL]
        # Calculate min only from non-NaN values for proper offset
        valid_x_unwrapped = x_unwrapped_raw[~np.isnan(x_unwrapped_raw)]
        x_min = np.min(valid_x_unwrapped) if len(valid_x_unwrapped) > 0 else 0.0
        length_mm = np.where(
            np.isnan(x_unwrapped_raw), np.nan, (x_unwrapped_raw - x_min) * M_TO_MM
        )

        r_mm = np.where(
            np.isnan(np_array[:, RADIUS_COL]), np.nan, np_array[:, RADIUS_COL] * M_TO_MM
        )
        x_mm = np.where(
            np.isnan(np_array[:, X_COORD_COL]),
            np.nan,
            np_array[:, X_COORD_COL] * M_TO_MM,
        )
        z_mm = np.where(
            np.isnan(np_array[:, Z_COORD_COL]),
            np.nan,
            np_array[:, Z_COORD_COL] * M_TO_MM,
        )
        turns = np.where(
            np.isnan(np_array[:, TURNS_COL]), np.nan, np_array[:, TURNS_COL]
        )

        # Create DataFrame with NaN values preserved (pandas will convert NaN to None where appropriate)
        df = pd.DataFrame(
            {
                "Theta (degrees)": theta_deg,
                "Unwrapped Length (mm)": length_mm,
                "Radius (mm)": r_mm,
                "X (mm)": x_mm,
                "Z (mm)": z_mm,
                "Turns": turns,
            }
        )

        # Convert NaN to None for better representation in pandas
        df = df.where(pd.notna(df), None)

        return df


    @staticmethod
    def min_thickness_orientation(
        valid_points: np.ndarray,
    ) -> tuple[float, float, float]:
        """Exact minimal-thickness orientation via convex hull + rotating calipers.

        The thickness after rotating by θ equals the extent of the point set
        along the direction ``v(θ) = (sin θ, cos θ)``, and the minimum width
        of a convex polygon is always attained perpendicular to one of its
        edges. So the global optimum is found by scanning hull-edge normals —
        no iterative search, no local minima.

        Dense clouds are first reduced to their outer rim (max-radius points
        per angular bin around the centroid), which preserves the hull
        vertices of the star-shaped jelly-roll cross-sections to sub-µm
        accuracy while capping the qhull input size.

        Parameters
        ----------
        valid_points : np.ndarray
            (N, 2) array of finite x-z points.

        Returns
        -------
        tuple[float, float, float]
            ``(angle, thickness, width)`` where ``angle`` is the rotation (in
            radians, mod π) that minimizes the z-extent, ``thickness`` is that
            minimal z-extent, and ``width`` is the x-extent at that rotation.

        Raises
        ------
        Exception
            Degenerate inputs (e.g. all-collinear points) propagate qhull
            errors; callers fall back to the scalar search.
        """
        from scipy.spatial import ConvexHull

        pts = valid_points
        if len(pts) > 4096:
            center = pts.mean(axis=0)
            d = pts - center
            r2 = d[:, 0] ** 2 + d[:, 1] ** 2
            angles = np.arctan2(d[:, 1], d[:, 0])
            n_bins = 2048
            bins = ((angles + np.pi) * (n_bins / (2.0 * np.pi))).astype(np.intp)
            np.clip(bins, 0, n_bins - 1, out=bins)
            best_r2 = np.full(n_bins, -1.0)
            np.maximum.at(best_r2, bins, r2)
            keep = r2 >= best_r2[bins] - 1e-30
            rim = pts[keep]
            if len(rim) >= 3:
                pts = rim

        hull = ConvexHull(pts)
        hp = pts[hull.vertices]

        edges = np.diff(np.vstack([hp, hp[:1]]), axis=0)
        lengths = np.hypot(edges[:, 0], edges[:, 1])
        good = lengths > 1e-15
        if not np.any(good):
            return 0.0, 0.0, 0.0
        normals = edges[good][:, ::-1] * np.array([-1.0, 1.0]) / lengths[good, None]

        # Projections of every hull vertex onto every candidate normal.
        proj = hp @ normals.T
        widths = proj.max(axis=0) - proj.min(axis=0)
        i_best = int(np.argmin(widths))
        n_best = normals[i_best]
        thickness = float(widths[i_best])

        # Extent along the perpendicular direction = width after rotation.
        perp = np.array([n_best[1], -n_best[0]])
        proj_perp = hp @ perp
        width = float(proj_perp.max() - proj_perp.min())

        # v(θ) = (sin θ, cos θ) must align with the best normal (mod π).
        angle = float(np.arctan2(n_best[0], n_best[1])) % np.pi
        return angle, thickness, width


    @staticmethod
    def translate_spirals_xz(
        spiral_data,
        x_shift: float,
        z_shift: float,
        x_col: int = X_COORD_COL,
        z_col: int = Z_COORD_COL,
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
            raise TypeError(
                f"spiral_data must be np.ndarray or dict, got {type(spiral_data)}"
            )

        return spiral_data
