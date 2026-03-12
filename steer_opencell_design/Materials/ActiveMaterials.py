"""Active material definitions with half-cell voltage-capacity curves."""

from steer_core.Constants.Units import *
from steer_core.Mixins.Data import DataMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Decorators.General import calculate_all_properties

from steer_materials.Base import _Material, _VolumedMaterialMixin

from steer_opencell_design.Materials.CapacityCurveUtils import CapacityCurveMixin

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly import graph_objects as go
from typing import List, Tuple, Union, Optional, Type
from copy import deepcopy
import base64
from io import StringIO


class _ActiveMaterial(
    _VolumedMaterialMixin, 
    _Material, 
    DataMixin,
    CapacityCurveMixin,
    PlotterMixin
    ):
    """Base class for electrode active materials (cathode/anode).

    Manages half-cell voltage-capacity curves, scaling factors for reversible
    and irreversible capacity, and provides plotting utilities for capacity
    curves.
    """

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: Optional[str] = "#2c2c2c",
        extrapolation_window: Optional[float] = 0.4,
        reversible_specific_capacity_scaling_percentage: Optional[float] = 0.0,
        irreversible_specific_capacity_scaling_percentage: Optional[float] = 0.0,
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
        extrapolation_window : Optional[float]
            The extrapolation window in V. This is the amount of voltage below the maximum voltage (for CathodeMaterial) or above the minimum voltage (for AnodeMaterial)
            of the half cell curves that will be used for extrapolation. This allows for estimation of voltage profiles over a voltage window
        reversible_specific_capacity_scaling_percentage : Optional[float]
            Percentage adjustment for the reversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
        irreversible_specific_capacity_scaling_percentage : Optional[float]
            Percentage adjustment for the irreversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
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
        self.reversible_specific_capacity_scaling_percentage = reversible_specific_capacity_scaling_percentage
        self.irreversible_specific_capacity_scaling_percentage = irreversible_specific_capacity_scaling_percentage

    @classmethod
    def _from_app_csv(
        cls,
        contents: Union[str, List[str]],
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        **kwargs,
    ) -> "_ActiveMaterial":
        """
        Create an ActiveMaterial instance from base64-encoded CSV content(s) uploaded via a Dash dcc.Upload component.

        Parameters
        ----------
        contents : Union[str, List[str]]
            Base64-encoded CSV string(s) from dcc.Upload. Format: "data:text/csv;base64,<encoded_data>".
            Can be a single string or a list of strings for multiple capacity curves.
        name : str
            Name of the material.
        reference : str
            Reference electrode for the material, e.g., 'Li/Li+'.
        specific_cost : float
            Specific cost of the material in $/kg.
        density : float
            Density of the material in g/cm^3.
        **kwargs
            Additional keyword arguments passed to the constructor (e.g., color, extrapolation_window,
            reversible_specific_capacity_scaling_percentage, irreversible_specific_capacity_scaling_percentage).

        Returns
        -------
        _ActiveMaterial
            A new instance of the class (or subclass) with parsed capacity curves.

        Notes
        -----
        The CSV file(s) must have the following column headers:
            - "Specific Capacity (mAh/g)"
            - "Voltage (V)"
            - "Direction (Charge/Discharge)"

        The "Direction (Charge/Discharge)" column should contain "Charge" or "Discharge" values.
        """
        column_mapping = {
            "Specific Capacity (mAh/g)": "specific_capacity",
            "Voltage (V)": "voltage",
            "Direction (Charge/Discharge)": "direction",
        }

        def parse_single_csv(content: str) -> pd.DataFrame:
            # Split content type prefix from base64 data
            _, content_string = content.split(",")
            # Decode base64 to bytes, then to string
            decoded = base64.b64decode(content_string).decode("utf-8")
            # Read CSV from string
            df = pd.read_csv(StringIO(decoded))
            # Rename columns to expected format
            df = df.rename(columns=column_mapping)
            # Normalize direction values to lowercase
            df["direction"] = df["direction"].str.lower()
            return df

        # Handle single or multiple uploads
        if isinstance(contents, str):
            curves = [parse_single_csv(contents)]
        else:
            curves = [parse_single_csv(c) for c in contents]

        return cls(
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            specific_capacity_curves=curves,
            **kwargs,
        )

    def _calculate_all_properties(self) -> None:

        self._refresh_specific_capacity_curve()

        if self._update_properties == False:
            self._calculate_specific_capacity_ranges()

    def _calculate_specific_capacity_ranges(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:

        # Convert percentage ranges to multiplier ranges for internal calculations
        irreversible_range_percentage = self.irreversible_specific_capacity_scaling_percentage_range
        irreversible_range_multiplier = (1.0 + irreversible_range_percentage[0]/100.0, 1.0 + irreversible_range_percentage[1]/100.0)
        
        _minimum_curve = self._apply_irreversible_specific_capacity_scaling(
            self._specific_capacity_curve, irreversible_range_multiplier[0]
        )

        _maximum_curve = self._apply_irreversible_specific_capacity_scaling(
            self._specific_capacity_curve, irreversible_range_multiplier[1]
        )

        self._irreversible_specific_capacity_range = (
            _minimum_curve[:, 0].max(),
            _maximum_curve[:, 0].max(),
        )

        # Convert percentage ranges to multiplier ranges for internal calculations
        reversible_range_percentage = self.reversible_specific_capacity_scaling_percentage_range
        reversible_range_multiplier = (1.0 + reversible_range_percentage[0]/100.0, 1.0 + reversible_range_percentage[1]/100.0)
        
        _minimum_curve = self._apply_reversible_specific_capacity_scaling(
            self._specific_capacity_curve, reversible_range_multiplier[0]
        )

        _maximum_curve = self._apply_reversible_specific_capacity_scaling(
            self._specific_capacity_curve, reversible_range_multiplier[1]
        )

        discharge_mask = self._specific_capacity_curve[:, 2] == -1

        self._reversible_specific_capacity_range = (
            _minimum_curve[:, 0].max() - _minimum_curve[discharge_mask, 0].min(),
            _maximum_curve[:, 0].max() - _maximum_curve[discharge_mask, 0].min(),
        )

        return self._irreversible_specific_capacity_range, self._reversible_specific_capacity_range

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

        return self._maximum_operating_voltage

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

        return self._minimum_operating_voltage

    def _get_operating_voltage_range(self) -> Tuple[float, float, float]:
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

        return self._voltage_operation_window

    def _calculate_specific_capacity_curves_properties(self):

        self._get_maximum_operating_voltage()
        self._get_minimum_operating_voltage()
        self._get_operating_voltage_range()

        if not hasattr(self, '_voltage_cutoff') or self._voltage_cutoff is None:
            self._voltage_cutoff = self._voltage_operation_window[1]

    def _refresh_specific_capacity_curve(self) -> None:
        """Recalculate the working half-cell curve using the current cutoff."""

        # calculate properties from the underlying data
        self._calculate_specific_capacity_curves_properties()

        # Type narrowing: voltage_cutoff should be set after calculating properties
        assert self._voltage_cutoff is not None, "voltage_cutoff should be set after calculating properties"
        assert self._irreversible_specific_capacity_scaling is not None, "irreversible_specific_capacity_scaling should not be None"
        assert self._reversible_specific_capacity_scaling is not None, "reversible_specific_capacity_scaling should not be None"

        # get the curve from the underlying curves data
        self._specific_capacity_curve = self._calculate_specific_capacity_curve(
            self._specific_capacity_curves,
            self._voltage_cutoff,
            self._voltage_operation_window,
            type(self),
        )

        # apply irreversible scaling
        if self._irreversible_specific_capacity_scaling != 1.0:
            self._specific_capacity_curve = self._apply_irreversible_specific_capacity_scaling(self._specific_capacity_curve, self._irreversible_specific_capacity_scaling)

        # apply reversible scaling
        if self._reversible_specific_capacity_scaling != 1.0:
            self._specific_capacity_curve = self._apply_reversible_specific_capacity_scaling(self._specific_capacity_curve, self._reversible_specific_capacity_scaling)

        # calculate capacity properties
        self._irreversible_specific_capacity, self._reversible_specific_capacity = self._calculate_capacity_curve_properties(
            self._specific_capacity_curve
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

    def plot_specific_capacity_curve_interactive(self, n_steps: int = 20, **kwargs):
        """Return a Plotly figure with a slider to explore voltage cutoff values.

        Parameters
        ----------
        n_steps : int
            Number of discrete voltage steps to pre-compute across the valid
            voltage cutoff range. Default is 20.
        **kwargs
            Additional keyword arguments passed to ``fig.update_layout``.

        Returns
        -------
        go.Figure
            A Plotly figure with a slider controlling which pre-computed curve
            is displayed.
        """
        # Use the raw operation window bounds and apply ceil/floor to ensure
        # generated voltages stay strictly within the valid range
        v_min = np.ceil(float(self._voltage_operation_window[0]) * 10000) / 10000
        v_max = np.floor(float(self._voltage_operation_window[2]) * 10000) / 10000
        voltages = np.round(np.linspace(v_min, v_max, n_steps), 4)
        capacity_conversion = S_TO_H * A_TO_mA / KG_TO_G

        # Pre-compute a curve for each voltage step and track axis ranges
        frames = []
        all_x_values = []
        all_y_values = []
        
        for v in voltages:
            curve = self._calculate_specific_capacity_curve(
                self._specific_capacity_curves,
                float(v),
                self._voltage_operation_window,
                type(self),
            )
            x = np.round(curve[:, 0] * capacity_conversion, 4)
            y = np.round(curve[:, 1], 4)
            
            # Track ranges across all frames
            all_x_values.extend(x)
            all_y_values.extend(y)
            
            frames.append(go.Frame(
                data=[go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    line=dict(color=self._color, width=2),
                    hovertemplate=(
                        "<b>%{fullData.name}</b><br>"
                        "Capacity: %{x:.2f} mAh/g<br>"
                        "Voltage: %{y:.3f} V<br>"
                        "<extra></extra>"
                    ),
                )],
                name=str(v),
            ))
        
        # Calculate axis ranges that encompass all curves
        x_min, x_max = min(all_x_values), max(all_x_values)
        y_min, y_max = min(all_y_values), max(all_y_values)
        # Add 5% padding
        x_padding = (x_max - x_min) * 0.05
        y_padding = (y_max - y_min) * 0.05

        # Initial trace uses the last frame's data (maximum voltage cutoff)
        fig = go.Figure(data=frames[-1].data, frames=frames)

        # Build slider steps
        slider_steps = [
            dict(
                args=[[str(v)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                label=str(v),
                method="animate",
            )
            for v in voltages
        ]

        sliders = [dict(
            active=len(voltages) - 1,  # Default to maximum voltage cutoff
            currentvalue={"prefix": "Voltage Cutoff: ", "suffix": " V"},
            pad={"t": 50},
            steps=slider_steps,
        )]

        XAXIS = self.SCATTER_X_AXIS.copy()
        XAXIS['title'] = 'Specific Capacity (mAh/g)'
        XAXIS['range'] = [x_min - x_padding, x_max + x_padding]  # type: ignore[assignment]
        
        YAXIS = self.SCATTER_Y_AXIS.copy()
        YAXIS['title'] = 'Voltage (V)'
        YAXIS['range'] = [y_min - y_padding, y_max + y_padding]  # type: ignore[assignment]

        fig.update_layout(
            title=kwargs.pop("title", f"{self.name} - Interactive Voltage Cutoff"),
            paper_bgcolor=kwargs.pop("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.pop("plot_bgcolor", "white"),
            hovermode="closest",
            xaxis=XAXIS,
            yaxis=YAXIS,
            sliders=sliders,
            **kwargs,
        )

        return fig

    @property
    def voltage_cutoff(self) -> Optional[float]:
        """
        Get the voltage cutoff for this active material.
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
    def extrapolation_window(self) -> Optional[float]:
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
    def specific_capacity_curve(self) -> Optional[pd.DataFrame]:
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
    def specific_capacity_curves(self) -> Optional[pd.DataFrame]:
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
    def specific_capacity_curves_traces(self) -> Optional[List[go.Scatter]]:

        if self._specific_capacity_curves is None:
            return None

        data = self.specific_capacity_curves
        if data is None:
            return None
        
        traces = []

        for name, df in data.groupby("Voltage at Maximum Capacity (V)"):

            trace = go.Scatter(
                x=df["Specific Capacity (mAh/g)"],
                y=df["Voltage (V)"],
                name=f"{name} V",
                line=dict(color=self._color, width=2),
                mode="lines",
                hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "<i>Individual Material</i><extra></extra>",
            )

            traces.append(trace)

        return traces
    
    @property
    def specific_capacity_curve_trace(self) -> Optional[go.Scatter]:
        curve = self.specific_capacity_curve
        if curve is None:
            return None
            
        return go.Scatter(
            x=curve["Specific Capacity (mAh/g)"],
            y=curve["Voltage (V)"],
            name=self.name,
            line=dict(color=self._color, width=2),
            mode="lines",
            hovertemplate="<b>%{fullData.name}</b><br>" + "Capacity: %{x:.2f} mAh/g<br>" + "Voltage: %{y:.3f} V<br>" + "<i>Individual Material</i><extra></extra>",
        )

    @property
    def irreversible_specific_capacity_scaling_percentage(self) -> float:
        if self._irreversible_specific_capacity_scaling is None:
            return 0.0
        return np.round((self._irreversible_specific_capacity_scaling - 1.0) * 100, 1)

    @property
    def irreversible_specific_capacity_scaling_percentage_range(self) -> Tuple:
        return -30.0, 30.0

    @property
    def irreversible_specific_capacity_scaling_percentage_hard_range(self) -> Tuple:
        return -100.0, 100.0

    @property
    def reversible_specific_capacity_scaling_percentage(self) -> float:
        if self._reversible_specific_capacity_scaling is None:
            return 0.0
        return np.round((self._reversible_specific_capacity_scaling - 1.0) * 100, 1)

    @property
    def reversible_specific_capacity_scaling_percentage_range(self) -> Tuple:
        return -30.0, 30.0

    @property
    def reversible_specific_capacity_scaling_percentage_hard_range(self) -> Tuple:
        return -100.0, 100.0

    @property
    def irreversible_specific_capacity(self) -> float:
        """Get the irreversible specific capacity in mAh/g."""
        return np.round(self._irreversible_specific_capacity * (S_TO_H * A_TO_mA / KG_TO_G), 2)
    
    @property
    def irreversible_specific_capacity_range(self) -> Tuple[float, float]:
        """Get the irreversible specific capacity range in mAh/g."""
        return (
            np.round(self._irreversible_specific_capacity_range[0] * (S_TO_H * A_TO_mA / KG_TO_G), 2),
            np.round(self._irreversible_specific_capacity_range[1] * (S_TO_H * A_TO_mA / KG_TO_G), 2),
        )
    
    @property
    def irreversible_specific_capacity_hard_range(self) -> Tuple[float, float]:
        """Get the irreversible specific capacity hard range in mAh/g."""
        return (0, 6000)

    @property
    def reversible_specific_capacity(self) -> float:
        """Get the reversible specific capacity in mAh/g."""
        return np.round(self._reversible_specific_capacity * (S_TO_H * A_TO_mA / KG_TO_G), 2)
    
    @property
    def reversible_specific_capacity_range(self) -> Tuple[float, float]:
        """Get the reversible specific capacity range in mAh/g."""
        return (
            np.round(self._reversible_specific_capacity_range[0] * (S_TO_H * A_TO_mA / KG_TO_G), 2),
            np.round(self._reversible_specific_capacity_range[1] * (S_TO_H * A_TO_mA / KG_TO_G), 2),
        )
    
    @property
    def reversible_specific_capacity_hard_range(self) -> Tuple[float, float]:
        """Get the reversible specific capacity hard range in mAh/g."""
        return (0, 6000)

    @irreversible_specific_capacity.setter
    def irreversible_specific_capacity(self, capacity: float):
        
        # validate input
        self.validate_positive_float(capacity, "Irreversible specific capacity")

        # convert to SI units
        target_capacity = capacity * (mA_TO_A * H_TO_S / G_TO_KG)

        # Get the base capacity (when scaling = 1.0)
        base_capacity = self._irreversible_specific_capacity / self._irreversible_specific_capacity_scaling

        # Calculate new scaling factor to achieve target capacity
        new_scaling = target_capacity / base_capacity

        # Convert to percentage and apply
        new_percentage = (new_scaling - 1.0) * 100
        self.irreversible_specific_capacity_scaling_percentage = new_percentage

    @reversible_specific_capacity.setter
    def reversible_specific_capacity(self, capacity: float):
        # validate input
        self.validate_positive_float(capacity, "Reversible specific capacity")

        # convert to SI units
        target_capacity = capacity * (mA_TO_A * H_TO_S / G_TO_KG)

        # Get the base capacity (when scaling = 1.0)
        base_capacity = self._reversible_specific_capacity / self._reversible_specific_capacity_scaling

        # Calculate new scaling factor to achieve target capacity
        new_scaling = target_capacity / base_capacity

        # Convert to percentage and apply
        new_percentage = (new_scaling - 1.0) * 100
        self.reversible_specific_capacity_scaling_percentage = new_percentage

    @reference.setter
    def reference(self, reference: str):
        self.validate_electrochemical_reference(reference)
        self._reference = reference

    @reversible_specific_capacity_scaling_percentage.setter
    @calculate_all_properties
    def reversible_specific_capacity_scaling_percentage(self, percentage: Optional[float]):
        """
        Set the reversible capacity scaling percentage.

        :param percentage: float: percentage adjustment for reversible capacity (e.g., 10 for 10% increase, -10 for 10% decrease)
        """
        if percentage is None:
            self._reversible_specific_capacity_scaling = None
            return

        # validate input - percentage can be negative, zero, or positive
        if not isinstance(percentage, (int, float)):
            raise TypeError("Reversible capacity scaling percentage must be a number")

        # convert percentage to scaling factor (multiplier)
        scaling = 1.0 + (percentage / 100.0)
        
        # apply the scaling factor
        self._reversible_specific_capacity_scaling = scaling

    @voltage_cutoff.setter
    @calculate_all_properties
    def voltage_cutoff(self, voltage: Optional[float]) -> None:
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
            self._voltage_cutoff = None
            return
            
        else:
            self.validate_number(voltage, "Voltage cutoff")
            self._voltage_cutoff = voltage
            return 
        
    @irreversible_specific_capacity_scaling_percentage.setter
    @calculate_all_properties
    def irreversible_specific_capacity_scaling_percentage(self, percentage: Optional[float]):
        """
        Set the irreversible capacity scaling percentage.

        :param percentage: float: percentage adjustment for irreversible capacity (e.g., 10 for 10% increase, -10 for 10% decrease)
        """
        if percentage is None:
            self._irreversible_specific_capacity_scaling = None
            return
        
        # validate input - percentage can be negative, zero, or positive
        if not isinstance(percentage, (int, float)):
            raise TypeError("Irreversible capacity scaling percentage must be a number")

        # convert percentage to scaling factor (multiplier)
        scaling = 1.0 + (percentage / 100.0)
        
        # apply the scaling factor
        self._irreversible_specific_capacity_scaling = scaling

    @specific_capacity_curves.setter
    @calculate_all_properties
    def specific_capacity_curves(self, specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame]) -> None:

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
                .map({"charge": 1, "discharge": -1, "Charge": 1, "Discharge": -1})  # type: ignore[arg-type]
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

    @extrapolation_window.setter
    @calculate_all_properties
    def extrapolation_window(self, window: Optional[float]):

        if window is None:
            self._extrapolation_window = None
            return

        # validate input
        self.validate_positive_float(window, "Extrapolation window")

        # set the extrapolation window
        self._extrapolation_window = abs(float(window))


class CathodeMaterial(_ActiveMaterial):
    """Cathode active material with half-cell voltage-capacity curve data.

    Inherits capacity curve processing from ``_ActiveMaterial`` and adds
    cathode-specific voltage cutoff handling.
    """

    _table_name = "cathode_materials"

    def __init__(
        self,
        name: str,
        reference: str,
        specific_cost: float,
        density: float,
        specific_capacity_curves: Union[List[pd.DataFrame], pd.DataFrame],
        color: str = "#2c2c2c",
        voltage_cutoff: Optional[float] = None,
        extrapolation_window: float = 0.4,
        reversible_specific_capacity_scaling_percentage: float = 0.0,
        irreversible_specific_capacity_scaling_percentage: float = 0.0,
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
        reversible_specific_capacity_scaling_percentage : float
            Percentage adjustment for the reversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
        irreversible_specific_capacity_scaling_percentage : float
            Percentage adjustment for the irreversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
        """
        super().__init__(
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            specific_capacity_curves=specific_capacity_curves,
            color=color,
            extrapolation_window=extrapolation_window,
            reversible_specific_capacity_scaling_percentage=reversible_specific_capacity_scaling_percentage,
            irreversible_specific_capacity_scaling_percentage=irreversible_specific_capacity_scaling_percentage,
            volume=volume,
            mass=mass,
            **kwargs,
        )

        self.voltage_cutoff = voltage_cutoff
        self._calculate_all_properties()
        self._update_properties = True

    @property
    def minimum_extrapolated_voltage(self) -> Optional[float]:
        """
        Get the minimum extrapolated voltage for the half cell curves.

        :return: float: minimum extrapolated voltage of the half cell curves
        """
        try:
            return float(round(self._minimum_extrapolated_voltage, 2))  # type: ignore[attr-defined]
        except Exception:
            return None


class AnodeMaterial(_ActiveMaterial):
    """Anode active material with half-cell voltage-capacity curve data.

    Inherits capacity curve processing from ``_ActiveMaterial`` and adds
    anode-specific voltage cutoff handling.
    """

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
        reversible_specific_capacity_scaling_percentage: float = 0.0,
        irreversible_specific_capacity_scaling_percentage: float = 0.0,
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
        extrapolation_window : float
            The positive voltage extrapolation window in V. This is the amount of voltage above the maximum voltage of the half cell curves that will be used for extrapolation.
            This is useful for anode materials where the voltage can go above 0V, e.g., for Li-ion batteries.
        reversible_specific_capacity_scaling_percentage : float
            Percentage adjustment for the reversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
        irreversible_specific_capacity_scaling_percentage : float
            Percentage adjustment for the irreversible capacity of the material. Default is 0.0 (no change). Positive values increase capacity (e.g., 10 = 10% increase), negative values decrease it (e.g., -10 = 10% decrease).
        """
        super().__init__(
            name=name,
            reference=reference,
            specific_cost=specific_cost,
            density=density,
            specific_capacity_curves=specific_capacity_curves,
            color=color,
            extrapolation_window=extrapolation_window,
            reversible_specific_capacity_scaling_percentage=reversible_specific_capacity_scaling_percentage,
            irreversible_specific_capacity_scaling_percentage=irreversible_specific_capacity_scaling_percentage,
            volume=volume,
            mass=mass,
            **kwargs,
        )

        self._calculate_all_properties()
        self._update_properties = True


