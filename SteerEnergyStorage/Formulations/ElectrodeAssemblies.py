from SteerEnergyStorage.Constructions.Electrodes import Anode, Cathode
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, TabWeldedCurrentCollector, NotchedCurrentCollector

from App.styles import *
from SteerEnergyStorage.Constants import *

from copy import deepcopy
from copy import copy
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from shapely import minimum_bounding_circle
import warnings
import plotly.graph_objects as go



class _ElectrodeAssembly():

    def __init__(self,
                 anode: Anode | CurrentCollector,
                 cathode: Cathode | None,
                 separator: Separator | None,
                 name: str) -> None:
        
        self._check_cathode(cathode)
        self._check_anode(anode)
        self._check_separator(separator)
        self._name = name

    def _check_cathode(self, cathode: Cathode):
        """
        Function to check the cathode properties

        :param cathode: Cathode: cathode used in the stack
        """
        if not isinstance(cathode, Cathode):
            raise ValueError("Cathode must be an instance of the Cathode class")
        
        self._cathode = deepcopy(cathode)

    def _check_anode(self, anode: Anode):
        """
        Function to check the anode properties

        :param anode: Anode: anode used in the stack
        """
        if not isinstance(anode, Anode) and not isinstance(anode, CurrentCollector):
            raise ValueError("Anode must be an instance of the Anode class")
        
        if isinstance(anode, CurrentCollector):
            self._anode_free = True
            anode = Anode(formulation={}, mass_loading=0, current_collector=anode, calender_density=0)
        else:
            self._anode_free = False
            self._anode = deepcopy(anode)

    def _check_separator(self, separator: Separator):
        """
        Function to check the separator properties

        :param separator: Separator: separator used in the stack
        """
        if hasattr(separator, '_fold_length'):
            if separator._fold_length < self._cathode._current_collector._length or separator._fold_length < self._anode._current_collector._length:
                raise ValueError("separator length must be greater or equal to cathode and anode length")
            
        if hasattr(separator, '_length'):
            if separator._length < self._cathode._current_collector._length or separator._length < self._anode._current_collector._length:
                raise ValueError("separator length must be greater or equal to cathode and anode length")
        
        if separator._width < self._cathode._current_collector._width or separator._width < self._anode._current_collector._width:
            raise ValueError("separator width must be greater or equal to cathode and anode width")
        
        self._separator = deepcopy(separator)

    @staticmethod
    def _linear_interpolate_on_capacity(df) -> pd.DataFrame:

            warnings.simplefilter("ignore", category=RuntimeWarning)
            cathode_curve = df.query("electrode == 'cathode'")
            anode_curve = df.query("electrode == 'anode'")

            cap_min = max(cathode_curve['capacity'].min(), anode_curve['capacity'].min())
            cap_max = min(cathode_curve['capacity'].max(), anode_curve['capacity'].max())
            cap_grid = np.linspace(cap_min, cap_max, 100)

            cathode_voltage = np.interp(cap_grid, cathode_curve['capacity'], cathode_curve['voltage'])
            anode_voltage = np.interp(cap_grid, anode_curve['capacity'], anode_curve['voltage'])

            full_cell_voltage = cathode_voltage - anode_voltage

            data = pd.DataFrame({'capacity': cap_grid, 'voltage': full_cell_voltage, 'electrode': 'full cell'})

            return data

    def _calculate_full_cell_curve(self):
        """
        Function to calculate the full cell curves of the stack
        """
        cathode_half_cell = self._cathode_half_cell_curve.copy().assign(electrode = 'cathode')

        if not self._anode_free:
            anode_half_cell = self._anode_half_cell_curve.copy().assign(electrode = 'anode')
        else:
            anode_half_cell = cathode_half_cell.copy().assign(electrode = 'anode').assign(voltage = 0)

        full_cell_curve = (pd
                            .concat([cathode_half_cell, anode_half_cell])
                            .groupby(['direction'], group_keys=True)
                            .apply(lambda df: (df
                                               .sort_values(by='capacity', ascending=True)
                                               .pipe(self._linear_interpolate_on_capacity)
                                               ))
                            .reset_index()
                            )
        
        cathode_discharge_min = cathode_half_cell.query("direction == 'discharge'")['capacity'].min()
        anode_discharge_min = anode_half_cell.query("direction == 'discharge'")['capacity'].min()

        full_cell_curve = (full_cell_curve
                            .query('not (direction == "discharge" and capacity < @cathode_discharge_min)')
                            .query('not (direction == "discharge" and capacity < @anode_discharge_min)')
                            )
        
        full_cell_curve = (full_cell_curve
                            .assign(sort_key_1 = lambda x: [-c if d == 'discharge' else c for c, d in zip(x['capacity'], x['direction'])])
                            .assign(sort_key_2 = lambda x: [1 if d == 'discharge' else 0 for d in x['direction']])
                            .sort_values(by=['electrode', 'sort_key_2', 'sort_key_1'])
                            .drop(columns=['sort_key_2', 'sort_key_1'])
                            )

        self._full_cell_curve = full_cell_curve

    @property
    def anode(self):
        return self._anode
    
    @property
    def cathode(self):
        return self._cathode
    
    @property
    def separator(self):
        return self._separator

    @property
    def name(self):
        return self._name

    @property
    def length(self):
        if hasattr(self, '_length'):
            return round(self._length * M_TO_MM, 2)
        else:
            return AttributeError("Length not calculated yet.")

    @property
    def width(self):
        if hasattr(self, '_width'):
            return round(self._width * M_TO_MM, 2)
        else:
            return AttributeError("Width not calculated yet.")

    @property
    def thickness(self):
        if hasattr(self, '_thickness'):
            return round(self._thickness * M_TO_MM, 2)
        else:
            return AttributeError("Thickness not calculated yet.")

    @property
    def cost(self):
        return round(self._cost, 2)

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)

    @property
    def pore_volume(self):
        return round(self._pore_volume * M_TO_CM**3, 2)

    @property
    def cathode_half_cell_curve(self) -> pd.DataFrame:
        """
        Get the half cell curve of the electrode.

        :return: DataFrame containing the half cell curve.
        """
        if not hasattr(self, '_cathode_half_cell_curve'):
            raise AttributeError("Half cell curves have not been calculated yet")

        return (self
                ._cathode_half_cell_curve
                .assign(capacity=lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction'})
                )
    
    @property
    def anode_half_cell_curve(self) -> pd.DataFrame:
        """
        Get the half cell curve of the electrode.

        :return: DataFrame containing the half cell curve.
        """
        if not hasattr(self, '_anode_half_cell_curve'):
            raise AttributeError("Half cell curves have not been calculated yet")

        return (self
                ._anode_half_cell_curve
                .assign(capacity=lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction'})
                )
    
    @property
    def full_cell_curve(self) -> pd.DataFrame:
        """
        Get the full cell curve of the electrode.

        :return: DataFrame containing the full cell curve.
        """
        if not hasattr(self, '_full_cell_curve'):
            raise AttributeError("Full cell curves have not been calculated yet")

        return (self
                ._full_cell_curve
                .assign(capacity=lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction'})
                )

    @property
    def mass_breakdown(self):
        return {item.replace('_', ' ').capitalize(): round(value * KG_TO_G, 2) for item, value in self._mass_breakdown.items()}

    @property
    def active_geometric_area(self):
        return round(self._active_geometric_area * M_TO_CM**2, 2)
    
    @property
    def cost_breakdown(self):
        return {key.replace('_', ' ').capitalize(): round(value, 2) for key, value in self._cost_breakdown.items()}

    @property
    def cathode_cost_breakdown(self):

        if hasattr(self, '_cathode_cost_breakdown'):
            rounded_dict = {
                item.replace('_', ' ').capitalize(): (
                    {key: round(value, 3) for key, value in value.items()}
                    if isinstance(value, dict) else round(value, 2)
                )
                for item, value in self._cathode_cost_breakdown.items()
            }
            return rounded_dict
        else:
            raise AttributeError("Cathode cost breakdown not calculated yet.")
    
    @property
    def anode_cost_breakdown(self):
        
        if hasattr(self, '_anode_cost_breakdown'):
            rounded_dict = {
                item.replace('_', ' ').capitalize(): (
                    {key: round(value, 3) for key, value in value.items()}
                    if isinstance(value, dict) else round(value, 2)
                )
                for item, value in self._anode_cost_breakdown.items()
            }
            return rounded_dict
        else:
            raise AttributeError("Anode cost breakdown not calculated yet.")
    
    @property
    def cathode_mass_breakdown(self):
        if hasattr(self, '_cathode_mass_breakdown'):
            rounded_dict = {
                item.replace('_', ' ').capitalize(): (
                    {key: round(value * KG_TO_G, 2) for key, value in value.items()}
                    if isinstance(value, dict) else round(value, 3)
                )
                for item, value in self._cathode_mass_breakdown.items()
            }
            return rounded_dict
        else:
            raise AttributeError("Cathode mass breakdown not calculated yet.")
    
    @property
    def anode_mass_breakdown(self):
        if hasattr(self, '_anode_mass_breakdown'):
            rounded_dict = {
                item.replace('_', ' ').capitalize(): (
                    {key: round(value * KG_TO_G, 2) for key, value in value.items()}
                    if isinstance(value, dict) else round(value, 3)
                )
                for item, value in self._anode_mass_breakdown.items()
            }
            return rounded_dict
        else:
            raise AttributeError("Anode mass breakdown not calculated yet.")


class _JellyRoll(_ElectrodeAssembly):

    def __init__(self, 
                 anode: Anode | CurrentCollector, 
                 cathode: Cathode, 
                 separator: Separator, 
                 name: str = 'jelly_roll') -> None:
        """
        Initialize an object that represents an electrochemical jelly roll within an electrochemical cell
        """
        super().__init__(anode=anode, cathode=cathode, separator=separator, name=name)

        self._calculate_active_area()
        self._calculate_anode_properties()
        self._calculate_separator_properties()
        self._calculate_roll_properties()
        self._calculate_components()
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()
        self._calculate_cathode_cost_breakdown()
        self._calculate_anode_cost_breakdown()
        self._calculate_cathode_mass_breakdown()
        self._calculate_anode_mass_breakdown()

    def _check_anode(self, anode: Anode):
        """
        Function to check the anode properties

        :param anode: Anode: anode used in the stack
        """
        if not isinstance(anode, Anode) and not isinstance(anode, CurrentCollector):
            raise ValueError("Anode must be an instance of the Anode class or CurrentCollector class")
        
        if not isinstance(anode._current_collector, TabWeldedCurrentCollector) and not isinstance(anode._current_collector, NotchedCurrentCollector):
            raise ValueError("Anode current collector must be an instance of the TabWeldedCurrentCollector or NotchedCurrentCollector class")
        
        if isinstance(anode, CurrentCollector):
            self._anode_free = True
            anode = Anode(formulation={}, mass_loading=0, current_collector=anode, calender_density=0)
        else:
            self._anode_free = False
            self._anode = deepcopy(anode)

    def _check_cathode(self, cathode: Cathode):
        """
        Function to check the cathode properties

        :param cathode: Cathode: cathode used in the stack
        """
        if not isinstance(cathode, Cathode):
            raise ValueError("Cathode must be an instance of the Cathode class")
        
        if not isinstance(cathode._current_collector, TabWeldedCurrentCollector) and not isinstance(cathode._current_collector, NotchedCurrentCollector):
            raise ValueError("Cathode current collector must be an instance of the TabWeldedCurrentCollector or NotchedCurrentCollector class")
        
        self._cathode = deepcopy(cathode)

    def _calculate_active_area(self):
        self._active_geometric_area = self._cathode._single_sided_area * 2

    def _calculate_anode_properties(self):
        anode_overhang = (self._anode._single_sided_area/self._cathode._single_sided_area) - 1
        self._anode._overhang = anode_overhang

    def _calculate_separator_properties(self):
        self._separator._length = (self._separator._fold_length * 2) + ((self._cathode._thickness + self._separator._thickness) * PI)
        self._separator._calculate_area_properties()

    def _calculate_roll_properties(self):
        self._pore_volume = self._anode._pore_volume + self._cathode._pore_volume + self._separator._pore_volume
        self._width = self._separator._width
        self._electrode_thickness = self._separator._thickness * 2 + self._anode._thickness + self._cathode._thickness

    def _calculate_components(self):
        self._cathode_active_materials = list(self._cathode._formulation._active_materials.keys())
        self._cathode_binders = list(self._cathode._formulation._binders.keys())
        self._cathode_conductive_additives = list(self._cathode._formulation._conductive_additives.keys())
        self._cathode_current_collectors = [self._cathode._current_collector]

        self._anode_active_materials = list(self._anode._formulation._active_materials.keys())
        self._anode_binders = list(self._anode._formulation._binders.keys())
        self._anode_conductive_additives = list(self._anode._formulation._conductive_additives.keys())
        self._anode_current_collectors = [self._anode._current_collector]

    def _calculate_mass_breakdown(self):

        self._mass_breakdown = {
            'cathode': self._cathode._mass,
            'anode': self._anode._mass,
            'separator': self._separator._mass
        }
        self._mass = sum(self._mass_breakdown.values())

    def _calculate_cost_breakdown(self):

        self._cost_breakdown = {
            'cathode': self._cathode._cost,
            'anode': self._anode._cost,
            'separator': self._separator._cost
        }

        self._cost = sum(self._cost_breakdown.values())

    def _calculate_half_cell_curve(self, grid_n: int):

        self._cathode._calculate_half_cell_curve(grid_n=grid_n)
        self._anode._calculate_half_cell_curve(grid_n=grid_n)

        self._cathode_half_cell_curve = (self
                                         ._cathode
                                         ._half_cell_curve
                                         .groupby('direction', as_index=False)
                                         .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                                         )
        
        if not self._anode_free:
            self._anode_half_cell_curve = (self
                                           ._anode
                                           ._half_cell_curve
                                           .groupby('direction', as_index=False)
                                           .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                                           )
            
        self._areal_capacity = self._cathode._areal_capacity

    def _calculate_cathode_mass_breakdown(self):
        cathode_mass_breakdown = self._cathode._mass_breakdown.copy()
        current_collector_value = cathode_mass_breakdown['current_collector']
        cathode_mass_breakdown.pop('current_collector')
        cathode_mass_breakdown['current_collectors'] = {self._cathode._current_collector: current_collector_value}
        self._cathode_mass_breakdown = cathode_mass_breakdown

    def _calculate_anode_mass_breakdown(self):
        anode_mass_breakdown = self._anode._mass_breakdown.copy()
        current_collector_value = anode_mass_breakdown['current_collector']
        anode_mass_breakdown.pop('current_collector')
        anode_mass_breakdown['current_collectors'] = {self._anode._current_collector: current_collector_value}
        self._anode_mass_breakdown = anode_mass_breakdown

    def _calculate_cathode_cost_breakdown(self):
        cathode_cost_breakdown = self._cathode._cost_breakdown.copy()
        current_collector_value = cathode_cost_breakdown['current_collector']
        cathode_cost_breakdown.pop('current_collector')
        cathode_cost_breakdown['current_collectors'] = {self._cathode._current_collector: current_collector_value}
        self._cathode_cost_breakdown = cathode_cost_breakdown

    def _calculate_anode_cost_breakdown(self):
        anode_cost_breakdown = self._anode._cost_breakdown.copy()
        current_collector_value = anode_cost_breakdown['current_collector']
        anode_cost_breakdown.pop('current_collector')
        anode_cost_breakdown['current_collectors'] = {self._anode._current_collector: current_collector_value}
        self._anode_cost_breakdown = anode_cost_breakdown

    @property
    def electrode_thickness(self):
        return round(self._electrode_thickness * M_TO_MM, 2)


class CylindricalJellyRoll(_JellyRoll):

    def __init__(self, 
                 anode: Anode | CurrentCollector, 
                 cathode: Cathode, 
                 separator: Separator, 
                 mandrel_diameter: float,
                 name: str = 'cylindrical_jelly_roll') -> None:
        """
        Initialize an object that represents an electrochemical cylindrical jelly roll within an electrochemical cell

        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param separator: Separator: separator used in the stack
        :param mandrel_diameter: float: internal mandrel diameter of the cylindrical jelly roll in mm
        :param name: str: name of the cylindrical jelly roll
        """
        super().__init__(anode=anode, cathode=cathode, separator=separator, name=name)

        self._check_mandrel_diameter(mandrel_diameter)
        self._calculate_archimedean_spiral()
        self._center_and_calculate_radius()

    def _check_mandrel_diameter(self, mandrel_diameter: float):
        """
        Function to check the internal mandrel diameter

        :param mandrel_diameter: float: internal mandrel diameter of the cylindrical jelly roll in mm
        """
        if not isinstance(mandrel_diameter, (int, float)):
            raise ValueError("Internal mandrel diameter must be a number")
        
        if mandrel_diameter < 0:
            raise ValueError("Internal mandrel diameter must be greater than 0")
        
        self._mandrel_diameter = mandrel_diameter * MM_TO_M

    def _calculate_archimedean_spiral(self, dtheta: float = 0.05) -> pd.DataFrame:
        """
        Function to calculate the Archimedean spiral using the archemdyan spiral solved numerically

        :param dtheta: float: step size for the theta angle in radians
        """
        length = self._anode._current_collector._length
        b = self._electrode_thickness / (2*np.pi)
        a = (self._mandrel_diameter / 2)
        
        total_length = 0
        theta = 0

        theta_list = []
        r_list = []

        while total_length < length:
            r = a + b * theta
            r_list.append(r)
            ds = np.sqrt(r**2 + b**2) * dtheta
            total_length += ds
            theta += dtheta
            theta_list.append(theta)

        self._spiral = (pd
                        .DataFrame({'theta': theta_list, 'r': r_list})
                        .assign(r_outer = lambda x: x['r'] + self._electrode_thickness)
                        .assign(x = lambda x: x['r'] * np.cos(x['theta']))
                        .assign(y = lambda x: x['r'] * np.sin(x['theta']))
                        .assign(x_outer = lambda x: x['r_outer'] * np.cos(x['theta']))
                        .assign(y_outer = lambda x: x['r_outer'] * np.sin(x['theta']))
                        )

    def _center_and_calculate_radius(self):
        """
        Function to calculate the radius of the cylindrical jelly roll using the archemdyan spiral solved numerically

        :param dtheta: float: step size for the theta angle in radians
        """
        spiral = self._spiral.copy()

        theta_max = spiral['theta'].max()
        theta_min = theta_max - 2*np.pi

        x_list = spiral.query(f'theta < {theta_max} and theta > {theta_min}')['x_outer']
        y_list = spiral.query(f'theta < {theta_max} and theta > {theta_min}')['y_outer']

        points = [(x, y) for x, y in zip(x_list, y_list)]
        polygon = Polygon(points)
        bounding_circle = minimum_bounding_circle(polygon)

        x_center = bounding_circle.centroid.x
        y_center = bounding_circle.centroid.y

        spiral = (spiral
                  .assign(x = lambda x: x['x'] - x_center)
                  .assign(y = lambda x: x['y'] - y_center)
                  .assign(x_outer = lambda x: x['x_outer'] - x_center)
                  .assign(y_outer = lambda x: x['y_outer'] - y_center)
                  )

        self._shift_vector = np.array([x_center, y_center])
        self._radius = (bounding_circle.bounds[2] - bounding_circle.bounds[0])/2
        self._diameter = self._radius * 2
        self._n_turns = theta_max / (2 * np.pi)
        self._spiral = spiral

    def get_top_down_view(self, encapsulation = None, paper_bgcolor='white', plot_bgcolor='white', **kwargs) -> go.Figure:
        """
        Function to show the jelly roll wrapped up 
        """
        data = self._spiral.copy()
        n_turns = self.n_turns
        diameter = self.radius * 2
        
        fig = go.Figure()

        if encapsulation is not None:
            for trace in encapsulation.get_top_down_view().data:
                if trace.name == 'Canister Wall':
                    fig.add_trace(trace)

        def get_coil(df, thickness):

            df1 = df.copy().filter(['r', 'theta']).sort_values(by='theta', ascending=True)
            df2 = df.copy().filter(['r', 'theta']).sort_values(by='theta', ascending=False).assign(r = lambda x: x['r'] + thickness)

            df = pd.concat([df1, df2])

            df = (df
                  .assign(x = lambda x: (x['r'] * np.cos(x['theta'])) - self._shift_vector[0])
                  .assign(y = lambda x: (x['r'] * np.sin(x['theta'])) - self._shift_vector[1])
                  .assign(x = lambda x: x['x'] * M_TO_MM)
                  .assign(y = lambda x: x['y'] * M_TO_MM)
                  .rename(columns={'x': 'X (mm)', 'y': 'Y (mm)'})
                  )
            
            return df, df2

        line_dict = dict(width=0, shape='spline')

        # first separator
        plot_data, edge_data = get_coil(data, self._separator._thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Bottom separator', line=line_dict, fillcolor=SEPARATOR_COLOR, fill='toself'))
        
        # anode active layer 1
        plot_data, edge_data = get_coil(edge_data, self._anode._material_thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Bottom anode layer', line=line_dict, fillcolor=ANODE_COLOR, fill='toself'))

        # anode current collector
        plot_data, edge_data = get_coil(edge_data, self._anode._current_collector._thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Anode current collector', line=line_dict, fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself'))

        # anode active layer 2
        plot_data, edge_data = get_coil(edge_data, self._anode._material_thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Top anode layer', line=line_dict, fillcolor=ANODE_COLOR, fill='toself'))

        # separator
        plot_data, edge_data = get_coil(edge_data, self._separator._thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Top seperator', line=line_dict, fillcolor=SEPARATOR_COLOR, fill='toself'))

        # cathode active layer 1
        plot_data, edge_data = get_coil(edge_data, self._cathode._material_thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Bottom cathode layer', line=line_dict, fillcolor=CATHODE_COLOR, fill='toself'))

        # cathode current collector
        plot_data, edge_data = get_coil(edge_data, self._cathode._current_collector._thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Cathode current collector', line=line_dict, fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself'))

        # cathode active layer 2
        plot_data, edge_data = get_coil(edge_data, self._cathode._material_thickness)
        fig.add_trace(go.Scatter(x=plot_data['X (mm)'], y=plot_data['Y (mm)'], mode='lines', name='Top cathode layer', line=line_dict, fillcolor=CATHODE_COLOR, fill='toself'))

        fig.update_layout(xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X (mm)"),
                          yaxis=dict(showgrid=False, zeroline=False, title="Y (mm)"),
                          paper_bgcolor=paper_bgcolor,
                          plot_bgcolor=plot_bgcolor,
                          legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left"),
                          **kwargs)

        return fig

    def get_side_view(self, slider=0, encapsulation = None, paper_bgcolor='white', plot_bgcolor='white', **kwargs) -> go.Figure:
        """
        Function to show the jelly roll from the side
        """
        fig = go.Figure()

        line_dict=dict(width=0)

        # cathode
        neg_y_disp = -self._cathode._current_collector.width/2
        pos_y_disp = self._cathode._current_collector.width/2
        left_x = -self.radius + self.diameter * slider
        right_x = self.radius + self.diameter * slider
        covered_area_x = [left_x, right_x, right_x, left_x, left_x]
        covered_area_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=covered_area_x, y=covered_area_y, mode='lines', name='Cathode', line=line_dict, fillcolor=CATHODE_COLOR, fill='toself'))

        # cathode_tab
        neg_y_disp = self._cathode._current_collector.width/2
        pos_y_disp = self._cathode._current_collector.width/2 + self._cathode._current_collector.tab_width
        left_x = -self.radius + self.diameter * slider
        right_x = self.radius + self.diameter * slider
        tab_x = [left_x, right_x, right_x, left_x, left_x]
        tab_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=tab_x, y=tab_y, mode='lines', name='Cathode Tab', line=line_dict, fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself'))
                      
        # separator
        neg_y_disp = -self._separator.width/2
        pos_y_disp = self._separator.width/2
        left_x = -self.radius + self.diameter * 3 * slider
        right_x = self.radius + self.diameter * 3 * slider
        covered_area_x = [left_x, right_x, right_x, left_x, left_x]
        covered_area_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=covered_area_x, y=covered_area_y, mode='lines', name='Separator 1', line=line_dict, fillcolor=SEPARATOR_COLOR, fill='toself'))

        # anode
        neg_y_disp = -self._anode._current_collector.width/2
        pos_y_disp = self._anode._current_collector.width/2
        left_x = -self.radius + self.diameter * 2 * slider
        right_x = self.radius + self.diameter * 2 * slider
        covered_area_x = [left_x, right_x, right_x, left_x, left_x]
        covered_area_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=covered_area_x, y=covered_area_y, mode='lines', name='Anode', line=line_dict, fillcolor=ANODE_COLOR, fill='toself'))

        # anode_tab
        neg_y_disp = -self._anode._current_collector.width/2 - self._anode._current_collector.tab_width
        pos_y_disp = -self._anode._current_collector.width/2
        left_x = -self.radius + self.diameter * 2 * slider
        right_x = self.radius + self.diameter * 2 * slider
        tab_x = [left_x, right_x, right_x, left_x, left_x]
        tab_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=tab_x, y=tab_y, mode='lines', name='Anode Tab', line=line_dict, fillcolor=CURRENT_COLLECTOR_COLOR, fill='toself'))

        # separator
        neg_y_disp = -self._separator.width/2
        pos_y_disp = self._separator.width/2
        left_x = -self.radius + self.diameter * 3 * slider
        right_x = self.radius + self.diameter * 3 * slider
        covered_area_x = [left_x, right_x, right_x, left_x, left_x]
        covered_area_y = [neg_y_disp, neg_y_disp, pos_y_disp, pos_y_disp, neg_y_disp]
        fig.add_trace(go.Scatter(x=covered_area_x, y=covered_area_y, mode='lines', name='Separator 2', line=line_dict, fillcolor=SEPARATOR_COLOR, fill='toself'))
        
        if encapsulation is not None:
            for trace in encapsulation.get_side_view().data:
                fig.add_trace(trace)

        fig.update_layout(xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", title="X (mm)"),
                          yaxis=dict(showgrid=False, zeroline=False, title="Y (mm)"),
                          paper_bgcolor=paper_bgcolor,
                          plot_bgcolor=plot_bgcolor,
                          **kwargs)
        
        return fig

    def get_layup(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs) -> go.Figure:
        """
        Function to show the jelly roll layed out flat
        """
        figure = go.Figure()
        all_x = []
        all_y = []

        # Cathode
        for trace in self._cathode._current_collector.get_top_down_view(split=False).data:
            trace.legendgroup = 'Cathode'
            trace.showlegend = True if trace.name == 'Main Body' else False
            trace.name = 'Cathode'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Separator 1
        for trace in self._separator.get_top_down_view(split=False).data:
            trace.legendgroup = 'Separator 1'
            trace.name = 'Separator 1'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Anode
        for trace in self._anode._current_collector.get_top_down_view(split=False).data:
            trace.legendgroup = 'Anode'
            trace.showlegend = True if trace.name == 'Main Body' else False
            trace.name = 'Anode'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Separator 2
        for trace in self._separator.get_top_down_view(split=False).data:
            trace.legendgroup = 'Separator 2'
            trace.name = 'Separator 2'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Compute axis ranges with a small margin
        if all_x and all_y:
            x_margin = 0.05 * (max(all_x) - min(all_x)) if max(all_x) > min(all_x) else 1
            y_margin = 0.05 * (max(all_y) - min(all_y)) if max(all_y) > min(all_y) else 1
            x_range = [min(all_x) - x_margin, max(all_x) + x_margin]
            y_range = [min(all_y) - y_margin, max(all_y) + y_margin]
        else:
            x_range = None
            y_range = None

        figure.update_layout(
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                scaleanchor="y",
                title="X (mm)",
                range=x_range
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                title="Y (mm)",
                range=y_range
            ),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            **kwargs
        )

        return figure
        
    @property
    def mandrel_diameter(self):
        return round(self._mandrel_diameter * M_TO_MM, 2)
    
    @property
    def radius(self):
        return round(self._radius * M_TO_MM, 2)
    
    @property
    def diameter(self):
        return round(self._diameter * M_TO_MM, 2)

    @property
    def n_turns(self):
        return round(self._n_turns, 2)
    
    @property
    def spiral(self):
        
        return (self
                ._spiral
                .assign(r = lambda x: x['r'] * M_TO_MM)
                .assign(theta = lambda x: x['theta'] * DEG_TO_RAD)
                .rename(columns={'theta': 'Theta (deg)', 'r': 'Radius (mm)'})
                )


