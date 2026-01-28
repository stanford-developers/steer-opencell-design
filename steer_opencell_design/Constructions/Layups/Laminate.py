from copy import copy, deepcopy
from enum import Enum
from typing import Tuple

import numpy as np
import pandas as pd

from steer_core.Constants.Units import *
from steer_core.Decorators.Coordinates import calculate_coordinates
from steer_core.Decorators.General import calculate_bulk_properties, calculate_all_properties

from steer_opencell_design.Components.CurrentCollectors.Base import _TapeCurrentCollector
from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups.MonoLayers import ElectrodeOrientation

from steer_opencell_design.Constructions.Layups.Base import (
    _Layup,
    SEPARATOR_WIDTH_EXTENSION,
    SEPARATOR_LENGTH_EXTENSION,
    DEFAULT_X_SPACING,
    THICKNESS_FALLBACK,
)


class Laminate(_Layup):

    def __init__(
        self,
        cathode: Cathode,
        bottom_separator: Separator,
        anode: Anode,
        top_separator: Separator,
        electrode_orientation: ElectrodeOrientation = ElectrodeOrientation.TRANSVERSE,
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
            electrode_orientation=electrode_orientation,
            name=name,
        )

        # Store canonical separator for unified API
        self._canonical_separator = Separator(
            material=bottom_separator.material,
            thickness=bottom_separator.thickness,
        )

        self._calculate_all_properties()
        self._update_properties = True

        # set voltage operating limits
        self._minimum_operating_voltage = min(self._minimum_operating_voltage_range)
        self._maximum_operating_voltage = max(self._maximum_operating_voltage_range)

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
        
        # set separator width/length ranges based on electrode sizes
        self._top_separator._set_width_range(self._anode, extended_range=SEPARATOR_WIDTH_EXTENSION)
        self._top_separator._set_length_range(self._anode, extended_range=SEPARATOR_LENGTH_EXTENSION)
        self._bottom_separator._set_width_range(self._cathode, extended_range=SEPARATOR_WIDTH_EXTENSION)
        self._bottom_separator._set_length_range(self._cathode, extended_range=SEPARATOR_LENGTH_EXTENSION)

    def _calculate_coordinates(self):
        super()._calculate_coordinates()
        self._calculate_total_geometries()

    def calculate_flattened_center_lines(self, x_spacing: float = DEFAULT_X_SPACING) -> dict:
        """Vectorized construction of flattened center lines for laminate layers.

        Builds an explicit bottom->top ordered stack and computes center line
        elevations using cumulative thickness. This replaces the prior per-layer
        search for a single "supporting" component and removes duplication.

        Parameters
        ----------
        x_spacing : float, optional
            Sampling resolution along the x-axis in meters. Determines the spacing
            between interpolation points for thickness calculations. Smaller values
            provide higher resolution but increase computation time.
            Default is 0.004 meters (4mm).

        Returns
        -------
        dict
            Dictionary mapping layer names to their flattened center line coordinates.
            Keys include component names like 'cathode_current_collector', 'anode_b_side_coating', etc.

        Notes
        -----
        - Currently no smoothing is applied (keeps geometric fidelity). A future
          enhancement could expose smoothing parameters.
        - Stores auxiliary arrays for rapid thickness interpolation.
        - The sampling resolution affects the accuracy of thickness calculations
          via get_thickness_at_x().
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

        # Filter out empty arrays (components that don't exist due to bare lengths)
        valid_layer_specs = []
        for name, coords, thickness in layer_specs:
            if coords.size > 0 and coords.shape[0] > 0:
                valid_layer_specs.append((name, coords, thickness))
        
        # Gather all x end points from valid layers only
        x_breaks = []
        for _, coords, _ in valid_layer_specs:
            x_breaks.append(coords[0, 0])
            x_breaks.append(coords[-1, 0])

        # Create common x-sampling grid
        # Get the min and max x values
        x_min, x_max = min(x_breaks), max(x_breaks)
        # Set the number of samples
        n_samples = int(self._total_length / x_spacing) + 1
        # make the x array
        x = np.linspace(x_min, x_max, n_samples)

        # Create baseline directly below lowest layer (use first valid layer's lower surface)
        # Get the first valid layer's z coordinates
        first_valid_coords_z = valid_layer_specs[0][1][:, 1]
        # Remove potential NaNs from skip coats
        first_valid_coords_z = first_valid_coords_z[~np.isnan(first_valid_coords_z)]
        # Find minimum z
        zmin = np.min(first_valid_coords_z)
        # Go half thickness of first valid layer below
        baseline_z = zmin - valid_layer_specs[0][2] / 2
        # turn into array
        baseline = np.column_stack((x, np.full_like(x, baseline_z)))

        # build layer masks for valid layers only
        layer_masks = []
        for _, coords, _ in valid_layer_specs:
            # If no nans then limit mask around min/max x
            if not np.isnan(coords).any():
                x0, x1 = coords[0, 0], coords[-1, 0]
                layer_masks.append((x >= x0) & (x <= x1))
                continue
            # otherwise build mask from segments
            else:
                # make the default mask
                mask = np.zeros_like(x, dtype=bool)
                nan_rows = np.isnan(coords[:, 0])
                groups = np.split(coords[:, 0], np.where(nan_rows)[0])
                # iterate groups and build mask from non-nan segments
                for i, g in enumerate(groups):
                    g = g[~np.isnan(g)]
                    xmin = g[0]
                    xmax = g[-1]
                    mask |= (x >= xmin) & (x <= xmax)
            layer_masks.append(mask)

        # Layer thicknesses array for valid layers only
        layer_thicknesses = [spec[2] for spec in valid_layer_specs]
        layer_thicknesses = np.array(layer_thicknesses)  # shape (L,)

        # Cumulative thickness below each layer (exclude that layer's own thickness)
        cumalitive_below_including_self = np.cumsum(layer_thicknesses[:, None] * layer_masks, axis=0)
        self_thickness = layer_thicknesses[:, None] * layer_masks
        cumulative_below = cumalitive_below_including_self - self_thickness

        # Raw total thickness profile (top surface w/out baseline offset)
        raw_total_thickness = np.sum(layer_thicknesses[:, None] * layer_masks, axis=0)
        top_surface = baseline_z + raw_total_thickness

        # Build flattened center lines for valid layers only
        flattened = {"baseline": baseline}
        layer_thickness_map = {}
        for i, (name, _coords, thickness) in enumerate(valid_layer_specs):
            mask = layer_masks[i]
            center_z = baseline_z + cumulative_below[i, mask] + thickness / 2
            flattened[name] = np.column_stack((x[mask], center_z))
            layer_thickness_map[name] = thickness

        # for each line, add one NaN row at each gap in x coordinates
        for name in flattened.keys():
            coords = flattened[name]
            coords = self.insert_gaps_with_nans(coords, 0)
            flattened[name] = coords

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
        anode_length = self._anode._current_collector._x_foil_length
        cathode_length = self._cathode._current_collector._x_foil_length

        # The laminate length is determined by the shorter of the two electrodes
        laminate_length = min(anode_length, cathode_length)

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
        anode_width = self._anode._current_collector._y_foil_length
        cathode_width = self._cathode._current_collector._y_foil_length

        # The laminate width is determined by the narrower of the two electrodes
        laminate_width = min(anode_width, cathode_width)

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
            self._anode._current_collector._foil_coordinates,
            self._anode._a_side_coating_coordinates,
            self._anode._b_side_coating_coordinates,
            self._cathode._current_collector._foil_coordinates,
            self._cathode._a_side_coating_coordinates,
            self._cathode._b_side_coating_coordinates,
            self._top_separator._coordinates
        ]
        
        # Stack all coordinates and find global bounds
        all_coords = np.vstack(coordinate_arrays)
        all_coords = all_coords[~np.isnan(all_coords).any(axis=1)]
        min_coords = np.min(all_coords, axis=0)
        max_coords = np.max(all_coords, axis=0)
        
        # Calculate dimensions and store results
        self._total_length = max_coords[0] - min_coords[0]
        self._total_width = max_coords[1] - min_coords[1]
        self._total_height = max_coords[2] - min_coords[2]
        self._start_position = tuple(min_coords)

        return self._total_length, self._start_position

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
        Returns THICKNESS_FALLBACK if x is outside the sampled domain or no layers present.
        """
        if not hasattr(self, "_top_surface"):
            raise ValueError("Top surface coordinates not calculated. Call calculate_flattened_center_lines() first.")

        xs = self._top_surface[:, 0]

        if x_position < xs.min() or x_position > xs.max():
            return THICKNESS_FALLBACK

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
                return THICKNESS_FALLBACK

        return max(THICKNESS_FALLBACK, top_z - baseline_z)

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
        return np.round(self._length * M_TO_MM, 2)
    
    @property
    def length_range(self) -> tuple:
        return self._cathode._current_collector.length_range
    
    @property
    def length_hard_range(self) -> tuple:
        return self._cathode._current_collector.length_hard_range

    @property
    def width(self) -> float:
        return np.round(self._width * M_TO_MM, 2)

    @property
    def width_range(self) -> tuple:
        return self._cathode._current_collector.width_range
    
    @property
    def width_hard_range(self) -> tuple:
        return self._cathode._current_collector.width_hard_range
    @property
    def total_length(self) -> float:
        """Return the total length of the layup in mm."""
        return np.round(self._total_length * M_TO_MM, 2)

    @property
    def thickness(self) -> float:
        """Return the total thickness of the laminate in micrometers."""
        return np.round(self._thickness * M_TO_UM, 2)

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
    @calculate_all_properties
    def length(self, value: float):

        # Validate input 
        self.validate_positive_float(value, "Laminate Length")
        
        # get the current length
        current_length = self.length

        # get the difference in the lengths
        length_diff = value - current_length

        # Update the length property of the bottom separator
        self._bottom_separator.length = self._bottom_separator.length + length_diff

        # Update the length property of the top separator
        self._top_separator.length = self._top_separator.length + length_diff

        # Update the length property of the anode
        self._anode._current_collector.length = self._anode._current_collector.length + length_diff
        self._anode.current_collector = self._anode._current_collector

        # Update the length property of the cathode
        self._cathode._current_collector.length = self._cathode._current_collector.length + length_diff
        self._cathode.current_collector = self._cathode._current_collector
        
    @width.setter
    @calculate_all_properties
    def width(self, value: float):

        # Validate input
        self.validate_positive_float(value, "Laminate Width")
        
        # get the current width
        current_width = self.width

        # get the difference in the widths
        width_diff = value - current_width

        # Update the width property of the bottom separator
        self._bottom_separator.width = self._bottom_separator.width + width_diff

        # Update the width property of the top separator
        self._top_separator.width = self._top_separator.width + width_diff

        # Update the width property of the anode
        self._anode._current_collector.width = self._anode._current_collector.width + width_diff
        self._anode.current_collector = self._anode._current_collector

        # Update the width property of the cathode
        self._cathode._current_collector.width = self._cathode._current_collector.width + width_diff
        self._cathode.current_collector = self._cathode._current_collector

