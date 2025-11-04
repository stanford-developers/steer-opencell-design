from steer_opencell_design.Constructions.Layups.Base import _Layup

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


# Constants for curve calculations
CHARGE_DIRECTION = 1
DISCHARGE_DIRECTION = -1
CAPACITY_COL = 0
VOLTAGE_COL = 1
DIRECTION_COL = 2


class _ElectrodeAssembly(
    ABC,
    CoordinateMixin, 
    ValidationMixin, 
    SerializerMixin, 
    ColorMixin, 
    DunderMixin,
    PlotterMixin,
    DataMixin
):
    
    def __init__(
            self,
            layup: _Layup,
            name: str = "Electrode Assembly"
        ) -> None:
        """
        Initialize the electrode assembly.
        
        Parameters
        ----------
        layup : _Layup
            The layup configuration for the electrode assembly
        name : str, optional
            Name identifier for the assembly, by default "Electrode Assembly"
            
        Raises
        ------
        ValueError
            If layup is invalid or None
        """
        self._update_properties = False
        self.layup = layup
        self.name = name

    def _calculate_all_properties(self) -> None:
        """
        Calculate all properties of the electrode assembly.
        
        This method orchestrates the calculation of all derived properties
        in the correct order to handle dependencies.
        """
        self._calculate_bulk_properties()
        self._calculate_interfacial_area()
        self._calculate_full_cell_curve()
        self._calculate_energy()
        
    def _ensure_properties_calculated(self) -> None:
        """Ensure all properties have been calculated before access."""
        if not hasattr(self, '_energy') or self._energy is None:
            self._calculate_all_properties()

    def _calculate_bulk_properties(self):
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_energy(self):
        discharge_curve = self._full_cell_curve[self._full_cell_curve[:,2] == -1]
        discharge_curve = discharge_curve[np.argsort(discharge_curve[:,0])]
        capacity = discharge_curve[:,0]
        voltage = discharge_curve[:,1]
        energy = np.trapz(capacity, voltage)
        self._energy = energy
        return self._energy

    @abstractmethod
    def _calculate_mass_properties(self):
        """Calculate mass properties of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_cost_properties(self):
        """Calculate cost properties of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_geometry_parameters(self):
        """Calculate geometry parameters of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_interfacial_area(self):
        """Calculate the interfacial area between anode and cathode."""
        pass

    def _calculate_full_cell_curve(self):
        """Calculate full cell voltage curve of the electrode assembly."""
        _full_cell_curve = deepcopy(self._layup._full_cell_curve)
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * self._interfacial_area
        self._full_cell_curve = _full_cell_curve

        # also calculate half-cell curve for cathode
        _cathode_half_cell_curve = deepcopy(self._layup._cathode._half_cell_curve)
        _cathode_half_cell_curve[:, 4] = _cathode_half_cell_curve[:, 4] * self._interfacial_area
        self._cathode_half_cell_curve = np.column_stack([_cathode_half_cell_curve[:,4], _cathode_half_cell_curve[:,1], _cathode_half_cell_curve[:,2]])

        # also calculate half-cell curve for anode
        _anode_half_cell_curve = deepcopy(self._layup._anode._half_cell_curve)
        _anode_half_cell_curve[:, 4] = _anode_half_cell_curve[:, 4] * self._interfacial_area
        self._anode_half_cell_curve = np.column_stack([_anode_half_cell_curve[:,4], _anode_half_cell_curve[:,1], _anode_half_cell_curve[:,2]])

        return self._full_cell_curve, self._cathode_half_cell_curve, self._anode_half_cell_curve
    
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

        fig.add_trace(self.cathode_half_cell_curve_trace)
        fig.add_trace(self.anode_half_cell_curve_trace)
        fig.add_trace(self.full_cell_curve_trace)

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

    @property
    def energy(self) -> float:
        """
        Return the energy of the electrode assembly in Wh.
        
        Returns
        -------
        float
            Energy in watt-hours (Wh)
        """
        self._ensure_properties_calculated()
        return round(self._energy * J_TO_WH, 2)

    @property
    def name(self) -> str:
        """Return the name of the electrode assembly."""
        return self._name

    @property
    def interfacial_area(self) -> float:
        """Return the interfacial area of the electrode assembly in cm²."""
        return round(self._interfacial_area * M_TO_CM**2, 2)

    @property
    def layup(self) -> _Layup:
        """Return the underlying `_Layup` instance."""
        return self._layup
    
    @property
    def full_cell_curve(self) -> pd.DataFrame:

        return (
            pd.DataFrame(
                self._full_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                    "capacity": "Capacity (Ah)",
                }
            )
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
            line=dict(color=full_cell_color, width=3),  # Slightly thicker for emphasis
            customdata=self.full_cell_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def anode_half_cell_curve(self) -> pd.DataFrame:

        return (
            pd
            .DataFrame(
                self._anode_half_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "capacity": "Capacity (Ah)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
        )
    
    @property
    def anode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_half_cell_curve["Capacity (Ah)"],
            y=self.anode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.anode.name} Half-Cell",
            line=dict(color=self.layup.anode.formulation.color, width=2.5),
            customdata=self.anode_half_cell_curve["Direction"],
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cathode_half_cell_curve(self) -> pd.DataFrame:
        
        return (
            pd
            .DataFrame(
                self._cathode_half_cell_curve,
                columns=["capacity", "voltage", "direction"],
            )
            .assign(
                direction=lambda x: np.where(x["direction"] == 1, "charge", "discharge"),
                capacity=lambda x: x["capacity"] * (S_TO_H),
            )
            .rename(
                columns={
                    "capacity": "Capacity (Ah)",
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                }
            )
        )
    
    @property
    def cathode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_half_cell_curve["Capacity (Ah)"],
            y=self.cathode_half_cell_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.cathode.name} Half-Cell",
            line=dict(color=self.layup.cathode.formulation.color, width=2.5),
            customdata=self.cathode_half_cell_curve["Direction"],
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cost(self) -> float:
        """Return the cost of the electrode assembly in $."""
        return round(self._cost, 2)

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
    def mass(self) -> float:
        """Return the mass of the electrode assembly in g."""
        return round(self._mass * KG_TO_G, 2)

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

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the electrode assembly with validation."""
        self.validate_string(value, "name")
        self._name = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: _Layup) -> None:
        """
        Set the layup with validation and property recalculation.
        
        Parameters
        ----------
        value : _Layup
            The new layup configuration
            
        Raises
        ------
        ValueError
            If layup is None or invalid
        """
        self.validate_type(value, _Layup, "layup")
        self._layup = value

