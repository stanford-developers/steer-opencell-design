from copy import copy, deepcopy
from enum import Enum
from typing import Tuple

import numpy as np
import pandas as pd

from steer_core.Constants.Units import *
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import calculate_bulk_properties

from steer_opencell_design.Components.CurrentCollectors import _TapeCurrentCollector
from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups.Base import _Layup


class Laminate(_Layup):

    def __init__(
        self,
        cathode: Cathode,
        bottom_separator: Separator,
        anode: Anode,
        top_separator: Separator,
        name: str = "Layup",
    ):
        
        # Ensure anode is flipped in y-direction for correct orientation in laminate
        if not anode._flipped_y:
            anode._flip("y")

        # call the general layup init
        super().__init__(
            cathode=cathode,
            bottom_separator=bottom_separator,
            anode=anode,
            top_separator=top_separator,
            name=name,
        )

        # Store canonical separator for unified API
        self._canonical_separator = Separator(
            material=bottom_separator.material,
            thickness=bottom_separator.thickness,
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_all_properties(self):
                
        # Then validate that current collectors are of the correct type
        self.validate_type(
            self.anode.current_collector,
            _TapeCurrentCollector,
            "Anode Current Collector",
        )
        
        self.validate_type(
            self.cathode.current_collector,
            _TapeCurrentCollector,
            "Cathode Current Collector",
        )

        # Ensure bottom and top separators are not rotated in xy-plane
        if self._bottom_separator._rotated_xy:
            self._bottom_separator._rotate_90_xy()
        if self._top_separator._rotated_xy:
            self._top_separator._rotate_90_xy()

        # First call parent method to calculate all standard properties
        super()._calculate_all_properties()
        
        # set separator width/length ranges based on anode size
        self._top_separator._set_width_range(self._anode, extended_range=0.1)
        self._top_separator._set_length_range(self._anode, extended_range=1)
        self._bottom_separator._set_width_range(self._cathode, extended_range=0.1)
        self._bottom_separator._set_length_range(self._cathode, extended_range=1)

    def _calculate_coordinates(self):
        super()._calculate_coordinates()
        self._calculate_flattened_center_lines()

    def _calculate_flattened_center_lines(self):
        """Vectorized construction of flattened center lines for laminate layers.

        Builds an explicit bottom->top ordered stack and computes center line
        elevations using cumulative thickness. This replaces the prior per-layer
        search for a single "supporting" component and removes duplication.

        Notes
        -----
        - Currently no smoothing is applied (keeps geometric fidelity). A future
          enhancement could expose smoothing parameters.
        - Stores auxiliary arrays for rapid thickness interpolation.
        """

        # Ordered bottom->top layers (excluding baseline) using canonical names
        layer_specs = [
            ("cathode_b_side_coating", self._cathode.get_b_side_center_line(), self._cathode._coating_thickness),
            ("cathode_current_collector", self._cathode._current_collector.get_center_line(), self._cathode._current_collector._thickness),
            ("cathode_a_side_coating", self._cathode.get_a_side_center_line(), self._cathode._coating_thickness),
            ("bottom_separator", self._bottom_separator.get_center_line(), self._bottom_separator._thickness),
            ("anode_b_side_coating", self._anode.get_b_side_center_line(), self._anode._coating_thickness),
            ("anode_current_collector", self._anode._current_collector.get_center_line(), self._anode._current_collector._thickness),
            ("anode_a_side_coating", self._anode.get_a_side_center_line(), self._anode._coating_thickness),
            ("top_separator", self._top_separator.get_center_line(), self._top_separator._thickness),
        ]

        # Gather all x breakpoints
        x_breaks = []
        for _, coords, _ in layer_specs:
            if len(coords) == 0:
                continue
            x_breaks.append(coords[0, 0])
            x_breaks.append(coords[-1, 0])

        if not x_breaks:
            self._flattened_center_lines = {}
            self._layer_thickness_map = {}
            self._top_surface = None
            return {}

        x_min, x_max = min(x_breaks), max(x_breaks)
        # Resolution: sample ~1000 points across full span (consistent w/ prior n=1000)
        n_samples = 1000
        x = np.linspace(x_min, x_max, n_samples)

        # Baseline directly below lowest layer (use cathode b-side lower surface)
        baseline_z = (
            np.min(self._cathode.get_b_side_center_line()[:, 1])
            - self._cathode._coating_thickness / 2
        )
        baseline = np.column_stack((x, np.full_like(x, baseline_z)))

        # Coverage masks & thickness arrays
        layer_masks = []
        layer_thicknesses = []
        for _, coords, thickness in layer_specs:
            if len(coords) == 0:
                layer_masks.append(np.zeros_like(x, dtype=bool))
            else:
                x0, x1 = coords[0, 0], coords[-1, 0]
                layer_masks.append((x >= x0) & (x <= x1))
            layer_thicknesses.append(thickness)

        layer_masks = np.array(layer_masks)  # shape (L, N)
        layer_thicknesses = np.array(layer_thicknesses)  # shape (L,)

        # Cumulative thickness below each layer (exclude that layer's own thickness)
        cumulative_below = (
            np.cumsum(layer_thicknesses[:, None] * layer_masks, axis=0)
            - (layer_thicknesses[:, None] * layer_masks)
        )

        # Raw total thickness profile (top surface w/out baseline offset)
        raw_total_thickness = np.sum(layer_thicknesses[:, None] * layer_masks, axis=0)
        top_surface = baseline_z + raw_total_thickness

        # Build flattened center lines
        flattened = {"baseline": baseline}
        layer_thickness_map = {}
        for i, (name, _coords, thickness) in enumerate(layer_specs):
            mask = layer_masks[i]
            if not np.any(mask):
                flattened[name] = np.empty((0, 2))
                layer_thickness_map[name] = thickness
                continue
            center_z = baseline_z + cumulative_below[i, mask] + thickness / 2
            flattened[name] = np.column_stack((x[mask], center_z))
            layer_thickness_map[name] = thickness

        # Persist for downstream usage
        self._flattened_center_lines = flattened
        self._layer_thickness_map = layer_thickness_map
        self._top_surface = np.column_stack((x, top_surface))
        self._baseline_z = baseline_z

        return flattened

    def _calculate_bulk_properties(self):
        self._calculate_length()
        self._calculate_width()
        self._calculate_total_geometries()
        self._calculate_thickness()

    def _calculate_length(self) -> float:
        """
        Calculate the length of the laminate based on the anode and cathode lengths.

        Returns
        -------
        float
            The length of the laminate in meters.
        """
        anode_length = self._anode._current_collector._x_body_length
        cathode_length = self._cathode._current_collector._x_body_length

        # The laminate length is determined by the longer of the two electrodes
        laminate_length = max(anode_length, cathode_length)

        self._length = laminate_length

        return self._length

    def _calculate_width(self) -> float:
        """
        Calculate the width of the laminate based on the anode and cathode widths.

        Returns
        -------
        float
            The width of the laminate in meters.
        """
        anode_width = self._anode._current_collector._y_body_length
        cathode_width = self._cathode._current_collector._y_body_length

        # The laminate width is determined by the wider of the two electrodes
        laminate_width = max(anode_width, cathode_width)

        self._width = laminate_width

        return self._width
    
    def _calculate_total_geometries(self):
        """Calculate the total length of the layup by finding the maximum end-to-end distance.
        
        Returns
        -------
        tuple
            (total_length, x_start_position) both in meters
        """
        # Collect all coordinate arrays
        coordinate_arrays = [
            self._bottom_separator._coordinates,
            self._anode._current_collector._body_coordinates,
            self._anode._a_side_coating_coordinates,
            self._anode._b_side_coating_coordinates,
            self._cathode._current_collector._body_coordinates,
            self._cathode._a_side_coating_coordinates,
            self._cathode._b_side_coating_coordinates,
            self._top_separator._coordinates
        ]
        
        # Stack all coordinates and find global bounds
        all_coords = np.vstack(coordinate_arrays)
        min_coords = np.min(all_coords, axis=0)
        max_coords = np.max(all_coords, axis=0)
        
        # Calculate dimensions and store results
        self._total_length = max_coords[0] - min_coords[0]
        self._total_width = max_coords[1] - min_coords[1]
        self._total_height = max_coords[2] - min_coords[2]
        self._start_position = tuple(min_coords)

        return self._total_length, self._start_position
    
    def _smooth_center_line(self, center_line: np.ndarray) -> np.ndarray:
        """
        Smooth center line by removing points around z-value jumps.
        
        Parameters
        ----------
        center_line : np.ndarray
            Array with x values in column 0 and z values in column 1
            
        Returns
        -------
        np.ndarray
            Smoothed center line with points removed around jumps
        """
        if len(center_line) < 2:
            return center_line
        
        x_coords = center_line[:, 0]
        z_coords = center_line[:, 1]
        
        # Calculate z differences between consecutive points
        z_diffs = np.diff(z_coords)
        
        # Find significant jumps (use a small threshold to detect actual jumps)
        jump_threshold = 1e-6  # Small threshold to detect meaningful jumps
        jump_indices = np.where(np.abs(z_diffs) > jump_threshold)[0]
        
        if len(jump_indices) == 0:
            return center_line
        
        # Create mask for points to keep
        keep_mask = np.ones(len(center_line), dtype=bool)
        
        for jump_idx in jump_indices:
            z_diff = z_diffs[jump_idx]  # Signed z difference
            z_jump = np.abs(z_diff)     # Size of the z jump
            removal_distance = 0 * z_jump  # Remove 5 times the jump size
            x_jump = x_coords[jump_idx]
            
            if z_diff > 0:  # Z jumps up - remove x values before the jump
                removal_mask = (x_coords >= (x_jump - removal_distance)) & (x_coords <= x_jump)
            else:  # Z jumps down - remove x values after the jump
                x_after_jump = x_coords[jump_idx + 1] if jump_idx + 1 < len(x_coords) else x_jump
                removal_mask = (x_coords >= x_after_jump) & (x_coords <= (x_after_jump + removal_distance))
            
            keep_mask = keep_mask & ~removal_mask
        
        return center_line[keep_mask]
    
    def _check_coordinate_intersection(self, coordinates, x_position: float) -> bool:
        """Helper function to check if x_position intersects with given coordinates.
        
        Parameters
        ----------
        coordinates : np.ndarray or None
            Coordinate array to check intersection with
        x_position : float
            The x position to check in meters
            
        Returns
        -------
        bool
            True if x_position intersects with the coordinates, False otherwise
        """
        if coordinates is None or len(coordinates) == 0:
            return False
        
        x_min = np.min(coordinates[:, 0])
        x_max = np.max(coordinates[:, 0])
        return x_min <= x_position <= x_max

    def _calculate_thickness(self):

        self._thickness = (
            self._bottom_separator._thickness +
            self._cathode._thickness + 
            self._anode._thickness +
            self._top_separator._thickness
        )

        return self._thickness

    def get_thickness_at_x(self, x_position: float) -> float:
        """Return local laminate thickness at a given unwrapped x-position (meters).

        Uses precomputed top surface (baseline + cumulative layer thickness)
        for O(log N) interpolation instead of scanning individual layers.
        Returns 0.0 if x is outside the sampled domain or no layers present.
        """
        if getattr(self, "_top_surface", None) is None or len(self._top_surface) == 0:
            return 0.0

        xs = self._top_surface[:, 0]
        if x_position < xs[0] or x_position > xs[-1]:
            return 0.0

        top_z = np.interp(x_position, xs, self._top_surface[:, 1])
        baseline_z = getattr(self, "_baseline_z", None)
        if baseline_z is None:
            # fallback: derive from baseline if available
            if (
                hasattr(self, "_flattened_center_lines")
                and "baseline" in self._flattened_center_lines
                and len(self._flattened_center_lines["baseline"]) > 0
            ):
                baseline_z = self._flattened_center_lines["baseline"][0, 1]
            else:
                return 0.0

        return max(0.0, top_z - baseline_z)

    @property
    def flattened_center_lines(self) -> dict:

        coordinates = []

        for key, value in self._flattened_center_lines.items():

            coordinate_df = (
                pd
                .DataFrame(value, columns=["x", "z"])
                .assign(Component=key)
            )

            coordinates.append(coordinate_df)

        return (
            pd
            .concat(coordinates, ignore_index=True)
            .assign(x=lambda df: df["x"] * M_TO_MM, z=lambda df: df["z"] * M_TO_MM)
            .rename(columns={"x": "X (mm)", "z": "Z (mm)"})
        )

    @property
    def separator(self) -> Separator:
        """
        Get the canonical separator used in the laminate.

        Returns
        -------
        Separator
            The canonical separator instance.
        """
        return self._canonical_separator

    @property
    def length(self) -> float:
        return round(self._length * M_TO_MM, 2)
    
    @property
    def length_range(self) -> tuple:
        return self.cathode.current_collector.length_range
    
    @property
    def length_hard_range(self) -> tuple:
        return self.cathode.current_collector.length_hard_range

    @property
    def width(self) -> float:
        return round(self._width * M_TO_MM, 2)

    @property
    def width_range(self) -> tuple:
        return self.cathode.current_collector.width_range
    
    @property
    def width_hard_range(self) -> tuple:
        return self.cathode.current_collector.width_hard_range

    @property
    def total_length(self) -> float:
        """Return the total length of the layup in mm."""
        return round(self._total_length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        """Return the total thickness of the laminate in micrometers."""
        return round(self._thickness * M_TO_UM, 2)

    @separator.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def separator(self, value: Separator):

        # Validate input type
        self.validate_type(value, Separator, "Laminate Separator")

        # transfer properties to bottom separator
        self.bottom_separator.material = value.material
        self.bottom_separator.thickness = value.thickness
        self.bottom_separator = self.bottom_separator

        # transfer properties to top separator
        self.top_separator.material = value.material
        self.top_separator.thickness = value.thickness
        self.top_separator = self.top_separator

        # Store canonical separator for unified API
        self._canonical_separator.material = value.material
        self._canonical_separator.thickness = value.thickness

    @length.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def length(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Length")
        
        # get the current length
        current_length = self.length

        # get the difference in the lengths
        length_diff = value - current_length

        # Update the length property of the bottom separator
        self.bottom_separator.length = self.bottom_separator.length + length_diff
        self.bottom_separator = self.bottom_separator

        # Update the length property of the top separator
        self.top_separator.length = self.top_separator.length + length_diff 
        self.top_separator = self.top_separator

        # Update the length property of the anode
        self.anode.current_collector.length = self.anode.current_collector.length + length_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the length property of the cathode
        self.cathode.current_collector.length = self.cathode.current_collector.length + length_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode

    @width.setter
    @calculate_coordinates
    @calculate_bulk_properties
    def width(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Width")
        
        # get the current width
        current_width = self.width

        # get the difference in the widths
        width_diff = value - current_width

        # Update the width property of the bottom separator
        self.bottom_separator.width = self.bottom_separator.width + width_diff
        self.bottom_separator = self.bottom_separator

        # Update the width property of the top separator
        self.top_separator.width = self.top_separator.width + width_diff 
        self.top_separator = self.top_separator

        # Update the width property of the anode
        self.anode.current_collector.width = self.anode.current_collector.width + width_diff
        self.anode.current_collector = self.anode.current_collector
        self.anode = self.anode

        # Update the width property of the cathode
        self.cathode.current_collector.width = self.cathode.current_collector.width + width_diff
        self.cathode.current_collector = self.cathode.current_collector
        self.cathode = self.cathode


