from steer_core.Decorators.Coordinates import calculate_coordinates, calculate_volumes
from steer_core.Decorators.General import calculate_all_properties, calculate_bulk_properties
from steer_core.Decorators.Electrochemical import calculate_half_cell_curve

from steer_core.Mixins.Validators import ValidationMixin
from steer_core.Mixins.Coordinates import CoordinateMixin
from steer_core.Mixins.Serializer import SerializerMixin

from steer_core.Constants.Units import *

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation, _ElectrodeFormulation
from steer_opencell_design.Components.CurrentCollectors import _CurrentCollector

from steer_materials.CellMaterials.Base import InsulationMaterial

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings

from copy import deepcopy
from typing import Dict, Any, Tuple
from enum import Enum


class ElectrodeControlMode(Enum):
    """Control modes for electrode property interdependencies."""
    MAINTAIN_CALENDER_DENSITY = "maintain_calender_density"      # Keep calender density constant (current behavior)
    MAINTAIN_MASS_LOADING = "maintain_mass_loading"             # Keep mass loading constant
    MAINTAIN_COATING_THICKNESS = "maintain_coating_thickness"   # Keep coating thickness constant


class _Electrode(ValidationMixin, CoordinateMixin, SerializerMixin):
    """
    Base class for electrodes, representing the common properties and methods of an electrode.
    """
    def __init__(
            self, 
            formulation: _ElectrodeFormulation,
            mass_loading: float,
            current_collector: _CurrentCollector,
            calender_density: float,
            insulation_material: InsulationMaterial = None,
            insulation_thickness: float = 0.0,
            voltage_cutoff: float = None,
            name: str = 'Electrode',
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):
        """
        Initialize an object that represents an electrode.

        Parameters
        ----------
        formulation : _ElectrodeFormulation
            The formulation of the electrode, which includes active materials, binders, and conductive additives.
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
        voltage_cutoff : float, optional
            The maximum voltage of the half cell curves (default is None).
        name : str, optional
            The name of the electrode (default is 'Electrode').
        ----------
        """
        self._update_properties = False

        self.name = name
        self.formulation = formulation
        self.current_collector = current_collector
        self.datum = datum
        self.voltage_cutoff = voltage_cutoff
        self.insulation_material = insulation_material
        self.insulation_thickness = insulation_thickness
        self.mass_loading = mass_loading
        self.calender_density = calender_density

        # Calculate initial properties
        self._calculate_all_properties()

        # set final control mode
        self.control_mode = ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY

    # === CONTROL SYSTEM ===

    def _update_dependent_properties(self, property_name: str, new_val: float):
        """
        A dictionary that maps a mode to a function via the property that has been triggered
        """
        dependency_function = {
            ElectrodeControlMode.MAINTAIN_MASS_LOADING: {
                'mass_loading': self._calculate_coating_thickness,
                'calender_density': self._calculate_coating_thickness,
                'coating_thickness': self._calculate_calender_density,
            },
            ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: {
                'mass_loading': self._calculate_coating_thickness,
                'calender_density': self._calculate_coating_thickness,
                'coating_thickness': self._calculate_mass_loading,
            },
            ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: {
                'mass_loading': self._calculate_calender_density,
                'calender_density': self._calculate_mass_loading,
                'coating_thickness': self._calculate_mass_loading,
            }
        }

        dependency_inputs = {
            ElectrodeControlMode.MAINTAIN_MASS_LOADING: {
                'mass_loading': (new_val, self.calender_density),
                'calender_density': (self.mass_loading, new_val),
                'coating_thickness': (self.mass_loading, new_val),
            },
            ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: {
                'mass_loading': (new_val, self.calender_density),
                'calender_density': (self.mass_loading, new_val),
                'coating_thickness': (self.calender_density, new_val),
            },
            ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: {
                'mass_loading': (new_val, self.coating_thickness),
                'calender_density': (new_val, self.coating_thickness),
                'coating_thickness': (self.calender_density, new_val)
            }
        }

        update_function = dependency_function[self.control_mode].get(property_name)
        inputs = dependency_inputs[self.control_mode].get(property_name)

        # execute update
        update_function(inputs[0], inputs[1])

    @property
    def control_mode(self) -> ElectrodeControlMode:
        """Get the current control mode."""
        return self._control_mode

    @control_mode.setter
    def control_mode(self, mode: ElectrodeControlMode):
        if not isinstance(mode, ElectrodeControlMode):
            raise ValueError(f"Mode must be an ElectrodeControlMode enum, got {type(mode)}")
        self._control_mode = mode

    def _calculate_mass_loading(self, calender_density: float, coating_thickness: float) -> None:
        _calender_density = calender_density * (G_TO_KG / CM_TO_M**3)
        _coating_thickness = coating_thickness * UM_TO_M
        self._mass_loading = _calender_density * _coating_thickness

    def _calculate_coating_thickness(self, mass_loading: float, calender_density: float) -> None:
        _mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)
        _calender_density = calender_density * (G_TO_KG / CM_TO_M**3)
        self._coating_thickness = _mass_loading / _calender_density

    def _calculate_calender_density(self, mass_loading: float, coating_thickness: float) -> None:
        _mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)
        _coating_thickness = coating_thickness * UM_TO_M
        self._calender_density = _mass_loading / _coating_thickness

    # === CALCULATE PROPERTIES ===

    def _calculate_all_properties(self) -> None:
        self._calculate_coating_thickness(self.mass_loading, self.calender_density)
        self._calculate_bulk_properties()
        self._calculate_half_cell_curve()
        self._calculate_coordinates()

    def _calculate_half_cell_curve(self) -> None:

        # get the half cell curve from the formulation
        curve = self._formulation._half_cell_curve.copy()

        # calculate the capacity
        capacity = curve[:, 0] * self._coating_mass

        # calculate the areal capacity
        areal_capacity = capacity / self._current_collector._coated_area
        
        # set 
        self._half_cell_curve = np.column_stack([curve, capacity, areal_capacity])

    def _calculate_bulk_properties(self) -> None:
        self._calculate_porosity()
        self._calculate_thickness_properties()
        self._calculate_mass_properties()
        self._calculate_cost_properties()

    def _calculate_coordinates(self) -> None:
        """Calculate coating and insulation coordinates for both sides of the electrode."""
        
        def _calculate_side_coordinates(side: str) -> None:
            """Calculate coordinates for one side (a or b)."""
            side_multiplier = 1 if side == 'a' else -1
            
            # Calculate coating coordinates
            coating_coordinates = getattr(self._current_collector, f'_{side}_side_coated_coordinates')

            coating_datum = (
                self._datum[0], 
                self._datum[1], 
                self._datum[2] + side_multiplier * (self._current_collector._thickness / 2 + self._coating_thickness / 2)
            )
            
            x, y, z, _ = self.extrude_footprint(
                coating_coordinates[:, 0],
                coating_coordinates[:, 1],
                coating_datum,
                self._coating_thickness,
            )

            setattr(self, f'_{side}_side_coating_coordinates', np.column_stack([x, y, z]))
            
            if (hasattr(self._current_collector, f'_{side}_side_insulation_coordinates') and 
                getattr(self._current_collector, f'_{side}_side_insulation_coordinates') is not None):

                # Calculate insulation coordinates
                insulation_coordinates = getattr(self._current_collector, f'_{side}_side_insulation_coordinates')
                
                x, y, z, _ = self.extrude_footprint(
                    insulation_coordinates[:, 0],
                    insulation_coordinates[:, 1],
                    coating_datum,  # Use same datum as coating
                    self._insulation_thickness,
                )

                setattr(self, f'_{side}_side_insulation_coordinates', np.column_stack([x, y, z]))

            else:
                # If no insulation coordinates, set to empty array
                setattr(self, f'_{side}_side_insulation_coordinates', None)
        
        # Calculate for both sides
        _calculate_side_coordinates('a')
        _calculate_side_coordinates('b')

    def _calculate_mass_properties(self) -> None:
        """
        Calculate the mass properties of the electrode.
        """
        self._coating_mass = self._current_collector._coated_area * self._mass_loading
        
        # Only calculate insulator mass if insulation thickness is initialized
        if hasattr(self, '_insulation_thickness'):
            self._insulator_mass = self._current_collector._insulation_area * self._insulation_material._density * self._insulation_thickness if self._insulation_material else 0.0
        else:
            self._insulator_mass = 0.0
            
        self._mass = self._coating_mass + self._current_collector._mass + self._insulator_mass

        # Only calculate mass breakdown if minimum coating volume exists
        if hasattr(self, '_minimum_coating_volume'):
            self._mass_breakdown = (
                {k: float(v * self._minimum_coating_volume) for k, v in self._formulation._density_breakdown.items()} | 
                {self._current_collector.name: self._current_collector._mass} |
                ({self._insulation_material.name: self._insulator_mass} if self._insulation_material else {})
            )
            
    def _calculate_cost_properties(self) -> None:
        """
        Calculate the cost properties of the electrode.
        """
        self._coating_cost = self._coating_mass * self._formulation._specific_cost
        self._insulator_cost = self._insulator_mass * self._insulation_material._specific_cost if self._insulation_material else 0.0
        self._cost = self._coating_cost + self._current_collector._cost + self._insulator_cost

        self._cost_breakdown = (
            {k: float(v * self._coating_mass) for k, v in self._formulation._specific_cost_breakdown.items()} |
            {self._current_collector.name: self._current_collector._cost} |
            ({self._insulation_material.name: self._insulator_cost} if self._insulation_material else {})
        )

    def _calculate_thickness_properties(self) -> None:
        """
        Calculate the thickness properties of the electrode.
        """
        self._coating_volume = self._current_collector._coated_area * self._coating_thickness
        self._thickness = self._coating_thickness * 2 + self._current_collector._thickness
        self._pore_volume = self._coating_volume * self._porosity

        _minimum_coating_thickness = self._mass_loading / self._formulation._density
        self._minimum_coating_volume = _minimum_coating_thickness * self._current_collector._coated_area

        if self._coating_thickness < _minimum_coating_thickness:

            warnings.warn(f"""Your caldender density of {self.calender_density} g/cm^3 is too high, 
                           leading to negative porosity. Decrease your calender density below 
                           {self._formulation._density} g/cm^3.""", UserWarning)

        if self._insulation_thickness > self._coating_thickness:

            warnings.warn(f"""Insulation thickness is greater than the coating thickness on {self.name}. 
                          Reduce the insulation thickness ({self.insulation_thickness}  um) 
                          or increase the coating thickness ({self.coating_thickness}  um)""", UserWarning)

    def _calculate_porosity(self) -> None:
        porosity = 1 - (self._formulation._specific_volume * self._calender_density)
        self._porosity = porosity

        if porosity < 0:
            warnings.warn(f"Negative porosity calculated for {self.name}.", UserWarning)

    # === VIEWS ===

    def _get_full_top_down_view(self, **kwargs) -> pd.DataFrame:
        """
        Helper method to get a top-down view of the electrode.
        """
        figure = self._current_collector._get_full_top_down_view(**kwargs)
        figure.data = [trace for trace in figure.data if trace.name == "Body" or trace.name == "Tab"]
        figure.add_trace(self.top_down_coating_trace)

        # Only add insulation trace if it exists and is not None
        insulation_trace = self.top_down_insulation_trace
        if insulation_trace is not None:
            figure.add_trace(insulation_trace)
        
        return figure

    def _get_full_right_left_view(self, **kwargs) -> pd.DataFrame:
        figure = self._current_collector.get_right_left_view(**kwargs)
        figure.data = [trace for trace in figure.data if trace.name == "Body" or trace.name == "Tab"]
        figure.add_trace(self.right_left_a_side_coating_trace)
        figure.add_trace(self.right_left_b_side_coating_trace)

        if hasattr(self, '_a_side_insulation_coordinates') and self._a_side_insulation_coordinates is not None:
            figure.add_trace(self.right_left_a_side_insulation_trace)
        if hasattr(self, '_b_side_insulation_coordinates') and self._b_side_insulation_coordinates is not None:
            figure.add_trace(self.right_left_b_side_insulation_trace)
            
        return figure

    def plot_half_cell_curve(self, areal: bool = True, **kwargs) -> None:
        """
        Plot the half cell curve of the electrode.

        Parameters
        ----------
        areal : bool, optional
            If True, plot the areal capacity instead of the specific capacity (default is False).
        """
        x_col = 'Capacity (Ah)' if not areal else 'Areal Capacity (mAh/cm²)'

        fig = px.line(
            self.half_cell_curve, 
            y='Voltage (V)', 
            x=x_col, 
            line_shape='spline', 
            template='presentation', 
            **kwargs
        )

        fig.update_traces(
            line=dict(color=self._formulation._color),
        )

        return fig    

    def get_top_down_view(self, **kwargs) -> go.Figure:
        
        figure = self.current_collector.get_top_down_view(**kwargs)
        figure.data = [trace for trace in figure.data if trace.name == "Body" or trace.name == "Tab"]
        
        # Get the traces to add
        coating_trace = self.top_down_coating_trace
        insulation_trace = self.top_down_insulation_trace
        
        # Check if this is a subplot figure by looking for subplot annotations
        is_subplot = hasattr(figure, '_grid_ref') and figure._grid_ref is not None
        
        if is_subplot:
            # Get the number of subplots
            rows = len(figure._grid_ref)
            cols = len(figure._grid_ref[0]) if rows > 0 else 0
            
            # Add traces to each subplot
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    # Create deep copies of the traces for each subplot
                    coating_trace_copy = deepcopy(coating_trace)
                    insulation_trace_copy = deepcopy(insulation_trace)
                    
                    # Set legend properties - only show in legend for first subplot
                    is_first_subplot = (row == 1 and col == 1)
                    
                    coating_trace_copy.showlegend = is_first_subplot
                    coating_trace_copy.legendgroup = coating_trace.name
                    
                    if insulation_trace_copy:
                        insulation_trace_copy.showlegend = is_first_subplot
                        insulation_trace_copy.legendgroup = insulation_trace.name
                    
                    # Add traces to specific subplot
                    figure.add_trace(coating_trace_copy, row=row, col=col)
                    if insulation_trace_copy:  # Check if insulation exists
                        figure.add_trace(insulation_trace_copy, row=row, col=col)
        else:
            # Regular figure - add traces normally
            figure.add_trace(coating_trace)
            if insulation_trace:  # Check if insulation exists
                figure.add_trace(insulation_trace)
        
        return figure

    def get_a_side_view(self, **kwargs) -> go.Figure:

        if self.top_side == 'a':
            return self.get_top_down_view(**kwargs)
        else:
            self._flip('y')
            figure = self.get_top_down_view(**kwargs)
            self._flip('y')
            return figure

    def get_b_side_view(self, **kwargs) -> go.Figure:

        if self.top_side == 'b':
            return self.get_top_down_view(**kwargs)
        else:
            self._flip('y')
            figure = self.get_top_down_view(**kwargs)
            self._flip('y')
            return figure

    def get_cross_section(self, **kwargs) -> go.Figure:
        """
        Get a cross-section view of the electrode, zoomed in around the datum.
        """
        figure = self._get_full_right_left_view(**kwargs)
        
        # Get datum coordinates in mm (for plotting)
        datum_y = self.datum[1]  # y-coordinate of datum
        datum_z = self.datum[2]  # z-coordinate of datum
        
        # Get total thickness in mm (electrode thickness includes coating on both sides + current collector)
        total_thickness_mm = self.thickness * UM_TO_MM
        
        # Calculate zoom range (1.5x the thickness)
        zoom_range = total_thickness_mm * 1.5
        half_range = zoom_range / 2
        
        # Set axis ranges centered on datum
        y_range = [datum_y - half_range, datum_y + half_range]
        
        # Update layout to zoom in and lock aspect ratio
        figure.update_layout(
            xaxis=dict(
                range = y_range,
                scaleanchor="y",  # Lock aspect ratio
                scaleratio=1,
            ),
            yaxis=dict(
                scaleratio=1,
            ),
            **kwargs
        )
        
        return figure

    @property
    def right_left_a_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the a side insulated area.
        """
        # get the coordinates
        a_side_insulation_coordinates = self.order_coordinates_clockwise(self.a_side_insulation_coordinates, plane='yz')

        # make the trace
        a_side_insulation_trace = go.Scatter(
            x=a_side_insulation_coordinates['y'],
            y=a_side_insulation_coordinates['z'],
            mode='lines',
            name='A Side Insulated Area',
            line=dict(width=1, color='black'),
            fill='toself',
            fillcolor=self._insulation_material._color,
            legendgroup='A Side Insulated Area',
            showlegend=True
        )

        return a_side_insulation_trace
    
    @property
    def right_left_b_side_insulation_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the b side insulated area.
        """
        # get the coordinates
        b_side_insulation_coordinates = self.order_coordinates_clockwise(self.b_side_insulation_coordinates, plane='yz')

        # make the trace
        b_side_insulation_trace = go.Scatter(
            x=b_side_insulation_coordinates['y'],
            y=b_side_insulation_coordinates['z'],
            mode='lines',
            name='B Side Insulated Area',
            line=dict(width=1, color='black'),
            fill='toself',
            fillcolor=self._insulation_material._color,
            legendgroup='B Side Insulated Area',
            showlegend=True
        )

        return b_side_insulation_trace

    @property
    def right_left_a_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the a side coated area.
        """
        # get the coordinates
        a_side_coating_coordinates = self.order_coordinates_clockwise(self.a_side_coating_coordinates, plane='yz')

        # make the trace
        a_side_coating_trace = go.Scatter(
            x=a_side_coating_coordinates['y'],
            y=a_side_coating_coordinates['z'],
            mode='lines',
            name='A Side Coated Area',
            line=dict(width=1, color='black'),
            fill='toself',
            fillcolor=self._formulation._color,
            legendgroup='A Side Coated Area',
            showlegend=True
        )

        return a_side_coating_trace

    @property
    def right_left_b_side_coating_trace(self) -> pd.DataFrame:
        """
        Get the coordinates of the b side coated area.
        """
        # get the coordinates
        b_side_coating_coordinates = self.order_coordinates_clockwise(self.b_side_coating_coordinates, plane='yz')

        # make the trace
        b_side_coating_trace = go.Scatter(
            x=b_side_coating_coordinates['y'],
            y=b_side_coating_coordinates['z'],
            mode='lines',
            name='B Side Coated Area',
            line=dict(width=1, color='black'),
            fill='toself',
            fillcolor=self._formulation._color,
            legendgroup='B Side Coated Area',
            showlegend=True
        )

        return b_side_coating_trace

    @property
    def top_side(self) -> str:
        return self._current_collector.top_side

    @property
    def top_down_coating_trace(self) -> go.Scatter:

        side = self.current_collector.top_side
        coated_area_coordinates = self.a_side_coating_coordinates if side == 'a' else self.b_side_coating_coordinates

        # make the coated area trace
        coated_area_trace = go.Scatter(
            x=coated_area_coordinates['x'], 
            y=coated_area_coordinates['y'], 
            mode='lines', 
            name='A Side Coating' if side == 'a' else 'B Side Coating',
            line=dict(width=1, color='black'), 
            fillcolor=self.formulation.color, 
            fill='toself',
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
        insulation_coordinates = self.a_side_insulation_coordinates if side == 'a' else self.b_side_insulation_coordinates

        # make the insulation area trace
        insulation_area_trace = go.Scatter(
            x=insulation_coordinates['x'], 
            y=insulation_coordinates['y'], 
            mode='lines', 
            name='A Side Insulation' if side == 'a' else 'B Side Insulation',
            line=dict(width=1, color='black'), 
            fillcolor=self.insulation_material.color, 
            fill='toself',
        )

        return insulation_area_trace

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
        if axis not in ['x', 'y', 'z']:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")

        # Flip the current collector first (this handles all current collector coordinates)
        self._current_collector._flip(axis)

    # === PROPERTIES ===

    @property
    def datum(self) -> Tuple[float, float, float]:
        """
        Get the datum of the electrode.

        :return: Tuple containing the x, y, z coordinates of the electrode's datum.
        """
        return (
            round(self._datum[0] * M_TO_MM, 1),
            round(self._datum[1] * M_TO_MM, 1),
            round(self._datum[2] * M_TO_MM, 1)
        )

    @property
    def formulation(self) -> _ElectrodeFormulation:
        return self._formulation

    @property
    def voltage_cutoff(self) -> float:
        return round(self._voltage_cutoff, 3)

    @property
    def insulation_material(self) -> InsulationMaterial:
        return self._insulation_material

    @property
    def properties(self) -> Dict[str, Any]:
        """
        Get the properties of the electrode.

        :return: Dictionary containing the properties of the electrode.
        """
        return {
            'Cost': f"$ {self.cost}",
            'Mass': f"{self.mass} g",
            'Coating mass': f"{self.coating_mass} g",
            'Total thickness': f"{self.thickness} um",
            'Coating thickness': f"{self.coating_thickness} um",
        }

    @property
    def insulation_thickness(self) -> float:
        """
        Get the insulation thickness of the electrode.

        :return: Insulation thickness of the electrode in micrometers.
        """
        return round(self._insulation_thickness * M_TO_UM, 2)

    @property
    def insulation_thickness_range(self) -> Tuple[float, float]:
        """
        Get the range of insulation thickness of the electrode.

        :return: Tuple containing the minimum and maximum insulation thickness in micrometers.
        """
        return (
            0, 
            self._coating_thickness * M_TO_UM
        )

    @property
    def coating_thickness(self) -> float:
        """
        Get the coating thickness of the electrode.

        :return: Coating thickness of the electrode in micrometers.
        """
        return round(self._coating_thickness * M_TO_UM, 2)

    @property
    def coating_thickness_range(self) -> Tuple[float, float]:
       return (10, 60)
    
    @property
    def coating_thickness_hard_range(self) -> Tuple[float, float]:
        return (0, 200)

    @property
    def coating_thickness_marks(self) -> Dict[str, float]:
        """
        Get the coating thickness marks of the electrode.

        :return: Dictionary containing the coating thickness marks.
        """
        min = np.ceil(self.coating_thickness_range[0])
        max = np.floor(self.coating_thickness_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 40)}

    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        """
        Get the cost breakdown of the electrode.

        :return: Dictionary containing the cost breakdown.
        """
        return {k: round(v, 2) for k, v in self._cost_breakdown.items()}

    @property
    def mass_breakdown(self) -> Dict[str, Any]:
        """
        Get the mass breakdown of the electrode.

        :return: Dictionary containing the mass breakdown.
        """
        return {k: round(v * KG_TO_G, 2) for k, v in self._mass_breakdown.items()}

    @property
    def half_cell_curve(self) -> pd.DataFrame:

        return (
            pd.DataFrame(
                self._half_cell_curve,
                columns=['specific_capacity', 'voltage', 'direction', 'capacity', 'areal_capacity']
            )
            .assign(
                direction = lambda x: np.where(x['direction'] == 1, 'charge', 'discharge'),
                specific_capacity = lambda x: x['specific_capacity'] * (S_TO_H * A_TO_mA / KG_TO_G),
                capacity = lambda x: x['capacity'] * (S_TO_H),
                areal_capacity = lambda x: x['areal_capacity'] * (S_TO_H * A_TO_mA / M_TO_CM**2)
            ).filter(
                    items=['capacity', 'voltage', 'direction', 'areal_capacity']
            ).rename(
                columns={
                    'capacity': 'Capacity (Ah)', 
                    'voltage': 'Voltage (V)', 
                    'direction': 'Direction',
                    'areal_capacity': 'Areal Capacity (mAh/cm²)'
                }
            ).round(
                4
            )
        )

    @property
    def porosity(self) -> float:
        """
        Get the porosity of the electrode.

        :return: Porosity of the electrode.
        """
        return round(self._porosity * 100, 2)
    
    @property
    def porosity_marks(self) -> Dict[str, float]:
        """
        Get the porosity marks of the electrode.

        :return: Dictionary containing the porosity marks.
        """
        min = np.ceil(self.porosity_range[0])
        max = np.floor(self.porosity_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 10)}
    
    @property
    def calender_density(self) -> float:
        """
        Get the calender density of the electrode.

        :return: Calender density of the electrode.
        """
        return round(self._calender_density * (KG_TO_G / M_TO_CM**3), 2)

    @property
    def calender_density_range(self) -> Tuple[float, float]:

        max_porosity = self.porosity_range[1] / 100
        min_porosity = self.porosity_range[0] / 100

        min_calender_density = ((1 - max_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)
        max_calender_density = ((1 - min_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)

        return (
            min_calender_density,
            max_calender_density
        )
    
    @property
    def calender_density_hard_range(self) -> Tuple[float, float]:
        
        max_porosity = self.porosity_hard_range[1] / 100
        min_porosity = self.porosity_hard_range[0] / 100

        min_calender_density = ((1 - max_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)
        max_calender_density = ((1 - min_porosity) / self._formulation._specific_volume) * (KG_TO_G / M_TO_CM**3)
     
        return (
            min_calender_density,
            max_calender_density
        )

    @property
    def calender_density_marks(self) -> Dict[str, float]:
        """
        Get the calender density marks of the electrode.

        :return: Dictionary containing the calender density marks.
        """
        min = np.ceil(self.calender_density_range[0])
        max = np.floor(self.calender_density_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 1)}

    @property
    def a_side_insulation_coordinates(self) -> pd.DataFrame:
        """
        Get the A side insulation coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._a_side_insulation_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'].astype(float) * M_TO_MM).round(10),
                y = lambda x: (x['y'].astype(float) * M_TO_MM).round(10),
                z = lambda x: (x['z'].astype(float) * M_TO_MM).round(10)
            )
        )
    
    @property
    def b_side_insulation_coordinates(self) -> pd.DataFrame:
        """
        Get the B side insulation coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._b_side_insulation_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'].astype(float) * M_TO_MM).round(10),
                y = lambda x: (x['y'].astype(float) * M_TO_MM).round(10),
                z = lambda x: (x['z'].astype(float) * M_TO_MM).round(10)
            )
        )

    @property
    def a_side_coating_coordinates(self) -> pd.DataFrame:
        """
        Get the A side coating coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._a_side_coating_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'].astype(float) * M_TO_MM).round(10),
                y = lambda x: (x['y'].astype(float) * M_TO_MM).round(10),
                z = lambda x: (x['z'].astype(float) * M_TO_MM).round(10)
            )
        ) 

    @property
    def b_side_coating_coordinates(self) -> pd.DataFrame:
        """
        Get the B side coating coordinates of the current collector.
        """
        return (
            pd.DataFrame(
                self._b_side_coating_coordinates,
                columns=['x', 'y', 'z']
            ).assign(
                x = lambda x: (x['x'].astype(float) * M_TO_MM).round(10),
                y = lambda x: (x['y'].astype(float) * M_TO_MM).round(10),
                z = lambda x: (x['z'].astype(float) * M_TO_MM).round(10)
            )
        ) 

    @property
    def mass_loading(self) -> float:
        """
        Get the mass loading of the electrode.

        :return: Mass loading of the electrode.
        """
        return round(self._mass_loading * (KG_TO_MG / M_TO_CM**2), 2)

    @property
    def mass_loading_range(self) -> Tuple[float, float]:

        return (
            self.calender_density_range[0] * self.coating_thickness_range[0] * UM_TO_CM * G_TO_mG,
            self.calender_density_range[1] * self.coating_thickness_range[1] * UM_TO_CM * G_TO_mG
        )
    
    @property
    def mass_loading_hard_range(self) -> Tuple[float, float]:
        return (
            self.calender_density_hard_range[0] * self.coating_thickness_hard_range[0] * UM_TO_CM * G_TO_mG,
            self.calender_density_hard_range[1] * self.coating_thickness_hard_range[1] * UM_TO_CM * G_TO_mG
        )

    @property
    def mass_loading_marks(self) -> Dict[str, float]:
        """
        Get the mass loading marks of the electrode.

        :return: Dictionary containing the mass loading marks.
        """
        min = np.ceil(self.mass_loading_range[0])
        max = np.floor(self.mass_loading_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 10)}

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
    def coating_mass(self) -> float:
        """
        Get the coating mass of the electrode.

        :return: Coating mass of the electrode.
        """
        return round(self._coating_mass * KG_TO_G, 2)

    @property
    def mass(self) -> float:
        """
        Get the mass of the electrode.

        :return: Mass of the electrode.
        """
        return round(self._mass * KG_TO_G, 2)

    @property
    def mass_range(self) -> Tuple[float, float]:

        min = 0
        hyp_max = 1
        max = hyp_max * (1 - np.exp(-0.5/self._mass))

        return (
            round(min * KG_TO_G, 2), 
            round(max * KG_TO_G, 2)
        )

    @property
    def mass_marks(self) -> Dict[int, str]:
        min_mass = self.mass_range[0]
        max_mass = self.mass_range[1]
        delta = 80
        num_steps = int(round((max_mass - min_mass) / delta)) + 1
        values = np.linspace(min_mass, max_mass, num_steps).round(10).tolist()
        return {i: '' for i in values}

    @property
    def thickness(self) -> float:
        """
        Get the thickness of the electrode.

        :return: Thickness of the electrode.
        """
        return round(self._thickness * M_TO_UM, 1)

    @property
    def thickness_range(self) -> Tuple[float, float]:
        """
        Get the range of thickness of the electrode.

        :return: Tuple containing the minimum and maximum thickness in micrometers.
        """
        return (
            self.coating_thickness_range[0]*2 + self.current_collector.thickness,
            self.coating_thickness_range[1]*2 + self.current_collector.thickness
        )

    @property
    def thickness_marks(self) -> Dict[str, float]:
        """
        Get the thickness marks of the electrode.

        :return: Dictionary containing the thickness marks.
        """
        min = np.ceil(self.thickness_range[0])
        max = np.floor(self.thickness_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 40)}

    @property
    def cost(self) -> float:
        return round(self._cost, 2)
   
    @property
    def cost_range(self):
        min = 0
        max = self._cost + (1/self._cost)/5
        return (min, max)

    @property
    def cost_marks(self) -> Dict[str, float]:
        """
        Get the cost marks of the electrode.

        :return: Dictionary containing the cost marks.
        """
        min = np.ceil(self.cost_range[0])
        max = np.floor(self.cost_range[1])
        return {i: '' for i in range(int(min), int(max) + 1, 1)}

    @property
    def datum_x(self) -> float:
        """
        Get the x-coordinate of the datum in mm.
        """
        return round(self._datum[0] * M_TO_MM, 2)
    
    @property
    def datum_x_range(self) -> Tuple[float, float]:
        """
        Get the x-coordinate range of the datum in mm.
        """
        return (-100, 100)
    
    @property
    def datum_x_marks(self) -> Dict[int, str]:
        """
        Get the x-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_x_range[0])
        max_datum = np.floor(self.datum_x_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

    @property
    def datum_y(self) -> float:
        """
        Get the y-coordinate of the datum in mm.
        """
        return round(self._datum[1] * M_TO_MM, 2)

    @property
    def datum_y_range(self) -> Tuple[float, float]:
        """
        Get the y-coordinate range of the datum in mm.
        """
        return (-100, 100)
    
    @property
    def datum_y_marks(self) -> Dict[int, str]:
        """
        Get the y-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_y_range[0])
        max_datum = np.floor(self.datum_y_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

    @property
    def datum_z(self) -> float:
        """
        Get the z-coordinate of the datum in mm.
        """
        return round(self._datum[2] * M_TO_MM, 2)

    @property
    def datum_z_range(self) -> Tuple[float, float]:
        """
        Get the z-coordinate range of the datum in mm.
        """
        return (-100, 100)
    
    @property
    def datum_z_marks(self) -> Dict[int, str]:
        """
        Get the z-coordinate marks for the slider.
        """
        min_datum = np.ceil(self.datum_z_range[0])
        max_datum = np.floor(self.datum_z_range[1])
        return {i: '' for i in range(int(min_datum), int(max_datum) + 1, 20)}

    @property
    def porosity_hard_range(self) -> Tuple[float, float]:
        return (10, 80)

    # === SETTERS ===

    @datum_x.setter
    def datum_x(self, x: float) -> None:
        self.datum = (x, self.datum_y, self.datum_z)

    @datum_y.setter
    def datum_y(self, y: float) -> None:
        self.datum = (self.datum_x, y, self.datum_z)

    @datum_z.setter
    def datum_z(self, z: float) -> None:
        self.datum = (self.datum_x, self.datum_y, z)

    @thickness.setter
    def thickness(self, thickness: float):
        self.validate_positive_float(thickness, 'thickness')
        new_coating_thickness = (thickness - self.current_collector.thickness)/2
        self.coating_thickness = new_coating_thickness

    @coating_thickness.setter
    @calculate_bulk_properties
    @calculate_coordinates
    def coating_thickness(self, coating_thickness: float):
        """
        Set the coating thickness of the electrode. Behavior depends on control mode.
        
        :param coating_thickness: Coating thickness of the electrode in micrometers.
        """
        self.validate_positive_float(coating_thickness, 'coating thickness')
        self._coating_thickness = coating_thickness * UM_TO_M

        if self._update_properties:
            self._update_dependent_properties('coating_thickness', coating_thickness)
        
    @porosity.setter
    def porosity(self, porosity: float):
        """
        Set the porosity of the electrode.

        :param porosity: Porosity of the electrode in percentage.
        """
        self.validate_percentage(porosity, 'porosity')
        porosity_fraction = porosity / 100
        new_calender_density = (1 - porosity_fraction) / self._formulation._specific_volume
        self.calender_density = new_calender_density  * (KG_TO_G / M_TO_CM**3)
        
    @formulation.setter
    @calculate_all_properties
    def formulation(self, formulation: _ElectrodeFormulation):
        self.validate_type(formulation, _ElectrodeFormulation, 'formulation')
        self._formulation = formulation

    @voltage_cutoff.setter
    @calculate_half_cell_curve
    def voltage_cutoff(self, voltage: float):
        self.formulation.voltage_cutoff = voltage
        self._voltage_cutoff = voltage
        
    @calender_density.setter
    @calculate_bulk_properties
    @calculate_coordinates
    def calender_density(self, calender_density: float):
        self.validate_positive_float(calender_density, 'calender density')
        self._calender_density = calender_density * (G_TO_KG / CM_TO_M**3)

        if self._update_properties:
            self._update_dependent_properties('calender_density', calender_density)

    @insulation_material.setter
    @calculate_bulk_properties
    def insulation_material(self, insulation_material: InsulationMaterial | None):

        self.validate_type(insulation_material, InsulationMaterial, 'insulation material') if insulation_material else None

        if self._current_collector.insulation_area != 0 and insulation_material is None:
            raise ValueError("Insulation material must be provided if the current collector has an insulation width")
        
        if self._current_collector.insulation_area == 0 and insulation_material is not None:
            raise ValueError("Insulation material cannot be provided if the current collector does not have an insulation area")
        
        self._insulation_material = insulation_material

    @insulation_thickness.setter
    @calculate_volumes
    def insulation_thickness(self, insulation_thickness: float):
        self.validate_positive_float(insulation_thickness, 'insulation thickness')
        self._insulation_thickness = insulation_thickness * UM_TO_M

    @mass_loading.setter
    @calculate_bulk_properties
    @calculate_coordinates
    def mass_loading(self, mass_loading: float):
        self.validate_positive_float(mass_loading, 'mass loading')
        self._mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)

        if self._update_properties:
            self._update_dependent_properties('mass_loading', mass_loading)

    @current_collector.setter
    @calculate_all_properties
    def current_collector(self, current_collector: _CurrentCollector):
        self.validate_type(current_collector, _CurrentCollector, 'current collector')
        self._current_collector = current_collector

    @name.setter
    def name(self, name: str):
        self.validate_string(name, 'name')
        self._name = name

    @datum.setter
    @calculate_coordinates
    def datum(self, datum: Tuple[float, float, float]):
        self.validate_datum(datum)
        self._datum = tuple(d * MM_TO_M for d in datum)
        self.current_collector.datum = datum

    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return self.__str__()


