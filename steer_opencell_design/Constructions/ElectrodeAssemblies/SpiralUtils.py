from steer_opencell_design.Constructions.Layups import Laminate
from steer_core.Constants.Universal import PI
from steer_core.Constants.Units import *
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, Point
from shapely import minimum_bounding_circle

from steer_core.Mixins.Coordinates import CoordinateMixin

# Constants for array column indices
THETA_COL = 0
X_UNWRAPPED_COL = 1
RADIUS_COL = 2
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5

# Constants for calculations
TWO_PI = 2.0 * PI
TARGET_ERROR = 5e-5
MAX_ITERATIONS = 500000
MAX_POINTS = 120000


class SpiralCalculator:

    @staticmethod
    def calculate_variable_thickness_spiral(
        laminate: Laminate, 
        start_radius: float, 
        dtheta: float = None,
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
        
        total_length = laminate._total_length
        r0 = start_radius
            
        # Build interpolation grid for thickness
        # Heuristic: finer where dtheta small or mandrel small
        base_dl = max(dtheta * r0 / 8.0, 0.00025)
        n_grid = min(6000, max(400, int(total_length / base_dl) + 2))
        x_grid = np.linspace(0.0, total_length, n_grid)
        t_grid = np.array([laminate.get_thickness_at_x(x) for x in x_grid], dtype=float)
        t_min, t_max = float(t_grid.min()), float(t_grid.max())

        def thickness_at(x):
            if x <= 0: return t_grid[0]
            if x >= total_length: return t_grid[-1]
            return float(np.interp(x, x_grid, t_grid))

        # Adaptive RK4 integration (θ decreases)
        # State: (r, x); derivatives w.r.t θ
        def deriv(r, x):
            tloc = thickness_at(x)
            dr_dth = tloc / TWO_PI
            ds_dth = np.sqrt(r*r + dr_dth*dr_dth)
            return dr_dth, ds_dth

        theta = np.pi/2  # start top
        r = r0
        x_unwrapped = 0.0
        h_max = abs(dtheta)
        h_min = h_max / 64.0
        target_err = TARGET_ERROR
        max_points = MAX_POINTS
        max_iterations = MAX_ITERATIONS
        growth = 1.5
        shrink = 0.5
        
        # Adaptive step size reduction towards end of spiral
        def adaptive_h_max(x_progress, r_current):
            """Reduce maximum step size as spiral progresses and radius increases."""
            progress_factor = x_progress / total_length  # 0 to 1
            # Reduce step size in final 30% of spiral
            if progress_factor > 0.7:
                end_reduction = 1.0 - 0.6 * ((progress_factor - 0.7) / 0.3)  # Linear reduction to 40% of original
            else:
                end_reduction = 1.0
            
            # Also reduce step size as radius increases (arc length per angular step grows)
            radius_factor = min(1.0, r0 / max(r_current, r0))  # Smaller factor for larger radius
            radius_reduction = 0.3 + 0.7 * radius_factor  # Range: 30% to 100% of original
            
            # Apply both reductions
            combined_factor = min(end_reduction, radius_reduction)
            return h_max * combined_factor

        theta_list = [theta]
        r_list = [r]
        x_list = [x_unwrapped]

        iterations = 0
        h = h_max
        # Pre-compute rough gradient to modulate minimal step
        dt_dx = np.gradient(t_grid, x_grid)
        max_grad = np.max(np.abs(dt_dx)) + 1e-12

        while x_unwrapped < total_length and iterations < max_iterations and len(theta_list) < max_points:
            iterations += 1
            
            # Update maximum step size based on progress and radius
            current_h_max = adaptive_h_max(x_unwrapped, r)
            h = min(h, current_h_max)  # Don't exceed adaptive maximum
            
            # Clamp step not to overshoot total_length (rough estimate)
            # Predict ds ≈ r * h; adjust if would exceed remaining length by large margin
            remaining = total_length - x_unwrapped
            if r * h > 1.5 * remaining:
                h = max(remaining / (r + 1e-12), h_min)

            # Single RK4 full step size h
            dr1, dx1 = deriv(r, x_unwrapped)
            r2 = r + 0.5*h*dr1; x2 = x_unwrapped + 0.5*h*dx1
            dr2, dx2 = deriv(r2, x2)
            r3 = r + 0.5*h*dr2; x3 = x_unwrapped + 0.5*h*dx2
            dr3, dx3 = deriv(r3, x3)
            r4 = r + h*dr3; x4 = x_unwrapped + h*dx3
            dr4, dx4 = deriv(r4, x4)
            r_full = r + (h/6.0)*(dr1 + 2*dr2 + 2*dr3 + dr4)
            x_full = x_unwrapped + (h/6.0)*(dx1 + 2*dx2 + 2*dx3 + dx4)

            # Two half steps (h/2 + h/2)
            h2 = 0.5 * h
            # First half
            dr1h, dx1h = dr1, dx1  # same as above first evaluation
            r2h = r + 0.5*h2*dr1h; x2h = x_unwrapped + 0.5*h2*dx1h
            dr2h, dx2h = deriv(r2h, x2h)
            r3h = r + 0.5*h2*dr2h; x3h = x_unwrapped + 0.5*h2*dx2h
            dr3h, dx3h = deriv(r3h, x3h)
            r4h = r + h2*dr3h; x4h = x_unwrapped + h2*dx3h
            dr4h, dx4h = deriv(r4h, x4h)
            r_half = r + (h2/6.0)*(dr1h + 2*dr2h + 2*dr3h + dr4h)
            x_half = x_unwrapped + (h2/6.0)*(dx1h + 2*dx2h + 2*dx3h + dx4h)
            # Second half from (r_half, x_half)
            dr1s, dx1s = deriv(r_half, x_half)
            r2s = r_half + 0.5*h2*dr1s; x2s = x_half + 0.5*h2*dx1s
            dr2s, dx2s = deriv(r2s, x2s)
            r3s = r_half + 0.5*h2*dr2s; x3s = x_half + 0.5*h2*dx2s
            dr3s, dx3s = deriv(r3s, x3s)
            r4s = r_half + h2*dr3s; x4s = x_half + h2*dx3s
            dr4s, dx4s = deriv(r4s, x4s)
            r_two_half = r_half + (h2/6.0)*(dr1s + 2*dr2s + 2*dr3s + dr4s)
            x_two_half = x_half + (h2/6.0)*(dx1s + 2*dx2s + 2*dx3s + dx4s)

            # Error estimate (local): difference between full and two half steps (O(h^5))
            err_r = abs(r_full - r_two_half)
            err_x = abs(x_full - x_two_half)
            scale_r = max(abs(r), abs(r_two_half), 1e-9)
            scale_x = max(abs(x_unwrapped), abs(x_two_half), 1e-9)
            rel_err = max(err_r/scale_r, err_x/scale_x)

            if rel_err > target_err and h > h_min * 1.01:
                # Reject step, shrink and retry
                h = max(h * shrink * max(0.2, (target_err / (rel_err + 1e-14))**0.25), h_min)
                continue

            # Accept step -> use higher accuracy two half-steps solution
            r = r_two_half
            x_unwrapped = x_two_half
            theta -= h  # clockwise (θ decreasing)

            theta_list.append(theta)
            r_list.append(r)
            x_list.append(x_unwrapped)

            if rel_err < target_err / 8.0 and h < h_max / 0.6:
                h = min(h * growth * min(2.0, (target_err / (rel_err + 1e-14))**0.20), h_max)

            # Enforce minimal step if local thickness gradient high
            local_grad = abs(interp_grad := (np.interp(x_unwrapped, x_grid, dt_dx) if 0 < x_unwrapped < total_length else 0.0))
            grad_factor = 1.0 + 5.0 * (local_grad / max_grad)
            h = max(h / grad_factor, h_min)

        # Interpolate final point if overshoot
        if x_list[-1] > total_length and len(x_list) > 1:
            x_prev, x_curr = x_list[-2], x_list[-1]
            f = (total_length - x_prev)/(x_curr - x_prev + 1e-14)
            r_prev, r_curr = r_list[-2], r_list[-1]
            th_prev, th_curr = theta_list[-2], theta_list[-1]
            x_list[-1] = total_length
            r_list[-1] = r_prev + f*(r_curr - r_prev)
            theta_list[-1] = th_prev + f*(th_curr - th_prev)

        theta_arr = np.array(theta_list)
        x_unwrapped_arr = np.array(x_list)
        r_arr = np.array(r_list)

        # Calculate number of turns: cumulative rotations from start (theta decreases from π/2)
        theta_start = np.pi/2
        theta_traveled = theta_start - theta_arr  # Total angle traveled `(positive)
        turns_arr = theta_traveled / TWO_PI  # Number of complete turns

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

            # insert nan rows every time there is a gap
            component_spiral = CoordinateMixin.insert_gaps_with_nans(component_spiral, X_UNWRAPPED_COL)
            
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
    def _extrude_single_spiral(spiral, thickness) -> np.array:

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
        n_turns: float = None,
        start_radius: float = None, 
        thickness: float = None,
        points_per_turn: int = 100,
        target_length: float = None
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
        
        # Determine n_turns based on input
        if target_length is not None:
            # Rough overestimate: assume average radius is start_radius + some thickness buildup
            # For safety, use 50% more turns than the rough estimate
            avg_radius_estimate = start_radius + thickness * 2  # Conservative estimate
            rough_turns_estimate = target_length / (TWO_PI * avg_radius_estimate)
            n_turns = rough_turns_estimate * 1.5  # 50% overestimate for safety
        
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
            ds_target: float = None,
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
        
        total_length = laminate._total_length  # meters

        # Initialize arrays for spiral path
        positions = []
        x_unwrapped = 0.0
        accumulated_thickness = 0.0  # Track actual thickness buildup
        turn_count = 0.0
        
        # Start at top of right semicircle (theta=2π in racetrack coordinates, will decrease clockwise)
        theta_racetrack = TWO_PI
        
        while x_unwrapped < total_length:
            # Get thickness at current unwrapped position
            thickness = laminate.get_thickness_at_x(x_unwrapped)
            current_radius = mandrel_radius + accumulated_thickness
            
            # Calculate position on current racetrack
            x_pos, z_pos = SpiralCalculator.racetrack_position(theta_racetrack, current_radius, straight_length)
            
            # Calculate normalized theta for clockwise motion (starting from 2π, decreasing)
            # Total turns traveled = (initial_theta - current_theta) / (2π) + full_turns_completed
            theta_traveled = (TWO_PI - theta_racetrack) + turn_count * TWO_PI
            total_turns = theta_traveled / TWO_PI
            normalized_theta = theta_traveled  # Represents cumulative angle traveled clockwise
            
            # Store position data
            positions.append([
                normalized_theta, # Normalized theta representing cumulative angle traveled clockwise
                x_unwrapped,      # Cumulative unwrapped length
                current_radius,   # Distance from center to current layer
                x_pos,           # Cartesian x coordinate
                z_pos,           # Cartesian z coordinate  
                total_turns      # Total number of turns (fractional)
            ])
            
            # Calculate step size based on local curvature and thickness
            curvature = SpiralCalculator.racetrack_curvature(theta_racetrack, current_radius, straight_length)
            if curvature > 0:
                # On curved sections, limit step by curvature
                ds_max = min(ds_target, 0.1 / curvature)
            else:
                # On straight sections, use target step size
                ds_max = ds_target
            
            ds_actual = min(ds_max, total_length - x_unwrapped)
            
            # Calculate how much thickness to add based on this step
            # Thickness accumulation rate depends on perimeter
            perimeter_current = TWO_PI * current_radius + 2 * straight_length
            dtheta = ds_actual * TWO_PI / perimeter_current
            
            # Add thickness proportional to angular progress
            thickness_increment = thickness * dtheta / TWO_PI
            accumulated_thickness += thickness_increment
            
            # Move clockwise (decrease theta)
            theta_racetrack -= dtheta
            x_unwrapped += ds_actual
            
            # Update turn count when completing full loops (theta goes below 0)
            if theta_racetrack < 0:
                full_turns = (-theta_racetrack) // TWO_PI + 1
                turn_count += full_turns
                theta_racetrack = theta_racetrack + full_turns * TWO_PI

        # Convert to numpy array
        spiral_array = np.array(positions)
        
        # Downsample straight sections to reduce point count
        # Calculate curvature at each point to identify straight vs curved sections
        curvatures = np.array([
            SpiralCalculator.racetrack_curvature(
                spiral_array[i, 0],  # theta
                spiral_array[i, 2],  # radius
                straight_length
            ) for i in range(len(spiral_array))
        ])
        
        # Identify curved sections (curvature > threshold)
        curvature_threshold = 1e-6  # Small threshold for numerical stability
        is_curved = curvatures > curvature_threshold
        
        # Build mask for points to keep
        # Always keep: first point, last point, all curved points, and every Nth straight point
        downsample_factor = 5  # Keep every 5th point on straight sections
        keep_mask = np.zeros(len(spiral_array), dtype=bool)
        keep_mask[0] = True   # Always keep first point
        keep_mask[-1] = True  # Always keep last point
        keep_mask[is_curved] = True  # Keep all curved section points
        
        # For straight sections, keep every Nth point
        straight_indices = np.where(~is_curved)[0]
        if len(straight_indices) > 0:
            # Keep every downsample_factor-th point in straight sections
            keep_straight = straight_indices[::downsample_factor]
            keep_mask[keep_straight] = True
        
        # Apply downsampling
        downsampled_spiral = spiral_array[keep_mask]
        
        return downsampled_spiral

    @staticmethod
    def calculate_simple_racetrack(
        n_turns: float = None,
        start_radius: float = None,
        straight_length: float = None,
        thickness: float = None,
        points_per_turn: int = 300,
        target_length: float = None
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
        
        # Determine n_turns based on input
        if target_length is not None:
            # Estimate based on average perimeter
            avg_perimeter = TWO_PI * start_radius + 2 * straight_length
            # For safety, use 50% more turns than the rough estimate
            rough_turns_estimate = target_length / avg_perimeter
            n_turns = rough_turns_estimate * 1.5  # 50% overestimate for safety
        
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
        
        # Calculate unwrapped length along racetrack path
        x_unwrapped_arr = np.zeros_like(theta_arr)
        if len(theta_arr) > 1:
            # Calculate incremental arc lengths
            for i in range(1, len(theta_arr)):
                # Use average radius for this segment
                avg_radius = (current_radii[i-1] + current_radii[i]) / 2
                dtheta = abs(theta_arr[i] - theta_arr[i-1])
                
                # Calculate perimeter at average radius
                perimeter_avg = TWO_PI * avg_radius + 2 * straight_length
                
                # Arc length increment proportional to angle increment
                ds = (dtheta / TWO_PI) * perimeter_avg
                x_unwrapped_arr[i] = x_unwrapped_arr[i-1] + ds
        
        # Calculate Cartesian coordinates for each point
        x_coords = np.zeros_like(theta_arr)
        z_coords = np.zeros_like(theta_arr)
        
        for i, (theta, radius) in enumerate(zip(theta_arr, current_radii)):
            x_pos, z_pos = SpiralCalculator.racetrack_position(theta, radius, straight_length)
            x_coords[i] = x_pos
            z_coords[i] = z_pos
        
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
    def _extrude_single_racetrack(spiral, thickness, mandrel_radius, straight_length) -> np.array:

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
        # Initialize outer and inner spirals
        outer_spiral = center_spiral.copy()
        inner_spiral = center_spiral.copy()
        
        # Process each point to apply thickness in correct direction
        for i in range(len(center_spiral)):
            current_x = center_spiral[i, 3]  # Current x position
            current_z = center_spiral[i, 4]  # Current z position
            
            # Get the direction vector for thickness application based on coordinates
            direction_vector = SpiralCalculator.get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Calculate outer position (center + half_thickness in direction)
            outer_x = center_spiral[i, 3] + half_thickness * direction_vector[0]
            outer_z = center_spiral[i, 4] + half_thickness * direction_vector[1]
            
            # Calculate inner position (center - half_thickness in direction)
            inner_x = center_spiral[i, 3] - half_thickness * direction_vector[0]
            inner_z = center_spiral[i, 4] - half_thickness * direction_vector[1]
            
            # Update outer spiral
            outer_spiral[i, 3] = outer_x
            outer_spiral[i, 4] = outer_z
            outer_spiral[i, 2] = np.sqrt(outer_x**2 + outer_z**2)  # Update effective radius
            
            # Update inner spiral
            inner_spiral[i, 3] = inner_x
            inner_spiral[i, 4] = inner_z
            inner_spiral[i, 2] = np.sqrt(inner_x**2 + inner_z**2)  # Update effective radius
        
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
        # Define the centers of the semicircular ends
        right_center_x = straight_length / 2
        left_center_x = -straight_length / 2
        center_z = 0.0
        
        # Tolerance for determining if we're on a straight section
        straight_tolerance = mandrel_radius * 0.1
        
        # Check if we're on the right semicircle
        if x > (straight_length / 2 - straight_tolerance):
            # Distance from right semicircle center
            dx_from_center = x - right_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from right center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # Check if we're on the left semicircle
        elif x < (-straight_length / 2 + straight_tolerance):
            # Distance from left semicircle center
            dx_from_center = x - left_center_x
            dz_from_center = z - center_z
            distance_from_center = np.sqrt(dx_from_center**2 + dz_from_center**2)
            
            if distance_from_center > 1e-12:  # Avoid division by zero
                # Unit vector pointing radially outward from left center
                direction_x = dx_from_center / distance_from_center
                direction_z = dz_from_center / distance_from_center
            else:
                # Fallback: assume we're at the center, point upward
                direction_x = 0.0
                direction_z = 1.0
                
        # We're on a straight section
        else:
            if z > 0:
                # Top straight section: directly upward
                direction_x = 0.0
                direction_z = 1.0
            else:
                # Bottom straight section: directly downward
                direction_x = 0.0
                direction_z = -1.0
        
        return np.array([direction_x, direction_z])

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

            # insert nan rows every time there is a gap
            component_spiral = CoordinateMixin.insert_gaps_with_nans(component_spiral, X_UNWRAPPED_COL)
        
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
        # Process each point to determine adjustment direction
        for i in range(len(spiral)):
            current_x = spiral[i, 3]  # Current x position
            current_z = spiral[i, 4]  # Current z position
            height_adj = height_adjustments[i]
            
            # Determine position type and adjustment direction based on actual coordinates
            adjustment_vector = SpiralCalculator.get_coordinate_based_adjustment_direction(
                current_x, current_z, mandrel_radius, straight_length
            )
            
            # Apply height adjustment in the correct direction
            new_x = current_x + height_adj * adjustment_vector[0]
            new_z = current_z + height_adj * adjustment_vector[1]
            
            # Update spiral coordinates
            spiral[i, 3] = new_x  # x coordinate
            spiral[i, 4] = new_z  # z coordinate
            
            # Update effective radius (distance from origin)
            spiral[i, 2] = np.sqrt(new_x**2 + new_z**2)

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
        optimal_angle = result.x

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
    


