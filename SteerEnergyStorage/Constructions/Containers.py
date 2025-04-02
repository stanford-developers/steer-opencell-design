from SteerEnergyStorage.Materials.other import Laminate, Tape, Terminal
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import Stack

from copy import deepcopy

CM_TO_M = 0.01
M_TO_CM = 100
G_TO_KG = 0.001
KG_TO_G = 1000
MM_TO_M = 0.001
M_TO_MM = 1000

class Pouch:

    def __init__(self,
                 positive_terminal: Terminal,
                 negative_terminal: Terminal,
                 heat_seal_size_sides: float,
                 heat_seal_size_top: float,
                 laminate: Laminate,
                 tape: Tape,
                 name: str = 'Pouch'):
        """
        Class representing a pouch used for a pouch cell.

        :param positive_terminal: Terminal: positive terminal of the pouch
        :param negative_terminal: Terminal: negative terminal of the pouch
        :param heat_seal_size_sides: float: size of the heat seal on the sides of the pouch in mm
        :param heat_seal_size_top: float: size of the heat seal on the top of the pouch in mm
        :param laminate: Laminate: laminate used in the pouch
        :param tape: Tape: tape used in the pouch
        :param name: str: name of the pouch
        """
        self._check_positive_terminal(positive_terminal)
        self._check_negative_terminal(negative_terminal)
        self._check_heat_seal_size_sides(heat_seal_size_sides)
        self._check_heat_seal_size_top(heat_seal_size_top)
        self._check_laminate(laminate)
        self._check_tape(tape)
        self._check_name(name)

    def _check_positive_terminal(self, positive_terminal: Terminal):

        if not isinstance(positive_terminal, Terminal):
            raise TypeError("Positive terminal must be a Terminal")
        
        self._positive_terminal = deepcopy(positive_terminal)

    def _check_negative_terminal(self, negative_terminal: Terminal):

        if not isinstance(negative_terminal, Terminal):
            raise TypeError("Negative terminal must be a Terminal")
        
        self._negative_terminal = deepcopy(negative_terminal)

    def _check_heat_seal_size_sides(self, heat_seal_size_sides: float):

        if not isinstance(heat_seal_size_sides, (int, float)):
            raise TypeError("Heat seal size sides must be a number")

        if heat_seal_size_sides <= 0:
            raise ValueError("Heat seal size sides must be positive")
        
        self._heat_seal_size_sides = heat_seal_size_sides * MM_TO_M

    def _check_heat_seal_size_top(self, heat_seal_size_top: float):

        if not isinstance(heat_seal_size_top, (int, float)):
            raise TypeError("Heat seal size top must be a number")

        if heat_seal_size_top <= 0:
            raise ValueError("Heat seal size top must be positive")
        
        self._heat_seal_size_top = heat_seal_size_top * MM_TO_M

    def _check_laminate(self, laminate: Laminate):

        if not isinstance(laminate, Laminate):
            raise TypeError("Laminate must be a Laminate")
        
        self._laminate = laminate

    def _check_tape(self, tape: Tape):

        if not isinstance(tape, Tape):
            raise TypeError("Tape must be a Tape")
        
        self._tape = tape

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")
        
        self._name = name

    def _calculate_properties(self, stack: Stack):
        self._width = stack._width + 2 * self._heat_seal_size_sides
        self._length = stack._length + self._heat_seal_size_top
        self._area = self._width * self._length
        self._mass = self._area * self._laminate._areal_mass * 2 + self._positive_terminal._mass + self._negative_terminal._mass
        self._cost = self._area * self._laminate._areal_cost * 2 + self._positive_terminal._cost + self._negative_terminal._cost

    @property
    def name(self) -> str:
        return self._name

    @property
    def area(self) -> float:
        if hasattr(self, '_area'):
            return round(self._area * M_TO_CM**2, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")
    
    @property
    def mass(self) -> float:
        if hasattr(self, '_mass'):
            return round(self._mass * KG_TO_G, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its mass")
    
    @property
    def cost(self) -> float:
        if hasattr(self, '_cost'):
            return round(self._cost, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its cost")
    
    @property
    def length(self) -> float:
        if hasattr(self, '_length'):
            return round(self._length * M_TO_CM, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")
    
    @property
    def width(self) -> float:
        if hasattr(self, '_width'):
            return round(self._width * M_TO_CM, 2)
        else:
            raise AttributeError("The pouch needs to be used in a pouch cell to calculate its dimensions")
    
    @property
    def tape(self) -> Tape:
        return self._tape
    
    @property
    def laminate(self) -> Laminate:
        return self._laminate
    
    @property
    def heat_seal_size_sides(self) -> float:
        return round(self._heat_seal_size_sides * M_TO_MM, 2)
    
    @property
    def heat_seal_size_top(self) -> float:
        return round(self._heat_seal_size_top * M_TO_MM, 2)
    
    @property
    def positive_terminal(self) -> Terminal:
        return self._positive_terminal
    
    @property
    def negative_terminal(self) -> Terminal:
        return self._negative_terminal

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()
    

class CylindricalShell:

    def __init__(self,
                 cost: float,
                 mass: float,
                 internal_radius: float,
                 length: float,
                 wall_thickness: float,
                 name: str = 'Cylindrical Shell'):
        """
        Class representing a shell used for a cylindrical cell.

        :param cost: float: cost of the shell in $
        :param mass: float: mass of the shell in g
        :param internal_radius: float: internal radius of the shell in cm
        :param length: float: internal length of the shell in cm
        :param wall_thickness: float: thickness of the shell wall in mm
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_internal_radius(internal_radius)
        self._check_length(length)
        self._check_wall_thickness(wall_thickness)
        self._check_name(name)
        self._calculate_properties()

    def _check_cost(self, cost: float):

        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")
        
        self._cost = cost

    def _check_mass(self, mass: float):

        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")
        
        self._mass = mass * G_TO_KG

    def _check_internal_radius(self, internal_radius: float):

        if not isinstance(internal_radius, (int, float)):
            raise TypeError("Internal radius must be a number")

        if internal_radius <= 0:
            raise ValueError("Internal radius must be positive")
        
        self._internal_radius = internal_radius * CM_TO_M

    def _check_length(self, length: float):

        if not isinstance(length, (int, float)):
            raise TypeError("Internal length must be a number")

        if length <= 0:
            raise ValueError("Internal length must be positive")
        
        self._length = length * CM_TO_M

    def _check_wall_thickness(self, wall_thickness: float):

        if not isinstance(wall_thickness, (int, float)):
            raise TypeError("Wall thickness must be a number")

        if wall_thickness <= 0:
            raise ValueError("Wall thickness must be positive")
        
        self._wall_thickness = wall_thickness * MM_TO_M

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")
        
        self._name = name

    def _calculate_properties(self):
        self._external_radius = self._internal_radius + self._wall_thickness

    @property
    def external_radius(self) -> float:
        return round(self._external_radius * M_TO_CM, 2)
    
    @property
    def external_length(self) -> float:
        return round(self._internal_length * M_TO_CM, 2)
    
    @property
    def internal_volume(self) -> float:
        return round(3.14 * (self._internal_radius**2) * self._internal_length * M_TO_CM**3, 2)
    
    @property
    def internal_radius(self) -> float:
        return round(self._internal_radius * M_TO_CM, 2)
    
    @property
    def wall_thickness(self) -> float:
        return round(self._wall_thickness * M_TO_MM, 2)
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self):
        return self.__str__()


class PrismaticShell:

    def __init__(self,
                 cost: float,
                 mass: float,
                 internal_width: float,
                 internal_length: float,
                 internal_height: float,
                 wall_thickness: float,
                 name: str = 'Prismatic Shell'):
        """
        Class representing a shell used for a prismatic cell.

        :param cost: float: cost of the shell in $
        :param mass: float: mass of the shell in g
        :param internal_width: float: internal width of the shell in cm
        :param internal_length: float: internal length of the shell in cm
        :param wall_thickness: float: thickness of the shell wall in mm
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_internal_width(internal_width)
        self._check_internal_length(internal_length)
        self._check_internal_height(internal_height)
        self._check_wall_thickness(wall_thickness)
        self._check_name(name)
        self._calculate_properties()

    def _calculate_properties(self):
        self._external_width = self._internal_width + 2 * self._wall_thickness
        self._external_length = self._internal_length + 2 * self._wall_thickness
        self._external_height = self._internal_height + 2 * self._wall_thickness
        self._external_volume = self._external_width * self._external_length * self._external_height
        self._internal_volume = self._internal_width * self._internal_length * self._internal_height

    def _check_cost(self, cost: float):

        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")
        
        self._cost = cost

    def _check_mass(self, mass: float):

        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")
        
        self._mass = mass * G_TO_KG

    def _check_internal_width(self, internal_width: float):

        if not isinstance(internal_width, (int, float)):
            raise TypeError("Internal width must be a number")

        if internal_width <= 0:
            raise ValueError("Internal width must be positive")
        
        self._internal_width = internal_width * CM_TO_M

    def _check_internal_length(self, internal_length: float):

        if not isinstance(internal_length, (int, float)):
            raise TypeError("Internal length must be a number")

        if internal_length <= 0:
            raise ValueError("Internal length must be positive")
        
        self._internal_length = internal_length * CM_TO_M

    def _check_internal_height(self, internal_height: float):

        if not isinstance(internal_height, (int, float)):
            raise TypeError("Internal height must be a number")

        if internal_height <= 0:
            raise ValueError("Internal height must be positive")
        
        self._internal_height = internal_height * CM_TO_M

    def _check_wall_thickness(self, wall_thickness: float):

        if not isinstance(wall_thickness, (int, float)):
            raise TypeError("Wall thickness must be a number")

        if wall_thickness <= 0:
            raise ValueError("Wall thickness must be positive")
        
        self._wall_thickness = wall_thickness * MM_TO_M

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")
        
        self._name = name

    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_CM, 2)
    
    @property
    def external_length(self) -> float:
        return round(self._external_length * M_TO_CM, 2)
    
    @property
    def external_height(self) -> float:
        return round(self._external_height * M_TO_CM, 2)
    
    @property
    def internal_volume(self) -> float:
        return round(self._internal_volume * M_TO_CM**3, 2)
    
    @property
    def internal_volume(self) -> float:
        return round(self._internal_volume * M_TO_CM**3, 2)

    def external_volume(self) -> float:
        return round(self._external_volume * M_TO_CM**3, 2)

    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_CM, 2)
    
    @property
    def internal_length(self) -> float:
        return round(self._internal_length * M_TO_CM, 2)
    
    @property
    def internal_height(self) -> float:
        return round(self._internal_height * M_TO_CM, 2)
    
    @property
    def wall_thickness(self) -> float:
        return round(self._wall_thickness * M_TO_MM, 2)
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self):
        return self.__str__()
        

class PrismaticLid:

    def __init__(self,
                 cost: float,
                 mass: float,
                 internal_width: float,
                 external_width: float,
                 name: str = 'Prismatic Lid'
                 ):
        """
        Class representing a lid used for a prismatic cell.

        :param cost: float: cost of the lid in $
        :param mass: float: mass of the lid in g
        :param height: float: height of the lid in cm
        :param name: str: name of the lid
        """
        self._check_cost(cost)
        self._check_mass(mass)
        self._check_internal_width(internal_width)
        self._check_external_width(external_width)
        self._check_name(name)

    def _check_cost(self, cost: float):

        if not isinstance(cost, (int, float)):
            raise TypeError("Cost must be a number")

        if cost < 0:
            raise ValueError("Cost cannot be negative")
        
        self._cost = cost

    def _check_mass(self, mass: float):

        if not isinstance(mass, (int, float)):
            raise TypeError("Mass must be a number")

        if mass < 0:
            raise ValueError("Mass cannot be negative")
        
        self._mass = mass * G_TO_KG

    def _check_internal_width(self, internal_width: float):

        if not isinstance(internal_width, (int, float)):
            raise TypeError("Internal width must be a number")

        if internal_width <= 0:
            raise ValueError("Internal width must be positive")
        
        self._internal_width = internal_width * CM_TO_M

    def _check_external_width(self, external_width: float):

        if not isinstance(external_width, (int, float)):
            raise TypeError("External width must be a number")

        if external_width <= 0:
            raise ValueError("External width must be positive")
        
        self._external_width = external_width * CM_TO_M

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")
        
        self._name = name

    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_CM, 2)
    
    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_CM, 2)
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self):
        return self.__str__()
    

