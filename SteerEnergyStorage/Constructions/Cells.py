from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.Containers import Pouch, PrismaticCase
from scipy.interpolate import interp1d
import warnings

import pandas as pd
import numpy as np
import plotly.express as px

KG_TO_G = 1e3
M_TO_CM = 1e2
M_TO_MM = 1e3
A_TO_mA = 1e3
mA_TO_A = 1e-3
S_TO_H = 1/3600
H_TO_S = 3600
W_TO_KW = 1e-3
M_TO_DM = 10

class _Cell:
    def __init__(self,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 500,
                 name: str = 'Cell'):
        """
        Initiate an object that represents an electrochemical cell.

        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param reversible_capacity: Reversible capacity of the cell in Ah
        :param irreversible_capacity: Irreversible capacity of the cell in Ah
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        self._electrolyte = self._validate_electrolyte(electrolyte)
        self._electrolyte_overfill = self._validate_percentage(electrolyte_overfill) / 100
        self._name = name
        self._reversible_capacity = reversible_capacity * H_TO_S
        self._irreversible_capacity = irreversible_capacity * H_TO_S
        self._grid_n = grid_n

    def get_capacity_voltage_plot(self, 
                                  upper_voltage_cuttoff: float = None, 
                                  lower_voltage_cutoff: float = None,
                                  **kwargs):

        try:
            half_curves = self.half_cell_curves.copy()
            full_curves = self.full_cell_curves.copy()
        except AttributeError:
            raise AttributeError("The cell curves have not been calculated yet. Make sure you initiated the right cell object")

        data = (pd
                .concat([half_curves, full_curves])
                .assign(sort_key_1 = lambda x: [-c if d == 'discharge' else c for c, d in zip(x['Capacity (Ah)'], x['Direction'])])
                .assign(sort_key_2 = lambda x: [1 if d == 'discharge' else 0 for d in x['Direction']])
                .sort_values(by=['Electrode', 'sort_key_2', 'sort_key_1'])
                .drop(columns=['sort_key_2', 'sort_key_1'])
                )

        upper_cap_limit = self.reversible_capacity + self.irreversible_capacity
        lower_cap_limit = self.irreversible_capacity

        color_map = {'cathode': 'blue', 'anode': 'red', 'full cell': 'black'}

        figure = px.line(data, x='Capacity (Ah)', y='Voltage (V)', color='Electrode', title='Capacity vs Voltage', 
                         template='presentation', color_discrete_map=color_map, **kwargs)
        
        figure.update_traces(line=dict(width=4))
        figure.add_vline(x=upper_cap_limit, line_color='black', line_width=2)
        figure.add_vline(x=lower_cap_limit, line_color='black', line_width=2)

        if upper_voltage_cuttoff:
            figure.add_hline(y=upper_voltage_cuttoff, line_color='black', line_width=2)
        if lower_voltage_cutoff:
            figure.add_hline(y=lower_voltage_cutoff, line_color='black', line_width=2)

        return figure

    def _validate_electrolyte(self, value: Electrolyte) -> Electrolyte:
        if not isinstance(value, Electrolyte):
            raise ValueError("Electrolyte must be an instance of Electrolyte")
        return value

    def _validate_percentage(self, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Percentage must be between 0 and 100")
        return value
    
    def get_cost_breakdown_plot(self, mode='pie', **kwargs):
        """
        Function to get the cost breakdown of the cell in a plot

        :param mode: str: mode of the plot. Options are 'pie' and 'bar'
        """
        if mode == 'pie':
            return self._get_cost_breakdown_plot_pie(**kwargs)
        else:
            raise ValueError("Only pie plot is supported for now")
        
    def get_mass_breakdown_plot(self, mode='pie', **kwargs):
        """
        Function to get the mass breakdown of the cell in a plot

        :param mode: str: mode of the plot. Options are 'pie' and 'bar'
        """
        if mode == 'pie':
            return self._get_mass_breakdown_plot_pie(**kwargs)
        else:
            return ValueError("Only pie plot is supported for now")

    @property
    def electrolyte_overfill(self) -> float:
        return self._electrolyte_overfill * 100

    @property
    def electrolyte(self) -> Electrolyte:
        return self._electrolyte
    
    @property
    def full_cell_curves(self):

        if not hasattr(self, '_full_cell_curves'):
            raise AttributeError("Full cell curves have not been calculated yet")

        data = (self
                ._full_cell_curves
                .assign(capacity = lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction',
                                 'electrode': 'Electrode'})
                )
        
        return data
    
    @property
    def half_cell_curves(self):

        if not hasattr(self, '_half_cell_curves'):
            raise AttributeError("Half cell curves have not been calculated yet")

        data = (self
                ._half_cell_curves
                .assign(capacity = lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction', 
                                 'electrode': 'Electrode'})
                )
        
        return data
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def reversible_capacity(self) -> float:
        return round(self._reversible_capacity * S_TO_H, 2)
    
    @property
    def irreversible_capacity(self) -> float:
        return round(self._irreversible_capacity * S_TO_H, 2)
    
    @property
    def cost_breakdown(self) -> dict:
        if not hasattr(self, '_cost_breakdown'):
            raise AttributeError("Cost breakdown has not been calculated yet")
        return {item: round(value, 3) for item, value in self._cost_breakdown.items()}
    
    @property
    def cost(self) -> float:
        if not hasattr(self, '_cost'):
            raise AttributeError("Cost has not been calculated yet")
        return round(self._cost, 2)

    @property
    def mass(self) -> float:
        if not hasattr(self, '_mass'):
            raise AttributeError("Mass has not been calculated yet")
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def mass_breakdown(self) -> dict:
        if not hasattr(self, '_mass_breakdown'):
            raise AttributeError("Mass breakdown has not been calculated yet")
        return {item: round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}
    
    @property
    def thickness(self) -> float:
        if not hasattr(self, '_thickness'):
            raise AttributeError("Thickness has not been calculated yet")
        return round(self._thickness * M_TO_MM, 2)
    
    @property
    def volume(self) -> float:
        if not hasattr(self, '_volume'):
            raise AttributeError("Volume has not been calculated yet")
        return round(self._volume * M_TO_CM**3, 2)
    
    @property
    def height(self) -> float:
        if not hasattr(self, '_height'):
            raise AttributeError("Height has not been calculated yet")
        return round(self._height * M_TO_CM, 2)
    
    @property
    def width(self) -> float:
        if not hasattr(self, '_width'):
            raise AttributeError("Width has not been calculated yet")
        return round(self._width * M_TO_CM, 2)
    
    @property
    def length(self) -> float:
        if not hasattr(self, '_length'):
            raise AttributeError("Length has not been calculated yet")
        return round(self._length * M_TO_CM, 2)
    
    @property
    def energy(self) -> float:
        if not hasattr(self, '_energy'):
            raise AttributeError("Energy has not been calculated yet")
        return round(self._energy * S_TO_H, 2)
    
    @property
    def specific_energy(self) -> float:
        if not hasattr(self, '_specific_energy'):
            raise AttributeError("Specific energy has not been calculated yet")
        return round(self._specific_energy * S_TO_H, 2)
    
    @property
    def energy_density(self) -> float:
        if not hasattr(self, '_energy_density'):
            raise AttributeError("Energy density has not been calculated yet")
        return round(self._energy_density * S_TO_H / M_TO_DM**3, 2)
    
    @property
    def normalized_cost(self) -> float:
        if not hasattr(self, '_normalized_cost'):
            raise AttributeError("Normalized cost has not been calculated yet")
        return round(self._normalized_cost /  (S_TO_H * W_TO_KW), 2)
    
    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return self.__str__()
    

class _PrismaticCell(_Cell):

    def __init__(self,
                 prismatic_case: PrismaticCase,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 500,
                 name: str = 'Prismatic cell'):
        """
        Class to represent a prismatic cell.

        :param prismatic_case: Prismatic case used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        _Cell.__init__(self,
                      electrolyte=electrolyte, 
                      electrolyte_overfill=electrolyte_overfill, 
                      reversible_capacity=reversible_capacity,
                      irreversible_capacity=irreversible_capacity,
                      grid_n=grid_n,
                      name=name)
        
        self._prismatic_case = self._validate_prismatic_case(prismatic_case)
        self._height = self._prismatic_case._external_height
        self._width = self._prismatic_case._external_width
        self._length = self._prismatic_case._external_length
        self._volume = self._prismatic_case._external_volume

    def _validate_prismatic_case(self, value: PrismaticCase) -> PrismaticCase:
        if not isinstance(value, PrismaticCase):
            raise ValueError("Prismatic case must be an instance of PrismaticCase")
        return value
    
    @property
    def prismatic_case(self) -> PrismaticCase:
        return self._prismatic_case


