from SteerEnergyStorage.Constructions.Electrodes import Anode, Cathode
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation

from copy import deepcopy
from copy import copy
import pandas as pd
import warnings
from scipy.interpolate import CubicSpline

KG_TO_G = 1e3
M_TO_CM = 1e2
M_TO_MM = 1e3
A_TO_mA = 1e3
mA_TO_A = 1e-3
S_TO_H = 1/3600
H_TO_S = 3600
PI = 3.14159265359

class Stack():

    def __init__(self, 
                 anode: Anode | CurrentCollector,
                 cathode: Cathode,
                 separator: Separator,
                 n_layers: int,
                 additional_separator_wraps: int = 1,
                 name: str = 'stack'):
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell

        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param n_layers: int: number of stacks in the cell
        :param separator: Separator: separator used in the stack
        :param additional_separator_wraps: int: number of additional wraps of the separator in the stack
        :param name: str: name of the stack
        """
        self._check_n_layers(n_layers)
        self._check_and_copy_cathode(cathode, n_layers)
        self._check_and_copy_anode(anode, n_layers)
        self._check_and_copy_separator(separator)

        self._additional_separator_wraps = additional_separator_wraps
        self._name = name

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

    def _calculate_half_cell_curves(self, grid_n: int):
        """
        Function to calculate the half cell curves for the stack. It will calculate the half cell curves for each electrode first, and then it will add the capacities together. 

        :param grid_n: int: number of points to use in the half cell curve
        """
        for c in self._cathodes:
            c._calculate_half_cell_curve(grid_n=grid_n)

        for a in self._anodes:
            a._calculate_half_cell_curve(grid_n=grid_n)

        cathode_half_cell = (pd
                             .concat([c._half_cell_curve for c in self._cathodes])
                             .groupby(['direction', 'voltage'], as_index=False)['capacity']
                             .sum()
                             .groupby('direction', as_index=False)
                             .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                             )

        anode_half_cell = (pd
                           .concat([a._half_cell_curve for a in self._anodes])
                           .groupby(['direction', 'voltage'], as_index=False)['capacity']
                           .sum()
                           .groupby('direction', as_index=False)
                           .apply(lambda x: x.sort_values('capacity', ascending=True if x['direction'].values[0] == 'charge' else False))
                           )
        
        self._areal_capacity = sum([c._areal_capacity for c in self._cathodes])
        self._cathode_half_cell_curve = cathode_half_cell
        self._anode_half_cell_curve = anode_half_cell

    @staticmethod
    def _cubic_interpolate_on_capacity(df) -> pd.DataFrame:

            warnings.simplefilter("ignore", category=RuntimeWarning)
            df1 = df.query("electrode == 'cathode'")
            df2 = df.query("electrode == 'anode'")

            interp_func = CubicSpline(df2['capacity'], df2['voltage'])
            df1['voltage'] = df1['voltage'] - interp_func(df1['capacity'])

            return (df1
                    .assign(electrode = 'full cell')
                    .query('voltage != inf')
                    .query('voltage != -inf')
                    )

    def _calculate_full_cell_curve(self):
        """
        Function to calculate the full cell curves of the stack
        """
        cathode_half_cell = self._cathode_half_cell_curve.copy().assign(electrode = 'cathode')
        anode_half_cell = self._anode_half_cell_curve.copy().assign(electrode = 'anode')

        full_cell_curve = (pd
                            .concat([cathode_half_cell, anode_half_cell])
                            .groupby(['direction'], group_keys=True)
                            .apply(lambda df: (df
                                               .sort_values(by='capacity', ascending=True)
                                               .pipe(self._cubic_interpolate_on_capacity)
                                               ))
                            .reset_index(drop=True)
                            )
        
        cathode_discharge_min = self._cathode_half_cell_curve.query("direction == 'discharge'")['capacity'].min()
        anode_discharge_min = self._anode_half_cell_curve.query("direction == 'discharge'")['capacity'].min()

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
        self._width = self._separator._slit_width

    def _calculate_active_area(self):
        self._active_geometric_area = sum([c._single_sided_area * 2 for c in self._cathodes])

    def _calculate_separator_properties(self):
        self._n_separator = len(self._cathodes) + len(self._anodes) + 1 + 2 * self._additional_separator_wraps
        self._separator._area, self._thickness = self._calculate_sperarator_area()
        self._separator._mass = self._separator._thickness * self._separator._area * self._separator._density
        self._separator._cost = self._separator._area * self._separator._areal_cost
        self._separator._pore_volume = self._separator._thickness * self._separator._area * self._separator._porosity

    def _calculate_anode_properties(self):
        self._total_anode_thickness = sum([a._double_sided_thickness for a in self._anodes])
        self._total_anode_pore_volume = sum([a._pore_volume for a in self._anodes])
        
        anode_overhang = (self._anodes[0]._single_sided_area/self._cathodes[0]._single_sided_area) - 1
        for a in self._anodes:
            a._overhang = anode_overhang

    def _calculate_cathode_properties(self):
        self._total_cathode_thickness = sum([c._double_sided_thickness for c in self._cathodes])
        self._total_cathode_pore_volume = sum([c._pore_volume for c in self._cathodes])

    def _calculate_sperarator_area(self):
        """
        Function to calculate the area of the separator used in the stack
        """
        # get the separator area between the electrodes
        area_between_stacks = self._separator._slit_width * self._separator._fold_length * self._n_separator

        # get the additional area that wraps around the edge of the cathode
        cathode_cap_area = 0
        for c in self._cathodes:
            cathode_cap_area += PI * (c._double_sided_thickness + self._separator._thickness) * self._separator._slit_width

        # get the additional area that wraps around the edge of the anode
        anode_cap_area = 0
        for a in self._anodes:
            anode_cap_area += PI * (a._double_sided_thickness + self._separator._thickness) * self._separator._slit_width

        # get the area of the sides of the stack from the additional separator wraps. thickness changes with each wrap
        stack_thickness = self._total_anode_thickness + self._total_cathode_thickness + (self._separator._thickness * self._n_separator)
        for w in range(self._additional_separator_wraps):
            stack_thickness += self._separator._thickness * 2
        side_area = stack_thickness * self._separator._slit_width * 2

        # get the total area
        total_area = area_between_stacks + cathode_cap_area + anode_cap_area + side_area

        return total_area, stack_thickness
    
    def _check_and_copy_cathode(self, cathode: Cathode, n_layers: int):
        """
        Function to check the cathode properties and copy them into a list

        :param cathode: Cathode: cathode used in the stack
        """
        if not isinstance(cathode, Cathode):
            raise ValueError("Cathode must be an instance of the Cathode class")
        
        self._cathodes = [copy(cathode) for _ in range(n_layers)]
        for i, c in enumerate(self._cathodes):
            c._name = f"{cathode._name}_{i+1}"

    def _check_and_copy_anode(self, anode: Anode | CurrentCollector, n_layers: int):
        """
        Function to check the anode properties and copy them into a list
        
        :param anode: Anode: anode used in the stack
        """
        if isinstance(anode, CurrentCollector):
            formulation = ElectrodeFormulation(active_materials={})
            anode = Anode(formulation=formulation, mass_loading=0, current_collector=anode, calender_density=1)

        for c in self._cathodes:
            if c._current_collector._length > anode._current_collector._length:
                raise ValueError("Cathode current collector length must be greater or equal to anode length")
            
            if c._current_collector._width > anode._current_collector._width:
                raise ValueError("Cathode current collector width must be greater or equal to anode width")
            
        self._anodes = [copy(anode) for _ in range(n_layers + 1)]

        for i in range(n_layers + 1):
            self._anodes[i]._name = f"{anode._name}_{i}"

    def _check_and_copy_separator(self, separator: Separator):
        """
        Function to check the separator properties

        :param separator: Separator: separator used in the stack
        """
        max_cathode_length = max([c._current_collector._length for c in self._cathodes])
        max_anode_length = max([a._current_collector._length for a in self._anodes])
        separator_length = separator._fold_length

        if separator_length < max_cathode_length or separator_length < max_anode_length:
            raise ValueError("separator length must be greater or equal to cathode and anode length")
        
        max_cathode_width = max([c._current_collector._width for c in self._cathodes])
        max_anode_width = max([a._current_collector._width for a in self._anodes])
        separator_width = separator._slit_width

        if separator_width < max_cathode_width or separator_width < max_anode_width:
            raise ValueError("separator width must be greater or equal to cathode and anode width")
        
        self._separator = deepcopy(separator)

    @property
    def name(self):
        return self._name

    @property
    def cost_breakdown(self):
        return {key.replace('_', ' ').capitalize(): round(value, 2) for key, value in self._cost_breakdown.items()}
    
    @property
    def cathode_cost_breakdown(self):
        rounded_dict = {
            item.replace('_', ' ').capitalize(): (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 2)
            )
            for item, value in self._cathode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_cost_breakdown(self):
        rounded_dict = {
            item.replace('_', ' ').capitalize(): (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 2)
            )
            for item, value in self._anode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def mass_breakdown(self):
        return {item: round(value * KG_TO_G, 2) for item, value in self._mass_breakdown.items()}
    
    @property
    def cathode_mass_breakdown(self):
        rounded_dict = {
            item.replace('_', ' ').capitalize(): (
                {key: round(value * KG_TO_G, 2) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._cathode_mass_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_mass_breakdown(self):
        rounded_dict = {
            item.replace('_', ' ').capitalize(): (
                {key: round(value * KG_TO_G, 2) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._anode_mass_breakdown.items()
        }
        return rounded_dict

    @property
    def cost(self):
        return round(self._cost, 2)

    @property
    def thickness(self):
        return round(self._thickness * M_TO_MM, 2)

    @property
    def active_geometric_area(self):
        return round(self._active_geometric_area * M_TO_CM**2, 2)

    @property
    def pore_volume(self):
        return round(self._pore_volume * M_TO_CM**3, 2)

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def mass_breakdown(self):
        return {item.replace('_', ' ').capitalize(): round(value * KG_TO_G, 2) for item, value in self._mass_breakdown.items()}

    @property
    def anodes(self):
        return self._anodes
    
    @property
    def cathodes(self):
        return self._cathodes
    
    @property
    def separator(self):
        return self._separator
    
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

    def __str__(self):
        return f"{self.name}"
        
    def __repr__(self):
        return self.__str__()
    