class FlatJellyRoll(_JellyRoll):

    def __init__(self, 
                 anode: Anode | CurrentCollector, 
                 cathode: Cathode, 
                 separator: Separator, 
                 focal_length: float,
                 name: str = 'flat_jelly_roll') -> None:
        """
        Initialize an object that represents an electrochemical flat jelly roll within an electrochemical cell

        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param separator: Separator: separator used in the stack
        :param focal_length: float: focal length of the flat jelly roll in mm
        :param name: str: name of the flat jelly roll
        """
        super().__init__(anode=anode, cathode=cathode, separator=separator, name=name)

        self._focal_length = focal_length * MM_TO_M
        self._calculate_flat_roll_properties()

    def _calculate_flat_roll_properties(self):
        """
        Function to calculate the geometry of the flat jelly roll after it has been wound
        """
        remaining_length = self._separator._fold_length
        top_layers = 0
        bottom_layers = 0
        left_turns = 0
        right_turns = 0
        left_radius = self._electrode_thickness / 2
        right_radius = self._electrode_thickness / 2

        while remaining_length > 0:
            top_layers += 1
            remaining_length = remaining_length - self._focal_length
            if remaining_length < 0:
                break
            right_turns += 1
            remaining_length = remaining_length - (PI * right_radius)
            right_radius = right_radius + self._electrode_thickness
            if remaining_length < 0:
                break
            bottom_layers += 1
            remaining_length = remaining_length - self._focal_length
            if remaining_length < 0:
                break
            left_turns += 1
            remaining_length = remaining_length - (PI * left_radius)
            left_radius = left_radius + self._electrode_thickness

        self._thickness = self._electrode_thickness * (top_layers + bottom_layers)
        self._length = self._focal_length + (left_turns * self._electrode_thickness) + (right_turns * self._electrode_thickness)
            
    @property
    def focal_length(self):
        return self._focal_length * M_TO_MM


