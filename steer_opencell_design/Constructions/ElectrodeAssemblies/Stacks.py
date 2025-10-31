from steer_opencell_design.Constructions.Layups import MonoLayer, ZFoldMonoLayer

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly

from copy import deepcopy
import numpy as np
from shapely.geometry import Polygon
import plotly.graph_objects as go
from typing import Dict, Tuple, Union, Any


class _Stack(_ElectrodeAssembly):
    """
    Stack electrode assembly base class.

    Accepts a `MonoLayer` or `ZFoldMonoLayer` layup representing stacked sheets.
    
    Parameters
    ----------
    layup : MonoLayer | ZFoldMonoLayer
        The layup configuration for the stack
    n_layers : int, optional
        Number of layers in the stack, by default 1
        
    Raises
    ------
    ValueError
        If n_layers is not a positive integer
    """
    def __init__(
            self, 
            layup: Union[MonoLayer, ZFoldMonoLayer],
            n_layers: int = 1
        ) -> None:

        super().__init__(layup)
        self.n_layers = n_layers

    def _calculate_geometry_parameters(self) -> None:
        """Calculate geometry parameters - placeholder for implementation."""
        pass

    def _calculate_all_properties(self) -> None:
        """Calculate all properties including stack configuration."""
        self._calculate_stack()
        super()._calculate_all_properties()

    def _calculate_stack(self) -> Dict[int, Any]:
        
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

    def _calculate_interfacial_area(self) -> float:
        """
        Calculate the interfacial area between anode and cathode electrodes.
        
        Returns
        -------
        float
            Total interfacial area in square meters
            
        Raises
        ------
        ValueError
            If electrode coordinates are invalid or missing
        """
        # Constants
        Z_TOLERANCE = 1e-8
        
        try:
            # Get anode polygon from top surface coordinates
            anode_coords = self._layup._anode._a_side_coating_coordinates
            if len(anode_coords) == 0:
                raise ValueError("Anode coordinates are empty")
                
            max_z_anode = np.max(anode_coords[:, 2])
            top_anode_coords = anode_coords[
                np.abs(anode_coords[:, 2] - max_z_anode) < Z_TOLERANCE
            ][:, :2]
            anode_polygon = Polygon(top_anode_coords)

            # Get cathode polygon from top surface coordinates  
            cathode_coords = self._layup._cathode._a_side_coating_coordinates
            if len(cathode_coords) == 0:
                raise ValueError("Cathode coordinates are empty")
                
            max_z_cathode = np.max(cathode_coords[:, 2])
            top_cathode_coords = cathode_coords[
                np.abs(cathode_coords[:, 2] - max_z_cathode) < Z_TOLERANCE
            ][:, :2]
            cathode_polygon = Polygon(top_cathode_coords)

            # Calculate intersection area
            intersection_polygon = anode_polygon.intersection(cathode_polygon)
            single_layer_interfacial_area = intersection_polygon.area

            # Count cathodes to determine number of interfaces
            cathodes = [c for c in self._stack.values() if isinstance(c, Cathode)]
            n_interfaces = len(cathodes) * 2  # Each cathode has two interfaces

            # Calculate total interfacial area
            self._interfacial_area = single_layer_interfacial_area * n_interfaces

        except (IndexError, ValueError) as e:
            raise ValueError(f"Failed to calculate interfacial area: {e}")

        return self._interfacial_area

    def _get_component_groups(self) -> Tuple[list, list, list]:
        """
        Extract component groups from the stack.
        
        Returns
        -------
        Tuple[list, list, list]
            Anodes, cathodes, and separators lists
        """
        anodes = [a for a in self._stack.values() if isinstance(a, Anode)]
        cathodes = [c for c in self._stack.values() if isinstance(c, Cathode)]
        separators = [s for s in self._stack.values() if isinstance(s, Separator)]
        return anodes, cathodes, separators

    def _calculate_mass_properties(self) -> float:
        """Calculate mass properties for all components in the stack."""
        anodes, cathodes, separators = self._get_component_groups()

        self._mass = (
            sum(a._mass for a in anodes) + 
            sum(c._mass for c in cathodes) + 
            sum(s._mass for s in separators)
        )

        self._mass_breakdown = {
            "Anodes": self.sum_breakdowns(anodes, "mass"),
            "Cathodes": self.sum_breakdowns(cathodes, "mass"),
            "Separators": self.sum_breakdowns(separators, "mass"),
        }

        return self._mass

    def _calculate_cost_properties(self) -> float:
        """Calculate cost properties for all components in the stack."""
        anodes, cathodes, separators = self._get_component_groups()

        self._cost = (
            sum(a._cost for a in anodes) + 
            sum(c._cost for c in cathodes) + 
            sum(s._cost for s in separators)
        )

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
    def add_layer(stack: Dict[int, Any], component: Any, z_datum: float) -> Tuple[float, Dict[int, Any]]:
        """
        Add a layer component to the stack at specified z-datum.
        
        Parameters
        ----------
        stack : Dict[int, Any]
            Current stack of components
        component : Any
            Component to add to the stack
        z_datum : float
            Current z-position datum
            
        Returns
        -------
        Tuple[float, Dict[int, Any]]
            Updated z_datum and stack with new component
            
        Raises
        ------
        ValueError
            If component is None or invalid
        """
        if component is None:
            raise ValueError("Component cannot be None")
            
        stack_size = len(stack)
        new_component = deepcopy(component)

        # Calculate new z-datum based on component thickness
        component_half_thickness = new_component._thickness * M_TO_MM / 2
        
        if stack_size == 0:
            # First component: place at z_datum + half thickness
            new_z_datum = z_datum + component_half_thickness
        else:
            # Subsequent components: account for previous component thickness
            prev_component = stack[stack_size - 1]
            prev_half_thickness = prev_component._thickness * M_TO_MM / 2
            new_z_datum = z_datum + component_half_thickness + prev_half_thickness

        # Update component datum with converted coordinates
        new_component.datum = (
            new_component._datum[0] * M_TO_MM, 
            new_component._datum[1] * M_TO_MM, 
            new_z_datum
        )
        
        # Add component to stack
        stack[len(stack)] = new_component

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
    """
    Z-Fold stack electrode assembly.

    Accepts a `ZFoldMonoLayer` layup representing stacked sheets in a Z-fold configuration.
    Additional separator wraps provide extra insulation around the stack.
    
    Parameters
    ----------
    layup : ZFoldMonoLayer
        The Z-fold layup configuration
    n_layers : int
        Number of electrode layers in the stack
    additional_separator_wraps : float, optional
        Number of additional separator wraps around the stack, by default 1
    """
    def __init__(
            self, 
            layup: ZFoldMonoLayer,
            n_layers: int,
            additional_separator_wraps: float = 1
        ) -> None:

        super().__init__(layup, n_layers)
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

    # ZFoldStack uses the same mass/cost calculation as base class
    # No need to override _calculate_mass_properties and _calculate_cost_properties

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
    """
    Punched mono-layer stack electrode assembly.

    Accepts a `MonoLayer` layup representing stacked sheets in a mono-layer configuration.
    This configuration is typically used with punched current collectors.
    
    Parameters
    ----------
    layup : MonoLayer
        The mono-layer layup configuration
    n_layers : int
        Number of electrode layers in the stack
    """
    def __init__(
            self, 
            layup: MonoLayer,
            n_layers: int
        ) -> None:

        super().__init__(layup, n_layers)
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



