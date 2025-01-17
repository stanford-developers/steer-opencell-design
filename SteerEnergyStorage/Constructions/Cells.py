import numpy as np
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.other import Pouch


class Cell():

    def __init__(self,
                 stack: Stack,
                 electrolyte: Electrolyte,
                 electrolyte_overfill:float,
                 voltage_upper_cut_off: float,
                 voltage_lower_cut_off: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal
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
        :param positive_terminal: Terminal: positive terminal of the cell
        :param negative_terminal: Terminal: negative terminal of the cell
        """
        self._stack = stack
        self._electrolyte = electrolyte
        self._electrolyte_overfill = electrolyte_overfill
        self._voltage_upper_cut_off = voltage_upper_cut_off
        self._voltage_lower_cut_off = voltage_lower_cut_off
        self._reversible_capacity = reversible_capacity
        self._irreversible_capacity = irreversible_capacity
        self._positive_terminal = positive_terminal
        self._negative_terminal = negative_terminal

        self._effective_areal_capacity = self._reversible_capacity / self._stack.active_geometric_area

        # calculate electrolyte quantities
        self._electrolyte._volume = self._stack._pore_volume * (1 + self._electrolyte_overfill/100)
        self._electrolyte._mass = self._electrolyte.volume * self._electrolyte.density
        self._electrolyte._cost = (self._electrolyte.mass/1000) * self._electrolyte.specific_cost                     

    @property
    def positive_terminal(self):
        return self._positive_terminal
    
    @property
    def negative_terminal(self):
        return self._negative_terminal

    @property
    def effective_areal_capacity(self):
        return np.round(self._effective_areal_capacity, 2)

    @property
    def electrolyte_overfill(self):
        return self._electrolyte_overfill

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
                 pouch: Pouch,
                 width: float,
                 length: float,
                 electrolyte: Electrolyte,
                 electrolyte_overfill:float,
                 voltage_upper_cut_off: float,
                 voltage_lower_cut_off: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal
                 ):
        """
        A class that represents a pouch cell
        :param stack: Stack: stack within the cell
        :param width: float: width of the cell in cm
        :param length: float: length of the cell in cm
        :param electrolyte: Electrolyte: electrolyte used in the cell
        :param electrolyte_overfill: float: overfill of the electrolyte in the cell %
        :param voltage_upper_cut_off: float: upper cut-off voltage of the cell
        :param voltage_lower_cut_off: float: lower cut-off voltage of the cell
        :param reversible_capacity: float: reversible capacity of the cell in mAh
        :param irreversible_capacity: float: irreversible capacity of the cell in mAh,
        :param positive_terminal: Terminal: positive terminal of the cell
        :param negative_terminal: Terminal: negative terminal of the cell
        """
        super().__init__(stack = stack, 
                         electrolyte = electrolyte, 
                         electrolyte_overfill = electrolyte_overfill, 
                         voltage_upper_cut_off = voltage_upper_cut_off, 
                         voltage_lower_cut_off = voltage_lower_cut_off, 
                         reversible_capacity = reversible_capacity, 
                         irreversible_capacity = irreversible_capacity,
                         positive_terminal = positive_terminal,
                         negative_terminal = negative_terminal
                         )
        
        self._length = length
        self._width = width
        self._pouch = pouch

        self._mass = self._stack._total_cathode_mass + \
                     self._stack._total_anode_mass + \
                     self._stack._seperator._mass + \
                     self._electrolyte._mass + \
                     self._pouch._mass + \
                     self._positive_terminal._mass + \
                     self._negative_terminal._mass
        
        self._thickness = self._stack._thickness + (self._pouch._laminate._thickness * 2)/1000
        self._volume = (self._length/10 * self._width/10 * self._thickness/10)/1000 # in Liters

    @property
    def mass(self):
        return np.round(self._mass, 2)
    
    @property
    def thickness(self):
        return np.round(self._thickness, 2)
    
    @property
    def volume(self):
        return np.rounc(self._volume, 2)

    @property
    def pouch(self):
        return self._pouch

    @property
    def length(self):
        return self._length
    
    @property
    def width(self):
        return self._width
    
    def __str__(self):
        return f"Pouch cell with a width of {self.width} cm and a length of {self.length} cm"
    
    def __repr__(self):
        return f"Pouch cell with a width of {self.width} cm and a length of {self.length} cm"
    