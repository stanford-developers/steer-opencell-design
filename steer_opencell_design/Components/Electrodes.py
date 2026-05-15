# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Electrode definitions combining formulations with current collectors and coating parameters."""

from steer_core.Decorators.Coordinates import calculate_coordinates, calculate_volumes
from steer_core.Decorators.General import (
    calculate_all_properties,
    calculate_bulk_properties,
    recalculate,
)

from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Datum import DatumMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Propagation import PropagationMixin, propagating_setter

from steer_core.Constants.Units import *
from steer_core.Utils import round_dict_recursive

from steer_opencell_design.Materials.Formulations import (
    CathodeFormulation,
    AnodeFormulation,
    _ElectrodeFormulation,
)
from steer_opencell_design.Components.CurrentCollectors.Base import _CurrentCollector

from steer_opencell_design.Materials.Other import InsulationMaterial

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings

from copy import deepcopy
from typing import Dict, Any, Tuple, Optional
from enum import Enum


class ElectrodeControlMode(Enum):
    """Control modes for electrode property interdependencies."""
    MAINTAIN_CALENDER_DENSITY = "maintain_calender_density"  # Keep calender density constant (current behavior)
    MAINTAIN_MASS_LOADING = "maintain_mass_loading"  # Keep mass loading constant
    MAINTAIN_COATING_THICKNESS = "maintain_coating_thickness"  # Keep coating thickness constant


class _Electrode(
    ValidationMixin,
    CoordinateMixin,
    DatumMixin,
    PropagationMixin,
    SerializerMixin, 
    PlotterMixin,
    DunderMixin,
    ):
    """
    Base class for electrodes, representing the common properties and methods of an electrode.
    """

    def __init__(
        self,
        formulation: Optional[_ElectrodeFormulation],
        mass_loading: float,
        current_collector: _CurrentCollector,
        calender_density: float,
        insulation_material: InsulationMaterial = None,
        insulation_thickness: float = 0.0,
        name: str = "Electrode",
        datum: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        """
        Initialize an object that represents an electrode.

        Parameters
        ----------
        formulation : _ElectrodeFormulation or None
            The formulation of the electrode, which includes active materials, binders, and conductive additives.
            If None, the electrode is treated as anode-free (bare current collector, no areal capacity curve).
        mass_loading : float
            The mass loading of the electrode in mg/cm^2.
        current_collector : _CurrentCollector
            The current collector used in the electrode.
        calender_density : float
            The density of the electrode coating after calendering in g/cm^3.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the electrode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation material in micrometers (default is 0.0).
        name : str, optional
            The name of the electrode (default is 'Electrode').
        ----------
        """
        self._update_properties = False
        self._is_anode_free = False
        self._property_cache = {}

        # Initialize _datum early so mixin properties work during component setup
        self._datum = tuple(float(d) * MM_TO_M for d in datum)

        self.name = name

        # Assign formulation first — setter handles None → sets _is_anode_free
        self.formulation = formulation
        self.mass_loading = mass_loading
        self.calender_density = calender_density

        self.current_collector = current_collector
        self.datum = datum
        self.insulation_material = insulation_material
        self.insulation_thickness = insulation_thickness

        # Validate that insulation material is provided when current collector has insulation area
        if not self._is_anode_free and self.current_collector.insulation_area > 0 and self.insulation_material is None:
            raise ValueError(
                f"Current collector has insulation area ({self.current_collector.insulation_area} cm²) "
                f"but no insulation material was provided. Please specify an insulation_material."
            )

        # Calculate initial properties
        self._calculate_all_properties()

        # set final control mode
        self.control_mode = ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY

        # action booleans
        self._flipped_x = False
        self._flipped_y = False
        self._flipped_z = False

    # === CONTROL SYSTEM ===

    def _update_dependent_properties(self, property_name: str, new_val: float):
        """Route a property change to the correct recalculation based on control mode."""
        from steer_core.Utils.ControlModes import dispatch_dependent_update

        dependency_function = {
            ElectrodeControlMode.MAINTAIN_MASS_LOADING: {
                "mass_loading": self._calculate_coating_thickness,
                "calender_density": self._calculate_coating_thickness,
                "coating_thickness": self._calculate_calender_density,
            },
            ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: {
                "mass_loading": self._calculate_coating_thickness,
                "calender_density": self._calculate_coating_thickness,
                "coating_thickness": self._calculate_mass_loading,
            },
            ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: {
                "mass_loading": self._calculate_calender_density,
                "calender_density": self._calculate_mass_loading,
                "coating_thickness": self._calculate_mass_loading,
            },
        }

        dependency_inputs = {
            ElectrodeControlMode.MAINTAIN_MASS_LOADING: {
                "mass_loading": (new_val, self.calender_density),
                "calender_density": (self.mass_loading, new_val),
                "coating_thickness": (self.mass_loading, new_val),
            },
            ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: {
                "mass_loading": (new_val, self.calender_density),
                "calender_density": (self.mass_loading, new_val),
                "coating_thickness": (self.calender_density, new_val),
            },
            ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: {
                "mass_loading": (new_val, self.coating_thickness),
                "calender_density": (new_val, self.coating_thickness),
                "coating_thickness": (self.calender_density, new_val),
            },
        }

        dispatch_dependent_update(
            self.control_mode, property_name, dependency_function, dependency_inputs
        )

    @property
    def control_mode(self) -> ElectrodeControlMode:
        """Get the current control mode."""
        return self._control_mode

    @control_mode.setter
    def control_mode(self, mode: ElectrodeControlMode | str) -> None:
        """Set the control mode from an enum member or string value."""

        if isinstance(mode, ElectrodeControlMode):
            self._control_mode = mode
            return
        
        elif isinstance(mode, str):
            for enum_member in ElectrodeControlMode:
                if mode.lower().replace(" ", "_") == enum_member.value:
                    self._control_mode = enum_member
                    return
            raise ValueError(f"Invalid control mode: '{mode}'. Available modes are: {[e.value for e in ElectrodeControlMode]}")
                
        else:
            raise ValueError(f"Invalid control mode: {mode}. Available modes are: {[e.value for e in ElectrodeControlMode]}")

    def _calculate_mass_loading(self, calender_density: float, coating_thickness: float) -> None:
        """Derive mass loading from calender density and coating thickness."""
        _calender_density = calender_density * (G_TO_KG / CM_TO_M**3)
        _coating_thickness = coating_thickness * UM_TO_M
        self._mass_loading = _calender_density * _coating_thickness

    def _calculate_coating_thickness(self, _mass_loading: float, _calender_density: float) -> None:
        """Derive coating thickness from mass loading and calender density."""
        if _calender_density == 0.0:
            self._coating_thickness = 0.0
            return
        self._coating_thickness = _mass_loading / _calender_density

    def _calculate_calender_density(self, mass_loading: float, coating_thickness: float) -> None:
        """Derive calender density from mass loading and coating thickness."""
        _mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)
        _coating_thickness = coating_thickness * UM_TO_M
        if _coating_thickness == 0:
            self._calender_density = 0.0
            return
        self._calender_density = _mass_loading / _coating_thickness

    # === CALCULATE PROPERTIES ===

    def _calculate_all_properties(self) -> None:
        """Recalculate coating thickness, bulk properties, areal curves, and coordinates."""
        self._property_cache.clear()
        if self._is_anode_free:
            self._coating_thickness = 0.0
        else:
            self._calculate_coating_thickness(self._mass_loading, self._calender_density)
        self._calculate_bulk_properties()
        self._calculate_areal_capacity_curve()
        self._calculate_coordinates()

    def _calculate_areal_capacity_curve(self) -> None:
        """Compute the areal capacity curve from the formulation.

        For anode-free electrodes the curve is set to ``None``.
        """
        if self._is_anode_free:
            self._areal_capacity_curve = None
            return

        # get the half cell curve from the formulation
        curve = self._formulation._capacity_curve.copy()

        # calculate the areal capacity
        areal_capacity = curve[:, 0] / self._current_collector._coated_area

        # set
        self._areal_capacity_curve = np.column_stack([areal_capacity, curve[:, 1], curve[:, 2]])

    def _calculate_bulk_properties(self) -> None:
        if self._is_anode_free:
            self._porosity = 0.0
            self._coating_volume = 0.0
            self._thickness = self._current_collector._thickness
            self._pore_volume = 0.0
            self._minimum_coating_volume = 0.0
            self._mass = self._current_collector._mass
            self._mass_breakdown = {
                "Current Collector": self._current_collector._mass,
            }
            self._cost = self._current_collector._cost
            self._cost_breakdown = {
                "Current Collector": self._current_collector._cost,
            }
            return
        self._calculate_porosity()
        self._calculate_thickness_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_coordinates(self) -> None:
        """Calculate coating and insulation coordinates for both sides of the electrode.

        For anode-free electrodes all coating and insulation coordinates are
        set to ``None``; downstream consumers must guard accordingly.
        """
        if hasattr(self, "_property_cache"):
            self._property_cache.clear()
        if self._is_anode_free:
            self._a_side_coating_coordinates = None
            self._b_side_coating_coordinates = None
            self._a_side_insulation_coordinates = None
            self._b_side_insulation_coordinates = None
            return

        def _calculate_side_coordinates(side: str) -> None:
            """Calculate coordinates for one side (a or b)."""
            side_multiplier = 1 if side == "a" else -1

            # Calculate coating coordinates
            coating_coordinates = getattr(self._current_collector, f"_{side}_side_coated_coordinates")

            coating_datum = (
                self._current_collector._datum[0],
                self._current_collector._datum[1],
                self._current_collector._datum[2] + side_multiplier * (self._current_collector._thickness / 2 + self._coating_thickness / 2),
            )

            x, y, z, _ = self.extrude_footprint(
                coating_coordinates[:, 0],
                coating_coordinates[:, 1],
                coating_datum,
                self._coating_thickness,
            )

            setattr(self, f"_{side}_side_coating_coordinates", np.column_stack([x, y, z]))

            if hasattr(self._current_collector, f"_{side}_side_insulation_coordinates") and getattr(self._current_collector, f"_{side}_side_insulation_coordinates") is not None:
                # Calculate insulation coordinates
                insulation_coordinates = getattr(self._current_collector, f"_{side}_side_insulation_coordinates")

                x, y, z, _ = self.extrude_footprint(
                    insulation_coordinates[:, 0],
                    insulation_coordinates[:, 1],
                    coating_datum,  # Use same datum as coating
                    self._insulation_thickness,
                )

                setattr(
                    self,
                    f"_{side}_side_insulation_coordinates",
                    np.column_stack([x, y, z]),
                )

            else:
                # If no insulation coordinates, set to empty array
                setattr(self, f"_{side}_side_insulation_coordinates", None)

        # Calculate for both sides
        _calculate_side_coordinates("a")
        _calculate_side_coordinates("b")

    def _calculate_mass_properties(self) -> None:
        """
        Calculate the mass properties of the electrode.
        """
        # calculate mass of the coating
        _coated_mass = self._current_collector._coated_area * self._mass_loading
        coated_mass = _coated_mass * KG_TO_G
        self._formulation.mass = coated_mass

        # calculate the total mass
        self._mass = self._formulation._mass + self._current_collector._mass

        # calculate the mass breakdown
        self._mass_breakdown = {
            "Coating": self._formulation._mass_breakdown,
            "Current Collector": self._current_collector._mass,
        }

        # insulation mass
        if hasattr(self, "_insulation_material") and self._insulation_material is not None:
            _insulator_mass = self._current_collector._insulation_area * self._insulation_material._density * self._insulation_thickness
            insulator_mass = _insulator_mass * KG_TO_G
            self._insulation_material.mass = insulator_mass
            self._mass += self._insulation_material._mass
            self._mass_breakdown["Electrical Insulation"] = self._insulation_material._mass

        return self._mass, self._mass_breakdown

    def _calculate_cost_properties(self) -> None:
        """
        Calculate the cost properties of the electrode.
        """
        # calculate the total cost
        self._cost = self._formulation._cost + self._current_collector._cost

        # calculate the cost breakdown
        self._cost_breakdown = {
            "Coating": self._formulation._cost_breakdown,
            "Current Collector": self._current_collector._cost,
        }

        # insulation cost
        if hasattr(self, "_insulation_material") and self._insulation_material is not None:
            self._cost += self._insulation_material._cost
            self._cost_breakdown["Electrical Insulation"] = self._insulation_material._cost

        return self._cost, self._cost_breakdown

    def _calculate_thickness_properties(self) -> None:
        """
        Calculate the thickness properties of the electrode.
        """
        self._coating_volume = self._current_collector._coated_area * self._coating_thickness
        self._thickness = self._coating_thickness * 2 + self._current_collector._thickness
        self._pore_volume = self._coating_volume * self._porosity

        _minimum_coating_thickness = self._mass_loading / self._formulation._density
        self._minimum_coating_volume = _minimum_coating_thickness * self._current_collector._coated_area

        if self._calender_density > 0.0 and self._coating_thickness < _minimum_coating_thickness:
            warnings.warn(
                f"""Your calender density of {self.calender_density} g/cm^3 is too high, 
                           leading to negative porosity. Decrease your calender density below 
                           {self._formulation._density} g/cm^3.""",
                UserWarning,
            )

        if self._insulation_thickness > self._coating_thickness:
            warnings.warn(
                f"""Insulation thickness is greater than the coating thickness on {self.name}. 
                          Reduce the insulation thickness ({self.insulation_thickness}  um) 
                          or increase the coating thickness ({self.coating_thickness}  um)""",
                UserWarning,
            )

    def _calculate_porosity(self) -> None:
        """Calculate coating porosity from formulation specific volume and calender density."""
        porosity = 1 - (self._formulation._specific_volume * self._calender_density)

        if porosity < 0:
            warnings.warn(f"Negative porosity calculated for {self.name}. Clamping to 0.", UserWarning)
            porosity = 0.0

        self._porosity = porosity

    def _clear_cached_data(self) -> None:
        """Clear cached property data and downstream formulation caches."""
        self._property_cache.clear()
        self._areal_capacity_curve = None
        if not self._is_anode_free:
            self._formulation._clear_cached_data()

    # === VIEWS ===

    def plot_right_left_view(self, set_z_zero: bool = False, **kwargs) -> go.Figure:
        """Generate a right-left (side) Plotly figure of the electrode."""
        if set_z_zero:
            if self.datum_z == 0.0:
                electrode = self
            else: 
                electrode = deepcopy(self)
                electrode.datum = (self.datum_x, self.datum_y, 0.0)
        else:
            electrode = self

        figure = electrode._current_collector.plot_right_left_view(**kwargs)
        figure.data = [trace for trace in figure.data if trace.name == "Foil" or trace.name == "Tab"]

        if not electrode._is_anode_free:
            figure.add_trace(electrode.right_left_a_side_coating_trace)
            figure.add_trace(electrode.right_left_b_side_coating_trace)

        if hasattr(electrode, "_insulation_material") and electrode._insulation_material is not None:
            figure.add_trace(electrode.right_left_a_side_insulation_trace)
        if hasattr(electrode, "_insulation_material") and electrode._insulation_material is not None:
            figure.add_trace(electrode.right_left_b_side_insulation_trace)

        figure.update_layout(
            xaxis=electrode.SCHEMATIC_X_AXIS,
            yaxis=electrode.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

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

    def plot_top_down_view(self, **kwargs) -> go.Figure:
        """Generate a top-down Plotly figure of the electrode."""
        figure = self.current_collector.plot_top_down_view(**kwargs)
        figure.data = [trace for trace in figure.data if trace.name == "Foil" or trace.name == "Tab"]

        if not self._is_anode_free:
            # Get the traces to add
            coating_trace = self.top_down_coating_trace
            insulation_trace = self.top_down_insulation_trace

            # Regular figure - add traces normally
            figure.add_trace(coating_trace)

            if insulation_trace:  # Check if insulation exists
                figure.add_trace(insulation_trace)

        return figure

    def plot_a_side_view(self, **kwargs) -> go.Figure:
        """Generate a Plotly figure of the A-side of the electrode."""
        if self.top_side == "a":
            return self.plot_top_down_view(**kwargs)
        else:
            self._flip("y")
            figure = self.plot_top_down_view(**kwargs)
            self._flip("y")
            return figure

    def plot_b_side_view(self, **kwargs) -> go.Figure:
        """Generate a Plotly figure of the B-side of the electrode."""
        if self.top_side == "b":
            return self.plot_top_down_view(**kwargs)
        else:
            self._flip("y")
            figure = self.plot_top_down_view(**kwargs)
            self._flip("y")
            return figure

    def plot_cross_section(self, **kwargs) -> go.Figure:
        """
        Get a cross-section view of the electrode, zoomed in around the datum.
        
        Parameters
        ----------
        y_axis_range : list or tuple, optional
            Custom y-axis range as [min, max]. If not provided, automatically calculated 
            based on electrode thickness and datum position with locked scaling for thin electrodes.
        """
        # For anode-free electrodes, return the current collector cross-section directly
        if self._is_anode_free:
            figure = self._current_collector.plot_right_left_view(**kwargs)
            figure.data = [trace for trace in figure.data if trace.name == "Foil" or trace.name == "Tab"]
            return figure

        # Get base figure using plot_right_left_view (includes current collector and coating traces)
        figure = self.plot_right_left_view(**kwargs)
        
        # Note: Insulation traces are intentionally excluded from cross-section view
        # Remove insulation traces if they exist
        figure.data = [trace for trace in figure.data if "Insulation" not in trace.name]

        # covert traces from mm to um
        for trace in figure.data:
            trace.x = [x * MM_TO_UM for x in trace.x]
            trace.y = [y * MM_TO_UM for y in trace.y]

        # Get datum coordinates in mm (for plotting)
        datum_y = self.datum[1]  # y-coordinate of datum

        # Apply locked scaling based on thickness ranges
        if self.thickness <= 0.4:
            y_range = [datum_y - 0.2, datum_y + 0.2]
        elif self.thickness <= 0.8:
            y_range = [datum_y - 0.4, datum_y + 0.4]
        elif self.thickness <= 1.2:
            y_range = [datum_y - 0.6, datum_y + 0.6]
        else:
            zoom_range = self.thickness * 1.5
            half_range = zoom_range / 2
            y_range = [datum_y - half_range, datum_y + half_range]

        Y_AXIS = self.SCHEMATIC_Y_AXIS.copy()
        Y_AXIS['title'] = "Thickness (µm)"
        Y_AXIS['range'] = y_range

        X_AXIS = {
            "range": y_range,
            "title": "",
            "showticklabels": False,
            "ticks": "",
        }

        # Update layout to zoom in and lock aspect ratio
        figure.update_layout(
            xaxis=X_AXIS,
            yaxis=Y_AXIS,
            legend=self.BOTTOM_LEGEND
        )

        return figure

    def get_a_side_center_line(self) -> np.ndarray:
        """Return the A-side coating center line as an (x, z) array."""
        if self._a_side_coating_coordinates is None:
            return np.empty((0, 2))
        return self.get_xz_center_line(self._a_side_coating_coordinates)
    
    def get_b_side_center_line(self) -> np.ndarray:
        """Return the B-side coating center line as an (x, z) array."""
        if self._b_side_coating_coordinates is None:
            return np.empty((0, 2))
        return self.get_xz_center_line(self._b_side_coating_coordinates)

    def plot_areal_capacity_curve(self, **kwargs) -> go.Figure:
        """
        Plot the areal capacity curve of the electrode.
        """
        if self._is_anode_free:
            return None

        figure = go.Figure()
        figure.add_trace(self.areal_capacity_curve_trace)

        XAXIS = self.SCATTER_X_AXIS.copy()
        XAXIS['title'] = "Areal Capacity (mAh/cm²)"
        YAXIS = self.SCATTER_Y_AXIS.copy()
        YAXIS['title'] = "Voltage (V)"

        figure.update_layout(
            xaxis=XAXIS,
            yaxis=YAXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @property
    def right_left_a_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the a side insulated area.
        """
        try:
            # get the coordinates
            a_side_insulation_coordinates = self.order_coordinates_clockwise(self.a_side_insulation_coordinates, plane="yz")

            # make the trace
            a_side_insulation_trace = go.Scatter(
                x=a_side_insulation_coordinates["y"],
                y=a_side_insulation_coordinates["z"],
                mode="lines",
                name="A Side Insulated Area",
                line=dict(width=1, color="black"),
                fill="toself",
                fillcolor=self._insulation_material._color,
                legendgroup="A Side Insulated Area",
                showlegend=True,
            )

            return a_side_insulation_trace

        except Exception as e:
            return None

    @property
    def right_left_b_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the b side insulated area.
        """
        try:
            # get the coordinates
            b_side_insulation_coordinates = self.order_coordinates_clockwise(self.b_side_insulation_coordinates, plane="yz")

            # make the trace
            b_side_insulation_trace = go.Scatter(
                x=b_side_insulation_coordinates["y"],
                y=b_side_insulation_coordinates["z"],
                mode="lines",
                name="B Side Insulated Area",
                line=dict(width=1, color="black"),
                fill="toself",
                fillcolor=self._insulation_material._color,
                legendgroup="B Side Insulated Area",
                showlegend=True,
            )

            return b_side_insulation_trace
        
        except Exception as e:
            return None

    @property
    def right_left_a_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the a side coated area.
        """
        if self._is_anode_free:
            return None

        # get the coordinates
        a_side_coating_coordinates = self.order_coordinates_clockwise(self.a_side_coating_coordinates, plane="yz")

        # make the trace
        a_side_coating_trace = go.Scatter(
            x=a_side_coating_coordinates["y"],
            y=a_side_coating_coordinates["z"],
            mode="lines",
            name="A Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self._formulation._color,
            legendgroup="A Side Coated Area",
            showlegend=True,
        )

        return a_side_coating_trace

    @property
    def bottom_up_a_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the a side coated area.
        """
        if self._is_anode_free:
            return None

        # get the coordinates
        a_side_coating_coordinates = self.order_coordinates_clockwise(self.a_side_coating_coordinates, plane="xz")

        # add first row to end to close the shape
        a_side_coating_coordinates = pd.concat([a_side_coating_coordinates, a_side_coating_coordinates.iloc[[0]]], ignore_index=True)

        # make the trace
        a_side_coating_trace = go.Scatter(
            x=a_side_coating_coordinates["x"],
            y=a_side_coating_coordinates["z"],
            mode="lines",
            name="A Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self._formulation._color,
            legendgroup="A Side Coated Area",
            showlegend=True,
        )

        return a_side_coating_trace

    @property
    def right_left_b_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the b side coated area.
        """
        if self._is_anode_free:
            return None

        # get the coordinates
        b_side_coating_coordinates = self.order_coordinates_clockwise(self.b_side_coating_coordinates, plane="yz")

        # make the trace
        b_side_coating_trace = go.Scatter(
            x=b_side_coating_coordinates["y"],
            y=b_side_coating_coordinates["z"],
            mode="lines",
            name="B Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self._formulation._color,
            legendgroup="B Side Coated Area",
            showlegend=True,
        )

        return b_side_coating_trace
    
    @property
    def bottom_up_b_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the Plotly trace for the b side coated area.
        """
        if self._is_anode_free:
            return None

        # get the coordinates
        b_side_coating_coordinates = self.order_coordinates_clockwise(self.b_side_coating_coordinates, plane="xz")

        # add first row to end to close the shape
        b_side_coating_coordinates = pd.concat([b_side_coating_coordinates, b_side_coating_coordinates.iloc[[0]]], ignore_index=True)

        # make the trace
        b_side_coating_trace = go.Scatter(
            x=b_side_coating_coordinates["x"],
            y=b_side_coating_coordinates["z"],
            mode="lines",
            name="B Side Coated Area",
            line=dict(width=1, color="black"),
            fill="toself",
            fillcolor=self._formulation._color,
            legendgroup="B Side Coated Area",
            showlegend=True,
        )

        return b_side_coating_trace

    @property
    def top_side(self) -> str:
        """Get which side ('a' or 'b') is currently facing up."""
        return self._current_collector.top_side

    @property
    def top_down_coating_trace(self) -> go.Scatter:
        """Get the top-down Plotly trace for the visible coating side."""
        if self._is_anode_free:
            return None

        side = self.current_collector.top_side
        coated_area_coordinates = self.a_side_coating_coordinates if side == "a" else self.b_side_coating_coordinates

        # make the coated area trace
        coated_area_trace = go.Scatter(
            x=coated_area_coordinates["x"],
            y=coated_area_coordinates["y"],
            mode="lines",
            name="A Side Coating" if side == "a" else "B Side Coating",
            line=dict(width=1, color="black"),
            fillcolor=self.formulation.color,
            fill="toself",
        )

        return coated_area_trace

    @property
    def top_down_insulation_trace(self) -> go.Scatter:
        """
        Get the top-down insulation trace of the electrode.
        """
        if not self._insulation_material:
            return None

        side = self.current_collector.top_side
        insulation_coordinates = self.a_side_insulation_coordinates if side == "a" else self.b_side_insulation_coordinates

        # make the insulation area trace
        insulation_area_trace = go.Scatter(
            x=insulation_coordinates["x"],
            y=insulation_coordinates["y"],
            mode="lines",
            name="A Side Insulation" if side == "a" else "B Side Insulation",
            line=dict(width=1, color="black"),
            fillcolor=self.insulation_material.color,
            fill="toself",
        )

        return insulation_area_trace

    @property
    def voltage_cutoff(self) -> float:
        """Get the voltage cutoff of the electrode."""
        if self._is_anode_free:
            return 0.0
        return self._formulation.voltage_cutoff

    # === ACTIONS ===

    @calculate_coordinates
    def _flip(self, axis: str) -> None:
        """
        Function to rotate the electrode around a specified axis by 180 degrees
        around the current datum position.

        Parameters
        ----------
        axis : str
            The axis to rotate around. Must be 'x' or 'y'.
        """
        self._property_cache.clear()
        if axis not in ["x", "y", "z"]:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")

        # Flip the current collector first (this handles all current collector coordinates)
        self._current_collector._flip(axis)

        if axis == "x":
            self._flipped_x = not self._flipped_x
        if axis == "y":
            self._flipped_y = not self._flipped_y
        if axis == "z":
            self._flipped_z = not self._flipped_z

    # === PROPERTIES ===

    @property
    def areal_capacity_curve(self) -> pd.DataFrame:
        """Get the capacity curve with proper units and formatting."""

        if self._areal_capacity_curve is None:
            return None

        # Pre-compute unit conversion factor
        areal_capacity_conversion = S_TO_H * A_TO_mA / M_TO_CM**2

        # original curve
        curve = self._areal_capacity_curve
        
        # compute the columns
        areal_capacity = curve[:, 0] * areal_capacity_conversion
        voltage = curve[:, 1]
        direction = np.where(curve[:, 2] == 1, "charge", "discharge")

        # Create DataFrame with converted values directly
        return pd.DataFrame({
            "Areal Capacity (mAh/cm²)": areal_capacity,
            "Voltage (V)": voltage,
            "Direction": direction,
        })
    
    @property
    def areal_capacity_curve_trace(self) -> go.Scatter:
        """
        Get the areal capacity curve trace of the electrode.
        """
        if self.areal_capacity_curve is None:
            return None

        curve_df = self.areal_capacity_curve
        line_color = self._formulation._color if not self._is_anode_free else "#C0C0C0"

        trace = go.Scatter(
            x=curve_df["Areal Capacity (mAh/cm²)"],
            y=curve_df["Voltage (V)"],
            mode="lines",
            name=f"{self.name} Areal Capacity Curve",
            line=dict(color=line_color, shape="spline"),
            marker=dict(size=6),
            hovertemplate="Areal Capacity: %{x} mAh/cm²<br>Voltage: %{y} V<br><extra></extra>",
        )

        return trace

    @property
    def formulation(self) -> _ElectrodeFormulation:
        """Get the electrode formulation."""
        return self._formulation

    @property
    def insulation_material(self) -> InsulationMaterial:
        """Get the insulation material, or None if not set."""
        return self._insulation_material

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Get the properties of the electrode.

        :return: Dictionary containing the properties of the electrode.
        """
        if self._is_anode_free:
            return {
                "Cost": f"$ {self.cost}",
                "Mass": f"{self.mass} g",
                "Total thickness": f"{self.thickness} um",
                "Anode-free": "Yes",
            }
        return {
            "Cost": f"$ {self.cost}",
            "Mass": f"{self.mass} g",
            "Coating mass": f"{self._formulation.mass} g",
            "Total thickness": f"{self.thickness} um",
            "Coating thickness": f"{self.coating_thickness} um",
        }

    @property
    def insulation_thickness(self) -> float:
        """
        Get the insulation thickness of the electrode.

        :return: Insulation thickness of the electrode in micrometers.
        """
        return self._insulation_thickness * M_TO_UM

    @property
    def insulation_thickness_range(self) -> Tuple[float, float]:
        """
        Get the range of insulation thickness of the electrode.

        :return: Tuple containing the minimum and maximum insulation thickness in micrometers.
        """
        return (0, self._coating_thickness * M_TO_UM)

    @property
    def insulation_thickness_hard_range(self) -> Tuple[float, float]:
        """
        Get the range of insulation thickness of the electrode.

        :return: Tuple containing the minimum and maximum insulation thickness in micrometers.
        """
        return (0, self._coating_thickness * M_TO_UM)

    @property
    def coating_thickness(self) -> float:
        """
        Get the coating thickness of the electrode.

        :return: Coating thickness of the electrode in micrometers.
        """
        return self._coating_thickness * M_TO_UM

    @property
    def coating_thickness_hard_range(self) -> Tuple[float, float]:
        """Get the hard allowable coating thickness range in µm."""
        return (0, 200)

    @property
    def coating_thickness_range(self) -> Tuple[float, float]:
        """Get the allowable coating thickness range in µm."""
        return (2, 200)

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """

        return round_dict_recursive(self._cost_breakdown, precision=None)

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """

        return round_dict_recursive(self._mass_breakdown, precision=None, unit_conversion=KG_TO_G)

    @property
    def porosity(self) -> float:
        """
        Get the porosity of the electrode.

        :return: Porosity of the electrode.
        """
        return self._porosity * FRACTION_TO_PERCENT

    @property
    def calender_density(self) -> float:
        """
        Get the calender density of the electrode.

        :return: Calender density of the electrode.
        """
        return self._calender_density * (KG_TO_G / M_TO_CM**3)

    @property
    def calender_density_range(self) -> Tuple[float, float]:
        """Get the allowable calender density range in g/cm³."""
        if self._is_anode_free:
            return (0.0, 0.0)
        max_porosity = self.porosity_range[1] / 100
        min_porosity = self.porosity_range[0] / 100

        min_calender_density = ((1 - max_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)
        max_calender_density = ((1 - min_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)

        return (min_calender_density, max_calender_density)

    @property
    def calender_density_hard_range(self) -> Tuple[float, float]:
        """Get the hard allowable calender density range in g/cm³."""
        if self._is_anode_free:
            return (0.0, 0.0)
        max_porosity = self.porosity_hard_range[1] / 100
        min_porosity = self.porosity_hard_range[0] / 100

        min_calender_density = ((1 - max_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)
        max_calender_density = ((1 - min_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)

        return (min_calender_density, max_calender_density)

    def _get_coords_df(self, cache_key: str, raw_coords) -> pd.DataFrame:
        """Return a cached mm-unit DataFrame for the given raw coordinate array."""
        if raw_coords is None:
            return None
        if not hasattr(self, "_property_cache"):
            self._property_cache = {}
        cached = self._property_cache.get(cache_key)
        if cached is not None:
            return cached
        df = pd.DataFrame(raw_coords, columns=["x", "y", "z"]).assign(
            x=lambda x: (x["x"].astype(float) * M_TO_MM).round(10),
            y=lambda x: (x["y"].astype(float) * M_TO_MM).round(10),
            z=lambda x: (x["z"].astype(float) * M_TO_MM).round(10),
        )
        self._property_cache[cache_key] = df
        return df

    @property
    def a_side_insulation_coordinates(self) -> pd.DataFrame:
        """Get the A side insulation coordinates of the electrode."""
        return self._get_coords_df("a_ins_coords", self._a_side_insulation_coordinates)

    @property
    def b_side_insulation_coordinates(self) -> pd.DataFrame:
        """Get the B side insulation coordinates of the electrode."""
        return self._get_coords_df("b_ins_coords", self._b_side_insulation_coordinates)

    @property
    def a_side_coating_coordinates(self) -> pd.DataFrame:
        """Get the A side coating coordinates of the electrode."""
        return self._get_coords_df("a_coat_coords", self._a_side_coating_coordinates)

    @property
    def b_side_coating_coordinates(self) -> pd.DataFrame:
        """Get the B side coating coordinates of the electrode."""
        return self._get_coords_df("b_coat_coords", self._b_side_coating_coordinates)

    @property
    def mass_loading(self) -> float:
        """
        Get the mass loading of the electrode.

        :return: Mass loading of the electrode.
        """
        return self._mass_loading * (KG_TO_MG / M_TO_CM**2)

    @property
    def mass_loading_range(self) -> Tuple[float, float]:
        """Get the allowable mass loading range in mg/cm²."""
        return (
            self.calender_density_range[0] * self.coating_thickness_range[0] * UM_TO_CM * G_TO_mG,
            self.calender_density_range[1] * self.coating_thickness_range[1] * UM_TO_CM * G_TO_mG,
        )

    @property
    def mass_loading_hard_range(self) -> Tuple[float, float]:
        """Get the hard allowable mass loading range in mg/cm²."""
        return (
            self.calender_density_hard_range[0] * self.coating_thickness_hard_range[0] * UM_TO_CM * G_TO_mG,
            self.calender_density_hard_range[1] * self.coating_thickness_hard_range[1] * UM_TO_CM * G_TO_mG,
        )

    @property
    def current_collector(self) -> _CurrentCollector:
        """
        Get the current collector of the electrode.

        :return: Current collector of the electrode.
        """
        return self._current_collector

    @property
    def name(self) -> str:
        """
        Get the name of the electrode.

        :return: Name of the electrode.
        """
        return self._name

    @property
    def mass(self) -> float:
        """
        Get the mass of the electrode.

        :return: Mass of the electrode.
        """
        return self._mass * KG_TO_G

    @property
    def mass_range(self) -> Tuple[float, float]:
        """Get the allowable mass range in g."""
        min = 0
        hyp_max = 1
        max = hyp_max * (1 - np.exp(-0.5 / self._mass))

        return (min * KG_TO_G, max * KG_TO_G)

    @property
    def thickness(self) -> float:
        """
        Get the thickness of the electrode.

        :return: Thickness of the electrode.
        """
        return self._thickness * M_TO_UM

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """
        Get the range of thickness of the electrode.

        :return: Tuple containing the minimum and maximum thickness in micrometers.
        """
        return (
            self.coating_thickness_range[0] * 2 + self.current_collector.thickness,
            self.coating_thickness_range[1] * 2 + self.current_collector.thickness,
        )

    @property
    def cost(self) -> float:
        """Get the total electrode cost in $."""
        return self._cost

    @property
    def cost_range(self):
        """Get the allowable cost range in $."""
        min = 0
        max = self._cost + (1 / self._cost) / 5
        return (min, max)

    @property
    def porosity_hard_range(self) -> Tuple[float, float]:
        """Get the hard allowable porosity range in %."""
        return (10, 80)

    # === SETTERS ===

    @voltage_cutoff.setter
    @recalculate("areal_capacity_curve")
    def voltage_cutoff(self, voltage_cutoff: float):
        if self._is_anode_free:  # no-op: anode-free has no coating
            return
        self.validate_positive_float(voltage_cutoff, "voltage cutoff")
        self._formulation.voltage_cutoff = voltage_cutoff

    @thickness.setter
    def thickness(self, thickness: float):
        self.validate_positive_float(thickness, "thickness")
        new_coating_thickness = (thickness - self.current_collector.thickness) / 2
        self.coating_thickness = new_coating_thickness

    @coating_thickness.setter
    @calculate_all_properties
    def coating_thickness(self, coating_thickness: float):
        """
        Set the coating thickness of the electrode. Behavior depends on control mode.

        :param coating_thickness: Coating thickness of the electrode in micrometers.
        """
        if self._is_anode_free:  # no-op: anode-free has no coating
            return
        self.validate_positive_float(coating_thickness, "coating thickness")
        self._coating_thickness = coating_thickness * UM_TO_M

        if self._update_properties:
            self._update_dependent_properties("coating_thickness", coating_thickness)

    @porosity.setter
    def porosity(self, porosity: float):
        """
        Set the porosity of the electrode.

        :param porosity: Porosity of the electrode in percentage.
        """
        if self._is_anode_free:  # no-op: anode-free has no coating
            return
        self.validate_percentage(porosity, "porosity")
        porosity_fraction = porosity / 100
        new_calender_density = (1 - porosity_fraction) / self._formulation._specific_volume
        self.calender_density = new_calender_density * (KG_TO_G / M_TO_CM**3)

    @formulation.setter
    @calculate_all_properties
    @propagating_setter()
    def formulation(self, formulation: _ElectrodeFormulation):
        if formulation is None:
            self._formulation = None
            self._is_anode_free = True
            self._mass_loading = 0.0
            self._calender_density = 0.0
            self._coating_thickness = 0.0
            self._porosity = 0.0
            self._insulation_material = None
            self._insulation_thickness = 0.0
            self._areal_capacity_curve = None
            if hasattr(self, "_property_cache"):
                self._property_cache.clear()
            return
        self._is_anode_free = False
        self.validate_type(formulation, _ElectrodeFormulation, "formulation")
        self._formulation = formulation

    @calender_density.setter
    @calculate_all_properties
    def calender_density(self, calender_density: float):
        if self._is_anode_free:  # no-op: anode-free has no coating
            return
        self.validate_positive_float(calender_density, "calender density")
        self._calender_density = calender_density * (G_TO_KG / CM_TO_M**3)

        if self._update_properties:
            self._update_dependent_properties("calender_density", calender_density)

    @insulation_material.setter
    @calculate_bulk_properties
    @propagating_setter(deepcopy=True)
    def insulation_material(self, insulation_material: InsulationMaterial | None):

        if self._is_anode_free and insulation_material is not None:
            raise ValueError("Anode-free electrodes cannot have insulation material.")

        if insulation_material is not None:

            self.validate_type(insulation_material, InsulationMaterial, "insulation material") if insulation_material else None

            if self._current_collector.insulation_area != 0 and insulation_material is None:
                raise ValueError("Insulation material must be provided if the current collector has an insulation width")

            if self._current_collector.insulation_area == 0 and insulation_material is not None:
                raise ValueError("Insulation material cannot be provided if the current collector does not have an insulation area")

        self._insulation_material = insulation_material  # Already a copy due to decorator

    @insulation_thickness.setter
    @calculate_all_properties
    def insulation_thickness(self, insulation_thickness: float):
        self.validate_positive_float(insulation_thickness, "insulation thickness")
        self._insulation_thickness = insulation_thickness * UM_TO_M

    @mass_loading.setter
    @calculate_all_properties
    def mass_loading(self, mass_loading: float):
        if self._is_anode_free:  # no-op: anode-free has no coating
            return
        self.validate_positive_float(mass_loading, "mass loading")
        self._mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)

        if self._update_properties:
            self._update_dependent_properties("mass_loading", mass_loading)

    @current_collector.setter
    @calculate_bulk_properties
    @calculate_coordinates
    @propagating_setter()
    def current_collector(self, current_collector: _CurrentCollector):

        # validate the current collector
        self.validate_type(current_collector, _CurrentCollector, "current collector")

        # assign the current collector
        self._current_collector = current_collector

    @name.setter
    def name(self, name: str):
        self.validate_string(name, "name")
        self._name = name

    # Override datum setter to sync with current_collector and use decorator
    @DatumMixin.datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]):
        self.validate_datum(datum)
        self._datum = (
            float(datum[0]) * MM_TO_M,
            float(datum[1]) * MM_TO_M,
            float(datum[2]) * MM_TO_M,
        )
        # Sync datum to current collector
        self.current_collector.datum = datum


class Anode(_Electrode):
    """
    A class representing an anode in a battery system, inheriting from the _Electrode base class.

    For anode-free designs, pass ``formulation=None`` (and omit ``mass_loading``
    and ``calender_density``).  The resulting electrode is a bare current
    collector with no areal capacity curve (``_areal_capacity_curve = None``).
    The V = 0 integration is handled higher up in the cell hierarchy.
    """

    def __init__(
        self,
        formulation: Optional[AnodeFormulation] = None,
        mass_loading: float = 0.0,
        current_collector: _CurrentCollector = None,
        calender_density: float = 0.0,
        insulation_material: InsulationMaterial = None,
        insulation_thickness: float = 0.0,
        name: str = "Anode",
    ):
        """
        Initialize an object that represents an anode.

        Parameters:
        ----------
        formulation : AnodeFormulation or None
            The formulation of the anode.  Pass ``None`` for an anode-free
            design (bare current collector, no areal capacity curve).
        mass_loading : float
            The mass loading of the anode in mg/cm^2.  Ignored when
            ``formulation`` is None.
        current_collector : _CurrentCollector
            The current collector used in the anode.
        calender_density : float
            The density of the anode after calendering in g/cm^3.  Ignored
            when ``formulation`` is None.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the anode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation material in micrometers (default is 0.0).
        name : str, optional
            The name of the anode (default is 'Anode').
        ----------
        """
        if current_collector is None:
            raise ValueError("current_collector is required.")

        super().__init__(
            formulation=formulation,
            mass_loading=mass_loading,
            current_collector=current_collector,
            calender_density=calender_density,
            name=name,
            insulation_material=insulation_material,
            insulation_thickness=insulation_thickness,
        )

        self._update_properties = True

    @property
    def top_overhang(self) -> float:
        """
        Get the top overhang of the anode when in a layup or stack.

        :return: Top overhang of the anode in mm.
        """
        if hasattr(self, "_top_overhang"):
            return self._top_overhang * M_TO_MM
        else:
            return

    @top_overhang.setter
    def top_overhang(self, top_overhang: float):
        """
        Set the top overhang of the anode when in a layup or stack.

        :param top_overhang: Top overhang of the anode in mm.
        """
        if not isinstance(top_overhang, (int, float)):
            raise TypeError("Top overhang must be a number")

        if top_overhang < 0:
            raise ValueError("Top overhang must be greater than or equal to zero")

        if not hasattr(self, "_top_overhang"):
            raise AttributeError("Top overhang has not been set yet. This indicates that the anode is not part of a layup or stack, and so the top overhang cannot be set.")

        old_top_overhang = self.top_overhang
        new_top_overhang = top_overhang
        overhang_difference = new_top_overhang - old_top_overhang

        self.datum = (self.datum[0], self.datum[1] + overhang_difference, self.datum[2])

        self._top_overhang = new_top_overhang * MM_TO_M

    @property
    def bottom_overhang(self) -> float:
        """
        Get the bottom overhang of the anode when in a layup or stack.

        :return: Bottom overhang of the anode in mm.
        """
        if hasattr(self, "_bottom_overhang"):
            return self._bottom_overhang * M_TO_MM
        else:
            return

    @bottom_overhang.setter
    def bottom_overhang(self, bottom_overhang: float):
        """
        Set the bottom overhang of the anode when in a layup or stack.

        :param bottom_overhang: Bottom overhang of the anode in mm.
        """
        if not isinstance(bottom_overhang, (int, float)):
            raise TypeError("Bottom overhang must be a number")

        if bottom_overhang < 0:
            raise ValueError("Bottom overhang must be greater than or equal to zero")

        if not hasattr(self, "_bottom_overhang"):
            raise AttributeError("Bottom overhang has not been set yet. This indicates that the anode is not part of a layup or stack, and so the bottom overhang cannot be set.")

        old_bottom_overhang = self.bottom_overhang
        new_bottom_overhang = bottom_overhang
        overhang_difference = new_bottom_overhang - old_bottom_overhang

        self.datum = (self.datum[0], self.datum[1] - overhang_difference, self.datum[2])

        self._bottom_overhang = new_bottom_overhang * MM_TO_M

    @property
    def porosity_range(self) -> Tuple[float, float]:
        """
        Get the range of porosity of the electrode.

        :return: Tuple containing the minimum and maximum porosity in percentage.
        """
        return (25, 50)


class Cathode(_Electrode):
    """
    A class representing a cathode in a battery system, inheriting from the _Electrode base class.
    """

    def __init__(
        self,
        formulation: CathodeFormulation,
        mass_loading: float,
        current_collector: _CurrentCollector,
        calender_density: float,
        insulation_material: InsulationMaterial = None,
        insulation_thickness: float = 0.0,
        name: str = "Cathode",
    ):
        """
        Initialize an object that represents a cathode.

        Parameters
        ----------
        formulation : CathodeFormulation
            The formulation of the cathode.
        mass_loading : float
            The mass loading of the cathode in mg/cm².
        current_collector : _CurrentCollector
            The current collector used in the cathode.
        calender_density : float
            The density of the cathode after calendering in g/cm³.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the cathode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation in micrometers (default is 0.0).
        name : str, optional
            The name of the cathode (default is 'Cathode').
        """
        super().__init__(
            formulation=formulation,
            mass_loading=mass_loading,
            current_collector=current_collector,
            calender_density=calender_density,
            name=name,
            insulation_material=insulation_material,
            insulation_thickness=insulation_thickness,
        )

        self._update_properties = True

    @property
    def porosity_range(self) -> Tuple[float, float]:
        """
        Get the range of porosity of the electrode.

        :return: Tuple containing the minimum and maximum porosity in percentage.
        """
        return (15, 40)













