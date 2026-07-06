# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base class for electrode assemblies."""

from steer_opencell_design.Constructions.Layups.Base import _Layup
from steer_opencell_design.Utils.Constants import COLOR_FULL_CELL
from steer_core.Utils import round_dict_recursive

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Datum import DatumMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Data import DataMixin
from steer_core.Mixins.Propagation import PropagationMixin, propagating_setter

from steer_core.Decorators.General import calculate_all_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_core.Constants.Units import *

from abc import ABC, abstractmethod
from copy import deepcopy
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Any, Dict, Tuple


# Constants for curve calculations
CHARGE_DIRECTION = 1
DISCHARGE_DIRECTION = -1
CAPACITY_COL = 0
VOLTAGE_COL = 1
DIRECTION_COL = 2


class _ElectrodeAssembly(
    ABC,
    CoordinateMixin,
    DatumMixin,
    ValidationMixin, 
    PropagationMixin,
    SerializerMixin, 
    ColorMixin, 
    DunderMixin,
    PlotterMixin,
    DataMixin,
):
    """Abstract base class for electrode assemblies (jelly rolls, stacks). Provides common properties for mass, cost, pore volume, and capacity curves, as well as visualization methods for breakdowns and capacity plots."""
    
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
        
        # Initialize _datum early; will be properly set from layup or calculated later
        self._datum = (0.0, 0.0, 0.0)
        
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
        self._calculate_capacity_curves()
        
    def _calculate_bulk_properties(self):
        """Calculate pore volume, mass, and cost from the layup."""
        self._calculate_pore_volume()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    @abstractmethod
    def _calculate_pore_volume(self):
        """Calculate total pore volume of the assembly (implemented by subclasses)."""
        self._pore_volume = 0.0
        pass

    @abstractmethod
    def _calculate_mass_properties(self) -> None:
        """Calculate mass properties of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_cost_properties(self) -> None:
        """Calculate cost properties of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_geometry_parameters(self) -> None:
        """Calculate geometry parameters of the electrode assembly."""
        pass

    @abstractmethod
    def _calculate_interfacial_area(self) -> None:
        """Calculate the interfacial area between anode and cathode."""
        pass

    def _calculate_capacity_curves(self):
        """Calculate full cell voltage curve of the electrode assembly.
        
        Uses .copy() instead of deepcopy() for numpy arrays as we only need
        shallow copies for scaling operations - significantly faster.
        """
        # Initialize to None so anode-free (where anode curve is absent) doesn't crash
        self._capacity_curve = None
        self._cathode_capacity_curve = None
        self._anode_capacity_curve = None

        if self._layup._areal_capacity_curve is not None:
            _capacity_curve = self._layup._areal_capacity_curve.copy()
            _capacity_curve[:, 0] *= self._interfacial_area
            self._capacity_curve = _capacity_curve

        if self._layup._cathode._areal_capacity_curve is not None:
            _cathode_capacity_curve = self._layup._cathode._areal_capacity_curve.copy()
            _cathode_capacity_curve[:, 0] *= self._interfacial_area
            self._cathode_capacity_curve = _cathode_capacity_curve

        if self._layup._anode._areal_capacity_curve is not None:
            _anode_capacity_curve = self._layup._anode._areal_capacity_curve.copy()
            _anode_capacity_curve[:, 0] *= self._interfacial_area
            self._anode_capacity_curve = _anode_capacity_curve

        return self._capacity_curve, self._cathode_capacity_curve, self._anode_capacity_curve
    
    def _clear_cached_data(self) -> None:
        """Clear cached capacity curves and downstream formulation caches."""

        self._capacity_curve = None
        self._cathode_capacity_curve = None
        self._anode_capacity_curve = None

        self._layup._areal_capacity_curve = None

        self._layup.cathode._areal_capacity_curve = None
        self._layup.anode._areal_capacity_curve = None
        
        self._layup.cathode._formulation._clear_cached_data()
        if not self._layup.anode._is_anode_free:
            self._layup.anode._formulation._clear_cached_data()

    def plot_mass_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        """Generate a sunburst mass breakdown chart."""
        fig = self.plot_breakdown_sunburst(
            self.mass_breakdown,
            title=title or f"{self.name} Mass Breakdown",
            unit="g",
            **kwargs,
        )

        return fig

    def plot_cost_breakdown(self, title: str = None, **kwargs) -> go.Figure:
        """Generate a sunburst cost breakdown chart."""
        fig = self.plot_breakdown_sunburst(
            self.cost_breakdown,
            title=title or f"{self.name} Cost Breakdown",
            unit="$",
            **kwargs,
        )

        return fig

    def plot_capacity_curve(self, **kwargs) -> go.Figure:
        """
        Generate capacity plot for the assembly.

        Parameters
        ----------
        **kwargs
            Additional plotting parameters for customization

        Returns
        -------
        go.Figure
            Plotly figure with capacity curves

        Raises
        ------
        ValueError
            If half-cell data is missing or invalid
        """
        fig = go.Figure()

        traces = [
            self.cathode_capacity_curve_trace,
            self.anode_capacity_curve_trace,
            self.capacity_curve_trace
        ]

        # Filter out None traces (e.g. anode-free has no anode curve trace)
        traces = [t for t in traces if t is not None]

        fig.add_traces(traces)    

        return self.apply_plot_layout(
            fig,
            defaults={
                "title": f"{self.name} — Capacity Curves",
                "paper_bgcolor": "white",
                "plot_bgcolor": "white",
                "xaxis": {**self.SCATTER_X_AXIS, "title": "Capacity (Ah)"},
                "yaxis": {
                    **self.SCATTER_Y_AXIS,
                    "title": "Voltage (V)",
                    "rangemode": "tozero",
                },
                "hovermode": "closest",
            },
            overrides=kwargs,
        )

    @property
    def pore_volume(self) -> float:
        """Return the pore volume of the electrode assembly."""
        return self._pore_volume * M_TO_CM**3

    @property
    def name(self) -> str:
        """Return the name of the electrode assembly."""
        return self._name

    @property
    def interfacial_area(self) -> float:
        """Return the interfacial area of the electrode assembly in cm²."""
        return self._interfacial_area * M_TO_CM**2

    @property
    def layup(self) -> _Layup:
        """Return the underlying `_Layup` instance."""
        return self._layup
    
    @property
    def capacity_curve(self) -> pd.DataFrame:
        """Get the full-cell capacity curve as a DataFrame."""
        if self._capacity_curve is None:
            return None

        curve = self._capacity_curve.copy()
        direction = np.where(curve[:, DIRECTION_COL] == 1, "charge", "discharge")
        capacity = curve[:, CAPACITY_COL] * S_TO_H
        voltage = curve[:, VOLTAGE_COL]

        return pd.DataFrame({
            "Capacity (Ah)": capacity,
            "Voltage (V)": voltage,
            "Direction": direction
        })
    
    @property
    def capacity_curve_trace(self) -> go.Scatter:
        """Get the Plotly trace for the full-cell capacity curve."""
        if self._capacity_curve is None:
            return None

        return go.Scatter(
            x=self.capacity_curve["Capacity (Ah)"],
            y=self.capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Full-Cell",
            line=dict(color=COLOR_FULL_CELL, width=3),  # Slightly thicker for emphasis
            customdata=self.capacity_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} Ah<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def anode_capacity_curve(self) -> pd.DataFrame:
        """Get the anode capacity curve as a DataFrame."""
        if self.layup.anode._is_anode_free or self.layup.anode.formulation is None:
            return None

        if self._anode_capacity_curve is None:
            return None

        curve = self._anode_capacity_curve.copy()
        direction = np.where(curve[:, DIRECTION_COL] == 1, "charge", "discharge")
        capacity = curve[:, CAPACITY_COL] * S_TO_H
        voltage = curve[:, VOLTAGE_COL]

        return pd.DataFrame({
            "Capacity (Ah)": capacity,
            "Voltage (V)": voltage,
            "Direction": direction
        })
    
    @property
    def anode_capacity_curve_trace(self) -> go.Scatter:
        """Get the Plotly trace for the anode capacity curve."""
        if self.layup.anode._is_anode_free or self.layup.anode.formulation is None:
            return None

        if self._anode_capacity_curve is None:
            return None

        return go.Scatter(
            x=self.anode_capacity_curve["Capacity (Ah)"],
            y=self.anode_capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.anode.name} Half-Cell",
            line=dict(color=self.layup.anode.formulation.color, width=2.5),
            customdata=self.anode_capacity_curve["Direction"],
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} Ah<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cathode_capacity_curve(self) -> pd.DataFrame:
        """Get the cathode capacity curve as a DataFrame."""
        if self._cathode_capacity_curve is None:
            return None

        curve = self._cathode_capacity_curve.copy()
        direction = np.where(curve[:, DIRECTION_COL] == 1, "charge", "discharge")
        capacity = curve[:, CAPACITY_COL] * S_TO_H
        voltage = curve[:, VOLTAGE_COL]

        return pd.DataFrame({
            "Capacity (Ah)": capacity,
            "Voltage (V)": voltage,
            "Direction": direction
        })
    
    @property
    def cathode_capacity_curve_trace(self) -> go.Scatter:
        """Get the Plotly trace for the cathode capacity curve."""
        if self._cathode_capacity_curve is None:
            return None

        return go.Scatter(
            x=self.cathode_capacity_curve["Capacity (Ah)"],
            y=self.cathode_capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self.layup.cathode.name} Half-Cell",
            line=dict(color=self.layup.cathode.formulation.color, width=2.5),
            customdata=self.cathode_capacity_curve["Direction"],
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} Ah<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def cost(self) -> float:
        """Return the cost of the electrode assembly in $."""
        return self._cost

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """
        return round_dict_recursive(self._cost_breakdown, precision=None)

    @property
    def mass(self) -> float:
        """Return the mass of the electrode assembly in g."""
        return self._mass * KG_TO_G

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        return round_dict_recursive(self._mass_breakdown, precision=None, unit_conversion=KG_TO_G)

    # Override datum setter to sync with layup
    @DatumMixin.datum.setter
    def datum(self, value: Tuple[float, float, float]) -> None:
        """Set the datum coordinates of the electrode assembly with validation."""
        self.validate_datum(value)
        self._layup.datum = value
        self._datum = tuple(float(v) * MM_TO_M for v in value)

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the electrode assembly with validation."""
        self.validate_string(value, "name")
        self._name = value

    @layup.setter
    @calculate_all_properties
    @propagating_setter()
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

