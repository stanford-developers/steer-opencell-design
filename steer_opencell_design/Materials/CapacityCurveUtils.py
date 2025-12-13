import numpy as np
from typing import List, Type
from functools import wraps

from steer_core.Mixins.Data import DataMixin
from steer_core.Constants.Units import H_TO_S, mA_TO_A, G_TO_KG


def calculate_specific_capacity_curve(func):
    """
    Decorator to recalculate half-cell curve properties after a method call.
    This is useful for methods that modify the half-cell curve data.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_specific_capacity_curve()
        return result
    return wrapper

def calculate_capacity_curve(func):
    """
    Decorator to recalculate half-cell curve properties after a method call.
    This is useful for methods that modify the half-cell curve data.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties and hasattr(self, '_mass') and self._mass is not None:
            self._calculate_capacity_curve()
        return result
    return wrapper


class CapacityCurveMixin:

    @staticmethod
    def _correct_curve_directions(curve: np.ndarray) -> np.ndarray:
        """Ensure charge/discharge labeling matches the larger capacity excursion.

        Parameters
        ----------
        curve : np.ndarray
            Array of shape (n, 3) ordered as [specific_capacity, voltage, direction],
            where direction is 1 for charge and -1 for discharge.

        Returns
        -------
        np.ndarray
            Curve array where the segment with the larger capacity range is tagged
            as charge and the smaller as discharge.
        """
        # select out the charge and discharge curves
        charge_curve = curve[curve[:, 2] == 1]
        discharge_curve = curve[curve[:, 2] == -1]

        # check the specific capacity ranges of the curves and make sure the charge curve has the greater range
        charge_specific_capacity_range = (
            charge_curve[:, 0].max() - charge_curve[:, 0].min()
        )
        discharge_specific_capacity_range = (
            discharge_curve[:, 0].max() - discharge_curve[:, 0].min()
        )

        if charge_specific_capacity_range > discharge_specific_capacity_range:
            return curve
        else:
            # swap the charge and discharge curves
            charge_curve[:, 2] = -1
            discharge_curve[:, 2] = 1
            return np.concatenate([discharge_curve, charge_curve], axis=0)
        
    @staticmethod
    def _make_curve_monotonic(
        curve: np.ndarray,
    ) -> np.ndarray:
        """Force both charge and discharge trajectories to be monotonic.

        Parameters
        ----------
        curve : np.ndarray
            Array with columns [specific_capacity, voltage, direction] where the
            direction column is 1 for charge and -1 for discharge.

        Returns
        -------
        np.ndarray
            Curve array whose capacity and voltage columns are individually
            monotonic within each direction segment.
        """
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()

        # Enforce monotonicity on both capacity and voltage
        charge_curve[:, 0] = DataMixin.enforce_monotonicity(charge_curve[:, 0])
        charge_curve[:, 1] = DataMixin.enforce_monotonicity(charge_curve[:, 1])

        # Enforce monotonicity
        discharge_curve[:, 0] = DataMixin.enforce_monotonicity(discharge_curve[:, 0])
        discharge_curve[:, 1] = DataMixin.enforce_monotonicity(discharge_curve[:, 1])

        return np.concatenate([charge_curve, discharge_curve], axis=0)
    
    @staticmethod
    def _reverse_discharge_curve(curve: np.ndarray) -> np.ndarray:
        """Mirror the discharge curve so capacity decreases from the charge endpoint.

        Parameters
        ----------
        curve : np.ndarray
            Half-cell curve array ([specific_capacity, voltage, direction]).

        Returns
        -------
        np.ndarray
            Curve with the discharge segment reversed such that it begins at the
            maximum specific capacity and proceeds toward zero.
        """
        max_spec_cap = curve[:, 0].max()
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()
        discharge_curve[:, 0] = -discharge_curve[:, 0] + max_spec_cap
        return np.concatenate([charge_curve, discharge_curve], axis=0)
    
    @staticmethod
    def _add_point_to_discharge_curve(curve: np.ndarray) -> np.ndarray:
        """Prepend the final charge point to the discharge curve for continuity.

        Parameters
        ----------
        curve : np.ndarray
            Curve array containing both charge and discharge segments.

        Returns
        -------
        np.ndarray
            Curve array where the discharge sequence now starts with the last
            charge point to ensure both segments share a common junction.
        """
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()
        last_charge_point = charge_curve[-1, :].copy()
        last_charge_point[2] = -1
        discharge_curve = np.vstack([last_charge_point, discharge_curve])
        return np.concatenate([charge_curve, discharge_curve], axis=0)
    
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
        curve = CapacityCurveMixin._correct_curve_directions(curve)
        curve = CapacityCurveMixin._make_curve_monotonic(curve)
        curve = CapacityCurveMixin._reverse_discharge_curve(curve)
        curve = CapacityCurveMixin._add_point_to_discharge_curve(curve)
        return curve
    
    @staticmethod
    def _apply_reversible_capacity_scaling(curve: np.ndarray, scaling: float) -> np.ndarray:
        """Scale only the reversible capacity portion of the discharge curve.

        Parameters
        ----------
        curve : np.ndarray
            Processed curve array with direction column.
        scaling : float
            Scaling factor applied to the discharge segment relative to its
            maximum specific capacity.

        Returns
        -------
        np.ndarray
            Curve with the discharge segment shifted toward higher or lower
            reversible capacity depending on the scaling factor.
        """
        # Work on a copy to avoid modifying the input
        curve_copy = curve.copy()
        charge = curve_copy[curve_copy[:, 2] == 1].copy()
        discharge = curve_copy[curve_copy[:, 2] == -1].copy()
        maximum_specific_capacity = curve_copy[:, 0].max()
        
        discharge[:, 0] = (
            scaling * (discharge[:, 0] - maximum_specific_capacity)
            + maximum_specific_capacity
        )

        result = np.concatenate([charge, discharge], axis=0)

        return result

    @staticmethod
    def _apply_irreversible_capacity_scaling(curve: np.ndarray, scaling: float) -> np.ndarray:
        """Uniformly scale capacity columns to model irreversible loss.

        Parameters
        ----------
        curve : np.ndarray
            Processed curve array.
        scaling : float
            Factor applied to all specific-capacity values.

        Returns
        -------
        np.ndarray
            Curve whose capacity axis has been globally scaled.
        """
        # Work on a copy to avoid modifying the input
        result = curve.copy()
        result[:, 0] = result[:, 0] * scaling
        return result
    
    @staticmethod
    def _interpolate_curve_on_maximum_voltage(
        input_value: float,
        below_curve: np.ndarray,
        above_curve: np.ndarray,
        below_voltage_max: float,
        above_voltage_max: float,
    ) -> np.ndarray:
        """
        Numpy version of interpolating between two curves at a target max voltage.
        Handles both charge (increasing) and discharge (decreasing) curves.

        Parameters
        ----------
        input_value : float
            The target maximum voltage to interpolate between curves.
        below_curve : np.ndarray
            The curve with the maximum voltage below the target.
        above_curve : np.ndarray
            The curve with the maximum voltage above the target.
        below_voltage_max : float
            Maximum voltage of the below curve.
        above_voltage_max : float
            Maximum voltage of the above curve.

        Returns
        -------
        np.ndarray
            Array containing the interpolated curve with columns [specific_capacity, voltage, direction].
        """
        n_points = 100

        # Check if this is a discharge curve (direction = -1)
        is_discharge = (
            below_curve[0, 2] == -1 if len(below_curve) > 0 else above_curve[0, 2] == -1
        )

        if is_discharge:
            # For discharge curves, both capacity and voltage decrease
            # Sort in descending order and flip for interpolation
            below_sorted = below_curve[
                np.argsort(below_curve[:, 0])[::-1]
            ]  # descending capacity
            above_sorted = above_curve[
                np.argsort(above_curve[:, 0])[::-1]
            ]  # descending capacity

            # Create grids (still from min to max for interpolation)
            sc_grid_low = np.linspace(
                below_sorted[:, 0].min(), below_sorted[:, 0].max(), n_points
            )

            sc_grid_high = np.linspace(
                above_sorted[:, 0].min(), above_sorted[:, 0].max(), n_points
            )

            # Interpolate voltages - flip arrays so they're increasing for np.interp
            v_low_interp = np.interp(
                sc_grid_low,
                below_sorted[:, 0][::-1],  # flip to ascending order
                below_sorted[:, 1][::-1],  # flip corresponding voltages
            )

            v_high_interp = np.interp(
                sc_grid_high,
                above_sorted[:, 0][::-1],  # flip to ascending order
                above_sorted[:, 1][::-1],  # flip corresponding voltages
            )

        else:
            # For charge curves, both capacity and voltage increase
            below_sorted = below_curve[
                np.argsort(below_curve[:, 0])
            ]  # ascending capacity
            above_sorted = above_curve[
                np.argsort(above_curve[:, 0])
            ]  # ascending capacity

            # Create grids for interpolation
            sc_grid_low = np.linspace(
                below_sorted[:, 0].min(), below_sorted[:, 0].max(), n_points
            )

            sc_grid_high = np.linspace(
                above_sorted[:, 0].min(), above_sorted[:, 0].max(), n_points
            )

            # Interpolate voltages (arrays already in ascending order)
            v_low_interp = np.interp(
                sc_grid_low,
                below_sorted[:, 0],  # specific capacity
                below_sorted[:, 1],  # voltage
            )

            v_high_interp = np.interp(
                sc_grid_high,
                above_sorted[:, 0],  # specific capacity
                above_sorted[:, 1],  # voltage
            )

        # Calculate interpolation weights
        weight_low = (above_voltage_max - input_value) / (
            above_voltage_max - below_voltage_max
        )
        weight_high = (input_value - below_voltage_max) / (
            above_voltage_max - below_voltage_max
        )

        # Interpolate values
        c_values = sc_grid_low * weight_low + sc_grid_high * weight_high
        v_interp = v_low_interp * weight_low + v_high_interp * weight_high

        # Get direction from the first curve (assuming both have same direction)
        direction = below_curve[0, 2] if len(below_curve) > 0 else above_curve[0, 2]

        # Create interpolated curve
        interpolated_curve = np.column_stack(
            [c_values, v_interp, np.full(n_points, direction)]
        )

        # If discharge curve, sort back to descending order to maintain consistency
        if is_discharge:
            interpolated_curve = interpolated_curve[
                np.argsort(interpolated_curve[:, 0])[::-1]
            ]

        return interpolated_curve
    
    @staticmethod
    def _interpolate_curve(
        specific_capacity_curves: List[np.ndarray],
        voltage_cutoff: float,
    ) -> np.ndarray:
        """Interpolate between nearby curves so they share a target max voltage.

        Parameters
        ----------
        specific_capacity_curves : list[np.ndarray]
            Collection of processed curves sampled at different maximum
            voltages.
        voltage_cutoff : float
            Target voltage to interpolate between.

        Returns
        -------
        np.ndarray
            Interpolated curve with shape (n_points, 3) ordered as
            [specific_capacity, voltage, direction].
        """
        # Calculate voltage at max capacity for each curve
        voltages_at_max_capacity = []
        for curve in specific_capacity_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            voltages_at_max_capacity.append(voltage_at_max_capacity)

        voltages_at_max_capacity = np.array(voltages_at_max_capacity)

        # Get the closest curve below the voltage cutoff
        below_mask = voltages_at_max_capacity <= voltage_cutoff
        below_voltages = voltages_at_max_capacity[below_mask]
        max_below_voltage = np.max(below_voltages)
        below_curve_idx = np.where(voltages_at_max_capacity == max_below_voltage)[0][0]
        closest_below_curve = specific_capacity_curves[below_curve_idx]

        # Get the closest curve above the voltage cutoff
        above_mask = voltages_at_max_capacity >= voltage_cutoff
        above_voltages = voltages_at_max_capacity[above_mask]
        min_above_voltage = np.min(above_voltages)
        above_curve_idx = np.where(voltages_at_max_capacity == min_above_voltage)[0][0]
        closest_above_curve = specific_capacity_curves[above_curve_idx]

        # Split below curve into charge and discharge
        below_charge = closest_below_curve[closest_below_curve[:, 2] == 1]
        below_discharge = closest_below_curve[closest_below_curve[:, 2] == -1]

        # Split above curve into charge and discharge
        above_charge = closest_above_curve[closest_above_curve[:, 2] == 1]
        above_discharge = closest_above_curve[closest_above_curve[:, 2] == -1]

        # Interpolate charge curve
        charge_curve = CapacityCurveMixin._interpolate_curve_on_maximum_voltage(
            voltage_cutoff,
            below_charge,
            above_charge,
            max_below_voltage,
            min_above_voltage,
        )

        # Interpolate discharge curve
        discharge_curve = CapacityCurveMixin._interpolate_curve_on_maximum_voltage(
            voltage_cutoff,
            below_discharge,
            above_discharge,
            max_below_voltage,
            min_above_voltage,
        )

        # Sort discharge curve by specific capacity (descending)
        discharge_curve = discharge_curve[np.argsort(discharge_curve[:, 0])[::-1]]

        # Concatenate charge and discharge curves
        curve = np.vstack([charge_curve, discharge_curve])

        return curve
    
    @staticmethod
    def _prepare_arrays_for_interp(x_array, y_array):
        """
        Prepare arrays for np.interp by ensuring they're monotonically increasing.
        If both arrays are decreasing, flip both. If they're in opposite directions,
        flip the y array to match x direction.

        Parameters
        ----------
        x_array : np.ndarray
            The x values (e.g., voltage)
        y_array : np.ndarray
            The y values (e.g., capacity)

        Returns
        -------
        tuple
            (x_sorted, y_sorted) both monotonically increasing
        """
        # Check monotonicity direction
        x_increasing = np.all(np.diff(x_array) >= 0) or np.mean(np.diff(x_array)) > 0
        y_increasing = np.all(np.diff(y_array) >= 0) or np.mean(np.diff(y_array)) > 0

        # If both are decreasing, flip both
        if not x_increasing and not y_increasing:
            return x_array[::-1], y_array[::-1]

        # If x is decreasing but y is increasing (or vice versa), flip x and sort accordingly
        elif not x_increasing:
            # Sort by x (ascending) and reorder y accordingly
            sort_idx = np.argsort(x_array)
            return x_array[sort_idx], y_array[sort_idx]

        # If x is increasing (normal case)
        else:
            return x_array, y_array
        
    @staticmethod
    def _truncate_and_shift_curves(
        specific_capacity_curves: List[np.array],
        voltage_cutoff: float,
        material_type: Type
        ) -> np.ndarray:
        """Truncate curves at a cutoff voltage and align charge/discharge axes.

        Parameters
        ----------
        specific_capacity_curves : list[np.ndarray]
            Collection of processed curves sampled at different maximum
            voltages.
        voltage_cutoff : float
            Target voltage at which both charge and discharge segments should
            terminate.
        material_type : Type
            Electrode material class (e.g., cathode vs anode) used to determine
            whether voltages increase or decrease with capacity.

        Returns
        -------
        np.ndarray
            Combined curve truncated at the cutoff voltage with the discharge
            segment shifted so both segments share the same capacity origin.
        """

        # Get curve with minimum voltage at max capacity
        max_capacity_voltages = [
            curve[np.argmax(curve[:, 0]), 1] for curve in specific_capacity_curves
        ]

        min_voltage_curve = specific_capacity_curves[
            np.argmin(max_capacity_voltages)
        ].copy()

        # Split and process curves
        charge = min_voltage_curve[min_voltage_curve[:, 2] == 1]
        discharge = min_voltage_curve[min_voltage_curve[:, 2] == -1]

        # Prepare arrays for interpolation
        charge_v_sorted, charge_c_sorted = CapacityCurveMixin._prepare_arrays_for_interp(
            charge[:, 1], charge[:, 0]
        )
        discharge_v_sorted, discharge_c_sorted = CapacityCurveMixin._prepare_arrays_for_interp(
            discharge[:, 1], discharge[:, 0]
        )

        charge_cap_interp = np.interp(
            voltage_cutoff, charge_v_sorted, charge_c_sorted
        )

        discharge_cap_interp = np.interp(
            voltage_cutoff, discharge_v_sorted, discharge_c_sorted
        )

        # Add interpolated points and truncate
        charge_extended = np.vstack(
            [charge, [charge_cap_interp, voltage_cutoff, 1]]
        )
        discharge_extended = np.vstack(
            [[discharge_cap_interp, voltage_cutoff, -1], discharge]
        )

        # Truncate based on material type
        from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial
        
        voltage_condition = (
            (lambda v: v <= voltage_cutoff)
            if material_type == CathodeMaterial
            else (lambda v: v >= voltage_cutoff)
        )

        charge_final = charge_extended[voltage_condition(charge_extended[:, 1])]
        discharge_final = discharge_extended[
            voltage_condition(discharge_extended[:, 1])
        ]

        # Calculate and apply shift
        charge_at_voltage = charge_final[
            np.isclose(charge_final[:, 1], voltage_cutoff), 0
        ][0]
        discharge_at_voltage = discharge_final[
            np.isclose(discharge_final[:, 1], voltage_cutoff), 0
        ][0]

        discharge_final[:, 0] += charge_at_voltage - discharge_at_voltage

        return np.vstack([charge_final, discharge_final])
    
    @staticmethod
    def _calculate_specific_capacity_curve(
        specific_capacity_curves: List[np.array],
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

        # If the voltage cutoff corresponds to a particular curve, then return that curve
        if rounded_voltage_cutoff in [round(v, 5) for v in voltages_at_max_capacity]:
            curve_idx = voltages_at_max_capacity.index(voltage_cutoff)
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


