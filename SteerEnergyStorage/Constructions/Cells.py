from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.Containers import Pouch, PrismaticCase

import pandas as pd
import numpy as np
import plotly.express as px
from copy import deepcopy, copy
from scipy.interpolate import CubicSpline

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
                 grid_n: int = 100,
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
        self._validate_and_copy_electrolyte(electrolyte, electrolyte_overfill)
        self._name = name
        self._reversible_capacity = reversible_capacity * H_TO_S
        self._irreversible_capacity = irreversible_capacity * H_TO_S
        self._grid_n = grid_n

    def _validate_and_copy_electrolyte(self, electrolyte: Electrolyte, electrolyte_overfill: float) -> Electrolyte:
        """
        Function to validate and copy electrolyte
        """
        if not isinstance(electrolyte, Electrolyte):
            raise ValueError("Electrolyte must be an instance of Electrolyte")
        
        if not (0 <= electrolyte_overfill <= 100):
            raise ValueError("Electrolyte_overfill percentage must be between 0 and 100")
        
        self._electrolyte = deepcopy(electrolyte)
        self._electrolyte_overfill = electrolyte_overfill

    def get_capacity_voltage_plot(self, **kwargs):

        try:
            cathode_curve = self.cathode_half_cell_curve.copy()
            anode_curve = self.anode_half_cell_curve.copy()
            full_curves = self.full_cell_curve.copy()
        except AttributeError:
            raise AttributeError("The cell curves have not been calculated yet. Make sure you initiated the right cell object")

        cathode_curve = self.cathode_half_cell_curve.copy().assign(Electrode='Cathode')
        anode_curve = self.anode_half_cell_curve.copy().assign(Electrode='Anode')
        full_curves = self.full_cell_curve.copy().assign(Electrode='Full Cell')

        data = pd.concat([cathode_curve, anode_curve, full_curves])
        upper_cap_limit = self.reversible_capacity + self.irreversible_capacity
        lower_cap_limit = self.irreversible_capacity

        color_map = {'Cathode': 'blue', 'Anode': 'red', 'Full Cell': 'black'}

        figure = px.line(data, x='Capacity (Ah)', y='Voltage (V)', color='Electrode', title='Capacity vs Voltage', 
                         template='presentation', color_discrete_map=color_map, **kwargs)
        
        figure.update_traces(line=dict(width=4))
        figure.add_vline(x=upper_cap_limit, line_color='black', line_width=2)
        figure.add_vline(x=lower_cap_limit, line_color='black', line_width=2)
        return figure

    @property
    def electrolyte_overfill(self) -> float:
        return self._electrolyte_overfill * 100

    @property
    def electrolyte(self) -> Electrolyte:
        return self._electrolyte
    
    @property
    def full_cell_curve(self):

        if not hasattr(self, '_full_cell_curve'):
            raise AttributeError("Full cell curves have not been calculated yet")

        data = (self
                ._full_cell_curve
                .assign(capacity = lambda x: x['capacity'] * S_TO_H)
                .rename(columns={'capacity': 'Capacity (Ah)', 
                                 'voltage': 'Voltage (V)', 
                                 'direction': 'Direction'})
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
        return {item.replace('_', ' ').title(): round(value, 3) for item, value in self._cost_breakdown.items()}
    
    @property
    def stacks_cost_breakdown(self) -> dict:
        if not hasattr(self, '_stacks_cost_breakdown'):
            raise AttributeError("Stacks cost breakdown has not been calculated yet")
        return {item.replace('_', ' ').title(): round(value, 3) for item, value in self._stacks_cost_breakdown.items()}
    
    @property
    def anode_cost_breakdown(self) -> dict:
        
        if not hasattr(self, '_anode_cost_breakdown'):
            raise AttributeError("Anode cost breakdown has not been calculated yet")
        
        cost_breakdown = {
            key.replace('_', ' ').title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()}
            for key, inner in self._anode_cost_breakdown.items()
        }

        return cost_breakdown
    
    @property
    def cathode_cost_breakdown(self) -> dict:

        if not hasattr(self, '_cathode_cost_breakdown'):
            raise AttributeError("Cathode cost breakdown has not been calculated yet")
        
        cost_breakdown = {
            key.replace('_', ' ').title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()}
            for key, inner in self._cathode_cost_breakdown.items()
        }

        return cost_breakdown
    
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
        return {item.replace('_', ' ').title(): round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}
    
    @property
    def stacks_mass_breakdown(self) -> dict:
        if not hasattr(self, '_stacks_mass_breakdown'):
            raise AttributeError("Stacks mass breakdown has not been calculated yet")
        return {item.replace('_', ' ').title(): round(value * KG_TO_G, 3) for item, value in self._stacks_mass_breakdown.items()}

    @property
    def anode_mass_breakdown(self) -> dict:
        
        if not hasattr(self, '_anode_mass_breakdown'):
            raise AttributeError("Anode mass breakdown has not been calculated yet")
        
        mass_breakdown = {
            key.replace('_', ' ').title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()}
            for key, inner in self._anode_mass_breakdown.items()
        }

        return mass_breakdown
    
    @property
    def cathode_mass_breakdown(self) -> dict:
        
        if not hasattr(self, '_cathode_mass_breakdown'):
            raise AttributeError("Cathode mass breakdown has not been calculated yet")
        
        mass_breakdown = {
            key.replace('_', ' ').title(): {obj: round(value * KG_TO_G, 3) for obj, value in inner.items()}
            for key, inner in self._cathode_mass_breakdown.items()
        }

        return mass_breakdown

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
                 grid_n: int = 100,
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
        
        self._validate_and_copy_prismatic_case(prismatic_case)
        self._set_prismatic_case_properties()

    def _set_prismatic_case_properties(self):
        self._height = self._prismatic_case._external_height
        self._width = self._prismatic_case._external_width
        self._length = self._prismatic_case._external_length
        self._volume = self._prismatic_case._external_volume

    def _validate_and_copy_prismatic_case(self, prismatic_case: PrismaticCase) -> PrismaticCase:

        if not isinstance(prismatic_case, PrismaticCase):
            raise ValueError("Prismatic case must be an instance of PrismaticCase")
        
        self._prismatic_case = copy(prismatic_case)
    
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
                 grid_n: int = 100,
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
        
        self._validate_and_copy_pouch(pouch, positive_terminal, negative_terminal)

    def _validate_and_copy_pouch(self, pouch: Pouch, positive_terminal: Terminal, negative_terminal: Terminal) -> Pouch:

        if not isinstance(pouch, Pouch):
            raise ValueError("Pouch must be an instance of Pouch")
        
        if not isinstance(positive_terminal, Terminal):
            raise ValueError("Positive terminal must be an instance of Terminal")
        
        if not isinstance(negative_terminal, Terminal):
            raise ValueError("Negative terminal must be an instance of Terminal")
        
        self._pouch = copy(pouch)
        self._positive_terminal = positive_terminal
        self._negative_terminal = negative_terminal

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
                 n_stacks: int = 1,
                 grid_n: int = 100,
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
        :param n_stacks: Number of stacks in the cell
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
        
        self._validate_and_copy_stack(stack, n_stacks)
        self._calculate_electrolyte_quantities()
        self._calculate_half_cell_curves()
        self._calculate_full_cell_curve()
        self._get_effective_areal_capacity() #TODO 
        self._calculate_energy() 

    def _validate_and_copy_stack(self, stack: Stack, n_stacks: int) -> None:
        """
        Function to validate the stack and copy it n times

        :param stack: Stack to validate
        :param n_stacks: Number of times to copy the stack
        """
        if not isinstance(stack, Stack):
            raise ValueError("Stack must be an instance of Stack")
        
        self._stacks = [deepcopy(stack) for _ in range(n_stacks)]
        if n_stacks > 1:
            for i, stack in enumerate(self._stacks):
                stack._name = f"{stack._name}_{i + 1}"

    def _get_effective_areal_capacity(self) -> None:
        """
        Function to calculate the effective areal capacity of the stacks
        """
        self._effective_areal_capacity = self._reversible_capacity / sum([s._areal_capacity for s in self._stacks])

    def _calculate_electrolyte_quantities(self):
        """
        Function to calculate the electrolyte quantities in the cell
        """
        self._electrolyte._volume = sum([s._pore_volume for s in self._stacks]) * (1 + self._electrolyte_overfill)
        self._electrolyte._mass = self._electrolyte._volume * self._electrolyte._density
        self._electrolyte._cost = (self._electrolyte._mass) * self._electrolyte._specific_cost  

    def _calculate_half_cell_curves(self):
        """
        Function to calculate the half cell curve of the stack from the half cell curves of the anode and cathode active materials
        """
        for s in self._stacks:
            s._calculate_half_cell_curves(grid_n=self._grid_n)

        cathode_half_cell = (pd
                             .concat([s._cathode_half_cell_curve for c in self._stacks])
                             .groupby(['direction', 'voltage'], as_index=False)['capacity']
                             .sum()
                             .groupby('direction', as_index=False)
                             .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                             )

        anode_half_cell = (pd
                           .concat([s._anode_half_cell_curve for a in self._stacks])
                           .groupby(['direction', 'voltage'], as_index=False)['capacity']
                           .sum()
                           .groupby('direction', as_index=False)
                           .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                           )
        
        self._cathode_half_cell_curve = cathode_half_cell
        self._anode_half_cell_curve = anode_half_cell
    
    def _calculate_full_cell_curve(self):
        """
        Function to calculate the full cell curves of the stack
        """
        for s in self._stacks:
            s._calculate_full_cell_curve()

        full_cell_curve = (pd
                            .concat([s._full_cell_curve for s in self._stacks])
                            .groupby(['direction', 'voltage'], as_index=False)['capacity']
                            .sum()
                            .sort_values(['direction', 'capacity'])
                            )
        
        charge_curve = full_cell_curve.query("direction == 'charge'")
        discharge_curve = full_cell_curve.query("direction == 'discharge'")

        # interpolate charge_curve on capacity
        min_cap = charge_curve['capacity'].min()
        top_cap = self._reversible_capacity + self._irreversible_capacity
        max_cap = top_cap if top_cap < charge_curve['capacity'].max() else charge_curve['capacity'].max()
        cap_grid = np.linspace(min_cap, max_cap, self._grid_n)
        cs = CubicSpline(charge_curve['capacity'], charge_curve['voltage'])
        new_voltage = cs(cap_grid)
        charge_curve = pd.DataFrame({'capacity': cap_grid, 'voltage': new_voltage, 'direction': 'charge'})

        # interpolate discharge_curve on capacity
        max_cap = top_cap if top_cap < charge_curve['capacity'].max() else charge_curve['capacity'].max()
        min_cap = self._irreversible_capacity if self._irreversible_capacity > discharge_curve['capacity'].min() else discharge_curve['capacity'].min()
        cap_grid = np.linspace(min_cap, max_cap, self._grid_n)
        cs = CubicSpline(discharge_curve['capacity'], discharge_curve['voltage'])
        new_voltage = cs(cap_grid)
        discharge_curve = pd.DataFrame({'capacity': cap_grid, 'voltage': new_voltage, 'direction': 'discharge'})

        self._full_cell_curve = (pd
                                 .concat([charge_curve, discharge_curve])
                                 .groupby('direction', as_index=False)
                                 .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                                 )
    
    def _linear_interpolate_on_voltage(self, df) -> pd.DataFrame:

            direction = df['direction'].iloc[0]
            electrode = df['electrode'].iloc[0]

            if direction == "discharge" and electrode == "cathode":
                df = df.sort_values(by='capacity', ascending=False)
            elif direction == "charge" and electrode == "anode":
                df = df.sort_values(by='capacity', ascending=False)

            x_max = df['voltage'].max()
            x_min = df['voltage'].min()
            x = df['voltage']
            y = df['capacity']
            y_new = np.interp(self._v_grid, x, y)

            return (pd
                    .DataFrame({'capacity': y_new, 'voltage': self._v_grid})
                    .query("voltage >= @x_min and voltage <= @x_max")
                    )
    
    def _linear_interpolate_on_capacity(self, df) -> pd.DataFrame:
            
            df = df.sort_values(by='capacity', ascending=True)
            x_max = df['capacity'].max()
            x_min = df['capacity'].min()
            x = df['capacity']
            y = df['voltage']
            y_new = np.interp(self._c_grid, x, y)

            return (pd
                    .DataFrame({'voltage': y_new, 'capacity': self._c_grid})
                    .query("capacity >= @x_min and capacity <= @x_max")
                    )
    
    def _calculate_energy(self):
        self._energy = -np.trapezoid(self._full_cell_curve.query("direction == 'discharge'")['voltage'],
                                     self._full_cell_curve.query("direction == 'discharge'")['capacity'])
    
    def _get_mass_breakdown_plot_pie(self, **kwargs):

        mass_breakdown = self.mass_breakdown
        stack_mass_breakdown = self.stacks_mass_breakdown
        mass_breakdown.pop('Stacks')
        mass_breakdown.update(stack_mass_breakdown)
        mass_breakdown = pd.DataFrame(mass_breakdown.items(), columns=['component', 'mass']).assign(level = 'Cell')

        anode_mass_breakdown = self.anode_mass_breakdown
        anode_mass_breakdown = {obj: value for innder_dict in anode_mass_breakdown.values() for obj, value in innder_dict.items()}
        anode_mass_breakdown = pd.DataFrame(anode_mass_breakdown.items(), columns=['component', 'mass']).assign(level = 'Anode').assign(component = lambda x: x['component'].apply(lambda y: y.name))

        cathode_mass_breakdown = self.cathode_mass_breakdown
        cathode_mass_breakdown = {obj: value for innder_dict in cathode_mass_breakdown.values() for obj, value in innder_dict.items()}
        cathode_mass_breakdown = pd.DataFrame(cathode_mass_breakdown.items(), columns=['component', 'mass']).assign(level = 'Cathode').assign(component = lambda x: x['component'].apply(lambda y: y.name))

        data = pd.concat([mass_breakdown, anode_mass_breakdown, cathode_mass_breakdown])

        figure = px.pie(data, values='mass', names='component', title='Mass Breakdown', facet_col='level', color='component')
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure

    def _get_cost_breakdown_plot_pie(self, **kwargs):

        cost_breakdown = self.cost_breakdown
        stack_cost_breakdown = self.stacks_cost_breakdown
        cost_breakdown.pop('Stacks')
        cost_breakdown.update(stack_cost_breakdown)
        cost_breakdown = pd.DataFrame(cost_breakdown.items(), columns=['component', 'cost']).assign(level = 'Cell')

        anode_cost_breakdown = self.anode_cost_breakdown
        anode_cost_breakdown = {obj: value for innder_dict in anode_cost_breakdown.values() for obj, value in innder_dict.items()}
        anode_cost_breakdown = pd.DataFrame(anode_cost_breakdown.items(), columns=['component', 'cost']).assign(level = 'Anode').assign(component = lambda x: x['component'].apply(lambda y: y.name))

        cathode_cost_breakdown = self.cathode_cost_breakdown
        cathode_cost_breakdown = {obj: value for innder_dict in cathode_cost_breakdown.values() for obj, value in innder_dict.items()}
        cathode_cost_breakdown = pd.DataFrame(cathode_cost_breakdown.items(), columns=['component', 'cost']).assign(level = 'Cathode').assign(component = lambda x: x['component'].apply(lambda y: y.name))

        data = pd.concat([cost_breakdown, anode_cost_breakdown, cathode_cost_breakdown])

        figure = px.pie(data, values='cost', names='component', title='Cost Breakdown', facet_col='level', color='component')
        figure.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
        figure.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

        return figure

    def get_mass_breakdown_plot(self, plot_mode: str = 'pie', **kwargs):

        if plot_mode.lower() == 'pie':
            figure = self._get_mass_breakdown_plot_pie(**kwargs)
        else:
            raise ValueError("Plot mode not recognized. Please choose between 'pie'")

        return figure
    
    def get_cost_breakdown_plot(self, plot_mode: str = 'pie', **kwargs):

        if plot_mode.lower() == 'pie':
            figure = self._get_cost_breakdown_plot_pie(**kwargs)
        else:
            raise ValueError("Plot mode not recognized. Please choose between 'pie'")

        return figure

    @property
    def cathode_areal_capacity(self):
        return round(self._cathode_areal_capacity * (S_TO_H * A_TO_mA / M_TO_CM**2), 2)

    @property
    def stacks(self) -> Stack:
        return self._stacks
    
    @property
    def effective_areal_capacity(self) -> float:
        return round(self._effective_areal_capacity, 2) 


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
                 n_stacks: int = 1,
                 grid_n: int = 100,
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
                              n_stacks=n_stacks,
                              grid_n=grid_n,
                              name=name)

        self._calculate_pouch_properties()
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()
        self._calculate_geometry_properties()
        self._calculate_energy_properties()

    def _calculate_pouch_properties(self):
        self._pouch._width = max([s._width for s in self._stacks]) + 2 * self._pouch._heat_seal_size_sides
        self._pouch._length = max([s._length for s in self._stacks]) + self._pouch._heat_seal_size_top
        self._pouch._area = self._pouch._width * self._pouch._length
        self._pouch._mass = 2 * self._pouch._area * self._pouch._laminate._areal_mass
        self._pouch._cost = self._pouch._area * self._pouch._laminate._areal_cost

    def _add_to_dict(self, dictionary_1: dict, dictionary_2: dict):
        
        for key, value in dictionary_2.items():
            if key in dictionary_1:
                dictionary_1[key] += value
            else:
                dictionary_1[key] = value

        return dictionary_1

    def _calculate_cost_breakdown(self):

        self._cost_breakdown = {'stacks': sum([s._cost for s in self._stacks]),
                                'electrolyte': self._electrolyte._cost,
                                'encapsulation': self._pouch._cost + self._positive_terminal._cost + self._negative_terminal._cost}
        
        self._stacks_cost_breakdown = {'cathode': sum([s._cost_breakdown['cathode'] for s in self._stacks]),
                                       'anode': sum([s._cost_breakdown['anode'] for s in self._stacks]),
                                       'separator': sum([s._cost_breakdown['separator'] for s in self._stacks])}
        
        anode_cost_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}
        cathode_cost_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for s in self._stacks:
            for key in anode_cost_breakdown.keys():
                anode_cost_breakdown[key] = self._add_to_dict(anode_cost_breakdown[key], s._anode_cost_breakdown[key])
            for key in cathode_cost_breakdown.keys():
                cathode_cost_breakdown[key] = self._add_to_dict(cathode_cost_breakdown[key], s._cathode_cost_breakdown[key])

        self._anode_cost_breakdown = anode_cost_breakdown
        self._cathode_cost_breakdown = cathode_cost_breakdown

        self._cost = sum(self._cost_breakdown.values())

    def _calculate_mass_breakdown(self):
        
        self._mass_breakdown = {'stacks': sum([s._mass for s in self._stacks]),
                                'electrolyte': self._electrolyte._mass,
                                'encapsulation': self._pouch._mass + self._positive_terminal._mass + self._positive_terminal._mass}
        
        self._stacks_mass_breakdown = {'cathode': sum([s._mass_breakdown['cathode'] for s in self._stacks]),
                                       'anode': sum([s._mass_breakdown['anode'] for s in self._stacks]),
                                       'separator': sum([s._mass_breakdown['separator'] for s in self._stacks])}
        
        anode_mass_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}
        cathode_mass_breakdown = {'active_materials': {}, 'binders': {}, 'conductive_additives': {}, 'current_collectors': {}}

        for s in self._stacks:
            for key in anode_mass_breakdown.keys():
                anode_mass_breakdown[key] = self._add_to_dict(anode_mass_breakdown[key], s._anode_mass_breakdown[key])
            for key in cathode_mass_breakdown.keys():
                cathode_mass_breakdown[key] = self._add_to_dict(cathode_mass_breakdown[key], s._cathode_mass_breakdown[key])

        self._anode_mass_breakdown = anode_mass_breakdown
        self._cathode_mass_breakdown = cathode_mass_breakdown

        self._mass = sum(self._mass_breakdown.values())
    
    def _calculate_geometry_properties(self):
        self._thickness = sum([s._thickness for s in self._stacks]) + self._pouch._laminate._thickness * 2
        self._volume = self._pouch._length * self._pouch._width * self._thickness

    def _calculate_energy_properties(self):
        self._specific_energy = self._energy / self._mass
        self._energy_density = self._energy / self._volume
        self._normalized_cost = self._cost / self._energy


class StackedPrismaticCell(_PrismaticCell, _StackedCell):

    def __init__(self,
                 stack: Stack,
                 prismatic_case: PrismaticCase,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 grid_n: int = 100,
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
