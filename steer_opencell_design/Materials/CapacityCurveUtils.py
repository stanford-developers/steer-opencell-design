# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities for processing, interpolating, and scaling half-cell voltage-capacity curves."""

import numpy as np
from typing import List, Type

from steer_core.Decorators.General import recalculate
from steer_core.Constants.Units import H_TO_S, mA_TO_A, G_TO_KG
from steer_core.Utils.CurveProcessing import (
    correct_segment_directions,
    make_segments_monotonic,
    reverse_secondary_segment,
    prepend_primary_endpoint_to_secondary,
    scale_secondary_segment,
    scale_curve,
    interpolate_between_curves,
    interpolate_curve_at_target,
    prepare_arrays_for_interp,
    truncate_and_shift_segments,
)


calculate_specific_capacity_curve = recalculate("specific_capacity_curve")
calculate_capacity_curve = recalculate(
    "capacity_curve", requires={"_mass": lambda v: v is not None}
)


class CapacityCurveMixin:
    """Mixin providing static methods for processing half-cell voltage-capacity curves.

    Handles curve direction correction, monotonicity enforcement, interpolation,
    truncation, and reversible/irreversible capacity scaling.
    """

    @staticmethod
    def _correct_curve_directions(curve: np.ndarray) -> np.ndarray:
        """Ensure charge/discharge labeling matches the larger capacity excursion."""
        return correct_segment_directions(curve)
        
    @staticmethod
    def _make_curve_monotonic(curve: np.ndarray) -> np.ndarray:
        """Force both charge and discharge trajectories to be monotonic."""
        return make_segments_monotonic(curve)
    
    @staticmethod
    def _reverse_discharge_curve(curve: np.ndarray) -> np.ndarray:
        """Mirror the discharge curve so capacity decreases from the charge endpoint."""
        return reverse_secondary_segment(curve)
    
    @staticmethod
    def _add_point_to_discharge_curve(curve: np.ndarray) -> np.ndarray:
        """Prepend the final charge point to the discharge curve for continuity."""
        return prepend_primary_endpoint_to_secondary(curve)
    
    @staticmethod
    def process_specific_capacity_curves(curve: np.ndarray) -> np.ndarray:
        """Normalize and prepare raw half-cell curves for downstream use.

        Steps include unit conversion, direction validation, monotonic cleanup,
        reversing the discharge curve, and ensuring both segments share a common
        point.

        Parameters
        ----------
        curve : np.ndarray
            Experimental curve data ordered as [specific_capacity, voltage,
            direction]. Capacity must be in mAh/g before conversion.

        Returns
        -------
        np.ndarray
            Processed curve ready for property calculations.
        """
        curve[:, 0] = curve[:, 0] * (H_TO_S * mA_TO_A / G_TO_KG)
        curve = correct_segment_directions(curve)
        curve = make_segments_monotonic(curve)
        curve = reverse_secondary_segment(curve)
        curve = prepend_primary_endpoint_to_secondary(curve)
        return curve
    
    @staticmethod
    def _apply_reversible_specific_capacity_scaling(curve: np.ndarray, scaling: float) -> np.ndarray:
        """Scale only the reversible capacity portion of the discharge curve."""
        return scale_secondary_segment(curve, scaling)

    @staticmethod
    def _apply_irreversible_specific_capacity_scaling(curve: np.ndarray, scaling: float) -> np.ndarray:
        """Uniformly scale capacity columns to model irreversible loss."""
        return scale_curve(curve, scaling)
    
    @staticmethod
    def _interpolate_curve_on_maximum_voltage(
        input_value: float,
        below_curve: np.ndarray,
        above_curve: np.ndarray,
        below_voltage_max: float,
        above_voltage_max: float,
    ) -> np.ndarray:
        """Interpolate between two curves at a target max voltage."""
        return interpolate_between_curves(
            input_value, below_curve, above_curve,
            below_voltage_max, above_voltage_max,
        )
    
    @staticmethod
    def _interpolate_curve(
        specific_capacity_curves: List[np.ndarray],
        voltage_cutoff: float,
    ) -> np.ndarray:
        """Interpolate between nearby curves so they share a target max voltage."""
        return interpolate_curve_at_target(specific_capacity_curves, voltage_cutoff)
    
    @staticmethod
    def _prepare_arrays_for_interp(x_array, y_array):
        """Prepare arrays for np.interp by ensuring they're monotonically increasing."""
        return prepare_arrays_for_interp(x_array, y_array)
        
    @staticmethod
    def _truncate_and_shift_curves(
        specific_capacity_curves: List[np.ndarray],
        voltage_cutoff: float,
        material_type: Type
        ) -> np.ndarray:
        """Truncate curves at a cutoff voltage and align charge/discharge axes."""
        from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial
        truncate_below_cutoff = (material_type == CathodeMaterial)
        return truncate_and_shift_segments(
            specific_capacity_curves, voltage_cutoff, truncate_below_cutoff
        )
    
    @staticmethod
    def _calculate_specific_capacity_curve(
        specific_capacity_curves: List[np.ndarray],
        voltage_cutoff: float,
        voltage_operation_window: tuple[float, float, float],
        material_type: Type,
        ) -> np.ndarray:
        """Select, interpolate, or truncate curves based on a voltage cutoff.

        Parameters
        ----------
        specific_capacity_curves : list[np.ndarray]
            Curve catalogue sampled at distinct maximum voltages.
        voltage_cutoff : float
            Desired maximum voltage for the returned curve.
        voltage_operation_window : tuple[float, float, float]
            Lower guard band, nominal window, and upper guard band used to
            decide whether interpolation or truncation is required.
        material_type : Type
            Electrode material class, used when truncating curves to align the
            discharge branch.

        Returns
        -------
        np.ndarray
            Curve whose maximum voltage matches ``voltage_cutoff``. The caller
            is expected to wrap this in a DataFrame if necessary.
        """
        # Calculate the cutoff voltages for each curve
        voltages_at_max_capacity = []

        for curve in specific_capacity_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            voltages_at_max_capacity.append(voltage_at_max_capacity)

        # Round voltage cutoff for consistent comparison
        rounded_voltage_cutoff = np.round(voltage_cutoff, 5)
        rounded_voltages = [round(v, 5) for v in voltages_at_max_capacity]

        # If the voltage cutoff corresponds to a particular curve, then return that curve
        if rounded_voltage_cutoff in rounded_voltages:
            curve_idx = rounded_voltages.index(rounded_voltage_cutoff)
            specific_capacity_curve = specific_capacity_curves[curve_idx].copy()

        # If the voltage is between the second and third float in operating voltage range, then interpolate between the two curves
        elif (
            np.round(min(voltage_operation_window[1:]), 5)
            <= rounded_voltage_cutoff
            <= np.round(max(voltage_operation_window[1:]), 5)
        ):
            specific_capacity_curve = CapacityCurveMixin._interpolate_curve(
                specific_capacity_curves,
                voltage_cutoff,
            )

        # If the voltage cutoff is below the second float and above the first float in the operating voltage range, then interpolate between the two curves
        elif (
            np.round(min(voltage_operation_window[:2]), 5)
            <= rounded_voltage_cutoff
            <= np.round(max(voltage_operation_window[:2]), 5)
        ):
            specific_capacity_curve = CapacityCurveMixin._truncate_and_shift_curves(
                specific_capacity_curves,
                voltage_cutoff,
                material_type,
            )

        else:
            raise ValueError(
                f"Voltage cutoff {voltage_cutoff} is not within the range of the half cell curves. "
                f"Valid range is {voltage_operation_window[0]} to {voltage_operation_window[2]}."
            )

        return specific_capacity_curve

    @staticmethod
    def _calculate_capacity_curve_properties(specific_capacity_curve):

        # get the irreversible capacity as the maximum capacity of the curve
        _irreversible_capacity = specific_capacity_curve[:, 0].max()

        # get the reversible capacity as the maximum capacity of the discharge curve
        _discharge_mask = specific_capacity_curve[:, 2] == -1
        _reversible_capacity = _irreversible_capacity - specific_capacity_curve[_discharge_mask, 0].min()

        # return both capacities
        return _irreversible_capacity, _reversible_capacity
