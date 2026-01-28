import math
from steer_opencell_design.Constructions.Layups.MonoLayers import MonoLayer, ZFoldMonoLayer

from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties

from steer_core.Constants.Units import *
from steer_core.Constants.Universal import PI

from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies.Base import _ElectrodeAssembly

from copy import deepcopy
import numpy as np
import pandas as pd
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
            n_layers: int = 1,
            name: str = "Stack"
        ) -> None:

        super().__init__(layup, name=name)
        self.n_layers = n_layers

    def _calculate_geometry_parameters(self) -> None:
        """Calculate geometry parameters - placeholder for implementation."""
        self._thickness = sum(component._thickness for component in self._stack.values())

    def _calculate_datum(self): 

        _x_datums = [c._datum[0] for c in self._stack.values()]
        _y_datums = [c._datum[1] for c in self._stack.values()]
        _z_datums = [c._datum[2] for c in self._stack.values()]

        _datum = (
            np.mean(_x_datums),
            np.mean(_y_datums),
            np.mean(_z_datums)
        )

        if not hasattr(self, '_datum') or self._datum == None:
            self._datum = _datum
        else:
            _old_datum = self._datum
            old_datum = tuple(d * M_TO_MM for d in _old_datum)
            self._datum = _datum
            self.datum = old_datum  # triggers the setter to reposition components
    
    def _calculate_all_properties(self) -> None:
        """Calculate all properties including stack configuration."""
        self._calculate_stack()
        super()._calculate_all_properties()
        self._calculate_geometry_parameters()
        self._calculate_datum()

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

    def _calculate_pore_volume(self):
        
        _cathodes = [c for c in self._stack.values() if isinstance(c, Cathode)]
        _anodes = [a for a in self._stack.values() if isinstance(a, Anode)]

        _cathode_pore_volume = sum([c._pore_volume for c in _cathodes])
        _anode_pore_volume = sum([a._pore_volume for a in _anodes])

        self._pore_volume = _cathode_pore_volume + _anode_pore_volume

    def _get_center_point(self) -> Tuple[float, float, float]:
        """Get the center point of the stack assembly.
        
        Calculates the geometric center by finding the bounding box of all
        current collectors and separators.
        
        Returns
        -------
        Tuple[float, float, float]
            (x, y, z) coordinates of the center point in millimeters
        """
        cathodes = [c for c in self._stack.values() if isinstance(c, Cathode)]
        anodes = [a for a in self._stack.values() if isinstance(a, Anode)]
        current_collectors = [c._current_collector for c in cathodes + anodes]
        separators = [s for s in self._stack.values() if isinstance(s, Separator)]

        # Get the overall coordinates
        _cc_coordinates = np.vstack([cc._foil_coordinates for cc in current_collectors])
        _separator_coordinates = np.vstack([s._coordinates for s in separators])
        _all_coordinates = np.vstack([_cc_coordinates, _separator_coordinates])

        # Get the bounding box
        _max_x = _all_coordinates[:, 0].max()
        _min_x = _all_coordinates[:, 0].min()
        _max_y = _all_coordinates[:, 1].max()
        _min_y = _all_coordinates[:, 1].min()
        _max_z = _all_coordinates[:, 2].max()
        _min_z = _all_coordinates[:, 2].min()

        # Get the midpoints
        _mid_x = (_max_x + _min_x) / 2
        _mid_y = (_max_y + _min_y) / 2
        _mid_z = (_max_z + _min_z) / 2

        return (_mid_x, _mid_y, _mid_z)
    
    def _clip_current_collector_tabs(self, _clipped_length: float) -> None:
        """Clip current collector tabs to specified length."""
        
        # clip current collector tabs on cathode
        self._layup._cathode._current_collector.tab_height = _clipped_length * M_TO_MM
        self._layup._cathode.current_collector = self._layup._cathode._current_collector
        self._layup.cathode = self._layup._cathode
        
        # clip current collector tabs on anode
        self._layup._anode._current_collector.tab_height = _clipped_length * M_TO_MM
        self._layup._anode.current_collector = self._layup._anode._current_collector
        self._layup.anode = self._layup._anode
        
        # set the new layup to self
        self.layup = self._layup

    def get_side_view(self, **kwargs):
        """
        Generate an optimized side view of the stack with grouped component traces.
        
        Returns
        -------
        go.Figure
            Plotly figure showing the stack side view
        """
        # Group components by type
        cathodes = [c for c in self._stack.values() if isinstance(c, Cathode)]
        anodes = [a for a in self._stack.values() if isinstance(a, Anode)]
        separators = [s for s in self._stack.values() if isinstance(s, Separator)]
        
        traces = []
        
        # Define trace configurations for cleaner code
        trace_configs = [
            (cathodes, '_a_side_coating_coordinates', "Cathode A Side", lambda c: c._formulation._color),
            (cathodes, '_current_collector._foil_coordinates', "Cathode Current Collector", lambda c: c._current_collector._material._color),
            (cathodes, '_b_side_coating_coordinates', "Cathode B Side", lambda c: c._formulation._color),
            (anodes, '_a_side_coating_coordinates', "Anode A Side", lambda a: a._formulation._color),
            (anodes, '_current_collector._foil_coordinates', "Anode Current Collector", lambda a: a._current_collector._material._color),
            (anodes, '_b_side_coating_coordinates', "Anode B Side", lambda a: a._formulation._color),
            (separators, '_coordinates', "Separator", lambda s: s._material._color),
        ]
        
        # Process each trace configuration
        for components, coord_attr, name, color_func in trace_configs:
            trace = self.create_component_trace(
                components, 
                coord_attr, 
                name, 
                0.1, 
                color_func, 
                unit_conversion_factor=M_TO_MM,
                order_clockwise='yz',
                gl=True
            )
            traces.append(trace)
        
        # Create figure with all traces
        figure = go.Figure(data=traces)
        
        # Apply layout
        figure.update_layout(
            xaxis=self.SCHEMATIC_Y_AXIS,
            yaxis=self.SCHEMATIC_Z_AXIS,
            paper_bgcolor=kwargs.get("paper_bgcolor", "white"),
            plot_bgcolor=kwargs.get("plot_bgcolor", "white"),
            **kwargs,
        )
        
        return figure

    def get_top_down_view(self, **kwargs):
        return self._layup.get_top_down_view(**kwargs)

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

        # if electrode then clear its cached data
        if type(new_component) in [Cathode, Anode]:
            new_component._clear_cached_data()

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

    @classmethod
    def from_layup(
        cls, 
        layup: Union[MonoLayer, ZFoldMonoLayer], 
        n_layers: int = 1,
        **kwargs
    ) -> '_Stack':
        """Create appropriate stack type from layup.
        
        Parameters
        ----------
        layup : MonoLayer or ZFoldMonoLayer
            The layup configuration
        n_layers : int
            Number of layers in the stack
        **kwargs
            Additional arguments for specific stack types
            
        Returns
        -------
        _Stack
            ZFoldStack for ZFoldMonoLayer, PunchedStack for MonoLayer
        """
        if isinstance(layup, ZFoldMonoLayer):
            additional_separator_wraps = kwargs.get('additional_separator_wraps', 1)
            name = kwargs.get('name', 'ZFoldStack')
            return ZFoldStack(layup, n_layers, additional_separator_wraps, name)
            
        elif isinstance(layup, MonoLayer):
            name = kwargs.get('name', 'PunchedStack')
            return PunchedStack(layup, n_layers, name)
            
        else:
            raise ValueError(f"Unsupported layup type: {type(layup)}")

    @property
    def stack(self) -> dict:
        """Return the stack of components."""
        return self._stack

    @property
    def n_layers(self) -> int:
        """Return the number of layers in the stack."""
        return np.round(self._n_layers, 0)
    
    @property
    def n_layers_range(self) -> Tuple[int, int]:
        """Return the valid range for number of layers as a tuple (min, max)."""
        return (1, 60)
    
    @property
    def n_layers_hard_range(self) -> Tuple[int, int]:
        """Return the hard range for number of layers as a tuple (min, max)."""
        return (1, 1000)
    
    @property
    def thickness(self) -> float:
        """Return the total thickness of the stack in mm."""
        return np.round(self._thickness * M_TO_MM, 2)
    
    @property
    def thickness_range(self) -> Tuple[float, float]:
        """Return the valid range for stack thicknesses in mm as a tuple (min, max)."""
        min_n_layers, max_n_layers = self.n_layers_range
        
        # Calculate thickness for n_layers = 1 and n_layers = 2
        stack_1 = deepcopy(self)
        stack_1.n_layers = 1
        thickness_1 = stack_1._thickness
        
        stack_2 = deepcopy(self)
        stack_2.n_layers = 2
        thickness_2 = stack_2._thickness
        
        # Linear extrapolation: thickness = base + slope * n_layers
        # From two points: (1, thickness_1) and (2, thickness_2)
        slope = thickness_2 - thickness_1
        base = thickness_1 - slope  # thickness at n_layers = 0
        
        # Calculate min and max thickness using linear relationship
        _min_thickness = base + slope * min_n_layers
        _max_thickness = base + slope * max_n_layers

        return (
            math.ceil(_min_thickness * M_TO_MM * 100) / 100,
            math.floor(_max_thickness * M_TO_MM * 100) / 100
        )
        
    @property
    def thickness_hard_range(self) -> Tuple[float, float]:
        """Return the valid range for stack thicknesses in mm as a tuple (min, max)."""
        min_n_layers, max_n_layers = self.n_layers_hard_range
        
        # Calculate thickness for n_layers = 1 and n_layers = 2
        stack_1 = deepcopy(self)
        stack_1.n_layers = 1
        thickness_1 = stack_1._thickness
        
        stack_2 = deepcopy(self)
        stack_2.n_layers = 2
        thickness_2 = stack_2._thickness
        
        # Linear extrapolation: thickness = base + slope * n_layers
        # From two points: (1, thickness_1) and (2, thickness_2)
        slope = thickness_2 - thickness_1
        base = thickness_1 - slope  # thickness at n_layers = 0
        
        # Calculate min and max thickness using linear relationship
        _min_thickness = base + slope * min_n_layers
        _max_thickness = base + slope * max_n_layers

        return (
            math.ceil(_min_thickness * M_TO_MM * 100) / 100,
            math.floor(_max_thickness * M_TO_MM * 100) / 100
        )

    @property
    def layup(self) -> ZFoldMonoLayer | MonoLayer:
        return self._layup

    @property
    def datum(self) -> Tuple[float, float, float]:
        """Get the datum position in mm."""
        return tuple(round(coord * M_TO_MM, 2) for coord in self._datum)

    @datum.setter
    def datum(self, value: Tuple[float, float, float]):

        # Validate input
        self.validate_datum(value)

        # value in m
        _value = tuple(coord * MM_TO_M for coord in value)

        # get the translation vector
        _translation_vector = (
            _value[0] - self._datum[0],
            _value[1] - self._datum[1],
            _value[2] - self._datum[2],
        )

        # go through each component and apply the translation
        for component in self._stack.values():
            component.datum = (
                (component._datum[0] + _translation_vector[0]) * M_TO_MM,
                (component._datum[1] + _translation_vector[1]) * M_TO_MM,
                (component._datum[2] + _translation_vector[2]) * M_TO_MM,
            )

        # translate the layup
        self._layup.datum = (
            (self._layup._cathode._datum[0] + _translation_vector[0]) * M_TO_MM,
            (self._layup._cathode._datum[1] + _translation_vector[1]) * M_TO_MM,
            (self._layup._cathode._datum[2] + _translation_vector[2]) * M_TO_MM,
        )

        # update the stack datum
        self._datum = _value

    @n_layers.setter
    @calculate_all_properties
    def n_layers(self, value: float):
        self.validate_positive_float(value, "n_layers")
        value = int(round(value, 0))
        self._n_layers = value

    @thickness.setter
    def thickness(self, target_thickness: float) -> None:
        """Set thickness by calculating required number of layers.
        
        Uses the linear relationship between thickness and n_layers to determine
        the number of layers needed for the target thickness.
        
        Parameters
        ----------
        target_thickness : float
            Target thickness in millimeters
            
        Raises
        ------
        ValueError
            If target thickness is outside achievable range
        """
        # Validate input
        self.validate_positive_float(target_thickness, "thickness")
        
        # Check if target is within achievable range
        thickness_min, thickness_max = self.thickness_range
        if target_thickness < thickness_min or target_thickness > thickness_max:
            raise ValueError(
                f"Target thickness {target_thickness} mm is outside achievable range of "
                f"{thickness_min} mm to {thickness_max} mm."
            )
        
        # Get the linear relationship parameters
        min_n_layers, max_n_layers = self.n_layers_hard_range
        min_thickness, max_thickness = self.thickness_hard_range
        
        # Linear relationship: thickness = base + slope * n_layers
        slope = (max_n_layers - min_n_layers) / (max_thickness - min_thickness)
        base = min_n_layers - slope * min_thickness

        # Solve for n_layers: n_layers = (thickness - base) / slope
        calculated_n_layers = slope * target_thickness + base

        # set 
        self.n_layers = calculated_n_layers

    @layup.setter
    @calculate_all_properties  
    def layup(self, value: Union[MonoLayer, ZFoldMonoLayer]):
        self._layup = value


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
            additional_separator_wraps: float = 1,
            name: str = "ZFoldStack"
        ) -> None:

        super().__init__(layup, n_layers, name=name)
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
    def additional_separator_wraps_range(self) -> Tuple[int, int]:
        """Return the valid range for additional separator wraps as a tuple (min, max)."""
        return (0, 10)

    @additional_separator_wraps.setter
    @calculate_all_properties
    def additional_separator_wraps(self, value: float):

        # Validate input
        self.validate_positive_float(value, "additional_separator_wraps")
        
        # Round to nearest integer
        value = int(round(value, 0))
        
        # set the value
        self._additional_separator_wraps = value

    @property
    def layup(self) -> MonoLayer:
        return self._layup
    
    @layup.setter
    @calculate_all_properties  
    def layup(self, value: Union[MonoLayer, ZFoldMonoLayer]):

        """Set layup and convert stack type if needed."""
        self.validate_type(value, (MonoLayer, ZFoldMonoLayer), "layup")
        
        if self._update_properties:

            # If layup type changed, convert the entire stack
            current_layup_type = type(self._layup)
            new_layup_type = type(value)
            
            if current_layup_type != new_layup_type:
        
                # Create new stack of appropriate type
                converted_stack = self.from_layup(
                    layup=value,
                    n_layers=self.n_layers,
                    name=self.name
                )
                
                # Replace current instance with converted stack
                self.__class__ = converted_stack.__class__
                self.__dict__.update(converted_stack.__dict__)
            
        else:
            # Same type, just update layup
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
            n_layers: int,
            name: str = "PunchedStack"
        ) -> None:

        super().__init__(layup, n_layers, name=name)
        self._calculate_all_properties()
        self._update_properties = True
    
    @property
    def layup(self) -> MonoLayer:
        return self._layup
    
    @layup.setter
    @calculate_all_properties  
    def layup(self, value: Union[MonoLayer, ZFoldMonoLayer]):

        """Set layup and convert stack type if needed."""
        self.validate_type(value, (MonoLayer, ZFoldMonoLayer), "layup")
        
        if self._update_properties:

            # If layup type changed, convert the entire stack
            current_layup_type = type(self._layup)
            new_layup_type = type(value)
            
            if current_layup_type != new_layup_type:
        
                # Create new stack of appropriate type
                converted_stack = self.from_layup(
                    layup=value,
                    n_layers=self.n_layers,
                    name=self.name
                )
                
                # Replace current instance with converted stack
                self.__class__ = converted_stack.__class__
                self.__dict__.update(converted_stack.__dict__)
            
        else:
            # Same type, just update layup
            self._layup = value


