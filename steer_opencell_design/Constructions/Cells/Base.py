from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly
from steer_opencell_design.Components.Containers.Base import _Container
from steer_opencell_design.Utils.Decorators import calculate_electrochemical_properties

from steer_opencell_design.Components.Materials.Electrolytes import Electrolyte

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Data import DataMixin

from steer_core.Decorators.General import calculate_all_properties

from steer_core.Constants.Units import *

from abc import ABC, abstractmethod
from copy import deepcopy
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Any, Dict


class _Cell(
    ABC,
    DunderMixin,
    ValidationMixin,
    ColorMixin,
    PlotterMixin,
    SerializerMixin,
    DataMixin,
    CoordinateMixin,
):

    def __init__(
        self,
        reference_electrode_assembly: _ElectrodeAssembly,
        encapsulation: _Container,
        n_electrode_assembly: int,
        electrolyte: Electrolyte,
        electrolyte_overfill: float,
        operating_voltage_window: tuple[float, float],
        name: str = "Cell",
    ):
        self._update_properties = False

        self.reference_electrode_assembly = reference_electrode_assembly
        self.encapsulation = encapsulation
        self.n_electrode_assembly = n_electrode_assembly
        self.electrolyte = electrolyte
        self.electrolyte_overfill = electrolyte_overfill
        self.operating_voltage_window = operating_voltage_window
        self.name = name
    
    def _calculate_all_properties(self) -> None:
        self._make_assemblies()
        self._calculate_bulk_properties()
        self._calculate_electrochemical_properties()

    def _calculate_bulk_properties(self) -> None:
        self._calculate_electrolyte_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_electrolyte_properties(self) -> None:
        _pore_volume = sum([ea._pore_volume for ea in self._electrode_assemblies])
        _electrolyte_volume = _pore_volume * (1 + self.electrolyte_overfill)
        electrolyte_volume = _electrolyte_volume * M_TO_CM**3
        self._electrolyte.volume = electrolyte_volume

    def _calculate_electrochemical_properties(self) -> None:
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        self._calculate_energy_properties()

    def _calculate_curves(self) -> None:
        self._calculate_full_cell_curve()
        self._calculate_cathode_curve()
        self._calculate_anode_curve()

    def _calculate_voltage_limits(self) -> None:

        # copy the layup
        layup = deepcopy(self._reference_electrode_assembly._layup)

        # modify the cathode formulation voltage to have its maximum voltage
        layup._cathode._formulation.voltage_cutoff = layup._cathode._formulation.voltage_cutoff_range[1]
        layup._cathode.formulation = layup._cathode._formulation
        layup.cathode = layup._cathode
        max_voltage = layup._full_cell_curve[:, 1].max()

        # modify the cathode formulation voltage to have its minimum voltage
        layup._cathode._formulation.voltage_cutoff = layup._cathode._formulation.voltage_cutoff_range[0]
        layup._cathode.formulation = layup._cathode._formulation
        layup.cathode = layup._cathode
        min_voltage = layup._full_cell_curve[:, 1].max()

        _minimum_operating_voltage = self._reference_electrode_assembly._layup._full_cell_curve[:, 1].min()
        _minimum_operating_voltage_top_limit = _minimum_operating_voltage + (min_voltage - _minimum_operating_voltage) / 2

        self._maximum_operating_voltage_range = (min_voltage, max_voltage)
        self._minimum_operating_voltage_range = (_minimum_operating_voltage, _minimum_operating_voltage_top_limit)

    def _make_assemblies(self) -> None:
        # Create the electrode assemblies based on the reference assembly and number of assemblies
        self._electrode_assemblies = [
            deepcopy(self.reference_electrode_assembly)
            for _ in range(self.n_electrode_assembly)
        ]

    def _calculate_full_cell_curve(self) -> None:
        
        # get the full cell curve from the reference electrode assembly and scale it by the number of assemblies
        _full_cell_curve = self._reference_electrode_assembly._full_cell_curve
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * self._n_electrode_assembly
        
        # cut the discharge curve off at the self._minimum_operating_voltage
        _charge_curve = _full_cell_curve[_full_cell_curve[:, 2] == 1]
        _discharge_curve = _full_cell_curve[_full_cell_curve[:, 2] == -1]
        
        # add a point in the discharge curve where voltage equals self._minimum_operating_voltage
        _min_op_voltage = self._minimum_operating_voltage

        # find the indices surrounding the min operating voltage
        above_idx = np.where(_discharge_curve[:, 1] >= _min_op_voltage)[0][-1]
        below_idx = np.where(_discharge_curve[:, 1] <= _min_op_voltage)[0][0]

        # linear interpolation to find the capacity at min operating voltage
        v1, c1 = _discharge_curve[above_idx, 1], _discharge_curve[above_idx, 0]
        v2, c2 = _discharge_curve[below_idx, 1], _discharge_curve[below_idx, 0]

        slope = (c2 - c1) / (v2 - v1)
        c_min_op = c1 + slope * (_min_op_voltage - v1)

        # create new point
        new_point = np.array([[c_min_op, _min_op_voltage, -1]])

        # insert the new point into the discharge curve
        _discharge_curve = np.vstack((_discharge_curve[:below_idx], new_point))

        # recombine the charge and discharge curves
        _full_cell_curve = np.vstack((_charge_curve, _discharge_curve))

        self._full_cell_curve = _full_cell_curve

        return self._full_cell_curve

    def _calculate_cathode_curve(self) -> None:

        # do the same for cathode half cell curve
        _cathode_half_cell_curve = self._reference_electrode_assembly._cathode_half_cell_curve
        _cathode_half_cell_curve[:, 0] = _cathode_half_cell_curve[:, 0] * self._n_electrode_assembly

        self._cathode_half_cell_curve = _cathode_half_cell_curve

        return self._cathode_half_cell_curve

    def _calculate_anode_curve(self) -> None:

        # do the same for the anode half cell curve
        _anode_half_cell_curve = self._reference_electrode_assembly._anode_half_cell_curve
        _anode_half_cell_curve[:, 0] = _anode_half_cell_curve[:, 0] * self._n_electrode_assembly
        
        self._anode_half_cell_curve = _anode_half_cell_curve

        return self._anode_half_cell_curve

    def _calculate_reversible_capacity(self) -> None:
        pass

    def _calculate_irreversible_capacity(self) -> None:

        # get the anode and cathode half cell curves
        _cathode_curve = self._cathode_half_cell_curve.copy()
        _anode_curve = self._anode_half_cell_curve.copy()

        # get the discharge curve
        _cathode_discharge_curve = _cathode_curve[_cathode_curve[:, 2] == -1]
        _anode_discharge_curve = _anode_curve[_anode_curve[:, 2] == -1]

        # order them by the capacity column
        _cathode_discharge_curve = _cathode_discharge_curve[np.argsort(_cathode_discharge_curve[:, 0])]
        _anode_discharge_curve = _anode_discharge_curve[np.argsort(_anode_discharge_curve[:, 0])]

        # find the capacity at which the cathode and anode curves intersect using np.interp
        _cathode_capacity = _cathode_discharge_curve[:, 0]
        _anode_capacity = _anode_discharge_curve[:, 0]
        _cathode_voltage = _cathode_discharge_curve[:, 1]
        _anode_voltage = _anode_discharge_curve[:, 1]
        _crossing_capacity = np.interp(0, _cathode_voltage - _anode_voltage, _cathode_capacity)

        self._irreversible_capacity = _crossing_capacity

    def _calculate_mass_properties(self) -> tuple[float, Dict]:
        
        _assembly_mass = sum([assembly._mass for assembly in self._electrode_assemblies])
        _electrolyte_mass = self._electrolyte._mass
        _encapsulation_mass = self._encapsulation._mass

        self._mass = _assembly_mass + _electrolyte_mass + _encapsulation_mass

        self._mass_breakdown = {
            "Electrode Assemblies": self.sum_breakdowns(self._electrode_assemblies, "mass"),
            "Electrolyte": _electrolyte_mass,
            "Encapsulation": self._encapsulation._mass_breakdown,
        }

        return self._mass, self._mass_breakdown

    def _calculate_cost_properties(self) -> tuple[float, Dict]:
        
        _assembly_cost = sum([assembly._cost for assembly in self._electrode_assemblies])
        _electrolyte_cost = self._electrolyte._cost
        _encapsulation_cost = self._encapsulation._cost

        self._cost = _assembly_cost + _electrolyte_cost + _encapsulation_cost

        self._cost_breakdown = {
            "Electrode Assemblies": self.sum_breakdowns(self._electrode_assemblies, "cost"),
            "Electrolyte": _electrolyte_cost,
            "Encapsulation": self._encapsulation._cost_breakdown,
        }

        return self._cost, self._cost_breakdown

    def _calculate_energy_properties(self) -> tuple[float, Dict]:
        pass

    def get_capacity_plot(self, **kwargs) -> go.Figure:
        """
        Generate capacity plot for the assembly.

        Parameters
        ----------
        **kwargs
            Additional plotting parameters for customization

        Returns
        -------
        go.Figuren
            Plotly figure with capacity curves

        Raises
        ------
        ValueError
            If half-cell data is missing or invalid
        """
        fig = go.Figure()

        traces = [
            self.cathode_half_cell_curve_trace,
            self.anode_half_cell_curve_trace,
            self.full_cell_curve_trace
        ]

        fig.add_traces(traces)

        # # add vline at the irreversible capacity
        # fig.add_vline(
        #     x=self.irreversible_capacity,
        #     line=dict(color="red", width=2, dash="dash"),
        #     annotation_text=f"Irreversible Capacity: {self.irreversible_capacity:.2f} Ah",
        #     annotation_position="top right",
        #     annotation_font=dict(color="red", size=12),
        # )

        # Enhanced layout with zero lines and faint grid
        fig.update_layout(
            title=kwargs.get("title", f"Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Capacity (Ah)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
        )

        return fig
        
    def plot_mass_breakdown(self, title: str = None, **kwargs) -> go.Figure:

        fig = self.plot_breakdown_sunburst(
            self.mass_breakdown,
            title=title or f"{self.name} Mass Breakdown",
            unit="g",
            **kwargs,
        )

        return fig

    def plot_cost_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        
        fig = self.plot_breakdown_sunburst(
            self.cost_breakdown,
            title=title or f"{self.name} Cost Breakdown",
            unit="$",
            **kwargs,
        )

        return fig

    # ------------------------------------------------------------------
    # Properties with validation-backed setters
    # ------------------------------------------------------------------

    @property
    def maximum_operating_voltage_range(self) -> tuple[float, float]:

        return (
            round(self._maximum_operating_voltage_range[0], 2),
            round(self._maximum_operating_voltage_range[1], 2),
        )
    
    @property
    def minimum_operating_voltage_range(self) -> tuple[float, float]:

        return (
            round(self._minimum_operating_voltage_range[0], 2),
            round(self._minimum_operating_voltage_range[1], 2),
        )

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """

        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj, 2)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj * KG_TO_G, 2)

        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def irreversible_capacity(self) -> float:
        return round(self._irreversible_capacity * S_TO_H, 2)

    @property
    def full_cell_curve(self) -> pd.DataFrame:

        _full_cell_curve = self._full_cell_curve
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * S_TO_H

        # add the end of the charge curve for spline interpolation
        _charge_curve = _full_cell_curve[_full_cell_curve[:, 2] == 1]
        _discharge_curve = _full_cell_curve[_full_cell_curve[:, 2] == -1]
        _cahrge_curve = np.vstack((_charge_curve, _charge_curve[-1, :]))
        _full_cell_curve = np.vstack((_cahrge_curve, _discharge_curve))

        return (
            pd
            .DataFrame(_full_cell_curve, columns=["Capacity (Ah)", "Voltage (V)", "Direction"])
            .assign(direction=lambda x: np.where(x["Direction"] == 1, "charge", "discharge"))
            .round(4)
        )
    
    @property
    def full_cell_curve_trace(self) -> go.Scatter:

        full_cell_color = "#ff8c00"

        return go.Scatter(
            x=self.full_cell_curve["Capacity (Ah)"],
            y=self.full_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Full-Cell",
            line=dict(color=full_cell_color, width=3, shape='spline'),  # Slightly thicker for emphasis
            customdata=self.full_cell_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def anode_half_cell_curve(self) -> pd.DataFrame:

        _anode_half_cell = self._anode_half_cell_curve
        _anode_half_cell[:, 0] = _anode_half_cell[:, 0] * S_TO_H

        # add the end of the charge curve for spline interpolation
        _charge_curve = _anode_half_cell[_anode_half_cell[:, 2] == 1]
        _discharge_curve = _anode_half_cell[_anode_half_cell[:, 2] == -1]
        _cahrge_curve = np.vstack((_charge_curve, _charge_curve[-1, :]))
        _anode_half_cell = np.vstack((_cahrge_curve, _discharge_curve))

        return (
            pd
            .DataFrame(_anode_half_cell, columns=["Capacity (Ah)", "Voltage (V)", "Direction"])
            .assign(direction=lambda x: np.where(x["Direction"] == 1, "charge", "discharge"))
            .round(4)
        )
    
    @property
    def anode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_half_cell_curve["Capacity (Ah)"],
            y=self.anode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self._reference_electrode_assembly._layup._anode.name} Half-Cell",
            line=dict(color=self._reference_electrode_assembly._layup._anode.formulation.color, width=2, shape='spline'),
            customdata=self.anode_half_cell_curve["Direction"],
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cathode_half_cell_curve(self) -> pd.DataFrame:

        _cathode_half_cell = self._cathode_half_cell_curve
        _cathode_half_cell[:, 0] = _cathode_half_cell[:, 0] * S_TO_H

        # add the end of the charge curve for spline interpolation
        _charge_curve = _cathode_half_cell[_cathode_half_cell[:, 2] == 1]
        _discharge_curve = _cathode_half_cell[_cathode_half_cell[:, 2] == -1]
        _cahrge_curve = np.vstack((_charge_curve, _charge_curve[-1, :]))
        _cathode_half_cell = np.vstack((_cahrge_curve, _discharge_curve))
        
        return (
            pd
            .DataFrame(_cathode_half_cell, columns=["Capacity (Ah)", "Voltage (V)", "Direction"])
            .assign(direction=lambda x: np.where(x["Direction"] == 1, "charge", "discharge"))
            .round(4)
        )
    
    @property
    def cathode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_half_cell_curve["Capacity (Ah)"],
            y=self.cathode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self._reference_electrode_assembly._layup._cathode.name} Half-Cell",
            line=dict(color=self._reference_electrode_assembly._layup._cathode.formulation.color, width=2, shape='spline'),
            customdata=self.cathode_half_cell_curve["Direction"],
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def reference_electrode_assembly(self) -> _ElectrodeAssembly:
        return self._reference_electrode_assembly

    @property
    def encapsulation(self) -> _Container:
        return self._encapsulation

    @property
    def n_electrode_assembly(self) -> int:
        return self._n_electrode_assembly

    @property
    def electrolyte(self) -> Electrolyte:
        return self._electrolyte

    @property
    def electrolyte_overfill(self) -> float:
        return self._electrolyte_overfill

    @property
    def reversible_capacity(self) -> float:
        return self._reversible_capacity

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def electrode_assemblies(self) -> list[_ElectrodeAssembly]:
        return self._electrode_assemblies
    
    @property
    def operating_voltage_window(self) -> tuple[float, float]:

        return (
            round(self._operating_voltage_window[0], 2),
            round(self._operating_voltage_window[1], 2),
        )
    
    @property
    def maximum_operating_voltage(self) -> float:
        return round(self._operating_voltage_window[1], 2)
    
    @property
    def minimum_operating_voltage(self) -> float:
        return round(self._operating_voltage_window[0], 2)

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------

    @operating_voltage_window.setter
    def operating_voltage_window(self, value: tuple[float, float]) -> None:
        self.validate_positive_float(value[0], "operating_voltage_window[0]")
        self.validate_positive_float(value[1], "operating_voltage_window[1]")
        self.minimum_operating_voltage = value[0]
        self.maximum_operating_voltage = value[1]
        self._operating_voltage_window = value

    @minimum_operating_voltage.setter
    @calculate_electrochemical_properties
    def minimum_operating_voltage(self, value: float) -> None:
        
        # validate positive float
        self.validate_positive_float(value, "minimum_operating_voltage")
        
        # if below minimum value set to minimum
        if value < self.minimum_operating_voltage_range[0]:
            self._minimum_operating_voltage = self.minimum_operating_voltage_range[0]
        # elif above maximum value set to maximum
        elif value > self.minimum_operating_voltage_range[1]:
            self._minimum_operating_voltage = self.minimum_operating_voltage_range[1]
        # else set to value
        else:
            self._minimum_operating_voltage = value

    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: _ElectrodeAssembly) -> None:
        self.validate_type(value, _ElectrodeAssembly, "reference_electrode_assembly")
        self._reference_electrode_assembly = value
        self._calculate_voltage_limits()

    @encapsulation.setter
    @calculate_all_properties
    def encapsulation(self, value: _Container) -> None:
        self.validate_type(value, _Container, "encapsulation")
        self._encapsulation = value

    @n_electrode_assembly.setter
    @calculate_all_properties
    def n_electrode_assembly(self, value: int) -> None:
        self.validate_positive_int(value, "n_electrode_assembly")
        self._n_electrode_assembly = value

    @electrolyte.setter
    @calculate_all_properties
    def electrolyte(self, value: Electrolyte) -> None:
        self.validate_type(value, Electrolyte, "electrolyte")
        self._electrolyte = value

    @electrolyte_overfill.setter
    @calculate_all_properties
    def electrolyte_overfill(self, value: float) -> None:
        self.validate_percentage(value, "electrolyte_overfill")
        self._electrolyte_overfill = value

    @name.setter
    def name(self, value: str) -> None:
        self.validate_string(value, "name")
        self._name = value









