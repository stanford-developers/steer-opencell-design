from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.Containers import Pouch

KG_TO_G = 1e3
M_TO_CM = 1e2
M_TO_MM = 1e3

class Cell:
    def __init__(self,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 voltage_upper_cut_off: float,
                 voltage_lower_cut_off: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 name: str = 'Cell'):
        """
        Initiate an object that represents an electrochemical cell.

        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param voltage_upper_cut_off: Upper cut-off voltage of the cell
        :param voltage_lower_cut_off: Lower cut-off voltage of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param name: Name of the cell
        """
        self._electrolyte = self._validate_electrolyte(electrolyte)
        self._electrolyte_overfill = self._validate_percentage(electrolyte_overfill) / 100
        self._voltage_upper_cut_off = voltage_upper_cut_off
        self._voltage_lower_cut_off = voltage_lower_cut_off
        self._reversible_capacity = reversible_capacity
        self._irreversible_capacity = irreversible_capacity
        self._positive_terminal = positive_terminal
        self._negative_terminal = negative_terminal
        self._name = name

    def _validate_electrolyte(self, value: Electrolyte) -> Electrolyte:
        if not isinstance(value, Electrolyte):
            raise ValueError("Electrolyte must be an instance of Electrolyte")
        return value

    def _validate_percentage(self, value: float) -> float:
        if not (0 <= value <= 100):
            raise ValueError("Percentage must be between 0 and 100")
        return value

    @property
    def positive_terminal(self) -> Terminal:
        return self._positive_terminal
    
    @property
    def negative_terminal(self) -> Terminal:
        return self._negative_terminal

    @property
    def electrolyte_overfill(self) -> float:
        return self._electrolyte_overfill * 100

    @property
    def reversible_capacity(self) -> float:
        return self._reversible_capacity
    
    @property
    def irreversible_capacity(self) -> float:
        return self._irreversible_capacity

    @property
    def electrolyte(self) -> Electrolyte:
        return self._electrolyte
    
    @property
    def voltage_upper_cut_off(self) -> float:
        return self._voltage_upper_cut_off
    
    @property
    def voltage_lower_cut_off(self) -> float:
        return self._voltage_lower_cut_off
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return self._name
    
    def __repr__(self) -> str:
        return self.__str__()
    

class PouchCell(Cell):
    def __init__(self,
                 pouch: Pouch,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 voltage_upper_cut_off: float,
                 voltage_lower_cut_off: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 name: str = 'Pouch cell'):
        """
        Class to represent a pouch cell.

        :param pouch: Pouch used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param voltage_upper_cut_off: Upper cut-off voltage of the cell
        :param voltage_lower_cut_off: Lower cut-off voltage of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param name: Name of the cell
        """
        super().__init__(electrolyte=electrolyte, 
                         electrolyte_overfill=electrolyte_overfill, 
                         voltage_upper_cut_off=voltage_upper_cut_off, 
                         voltage_lower_cut_off=voltage_lower_cut_off, 
                         reversible_capacity=reversible_capacity, 
                         irreversible_capacity=irreversible_capacity,
                         positive_terminal=positive_terminal,
                         negative_terminal=negative_terminal,
                         name=name)
        
        self._pouch = self._validate_pouch(pouch)

    def _validate_pouch(self, value: Pouch) -> Pouch:
        if not isinstance(value, Pouch):
            raise ValueError("Pouch must be an instance of Pouch")
        return value

    @property
    def pouch(self) -> Pouch:
        return self._pouch
    

class StackedPouchCell(PouchCell):

    def __init__(self,
                 stack: Stack,
                 pouch: Pouch,
                 electrolyte: Electrolyte,
                 electrolyte_overfill: float,
                 voltage_upper_cut_off: float,
                 voltage_lower_cut_off: float,
                 reversible_capacity: float,
                 irreversible_capacity: float,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 name: str = None):
        """
        A class that represents a stacked pouch cell.

        :param stack: Stack within the cell
        :param pouch: Pouch used in the cell
        :param electrolyte: Electrolyte used in the cell
        :param electrolyte_overfill: Overfill of the electrolyte in the cell (%)
        :param voltage_upper_cut_off: Upper cut-off voltage of the cell
        :param voltage_lower_cut_off: Lower cut-off voltage of the cell
        :param reversible_capacity: Reversible capacity of the cell in mAh
        :param irreversible_capacity: Irreversible capacity of the cell in mAh
        :param positive_terminal: Positive terminal of the cell
        :param negative_terminal: Negative terminal of the cell
        :param name: Name of the cell
        """
        super().__init__(pouch=pouch,
                         electrolyte=electrolyte,
                         electrolyte_overfill=electrolyte_overfill,
                         voltage_upper_cut_off=voltage_upper_cut_off,
                         voltage_lower_cut_off=voltage_lower_cut_off,
                         reversible_capacity=reversible_capacity,
                         irreversible_capacity=irreversible_capacity,
                         positive_terminal=positive_terminal,
                         negative_terminal=negative_terminal,
                         name=name)
        
        self._stack = self._validate_stack(stack)

        # calculate pouch properties
        self._pouch._width = self._stack._anode._current_collector._width + 2 * self._pouch._heat_seal_size_sides
        self._pouch._length = self._stack._anode._current_collector._length + self._pouch._heat_seal_size_top
        self._pouch._area = self._pouch._width * self._pouch._length
        self._pouch._mass = 2 * self._pouch._area * self._pouch._laminate._areal_mass
        self._pouch._cost = self._pouch._area * self._pouch._laminate._areal_cost

        # calculate electrolyte quantities
        self._electrolyte._volume = self._stack._pore_volume * (1 + self._electrolyte_overfill)
        self._electrolyte._mass = self._electrolyte._volume * self._electrolyte._density
        self._electrolyte._cost = (self._electrolyte._mass) * self._electrolyte._specific_cost  

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
        self._effective_areal_capacity = self._reversible_capacity / self._stack.active_geometric_area   

        # calculate cost of the cell
        self._cost_breakdown = {self._stack: self._stack._cost,
                                self._pouch: self._pouch._cost,
                                self._electrolyte: self._electrolyte._cost,
                                self._positive_terminal: self._positive_terminal._cost,
                                self._negative_terminal: self._negative_terminal._cost}

        self._cost = sum(self._cost_breakdown.values())

    def _validate_stack(self, value: Stack) -> Stack:
        if not isinstance(value, Stack):
            raise ValueError("Stack must be an instance of Stack")
        return value

    @property
    def cost_breakdown(self) -> dict:
        return {item: round(value, 3) for item, value in self._cost_breakdown.items()}
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)

    @property
    def stack(self) -> Stack:
        return self._stack

    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def mass_breakdown(self) -> dict:
        return {item: round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}
    
    @property
    def thickness(self) -> float:
        return round(self._thickness * M_TO_MM, 2)
    
    @property
    def volume(self) -> float:
        return round(self._volume * M_TO_CM**3, 2)
    
    @property
    def effective_areal_capacity(self) -> float:
        return round(self._effective_areal_capacity, 2)
