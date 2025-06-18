from SteerEnergyStorage.DataManager import DataManager
from SteerEnergyStorage.Materials.RawMaterials import RawMaterial
from SteerEnergyStorage.Constants import *

import pandas as pd
import numpy as np
import plotly.express as px
from pickle import dumps, loads
from pathlib import Path
from typing import List, Union, Optional
from copy import deepcopy


class _ActiveMaterial(RawMaterial):

    def __init__(
            self, 
            name: str,
            reference: str,
            specific_cost: float, 
            density: float,
            half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
            negative_voltage_extrapolation_window: float = 0.4,
            color: str = '#2c2c2c',
        ) -> None:
        """
        Initialize an object that represents an active material.
        
        Args:
            name (str): Name of the material.
            reference (str): Reference electrode for the material, e.g., 'Li/Li+'
            specific_cost (float): Specific cost of the material per kg.
            density (float): Density of the material in g/cm^3.
            irreversible_capacity_scaling (float): Scaling factor for irreversible capacity (default: 1.0).
            reversible_capacity_scaling (float): Scaling factor for reversible capacity (default: 1.0).
            half_cell_curves (Optional[Union[Dict[pd.DataFrame], pd.DataFrame]]): Half cell curves data. Dataframes should 
            contain columns 'specific_capacity' in (mAh/g), 'voltage' in (V), and 'direction' (discharge or charge). Multiple curves
            can be passed as a list of dataframes. This is useful for providing electrochemical data over a range of maximum voltages. 
            negative_voltage_extrapolation_window (float): How far below the maximum votlage of the charge curve can we go for our data to be valid.

        Returns:
            None

        """
        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color
        )

        self._check_reference(reference)
        self._check_half_cell_curves(half_cell_curves)
        self._check_negative_voltage_extrapolation_window(negative_voltage_extrapolation_window)
        self._process_half_cell_curves()
        self._calculate_half_cell_curves_properties()

        self._reversible_capacity_scaling = 1.0
        self._irreversible_capacity_scaling = 1.0

    def _process_half_cell_curves(self) -> None:
        pass

    def _check_negative_voltage_extrapolation_window(self, negative_voltage_extrapolation_window: float):
        """
        Check if the negative voltage interpolation window is a valid float.
        """
        if not isinstance(negative_voltage_extrapolation_window, (float, int)) or negative_voltage_extrapolation_window <= 0:
            raise ValueError("Negative voltage interpolation window must be a positive float")
        
        self._negative_voltage_extrapolation_window = float(negative_voltage_extrapolation_window)

    def _check_reference(self, reference: str):
        """
        Check if the reference electrode is valid.
        """
        if reference not in ALLOWED_REFERENCE:
            raise ValueError(f"Reference electrode must be one of {ALLOWED_REFERENCE}")
        
        self._reference = reference

    def _check_half_cell_curves(self, half_cell_curves: Optional[Union[List[pd.DataFrame], pd.DataFrame]]):
        """
        Check if the half cell curves are valid.
        """
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

        self._half_cell_curves = half_cell_curves

    def _process_half_cell_curves(self) -> None:
        """
        Function to process the half cell curves. It will calculate the voltage and specific capacity maximums and then reflect and shift the curves if
        the specific capacity at the minimum voltage is greater than the specific capacity at the maximum voltage. It will store these processed curves
        in the `_half_cell_curves` attribute. This contains all the experimental input data for the half cell curves. 
        """
        new_half_cells_curves = []

        for id, curve in self._half_cell_curves.groupby('id', as_index=False):

            # calculate the maximum voltage and specific capacity for the curve
            curve = (
                curve
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * (mA_TO_A * H_TO_S / G_TO_KG),
                    voltage_max = lambda x: x['voltage'].max(),
                    specific_capacity_max = lambda x: x['specific_capacity'].max(),
                )
            )

            if type(self) == AnodeMaterial:
                # if the material is an anode, we need to reflect the curve directions
                curve = (
                    curve
                    .replace(
                        {'direction': {'discharge': 'charge', 'charge': 'discharge'}}
                    )
                ) 

            curve = (
                curve
                .sort_values(
                    ['direction', 'specific_capacity'],
                )
            )
            
            for dir, dir_curve in curve.groupby('direction', as_index=False):

                # check if the capacity is increasing or decreasing.  Get the capacity at the minimum votlage
                specific_capacity_at_minimum_voltage = (
                    dir_curve
                    .query('voltage == voltage.min()')
                    ['specific_capacity']
                    .values[0]
                )

                # get the capacity at the maximum votlage
                specific_capacity_at_maximum_voltage = (
                    dir_curve
                    .query('voltage == voltage.max()')
                    ['specific_capacity']
                    .values[0]
                )

                # if the specific capacity at the minimum voltage is greater than the specific capacity at the maximum voltage, we need to reflect and shift the curve
                if (specific_capacity_at_minimum_voltage > specific_capacity_at_maximum_voltage and type(self) == CathodeMaterial) or \
                    (specific_capacity_at_minimum_voltage < specific_capacity_at_maximum_voltage and type(self) == AnodeMaterial):

                    dir_curve = (
                        dir_curve
                        .assign(specific_capacity = lambda x: -x['specific_capacity'])
                    )

                    capacity_max = dir_curve['specific_capacity'].max()

                    dir_curve = (
                        dir_curve
                        .assign(specific_capacity = lambda x: x['specific_capacity'] - capacity_max + x['specific_capacity_max'])
                    )

                # Order the curve by specific capacity
                if dir == 'discharge':
                    dir_curve = dir_curve.sort_values('specific_capacity', ascending=False)
                elif dir == 'charge':
                    dir_curve = dir_curve.sort_values('specific_capacity', ascending=True)
                else:
                    raise ValueError("Unknown material type. Cannot sort half cell curves.")

                # add the manipulated curve to the list of new half cell curves
                new_half_cells_curves.append(dir_curve)

        # concatenate all the curves together and store as attribute
        self._half_cell_curves = pd.concat(
            new_half_cells_curves, 
            ignore_index=True
        )

    def _calculate_half_cell_curves_properties(self) -> None:

        # calculate the maximum voltage range for the half cell curves 
        self._maximum_voltage = round(
            self._half_cell_curves['voltage_max'].max(), 
            4
        )

        # calculate the minimum voltage range for interpolation of the curves
        self._minimum_voltage = round(
            self._half_cell_curves['voltage_max'].min(), 
            4
        )
        
        # calculate the minimum voltage range for extrapolation of the curves
        self._minimum_extrapolated_voltage = self._minimum_voltage - self._negative_voltage_extrapolation_window

    def _check_irreversible_capacity_scaling(self, scaling: float):
        """
        Check if the irreversible capacity scaling is a valid float.
        """
        if not isinstance(scaling, (float, int)) or scaling <= 0:
            raise ValueError("Irreversible capacity scaling must be a positive float")
        
        self._irreversible_capacity_scaling = float(scaling)
    
    def _check_reversible_capacity_scaling(self, scaling: float):
        """
        Check if the reversible capacity scaling is a valid float.
        """
        if not isinstance(scaling, (float, int)) or scaling <= 0:
            raise ValueError("Reversible capacity scaling must be a positive float")
        
        self._reversible_capacity_scaling = float(scaling)

    def _apply_reversible_capacity_scaling(self, scaling: float):

        data = (self
                ._half_cell_curve
                .groupby(
                    ['direction'], as_index=False
                ).apply(
                    lambda df: df.assign(
                        specific_capacity = df['specific_capacity'] * scaling + ((1 - scaling) * df['specific_capacity_max']) \
                            if df['direction'].iloc[0] == 'discharge' else df['specific_capacity']
                        )
                ).reset_index(
                    drop=True
                )
                )
        
        self._half_cell_curve = data

    def _apply_irreversible_capacity_scaling(self, scaling: float):

        data = (self
                ._half_cell_curve
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * scaling,
                    specific_capacity_max = lambda x: x['specific_capacity_max'] * scaling,
                )
                )
        
        self._half_cell_curve = data

    def _truncate_and_shift_curves(self, input_value: float) -> None:
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
            .query('voltage_max == voltage_max.min()')
        )

        # Split charge and discharge curves
        charge = data[data['direction'] == 'charge'].copy()
        discharge = data[data['direction'] == 'discharge'].copy()

        # Interpolate corresponding voltage on discharge curve
        charge_interp_value = np.interp(input_value, charge['voltage'], charge['specific_capacity'])

        # add the interpolated values to the curves
        charge = pd.concat([charge, pd.DataFrame({
            'specific_capacity': [charge_interp_value],
            'voltage': [input_value],
            'direction': ['charge'],
            'voltage_max': [input_value],
            'specific_capacity_max': [charge_interp_value]
        })], ignore_index=True)

        # Truncate curves to only include values below or equal to the voltage
        charge_trunc = charge[charge['voltage'] <= input_value].copy()
        discharge_trunc = discharge[discharge['voltage'] <= input_value].copy()

        # Calculate shift to make discharge curve continuous with charge curve
        # We assume continuity is needed in specific_capacity
        capacity_shift = charge_trunc['specific_capacity'].iloc[-1] - discharge_trunc['specific_capacity'].iloc[-1]
        discharge_trunc['specific_capacity'] += capacity_shift

        ref_charge = charge_trunc.loc[charge_trunc['voltage'].idxmax()]
        ref_discharge = discharge_trunc.loc[discharge_trunc['voltage'].idxmax()]

        capacity_shift = ref_charge['specific_capacity'] - ref_discharge['specific_capacity']
        discharge_trunc['specific_capacity'] += capacity_shift

        self._half_cell_curve = pd.concat([
            charge_trunc, discharge_trunc], 
            ignore_index=True
        )

    def _get_half_cell_interpolated_on_max_voltage(self, input_value: float) -> None:
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
            .query('voltage_max <= @input_value')
            .query('voltage_max == voltage_max.max()')
        )

        # Split the closest below curve into charge and discharge curves
        closest_below_curve_charge = closest_below_curve.query('direction == "charge"').sort_values('specific_capacity')
        closest_below_curve_discharge = closest_below_curve.query('direction == "discharge"').sort_values('specific_capacity')

        # Get the closest curves above the input value
        closest_above_curve = (
            self
            ._half_cell_curves
            .query('voltage_max >= @input_value')
            .query('voltage_max == voltage_max.min()')
        )

        # Split the closest above curve into charge and discharge curves
        closest_above_curve_charge = closest_above_curve.query('direction == "charge"').sort_values('specific_capacity')
        closest_above_curve_discharge = closest_above_curve.query('direction == "discharge"').sort_values('specific_capacity')

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
        self._half_cell_curve = pd.concat([charge_curve, discharge_curve], ignore_index=True)
        
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
        v_low_max = below_curve['voltage_max'].values[0]
        v_high_max = above_curve['voltage_max'].values[0]
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
            'voltage_max': [input_value] * n_points,
            'specific_capacity_max': [max(c_values)] * n_points
        })

        return interpolated_curve

    def plot_curves(self, **kwargs):

        data = self.half_cell_curves.copy()

        fig = px.line(
            data,
            x='Specific Capacity (mAh/g)',
            y='Voltage (V)',
            color='Maximum Voltage (V)',
            markers=True
        )

        fig.update_layout(
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )

        return fig

    def plot_half_cell_curve(self, **kwargs):

        data = self.half_cell_curve.copy()

        fig = px.line(
            data,
            x='Specific Capacity (mAh/g)',
            y='Voltage (V)',
            markers=True
        )

        fig.update_layout(
            paper_bgcolor=kwargs.get('paper_bgcolor', 'white'),
            plot_bgcolor=kwargs.get('plot_bgcolor', 'white'),
            **kwargs
        )
        
        return fig

    def pickle(self):
        """
        Serializes the object to a byte stream.
        
        :return: bytes: Serialized byte stream of the object.
        """
        return dumps(self)

    @property
    def reference(self) -> str:
        """
        Get the reference electrode for the material.
        
        :return: str: Reference electrode for the material, e.g., 'Li/Li+'
        """
        return self._reference

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def specific_cost(self) -> float:
        return self._specific_cost
    
    @property
    def half_cell_curve(self) -> pd.DataFrame:

        if not hasattr(self, '_half_cell_curve'):
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cuttoff or a maximum specific capacity before accessing this property.")

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
            raise ValueError(f"A half cell curve for {self.name} has not been calculated yet. Please set a voltage cuttoff or a maximum specific capacity before accessing this property.")

        data = (self
                ._half_cell_curves
                .assign(
                    specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    specific_capacity_max = lambda x: x['specific_capacity_max'] * (S_TO_H * A_TO_mA / KG_TO_G),
                    voltage_max = lambda x: x['voltage_max'].round(2),
                ).filter(
                    items=['specific_capacity', 'voltage', 'direction', 'voltage_max', 'specific_capacity_max']
                )
                .rename(
                    columns={
                        'specific_capacity': 'Specific Capacity (mAh/g)', 
                        'voltage': 'Voltage (V)', 
                        'direction': 'Direction',
                        'voltage_max': 'Maximum Voltage (V)',
                        'specific_capacity_max': 'Maximum Specific Capacity (mAh/g)'
                        }
                        )
                )
        
        return data

    @property
    def irreversible_capacity_scaling(self) -> float:
        return self._irreversible_capacity_scaling

    @irreversible_capacity_scaling.setter
    def irreversible_capacity_scaling(self, scaling: float):
        """
        Set the irreversible capacity scaling factor.
        
        :param scaling: float: scaling factor for irreversible capacity
        """
        self._apply_irreversible_capacity_scaling(1/self._irreversible_capacity_scaling)
        self._check_irreversible_capacity_scaling(scaling)
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
        self._apply_reversible_capacity_scaling(1/self._reversible_capacity_scaling)
        self._check_reversible_capacity_scaling(scaling)
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
            negative_voltage_extrapolation_window: float = 0.4,
            color: str = '#2c2c2c'
        ):
        """
        Initialize an object that represents a cathode material.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 4.0)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        super().__init__(
            name = name,
            reference = reference,
            specific_cost = specific_cost,
            density = density,
            half_cell_curves = half_cell_curves,
            negative_voltage_extrapolation_window = negative_voltage_extrapolation_window,
            color = color
        )

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
    def voltage_cuttoff_range(self) -> tuple:
        """
        Get the valid voltage range for the half cell curves.
        
        :return: tuple: (minimum voltage, maximum voltage)
        """
        min_v = float(round(self._minimum_extrapolated_voltage, 2))
        max_v = float(round(self._maximum_voltage, 2))
        return (min_v, max_v)

    @property
    def voltage_cuttoff(self) -> float:
        """
        Get the maximum voltage of the half cell curves.
        
        :return: float: maximum voltage of the half cell curves
        """
        return round(float(self.half_cell_curves['Maximum Voltage (V)'].max()), 3)

    @voltage_cuttoff.setter
    def voltage_cuttoff(self, voltage: float):
        """
        Set the voltage cuttoff for the half cell curves.
        
        :param voltage: float: maximum voltage of the half cell curves
        """
        if not isinstance(voltage, (float, int)) or voltage <= 0:
            raise ValueError("Voltage cuttoff must be a positive float")
        
        if voltage < self._minimum_extrapolated_voltage:
            raise ValueError(f"Voltage cuttoff must be greater than or equal to {self._minimum_extrapolated_voltage} V")
        elif voltage < self._minimum_voltage:
            self._truncate_and_shift_curves(voltage)
        elif voltage < self._maximum_voltage:
            self._get_half_cell_interpolated_on_max_voltage(voltage)
        else:
            raise ValueError(f"Voltage cuttoff must be less than or equal to {self._maximum_voltage} V")

        self._apply_reversible_capacity_scaling(self._reversible_capacity_scaling)
        self._apply_irreversible_capacity_scaling(self._irreversible_capacity_scaling)


class AnodeMaterial(_ActiveMaterial):

    def __init__(
            self, 
            name: str,
            reference: str,
            specific_cost: float,
            density: float,
            half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
            negative_voltage_extrapolation_window: float = 0.4,
            color: str = '#2c2c2c'
        ):
        """
        Initialize an object that represents an anode material.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.5)
        :param irreversible_capacity_scaling: float: scaling factor for irreversible capacity (default: 1.0)
        :param reversible_capacity_scaling: float: scaling factor for reversible capacity (default: 1.0)
        :param half_cell_path: str: path to the half cell data
        """
        super().__init__(
            name = name,
            reference = reference,
            specific_cost = specific_cost,
            density = density,
            half_cell_curves = half_cell_curves,
            negative_voltage_extrapolation_window = negative_voltage_extrapolation_window,
            color = color
        )

        self._half_cell_curve = self._half_cell_curves.copy().query('specific_capacity_max == specific_capacity_max.max()')

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







class Binder:

    def __init__(
            self, 
            specific_cost: float, 
            density: float,
            name: str = 'Binder'
        ):
        """
        Initialize an object that represents a binder.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.7)
        """
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3

    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def specific_cost(self) -> float:
        return self._specific_cost
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        if self.name is not None:
            return self.name
        else:
            return "binder"
        
    def __repr__(self) -> str:
        return self.__str__()
    
    
class ConductiveAdditive:

    def __init__(
            self, 
            specific_cost: float, 
            density: float,
            name: str = 'Conductive Additive'
        ):
        """
        Initialize an object that represents a conductive additive.
        
        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3
        """
        self._name = name
        self._specific_cost = specific_cost
        self._density = density * G_TO_KG / CM_TO_M**3

    @property
    def specific_cost(self) -> float:
        return self._specific_cost

    @property
    def density(self) -> float:
        density = self._density * KG_TO_G / M_TO_CM**3
        return round(density, 2)
    
    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        if self._name is not None:
            return self.name
        else:
            return "conductive additive"
        
    def __repr__(self) -> str:
        return self.__str__()


