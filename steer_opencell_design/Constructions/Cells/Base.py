from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly
from steer_opencell_design.Components.Containers.Base import _Container
from steer_opencell_design.Utils.Decorators import calculate_electrochemical_properties
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator

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
import re
from scipy.optimize import brentq


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
        self._calculate_bulk_properties()
        self._calculate_electrochemical_properties()

    def _calculate_bulk_properties(self) -> None:
        self._calculate_electrolyte_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_electrochemical_properties(self) -> None:
        self._calculate_curves()
        self._calculate_operating_voltage_window()
        self._calculate_upper_voltage_limit_range()
        self._calculate_lower_voltage_limit_range()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        self._calculate_energy_properties()

    def _calculate_curves(self) -> None:
        """Calculate all capacity curves for the cell."""
        self._calculate_capacity_curve()
        self._calculate_cathode_curve()
        self._calculate_anode_curve()

    def _calculate_operating_voltage_window(self) -> None:
        self._minimum_operating_voltage = self._reference_electrode_assembly._layup._minimum_operating_voltage
        self._maximum_operating_voltage = self._reference_electrode_assembly._layup._maximum_operating_voltage
        self._operating_voltage_window = (self._minimum_operating_voltage, self._maximum_operating_voltage)

    def _calculate_upper_voltage_limit_range(self) -> None:
        self._maximum_operating_voltage_range = self._reference_electrode_assembly._layup._maximum_operating_voltage_range
        return self._maximum_operating_voltage_range
    
    def _calculate_lower_voltage_limit_range(self) -> None:
        self._minimum_operating_voltage_range = self._reference_electrode_assembly._layup._minimum_operating_voltage_range
        return self._minimum_operating_voltage_range

    def _calculate_electrolyte_properties(self) -> None:
        """Calculate electrolyte volume based on pore volume and overfill."""
        _pore_volume = sum([ea._pore_volume for ea in self._electrode_assemblies])
        _electrolyte_volume = _pore_volume * (1 + self.electrolyte_overfill)
        electrolyte_volume = _electrolyte_volume * M_TO_CM**3
        self._electrolyte.volume = electrolyte_volume

    def _make_assemblies(self) -> list[_ElectrodeAssembly]:

        # Create the electrode assemblies based on the reference assembly and number of assemblies
        self._electrode_assemblies = [deepcopy(self.reference_electrode_assembly) for _ in range(self.n_electrode_assembly)]

        # clear their cached data
        for assembly in self._electrode_assemblies:
            assembly._clear_cached_data()

        return self._electrode_assemblies
    
    def _position_encapsulation(self) -> None:
        """Position encapsulation centered around electrode assemblies.
        
        Uses the _get_center_point method from each assembly to calculate the
        geometric center, then positions the encapsulation accordingly.
        """
        # Get center point from reference assembly (x, y coordinates)
        reference_center = self._electrode_assemblies[0]._get_center_point()
        mid_x = reference_center[0] * M_TO_MM
        mid_y = reference_center[1] * M_TO_MM
        
        # Calculate z-position as midpoint between all assemblies
        assembly_z_datums = [assembly._datum[2] for assembly in self._electrode_assemblies]
        max_z = max(assembly_z_datums) + (self._reference_electrode_assembly._thickness) / 2
        min_z = min(assembly_z_datums) - (self._reference_electrode_assembly._thickness) / 2
        mid_z = (max_z + min_z) / 2 * M_TO_MM

        # Position the encapsulation centered around the electrode assembly stack
        self._encapsulation.datum = (
            mid_x,
            mid_y,
            mid_z
        )

    def _position_assemblies(self) -> None:

        # get center point of the reference assembly
        _center_x, _center_y, _ = self._electrode_assemblies[0]._get_center_point()

        # get x and y datum positions from the reference assembly
        _datum_x, _datum_y, _ = self._electrode_assemblies[0]._datum

        # get translation to center assemblies at origin
        translation_x = _center_x - _datum_x
        translation_y = _center_y - _datum_y

        # get new datum positions for x and y
        new_datum_x = _datum_x - translation_x
        new_datum_y = _datum_y - translation_y

        # get the z values
        if hasattr(self._reference_electrode_assembly, "_thickness"):
            thickness = self._reference_electrode_assembly._thickness
        elif hasattr(self._reference_electrode_assembly, "_radius"):
            thickness = self._reference_electrode_assembly._radius

        # make z-grid centered at 0 with self._n_electrode_assembly points spaced by self._reference_electrode_assembly._thickness
        z_positions = np.linspace(
            -((self.n_electrode_assembly - 1) / 2) * thickness,
            ((self.n_electrode_assembly - 1) / 2) * thickness,
            self.n_electrode_assembly,
        )

        # position each assembly at the corresponding z position
        for assembly, z in zip(self._electrode_assemblies, z_positions):

            assembly.datum = (
                new_datum_x * M_TO_MM,
                new_datum_y * M_TO_MM,
                z * M_TO_MM
            )

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
        voltage_values = self.capacity_curve["Voltage (V)"]
        min_voltage = voltage_values.min()
        max_voltage = voltage_values.max()

        y_range = [
            min(min_voltage * VOLTAGE_GUIDE_MARGIN_LOWER, 0),
            max_voltage * VOLTAGE_GUIDE_MARGIN_UPPER
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
        capacity_values = self.capacity_curve["Capacity (Ah)"]
        max_capacity = capacity_values.max()
        min_capacity = capacity_values.min()

        x_range = [
            min_capacity * CAPACITY_GUIDE_EXTENSION, 
            max_capacity * CAPACITY_GUIDE_EXTENSION
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
        _min_op_voltage = self._reference_electrode_assembly._layup._minimum_operating_voltage

        # find the indices surrounding the min operating voltage
        above_indices = np.where(_discharge_curve[:, 1] >= _min_op_voltage)[0]
        below_indices = np.where(_discharge_curve[:, 1] <= _min_op_voltage)[0]
        
        # Check if min voltage is exactly on an existing point
        exact_match = np.where(np.isclose(_discharge_curve[:, 1], _min_op_voltage))[0]
        
        if len(exact_match) > 0:
            # Min voltage is exactly on a point, truncate points below this index
            match_idx = exact_match[0]
            _discharge_curve = _discharge_curve[:match_idx + 1]
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

            # truncate the discharge curve up to above_idx and append the new point
            _discharge_curve = np.vstack((_discharge_curve[:above_idx + 1], new_point))
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
        _cathode_capacity_curve = self._reference_electrode_assembly._cathode_capacity_curve.copy()
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
        _anode_capacity_curve = self._reference_electrode_assembly._anode_capacity_curve.copy()
        _anode_capacity_curve[:, 0] = _anode_capacity_curve[:, 0] * self._n_electrode_assembly
        self._anode_capacity_curve = _anode_capacity_curve
        return self._anode_capacity_curve

    def _calculate_reversible_capacity(self) -> float:
        _discharge_mask = self._capacity_curve[:, 2] == -1
        _discharge_curve = self._capacity_curve[_discharge_mask]
        _max_cap = (_discharge_curve[:, 0]).max()
        _min_cap = (_discharge_curve[:, 0]).min()
        self._reversible_capacity = _max_cap - _min_cap

    def _calculate_irreversible_capacity(self) -> float:
        _discharge_mask = self._capacity_curve[:, 2] == -1
        _discharge_curve = self._capacity_curve[_discharge_mask]
        self._irreversible_capacity = _discharge_curve[:, 0].min()

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
        _area_under_curve = np.trapezoid(_discharge_curve[:, 1], _discharge_curve[:, 0])
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

        # get maximum voltage for y axis
        x_max = max(self._reference_electrode_assembly._layup._cathode._formulation._voltage_operation_window)

        # Layout styling
        fig.update_layout(
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Capacity (Ah)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)", "range": [0, x_max]},
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
    def volume(self) -> float:
        """Cell volume in liters."""
        return np.round(self._encapsulation._volume * M_TO_DM**3, MASS_PRECISION)

    @property
    def reference_chemistry(self) -> str:
        
        # get the reference chemistries from the cathode materials
        cathode_reference_chemistries = []
        for am in self._reference_electrode_assembly._layup._cathode._formulation._active_materials.keys():
            cathode_reference_chemistries.append(am._reference)

        # get the reference chemistries from the anode materials
        anode_reference_chemistries = []
        for am in self._reference_electrode_assembly._layup._anode._formulation._active_materials.keys():
            anode_reference_chemistries.append(am._reference)

        # check if all the cathode materials have the same reference chemistry
        if len(set(cathode_reference_chemistries)) != 1:
            raise ValueError(f"All cathode active materials must have the same reference chemistry. Currently: {cathode_reference_chemistries}")

        # check if all the anode materials have the same reference chemistry
        if len(set(anode_reference_chemistries)) != 1:
            raise ValueError(f"All anode active materials must have the same reference chemistry. Currently: {anode_reference_chemistries}")
        
        cathode_reference_chemistry = cathode_reference_chemistries[0]
        anode_reference_chemistry = anode_reference_chemistries[0]

        # check if the cathode and anode reference chemistries are compatible
        if cathode_reference_chemistry != anode_reference_chemistry:
            raise ValueError(f"Cathode and anode reference chemistries are not compatible. Cathode: {cathode_reference_chemistry}, Anode: {anode_reference_chemistry}")

        return cathode_reference_chemistry

    @property
    def form_factor(self) -> str:
        form_factor = self.__class__.__name__
        form_factor = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', form_factor)
        return form_factor

    @property
    def internal_construction(self) -> str:
        internal = self._reference_electrode_assembly.__class__.__name__
        internal = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', internal)
        return internal

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
        return np.round(self._cost, COST_PRECISION)

    @property
    def mass(self) -> float:
        """Cell mass in grams."""
        return np.round(self._mass * KG_TO_G, MASS_PRECISION)

    @property
    def energy(self) -> float:
        """Cell energy in kWh."""
        return np.round(self._energy * ENERGY_CONVERSION_FACTOR, ENERGY_PRECISION)
    
    @property
    def specific_energy(self) -> float:
        """Cell specific energy in kWh/kg."""
        return np.round(self._specific_energy * ENERGY_CONVERSION_FACTOR, ENERGY_PRECISION)
    
    @property
    def volumetric_energy(self) -> float:
        """Cell volumetric energy in kWh/L."""
        return np.round(self._volumetric_energy * VOLUMETRIC_ENERGY_CONVERSION, ENERGY_PRECISION)

    @property
    def cost_per_energy(self) -> float:
        """Cell cost per energy in $/kWh."""
        return np.round(self._cost_per_energy * NORMALISED_COST_CONVERSION, MASS_PRECISION)

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
                return np.round(obj, MASS_PRECISION)

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
                return np.round(obj * KG_TO_G, MASS_PRECISION)

        return _convert_and_round_recursive(self._mass_breakdown)

    @property
    def reversible_capacity(self) -> float:
        """Reversible capacity in Ah."""
        return np.round(self._reversible_capacity * S_TO_H, CAPACITY_PRECISION)

    @property
    def irreversible_capacity(self) -> float:
        """Irreversible capacity in Ah."""
        return np.round(self._irreversible_capacity * S_TO_H, CAPACITY_PRECISION)

    @property
    def irreversible_capacity_range(self) -> Tuple[float, float]:
        """Range of achievable irreversible capacities in Ah.
        
        Computes the min and max irreversible capacity by setting the minimum
        operating voltage to its extreme values.
        
        Returns
        -------
        Tuple[float, float]
            (min_irreversible_capacity, max_irreversible_capacity) in Ah
        """
        # Store current state
        current_min_voltage = self._minimum_operating_voltage
        
        # Get voltage range
        v_min, v_max = self._minimum_operating_voltage_range
        
        # Calculate irreversible capacity at minimum voltage
        self._reference_electrode_assembly._layup.minimum_operating_voltage = v_min
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        irr_at_min_voltage = self._irreversible_capacity * S_TO_H
        
        # Calculate irreversible capacity at maximum voltage
        self._reference_electrode_assembly._layup.minimum_operating_voltage = v_max
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        irr_at_max_voltage = self._irreversible_capacity * S_TO_H
        
        # Restore original state
        self._reference_electrode_assembly._layup.minimum_operating_voltage = current_min_voltage
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        
        # Return range (min at max voltage, max at min voltage due to inverse relationship)
        return (
            np.round(min(irr_at_min_voltage, irr_at_max_voltage), CAPACITY_PRECISION),
            np.round(max(irr_at_min_voltage, irr_at_max_voltage), CAPACITY_PRECISION)
        )

    @property
    def reversible_capacity_range(self) -> Tuple[float, float]:
        """Range of achievable reversible capacities in Ah.
        
        Computes the min and max reversible capacity by setting the maximum
        operating voltage to its extreme values.
        
        Returns
        -------
        Tuple[float, float]
            (min_reversible_capacity, max_reversible_capacity) in Ah
        """
        # Store current state
        current_max_voltage = self._maximum_operating_voltage
        
        # Get voltage range
        v_min, v_max = self._maximum_operating_voltage_range
        
        # Calculate reversible capacity at minimum voltage
        self._reference_electrode_assembly._layup.maximum_operating_voltage = v_min
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        rev_at_min_voltage = self._reversible_capacity * S_TO_H
        
        # Calculate reversible capacity at maximum voltage
        self._reference_electrode_assembly._layup.maximum_operating_voltage = v_max
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        rev_at_max_voltage = self._reversible_capacity * S_TO_H
        
        # Restore original state
        self._reference_electrode_assembly._layup.maximum_operating_voltage = current_max_voltage
        self._reference_electrode_assembly._calculate_capacity_curves()
        self._calculate_curves()
        self._calculate_reversible_capacity()
        self._calculate_irreversible_capacity()
        
        # Return range (sorted min to max)
        return (
            np.round(min(rev_at_min_voltage, rev_at_max_voltage), CAPACITY_PRECISION),
            np.round(max(rev_at_min_voltage, rev_at_max_voltage), CAPACITY_PRECISION)
        )

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
            hovertemplate="<b>Full-Cell</b><br>" + "Capacity: %{x:.2f} mAh<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
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
            hovertemplate="<b>Anode</b><br>" + "Capacity: %{x:.2f} mAh<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
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
            hovertemplate="<b>Cathode</b><br>" + "Capacity: %{x:.2f} mAh<br>" + "Voltage: %{y:.3f} V<br>" + "Direction: %{customdata}<extra></extra>",
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
            hovertemplate="<b>Integrated Capacity Area</b><br>" + "Capacity: %{x:.2f} mAh<br>" + "Voltage: %{y:.3f} V<extra></extra>",
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
            self.reversible_capacity + self.irreversible_capacity,
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

    @property
    def operating_voltage_window(self) -> Tuple[float, float]:
        """Operating voltage window (min, max) in volts."""
        return (
            np.round(self._operating_voltage_window[0], VOLTAGE_PRECISION),
            np.round(self._operating_voltage_window[1], VOLTAGE_PRECISION),
        )
    
    @property
    def maximum_operating_voltage_range(self) -> Tuple[float, float]:
        """Maximum operating voltage range in volts."""
        return (
            np.round(self._maximum_operating_voltage_range[0], VOLTAGE_PRECISION),
            np.round(self._maximum_operating_voltage_range[1], VOLTAGE_PRECISION),
        )
    
    @property
    def maximum_operating_voltage(self) -> float:
        """Maximum operating voltage in volts."""
        return np.round(self._maximum_operating_voltage, VOLTAGE_PRECISION)
    
    @property
    def minimum_operating_voltage_range(self) -> Tuple[float, float]:
        """Minimum operating voltage range in volts."""
        return (
            np.round(self._minimum_operating_voltage_range[0], VOLTAGE_PRECISION),
            np.round(self._minimum_operating_voltage_range[1], VOLTAGE_PRECISION),
        )
    
    @property
    def minimum_operating_voltage(self) -> float:
        """Minimum operating voltage in volts."""
        return np.round(self._minimum_operating_voltage, VOLTAGE_PRECISION)
    
    @property
    def reference_electrode_assembly(self) -> _ElectrodeAssembly:
        return self._reference_electrode_assembly

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------

    @reference_electrode_assembly.setter
    @calculate_all_properties
    def reference_electrode_assembly(self, value: _ElectrodeAssembly) -> None:
        self.validate_type(value, _ElectrodeAssembly, "reference_electrode_assembly")
        self._reference_electrode_assembly = value

    @reversible_capacity.setter
    @calculate_electrochemical_properties
    def reversible_capacity(self, value: float) -> None:
        """Set reversible capacity by solving for maximum operating voltage.
        
        Parameters
        ----------
        value : float
            Desired reversible capacity in Ah
        
        Raises
        ------
        ValueError
            If desired capacity is outside achievable range
        """
        self.validate_positive_float(value, "Reversible Capacity")
        
        # Convert to internal units
        target_capacity = value * H_TO_S
        
        # Define function that computes reversible capacity for given voltage
        def compute_reversible_capacity(voltage: float) -> float:
            # Temporarily set the voltage
            self._reference_electrode_assembly._layup.maximum_operating_voltage = voltage
            self._reference_electrode_assembly._calculate_capacity_curves()
            
            # Recompute cell curves and reversible capacity
            self._calculate_curves()
            self._calculate_reversible_capacity()
            self._calculate_irreversible_capacity()
            
            return self._reversible_capacity - target_capacity
        
        # Get voltage range
        v_min, v_max = self._maximum_operating_voltage_range
        
        # Check if target is achievable
        rev_at_min = compute_reversible_capacity(v_min)
        rev_at_max = compute_reversible_capacity(v_max)
        
        # Tolerance for boundary checks - 0.01 Ah converted to internal units (A·s)
        tolerance = 0.005 * H_TO_S
        
        # Check if we're at the boundary (within tolerance)
        if abs(rev_at_min) < tolerance:
            # Target exactly at minimum boundary
            solved_voltage = v_min
        elif abs(rev_at_max) < tolerance:
            # Target exactly at maximum boundary
            solved_voltage = v_max
        elif rev_at_min * rev_at_max > 0:
            # Both have same sign and not at boundary - target not in range
            actual_at_v_min = (rev_at_min + target_capacity) * S_TO_H
            actual_at_v_max = (rev_at_max + target_capacity) * S_TO_H
            # Sort to ensure min < max
            actual_min = min(actual_at_v_min, actual_at_v_max)
            actual_max = max(actual_at_v_min, actual_at_v_max)
            raise ValueError(
                f"Cannot achieve reversible capacity of {value:.2f} Ah. "
                f"Achievable range is [{actual_min:.2f}, {actual_max:.2f}] Ah"
            )
        else:
            # Use Brent's method to find the voltage that gives target capacity
            solved_voltage = brentq(compute_reversible_capacity, v_min, v_max, xtol=1e-6)
        
        # Set the final voltage
        try:
            self._reference_electrode_assembly._layup.maximum_operating_voltage = solved_voltage
            self._reference_electrode_assembly._calculate_capacity_curves()
            self._maximum_operating_voltage = solved_voltage
            self._operating_voltage_window = (self._minimum_operating_voltage, solved_voltage)
        except ValueError as e:
            raise ValueError(f"Failed to solve for maximum operating voltage: {e}")

    @irreversible_capacity.setter
    @calculate_electrochemical_properties
    def irreversible_capacity(self, value: float) -> None:
        """Set irreversible capacity by solving for minimum operating voltage.
        
        Parameters
        ----------
        value : float
            Desired irreversible capacity in Ah
        
        Raises
        ------
        ValueError
            If desired capacity is outside achievable range
        """
        self.validate_positive_float(value, "Irreversible Capacity")
        
        # Convert to internal units
        target_capacity = value * H_TO_S
        
        # Define function that computes irreversible capacity for given voltage
        def compute_irreversible_capacity(voltage: float) -> float:
            # Temporarily set the voltage
            self._reference_electrode_assembly._layup.minimum_operating_voltage = voltage
            self._reference_electrode_assembly._calculate_capacity_curves()
            
            # Recompute cell curves and irreversible capacity
            self._calculate_curves()
            self._calculate_reversible_capacity()
            self._calculate_irreversible_capacity()
            
            return self._irreversible_capacity - target_capacity
        
        # Get voltage range
        v_min, v_max = self._minimum_operating_voltage_range
        
        # Check if target is achievable
        irr_at_min = compute_irreversible_capacity(v_min)
        irr_at_max = compute_irreversible_capacity(v_max)
        
        # Tolerance for boundary checks - 0.01 Ah converted to internal units (A·s)
        # Since we display with 2 decimal places, tolerance should be half of that precision
        tolerance = 0.005 * H_TO_S  # 0.005 Ah = 18 A·s
        
        # Check if we're at the boundary (within tolerance)
        if abs(irr_at_min) < tolerance:
            # Target exactly at minimum boundary
            solved_voltage = v_min
        elif abs(irr_at_max) < tolerance:
            # Target exactly at maximum boundary
            solved_voltage = v_max
        elif irr_at_min * irr_at_max > 0:
            # Both have same sign and not at boundary - target not in range
            actual_at_v_min = (irr_at_min + target_capacity) * S_TO_H
            actual_at_v_max = (irr_at_max + target_capacity) * S_TO_H
            # Sort to ensure min < max
            actual_min = min(actual_at_v_min, actual_at_v_max)
            actual_max = max(actual_at_v_min, actual_at_v_max)
            raise ValueError(
                f"Cannot achieve irreversible capacity of {value:.2f} Ah. "
                f"Achievable range is [{actual_min:.2f}, {actual_max:.2f}] Ah"
            )
        else:
            # Use Brent's method to find the voltage that gives target capacity
            solved_voltage = brentq(compute_irreversible_capacity, v_min, v_max, xtol=1e-6)
        
        # Set the final voltage
        try:
            self._reference_electrode_assembly._layup.minimum_operating_voltage = solved_voltage
            self._reference_electrode_assembly._calculate_capacity_curves()
            self._minimum_operating_voltage = solved_voltage
            self._operating_voltage_window = (solved_voltage, self._maximum_operating_voltage)
        except ValueError as e:
            raise ValueError(f"Failed to solve for minimum operating voltage: {e}")

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

    @operating_voltage_window.setter
    @calculate_electrochemical_properties
    def operating_voltage_window(self, value: Tuple[float, float]) -> None:

        # Ensure value is a list for mutability
        value = list(value)

        # Fill in None values with layup limits
        if value[0] is None:
            value[0] = min(self._reference_electrode_assembly._layup._minimum_operating_voltage_range)
        if value[1] is None:
            value[1] = max(self._reference_electrode_assembly._layup._maximum_operating_voltage_range)

        # clip values
        if self._update_properties:
            value[0] = np.clip(value[0], self._minimum_operating_voltage_range[0], self._minimum_operating_voltage_range[1])
            value[1] = np.clip(value[1], self._maximum_operating_voltage_range[0], self._maximum_operating_voltage_range[1])

        # Validate tuple structure
        self.validate_positive_float(value[0], "operating_voltage_window minimum")
        self.validate_positive_float(value[1], "operating_voltage_window maximum")

        # Validate logical consistency
        if value[0] >= value[1]:
            raise ValueError("operating_voltage_window minimum must be less than maximum.")

        # set the voltage window to the layup
        self._reference_electrode_assembly._layup.operating_voltage_window = value
        self._reference_electrode_assembly._calculate_capacity_curves()

        # assign
        self._operating_voltage_window = value
        self._maximum_operating_voltage = max(value)
        self._minimum_operating_voltage = min(value)

    @maximum_operating_voltage.setter
    def maximum_operating_voltage(self, value: float) -> None:

        if value is None:
            value = max(self._reference_electrode_assembly._layup._maximum_operating_voltage_range)

        self.validate_positive_float(value, "maximum_operating_voltage")
        value = np.clip(value, self._maximum_operating_voltage_range[0], self._maximum_operating_voltage_range[1])

        self._reference_electrode_assembly._layup.maximum_operating_voltage = value
        self._reference_electrode_assembly._calculate_capacity_curves()

        self._maximum_operating_voltage = value
        self.operating_voltage_window = (self._minimum_operating_voltage, value)

    @minimum_operating_voltage.setter
    @calculate_electrochemical_properties
    def minimum_operating_voltage(self, value: float) -> None:
            
        if value is None:
            value = min(self._reference_electrode_assembly._layup._minimum_operating_voltage_range)

        self.validate_positive_float(value, "minimum_operating_voltage")
        value = np.clip(value, self._minimum_operating_voltage_range[0], self._minimum_operating_voltage_range[1])

        self._reference_electrode_assembly._layup.minimum_operating_voltage = value
        self._reference_electrode_assembly._calculate_capacity_curves()

        self._minimum_operating_voltage = value
        self._operating_voltage_window = (value, self._maximum_operating_voltage)