class PrismaticCase:

    def __init__(self,
                 shell: PrismaticShell,
                 lid: PrismaticLid,
                 name: str = 'Prismatic Case'
                 ):
        """
        Class representing a casing used for a prismatic cell.

        :param shell: PrismaticShell: shell of the case
        :param lid: PrismaticLid: lid of the case
        :param name: str: name of the case
        """
        self._check_shell(shell)
        self._check_lid(lid)
        self._check_name(name)
        self._calculate_properties()

    def _calculate_properties(self):
        self._cost = self._shell._cost + self._lid._cost
        self._mass = self._shell._mass + self._lid._mass
        
        self._internal_width = self._shell._internal_width + self._lid._internal_width
        self._internal_length = self._shell._internal_length
        self._internal_height = self._shell._internal_height
        self._internal_volume = self._internal_height * self._internal_length * self._internal_width

        self._external_width = self._shell._external_width + self._lid._external_width
        self._external_length = self._shell._external_length
        self._external_height = self._shell._external_height
        self._external_volume = self._external_height * self._external_length * self._external_width

    def _check_shell(self, shell: PrismaticShell):

        if not isinstance(shell, PrismaticShell):
            raise TypeError("Shell must be a PrismaticShell")

        self._shell = shell

    def _check_lid(self, lid: PrismaticLid):

        if not isinstance(lid, PrismaticLid):
            raise TypeError("Lid must be a PrismaticLid")

        self._lid = lid

    def _check_name(self, name: str):

        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if len(name) == 0:
            raise ValueError("Name cannot be empty")
        
        self._name = name

    def get_optimized_stack(self, 
                            anode: Anode,
                            cathode: Cathode,
                            separator: Separator,
                            n_stacks: int = 1,
                            **kwargs) -> Stack:
        """
        Function to get the optimized stack for the prismatic case.
        
        :param anode: Anode: anode used in the cell
        :param cathode: Cathode: cathode used in the cell
        :param separator: Separator: separator used in the cell
        :return: tuple: optimized stack
        """
        # Check stack is small enough to fit in the prismatic case
        if anode.current_collector._width > self._internal_width:
            raise ValueError("Anode current collector width is too large for the prismatic case")
        if anode.current_collector._length > self._internal_length:
            raise ValueError("Anode current collector length is too large for the prismatic case")
        
        target_stack_height = self._internal_height / n_stacks
        stack_layers = 2
        stack = Stack(anode=anode, cathode=cathode, separator=separator, n_layers=stack_layers, **kwargs)

        if stack._length > self._internal_length:
            raise ValueError("Stack length is too large for the prismatic case. Reduce your current collector lengths.")
        if stack._width > self._internal_width:
            raise ValueError("Stack width is too large for the prismatic case. Reduce your current collector widths.")
        if stack._thickness > target_stack_height:
            raise ValueError("Stack is too thick for the prismatic case even with one layer. Check your inputs.")
        
        initial_layer_guess = int(target_stack_height // (stack._thickness/2))
        stack = Stack(anode=anode, cathode=cathode, separator=separator, n_layers=initial_layer_guess, **kwargs)

        if stack._thickness > target_stack_height:
            while stack._thickness > target_stack_height:
                initial_layer_guess -= 1
                stack = Stack(anode=anode, cathode=cathode, separator=separator, n_layers=initial_layer_guess, **kwargs)
        elif stack._thickness < target_stack_height:
            while stack._thickness < target_stack_height:
                initial_layer_guess += 1
                stack = Stack(anode=anode, cathode=cathode, separator=separator, n_layers=initial_layer_guess, **kwargs)
            stack = Stack(anode=anode, cathode=cathode, separator=separator, n_layers=initial_layer_guess-1, **kwargs)

        return stack
    
    @property
    def internal_width(self) -> float:
        return round(self._internal_width * M_TO_CM, 2)
    
    @property
    def internal_length(self) -> float:
        return round(self._internal_length * M_TO_CM, 2)
    
    @property
    def internal_height(self) -> float:
        return round(self._internal_height * M_TO_CM, 2)
    
    @property
    def internal_volume(self) -> float:
        return round(self._internal_volume * M_TO_CM**3, 2)
    
    @property
    def external_width(self) -> float:
        return round(self._external_width * M_TO_CM, 2)
    
    @property
    def external_length(self) -> float:
        return round(self._external_length * M_TO_CM, 2)
    
    @property
    def external_height(self) -> float:
        return round(self._external_height * M_TO_CM, 2)
    
    @property
    def external_volume(self) -> float:
        return round(self._external_volume * M_TO_CM**3, 2)

    @property
    def shell(self) -> PrismaticShell:
        return self._shell
    
    @property
    def lid(self) -> PrismaticLid:
        return self._lid
    
    @property
    def cost(self) -> float:
        return round(self._cost, 2)
    
    @property
    def mass(self) -> float:
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def name(self) -> str:
        return self._name
    
    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return self.__str__()
