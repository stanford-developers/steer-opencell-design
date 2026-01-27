from steer_core.Constants.Units import *
from steer_core.Mixins.Data import DataMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Plotter import PlotterMixin

from steer_materials.Base import _Material, _VolumedMaterialMixin

from steer_opencell_design.Materials.CapacityCurveUtils import CapacityCurveMixin

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly import graph_objects as go
from typing import List, Tuple, Union, Optional, Type
from copy import deepcopy


class _ActiveMaterial(
    _VolumedMaterialMixin, 
    _Material, 
    DataMixin,
    CapacityCurveMixin,
    PlotterMixin
    ):

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: Optional[str] = "#2c2c2c",
        voltage_cutoff: Optional[float] = None,
        extrapolation_window: Optional[float] = 0.4,
        reversible_capacity_scaling: Optional[float] = 1.0,
        irreversible_capacity_scaling: Optional[float] = 1.0,
        *,
        volume=None,
        mass=None,
        **kwargs,
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
        specific_capacity_curves : Union[List[pd.DataFrame], pd.DataFrame]
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
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )

        self._update_properties = False

        self.reference = reference
        self.extrapolation_window = extrapolation_window
        self.specific_capacity_curves = specific_capacity_curves
        self.voltage_cutoff = voltage_cutoff
        self.reversible_capacity_scaling = reversible_capacity_scaling
        self.irreversible_capacity_scaling = irreversible_capacity_scaling

        self._update_properties = True

    def _calculate_all_properties(self) -> None:
        self._refresh_specific_capacity_curve()

    def _get_default_curve_from_curves(self) -> None:
        """
        Get the default half cell curve from the half cell curves.

        :return: pd.DataFrame: The default half cell curve.
        """
        specific_capacity_curves = self._specific_capacity_curves.copy()

        # get the maximum specific capacity for each half cell curve
        maximum_specific_capacities = []
        for hcc in specific_capacity_curves:
            maximum_specific_capacities.append(np.max(hcc[:, 0]))

        # get the index of the half cell curve with the maximum specific capacity
        max_index = np.argmax(maximum_specific_capacities)

        # get the half cell curve with the maximum specific capacity
        self._specific_capacity_curve = self._specific_capacity_curves[max_index].copy()

        # get the voltage at maximum specific capacity
        self._voltage_cutoff = self._specific_capacity_curve[
            self._specific_capacity_curve[:, 0] == np.max(self._specific_capacity_curve[:, 0]), 1
        ][0]

    def _get_maximum_operating_voltage(self) -> float:
        """
        Function to get the maximum operating voltage of the half cell curves.
        """
        max_voltages = []

        for curve in self._specific_capacity_curves:
            max_capacity_idx = np.argmax(curve[:, 0])
            voltage_at_max_capacity = curve[max_capacity_idx, 1]
            max_voltages.append(voltage_at_max_capacity)

        self._maximum_operating_voltage = np.max(max_voltages)

    def _get_minimum_operating_voltage(self) -> float:
        """
        Function to get the minimum operating voltage of the half cell curves without extrapolation.
        """
        max_voltages = []

        for curve in self._specific_capacity_curves:
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
                self._maximum_operating_voltage,
            )

        elif type(self) == AnodeMaterial:

            self._voltage_operation_window = (
                self._minimum_operating_voltage + self._extrapolation_window,
                self._minimum_operating_voltage,
                self._maximum_operating_voltage,
            )

    def _calculate_specific_capacity_curves_properties(self):
        self._get_maximum_operating_voltage()
        self._get_minimum_operating_voltage()
        self._get_operating_voltage_range()

    def _refresh_specific_capacity_curve(self) -> None:
        """Recalculate the working half-cell curve using the current cutoff."""
        if not hasattr(self, "_specific_capacity_curves") or not self._specific_capacity_curves:
            return

        if not hasattr(self, "_voltage_operation_window"):
            self._calculate_specific_capacity_curves_properties()

        voltage_cutoff = getattr(self, "_voltage_cutoff", None)

        if voltage_cutoff is None:
            self._get_default_curve_from_curves()
            return

        self._specific_capacity_curve = self._calculate_specific_capacity_curve(
            self._specific_capacity_curves,
            voltage_cutoff,
            self._voltage_operation_window,
            type(self),
        )

    def plot_underlying_specific_capacity_curves(self, **kwargs):

        fig = go.Figure()
        fig.add_traces(self.specific_capacity_curves_traces)
        XAXIS = self.SCATTER_X_AXIS
        XAXIS['title'] = 'Specific Capacity (mAh/g)'
        YAXIS = self.SCATTER_Y_AXIS
        YAXIS['title'] = 'Voltage (V)'

        fig.update_layout(
            title=kwargs.get("title", f"Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            hovermode="closest",
            xaxis=XAXIS,
            yaxis=YAXIS,
            **kwargs,
        )

        return fig

    def plot_specific_capacity_curve(self, **kwargs):

        fig = go.Figure()
        fig.add_trace(self.specific_capacity_curve_trace)
        XAXIS = self.SCATTER_X_AXIS
        XAXIS['title'] = 'Specific Capacity (mAh/g)'
        YAXIS = self.SCATTER_Y_AXIS
        YAXIS['title'] = 'Voltage (V)'

        fig.update_layout(
            title=kwargs.get("title", f"Half Cell Curve"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            hovermode="closest",
            xaxis=XAXIS,
            yaxis=YAXIS,
            **kwargs,
        )

        fig.update_traces(line=dict(color=self.color))

        return fig

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
            np.round(float(self._voltage_operation_window[0]), 2),
            np.round(float(self._voltage_operation_window[2]), 2),
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
    def specific_capacity_curve(self) -> pd.DataFrame:
        """Get the specific capacity curve with proper units and formatting."""
        if self._specific_capacity_curve is None:
            return None

        # Pre-compute unit conversion factor
        capacity_conversion = S_TO_H * A_TO_mA / KG_TO_G
        
        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Specific Capacity (mAh/g)": np.round(
                self._specific_capacity_curve[:, 0] * capacity_conversion, 4
            ),
            "Voltage (V)": np.round(self._specific_capacity_curve[:, 1], 4),
            "Direction": np.where(
                self._specific_capacity_curve[:, 2] == 1, "charge", "discharge"
            ),
        })

    @property
    def specific_capacity_curves(self) -> pd.DataFrame:
        """Get all specific capacity curves with proper units and formatting."""
        # Pre-compute unit conversion factor once
        if self._specific_capacity_curves is None:
            return None

        capacity_conversion = S_TO_H * A_TO_mA / KG_TO_G
        
        # Pre-allocate list with known size
        data_list = []
        
        for curve in self._specific_capacity_curves:

            # Compute max voltage once
            max_voltage = np.round(curve[:, 1].max(), 4)
            
            # Create arrays directly without intermediate steps
            capacity = np.round(curve[:, 0] * capacity_conversion, 4)
            voltage = np.round(curve[:, 1], 4)
            direction = np.where(curve[:, 2] == 1, "charge", "discharge")
            
            # Create DataFrame with pre-computed arrays
            df = pd.DataFrame({
                "Specific Capacity (mAh/g)": capacity,
                "Voltage (V)": voltage,
                "Direction": direction,
                "Voltage at Maximum Capacity (V)": max_voltage,
            })
            
            data_list.append(df)
        
        return pd.concat(data_list, ignore_index=True)
    
    @property
    def specific_capacity_curves_traces(self) -> List[go.Scatter]:

        if self._specific_capacity_curves is None:
            return None

        data = self.specific_capacity_curves
        traces = []

        for name, df in data.groupby("Voltage at Maximum Capacity (V)"):

            trace = go.Scatter(
                x=df["Specific Capacity (mAh/g)"],
                y=df["Voltage (V)"],
                name=f"{name} V",
                line=dict(width=2),
                mode="lines",
                hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "<i>Individual Material</i><extra></extra>",
            )

            traces.append(trace)

        return traces
    
    @property
    def specific_capacity_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.specific_capacity_curve["Specific Capacity (mAh/g)"],
            y=self.specific_capacity_curve["Voltage (V)"],
            name=self.name,
            line=dict(color=self._color, width=2),
            mode="lines",
            hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "<i>Individual Material</i><extra></extra>",
        )

    @property
    def irreversible_capacity_scaling(self) -> float:
        return self._irreversible_capacity_scaling

    @property
    def irreversible_capacity_scaling_range(self) -> Tuple:
        return 0.8, 1.1

    @property
    def irreversible_capacity_scaling_hard_range(self) -> Tuple:
        return 0, 2

    @property
    def reversible_capacity_scaling(self) -> float:
        return self._reversible_capacity_scaling

    @property
    def reversible_capacity_scaling_range(self) -> Tuple:
        return 0.8, 1.1

    @property
    def reversible_capacity_scaling_hard_range(self) -> Tuple:
        return 0, 2

    @property
    def specific_capacity_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.specific_capacity_curve["Specific Capacity (mAh/g)"],
            y=self.specific_capacity_curve["Voltage (V)"],
            name=self.name,
            line=dict(color=self._color, width=2),
            mode="lines",
            hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "<i>Individual Material</i><extra></extra>",
        )

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
        # validate input
        self.validate_positive_float(scaling, "Reversible capacity scaling")

        # get the old scaling factor
        if hasattr(self, "_reversible_capacity_scaling") and self._reversible_capacity_scaling != 1.0:
            original_scaling = self._reversible_capacity_scaling
            self._specific_capacity_curve = self._apply_reversible_capacity_scaling(self._specific_capacity_curve, 1 / original_scaling)
        else:
            original_scaling = 1.0

        self._specific_capacity_curve = self._apply_reversible_capacity_scaling(self._specific_capacity_curve, scaling)
        self._reversible_capacity_scaling = scaling

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
            self.validate_positive_float(voltage, "Voltage cutoff")
            self._voltage_cutoff = voltage
            if not hasattr(self, "_voltage_operation_window"):
                self._calculate_specific_capacity_curves_properties()

            self._specific_capacity_curve = self._calculate_specific_capacity_curve(
                self._specific_capacity_curves,
                self._voltage_cutoff,
                self._voltage_operation_window,
                type(self),
            )

            if (
                hasattr(self, "_irreversible_capacity_scaling")
                and self._irreversible_capacity_scaling != 1.0
            ):
                self._specific_capacity_curve = self._apply_irreversible_capacity_scaling(
                    self._specific_capacity_curve,
                    self._irreversible_capacity_scaling,
                )

            if (
                hasattr(self, "_reversible_capacity_scaling")
                and self._reversible_capacity_scaling != 1.0
            ):
                self._specific_capacity_curve = self._apply_reversible_capacity_scaling(
                    self._specific_capacity_curve,
                    self._reversible_capacity_scaling,
                )

    @irreversible_capacity_scaling.setter
    def irreversible_capacity_scaling(self, scaling: float):
        """
        Set the irreversible capacity scaling factor.

        :param scaling: float: scaling factor for irreversible capacity
        """
        self.validate_positive_float(scaling, "Irreversible capacity scaling")
        
        if hasattr(self, "_irreversible_capacity_scaling") and self._irreversible_capacity_scaling != 1.0:
            original_scaling = self._irreversible_capacity_scaling
            self._specific_capacity_curve = self._apply_irreversible_capacity_scaling(self._specific_capacity_curve, 1 / original_scaling)
        else:
            original_scaling = 1.0
        
        # apply the new scaling factor
        if hasattr(self, "_specific_capacity_curve"):
            self._specific_capacity_curve = self._apply_irreversible_capacity_scaling(self._specific_capacity_curve, scaling)

        self._irreversible_capacity_scaling = scaling

    @specific_capacity_curves.setter
    def specific_capacity_curves(
        self, specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame]
    ) -> None:

        # Ensure specific_capacity_curves is a list
        if not isinstance(specific_capacity_curves, List):
            specific_capacity_curves = [specific_capacity_curves]

        # make a deep copy to avoid modifying the original data
        specific_capacity_curves = deepcopy(specific_capacity_curves)

        # Validate each dataframe
        for df in specific_capacity_curves:

            self.validate_pandas_dataframe(
                df,
                "half cell curves",
                column_names=["specific_capacity", "voltage", "direction"],
            )

        # map the direction values to integers for faster processing
        for df in specific_capacity_curves:
            df["direction"] = (
                df["direction"]
                .map({"charge": 1, "discharge": -1, "Charge": 1, "Discharge": -1})
            )

        # Then convert to numpy arrays and process each curve individually
        array_list = [
            df[["specific_capacity", "voltage", "direction"]].to_numpy()
            for df in specific_capacity_curves
        ]

        processed_curves = [
            self.process_specific_capacity_curves(curve_array.copy())
            for curve_array in array_list
        ]

        self._specific_capacity_curves = processed_curves

        # Store useful values for the half cell curves
        self._calculate_specific_capacity_curves_properties()
        self._refresh_specific_capacity_curve()

    @extrapolation_window.setter
    def extrapolation_window(self, window: float):
        self.validate_positive_float(window, "Extrapolation window")
        self._extrapolation_window = abs(float(window))

        if self._update_properties:
            self._calculate_specific_capacity_curves_properties()