class _PouchCell(_Cell):
    def __init__(self,
                 pouch: Pouch,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 500,
                 name: str = 'Pouch Cell'):
        """
        Class to represent a pouch cell.

        :param pouch: Pouch used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param name: Name of the cell
        """
        _Cell.__init__(self,
                         electrolyte=electrolyte, 
                         electrolyte_overfill=electrolyte_overfill, 
                         reversible_capacity=reversible_capacity,
                         irreversible_capacity=irreversible_capacity,
                         grid_n=grid_n,
                         name=name)
        
        self._pouch = self._validate_pouch(pouch)
        self._positive_terminal = positive_terminal
        self._negative_terminal = negative_terminal

    def _validate_pouch(self, value: Pouch) -> Pouch:
        if not isinstance(value, Pouch):
            raise ValueError("Pouch must be an instance of Pouch")
        return value

    @property
    def pouch(self) -> Pouch:
        return self._pouch
    
    @property
    def positive_terminal(self) -> Terminal:
        return self._positive_terminal
    
    @property
    def negative_terminal(self) -> Terminal:
        return self._negative_terminal
    

class _StackedCell(_Cell):

    def __init__(self,
                 stack: Stack,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 500,
                 name: str = "Stacked Cell"):
        """
        A class that represents a stacked cell.

        :param stack: Stack within the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        _Cell.__init__(self,
                      electrolyte=electrolyte, 
                      electrolyte_overfill=electrolyte_overfill, 
                      reversible_capacity=reversible_capacity,
                      irreversible_capacity=irreversible_capacity,
                      grid_n=grid_n,
                      name=name)
        
        self._stack = self._validate_stack(stack)
        self._effective_areal_capacity = self._reversible_capacity / self._stack._active_geometric_area
        self._calculate_electrolyte_properties()
        self._half_cell_curves, self._cathode_areal_capacity = self._calculate_half_cell_curves()
        self._full_cell_curves = self._calculate_full_cell_curves()

        # get storage properties
        self._energy = -np.trapezoid(self._full_cell_curves.query("direction == 'discharge'")['voltage'],
                                     self._full_cell_curves.query("direction == 'discharge'")['capacity'])
        
        #color_dictionary
        self._color_map = {self.name: '#2E86AB', 
                            'Encapsulation': '#F6C85F', 
                            self.stack.anode.name: '#9B59B6', 
                            self.stack.cathode.name: '#E74C3C', 
                            self.stack.separator.name: '#27AE60',
                            self.electrolyte.name: '#F39C12'}
        self._color_map.update(self.stack.cathode.formulation._color_map)
        self._color_map.update(self.stack.anode.formulation._color_map)   

    def _calculate_electrolyte_properties(self):
        """
        Function to calculate the properties of the electrolyte
        """
        self._electrolyte._volume = self._stack._pore_volume * (1 + self._electrolyte_overfill)
        self._electrolyte._mass = self._electrolyte._volume * self._electrolyte._density
        self._electrolyte._cost = (self._electrolyte._mass) * self._electrolyte._specific_cost      

    def _calculate_half_cell_curves(self):
        """
        Function to calculate the half cell curve of the stack from the half cell curves of the anode and cathode active materials
        """
        # get the cathode data
        cathode_data = (pd
                        .concat([am._half_cell_curve.copy().assign(active_material = am) for am in self.stack._cathode._formulation._active_materials.keys()])
                        .assign(mass = lambda x: [self.stack._cathode_mass_breakdown['Active Materials'][am] for am in x['active_material']])
                        .assign(electrode = 'cathode')
                        )
        
        # get the anode data
        if len(self.stack._anode._formulation._active_materials.keys()) > 0:
            # if the anode has active materials on it
            anode_data = (pd
                          .concat([am._half_cell_curve.copy().assign(active_material = am) for am in self.stack._anode._formulation._active_materials.keys()])
                          .assign(mass = lambda x: [self.stack._anode_mass_breakdown['Active Materials'][am] for am in x['active_material']])
                          .assign(electrode = 'anode')
                          )
        else:
            anode_data = pd.DataFrame()

        # calculate the capacity of each active material
        half_cell_curves = (pd
                            .concat([cathode_data, anode_data])
                            .assign(irrev_scaling = lambda x: [am._irreversible_capacity_scaling for am in x['active_material']])
                            .assign(rev_scaling = lambda x: [am._reversible_capacity_scaling for am in x['active_material']])
                            .assign(capacity = lambda x: x['mass'] * x['specific_capacity'])
                            .assign(capacity = lambda x: [c * i if d == "charge" else c * i * r for c, i, d, r in zip(x['capacity'], x['irrev_scaling'], x['direction'], x['rev_scaling'])])
                            .filter(['voltage', 'capacity', 'direction', 'active_material', 'electrode'])
                            .sort_values(by=['electrode', 'direction', 'active_material', 'capacity'])
                            )
        
        def order_and_clean_curves(df) -> pd.DataFrame:
            """
            Function to order and clean the curves ready for interpolation
            """
            electrode = df['electrode'].iloc[0]
            direction = df['direction'].iloc[0]

            if (electrode == 'cathode' and direction == 'charge') or (electrode == 'anode' and direction == 'discharge'):
                df = df.groupby(['active_material']).apply(lambda df: df.sort_values('capacity', ascending=True)).reset_index(drop=True)
            elif (electrode == 'cathode' and direction == 'discharge') or (electrode == 'anode' and direction == 'charge'):
                df = df.groupby(['active_material']).apply(lambda df: df.sort_values('capacity', ascending=False)).reset_index(drop=True)
            else:
                raise ValueError("Invalid direction or electrode in voltage interpolation")
            
            df = df.loc[df['voltage'] >= df['voltage'].cummax()].reset_index()
            return df
        
        def linear_interpolate_on_voltage(df) -> pd.DataFrame:
            """
            Function to linearly interpolate the curves on voltage
            """ 
            v_min = df['voltage'].min()
            v_max = df['voltage'].max()
            voltage_grid = np.linspace(v_min, v_max, self._grid_n)
            new_data = []
            for am in df['active_material'].unique():
                am_data = df.query(f"active_material == @am")
                x = am_data['voltage']
                y = am_data['capacity']
                first_cap = y.iloc[0]
                last_cap = y.iloc[-1]

                interp_func = interp1d(x, y, kind='linear', fill_value=(first_cap, last_cap), bounds_error=False)
                new_data.append(pd.DataFrame({'voltage': voltage_grid, 'capacity': interp_func(voltage_grid), 'active_material': am}))

            new_data = (pd
                        .concat(new_data)
                        .query('capacity != inf')
                        .query('capacity != -inf')
                        .sort_values(by=['active_material', 'capacity'])
                        )

            return new_data
        
        half_cell_curves = (half_cell_curves
                            .groupby(['electrode', 'direction', 'active_material'], group_keys=True)
                            .apply(lambda df: df.pipe(order_and_clean_curves))
                            .reset_index(drop=True)
                            .groupby(['electrode', 'direction'], group_keys=True)
                            .apply(lambda df: df.pipe(linear_interpolate_on_voltage))
                            .reset_index(drop=False)
                            .groupby(['electrode', 'direction', 'voltage'], group_keys=True)
                            .agg({'capacity': 'sum'})
                            .reset_index(drop=False)
                            )

        # flip the curves and shift
        half_cell_curves = (half_cell_curves
                            .groupby(['electrode'], group_keys=True)
                            .apply(lambda df: (df
                                               .assign(max_capacity = lambda x: x['capacity'].max())
                                               .assign(capacity = lambda x: [-c + m if d == 'discharge' else c for c, d, m in zip(x['capacity'], x['direction'], x['max_capacity'])])
                                               ))
                            .reset_index(drop=True)
                            .drop(columns=['max_capacity'])
                            )
        
        reversible_cathode_capacity = half_cell_curves.query("electrode == 'cathode' and direction == 'discharge'")['capacity'].max()
        cathode_areal_capacity = reversible_cathode_capacity / self.stack._active_geometric_area
        return half_cell_curves, cathode_areal_capacity
    
    def _calculate_full_cell_curves(self):
        """
        Function to calculate the full cell curves of the stack
        """
        def linear_interpolate_on_capacity(df) -> pd.DataFrame:
            warnings.simplefilter("ignore", category=RuntimeWarning)
            df1 = df.query("electrode == 'cathode'")
            df2 = df.query("electrode == 'anode'")
            interp_func = interp1d(df2['capacity'], df2['voltage'], kind='linear', fill_value='extrapolate')
            df1['voltage'] = df1['voltage'] - interp_func(df1['capacity'])
            return df1.assign(electrode = 'full cell').query('voltage != inf').query('voltage != -inf')

        full_cell_curves = (self
                            ._half_cell_curves
                            .copy()
                            .groupby(['direction'], group_keys=True)
                            .apply(lambda df: (df
                                               .sort_values(by='capacity', ascending=True)
                                               .pipe(linear_interpolate_on_capacity)
                                               ))
                            .reset_index(drop=True)
                            .query('capacity <= (@self._reversible_capacity + @self._irreversible_capacity)')
                            .query('direction == "charge" or (direction == "discharge" and capacity >= @self._irreversible_capacity)')
                            )
        
        cathode_discharge_min = self._half_cell_curves.query("electrode == 'cathode' and direction == 'discharge'")['capacity'].min()
        anode_discharge_min = self._half_cell_curves.query("electrode == 'anode' and direction == 'discharge'")['capacity'].min()

        full_cell_curves = (full_cell_curves
                            .query('not (direction == "discharge" and capacity < @cathode_discharge_min)')
                            .query('not (direction == "discharge" and capacity < @anode_discharge_min)')
                            )
        
        full_cell_curves = (full_cell_curves
                            .assign(sort_key_1 = lambda x: [-c if d == 'discharge' else c for c, d in zip(x['capacity'], x['direction'])])
                            .assign(sort_key_2 = lambda x: [1 if d == 'discharge' else 0 for d in x['direction']])
                            .sort_values(by=['electrode', 'sort_key_2', 'sort_key_1'])
                            .drop(columns=['sort_key_2', 'sort_key_1'])
                            )

        return full_cell_curves
    
    @property
    def cathode_areal_capacity(self):
        return round(self._cathode_areal_capacity * (S_TO_H * A_TO_mA / M_TO_CM**2), 2)

    @property
    def stack(self) -> Stack:
        return self._stack
    
    @property
    def effective_areal_capacity(self) -> float:
        return round(self._effective_areal_capacity, 2)

    def _validate_stack(self, value: Stack) -> Stack:
        if not isinstance(value, Stack):
            raise ValueError("Stack must be an instance of Stack")
        return value
    
    def _get_mass_breakdown_data_for_plotting(self, **kwargs):

        cathode_flattened = {}
        for key, value in self.stack.cathode_mass_breakdown.items():
            if isinstance(value, dict):
                for obj, cost in value.items():
                    cathode_flattened[obj.name] = cost
            else:
                cathode_flattened[key] = value

        anode_flattened = {}
        for key, value in self.stack.anode_mass_breakdown.items():
            if isinstance(value, dict):
                for obj, cost in value.items():
                    anode_flattened[obj.name] = cost
            else:
                anode_flattened[key] = value

        data_cell = (pd
                     .DataFrame(self.mass_breakdown.items(), columns=['component', 'mass'])
                     .assign(component = lambda x: x['component'].apply(lambda y: y.name))
                     .assign(level = 'Cell')
                     )

        data_stack = (pd
                      .DataFrame(self.stack.mass_breakdown.items(), columns=['component', 'mass'])
                      .assign(component = lambda x: x['component'].apply(lambda y: y.name))
                      .assign(level = 'Cell')
                      )

        data_cathode = (pd
                        .DataFrame(cathode_flattened.items(), columns=['component', 'mass'])
                        .assign(level = 'Cathode')
                        )

        data_anode = (pd
                      .DataFrame(anode_flattened.items(), columns=['component', 'mass'])
                      .assign(level = 'Anode')
                      )

        data = pd.concat([data_cell, data_stack, data_cathode, data_anode])
        
        return data

    def _get_cost_breakdown_data_for_plotting(self, **kwargs):

        cathode_flattened = {}
        for key, value in self.stack.cathode_cost_breakdown.items():
            if isinstance(value, dict):
                for obj, cost in value.items():
                    cathode_flattened[obj.name] = cost
            else:
                cathode_flattened[key] = value

        anode_flattened = {}
        for key, value in self.stack.anode_cost_breakdown.items():
            if isinstance(value, dict):
                for obj, cost in value.items():
                    anode_flattened[obj.name] = cost
            else:
                anode_flattened[key] = value

        data_cell = (pd
                     .DataFrame(self.cost_breakdown.items(), columns=['component', 'cost'])
                     .assign(component = lambda x: x['component'].apply(lambda y: y.name))
                     .assign(level = 'Cell')
                     )

        data_stack = (pd
                      .DataFrame(self.stack.cost_breakdown.items(), columns=['component', 'cost'])
                      .assign(component = lambda x: x['component'].apply(lambda y: y.name))
                      .assign(level = 'Cell')
                      )
        
        data_cathode = (pd
                        .DataFrame(cathode_flattened.items(), columns=['component', 'cost'])
                        .assign(level = 'Cathode')
                        )

        data_anode = (pd
                      .DataFrame(anode_flattened.items(), columns=['component', 'cost'])
                      .assign(level = 'Anode')
                      )

        data = pd.concat([data_cell, data_stack, data_cathode, data_anode])

        return data


class StackedPouchCell(_PouchCell, _StackedCell):

    def __init__(self,
                 stack: Stack,
                 pouch: Pouch,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 1000,
                 name: str = 'Stacked Pouch Cell'):
        """
        A class that represents a stacked pouch cell.

        :param stack: Stack within the cell
        :param pouch: Pouch used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """
        _PouchCell.__init__(self,
                           pouch=pouch,
                           electrolyte=electrolyte,
                           electrolyte_overfill=electrolyte_overfill,
                           positive_terminal=positive_terminal,
                           negative_terminal=negative_terminal,
                           reversible_capacity=reversible_capacity,
                           irreversible_capacity=irreversible_capacity,
                           grid_n=grid_n,
                           name=name)
        
        _StackedCell.__init__(self,
                             stack=stack,
                             electrolyte=electrolyte,
                             electrolyte_overfill=electrolyte_overfill,
                             reversible_capacity=reversible_capacity,
                             irreversible_capacity=irreversible_capacity,
                             grid_n=grid_n,
                             name=name)

        # calculate pouch properties
        self._pouch._width = self._stack._width + 2 * self._pouch._heat_seal_size_sides
        self._pouch._length = self._stack._length + self._pouch._heat_seal_size_top
        self._pouch._area = self._pouch._width * self._pouch._length
        self._pouch._mass = 2 * self._pouch._area * self._pouch._laminate._areal_mass
        self._pouch._cost = self._pouch._area * self._pouch._laminate._areal_cost

        # calculate mass of cell
        self._mass_breakdown = {self._stack: self._stack._mass,
                                self._electrolyte: self._electrolyte._mass,
                                self._pouch: self._pouch._mass,
                                self._positive_terminal: self._positive_terminal._mass,
                                self._negative_terminal: self._negative_terminal._mass}

        self._mass = sum(self._mass_breakdown.values())
        
        # calculate geometric properties of the cell
        self._thickness = (self._stack._thickness + self._pouch._laminate._thickness * 2)
        self._volume = self._pouch._length * self._pouch._width * self._thickness

        # calculate cost of the cell
        self._cost_breakdown = {self._stack: self._stack._cost,
                                self._pouch: self._pouch._cost,
                                self._electrolyte: self._electrolyte._cost,
                                self._positive_terminal: self._positive_terminal._cost,
                                self._negative_terminal: self._negative_terminal._cost}

        self._cost = sum(self._cost_breakdown.values())

        # energy properties
        self._specific_energy = self._energy / self._mass
        self._energy_density = self._energy / self._volume
        self._normalized_cost = self._cost / self._energy

    def _get_mass_breakdown_plot_pie(self, **kwargs):

        data = (self
                ._get_mass_breakdown_data_for_plotting()
                .assign(component = lambda x: ['Encapsulation' 
                                               if c == self.pouch.name or c == self.positive_terminal.name or c == self.negative_terminal.name
                                               else c 
                                               for c in x['component']])
                .query(f'not (component == "{self.stack.name}" and level == "Cell")')
                )
        
        figure = px.pie(data, values='mass', names='component', title='Mass Breakdown', facet_col='level', color='component', color_discrete_map=self._color_map, **kwargs)
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure
    
    def _get_cost_breakdown_plot_pie(self, **kwargs):

        data = (self
                ._get_cost_breakdown_data_for_plotting()
                .assign(component = lambda x: ['Encapsulation' 
                                               if c == self.pouch.name or c == self.positive_terminal.name or c == self.negative_terminal.name
                                               else c 
                                               for c in x['component']])
                .query(f'not (component == "{self.stack.name}" and level == "Cell")')
                )

        figure = px.pie(data, values='cost', names='component', title='Cost Breakdown', facet_col='level', color='component', color_discrete_map=self._color_map, **kwargs)
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure
    

class StackedPrismaticCell(_PrismaticCell, _StackedCell):

    def __init__(self,
                 stack: Stack,
                 prismatic_case: PrismaticCase,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 500,
                 name: str = 'Stacked Prismatic Cell'):
        """
        A class that represents a stacked prismatic cell.

        :param stack: Stack within the cell
        :param prismatic_case: Prismatic case used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param grid_n: Number of points to interpolate the half cell curves
        :param name: Name of the cell
        """

        # Check stack is small enough to fit in the prismatic case
        if stack._thickness > prismatic_case._internal_height:
            raise ValueError("Stack thickness cannot be greater than the internal height of the prismatic case")
        if stack._width > prismatic_case._internal_width:
            raise ValueError("Stack width cannot be greater than the internal width of the prismatic case")
        if stack._length > prismatic_case._internal_length:
            raise ValueError("Stack length cannot be greater than the internal length of the prismatic case")

        _PrismaticCell.__init__(self,
                               prismatic_case=prismatic_case,
                               electrolyte=electrolyte,
                               electrolyte_overfill=electrolyte_overfill,
                               reversible_capacity=reversible_capacity,
                               irreversible_capacity=irreversible_capacity,
                               grid_n=grid_n,
                               name=name)
        
        _StackedCell.__init__(self,
                             stack=stack,
                             electrolyte=electrolyte,
                             electrolyte_overfill=electrolyte_overfill,
                             reversible_capacity=reversible_capacity,
                             irreversible_capacity=irreversible_capacity,
                             grid_n=grid_n,
                             name=name)

        self._mass_breakdown = {self._stack: self._stack._mass,
                                self._electrolyte: self._electrolyte._mass,
                                self._prismatic_case: self._prismatic_case._mass}
        
        self._mass = sum(self._mass_breakdown.values())

        # calculate cost of the cell
        self._cost_breakdown = {self._stack: self._stack._cost,
                                self._electrolyte: self._electrolyte._cost,
                                self._prismatic_case: self._prismatic_case._cost}

        self._cost = sum(self._cost_breakdown.values())

        # energy properties
        self._specific_energy = self._energy / self._mass
        self._energy_density = self._energy / self._volume
        self._normalized_cost = self._cost / self._energy

    def _get_mass_breakdown_plot_pie(self, **kwargs):

        data = (self
                ._get_mass_breakdown_data_for_plotting()
                .assign(component = lambda x: ['Encapsulation' 
                                               if c == self.prismatic_case.name
                                               else c 
                                               for c in x['component']])
                .query(f'not (component == "{self.stack.name}" and level == "Cell")')
                )

        figure = px.pie(data, values='mass', names='component', title='Mass Breakdown', facet_col='level', color='component', color_discrete_map=self._color_map, **kwargs)
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure
    
    def _get_cost_breakdown_plot_pie(self, **kwargs):

        data = (self
                ._get_cost_breakdown_data_for_plotting()
                .assign(component = lambda x: ['Encapsulation' 
                                               if c == self.prismatic_case.name
                                               else c 
                                               for c in x['component']])
                .query(f'not (component == "{self.stack.name}" and level == "Cell")')
                )

        figure = px.pie(data, values='cost', names='component', title='Cost Breakdown', facet_col='level', color='component', color_discrete_map=self._color_map, **kwargs)
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure
