from steer_opencell_design.Constructions.Layups import _Layup
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer

from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.TypeChecker import ValidationMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.Mixins.Colors import ColorMixin
from steer_core.Mixins.Dunder import DunderMixin
from steer_core.Mixins.Plotter import PlotterMixin
from steer_core.Mixins.Data import DataMixin

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Decorators.Coordinates import calculate_coordinates

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.AuxillaryComponents.WindingEquipment import RoundMandrel, FlatMandrel

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial

from copy import deepcopy
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from shapely import minimum_bounding_circle
import warnings
import plotly.graph_objects as go
from typing import Any, Dict, Tuple



class _ElectrodeAssembly(
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
        ):

        self._update_properties = False

        self.layup = layup
        self.name = name

    def _calculate_all_properties(self):
        self._calculate_bulk_properties()
        self._calculate_interfacial_area()
        self._calcualate_full_cell_curve()

    def _calculate_bulk_properties(self):
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_mass_properties(self):
        pass

    def _calculate_cost_properties(self):
        pass

    def _calculate_interfacial_area(self):
        """Calculate interfacial area of the electrode assembly."""
        pass

    def _calcualate_full_cell_curve(self):
        """Calculate full cell voltage curve of the electrode assembly."""
        _full_cell_curve = deepcopy(self._layup._full_cell_curve)
        _full_cell_curve[:, 0] = _full_cell_curve[:, 0] * self._interfacial_area
        self._full_cell_curve = _full_cell_curve
        return self._full_cell_curve
    
    def _calculate_anode_half_cell_curve(self):
        """Calculate anode half-cell voltage curve of the electrode assembly."""
        _anode_half_cell = deepcopy(self._layup._anode._half_cell_curve)
        _anode_half_cell[:, 0] = _anode_half_cell[:, 0] * self._interfacial_area
        self._anode_half_cell = _anode_half_cell
        return self._anode_half_cell
    
    def _calculate_cathode_half_cell_curve(self):
        """Calculate cathode half-cell voltage curve of the electrode assembly."""
        _cathode_half_cell = deepcopy(self._layup._cathode._half_cell_curve)
        _cathode_half_cell[:, 0] = _cathode_half_cell[:, 0] * self._interfacial_area
        self._cathode_half_cell = _cathode_half_cell
        return self._cathode_half_cell
    
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
            title=kwargs.get("title", f"Areal Capacity Curves"),
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            xaxis={**self.SCATTER_X_AXIS, "title": "Areal Capacity (mAh/cm²)"},
            yaxis={**self.SCATTER_Y_AXIS, "title": "Voltage (V)"},
            hovermode="closest",
        )

        return fig

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
                capacity=lambda x: x["capacity"] * (S_TO_H * A_TO_mA),
            )
            .rename(
                columns={
                    "voltage": "Voltage (V)",
                    "direction": "Direction",
                    "capacity": "Capacity (mAh)",
                }
            )
            .round(4)
        )
    
    @property
    def full_cell_curve_trace(self) -> go.Scatter:

        full_cell_color = "#ff8c00"

        return go.Scatter(
            x=self.full_cell_curve["Capacity (mAh)"],
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
            self
            .layup
            .anode
            .half_cell_curve
            .copy()
            .assign(capacity = lambda x: x["Areal Capacity (mAh/cm²)"] * self.interfacial_area,)
            .drop(columns=["Areal Capacity (mAh/cm²)"])
            .rename(columns={"capacity": "Capacity (mAh)"})
        )
    
    @property
    def anode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.anode_half_cell_curve["Capacity (mAh)"],
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
            self
            .layup
            .cathode
            .half_cell_curve
            .copy()
            .assign(capacity = lambda x: x["Areal Capacity (mAh/cm²)"] * self.interfacial_area,)
            .drop(columns=["Areal Capacity (mAh/cm²)"])
            .rename(columns={"capacity": "Capacity (mAh)"})
        )
    
    @property
    def cathode_half_cell_curve_trace(self) -> go.Scatter:

        return go.Scatter(
            x=self.cathode_half_cell_curve["Capacity (mAh)"],
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
    def name(self, value: str):
        self.validate_string(value, "name")
        self._name = value


class _JellyRoll(_ElectrodeAssembly):
    """Jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel | RoundMandrel
        ):

        super().__init__(laminate)

        self.mandrel = mandrel

    def _calculate_all_properties(self):
        self._calculate_roll()
        super()._calculate_all_properties()

    def _calculate_mass_properties(self):

        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._mass = self.layup.anode._mass + self.layup.cathode._mass + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anode": self.layup.anode._mass_breakdown,
            "Cathode": self.layup.cathode._mass_breakdown,
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        separators = [self.layup._bottom_separator, self.layup._top_separator]

        self._cost = self.layup.anode._cost + self.layup.cathode._cost + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anode": self.layup.anode._cost_breakdown,
            "Cathode": self.layup.cathode._cost_breakdown,
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    @property
    def mandrel(self) -> RoundMandrel | FlatMandrel:
        """Return the mandrel instance."""
        return self._mandrel

    @property
    def layup(self) -> Laminate:
        """Return the underlying `Laminate` instance."""
        return self._layup

    @mandrel.setter
    @calculate_all_properties
    def mandrel(self, value: RoundMandrel | FlatMandrel):
        self.validate_type(value, (RoundMandrel, FlatMandrel), "mandrel")
        self._mandrel = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: Laminate):
        self.validate_type(value, Laminate, "layup")
        self._layup = value


class WoundJellyRoll(_JellyRoll):
    """Wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: RoundMandrel
        ):

        super().__init__(
            laminate=laminate,
            mandrel=mandrel,
        )

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_roll(self):
        pass


