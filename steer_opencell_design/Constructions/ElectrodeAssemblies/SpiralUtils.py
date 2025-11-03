from steer_opencell_design.Constructions.Layups import Laminate
from steer_core.Constants.Universal import PI
from steer_core.Constants.Units import *
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, Point
from shapely import minimum_bounding_circle

# Constants for array column indices
THETA_COL = 0
X_UNWRAPPED_COL = 1
RADIUS_COL = 2
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5

# Constants for calculations
TWO_PI = 2.0 * PI
DEFAULT_DTHETA = 0.4
DEFAULT_DS_TARGET = 0.5e-3
DEFAULT_PRESSED_HEIGHT = 0.0008
TARGET_ERROR = 5e-5
MAX_ITERATIONS = 500000
MAX_POINTS = 120000


class SpiralCalculator:

    @staticmethod
    def calculate_variable_thickness_spiral(laminate: Laminate, start_radius: float, dtheta: float = DEFAULT_DTHETA):
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
        dtheta : float
            Nominal (maximum) angular step magnitude (radians). Smaller steps are chosen adaptively as needed.

        Returns
        -------
        np.ndarray
            Columns: [theta, x_unwrapped, r, x, z, turns]
            
        Raises
        ------
        ValueError
            If laminate total length is invalid or spiral calculation fails
        """
        total_length = laminate._total_length
        r0 = start_radius
            
        # Build interpolation grid for thickness
        # Heuristic: finer where dtheta small or mandrel small
        base_dl = max(dtheta * r0 / 8.0, 0.00025)
        n_grid = min(6000, max(400, int(total_length / base_dl) + 2))
        x_grid = np.linspace(0.0, total_length, n_grid)
        t_grid = np.array([laminate.get_thickness_at_x(x) for x in x_grid], dtype=float)
        t_min, t_max = float(t_grid.min()), float(t_grid.max())
        near_uniform = (t_max - t_min) < 1e-6 * max(1e-9, t_max)

        def thickness_at(x):
            if x <= 0: return t_grid[0]
            if x >= total_length: return t_grid[-1]
            return float(np.interp(x, x_grid, t_grid))

        # Analytic fast path (uniform thickness)
        if near_uniform:
            t = (t_min + t_max) / 2.0
            k = t / TWO_PI  # dr/dθ
            # Solve s(θ) ≈ ((r0 + kθ)^2 - r0^2)/(2k) for θ_end where s = total_length
            if k > 0:
                theta_span = (np.sqrt(r0*r0 + 2*k*total_length) - r0) / k
            else:
                theta_span = 0.0
            # Choose number of steps so arc increment ~ dtheta*r scale
            n_steps = max(3, int(theta_span / dtheta) + 2)
            theta_arr = np.linspace(np.pi/2, np.pi/2 - theta_span, n_steps)
            dtheta_arr = -(theta_arr - theta_arr[0])  # not used directly, just for clarity
            # r(θ) = r0 + k(θ - θ_start) with θ_start=π/2
            delta = theta_arr - theta_arr[0]
            r_arr = r0 + k * delta
            # s(θ) relative to start: ((r)^2 - r0^2)/(2k)
            if k > 0:
                x_unwrapped_arr = ((r_arr**2 - r0**2) / (2*k))
            else:
                x_unwrapped_arr = np.zeros_like(r_arr)
            # Adjust sign (θ decreases for clockwise). Ensure monotonic x.
            # Trim / interpolate final
            if x_unwrapped_arr[-1] > total_length and len(x_unwrapped_arr) > 1:
                idx = np.searchsorted(x_unwrapped_arr, total_length)
                idx = min(max(idx, 1), len(x_unwrapped_arr)-1)
                x0, x1 = x_unwrapped_arr[idx-1], x_unwrapped_arr[idx]
                f = (total_length - x0)/(x1 - x0)
                theta_trim = theta_arr[idx-1] + f*(theta_arr[idx]-theta_arr[idx-1])
                r_trim = r_arr[idx-1] + f*(r_arr[idx]-r_arr[idx-1])
                theta_arr = np.concatenate([theta_arr[:idx], [theta_trim]])
                r_arr = np.concatenate([r_arr[:idx], [r_trim]])
                x_unwrapped_arr = np.concatenate([x_unwrapped_arr[:idx], [total_length]])
            
            # Calculate number of turns: cumulative rotations from start (theta decreases from π/2)
            theta_start = np.pi/2
            theta_traveled = theta_start - theta_arr  # Total angle traveled (positive)
            turns_arr = theta_traveled / TWO_PI  # Number of complete turns
            
            x_coords = r_arr * np.cos(theta_arr)
            z_coords = r_arr * np.sin(theta_arr)
            spiral = np.column_stack([theta_arr, x_unwrapped_arr, r_arr, x_coords, z_coords, turns_arr])
            return spiral

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
                'x_max': np.max(center_line[:, 0])
            }
        
        # Process each component
        for component_name in component_names:
                
            cl_data = center_line_data[component_name]
            
            # Vectorized spiral clipping using boolean mask
            x_unwrapped = base_spiral[:, 1]  # Extract x_unwrapped column
            mask = (x_unwrapped >= cl_data['x_min']) & (x_unwrapped <= cl_data['x_max'])
            
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
            
            component_spirals[component_name] = component_spiral

        return component_spirals

    @staticmethod
    def build_extruded_component_spirals(component_spirals: dict, layup: Laminate) -> dict:
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
        layup : Laminate
            The layup structure containing thickness information
            
        Returns
        -------
        dict
            Extruded component spirals for 3D visualization
            
        Raises
        ------
        ValueError
            If extrusion calculation fails or invalid thickness values
        """
        extruded_spirals = {}

        component_thicknesses = {
            'top_separator': layup.top_separator._thickness,
            'anode_a_side_coating': layup.anode._coating_thickness,
            'anode_current_collector': layup.anode.current_collector._thickness,
            'anode_b_side_coating': layup.anode._coating_thickness,
            'bottom_separator': layup.bottom_separator._thickness,
            'cathode_a_side_coating': layup.cathode._coating_thickness,
            'cathode_current_collector': layup.cathode.current_collector._thickness,
            'cathode_b_side_coating': layup.cathode._coating_thickness,
        }

        components = [n for n in layup._flattened_center_lines.keys()]
        
        # Process each component that has a center line spiral
        for component_name in components:

            thickness = component_thicknesses.get(component_name, 0.0)

            center_spiral = component_spirals[component_name]
            half_thickness = thickness / 2.0
            
            # Create outer spiral (center + thickness/2)
            outer_spiral = center_spiral.copy()
            outer_spiral[:, 2] += half_thickness  # Increase radius
            
            # Update outer spiral coordinates
            outer_spiral[:, 3] = outer_spiral[:, 2] * np.cos(outer_spiral[:, 0])  # x coordinates
            outer_spiral[:, 4] = outer_spiral[:, 2] * np.sin(outer_spiral[:, 0])  # z coordinates
            
            # Create inner spiral (center - thickness/2)
            inner_spiral = center_spiral.copy()
            inner_spiral[:, 2] -= half_thickness  # Decrease radius
            
            # Update inner spiral coordinates
            inner_spiral[:, 3] = inner_spiral[:, 2] * np.cos(inner_spiral[:, 0])  # x coordinates
            inner_spiral[:, 4] = inner_spiral[:, 2] * np.sin(inner_spiral[:, 0])  # z coordinates
            
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
            
            extruded_spirals[component_name] = filled_spiral

        return extruded_spirals

    @staticmethod
    def get_radius_of_spiral(coords: np.ndarray) -> float:
        """Calculate the radius of a spiral given its coordinates.

        Parameters
        ----------
        coords : np.ndarray
            Array of shape (N, 2) with columns [x, z]

        Returns
        -------
        float
            Radius of the spiral in meters

        Raises
        ------
        ValueError
            If input coordinates are invalid
        """
        polygon = Polygon(coords)
        circle = minimum_bounding_circle(polygon)
        center = circle.centroid
        first_point = list(circle.exterior.coords)[0]
        radius = Point(center).distance(Point(first_point))
        return radius

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
        theta_deg = np.abs(np_array[:, THETA_COL] * (180.0 / PI) - 90)
        length_mm = (np_array[:, X_UNWRAPPED_COL] - np.min(np_array[:, X_UNWRAPPED_COL])) * M_TO_MM
        r_mm = np_array[:, RADIUS_COL] * M_TO_MM
        x_mm = np_array[:, X_COORD_COL] * M_TO_MM
        z_mm = np_array[:, Z_COORD_COL] * M_TO_MM
        turns = np_array[:, TURNS_COL]  # Number of turns (dimensionless)
        
        # Create DataFrame directly with final column names and converted values
        return pd.DataFrame({
            "Theta (degrees)": theta_deg,
            "Unwrapped Length (mm)": length_mm,
            "Radius (mm)": r_mm,
            "X (mm)": x_mm,
            "Z (mm)": z_mm,
            "Turns": turns,
        })
    
