from SteerEnergyStorage.DataManager import DataManager
from SteerEnergyStorage.Materials.RawMaterials import _RawMaterial
from SteerEnergyStorage.Constants import *

import pandas as pd
import numpy as np
import plotly.express as px
from pickle import dumps, loads
from pathlib import Path
from typing import List, Union, Optional
from copy import deepcopy


class _ActiveMaterial(_RawMaterial):

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

        self.reference = reference
        self.extrapolation_window = extrapolation_window
        self.half_cell_curves = half_cell_curves
        self.voltage_cutoff = voltage_cutoff
        self.reversible_capacity_scaling = reversible_capacity_scaling
        self.irreversible_capacity_scaling = irreversible_capacity_scaling

    def _process_half_cell_curves(
            self, 
            half_cell_curves: pd.DataFrame
        ) -> pd.DataFrame:
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

        for id, curve in half_cell_curves.groupby(['id'], as_index=False):

            charge_curve = curve.query('direction == "charge"')
            discharge_curve = curve.query('direction == "discharge"')

            # check the specific capacity ranges of the curves and make sure the charge curve has the greater range
            charge_specific_cap_range = charge_curve['specific_capacity'].max() - charge_curve['specific_capacity'].min()
            discharge_specific_cap_range = discharge_curve['specific_capacity'].max() - discharge_curve['specific_capacity'].min()
            if discharge_specific_cap_range > charge_specific_cap_range:
                charge_curve, discharge_curve = discharge_curve.assign(direction='charge'), charge_curve.assign(direction='discharge')

            # reverse and shift the discharge curve if the maximum specific capacity is less than the minimum specific capacity
            max_spec_cap = curve['specific_capacity'].max()
            discharge_curve = (
                discharge_curve
                .assign(
                    specific_capacity = lambda x: -x['specific_capacity'] + max_spec_cap,
                )
            )

            # sort curves
            charge_curve = charge_curve.sort_values('specific_capacity', ascending=True).reset_index(drop=True)
            discharge_curve = discharge_curve.sort_values('specific_capacity', ascending=False).reset_index(drop=True)  

            # get last charge point and add to discharge curve
            discharge_curve = pd.concat(
                [
                    charge_curve.iloc[[-1]].assign(direction='discharge'),
                    discharge_curve
                ],
                ignore_index=True
            )

            # calculate the voltage at maximum capacity
            curve = (
                pd.concat(
                    [charge_curve, discharge_curve],
                    ignore_index=True
                ).assign(
                    specific_capacity = lambda x: x['specific_capacity'] * (mA_TO_A * H_TO_S / G_TO_KG),
                    specific_capacity_max = lambda x: x['specific_capacity'].max(),
                    voltage_at_max_capacity = lambda x: x.loc[x['specific_capacity'].idxmax(), 'voltage'],
                    voltage_at_min_capacity = lambda x: x.loc[x['specific_capacity'].idxmin(), 'voltage']
                )
            )

            # add the manipulated curve to the list of new half cell curves
            new_half_cells_curves.append(curve)

        # concatenate all the curves together and store as attribute
        return pd.concat(
            new_half_cells_curves, 
            ignore_index=True
        )

    def _apply_reversible_capacity_scaling(self, scaling: float):

        data = self._half_cell_curve.copy()
        charge = data[data['direction'] == 'charge']
        discharge = data[data['direction'] == 'discharge']
        max_specific_capacity = data['specific_capacity'].max()

        discharge.loc[:, 'specific_capacity'] = (
            scaling * (discharge['specific_capacity'] - max_specific_capacity) + max_specific_capacity
        )

        self._half_cell_curve = pd.concat([
            charge,
            discharge
        ], ignore_index=True)

    def _apply_irreversible_capacity_scaling(self, scaling: float):

        data = (self
                ._half_cell_curve
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * scaling,
                    specific_capacity_max = lambda x: x['specific_capacity_max'] * scaling,
                )
                )
        
        self._half_cell_curve = data
        
    def _calculate_half_cell_curves_properties(self):
        pass

    def _interpolate_curve_on_maximum_voltage(
            self, 
            input_value: float,
            below_curve: pd.DataFrame,
            above_curve: pd.DataFrame
        ) -> pd.DataFrame:
        """
        Interpolate between two curves at a target max voltage.

        Parameters
        ----------
        input_value : float
            The target maximum voltage to interpolate between curves.
        below_curve : pd.DataFrame
            The curve with the maximum voltage below the target.
        above_curve : pd.DataFrame
            The curve with the maximum voltage above the target.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the interpolated curve at the target maximum voltage.
        """
        n_points = 100

        # Create grid for below curve
        sc_grid_low = np.linspace(
            below_curve['specific_capacity'].min(),
            below_curve['specific_capacity'].max(),
            n_points
        )

        # Create grid for above curve
        sc_grid_high = np.linspace(
            above_curve['specific_capacity'].min(),
            above_curve['specific_capacity'].max(),
            n_points
        )

        # Interpolate onto 100 points between the maximum and minimum specific capacity of the below curve
        v_low_interp = np.interp(
            sc_grid_low,
            below_curve['specific_capacity'],
            below_curve['voltage']
        )

        # Interpolate voltage for the common specific_capacity range for the high curve
        v_high_interp = np.interp(
            sc_grid_high,
            above_curve['specific_capacity'],
            above_curve['voltage']
        )

        # Calculate weights for the interpolation
        v_low_max = below_curve['voltage_at_max_capacity'].values[0]
        v_high_max = above_curve['voltage_at_max_capacity'].values[0]
        weight_low = (v_high_max - input_value) / (v_high_max - v_low_max)
        weight_high = (input_value - v_low_max) / (v_high_max - v_low_max)

        # Interpolate the values
        c_values = [cl * weight_low + ch * weight_high for cl, ch in zip(sc_grid_low, sc_grid_high)]
        v_interp = [vl * weight_low + vh * weight_high for vl, vh in zip(v_low_interp, v_high_interp)]

        # Create a new DataFrame for the interpolated curve
        interpolated_curve = pd.DataFrame({
            'specific_capacity': c_values,
            'voltage': v_interp,
            'direction': below_curve['direction'].values[0],
            'voltage_at_max_capacity': [input_value] * n_points,
            'specific_capacity_max': [max(c_values)] * n_points
        })

        return interpolated_curve

    def _get_half_cell_interpolated_on_max_voltage(self, input_value: float) -> pd.DataFrame:
        """
        Get the half cell curves interpolated on a maximum voltage.

        Parameters
        ----------
        input_value : float
            The maximum voltage to interpolate the half cell curves on.
        """

        # Get the closest curves below the input value 
        closest_below_curve = (
            self
            ._half_cell_curves
            .query('voltage_at_max_capacity <= @input_value')
            .query('voltage_at_max_capacity == voltage_at_max_capacity.max()')
        )

        # Split the closest below curve into charge and discharge curves
        closest_below_curve_charge = (
            closest_below_curve
            .query('direction == "charge"')
            .sort_values('specific_capacity')
        )

        closest_below_curve_discharge = (
            closest_below_curve
            .query('direction == "discharge"')
            .sort_values('specific_capacity')
        )

        # Get the closest curves above the input value
        closest_above_curve = (
            self
            ._half_cell_curves
            .query('voltage_at_max_capacity >= @input_value')
            .query('voltage_at_max_capacity == voltage_at_max_capacity.min()')
        )

        # Split the closest above curve into charge and discharge curves
        closest_above_curve_charge = (
            closest_above_curve
            .query('direction == "charge"')
            .sort_values('specific_capacity')
        )

        closest_above_curve_discharge = (
            closest_above_curve
            .query('direction == "discharge"')
            .sort_values('specific_capacity')
        )

        # Get the interpolated charge curve
        charge_curve = self._interpolate_curve_on_maximum_voltage(
            input_value,
            closest_below_curve_charge,
            closest_above_curve_charge
        )

        # Get the interpolated discharge curve
        discharge_curve = (
            self
            ._interpolate_curve_on_maximum_voltage(
                input_value,
                closest_below_curve_discharge,
                closest_above_curve_discharge
            ).sort_values(
                'specific_capacity',
                ascending=False
            )
        )

        # Concatenate the charge and discharge curves
        return pd.concat([charge_curve, discharge_curve], ignore_index=True)

    def _truncate_and_shift_curves(self, input_value: float) -> pd.DataFrame:
        """
        Truncate charge/discharge curves based on a voltage or specific_capacity input and shift the discharge curve
        to maintain continuity with the charge curve.

        Parameters
        ----------
        input_value : float
            The voltage or specific_capacity value to truncate the curve at.

        Raises
        ------
        ValueError
            If `input_value` is not within the range of the charge curve along the specified axis.
        """

        # Get the data with the minimum voltage limit
        data = (
            self
            ._half_cell_curves
            .copy()
            .query('voltage_at_max_capacity == voltage_at_max_capacity.min()')
        )

        data = self.enforce_monotonicity(data, on='voltage')
        data = self.enforce_monotonicity(data, on='specific_capacity')

        # Split charge and discharge curves
        charge = data[data['direction'] == 'charge'].copy().reset_index(drop=True)
        discharge = data[data['direction'] == 'discharge'].copy().reset_index(drop=True)

        # Interpolate corresponding voltage on charge curve
        charge_capacity_interp_value = np.interp(
            input_value, 
            charge.sort_values(['voltage'])['voltage'], 
            charge.sort_values(['voltage'])['specific_capacity']
        )

        # Interpolate corresponding voltage on discharge curve
        discharge_capacity_interp_value = np.interp(
            input_value,
            discharge.sort_values(['voltage'])['voltage'],
            discharge.sort_values(['voltage'])['specific_capacity']
        )

        # Create a new row for the interpolated charge curve
        new_charge_row = charge.iloc[0].copy()
        new_charge_row['specific_capacity'] = charge_capacity_interp_value
        new_charge_row['voltage'] = input_value

        # Create a new row for the discharge curve
        new_discharge_row = discharge.iloc[0].copy()
        new_discharge_row['specific_capacity'] = discharge_capacity_interp_value
        new_discharge_row['voltage'] = input_value

        # Add the new rows to the charge and discharge curves
        charge = pd.concat([charge, new_charge_row.to_frame().T], ignore_index=True)
        discharge = pd.concat([new_discharge_row.to_frame().T, discharge], ignore_index=True)

        # Truncate curves to only include values below or equal to the voltage
        if type(self) == CathodeMaterial:
            charge = charge[charge['voltage'] <= input_value].copy()
            discharge = discharge[discharge['voltage'] <= input_value].copy()
        elif type(self) == AnodeMaterial:
            charge = charge[charge['voltage'] >= input_value].copy()
            discharge = discharge[discharge['voltage'] >= input_value].copy()

        # Calculate shift to make discharge curve continuous with charge curve
        # We assume continuity is needed in specific_capacity
        capacity_shift = charge[charge['voltage'] == input_value]['specific_capacity'].values[0] - discharge[discharge['voltage'] == input_value]['specific_capacity'].values[0]

        discharge['specific_capacity'] = discharge['specific_capacity'] + capacity_shift

        return pd.concat([
            charge, 
            discharge], 
            ignore_index=True
        )

    def _calculate_half_cell_curve(
            self, 
            extrapolate_bool: bool, 
            voltage_cutoff: float
        ) -> pd.DataFrame:
        """
        Calculate the half cell curve based on the voltage cutoff and whether to extrapolate or truncate the curves.

        Parameters
        ----------
        extrapolate_bool : bool
            Whether to extrapolate the curves based on the voltage cutoff.
        voltage_cutoff : float
            The voltage cutoff for the half cell curves in V. This is the maximum voltage (for CathodeMaterial) or minimum voltage (for AnodeMaterial)
            at which the half cell curve will be calculated.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame containing the half cell curve with columns 'specific_capacity', 'voltage', and 'direction'.
        """
        if extrapolate_bool:
            half_cell_curve = self._truncate_and_shift_curves(voltage_cutoff)
        else: 
            half_cell_curve = self._get_half_cell_interpolated_on_max_voltage(voltage_cutoff)

        return half_cell_curve

    @staticmethod
    def enforce_monotonicity(df: pd.DataFrame, on: str) -> pd.DataFrame:
        """
        Ensure that the voltage values in the DataFrame are monotonic.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing 'voltage' column.
        on : str
            The column name to enforce monotonicity on, either 'voltage' or 'specific_capacity'.
        """
        df = df.copy()

        df_charge = df.query('direction == "charge"')
        df_discharge = df.query('direction == "discharge"')

        trend_charge = df_charge[on].iloc[-1] - df_charge[on].iloc[0]
        trend_discharge = df_discharge[on].iloc[-1] - df_discharge[on].iloc[0]

        df_charge.loc[:, on] = np.maximum.accumulate(df_charge[on]) if trend_charge > 0 else np.minimum.accumulate(df_charge[on])
        df_discharge.loc[:, on] = np.minimum.accumulate(df_discharge[on]) if trend_discharge < 0 else np.maximum.accumulate(df_discharge[on])

        return pd.concat([df_charge, df_discharge], ignore_index=True)

    def plot_curves(self, **kwargs):

        data = self.half_cell_curves.copy()

        fig = px.line(
            data,
            x='Specific Capacity (mAh/g)',
            y='Voltage (V)',
            color='Voltage at Maximum Capacity (V)'
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
            y='Voltage (V)'
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
        if voltage is None:

            self._half_cell_curve = (
                self
                ._half_cell_curves
                .query('specific_capacity_max == specific_capacity_max.max()')
            )

            self._voltage_cuttoff = (
                self
                ._half_cell_curves
                ['voltage_at_max_capacity']
                .iloc[0]
            )

        else:

            if not isinstance(voltage, (float, int)):
                raise ValueError("Voltage cutoff must be a float")

            extrapolate_bool = self._check_cutoff_voltage_in_range(voltage)

            self._half_cell_curve = self._calculate_half_cell_curve(
                extrapolate_bool = extrapolate_bool, 
                voltage_cutoff = voltage
            )

            self._voltage_cutoff = voltage

            if hasattr(self, '_irreversible_capacity_scaling'):
                self._apply_irreversible_capacity_scaling(self._irreversible_capacity_scaling)
            
            if hasattr(self, '_reversible_capacity_scaling'):
                self._apply_reversible_capacity_scaling(self._reversible_capacity_scaling)

    def _check_cutoff_voltage_in_range(self, voltage: float) -> bool:
        pass

    @property
    def voltage_cutoff_range(self) -> tuple:
        """
        Get the valid voltage range for the half cell curves.
        
        :return: tuple: (minimum voltage, maximum voltage)
        """
        return (round(float(self._voltage_cutoff_range[0]), 2), round(float(self._voltage_cutoff_range[1]), 2))

    @property
    def extrapolation_window(self) -> float:
        """
        Get the extrapolation window for the half cell curves.
        
        :return: float: Extrapolation window in V.
        """
        return self._extrapolation_window
    
    @extrapolation_window.setter
    def extrapolation_window(self, window: float):

        if type(window) not in [float, int] or window < 0:
            raise ValueError("Extrapolation window must be a positive float")
        
        self._extrapolation_window = abs(float(window))
        self._calculate_half_cell_curves_properties()

    @property
    def reference(self) -> str:
        """
        Get the reference electrode for the material.
        
        :return: str: Reference electrode for the material, e.g., 'Li/Li+'
        """
        return self._reference

    @reference.setter
    def reference(self, reference: str):

        if reference not in ALLOWED_REFERENCE:
            raise ValueError(f"Reference electrode must be one of {ALLOWED_REFERENCE}")
        
        self._reference = reference

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        if not hasattr(self, '_half_cell_curve'):
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cutoff or a maximum specific capacity before accessing this property.")

        data = (self
                ._half_cell_curve
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    specific_capacity_max = lambda x: x['specific_capacity_max'] * (S_TO_H * A_TO_mA / KG_TO_G),
                ).filter(
                    items=['specific_capacity', 'voltage', 'direction']
                )
                .rename(
                    columns={
                        'specific_capacity': 'Specific Capacity (mAh/g)', 
                        'voltage': 'Voltage (V)', 
                        'direction': 'Direction',
                        }
                        )
                )
        
        return data

    @property
    def half_cell_curves(self) -> pd.DataFrame:

        if not hasattr(self, '_half_cell_curves'):
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cutoff or a maximum specific capacity before accessing this property.")

        data = (self
                ._half_cell_curves
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    specific_capacity_max = lambda x: x['specific_capacity_max'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    voltage_at_max_capacity = lambda x: x['voltage_at_max_capacity'].round(2),
                ).filter(
                    items=['specific_capacity', 'voltage', 'direction', 'voltage_at_max_capacity', 'specific_capacity_max']
                )
                .rename(
                    columns={
                        'specific_capacity': 'Specific Capacity (mAh/g)', 
                        'voltage': 'Voltage (V)', 
                        'direction': 'Direction',
                        'voltage_at_max_capacity': 'Voltage at Maximum Capacity (V)',
                        'specific_capacity_max': 'Maximum Specific Capacity (mAh/g)'
                        }
                        )
                )
        
        return data

    @half_cell_curves.setter
    def half_cell_curves(self, half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame]) -> None:
        
        if isinstance(half_cell_curves, pd.DataFrame):
            half_cell_curves = [half_cell_curves]
        
        if not isinstance(half_cell_curves, list) or not all(isinstance(curve, pd.DataFrame) for curve in half_cell_curves):
            raise ValueError("Half cell curves must be a list of pandas DataFrames or a single DataFrame")
        
        for curve in half_cell_curves:
            if not {'specific_capacity', 'voltage', 'direction'}.issubset(curve.columns):
                raise ValueError("Each half cell curve DataFrame must contain 'specific_capacity', 'voltage', and 'direction' columns")
            
        half_cell_curves = pd.concat(
            [df.assign(id = i) for i, df in enumerate(half_cell_curves)],
            ignore_index=True
        )

        self._half_cell_curves = self._process_half_cell_curves(half_cell_curves)
        self._calculate_half_cell_curves_properties()

    @property
    def irreversible_capacity_scaling(self) -> float:
        return self._irreversible_capacity_scaling

    @irreversible_capacity_scaling.setter
    def irreversible_capacity_scaling(self, scaling: float):
        """
        Set the irreversible capacity scaling factor.
        
        :param scaling: float: scaling factor for irreversible capacity
        """
        # undo previous scaling to get original curve
        if hasattr(self, '_irreversible_capacity_scaling'):
            self._apply_irreversible_capacity_scaling(1/self._irreversible_capacity_scaling)
        
        if not isinstance(scaling, (float, int)) or scaling <= 0:
            raise ValueError("Irreversible capacity scaling must be a positive float")
        
        self._irreversible_capacity_scaling = float(scaling)

        # apply the new scaling factor
        self._apply_irreversible_capacity_scaling(self._irreversible_capacity_scaling)

    @property
    def reversible_capacity_scaling(self) -> float:
        return self._reversible_capacity_scaling

    @reversible_capacity_scaling.setter
    def reversible_capacity_scaling(self, scaling: float):
        """
        Set the reversible capacity scaling factor.
        
        :param scaling: float: scaling factor for reversible capacity
        """
        # undo previous scaling to get original curve
        if hasattr(self, '_reversible_capacity_scaling'):
            self._apply_reversible_capacity_scaling(1/self._reversible_capacity_scaling)
        
        if not isinstance(scaling, (float, int)) or scaling <= 0:
            raise ValueError("Reversible capacity scaling must be a positive float")
        
        self._reversible_capacity_scaling = float(scaling)

        # apply the new scaling factor
        self._apply_reversible_capacity_scaling(self._reversible_capacity_scaling)

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

    def _calculate_half_cell_curves_properties(self) -> None:

        # calculate the maximum voltage range for the half cell curves 
        self._maximum_voltage_cutoff = self._half_cell_curves['voltage_at_max_capacity'].max()

        # calculate the minimum voltage range for interpolation of the curves
        self._minimum_voltage_cutoff = self._half_cell_curves['voltage_at_max_capacity'].min()
        
        # calculate the minimum voltage range for extrapolation of the curves
        self._minimum_extrapolated_voltage = self._minimum_voltage_cutoff - self._extrapolation_window

        # voltage cutoff range
        self._voltage_cutoff_range = (self._minimum_extrapolated_voltage, self._maximum_voltage_cutoff)

    def _check_cutoff_voltage_in_range(self, voltage: float) -> None:
        """
        Check if the voltage cutoff is within the valid range for the half cell curves.
        
        :param voltage: float: Voltage cutoff to check.
        :raises ValueError: If the voltage cutoff is outside the valid range.
        """
        if voltage > self._maximum_voltage_cutoff:
            raise ValueError(f"Voltage cutoff {voltage} V is greater than the maximum voltage of the half cell curves {self._maximum_voltage_cutoff} V. Please set a lower voltage cutoff.")
        elif voltage < self._minimum_extrapolated_voltage:
            raise ValueError(f"Voltage cutoff {voltage} V is less than the minimum extrapolated voltage of the half cell curves {self._minimum_extrapolated_voltage} V. Please set a higher voltage cutoff.")
        elif voltage < self._maximum_voltage_cutoff and voltage > self._minimum_voltage_cutoff:
            return False
        elif voltage < self._minimum_voltage_cutoff and voltage > self._minimum_extrapolated_voltage:
            return True
        
    @staticmethod
    def from_database(name) -> 'CathodeMaterial':
        """
        Pull object from the database.
        
        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
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

        self._half_cell_curve = self._half_cell_curves.copy().query('specific_capacity_max == specific_capacity_max.max()')

    def _calculate_half_cell_curves_properties(self) -> None:

        # calculate the maximum voltage range for the half cell curves 
        self._maximum_voltage_cutoff = self._half_cell_curves['voltage_at_max_capacity'].min()

        # calculate the minimum voltage range for interpolation of the curves
        self._minimum_voltage_cutoff = self._half_cell_curves['voltage_at_max_capacity'].max()
        
        # calculate the minimum voltage range for extrapolation of the curves
        self._minimum_extrapolated_voltage = self._minimum_voltage_cutoff + self._extrapolation_window

        # voltage cutoff range
        self._voltage_cutoff_range = (self._minimum_extrapolated_voltage, self._maximum_voltage_cutoff)

    def _check_cutoff_voltage_in_range(self, voltage: float) -> None:
        """
        Check if the voltage cutoff is within the valid range for the half cell curves.
        
        :param voltage: float: Voltage cutoff to check.
        :raises ValueError: If the voltage cutoff is outside the valid range.
        """
        if voltage < self._maximum_voltage_cutoff:
            raise ValueError(f"Voltage cutoff {voltage} V is less than the minimum voltage of the half cell curves {self._maximum_voltage_cutoff} V. Please set a lower voltage cutoff.")
        elif voltage > self._minimum_extrapolated_voltage:
            raise ValueError(f"Voltage cutoff {voltage} V is greater than the minimum extrapolated voltage of the half cell curves {self._minimum_extrapolated_voltage} V. Please set a higher voltage cutoff.")
        elif voltage > self._maximum_voltage_cutoff and voltage < self._minimum_voltage_cutoff:
            return False
        elif voltage > self._minimum_voltage_cutoff and voltage < self._minimum_extrapolated_voltage:
            return True

    @staticmethod
    def from_database(name) -> 'AnodeMaterial':
        """
        Pull object from the database.
        
        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('anode_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_anode_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material


class Binder(_RawMaterial):

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
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('binder_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_binder_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material


class ConductiveAdditive(_RawMaterial):

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
        database = DataManager((Path(__file__).parent / '../../Data/database.db').resolve())
        available_materials = database.get_unique_values('conductive_additive_materials', 'name')

        if name not in available_materials:
            raise ValueError(f"Material '{name}' not found in the database. Available materials: {available_materials}")
        
        data = database.get_conductive_additive_materials(most_recent=True).query(f"name == '{name}'")
        material = deepcopy(loads(data['object'].iloc[0]))
        return material