class FlatWoundJellyRoll(_JellyRoll):
    """Flat wound jelly roll electrode assembly.

    Accepts only a `Laminate` layup representing the layered winding structure.
    """
    def __init__(
            self, 
            laminate: Laminate,
            mandrel: FlatMandrel,
            mandrel_gap: float = 0.0
        ):

        super().__init__(
            laminate=laminate,
            mandrel=mandrel
        )

        self.mandrel_gap = mandrel_gap

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_roll(self):
        pass

    @property
    def mandrel_gap(self) -> float:
        """Return the mandrel gap in mm."""
        return round(self._mandrel_gap * M_TO_MM, 2)
    
    @mandrel_gap.setter
    @calculate_all_properties
    def mandrel_gap(self, value: float):
        self.validate_type(value, float, "mandrel_gap")
        self._mandrel_gap = value


class _Stack(_ElectrodeAssembly):
    """Stack electrode assembly.

    Accepts a `MonoLayer` or `ZFoldMonoLayer` layup representing stacked sheets.
    """
    def __init__(
            self, 
            layup: MonoLayer | ZFoldMonoLayer,
            n_layers: int = 1
        ):

        super().__init__(layup)
        self.n_layers = n_layers

    def _calculate_all_properties(self):
        self._calculate_stack()
        super()._calculate_all_properties()

    def _calculate_stack(self):
        
        # Initialize dictionaries for components
        stack = {}

        # set the starting z datum
        z_datum = 0

        # add bottom separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)

        # add anode to stack
        z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add layups to stack
        for _ in range(self.n_layers):
            z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._cathode, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add top separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._top_separator, z_datum)

        self._stack = stack

        return self._stack

    def _calculate_interfacial_area(self):
        
        # set the z tolerance
        z_tol = 1e-8

        # get the anode polygon
        _anode_coords = self._layup._anode._a_side_coating_coordinates
        _max_z = np.max(_anode_coords[:, 2])
        _top_anode_coords = _anode_coords[np.abs(_anode_coords[:, 2] - _max_z) < z_tol][:, :2]
        _anode_polygon = Polygon(_top_anode_coords)

        # get the cathode polygon
        _cathode_coords = self._layup._cathode._a_side_coating_coordinates
        _max_z = np.max(_cathode_coords[:, 2])
        _top_cathode_coords = _cathode_coords[np.abs(_cathode_coords[:, 2] - _max_z) < z_tol][:, :2]
        _cathode_polygon = Polygon(_top_cathode_coords)

        # calculate the intersection
        intersection_polygon = _anode_polygon.intersection(_cathode_polygon)

        # overlapping area
        _single_layer_interfacial_area = intersection_polygon.area

        # calculate the number of interfaces
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]       
        n_interfaces = len(cathodes) * 2

        # calculate total interfacial area
        self._interfacial_area = _single_layer_interfacial_area * n_interfaces

        return self._interfacial_area

    def _calculate_mass_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._mass = sum([a._mass for a in anodes]) + sum([c._mass for c in cathodes]) + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "mass"),
            "Cathodes": self.sum_breakdowns(cathodes, "mass"),
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._cost = sum([a._cost for a in anodes]) + sum([c._cost for c in cathodes]) + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "cost"),
            "Cathodes": self.sum_breakdowns(cathodes, "cost"),
            "Separators": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    def get_side_view(self, **kwargs):

        figure = go.Figure()

        for _, component in self.stack.items():
            layer_figure = component.get_right_left_view()
            legend_group = component.__class__.__name__
            for trace in layer_figure.data:
                trace.legendgroup = legend_group
                trace.name = legend_group
                trace.showlegend = True if legend_group not in [t.legendgroup for t in figure.data] else False
                # Set line width to 0.5
                if hasattr(trace, 'line') and trace.line is not None:
                    trace.line.width = 0.5
                figure.add_trace(trace)

        figure.update_layout(
            xaxis=self.SCHEMATIC_X_AXIS,
            yaxis=self.SCHEMATIC_Y_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )

        return figure

    @staticmethod
    def add_layer(stack: Dict, component, z_datum):

        stack_size = len(stack)

        new_component = deepcopy(component)

        if stack_size == 0:
            new_z_datum = z_datum + new_component._thickness * M_TO_MM / 2
        else:
            new_z_datum = z_datum + new_component._thickness * M_TO_MM / 2 + stack[stack_size - 1]._thickness * M_TO_MM / 2

        new_component.datum = (new_component._datum[0] * M_TO_MM, new_component._datum[1] * M_TO_MM, new_z_datum)
        stack_size = len(stack)
        stack[stack_size] = new_component

        return new_z_datum, stack

    @property
    def stack(self) -> dict:
        """Return the stack of components."""
        return self._stack

    @property
    def n_layers(self) -> int:
        """Return the number of layers in the stack."""
        return self._n_layers
    
    @n_layers.setter
    @calculate_all_properties
    def n_layers(self, value: int):
        self.validate_positive_int(value, "n_layers")
        self._n_layers = value