class Anode(_Electrode):
    """
    A class representing an anode in a battery system, inheriting from the _Electrode base class.
    """
    def __init__(
            self, 
            formulation: AnodeFormulation,
            mass_loading: float,
            current_collector: _CurrentCollector,
            calender_density: float,
            insulation_material: InsulationMaterial = None,
            insulation_thickness: float = 0.0,
            voltage_cutoff: float = None,
            name: str = 'Anode'
        ):
        """
        Initialize an object that represents an anode.

        Parameters:
        ----------
        formulation : AnodeFormulation
            The formulation of the anode.
        mass_loading : float
            The mass loading of the anode in mg/cm^2.
        current_collector : _CurrentCollector
            The current collector used in the anode.
        calender_density : float
            The density of the anode after calendering in g/cm^3.
        insulation_material : InsulationMaterial, optional
            The insulation material used in the anode (default is None).
        insulation_thickness : float, optional
            The thickness of the insulation material in micrometers (default is 0.0).
        voltage_cutoff : float, optional
            The maximum voltage of the half cell curves (default is None).
        name : str, optional
            The name of the anode (default is 'Anode').
        ----------
        """
        super().__init__(
            formulation=formulation,
            mass_loading=mass_loading,
            current_collector=current_collector,
            calender_density=calender_density,
            name=name,
            insulation_material=insulation_material,
            insulation_thickness=insulation_thickness,
            voltage_cutoff=voltage_cutoff
        )

        self._update_properties = True

    @property
    def top_overhang(self) -> float:
        """
        Get the top overhang of the anode when in a layup or stack.

        :return: Top overhang of the anode in mm.
        """
        if hasattr(self, '_top_overhang'):
            return round(self._top_overhang * M_TO_MM, 2)
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
        
        if not hasattr(self, '_top_overhang'):
            raise AttributeError("Top overhang has not been set yet. This indicates that the anode is not part of a layup or stack, and so the top overhang cannot be set.")
        
        old_top_overhang = self.top_overhang
        new_top_overhang = top_overhang
        overhang_difference = new_top_overhang - old_top_overhang

        self.datum = (
            self.datum[0],
            self.datum[1] + overhang_difference,
            self.datum[2]
        )

        self._top_overhang = new_top_overhang * MM_TO_M

    @property
    def bottom_overhang(self) -> float:
        """
        Get the bottom overhang of the anode when in a layup or stack.

        :return: Bottom overhang of the anode in mm.
        """
        if hasattr(self, '_bottom_overhang'):
            return round(self._bottom_overhang * M_TO_MM, 2)
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
        
        if not hasattr(self, '_bottom_overhang'):
            raise AttributeError("Bottom overhang has not been set yet. This indicates that the anode is not part of a layup or stack, and so the bottom overhang cannot be set.")
        
        old_bottom_overhang = self.bottom_overhang
        new_bottom_overhang = bottom_overhang
        overhang_difference = new_bottom_overhang - old_bottom_overhang

        self.datum = (
            self.datum[0],
            self.datum[1] - overhang_difference,
            self.datum[2]
        )

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
            voltage_cutoff: float = None,
            name: str = 'Cathode'
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
        voltage_cutoff : float, optional
            The maximum voltage of the half cell curves (default is None).
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
            voltage_cutoff=voltage_cutoff
        )

        self._update_properties = True

    @property
    def porosity_range(self) -> Tuple[float, float]:
        """
        Get the range of porosity of the electrode.

        :return: Tuple containing the minimum and maximum porosity in percentage.
        """
        return (15, 40)
    