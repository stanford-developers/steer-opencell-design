from SteerEnergyStorage.Constructions.Electrodes import Anode, Cathode
from SteerEnergyStorage.Materials.Separators import Separator
import pandas as pd
import numpy as np

KG_TO_G = 1e3
M_TO_CM = 1e2
M_TO_MM = 1e3
A_TO_mA = 1e3
mA_TO_A = 1e-3
S_TO_H = 1/3600
H_TO_S = 3600

class Stack():

    def __init__(self, 
                 anode: Anode,
                 cathode: Cathode,
                 separator: Separator,
                 n_stacks: int,
                 additional_separator_wraps: int = 1,
                 name: str = 'Stack'):
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell
        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param n_stacks: int: number of stacks in the cell
        :param separator: Separator: separator used in the stack
        :param additional_separator_wraps: int: number of additional wraps of the separator in the stack
        :param n_p_ratio: float: n/p ratio of the stack
        :param name: str: name of the stack
        """
        self._cathode = cathode
        self._anode = self._check_anode(anode)
        self._separator = self._check_separator(separator)
        self._additional_separator_wraps = additional_separator_wraps
        self._name = name

        self._n_stacks = n_stacks
        self._calculate_active_area()
        self._calculate_anode_properties()
        self._calculate_cathode_properties()
        self._calculate_separator_properties()
        self._calculate_stack_properties()
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()

    def _calculate_cost_breakdown(self):

        # calculate the cost breakdown
        self._cost_breakdown = {
            self._cathode: self._cathode._cost * self._n_cathode,
            self._anode: self._anode._cost * self._n_anode,
            self._separator: self._separator._cost
        }

        # calculate the total cost
        self._cost = sum(self._cost_breakdown.values())

        # get the cathode cost breakdown
        self._cathode_cost_breakdown = {
            "Active Material": {active_material: cost*self._n_stacks for active_material, cost in self._cathode._active_material_costs.items()},
            "Binder": {binder: cost*self._n_stacks for binder, cost in self._cathode._binder_costs.items()},
            "Conductive Additive": {conductive_additive: cost*self._n_stacks for conductive_additive, cost in self._cathode._conductive_additive_costs.items()},
            "Current Collector": self._cathode._current_collector._cost * self._n_stacks
        }

        # get the anode cost breakdown
        self._anode_cost_breakdown = {
            "Active Materials": {active_material: cost*(self._n_stacks + 1) for active_material, cost in self._anode._active_material_costs.items()},
            "Binders": {binder: cost*(self._n_stacks + 1) for binder, cost in self._anode._binder_costs.items()},
            "Conductive Additives": {conductive_additive: cost*(self._n_stacks + 1) for conductive_additive, cost in self._anode._conductive_additive_costs.items()},
            "Current Collector": self._anode._current_collector._cost * (self._n_stacks + 1)
        }

    def _calculate_mass_breakdown(self):

        self._mass_breakdown = {
            self._cathode: self._cathode._mass * self._n_cathode,
            self._anode: self._anode._mass * self._n_anode,
            self._separator: self._separator._mass
        }
        self._mass = sum(self._mass_breakdown.values())

        # calculate the cathode mass breakdown
        self._cathode_mass_breakdown = {
            "Active Materials": {active_material: mass * self._n_cathode for active_material, mass in self._cathode._active_masses.items()},
            "Binders": {binder: mass * self._n_cathode for binder, mass in self._cathode._binder_masses.items()},
            "Conductive Additives": {conductive_additive: mass * self._n_cathode for conductive_additive, mass in self._cathode._conductive_additive_masses.items()},
            "Current Collector": self._cathode._current_collector.mass * self._n_cathode
        }

        # calculate the anode mass breakdown
        self._anode_mass_breakdown = {
            "Active Materials": {active_material: mass * self._n_anode for active_material, mass in self._anode._active_masses.items()},
            "Binders": {binder: mass * self._n_anode for binder, mass in self._anode._binder_masses.items()},
            "Conductive Additives": {conductive_additive: mass * self._n_anode for conductive_additive, mass in self._anode._conductive_additive_masses.items()},
            "Current Collector": self._anode._current_collector.mass * self._n_anode
        }

    def _calculate_stack_properties(self):
        self._pore_volume = self._total_anode_pore_volume + self._total_cathode_pore_volume + self._separator._pore_volume
        self._length = self._separator._fold_length + (self._separator._thickness * self._additional_separator_wraps * 2)
        self._width = self._separator._slit_width

    def _calculate_active_area(self):
        self._active_geometric_area = self._cathode._single_sided_area * 2 * self._n_stacks

    def _calculate_separator_properties(self):
        self._n_separator = self._n_cathode + self._n_anode + 1 + 2 * self._additional_separator_wraps
        self._separator._area, self._thickness = self._calculate_sperarator_area()
        self._separator._mass = self._separator._thickness * self._separator._area * self._separator._density
        self._separator._cost = self._separator._area * self._separator._areal_cost
        self._separator._pore_volume = self._separator._thickness * self._separator._area * self._separator._porosity

    def _calculate_anode_properties(self):
        self._n_anode = self._n_stacks + 1
        self._total_anode_thickness = self._anode._double_sided_thickness * self._n_anode
        self._total_anode_pore_volume = self._anode._pore_volume * self._n_anode
        self._anode._overhang = (self._anode._single_sided_area/self._cathode._single_sided_area) - 1

    def _calculate_cathode_properties(self):
        self._n_cathode = self._n_stacks
        self._total_cathode_thickness = self._cathode._double_sided_thickness * self._n_cathode
        self._total_cathode_pore_volume = self._cathode._pore_volume * self._n_cathode

    def _calculate_sperarator_area(self):
        """
        Function to calculate the area of the separator used in the stack
        """
        # get the separator area between the electrodes
        area_between_stacks = self._separator._slit_width * self._separator._fold_length * self._n_separator

        # get the additional area that wraps around the edge of the cathode
        n_cathode_caps = self._n_cathode
        area_per_cathode_cap = np.pi * (self._cathode._double_sided_thickness + self._separator._thickness) * self._separator._slit_width

        # get the additional area that wraps around the edge of the anode
        n_anode_caps = self._n_anode
        area_per_anode_cap = np.pi * (self._anode._double_sided_thickness + self._separator._thickness) * self._separator._slit_width

        # get the area of the sides of the stack from the additional separator wraps. thickness changes with each wrap
        stack_thickness = self._total_anode_thickness + self._total_cathode_thickness + self._separator._thickness*self._n_separator
        for w in range(self._additional_separator_wraps):
            stack_thickness += self._separator._thickness * 2
        side_area = stack_thickness * self._separator._slit_width * 2

        # get the total area
        total_area = area_between_stacks + (n_cathode_caps * area_per_cathode_cap) + (n_anode_caps * area_per_anode_cap) + side_area

        return total_area, stack_thickness

    def _check_anode(self, anode: Anode):

        if anode._current_collector._length < self._cathode._current_collector._length:
            raise ValueError("Anode current collector length must be greater or equal to cathode length")
        
        if anode._current_collector._width < self._cathode._current_collector._width:
            raise ValueError("Anode current collector width must be greater or equal to cathode width")

        return anode
    
    def _check_separator(self, separator: Separator):

        cathode_length = self._cathode._current_collector._length
        anode_length = self._anode._current_collector._length
        separator_length = separator._fold_length

        if separator_length < cathode_length or separator_length < anode_length:
            raise ValueError("separator length must be greater or equal to cathode and anode length")
        
        cathode_width = self._cathode._current_collector._width
        anode_width = self._anode._current_collector._width
        separator_width = separator._slit_width

        if separator_width < cathode_width or separator_width < anode_width:
            raise ValueError("separator width must be greater or equal to cathode and anode width")

        return separator
    
    @property
    def cathode_charge_curve(self):
        return self.half_cell_curves.query("electrode == 'cathode' and direction == 'charge'")
    
    @property
    def cathode_discharge_curve(self):
        return self.half_cell_curves.query("electrode == 'cathode' and direction == 'discharge'")
    
    @property
    def anode_charge_curve(self):
        return self.half_cell_curves.query("electrode == 'anode' and direction == 'charge'")
    
    @property
    def anode_discharge_curve(self):
        return self.half_cell_curves.query("electrode == 'anode' and direction == 'discharge'")
    
    @property
    def name(self):
        return self._name

    @property
    def cost_breakdown(self):
        return {item: round(value, 3) for item, value in self._cost_breakdown.items()}
    
    @property
    def cathode_cost_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._cathode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_cost_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._anode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def mass_breakdown(self):
        return {item: round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}
    
    @property
    def cathode_mass_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value * KG_TO_G, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._cathode_mass_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_mass_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value * KG_TO_G, 3) for key, value in value.items()}
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
        return {item: round(value * KG_TO_G, 2) for item, value in self._mass_breakdown.items()}

    @property
    def n_stacks(self):
        return self._n_stacks
    
    @n_stacks.setter
    def n_stacks(self, n_stacks: int):
        self._n_stacks = n_stacks
        self._calculate_active_area()
        self._calculate_anode_properties()
        self._calculate_cathode_properties()
        self._calculate_separator_properties()
        self._calculate_stack_properties()
        self._calculate_mass_breakdown()
        self._calculate_cost_breakdown()
    
    @property
    def n_cathode(self):
        return self._n_cathode
    
    @property
    def n_anode(self):
        return self._n_anode
    
    @property
    def n_separator(self):
        return self._n_separator

    @property
    def anode(self):
        return self._anode
    
    @property
    def cathode(self):
        return self._cathode
    
    @property
    def separator(self):
        return self._separator
    
    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"stack"
        
    def __repr__(self):
        return self.__str__()
    