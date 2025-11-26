from steer_core.DataManager import DataManager
from steer_core.Constants.Units import *
from steer_core.Mixins.Data import DataMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_materials.Base import _Material, _VolumedMaterialMixin

from steer_opencell_design.Materials.HalfCellUtils import HalfCellMixin

import pandas as pd
import numpy as np
import plotly.express as px
from plotly import graph_objects as go
from typing import List, Tuple, Union, Optional, Type
from copy import deepcopy


class _ActiveMaterial(
    _Material, 
    _VolumedMaterialMixin, 
    DataMixin,
    HalfCellMixin
    ):

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: Optional[str] = "#2c2c2c",
        voltage_cutoff: Optional[float] = None,
        extrapolation_window: Optional[float] = 0.4,
        reversible_capacity_scaling: Optional[float] = 1.0,
        irreversible_capacity_scaling: Optional[float] = 1.0,
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
        self._refresh_half_cell_curve()

    def _get_default_curve_from_curves(self) -> None:
        """
        Get the default half cell curve from the half cell curves.

        :return: pd.DataFrame: The default half cell curve.
        """
        half_cell_curves = self._half_cell_curves.copy()

        # get the maximum specific capacity for each half cell curve
        maximum_specific_capacities = []
        for hcc in half_cell_curves:
            maximum_specific_capacities.append(np.max(hcc[:, 0]))

        # get the index of the half cell curve with the maximum specific capacity
        max_index = np.argmax(maximum_specific_capacities)

        # get the half cell curve with the maximum specific capacity
        self._half_cell_curve = self._half_cell_curves[max_index].copy()

        # get the voltage at maximum specific capacity
        self._voltage_cutoff = self._half_cell_curve[
            self._half_cell_curve[:, 0] == np.max(self._half_cell_curve[:, 0]), 1
        ][0]

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
                self._maximum_operating_voltage,
            )

        elif type(self) == AnodeMaterial:

            self._voltage_operation_window = (
                self._minimum_operating_voltage + self._extrapolation_window,
                self._minimum_operating_voltage,
                self._maximum_operating_voltage,
            )

    def _calculate_half_cell_curves_properties(self):
        self._get_maximum_operating_voltage()
        self._get_minimum_operating_voltage()
        self._get_operating_voltage_range()

    def _refresh_half_cell_curve(self) -> None:
        """Recalculate the working half-cell curve using the current cutoff."""
        if not hasattr(self, "_half_cell_curves") or not self._half_cell_curves:
            return

        if not hasattr(self, "_voltage_operation_window"):
            self._calculate_half_cell_curves_properties()

        voltage_cutoff = getattr(self, "_voltage_cutoff", None)

        if voltage_cutoff is None:
            self._get_default_curve_from_curves()
            return

        self._half_cell_curve = self._calculate_half_cell_curve(
            self._half_cell_curves,
            voltage_cutoff,
            self._voltage_operation_window,
            type(self),
        )

    def plot_curves(self, **kwargs):

        fig = px.line(
            self.half_cell_curves,
            x="Specific Capacity (mAh/g)",
            y="Voltage (V)",
            color="Voltage at Maximum Capacity (V)",
            line_shape="spline",
        )

        fig.update_layout(
            title=kwargs.get("title", f"Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            hovermode="closest",
            **kwargs,
        )

        return fig

    def plot_half_cell_curve(self, **kwargs):

        fig = px.line(
            self.half_cell_curve,
            x="Specific Capacity (mAh/g)",
            y="Voltage (V)",
            line_shape="spline",
        )

        fig.update_layout(
            title=kwargs.get("title", f"Half Cell Curve"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            hovermode="closest",
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
            round(float(self._voltage_operation_window[0]), 2),
            round(float(self._voltage_operation_window[2]), 2),
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
                columns=["specific_capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(
                    x["direction"] == 1, "charge", "discharge"
                ),
                specific_capacity=lambda x: x["specific_capacity"]
                * (S_TO_H * A_TO_mA / KG_TO_G),
            )
            .rename(
                columns={
                    "specific_capacity": "Specific Capacity (mAh/g)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
            .round(4)
        )

    @property
    def half_cell_curves(self) -> pd.DataFrame:

        data_list = []

        for curve in self._half_cell_curves:

            df = (
                pd.DataFrame(
                    curve, columns=["specific_capacity", "voltage", "direction"]
                )
                .assign(
                    direction=lambda x: np.where(
                        x["direction"] == 1, "charge", "discharge"
                    ),
                    specific_capacity=lambda x: x["specific_capacity"]
                    * (S_TO_H * A_TO_mA / KG_TO_G),
                    voltage_at_max_capacity=lambda x: x["voltage"].max(),
                )
                .rename(
                    columns={
                        "specific_capacity": "Specific Capacity (mAh/g)",
                        "voltage": "Voltage (V)",
                        "direction": "Direction",
                        "voltage_at_max_capacity": "Voltage at Maximum Capacity (V)",
                    }
                )
                .round(4)
            )

            data_list.append(df)

        return pd.concat(data_list, ignore_index=True)

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
    def half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.half_cell_curve["Specific Capacity (mAh/g)"],
            y=self.half_cell_curve["Voltage (V)"],
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
            self._half_cell_curve = self._apply_reversible_capacity_scaling(self._half_cell_curve, 1 / original_scaling)
        else:
            original_scaling = 1.0

        self._half_cell_curve = self._apply_reversible_capacity_scaling(self._half_cell_curve, scaling)
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
                self._calculate_half_cell_curves_properties()

            self._half_cell_curve = self._calculate_half_cell_curve(
                self._half_cell_curves,
                self._voltage_cutoff,
                self._voltage_operation_window,
                type(self),
            )

            if (
                hasattr(self, "_irreversible_capacity_scaling")
                and self._irreversible_capacity_scaling != 1.0
            ):
                self._half_cell_curve = self._apply_irreversible_capacity_scaling(
                    self._half_cell_curve,
                    self._irreversible_capacity_scaling,
                )

            if (
                hasattr(self, "_reversible_capacity_scaling")
                and self._reversible_capacity_scaling != 1.0
            ):
                self._half_cell_curve = self._apply_reversible_capacity_scaling(
                    self._half_cell_curve,
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
            self._half_cell_curve = self._apply_irreversible_capacity_scaling(self._half_cell_curve, 1 / original_scaling)
        else:
            original_scaling = 1.0
        
        # apply the new scaling factor
        if hasattr(self, "_half_cell_curve"):
            self._half_cell_curve = self._apply_irreversible_capacity_scaling(self._half_cell_curve, scaling)

        self._irreversible_capacity_scaling = scaling

    @half_cell_curves.setter
    def half_cell_curves(
        self, half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame]
    ) -> None:

        # Ensure half_cell_curves is a list
        if not isinstance(half_cell_curves, List):
            half_cell_curves = [half_cell_curves]

        # make a deep copy to avoid modifying the original data
        half_cell_curves = deepcopy(half_cell_curves)

        # Validate each dataframe
        for df in half_cell_curves:

            self.validate_pandas_dataframe(
                df,
                "half cell curves",
                column_names=["specific_capacity", "voltage", "direction"],
            )

        # map the direction values to integers for faster processing
        for df in half_cell_curves:
            df["direction"] = (
                df["direction"]
                .map({"charge": 1, "discharge": -1, "Charge": 1, "Discharge": -1})
            )

        # Then convert to numpy arrays and process each curve individually
        array_list = [
            df[["specific_capacity", "voltage", "direction"]].to_numpy()
            for df in half_cell_curves
        ]

        processed_curves = [
            self.process_half_cell_curves(curve_array.copy())
            for curve_array in array_list
        ]

        self._half_cell_curves = processed_curves

        # Store useful values for the half cell curves
        self._calculate_half_cell_curves_properties()
        self._refresh_half_cell_curve()

    @extrapolation_window.setter
    def extrapolation_window(self, window: float):
        self.validate_positive_float(window, "Extrapolation window")
        self._extrapolation_window = abs(float(window))

        if self._update_properties:
            self._calculate_half_cell_curves_properties()


class CathodeMaterial(_ActiveMaterial):

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: str = "#2c2c2c",
        voltage_cutoff: float = None,
        extrapolation_window: float = 0.4,
        reversible_capacity_scaling: float = 1.0,
        irreversible_capacity_scaling: float = 1.0,
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
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            half_cell_curves=half_cell_curves,
            color=color,
            extrapolation_window=extrapolation_window,
            voltage_cutoff=voltage_cutoff,
            reversible_capacity_scaling=reversible_capacity_scaling,
            irreversible_capacity_scaling=irreversible_capacity_scaling,
        )

    @staticmethod
    def from_database(name) -> "CathodeMaterial":
        """
        Pull object from the database.

        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values("cathode_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_cathode_materials(most_recent=True).query(
            f"name == '{name}'"
        )
        string_rep = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_rep)
        return material

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

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        half_cell_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: str = "#2c2c2c",
        extrapolation_window: float = 0.05,
        voltage_cutoff: float = None,
        reversible_capacity_scaling: float = 1.0,
        irreversible_capacity_scaling: float = 1.0,
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
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            half_cell_curves=half_cell_curves,
            color=color,
            voltage_cutoff=voltage_cutoff,
            extrapolation_window=extrapolation_window,
            reversible_capacity_scaling=reversible_capacity_scaling,
            irreversible_capacity_scaling=irreversible_capacity_scaling,
        )

    @staticmethod
    def from_database(name) -> "AnodeMaterial":
        """
        Pull object from the database.

        :param name: str: Name of the current collector material.
        :return: CurrentCollectorMaterial: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values("anode_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_anode_materials(most_recent=True).query(f"name == '{name}'")
        string_rep = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_rep)
        return material

