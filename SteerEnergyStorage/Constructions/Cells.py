import numpy as np
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte


class Cell():

    def __init__(self,
                 stack: Stack,
                 electrolyte: Electrolyte,
                 electrolyte_overfill = 10,
                 voltage_upper_cut_off: float = 4.2,
                 voltage_lower_cut_off: float = 0.1,
                 reversible_capacity: float = 12000,
                 irreversible_capacity: float = 1000
                 ):
        """
        Initiate an object that represents an electrochemical cell
        :param stack: Stack: stack within the cell
        :param electrolyte: Electrolyte: electrolyte used in the cell
        :param electrolyte_overfill: float: overfill of the electrolyte in the cell %
        :param voltage_upper_cut_off: float: upper cut-off voltage of the cell
        :param voltage_lower_cut_off: float: lower cut-off voltage of the cell
        :param reversible_capacity: float: reversible capacity of the cell in mAh
        :param irreversible_capacity: float: irreversible capacity of the cell in mAh,
        """
        self._stack = stack
        self._electrolyte = electrolyte
        self._electrolyte_overfill = electrolyte_overfill
        self._voltage_upper_cut_off = voltage_upper_cut_off
        self._voltage_lower_cut_off = voltage_lower_cut_off
        self._reversible_capacity = reversible_capacity
        self._irreversible_capacity = irreversible_capacity

    @property
    def electrolyte_overfill(self):
        return self._electrolyte_overfill

    @property
    def cathode_bare_tab_area(self):
        return self._cathode_bare_tab_area
    
    @property
    def anode_bare_tab_area(self):
        return self._anode_bare_tab_area

    @property
    def reversible_capacity(self):
        return self._reversible_capacity
    
    @property
    def irreversible_capacity(self):
        return self._irreversible_capacity

    @property
    def stack(self):
        return self._stack

    @property
    def electrolyte(self):
        return self._electrolyte
    
    @property
    def voltage_upper_cut_off(self):
        return self._voltage_upper_cut_off
    
    @property
    def voltage_lower_cut_off(self):
        return self._voltage_lower_cut_off
    
    def __str__(self):
        return f"Cell with a n/p ratio of {self.n_p_ratio}"
    
    def __repr__(self):
        return f"Cell with a n/p ratio of {self.n_p_ratio}"
    

class StackedPouchCell(Cell):

    def __init__(self,
                 stack: Stack,
                 width: float,
                 length: float,
                 n_stack: int,
                 electrolyte: Electrolyte,
                 electrolyte_overfill = 10,
                 voltage_upper_cut_off: float = 4.2,
                 voltage_lower_cut_off: float = 0.1,
                 reversible_capacity: float = 12000,
                 irreversible_capacity: float = 1000
                 ):
        """
        A class that represents a pouch cell
        :param stack: Stack: stack within the cell
        :param width: float: width of the cell in cm
        :param length: float: length of the cell in cm
        :param n_stack: int: number of stacks in the cell
        :param electrolyte: Electrolyte: electrolyte used in the cell
        :param electrolyte_overfill: float: overfill of the electrolyte in the cell %
        :param voltage_upper_cut_off: float: upper cut-off voltage of the cell
        :param voltage_lower_cut_off: float: lower cut-off voltage of the cell
        :param reversible_capacity: float: reversible capacity of the cell in mAh
        :param irreversible_capacity: float: irreversible capacity of the cell in mAh,
        """
        super().__init__(stack = stack, 
                       electrolyte = electrolyte, 
                       electrolyte_overfill = electrolyte_overfill, 
                       voltage_upper_cut_off = voltage_upper_cut_off, 
                       voltage_lower_cut_off = voltage_lower_cut_off, 
                       reversible_capacity = reversible_capacity, 
                       irreversible_capacity = irreversible_capacity)
        
        self._length = length
        self._width = width
        self._n_stack = n_stack

        self._active_geometric_area = self._calculate_active_geometric_area()
        self._effective_areal_capacity = self._calculate_effective_areal_capacity()

    @property
    def effective_areal_capacity(self):
        return np.round(self._effective_areal_capacity, 2)

    @property
    def active_geometric_area(self):
        return self._active_geometric_area

    @property
    def length(self):
        return self._length
    
    @property
    def width(self):
        return self._width
    
    @property
    def n_stack(self):
        return self._n_stack
    
    def _calculate_active_geometric_area(self):
        """
        Function to calculate the active geometric area of a stacked pouch cell
        """
        return self._stack._cathode._single_sided_area * 2 * self._n_stack
    
    def _calculate_effective_areal_capacity(self):
        """
        Function to calculate the effective areal capacity of the cell
        """
        return self._reversible_capacity / self._active_geometric_area
    
    def __str__(self):
        return f"Pouch cell with a width of {self.width} cm and a length of {self.length} cm"
    
    def __repr__(self):
        return f"Pouch cell with a width of {self.width} cm and a length of {self.length} cm"
    