class CathodeMaterial(_ActiveMaterial):

    _table_name = "cathode_materials"

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: str = "#2c2c2c",
        voltage_cutoff: float = None,
        extrapolation_window: float = 0.4,
        reversible_capacity_scaling: float = 1.0,
        irreversible_capacity_scaling: float = 1.0,
        *,
        volume=None,
        mass=None,
        **kwargs,
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
        specific_capacity_curves : Union[List[pd.DataFrame], pd.DataFrame]
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
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            specific_capacity_curves=specific_capacity_curves,
            color=color,
            extrapolation_window=extrapolation_window,
            voltage_cutoff=voltage_cutoff,
            reversible_capacity_scaling=reversible_capacity_scaling,
            irreversible_capacity_scaling=irreversible_capacity_scaling,
            volume=volume,
            mass=mass,
            **kwargs,
        )

    @property
    def minimum_extrapolated_voltage(self) -> float:
        """
        Get the minimum extrapolated voltage for the half cell curves.

        :return: float: minimum extrapolated voltage of the half cell curves
        """
        try:
            return float(round(self._minimum_extrapolated_voltage, 2))
        except Exception:
            return None


class AnodeMaterial(_ActiveMaterial):

    _table_name = "anode_materials"

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: str = "#2c2c2c",
        extrapolation_window: float = 0.05,
        voltage_cutoff: float = None,
        reversible_capacity_scaling: float = 1.0,
        irreversible_capacity_scaling: float = 1.0,
        *,
        volume=None,
        mass=None,
        **kwargs,
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
        specific_capacity_curves : Union[List[pd.DataFrame], pd.DataFrame]
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
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            specific_capacity_curves=specific_capacity_curves,
            color=color,
            voltage_cutoff=voltage_cutoff,
            extrapolation_window=extrapolation_window,
            reversible_capacity_scaling=reversible_capacity_scaling,
            irreversible_capacity_scaling=irreversible_capacity_scaling,
            volume=volume,
            mass=mass,
            **kwargs,
        )

