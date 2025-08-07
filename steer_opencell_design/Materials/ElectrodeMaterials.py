from steer_core.DataManager import DataManager
from steer_core.Constants.Units import *
from steer_core.Decorators.Electrochemical import calculate_half_cell_curves_properties
from steer_core.Mixins.Data import DataMixin

from steer_opencell_design.Materials.RawMaterials import _Material

import pandas as pd
import numpy as np
import plotly.express as px
from pickle import dumps, loads
from typing import List, Union, Optional
from copy import deepcopy


class _ActiveMaterial(_Material, DataMixin):

    def __init__(
            self, 
            name: str,
            reference: str,
            specific_cost: float, 
            density: float,
            half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
            color: Optional[str] = '#2c2c2c',
            voltage_cutoff: Optional[float] = None,
            extrapolation_window: Optional[float] = 0.2,
            reversible_capacity_scaling: Optional[float] = 1.0,
            irreversible_capacity_scaling: Optional[float] = 1.0
        ) -> None:
        """
        Initialize an object that represents an active material.
        
        Parameters
        ----------
        name : str
            Name of the material.
        reference : str
            Reference electrode for the material, e.g., 'Li/Li+'.
        specific_cost : float
            Specific cost of the material in $/kg.
        density : float
            Density of the material in g/cm^3.
        half_cell_curves : Union[List[pd.DataFrame], pd.DataFrame]
            Half cell curves for the material, either as a list of pandas DataFrames or a single DataFrame.
        color : str
            Color of the material, used for plotting.
        voltage_cutoff : Optional[float]
            The voltage cutoff for the half cell curves in V. This is the maximum voltage (for CathodeMaterial) or minimum voltage (for AnodeMaterial) 
            at which the half cell curve will be calculated.
        extrapolation_window : Optional[float]
            The extrapolation window in V. This is the amount of voltage below the maximum voltage (for CathodeMaterial) or above the minimum voltage (for AnodeMaterial)
            of the half cell curves that will be used for extrapolation. This allows for estimation of voltage profiles over a voltage window
        reversible_capacity_scaling : Optional[float]
            Scaling factor for the reversible capacity of the material. Default is 1.0 (no scaling).
        irreversible_capacity_scaling : Optional[float]
            Scaling factor for the irreversible capacity of the material. Default is 1.0 (no scaling).
        """
        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color
        )

        self._update_properties = False

        self.reference = reference
        self.extrapolation_window = extrapolation_window
        self.half_cell_curves = half_cell_curves
        self.voltage_cutoff = voltage_cutoff
        self.reversible_capacity_scaling = reversible_capacity_scaling
        self.irreversible_capacity_scaling = irreversible_capacity_scaling

        self._update_properties = True

    def _calculate_all_properties(self) -> None:
        self._calculate_half_cell_curves_properties()

    def _correct_curve_directions(
            self,
            curve: np.ndarray
    ) -> np.ndarray:
        """
        Function to check the directions of the charge and discharge curves in the half cell data. 
        It will ensure that the charge curve has a greater specific capacity range than the discharge curve.

        Parameters
        ----------
        curve : np.ndarray
            The half cell curve data as a numpy array with columns for specific capacity, voltage, and direction.
            The direction is represented as 1 for charge and -1 for discharge.
        """
        # select out the charge and discharge curves
        charge_curve = curve[curve[:,2] == 1]
        discharge_curve = curve[curve[:,2] == -1]

        # check the specific capacity ranges of the curves and make sure the charge curve has the greater range
        charge_specific_capacity_range = charge_curve[:, 0].max() - charge_curve[:, 0].min()
        discharge_specific_capacity_range = discharge_curve[:, 0].max() - discharge_curve[:, 0].min()

        if charge_specific_capacity_range > discharge_specific_capacity_range:
            return curve
        else:
            # swap the charge and discharge curves
            charge_curve[:, 2] = -1
            discharge_curve[:, 2] = 1
            return np.concatenate([discharge_curve, charge_curve], axis=0)

    def _reverse_discharge_curve(
            self,
            curve: np.ndarray
    ) -> np.ndarray:
        """
        Function to reverse the discharge curve in the half cell data. It will ensure that the discharge curve is shifted to the right

        Parameters
        ----------
        curve : np.ndarray
            The half cell curve data as a numpy array with columns for specific capacity, voltage, and direction.
            The direction is represented as 1 for charge and -1 for discharge.
        """
        max_spec_cap = curve[:, 0].max()
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()
        discharge_curve[:, 0] = -discharge_curve[:, 0] + max_spec_cap
        return np.concatenate([charge_curve, discharge_curve], axis=0)

    def _make_curve_monotonic(
        self,
        curve: np.ndarray,
    ) -> np.ndarray:
        """
        Make charge and discharge curves monotonic separately.
        
        Parameters
        ----------
        curve : np.ndarray
            Array with columns [specific_capacity, voltage, direction]
            where direction: 1 = charge, -1 = discharge
        """
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()

        # Enforce monotonicity on both capacity and voltage
        charge_curve[:, 0] = self.enforce_monotonicity(charge_curve[:, 0])
        charge_curve[:, 1] = self.enforce_monotonicity(charge_curve[:, 1])
        
        # Enforce monotonicity
        discharge_curve[:, 0] = self.enforce_monotonicity(discharge_curve[:, 0])
        discharge_curve[:, 1] = self.enforce_monotonicity(discharge_curve[:, 1])

        return np.concatenate([charge_curve, discharge_curve], axis=0)

    def _add_point_to_discharge_curve(
        self,
        curve: np.ndarray
    ) -> np.ndarray:
        """
        Function to add the last point of the charge curve to the discharge curve.
        """
        charge_curve = curve[curve[:, 2] == 1].copy()
        discharge_curve = curve[curve[:, 2] == -1].copy()
        last_charge_point = charge_curve[-1, :].copy()
        last_charge_point[2] = -1  # Change direction to discharge
        discharge_curve = np.vstack([last_charge_point, discharge_curve])

        return np.concatenate([charge_curve, discharge_curve], axis=0)

    def _process_half_cell_curves(
            self, 
            half_cell_curves: np.ndarray
        ) -> np.ndarray:
        """
        Function to process the half cell curves. It will calculate the voltage and specific capacity maximums and then reflect and shift the curves if
        the specific capacity at the minimum voltage is greater than the specific capacity at the maximum voltage. It will store these processed curves
        in the `_half_cell_curves` attribute. This contains all the experimental input data for the half cell curves. 

        Parameters
        ----------
        half_cell_curves : Union[List[pd.DataFrame], pd.DataFrame]
            Half cell curves for the material, either as a list of pandas DataFrames or a single DataFrame.
        """
        new_half_cells_curves = []

        for curve in half_cell_curves:
            curve[:, 0] = curve[:, 0] * (H_TO_S * mA_TO_A / G_TO_KG)
            curve = self._correct_curve_directions(curve)
            curve = self._make_curve_monotonic(curve)
            curve = self._reverse_discharge_curve(curve)
            curve = self._add_point_to_discharge_curve(curve)
            new_half_cells_curves.append(curve)

        self._half_cell_curves = new_half_cells_curves

    def _apply_reversible_capacity_scaling(self, scaling: float):
        """
        Apply scaling to the reversible capacity of the half cell curves.

        Parameters
        ----------
        scaling : float
            Scaling factor for the reversible capacity. This is applied to the specific capacity of the discharge curves.
        """
        data = self._half_cell_curve.copy()
        charge = data[data[:, 2] == 1]
        discharge = data[data[:, 2] == -1]
        maximum_specific_capacity = data[:, 0].max()
        discharge[:, 0] = (scaling * (discharge[:, 0] - maximum_specific_capacity) + maximum_specific_capacity)
        self._half_cell_curve = np.concatenate([charge, discharge], axis=0)

    def _apply_irreversible_capacity_scaling(self, scaling: float):
        """
        Apply scaling to the irreversible capacity of the half cell curves.

        Parameters
        ----------
        scaling : float
            Scaling factor for the irreversible capacity. This is applied to the specific capacity of the discharge curves.
        """
        data = self._half_cell_curve.copy()
        data[:, 0] = data[:, 0] * scaling
        self._half_cell_curve = data
        
    def _interpolate_curve_on_maximum_voltage(
        self,
        input_value: float,
        below_curve: np.ndarray,
        above_curve: np.ndarray,
        below_voltage_max: float,
        above_voltage_max: float
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
        is_discharge = below_curve[0, 2] == -1 if len(below_curve) > 0 else above_curve[0, 2] == -1
        
        if is_discharge:
            # For discharge curves, both capacity and voltage decrease
            # Sort in descending order and flip for interpolation
            below_sorted = below_curve[np.argsort(below_curve[:, 0])[::-1]]  # descending capacity
            above_sorted = above_curve[np.argsort(above_curve[:, 0])[::-1]]  # descending capacity
            
            # Create grids (still from min to max for interpolation)
            sc_grid_low = np.linspace(
                below_sorted[:, 0].min(),
                below_sorted[:, 0].max(),
                n_points
            )
            
            sc_grid_high = np.linspace(
                above_sorted[:, 0].min(),
                above_sorted[:, 0].max(),
                n_points
            )
            
            # Interpolate voltages - flip arrays so they're increasing for np.interp
            v_low_interp = np.interp(
                sc_grid_low,
                below_sorted[:, 0][::-1],  # flip to ascending order
                below_sorted[:, 1][::-1]   # flip corresponding voltages
            )

            v_high_interp = np.interp(
                sc_grid_high,
                above_sorted[:, 0][::-1],  # flip to ascending order
                above_sorted[:, 1][::-1]   # flip corresponding voltages
            )
            
        else:
            # For charge curves, both capacity and voltage increase
            below_sorted = below_curve[np.argsort(below_curve[:, 0])]  # ascending capacity
            above_sorted = above_curve[np.argsort(above_curve[:, 0])]  # ascending capacity
            
            # Create grids for interpolation
            sc_grid_low = np.linspace(
                below_sorted[:, 0].min(),
                below_sorted[:, 0].max(),
                n_points
            )

            sc_grid_high = np.linspace(
                above_sorted[:, 0].min(),
                above_sorted[:, 0].max(),
                n_points
            )

            # Interpolate voltages (arrays already in ascending order)
            v_low_interp = np.interp(
                sc_grid_low,
                below_sorted[:, 0],  # specific capacity
                below_sorted[:, 1]   # voltage
            )

            v_high_interp = np.interp(
                sc_grid_high,
                above_sorted[:, 0],  # specific capacity
                above_sorted[:, 1]   # voltage
            )

        # Calculate interpolation weights
        weight_low = (above_voltage_max - input_value) / (above_voltage_max - below_voltage_max)
        weight_high = (input_value - below_voltage_max) / (above_voltage_max - below_voltage_max)

        # Interpolate values
        c_values = sc_grid_low * weight_low + sc_grid_high * weight_high
        v_interp = v_low_interp * weight_low + v_high_interp * weight_high

        # Get direction from the first curve (assuming both have same direction)
        direction = below_curve[0, 2] if len(below_curve) > 0 else above_curve[0, 2]

        # Create interpolated curve
        interpolated_curve = np.column_stack([
            c_values,
            v_interp,
            np.full(n_points, direction)
        ])
        
        # If discharge curve, sort back to descending order to maintain consistency
        if is_discharge:
            interpolated_curve = interpolated_curve[np.argsort(interpolated_curve[:, 0])[::-1]]

        return interpolated_curve

    def _interpolate_curve(self) -> np.ndarray:
        """
        Get the half cell curves interpolated on a maximum voltage using numpy arrays.

        Returns
        -------
        np.ndarray
            Interpolated curve with shape (n_points, 3) where columns are [specific_capacity, voltage, direction]
        """
        # Calculate voltage at max capacity for each curve
        voltages_at_max_capacity = []
        for curve in self._half_cell_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            voltages_at_max_capacity.append(voltage_at_max_capacity)
        
        voltages_at_max_capacity = np.array(voltages_at_max_capacity)
        
        # Get the closest curve below the voltage cutoff
        below_mask = voltages_at_max_capacity <= self._voltage_cutoff
        below_voltages = voltages_at_max_capacity[below_mask]
        max_below_voltage = np.max(below_voltages)
        below_curve_idx = np.where(voltages_at_max_capacity == max_below_voltage)[0][0]
        closest_below_curve = self._half_cell_curves[below_curve_idx]
        
        # Get the closest curve above the voltage cutoff
        above_mask = voltages_at_max_capacity >= self._voltage_cutoff
        above_voltages = voltages_at_max_capacity[above_mask]
        min_above_voltage = np.min(above_voltages)
        above_curve_idx = np.where(voltages_at_max_capacity == min_above_voltage)[0][0]
        closest_above_curve = self._half_cell_curves[above_curve_idx]
        
        # Split below curve into charge and discharge
        below_charge = closest_below_curve[closest_below_curve[:, 2] == 1]
        below_discharge = closest_below_curve[closest_below_curve[:, 2] == -1]
        
        # Split above curve into charge and discharge
        above_charge = closest_above_curve[closest_above_curve[:, 2] == 1]
        above_discharge = closest_above_curve[closest_above_curve[:, 2] == -1]

        # Interpolate charge curve
        charge_curve = self._interpolate_curve_on_maximum_voltage(
            self._voltage_cutoff,
            below_charge,
            above_charge,
            max_below_voltage,
            min_above_voltage
        )
        
        # Interpolate discharge curve
        discharge_curve = self._interpolate_curve_on_maximum_voltage(
            self._voltage_cutoff,
            below_discharge,
            above_discharge,
            max_below_voltage,
            min_above_voltage
        )
        
        # Sort discharge curve by specific capacity (descending)
        discharge_curve = discharge_curve[np.argsort(discharge_curve[:, 0])[::-1]]
        
        # Concatenate charge and discharge curves
        return np.vstack([charge_curve, discharge_curve])

    def _prepare_arrays_for_interp(self, x_array, y_array):
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

    def _truncate_and_shift_curves(self) -> np.ndarray:
        """Numpy-optimized version of truncate and shift curves."""
        
        # Get curve with minimum voltage at max capacity
        max_capacity_voltages = [curve[np.argmax(curve[:, 0]), 1] for curve in self._half_cell_curves]
        min_voltage_curve = self._half_cell_curves[np.argmin(max_capacity_voltages)].copy()

        # Split and process curves
        charge = min_voltage_curve[min_voltage_curve[:, 2] == 1]
        discharge = min_voltage_curve[min_voltage_curve[:, 2] == -1]
        
        # Prepare arrays for interpolation
        charge_v_sorted, charge_c_sorted = self._prepare_arrays_for_interp(charge[:, 1], charge[:, 0])
        discharge_v_sorted, discharge_c_sorted = self._prepare_arrays_for_interp(discharge[:, 1], discharge[:, 0])
        
        charge_cap_interp = np.interp(self._voltage_cutoff, charge_v_sorted, charge_c_sorted)
        discharge_cap_interp = np.interp(self._voltage_cutoff, discharge_v_sorted, discharge_c_sorted)
        
        # Add interpolated points and truncate
        charge_extended = np.vstack([charge, [charge_cap_interp, self._voltage_cutoff, 1]])
        discharge_extended = np.vstack([[discharge_cap_interp, self._voltage_cutoff, -1], discharge])
        
        # Truncate based on material type
        voltage_condition = (lambda v: v <= self._voltage_cutoff) if type(self).__name__ == 'CathodeMaterial' else (lambda v: v >= self._voltage_cutoff)
        
        charge_final = charge_extended[voltage_condition(charge_extended[:, 1])]
        discharge_final = discharge_extended[voltage_condition(discharge_extended[:, 1])]
        
        # Calculate and apply shift
        charge_at_voltage = charge_final[np.isclose(charge_final[:, 1], self._voltage_cutoff), 0][0]
        discharge_at_voltage = discharge_final[np.isclose(discharge_final[:, 1], self._voltage_cutoff), 0][0]
        
        discharge_final[:, 0] += (charge_at_voltage - discharge_at_voltage)
        
        return np.vstack([charge_final, discharge_final])

    def _calculate_half_cell_curve(self) -> pd.DataFrame:
        """
        Calculate the half cell curve based on the voltage cutoff and whether to extrapolate or truncate the curves.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the half cell curve with columns 'specific_capacity', 'voltage', and 'direction'.
        """
        # Calculate the cutoff voltages for each curve
        voltages_at_max_capacity = []
        for curve in self._half_cell_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            voltages_at_max_capacity.append(voltage_at_max_capacity)

        # If the voltage cutoff corresponds to a particular curve, then return that curve
        if self._voltage_cutoff in voltages_at_max_capacity:
            curve_idx = voltages_at_max_capacity.index(self._voltage_cutoff)
            half_cell_curve = self._half_cell_curves[curve_idx].copy()

        # If the voltage is between the second and third float in operating voltage range, then interpolate between the two curves
        elif min(self._voltage_operation_window[1:]) < self._voltage_cutoff < max(self._voltage_operation_window[1:]):
            half_cell_curve = self._interpolate_curve()

        # If the voltage cutoff is below the second float and above the first float in the operating voltage range, then interpolate between the two curves
        elif min(self._voltage_operation_window[:2]) < self._voltage_cutoff < max(self._voltage_operation_window[:2]):
            half_cell_curve = self._truncate_and_shift_curves()

        else:
            raise ValueError(
                f"Voltage cutoff {self._voltage_cutoff} is not within the range of the half cell curves. "
                f"Valid range is {self._voltage_operation_window[0]} to {self._voltage_operation_window[2]}."
            )

        return half_cell_curve

    def _get_default_curve_from_curves(self) -> None:
        """
        Get the default half cell curve from the half cell curves.
        
        :return: pd.DataFrame: The default half cell curve.
        """
        half_cell_curves = self._half_cell_curves.copy()

        # get the maximum specific capacity for each half cell curve
        maximum_specific_capacities = []
        for hcc in half_cell_curves:
            maximum_specific_capacities.append(np.max(hcc[:,0]))

        # get the index of the half cell curve with the maximum specific capacity
        max_index = np.argmax(maximum_specific_capacities)

        # get the half cell curve with the maximum specific capacity
        self._half_cell_curve = self._half_cell_curves[max_index].copy()

        # get the voltage at maximum specific capacity
        self._cutoff_voltage = self._half_cell_curve[self._half_cell_curve[:, 0] == np.max(self._half_cell_curve[:, 0]), 1][0]

    def _get_maximum_operating_voltage(self) -> float:
        """
        Function to get the maximum operating voltage of the half cell curves.
        """
        max_voltages = []
        
        for curve in self._half_cell_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            max_voltages.append(voltage_at_max_capacity)

        self._maximum_operating_voltage = np.max(max_voltages)

    def _get_minimum_operating_voltage(self) -> float:
        """
        Function to get the minimum operating voltage of the half cell curves without extrapolation.
        """
        max_voltages = []
        
        for curve in self._half_cell_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            max_voltages.append(voltage_at_max_capacity)

        self._minimum_operating_voltage = np.min(max_voltages)

    def _get_operating_voltage_range(self) -> tuple:
        """
        Function to get the operating voltage range of the half cell curves.
        
        Returns
        -------
        tuple: A tuple containing the discharged operating voltage with extrapolation, the discharged operating voltage without extrapolation, and the charged operating voltage.
        """
        if type(self) == CathodeMaterial:

            self._voltage_operation_window = (
                self._minimum_operating_voltage - self._extrapolation_window,
                self._minimum_operating_voltage,
                self._maximum_operating_voltage
            )
        
        elif type(self) == AnodeMaterial:

            self._voltage_operation_window = (
                self._minimum_operating_voltage + self._extrapolation_window,
                self._minimum_operating_voltage,
                self._maximum_operating_voltage
            )

    def _calculate_half_cell_curves_properties(self):
        self._get_maximum_operating_voltage()
        self._get_minimum_operating_voltage()
        self._get_operating_voltage_range()

    def plot_curves(self, **kwargs):

        fig = px.line(
            self.half_cell_curves,
            x='Specific Capacity (mAh/g)',
            y='Voltage (V)',
            color='Voltage at Maximum Capacity (V)',
            line_shape='spline',
        )

        fig.update_layout(
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return fig

    def plot_half_cell_curve(self, **kwargs):

        fig = px.line(
            self.half_cell_curve,
            x='Specific Capacity (mAh/g)',
            y='Voltage (V)',
            line_shape='spline',
        )

        fig.update_layout(
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        fig.update_traces(line=dict(color=self.color))
        
        return fig

    def pickle(self):
        """
        Serializes the object to a byte stream.
        
        :return: bytes: Serialized byte stream of the object.
        """
        return dumps(self)

    @property
    def voltage_cutoff(self) -> float:
        """
        Get the maximum voltage of the half cell curves.
        """
        return self._voltage_cutoff

    @property
    def voltage_cutoff_range(self) -> tuple:
        """
        Get the valid voltage range for the half cell curves.
        
        :return: tuple: (minimum voltage, maximum voltage)
        """
        return (
            round(float(self._voltage_operation_window[0]), 2), 
            round(float(self._voltage_operation_window[2]), 2)
        )

    @property
    def extrapolation_window(self) -> float:
        """
        Get the extrapolation window for the half cell curves.
        
        :return: float: Extrapolation window in V.
        """
        return self._extrapolation_window

    @property
    def reference(self) -> str:
        """
        Get the reference electrode for the material.
        
        :return: str: Reference electrode for the material, e.g., 'Li/Li+'
        """
        return self._reference

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        return (
            pd.DataFrame(
                self._half_cell_curve,
                columns=['specific_capacity', 'voltage', 'direction']
            )
            .assign(
                direction = lambda x: np.where(x['direction'] == 1, 'charge', 'discharge'),
                specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
            ).rename(
                columns={
                    'specific_capacity': 'Specific Capacity (mAh/g)', 
                    'voltage': 'Voltage (V)', 
                    'direction': 'Direction',
                }
            ).round(
                4
            )
        )

    @property
    def half_cell_curves(self) -> pd.DataFrame:

        data_list = []

        for curve in self._half_cell_curves:

            df = (
                pd.DataFrame(
                    curve,
                    columns=['specific_capacity', 'voltage', 'direction']
                )
                .assign(
                    direction = lambda x: np.where(x['direction'] == 1, 'charge', 'discharge'),
                    specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    voltage_at_max_capacity = lambda x: x['voltage'].max(),
                ).rename(
                    columns={
                        'specific_capacity': 'Specific Capacity (mAh/g)', 
                        'voltage': 'Voltage (V)', 
                        'direction': 'Direction',
                        'voltage_at_max_capacity': 'Voltage at Maximum Capacity (V)',
                    }
                ).round(
                    4
                )
            )

            data_list.append(df)

        return pd.concat(data_list, ignore_index=True)

    @property
    def irreversible_capacity_scaling(self) -> float:
        return self._irreversible_capacity_scaling

    @property
    def reversible_capacity_scaling(self) -> float:
        return self._reversible_capacity_scaling

    @reference.setter
    def reference(self, reference: str):
        self.validate_electrochemical_reference(reference)
        self._reference = reference

    @reversible_capacity_scaling.setter
    def reversible_capacity_scaling(self, scaling: float):
        """
        Set the reversible capacity scaling factor.
        
        :param scaling: float: scaling factor for reversible capacity
        """
        self.validate_fraction(scaling, 'Reversible capacity scaling')
        
        original_scaling = self._reversible_capacity_scaling if hasattr(self, '_reversible_capacity_scaling') else 1.0
        self._reversible_capacity_scaling = scaling
        
        # undo previous scaling to get original curve
        if original_scaling != 1:
            self._apply_reversible_capacity_scaling(1/original_scaling)
                
        # apply the new scaling factor
        self._apply_reversible_capacity_scaling(self._reversible_capacity_scaling)
     
    @voltage_cutoff.setter
    def voltage_cutoff(self, voltage: float) -> None:
        """
        Set the voltage cutoff for the half cell curves.

        Parameters
        ----------
        voltage : float
            The voltage cutoff for the half cell curves in V. This is the maximum voltage at which the half cell curve will be calculated.

        Raises
        ------
        ValueError
            If the voltage cutoff is not a positive float, or if it is outside the valid voltage range for the half cell curves.
        ValueError
            If the voltage cutoff is less than the minimum extrapolated voltage or greater than the maximum voltage of the half cell curves.
        ValueError
            If the voltage cutoff is less than the minimum voltage of the half cell curves, which requires truncation and shifting of the curves.
        ValueError
            If the voltage cutoff is greater than the maximum voltage of the half cell curves, which requires interpolation of the curves.
        """
        # Check if the voltage is None, which means we want to use the default curve
        if voltage is None:
            self._get_default_curve_from_curves()

        # calculate the half cell curve based on the voltage cutoff and the available data
        else:
            self.validate_positive_float(voltage, 'Voltage cutoff')
            self._voltage_cutoff = voltage
            self._half_cell_curve = self._calculate_half_cell_curve()

            if hasattr(self, '_irreversible_capacity_scaling') and self._irreversible_capacity_scaling != 1.0:
                self._apply_irreversible_capacity_scaling(self._irreversible_capacity_scaling)

            if hasattr(self, '_reversible_capacity_scaling') and self._reversible_capacity_scaling != 1.0:
                self._apply_reversible_capacity_scaling(self._reversible_capacity_scaling)

    @irreversible_capacity_scaling.setter
    def irreversible_capacity_scaling(self, scaling: float):
        """
        Set the irreversible capacity scaling factor.
        
        :param scaling: float: scaling factor for irreversible capacity
        """
        self.validate_fraction(scaling, 'Irreversible capacity scaling')
        original_scaling = self._irreversible_capacity_scaling if hasattr(self, '_irreversible_capacity_scaling') else 1.0
        self._irreversible_capacity_scaling = float(scaling)

        # undo previous scaling to get original curve
        if original_scaling != 1:
            self._apply_irreversible_capacity_scaling(1/original_scaling)
        
        # apply the new scaling factor
        self._apply_irreversible_capacity_scaling(self._irreversible_capacity_scaling)

    @half_cell_curves.setter
    def half_cell_curves(self, half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame]) -> None:
        
        half_cell_curves = deepcopy(half_cell_curves)

        if not isinstance(half_cell_curves, List): 
            half_cell_curves = [half_cell_curves]
        
        for df in half_cell_curves:
            self.validate_pandas_dataframe(df, 'half cell curves', column_names=['specific_capacity', 'voltage', 'direction'])
        
        # map the direction values to integers for faster processing
        direction_map = {'charge': 1, 'discharge': -1}
        for df in half_cell_curves:
            df['direction'] = df['direction'].map(direction_map)

        # Then convert to array
        array_list = [df[['specific_capacity', 'voltage', 'direction']].to_numpy() for df in half_cell_curves]

        # Apply additional processing to the half cell curves
        self._process_half_cell_curves(array_list)

        # Store useful values for the half cell curves
        self._calculate_half_cell_curves_properties()

    @extrapolation_window.setter
    @calculate_half_cell_curves_properties
    def extrapolation_window(self, window: float):
        self.validate_positive_float(window, 'Extrapolation window')        
        self._extrapolation_window = abs(float(window))

    def __lt__(self, other):

        if not isinstance(other, _ActiveMaterial):
            raise ValueError("Can only compare ActiveMaterial objects together")
        
        if self._name is not None and other._name is not None:
            if self._name < other._name:
                return True
            elif self._name > other._name:
                return False
            
        return self._time_stamp < other._time_stamp
    
    def __gt__(self, other):

        if not isinstance(other, _ActiveMaterial):
            raise ValueError("Can only compare ActiveMaterial objects together")
        
        if self._name is not None and other._name is not None:
            if self._name > other._name:
                return True
            elif self._name < other._name:
                return False
            
        return self._time_stamp > other._time_stamp


class CathodeMaterial(_ActiveMaterial):

    def __init__(
            self, 
            name: str,
            reference: str,
            specific_cost: float, 
            density: float,
            half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
            color: str = '#2c2c2c',
            voltage_cutoff: float = None,
            extrapolation_window: float = 0.2,
            reversible_capacity_scaling: float = 1.0,
            irreversible_capacity_scaling: float = 1.0
        ):
        """
        Initialize an object that represents a cathode material.
        
        Parameters
        ----------
        name : str
            Name of the material.
        reference : str
            Reference electrode for the material, e.g., 'Li/Li+'.
        specific_cost : float
            Specific cost of the material in $/kg.
        density : float
            Density of the material in g/cm^3.
        half_cell_curves : Union[List[pd.DataFrame], pd.DataFrame]
            Half cell curves for the material, either as a list of pandas DataFrames or a single DataFrame.
        voltage_cutoff : float
            The voltage cutoff for the half cell curves in V. This is the maximum voltage at which the half cell curve will be calculated.
        extrapolation_window : float
            The negative voltage extrapolation window in V. This is the amount of voltage below the minimum voltage of the half cell curves that will be used for extrapolation.
            This is useful for cathode materials where the voltage can go below 0V, e.g., for Li-ion batteries.
        color : str
            Color of the material, used for plotting.
        reversible_capacity_scaling : float
            Scaling factor for the reversible capacity of the material. Default is 1.0 (no scaling).
        irreversible_capacity_scaling : float
            Scaling factor for the irreversible capacity of the material. Default is 1.0 (no scaling).
        """
        super().__init__(
            name = name,
            reference = reference,
            specific_cost = specific_cost,
            density = density,
            half_cell_curves = half_cell_curves,
            color = color,
            extrapolation_window= extrapolation_window,
            voltage_cutoff = voltage_cutoff,
            reversible_capacity_scaling = reversible_capacity_scaling,
            irreversible_capacity_scaling = irreversible_capacity_scaling
        )

    @staticmethod
    def from_database(name) -> 'CathodeMaterial':
        """
        Pull object from the database.
        
        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values('cathode_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_cathode_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material

    @property
    def minimum_extrapolated_voltage(self) -> float:
        """
        Get the minimum extrapolated voltage for the half cell curves.
        
        :return: float: minimum extrapolated voltage of the half cell curves
        """
        return float(round(self._minimum_extrapolated_voltage, 2))


class AnodeMaterial(_ActiveMaterial):

    def __init__(
            self, 
            name: str,
            reference: str,
            specific_cost: float,
            density: float,
            half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
            color: str = '#2c2c2c',
            extrapolation_window: float = 0.05,
            voltage_cutoff: float = None,
            reversible_capacity_scaling: float = 1.0,
            irreversible_capacity_scaling: float = 1.0
        ):
        """
        Initialize an object that represents an anode material.
        
        Parameters
        ----------
        name : str
            Name of the material.
        reference : str
            Reference electrode for the material, e.g., 'Li/Li+'.
        specific_cost : float
            Specific cost of the material in $/kg.
        density : float
            Density of the material in g/cm^3.
        half_cell_curves : Union[List[pd.DataFrame], pd.DataFrame]
            Half cell curves for the material, either as a list of pandas DataFrames or a single DataFrame.
        color : str
            Color of the material, used for plotting.
        voltage_cutoff : float
            The voltage cutoff for the half cell curves in V. This is the minimum voltage at which the half cell curve will be calculated.
        extrapolation_window : float
            The positive voltage extrapolation window in V. This is the amount of voltage above the maximum voltage of the half cell curves that will be used for extrapolation.
            This is useful for anode materials where the voltage can go above 0V, e.g., for Li-ion batteries.
        reversible_capacity_scaling : float
            Scaling factor for the reversible capacity of the material. Default is 1.0 (no scaling).
        irreversible_capacity_scaling : float
            Scaling factor for the irreversible capacity of the material. Default is 1.0 (no scaling).
        """
        super().__init__(
            name = name,
            reference = reference,
            specific_cost = specific_cost,
            density = density,
            half_cell_curves = half_cell_curves,
            color = color,
            voltage_cutoff = voltage_cutoff,
            extrapolation_window = extrapolation_window,
            reversible_capacity_scaling = reversible_capacity_scaling,
            irreversible_capacity_scaling = irreversible_capacity_scaling
        )

    @staticmethod
    def from_database(name) -> 'AnodeMaterial':
        """
        Pull object from the database.
        
        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values('anode_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_anode_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material


class Binder(_Material):

    def __init__(
            self, 
            name: str,
            specific_cost: float, 
            density: float,
            color: str = '#2c2c2c'
        ):
        """
        Initialize an object that represents a binder.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.7)
        """
        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost,
            color=color
        )

    @staticmethod
    def from_database(name) -> 'Binder':
        """
        Pull object from the database.
        
        :param name: str: Name of the binder material.
        :return: Binder: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values('binder_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_binder_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material


class ConductiveAdditive(_Material):

    def __init__(
            self, 
            name: str,
            specific_cost: float,
            density: float,
            color: str = '#2c2c2c'
        ):

        super().__init__(
                name=name, 
                density=density, 
                specific_cost=specific_cost,
                color=color
            )

    @staticmethod
    def from_database(name) -> 'ConductiveAdditive':
        """
        Pull object from the database.
        
        :param name: str: Name of the conductive additive material.
        :return: ConductiveAdditive: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values('conductive_additive_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_conductive_additive_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))

        return material

