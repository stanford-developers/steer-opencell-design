from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte


class Cell():

    def __init__(self,
                 stack: Stack,
                 electrolyte: Electrolyte,
                 overhang: float = 0,
                 electrolyte_overfill = 10,
                 voltage_upper_cut_off: float = 4.2,
                 voltage_lower_cut_off: float = 0.1,
                 reversible_capacity: float = 12000,
                 irreversible_capacity: float = 1000,
                 cathode_bare_tab_area: float = 8.22,
                 anode_bare_tab_area: float = 7.55,
                 ):
        """
        Initiate an object that represents an electrochemical cell
        :param stack: Stack: stack within the cell
        :param electrolyte: Electrolyte: electrolyte used in the cell
        :param overhang: float: overhang of the electrodes in the cell
        :param electrolyte_overfill: float: overfill of the electrolyte in the cell %
        :param voltage_upper_cut_off: float: upper cut-off voltage of the cell
        :param voltage_lower_cut_off: float: lower cut-off voltage of the cell
        :param reversible_capacity: float: reversible capacity of the cell in mAh
        :param irreversible_capacity: float: irreversible capacity of the cell in mAh,
        :param cathode_bare_tab_area: float: area of the cathode bare tab in cm^2
        :param anode_bare_tab_area: float: area of the anode bare tab in cm^2
        """
        self._stack = stack
        self._electrolyte = electrolyte
        self._overhang = overhang
        self._electrolyte_overfill = electrolyte_overfill
        self._voltage_upper_cut_off = voltage_upper_cut_off
        self._voltage_lower_cut_off = voltage_lower_cut_off
        self._reversible_capacity = reversible_capacity
        self._irreversible_capacity = irreversible_capacity
        self._cathode_bare_tab_area = cathode_bare_tab_area
        self._anode_bare_tab_area = anode_bare_tab_area

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
    def overhang(self):
        return self._overhang
    
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
    

class PouchCell(Cell):

    def __init__(self,
                 width: float,
                 length: float,
                 stack: Stack,
                 electrolyte: Electrolyte,
                 overhang: float = 0,
                 electrolyte_overfill = 10,
                 voltage_upper_cut_off: float = 4.2,
                 voltage_lower_cut_off: float = 0.1,
                 reversible_capacity: float = 12000,
                 irreversible_capacity: float = 1000,
                 cathode_bare_tab_area: float = 8.22,
                 anode_bare_tab_area: float = 7.55
                 ):
        """
        A class that represents a pouch cell
        :param width: float: width of the cell in cm
        :param length: float: length of the cell in cm
        :param stack: Stack: stack within the cell
        :param electrolyte: Electrolyte: electrolyte used in the cell
        :param overhang: float: overhang of the electrodes in the cell
        :param electrolyte_overfill: float: overfill of the electrolyte in the cell %
        :param voltage_upper_cut_off: float: upper cut-off voltage of the cell
        :param voltage_lower_cut_off: float: lower cut-off voltage of the cell
        :param reversible_capacity: float: reversible capacity of the cell in mAh
        :param irreversible_capacity: float: irreversible capacity of the cell in mAh,
        :param cathode_bare_tab_area: float: area of the cathode bare tab in cm^2
        :param anode_bare_tab_area: float: area of the anode bare tab in cm^2
        """
        super.__init__(stack = stack, 
                       electrolyte = electrolyte, 
                       overhang = overhang, 
                       electrolyte_overfill = electrolyte_overfill, 
                       voltage_upper_cut_off = voltage_upper_cut_off, 
                       voltage_lower_cut_off = voltage_lower_cut_off, 
                       reversible_capacity = reversible_capacity, 
                       irreversible_capacity = irreversible_capacity, 
                       cathode_bare_tab_area = cathode_bare_tab_area,
                       anode_bare_tab_area = anode_bare_tab_area)
        self._length = length
        self._width = width

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