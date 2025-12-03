from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly
from steer_opencell_design.Components.Containers.Base import _Container
from steer_opencell_design.Utils.Decorators import calculate_electrochemical_properties

from steer_opencell_design.Materials.Electrolytes import Electrolyte

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
from typing import Any, Dict, Tuple


# Module-level constants for calculations and formatting
VOLTAGE_GUIDE_MARGIN_LOWER = 0.95
VOLTAGE_GUIDE_MARGIN_UPPER = 1.05
CAPACITY_GUIDE_EXTENSION = 1.1

# Precision constants for different property types
MASS_PRECISION = 2
ENERGY_PRECISION = 2
CAPACITY_PRECISION = 2
VOLTAGE_PRECISION = 2
CURVE_PRECISION = 4
COST_PRECISION = 2

# Unit conversion factors
ENERGY_CONVERSION_FACTOR = S_TO_H
VOLUMETRIC_ENERGY_CONVERSION = S_TO_H / M_TO_DM**3
NORMALISED_COST_CONVERSION = 1 / (ENERGY_CONVERSION_FACTOR * W_TO_KW)

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
        operating_voltage_window: Tuple[float, float] = (None, None),
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

    def _calculate_electrochemical_properties(self) -> None:
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        self._calculate_energy_properties()

    def _calculate_curves(self) -> None:
        """Calculate all capacity curves for the cell."""
        self._calculate_capacity_curve()
        self._calculate_cathode_curve()
        self._calculate_anode_curve()

    def _calculate_electrolyte_properties(self) -> None:
        """Calculate electrolyte volume based on pore volume and overfill."""
        _pore_volume = sum([ea._pore_volume for ea in self._electrode_assemblies])
        _electrolyte_volume = _pore_volume * (1 + self.electrolyte_overfill)
        electrolyte_volume = _electrolyte_volume * M_TO_CM**3
        self._electrolyte.volume = electrolyte_volume

    def _make_assemblies(self) -> None:

        # Create the electrode assemblies based on the reference assembly and number of assemblies
        self._electrode_assemblies = [deepcopy(self.reference_electrode_assembly) for _ in range(self.n_electrode_assembly)]

    def _format_curve_for_display(self, curve: np.ndarray, scale_factor: float = S_TO_H) -> pd.DataFrame:
        """Convert raw curve array to formatted DataFrame with spline interpolation point.
        
        Parameters
        ----------
        curve : np.ndarray
            Raw curve array with columns [capacity, voltage, direction]
        scale_factor : float, optional
            Scaling factor for capacity values (default: S_TO_H)
            
        Returns
        -------
        pd.DataFrame
            Formatted DataFrame with columns: Capacity (Ah), Voltage (V), Direction, direction
        """
        curve = curve.copy()
        curve[:, 0] *= scale_factor
        
        # Split into charge and discharge curves
        charge_curve = curve[curve[:, 2] == 1]
        discharge_curve = curve[curve[:, 2] == -1]
        
        # Add end point for spline interpolation
        charge_curve = np.vstack((charge_curve, charge_curve[-1, :]))
        combined_curve = np.vstack((charge_curve, discharge_curve))

        # round curves
        combined_curve = np.round(combined_curve, CURVE_PRECISION)
        
        # Create DataFrame with all columns at once (more efficient)
        return pd.DataFrame({
            "Capacity (Ah)": combined_curve[:, 0],
            "Voltage (V)": combined_curve[:, 1],
            "Direction": combined_curve[:, 2],
            "direction": np.where(combined_curve[:, 2] == 1, "charge", "discharge")
        })
    
    def _create_vertical_guide_trace(self, x_value: float, label: str, color: str) -> go.Scatter:
        """Create a vertical guide line at specified x-value.
        
        Parameters
        ----------
        x_value : float
            X-coordinate for the vertical line
        label : str
            Display name for the trace
        color : str
            Line color
            
        Returns
        -------
        go.Scatter
            Plotly scatter trace for the vertical guide line
        """
        y_range = [
            min(self.operating_voltage_window[0] * VOLTAGE_GUIDE_MARGIN_LOWER, 0),
            self.operating_voltage_window[1] * VOLTAGE_GUIDE_MARGIN_UPPER
        ]

        return go.Scatter(
            x=[x_value, x_value],
            y=y_range,
            mode="lines",
            name=label,
            line=dict(color=color, width=2, dash="dash"),
            legendgroup="guides",
            showlegend=True,
        )
    
    def _create_horizontal_guide_trace(self, y_value: float, label: str, color: str) -> go.Scatter:
        """Create a horizontal guide line at specified y-value.
        
        Parameters
        ----------
        y_value : float
            Y-coordinate for the horizontal line
        label : str
            Display name for the trace
        color : str
            Line color
            
        Returns
        -------
        go.Scatter
            Plotly scatter trace for the horizontal guide line
        """
        x_range = [
            0, 
            max(
                self.reversible_capacity * CAPACITY_GUIDE_EXTENSION, 
                self.irreversible_capacity * CAPACITY_GUIDE_EXTENSION
            )
        ]
        return go.Scatter(
            x=x_range,
            y=[y_value, y_value],
            mode="lines",
            name=label,
            line=dict(color=color, width=2, dash="dash"),
            legendgroup="guides",
            showlegend=True,
        )

    def _calculate_capacity_curve(self) -> np.ndarray:
        
        # get the full cell curve from the reference electrode assembly and scale it by the number of assemblies
        _capacity_curve = self._reference_electrode_assembly._capacity_curve.copy()
        _capacity_curve[:, 0] = _capacity_curve[:, 0] * self._n_electrode_assembly
        
        # cut the discharge curve off at the self._minimum_operating_voltage
        _charge_curve = _capacity_curve[_capacity_curve[:, 2] == 1]
        _discharge_curve = _capacity_curve[_capacity_curve[:, 2] == -1]
        
        # add a point in the discharge curve where voltage equals self._minimum_operating_voltage
        _min_op_voltage = self._minimum_operating_voltage

        # find the indices surrounding the min operating voltage
        above_indices = np.where(_discharge_curve[:, 1] >= _min_op_voltage)[0]
        below_indices = np.where(_discharge_curve[:, 1] <= _min_op_voltage)[0]
        
        # Check if min voltage is exactly on an existing point
        exact_match = np.where(np.isclose(_discharge_curve[:, 1], _min_op_voltage))[0]
        
        if len(exact_match) > 0:
            # Min voltage is exactly on a point, truncate at that point
            cutoff_idx = exact_match[0]
            _discharge_curve = _discharge_curve[:cutoff_idx + 1]
        elif len(above_indices) > 0 and len(below_indices) > 0:
            # Need to interpolate between two points
            above_idx = above_indices[-1]
            below_idx = below_indices[0]
            
            # linear interpolation to find the capacity at min operating voltage
            v1, c1 = _discharge_curve[above_idx, 1], _discharge_curve[above_idx, 0]
            v2, c2 = _discharge_curve[below_idx, 1], _discharge_curve[below_idx, 0]

            slope = (c2 - c1) / (v2 - v1)
            c_min_op = c1 + slope * (_min_op_voltage - v1)

            # create new point
            new_point = np.array([[c_min_op, _min_op_voltage, -1]])

            # insert the new point into the discharge curve (keep points up to and including below_idx)
            _discharge_curve = np.vstack((_discharge_curve[:below_idx + 1], new_point))
        # else: min voltage is outside the discharge curve range, keep full discharge curve

        # recombine the charge and discharge curves
        _capacity_curve = np.vstack((_charge_curve, _discharge_curve))

        self._capacity_curve = _capacity_curve

        return self._capacity_curve

    def _calculate_cathode_curve(self) -> np.ndarray:
        """Calculate scaled cathode capacity curve for the cell.
        
        Returns
        -------
        np.ndarray
            Cathode capacity curve scaled by number of electrode assemblies
        """
        _cathode_capacity_curve = self._reference_electrode_assembly._cathode_capacity_curve
        _cathode_capacity_curve[:, 0] = _cathode_capacity_curve[:, 0] * self._n_electrode_assembly
        self._cathode_capacity_curve = _cathode_capacity_curve
        return self._cathode_capacity_curve

    def _calculate_anode_curve(self) -> np.ndarray:
        """Calculate scaled anode capacity curve for the cell.
        
        Returns
        -------
        np.ndarray
            Anode capacity curve scaled by number of electrode assemblies
        """
        _anode_capacity_curve = self._reference_electrode_assembly._anode_capacity_curve
        _anode_capacity_curve[:, 0] = _anode_capacity_curve[:, 0] * self._n_electrode_assembly
        self._anode_capacity_curve = _anode_capacity_curve
        return self._anode_capacity_curve

    def _calculate_reversible_capacity(self) -> float:
        """Calculate reversible capacity at maximum voltage.
        
        Returns
        -------
        float
            Reversible capacity in C (coulombs)
        """
        # get the capacity curve
        _capacity_curve = self._capacity_curve.copy()

        # order by capacity
        _capacity_curve = _capacity_curve[np.argsort(_capacity_curve[:, 0])]

        # get the capacity at the maximum voltage
        v_max = _capacity_curve[:, 1].max()
        c_at_max_voltage = _capacity_curve[_capacity_curve[:, 1] == v_max][0, 0]

        # assign
        self._reversible_capacity = c_at_max_voltage

        # return
        return self._reversible_capacity

    def _calculate_irreversible_capacity(self) -> float:
        """Calculate irreversible capacity at minimum operating voltage.
        
        Returns
        -------
        float
            Irreversible capacity in C (coulombs)
        """

        # get the capacity curve
        _capacity_curve = self._capacity_curve.copy()

        # get the discharge curve
        _discharge_curve = _capacity_curve[_capacity_curve[:, 2] == -1]

        # order by capacity
        _discharge_curve = _discharge_curve[np.argsort(_discharge_curve[:, 0])]

        # linear interpolate to find the capacity at self._minimum_operating_voltage
        v1_idx = np.where(_discharge_curve[:, 1] <= self._minimum_operating_voltage)[0][0]
        v2_idx = v1_idx - 1
        v1, c1 = _discharge_curve[v1_idx, 1], _discharge_curve[v1_idx, 0]
        v2, c2 = _discharge_curve[v2_idx, 1], _discharge_curve[v2_idx, 0]
        slope = (c2 - c1) / (v2 - v1)
        c_at_min_op_voltage = c1 + slope * (self._minimum_operating_voltage - v1)

        # assign
        self._irreversible_capacity = c_at_min_op_voltage

        # return 
        return self._irreversible_capacity

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
        
        # calculate energyin W * s
        _discharge_curve = self._capacity_curve[self._capacity_curve[:, 2] == -1]
        _discharge_curve = _discharge_curve[np.argsort(_discharge_curve[:, 0])]
        _area_under_curve = np.trapz(_discharge_curve[:, 1], _discharge_curve[:, 0])
        self._energy = _area_under_curve

        # get gravimetric energy
        self._specific_energy = self._energy / self._mass

        # get volumetric energy
        self._volumetric_energy = self._energy / self._encapsulation._volume

        # get normalised cost
        self._cost_per_energy = self._cost / self._energy
        
    def get_capacity_plot(
        self,
        include_guides: bool = True,
        show_operating_window: bool = True,
        show_capacity_markers: bool = True,
        **kwargs,
    ) -> go.Figure:
        """Return a styled capacity vs. voltage plot for the cell.

        The plot overlays full-cell, cathode half-cell, and anode half-cell
        capacity curves and optionally annotates key electrochemical guide
        markers (reversible/irreversible capacities and operating voltage
        window limits).

        Parameters
        ----------
        include_guides : bool, optional
            If True, draw all guide lines / annotations (default True).
        show_operating_window : bool, optional
            If True, annotate min/max operating voltages (default True).
        show_capacity_markers : bool, optional
            If True, annotate irreversible & reversible capacities (default True).
        **kwargs : Any
            Additional layout overrides (e.g. title, colors, backgrounds).

        Returns
        -------
        go.Figure
            Plotly figure containing the capacity curves.
        """
        # Basic validation – ensure curves are computed
        if not hasattr(self, "_capacity_curve"):
            raise ValueError("Capacity curve data not available. Ensure properties are calculated.")

        fig = go.Figure()

        # Collect all traces to add at once
        traces = [
            self.cathode_capacity_curve_trace,
            self.anode_capacity_curve_trace,
            self.capacity_curve_trace,
            self.integrated_capacity_area_trace,
        ]

        # Add guide traces conditionally
        if include_guides:
            if show_capacity_markers:
                traces.extend([
                    self.irreversible_capacity_guide_trace,
                    self.reversible_capacity_guide_trace,
                ])
            
            if show_operating_window:
                traces.extend([
                    self.minimum_voltage_guide_trace,
                    self.maximum_voltage_guide_trace,
                ])

        # Add all traces at once for better performance
        fig.add_traces(traces)

        # Layout styling
        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Capacity (Ah)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
            **kwargs
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
    # Properties
    # ------------------------------------------------------------------

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
    def name(self) -> str:
        """Cell name."""
        return self._name
    
    @property
    def electrode_assemblies(self) -> list[_ElectrodeAssembly]:
        """List of electrode assemblies in the cell."""
        return self._electrode_assemblies
    
    @property
    def cost(self) -> float:
        """Cell cost in dollars."""
        return round(self._cost, COST_PRECISION)

    @property
    def mass(self) -> float:
        """Cell mass in grams."""
        return round(self._mass * KG_TO_G, MASS_PRECISION)

    @property
    def energy(self) -> float:
        """Cell energy in kWh."""
        return round(self._energy * ENERGY_CONVERSION_FACTOR, ENERGY_PRECISION)
    
    @property
    def specific_energy(self) -> float:
        """Cell specific energy in kWh/kg."""
        return round(self._specific_energy * ENERGY_CONVERSION_FACTOR, ENERGY_PRECISION)
    
    @property
    def volumetric_energy(self) -> float:
        """Cell volumetric energy in kWh/L."""
        return round(self._volumetric_energy * VOLUMETRIC_ENERGY_CONVERSION, ENERGY_PRECISION)

    @property
    def cost_per_energy(self) -> float:
        """Cell cost per energy in $/kWh."""
        return round(self._cost_per_energy * NORMALISED_COST_CONVERSION, MASS_PRECISION)

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """Cost breakdown of the cell in dollars.

        Returns
        -------
        Dict[str, Any]
            Nested dictionary containing cost breakdown by component
        """
        def _round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj, MASS_PRECISION)

        return _round_recursive(self._cost_breakdown)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """Mass breakdown of the cell in grams.

        Returns
        -------
        Dict[str, Any]
            Nested dictionary containing mass breakdown by component
        """
        def _convert_and_round_recursive(obj):
            if isinstance(obj, dict):
                return {k: _convert_and_round_recursive(v) for k, v in obj.items()}
            else:
                return round(obj * KG_TO_G, MASS_PRECISION)

        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def reversible_capacity(self) -> float:
        """Reversible capacity in Ah."""
        return round(self._reversible_capacity * S_TO_H, CAPACITY_PRECISION)

    @property
    def irreversible_capacity(self) -> float:
        """Irreversible capacity in Ah."""
        return round(self._irreversible_capacity * S_TO_H, CAPACITY_PRECISION)

    @property
    def capacity_curve(self) -> pd.DataFrame:
        """Full-cell capacity curve as DataFrame.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: Capacity (Ah), Voltage (V), Direction, direction
        """
        return self._format_curve_for_display(self._capacity_curve)

    @property
    def anode_capacity_curve(self) -> pd.DataFrame:
        """Anode half-cell capacity curve as DataFrame.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: Capacity (Ah), Voltage (V), Direction, direction
        """
        return self._format_curve_for_display(self._anode_capacity_curve)

    @property
    def cathode_capacity_curve(self) -> pd.DataFrame:
        """Cathode half-cell capacity curve as DataFrame.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: Capacity (Ah), Voltage (V), Direction, direction
        """
        return self._format_curve_for_display(self._cathode_capacity_curve)
    
    @property
    def capacity_curve_trace(self) -> go.Scatter:

        color = "#ff8c00"

        return go.Scatter(
            x=self.capacity_curve["Capacity (Ah)"],
            y=self.capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"Full-Cell",
            line=dict(color=color, width=3, shape='spline'),  # Slightly thicker for emphasis
            customdata=self.capacity_curve["Direction"],
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )
    
    @property
    def anode_capacity_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_capacity_curve["Capacity (Ah)"],
            y=self.anode_capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self._reference_electrode_assembly._layup._anode.name} Half-Cell",
            line=dict(color=self._reference_electrode_assembly._layup._anode.formulation.color, width=2, shape='spline'),
            customdata=self.anode_capacity_curve["Direction"],
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )
    
    @property
    def cathode_capacity_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_capacity_curve["Capacity (Ah)"],
            y=self.cathode_capacity_curve["Voltage (V)"],
            mode="lines",
            name=f"{self._reference_electrode_assembly._layup._cathode.name} Half-Cell",
            line=dict(color=self._reference_electrode_assembly._layup._cathode.formulation.color, width=2, shape='spline'),
            customdata=self.cathode_capacity_curve["Direction"],
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh/cm²<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
        )

    @property
    def integrated_capacity_area_trace(self) -> go.Scatter:

        color = "#ff8c00"

        curve = self.capacity_curve.query("direction == 'discharge'")

        return go.Scatter(
            x=curve["Capacity (Ah)"],
            y=curve["Voltage (V)"],
            mode="lines",
            name=f"Integrated Capacity",
            line=dict(color=color, width=1),
            fillcolor='rgba(255, 140, 0, 0.2)',
            fill='tozeroy',
        )

    @property
    def irreversible_capacity_guide_trace(self) -> go.Scatter:
        """Vertical line marking irreversible capacity."""
        return self._create_vertical_guide_trace(
            self.irreversible_capacity,
            f"Irreversible Cap: {self.irreversible_capacity:.2f} Ah",
            "#d62728"
        )

    @property
    def reversible_capacity_guide_trace(self) -> go.Scatter:
        """Vertical line marking reversible capacity."""
        return self._create_vertical_guide_trace(
            self.reversible_capacity,
            f"Reversible Cap: {self.reversible_capacity:.2f} Ah",
            "#2ca02c"
        )

    @property
    def minimum_voltage_guide_trace(self) -> go.Scatter:
        """Horizontal line marking minimum operating voltage."""
        return self._create_horizontal_guide_trace(
            self.minimum_operating_voltage,
            f"Min Voltage: {self.minimum_operating_voltage:.2f} V",
            "#1f77b4"
        )

    @property
    def maximum_voltage_guide_trace(self) -> go.Scatter:
        """Horizontal line marking maximum operating voltage."""
        return self._create_horizontal_guide_trace(
            self.maximum_operating_voltage,
            f"Max Voltage: {self.maximum_operating_voltage:.2f} V",
            "#ff7f0e"
        )

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------

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






