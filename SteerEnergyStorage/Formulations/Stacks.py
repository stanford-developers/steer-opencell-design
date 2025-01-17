import numpy as np
from SteerEnergyStorage.Constructions.Electrodes import Anode
from SteerEnergyStorage.Constructions.Electrodes import Cathode
from SteerEnergyStorage.Materials.Seperators import Separator


class Stack():

    def __init__(self, 
                 anode: Anode,
                 cathode: Cathode,
                 n_stacks: int,
                 seperator: Separator,
                 n_p_ratio: float = 1.3):
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell
        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param n_stacks: int: number of stacks in the cell
        :param seperator: Separator: seperator used in the stack
        :param n_p_ratio: float: n/p ratio of the stack
        """
        if n_stacks != seperator.n_stacks:
            raise ValueError("The number of stacks in the stack should be equal to the number of stacks in the seperator")

        self._anode = anode
        self._cathode = cathode
        self._n_stacks = n_stacks
        self._seperator = seperator
        self._n_p_ratio = n_p_ratio

        self._active_geometric_area = self._cathode._single_sided_area * 2 * self._n_stacks

        # Calculate the masses in the stack
        self._total_cathode_mass = self._cathode.mass * self._n_stacks
        self._total_anode_mass = self._anode.mass * (self._n_stacks + 1)

        # Calculate the costs in the stack
        total_cathode_cc_cost = self._cathode._current_collector._cost * self._n_stacks
        total_anode_cc_cost = self._anode._current_collector._cost * (self._n_stacks + 1)
        self._total_cc_cost = total_cathode_cc_cost + total_anode_cc_cost

        # calculate pore volume
        total_cathode_pore_volume = self._cathode._pore_volume * self._n_stacks
        total_anode_pore_volume = self._anode._pore_volume * (self._n_stacks + 1)
        total_seperator_pore_volume = self._seperator._pore_volume
        self._pore_volume = total_anode_pore_volume + total_cathode_pore_volume + total_seperator_pore_volume

        # calculate the thickness of the stack
        total_cathode_thickness = self._cathode._double_sided_thickness * self._n_stacks
        total_anode_thickness = self._anode._double_sided_thickness * (self._n_stacks + 1)
        total_seperator_thickness = self._seperator._thickness * (self._n_stacks * 2 + 3) /1000
        self._thickness = total_anode_thickness + total_cathode_thickness + total_seperator_thickness

    @property
    def thickness(self):
        return np.round(self._thickness, 2)

    @property
    def active_geometric_area(self):
        return np.round(self._active_geometric_area, 2)

    @property
    def pore_volume(self):
        return np.round(self._pore_volume, 2)

    @property
    def total_cathode_mass(self):
        return np.round(self._total_cathode_mass, 2)
    
    @property
    def total_anode_mass(self):
        return np.round(self._total_anode_mass, 2)
    
    @property
    def total_cc_cost(self):
        return np.round(self._total_cc_cost, 2)

    @property
    def n_stacks(self):
        return self._n_stacks

    @property
    def anode(self):
        return self._anode
    
    @property
    def cathode(self):
        return self._cathode

    @property
    def n_p_ratio(self):
        return self._n_p_ratio

    @property
    def seperator(self):
        return self._seperator
    
    def __str__(self):
        return f"Stack with an anode formulation of {self.anode_formulation} and a cathode formulation of {self.cathode_formulation}"
    
    def __repr__(self):
        return f"Stack with an anode formulation of {self.anode_formulation} and a cathode formulation of {self.cathode_formulation}"
    