class ZFoldStack(_Stack):
    """Z-Fold stack electrode assembly.

    Accepts a `ZFoldMonoLayer` layup representing stacked sheets in a Z-fold configuration.
    """
    def __init__(
            self, 
            layup: ZFoldMonoLayer,
            n_layers: int,
            additional_separator_wraps: float = 1
        ):

        super().__init__(
            layup,
            n_layers
        )

        self.additional_separator_wraps = additional_separator_wraps

        self._calculate_all_properties()
        self._update_properties = True

    def _calculate_stack(self):

        # get bottom and top separator layers
        bottom_separator = deepcopy(self.layup._bottom_separator)
        top_separator = deepcopy(self.layup._top_separator)

        # estimate thickness of stack
        thickness = (
            self.n_layers * self.layup.cathode._thickness + \
            (self.n_layers + 1) * self.layup.anode._thickness + \
            ((self.n_layers * 2 + 1) + 2 * self.additional_separator_wraps) * self.layup._bottom_separator._thickness
        ) * M_TO_MM

        # Initialize dictionaries for components
        stack = {}

        # set the starting z datum
        z_datum = 0

        # for each additional separator wrap, add a separator to bottom
        for _ in range(self._additional_separator_wraps):
            bottom_separator_copy = deepcopy(bottom_separator)
            bottom_separator.length = bottom_separator.length + thickness
            z_datum, stack = self.add_layer(stack, bottom_separator_copy, z_datum)

        # add bottom separator to stack
        z_datum, stack = self.add_layer(stack, self.layup._bottom_separator, z_datum)

        # add anode to stack
        z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add layups to stack
        for _ in range(self.n_layers):
            z_datum, stack = self.add_layer(stack, bottom_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._cathode, z_datum)
            z_datum, stack = self.add_layer(stack, top_separator, z_datum)
            z_datum, stack = self.add_layer(stack, self.layup._anode, z_datum)

        # add top separator to stack
        z_datum, stack = self.add_layer(stack, top_separator, z_datum)

        # for each additional separator wrap, add a separator to top
        for _ in range(self._additional_separator_wraps):
            top_separator_copy = deepcopy(top_separator)
            top_separator.length = top_separator.length + thickness
            z_datum, stack = self.add_layer(stack, top_separator_copy, z_datum)

        self._stack = stack

        return self._stack

    def _calculate_mass_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._mass = sum([a._mass for a in anodes]) + sum([c._mass for c in cathodes]) + sum([s._mass for s in separators])

        self._mass_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "mass"),
            "Cathodes": self.sum_breakdowns(cathodes, "mass"),
            "Separator": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self):

        anodes = [a for a in self._stack.values() if type(a) == Anode]
        cathodes = [c for c in self._stack.values() if type(c) == Cathode]
        separators = [s for s in self._stack.values() if type(s) == Separator]

        self._cost = sum([a._cost for a in anodes]) + sum([c._cost for c in cathodes]) + sum([s._cost for s in separators])

        self._cost_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "cost"),
            "Cathodes": self.sum_breakdowns(cathodes, "cost"),
            "Separator": self.sum_breakdowns(separators, "cost"),
        }

        return self._cost

    @property
    def additional_separator_wraps(self) -> int:
        """Return the number of additional separator wraps."""
        return self._additional_separator_wraps

    @property
    def layup(self) -> ZFoldMonoLayer:
        """Return the underlying `ZFoldMonoLayer` instance."""
        return self._layup

    @additional_separator_wraps.setter
    @calculate_bulk_properties
    def additional_separator_wraps(self, value: float):
        self.validate_positive_float(value, "additional_separator_wraps")
        self._additional_separator_wraps = value

    @layup.setter
    @calculate_all_properties
    def layup(self, value: ZFoldMonoLayer):
        self.validate_type(value, ZFoldMonoLayer, "layup")
        self._layup = value


class PunchedStack(_Stack):
    """Mono-layer stack electrode assembly.

    Accepts a `MonoLayer` layup representing stacked sheets in a mono-layer configuration.
    """
    def __init__(
            self, 
            layup: MonoLayer,
            n_layers: int
        ):

        super().__init__(
            layup,
            n_layers
        )

        self._calculate_all_properties()
        self._update_properties = True
    
    @property
    def layup(self) -> MonoLayer:
        """Return the underlying `MonoLayer` instance."""
        return self._layup

    @layup.setter
    @calculate_all_properties
    def layup(self, value: MonoLayer):
        self.validate_type(value, MonoLayer, "layup")
        self._layup = value