class Stack(_ElectrodeAssembly):

    def __init__(self, 
                 anode: Anode | CurrentCollector,
                 cathode: Cathode,
                 separator: Separator,
                 n_layers: int,
                 additional_separator_wraps: int = 1,
                 name: str = 'stack') -> None:
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell

        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param n_layers: int: number of stacks in the cell
        :param separator: Separator: separator used in the stack
        :param additional_separator_wraps: int: number of additional wraps of the separator in the stack
        :param name: str: name of the stack
        """
        super().__init__(anode=anode, cathode=cathode, separator=separator, name=name)

        self._check_n_layers(n_layers)
        self._copy_cathode(cathode, n_layers)
        self._copy_anode(anode, n_layers + 1)

        self._additional_separator_wraps = additional_separator_wraps

        self._calculate_active_area()
        self._calculate_anode_properties()
        self._calculate_cathode_properties()
        self._calculate_separator_properties()
        self._calculate_stack_properties()

        self._calculate_components()
        self._calculate_mass_breakdown()
        self._calculate_cathode_mass_breakdown()
        self._calculate_anode_mass_breakdown()
        self._calculate_cost_breakdown()
        self._calculate_cathode_cost_breakdown()
        self._calculate_anode_cost_breakdown()

    def _calculate_components(self):

        cathode_active_materials = []
        cathode_binders = []
        cathode_conductive_additives = []
        cathode_current_collectors = []
        for c in self._cathodes:
            active_materials = c._formulation._active_materials.keys()
            binders = c._formulation._binders.keys()
            conductive_additives = c._formulation._conductive_additives.keys()
            cathode_active_materials.extend(active_materials)
            cathode_binders.extend(binders)
            cathode_conductive_additives.extend(conductive_additives)
            cathode_current_collectors.append(c._current_collector)

        self._cathode_active_materials = set(cathode_active_materials)
        self._cathode_binders = set(cathode_binders)
        self._cathode_conductive_additives = set(cathode_conductive_additives)
        self._cathode_current_collectors = set(cathode_current_collectors)

        anode_active_materials = []
        anode_binders = []
        anode_conductive_additives = []
        anode_current_collectors = []
        for a in self._anodes:
            active_materials = a._formulation._active_materials.keys()
            binders = a._formulation._binders.keys()
            conductive_additives = a._formulation._conductive_additives.keys()
            anode_active_materials.extend(active_materials)
            anode_binders.extend(binders)
            anode_conductive_additives.extend(conductive_additives)
            anode_current_collectors.append(a._current_collector)

        self._anode_active_materials = set(anode_active_materials)
        self._anode_binders = set(anode_binders)
        self._anode_conductive_additives = set(anode_conductive_additives)
        self._anode_current_collectors = set(anode_current_collectors)

    def _calculate_half_cell_curve(self, grid_n: int):
        """
        Function to calculate the half cell curves for the stack. It will calculate the half cell curves for each electrode first, and then it will add the capacities together. 

        :param grid_n: int: number of points to use in the half cell curve
        """
        # NOTE: Not explicitly calculating the half cell curve for each anode/cathode. Just the first and then copying. 
        self._cathodes[0]._calculate_half_cell_curve(grid_n=grid_n)
        for c in self._cathodes[1:]:
            c._half_cell_curve = self._cathodes[0]._half_cell_curve.copy()
            c._areal_capacity = self._cathodes[0]._areal_capacity

        # NOTE: Not explicitly calculating the half cell curve for each anode/cathode. Just the first and then copying. 
        if not self._anode_free:
            self._anodes[0]._calculate_half_cell_curve(grid_n=grid_n)
            for a in self._anodes[1:]:
                a._half_cell_curve = self._anodes[0]._half_cell_curve.copy()

        cathode_half_cell = (pd
                             .concat([c._half_cell_curve for c in self._cathodes])
                             .groupby(['direction', 'voltage'], as_index=False)['capacity']
                             .sum()
                             .groupby('direction', as_index=False)
                             .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                             )

        dummy = pd.DataFrame(columns=['direction', 'voltage', 'capacity'])
        anode_half_cell = (pd
                           .concat([a._half_cell_curve if not a._anode_free else dummy for a in self._anodes[:-1]]) # one anode's worth of material is not used on the outsides of the stack
                           .groupby(['direction', 'voltage'], as_index=False)['capacity']
                           .sum()
                           .groupby('direction', as_index=False)
                           .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                           )
        
        self._areal_capacity = sum([c._areal_capacity for c in self._cathodes])
        self._cathode_half_cell_curve = cathode_half_cell

        if len(anode_half_cell) > 0:
            self._anode_half_cell_curve = anode_half_cell

    def _check_n_layers(self, n_layers: int):

        if not isinstance(n_layers, int):
            raise ValueError("Number of layers must be an integer")
        
        if n_layers < 1:
            raise ValueError("Number of layers must be greater than 0")
        
        if n_layers == 1:
            raise Warning("You have made a stack of just one layer. Consider using the single layer electrode tape object instead. A stack of one layer will have two anodes and one cathode.")
        
        self._n_layers = n_layers

    def _calculate_cost_breakdown(self):

        # calculate the cost breakdown
        self._cost_breakdown = {
            'cathode': sum([c._cost for c in self._cathodes]),
            'anode': sum([a._cost for a in self._anodes]),
            'separator': self._separator._cost
        }

        # calculate the total cost
        self._cost = sum(self._cost_breakdown.values())

    def _calculate_cathode_cost_breakdown(self):

        # calculate the cathode mass breakdown
        cathode_cost_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for c in self._cathodes:

            for am, cost in c._cost_breakdown['active_materials'].items():
                if am in cathode_cost_breakdown['active_materials']:
                    cathode_cost_breakdown['active_materials'][am] += cost
                else:
                    cathode_cost_breakdown['active_materials'][am] = cost

            for b, cost in c._cost_breakdown['binders'].items():
                if b in cathode_cost_breakdown['binders']:
                    cathode_cost_breakdown['binders'][b] += cost
                else:
                    cathode_cost_breakdown['binders'][b] = cost

            for ca, cost in c._cost_breakdown['conductive_additives'].items():
                if ca in cathode_cost_breakdown['conductive_additives']:
                    cathode_cost_breakdown['conductive_additives'][ca] += cost
                else:
                    cathode_cost_breakdown['conductive_additives'][ca] = cost

            current_collector = c._current_collector
            current_collector_cost = c._current_collector._cost
            if current_collector in cathode_cost_breakdown['current_collectors']:
                cathode_cost_breakdown['current_collectors'][current_collector] += current_collector_cost
            else:
                cathode_cost_breakdown['current_collectors'][current_collector] = current_collector_cost
            
        self._cathode_cost_breakdown = cathode_cost_breakdown

    def _calculate_anode_cost_breakdown(self):

        # calculate the cathode mass breakdown
        anode_cost_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for a in self._anodes:

            for am, cost in a._cost_breakdown['active_materials'].items():
                if am in anode_cost_breakdown['active_materials']:
                    anode_cost_breakdown['active_materials'][am] += cost
                else:
                    anode_cost_breakdown['active_materials'][am] = cost

            for b, cost in a._cost_breakdown['binders'].items():
                if b in anode_cost_breakdown['binders']:
                    anode_cost_breakdown['binders'][b] += cost
                else:
                    anode_cost_breakdown['binders'][b] = cost

            for ca, cost in a._cost_breakdown['conductive_additives'].items():
                if ca in anode_cost_breakdown['conductive_additives']:
                    anode_cost_breakdown['conductive_additives'][ca] += cost
                else:
                    anode_cost_breakdown['conductive_additives'][ca] = cost

            current_collector = a._current_collector
            current_collector_cost = a._current_collector._cost
            if current_collector in anode_cost_breakdown['current_collectors']:
                anode_cost_breakdown['current_collectors'][current_collector] += current_collector_cost
            else:
                anode_cost_breakdown['current_collectors'][current_collector] = current_collector_cost
            
        self._anode_cost_breakdown = anode_cost_breakdown

    def _calculate_mass_breakdown(self):

        self._mass_breakdown = {
            'cathode': sum([c._mass for c in self._cathodes]),
            'anode': sum([a._mass for a in self._anodes]),
            'separator': self._separator._mass
        }
        self._mass = sum(self._mass_breakdown.values())

    def _calculate_cathode_mass_breakdown(self):

        # calculate the cathode mass breakdown
        cathode_mass_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for c in self._cathodes:

            for am, mass in c._mass_breakdown['active_materials'].items():
                if am in cathode_mass_breakdown['active_materials']:
                    cathode_mass_breakdown['active_materials'][am] += mass
                else:
                    cathode_mass_breakdown['active_materials'][am] = mass

            for b, mass in c._mass_breakdown['binders'].items():
                if b in cathode_mass_breakdown['binders']:
                    cathode_mass_breakdown['binders'][b] += mass
                else:
                    cathode_mass_breakdown['binders'][b] = mass

            for ca, mass in c._mass_breakdown['conductive_additives'].items():
                if ca in cathode_mass_breakdown['conductive_additives']:
                    cathode_mass_breakdown['conductive_additives'][ca] += mass
                else:
                    cathode_mass_breakdown['conductive_additives'][ca] = mass

            current_collector = c._current_collector
            current_collector_mass = c._current_collector._mass
            if current_collector in cathode_mass_breakdown['current_collectors']:
                cathode_mass_breakdown['current_collectors'][current_collector] += current_collector_mass
            else:
                cathode_mass_breakdown['current_collectors'][current_collector] = current_collector_mass
            

        self._cathode_mass_breakdown = cathode_mass_breakdown

    def _calculate_anode_mass_breakdown(self):

        # calculate the cathode mass breakdown
        anode_mass_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for a in self._anodes:

            for am, mass in a._mass_breakdown['active_materials'].items():
                if am in anode_mass_breakdown['active_materials']:
                    anode_mass_breakdown['active_materials'][am] += mass
                else:
                    anode_mass_breakdown['active_materials'][am] = mass

            for b, mass in a._mass_breakdown['binders'].items():
                if b in anode_mass_breakdown['binders']:
                    anode_mass_breakdown['binders'][b] += mass
                else:
                    anode_mass_breakdown['binders'][b] = mass

            for ca, mass in a._mass_breakdown['conductive_additives'].items():
                if ca in anode_mass_breakdown['conductive_additives']:
                    anode_mass_breakdown['conductive_additives'][ca] += mass
                else:
                    anode_mass_breakdown['conductive_additives'][ca] = mass

            current_collector = a._current_collector
            current_collector_mass = a._current_collector._mass
            if current_collector in anode_mass_breakdown['current_collectors']:
                anode_mass_breakdown['current_collectors'][current_collector] += current_collector_mass
            else:
                anode_mass_breakdown['current_collectors'][current_collector] = current_collector_mass

        self._anode_mass_breakdown = anode_mass_breakdown

    def _calculate_stack_properties(self):
        self._pore_volume = self._total_anode_pore_volume + self._total_cathode_pore_volume + self._separator._pore_volume
        self._length = self._separator._fold_length + (self._separator._thickness * self._additional_separator_wraps * 2)
        self._width = self._separator._width

    def _calculate_active_area(self):
        self._active_geometric_area = sum([c._single_sided_area * 2 for c in self._cathodes])

    def _calculate_separator_properties(self):
        self._n_separator_folds = len(self._cathodes) + len(self._anodes) + 1 + 2 * self._additional_separator_wraps
        self._calculate_separator_length()
        self._separator._calculate_area_properties()

    def _calculate_separator_length(self):
        """
        Function to calculate the length of the separator needed in the stack
        """
        # length of separator between layers
        length_between_layers = self._separator._fold_length * self._n_separator_folds

        # get the additional length that wraps around the edge of the cathode
        cathode_cap_len = 0
        for c in self._cathodes:
            cathode_cap_len += PI * (c._thickness + self._separator._thickness)

        # get the additional length that wraps around the edge of the anode
        anode_cap_len = 0
        for a in self._anodes[1:]:
            anode_cap_len += PI * (a._thickness + self._separator._thickness)

        # get the area of the sides of the stack from the additional separator wraps. thickness changes with each wrap
        stack_thickness = self._total_anode_thickness + self._total_cathode_thickness + (self._separator._thickness * self._n_separator_folds)

        for w in range(self._additional_separator_wraps):
            stack_thickness += self._separator._thickness * 2
        side_length = stack_thickness * 2

        # get the total length
        total_length = length_between_layers + cathode_cap_len + anode_cap_len + side_length

        self._separator._length = total_length
        self._thickness = stack_thickness

    def _calculate_anode_properties(self):
        self._total_anode_thickness = sum([a._thickness for a in self._anodes])
        self._total_anode_pore_volume = sum([a._pore_volume for a in self._anodes])
        
        anode_overhang = (self._anodes[0]._single_sided_area/self._cathodes[0]._single_sided_area) - 1
        for a in self._anodes:
            a._overhang = anode_overhang

    def _calculate_cathode_properties(self):
        self._total_cathode_thickness = sum([c._thickness for c in self._cathodes])
        self._total_cathode_pore_volume = sum([c._pore_volume for c in self._cathodes])
    
    def _copy_cathode(self, cathode: Cathode, n_layers: int):
        """
        Function to check the cathode properties and copy them into a list

        :param cathode: Cathode: cathode used in the stack
        """
        self._cathodes = [copy(cathode) for _ in range(n_layers)]
        for i, c in enumerate(self._cathodes):
            c._name = f"{cathode._name}_{i+1}"

        del self._cathode

    def _copy_anode(self, anode: Anode | CurrentCollector, n_layers: int):
        """
        Function to check the anode properties and copy them into a list
        
        :param anode: Anode: anode used in the stack
        """
        for c in self._cathodes:
            if c._current_collector._length > anode._current_collector._length:
                raise ValueError("Cathode current collector length must be greater or equal to anode length")
            
            if c._current_collector._width > anode._current_collector._width:
                raise ValueError("Cathode current collector width must be greater or equal to anode width")
            
        self._anodes = [copy(anode) for _ in range(n_layers)]

        for i in range(n_layers):
            self._anodes[i]._name = f"{anode._name}_{i}"

        del self._anode
        
    def get_layup(self, paper_bgcolor='white', plot_bgcolor='white', **kwargs):

        figure = go.Figure()
        all_x = []
        all_y = []

        # Separator 1
        for trace in self._separator.get_top_down_view().data:
            trace.legendgroup = 'Separator third layer'
            trace.name = 'Separator third layer'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Cathode
        for trace in self._cathodes[0]._current_collector.get_top_down_view().data:
            trace.legendgroup = 'Cathode'
            trace.showlegend = True if trace.name == 'Covered Area' else False
            trace.name = 'Cathode'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Separator 1
        for trace in self._separator.get_top_down_view().data:
            trace.legendgroup = 'Separator second layer'
            trace.name = 'Separator second layer'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Anode
        for trace in self._anodes[0]._current_collector.get_top_down_view().data:
            trace.legendgroup = 'Anode'
            trace.showlegend = True if trace.name == 'Covered Area' else False
            trace.name = 'Anode'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Separator 2
        for trace in self._separator.get_top_down_view().data:
            trace.legendgroup = 'Separator top layer'
            trace.name = 'Separator top layer'
            trace.line = dict(color='black', width=1)
            figure.add_trace(trace)
            all_x.extend(trace.x)
            all_y.extend(trace.y)

        # Compute axis ranges with a small margin
        if all_x and all_y:
            x_margin = 0.05 * (max(all_x) - min(all_x)) if max(all_x) > min(all_x) else 1
            y_margin = 0.05 * (max(all_y) - min(all_y)) if max(all_y) > min(all_y) else 1
            x_range = [min(all_x) - x_margin, max(all_x) + x_margin]
            y_range = [min(all_y) - y_margin, max(all_y) + y_margin]
        else:
            x_range = None
            y_range = None

        figure.update_layout(
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                scaleanchor="y",
                title="X (mm)",
                range=x_range
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                title="Y (mm)",
                range=y_range
            ),
            paper_bgcolor=paper_bgcolor,
            plot_bgcolor=plot_bgcolor,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            **kwargs
        )

        return figure

    @property
    def anodes(self):
        return self._anodes
    
    @property
    def cathodes(self):
        return self._cathodes

    def __str__(self):
        return f"{self.name}"
        
    def __repr__(self):
        return self.__str__()
    
