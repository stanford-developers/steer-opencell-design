from SteerEnergyStorage.Materials.other import Laminate, Tape
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Formulations.Stacks import Stack

CM_TO_M = 0.01
M_TO_CM = 100
G_TO_KG = 0.001
KG_TO_G = 1000
MM_TO_M = 0.001
M_TO_MM = 1000

class Pouch:

    def __init__(self,
                 heat_seal_size_sides: float,
                 heat_seal_size_top: float,
                 laminate: Laminate,
                 tape: Tape,
                 name: str = 'Pouch'):
        """
        Class representing a pouch used for a pouch cell.

        :param heat_seal_size_sides: float: size of the heat seal on the sides of the pouch in mm
        :param heat_seal_size_top: float: size of the heat seal on the top of the pouch in mm
        :param laminate: Laminate: laminate used in the pouch
        :param tape: Tape: tape used in the pouch
        :param name: str: name of the pouch
        """
        self._heat_seal_size_sides = heat_seal_size_sides * MM_TO_M
        self._heat_seal_size_top = heat_seal_size_top * MM_TO_M
        self._laminate = laminate
        self._tape = tape
        self._name = name

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
        self._cost = cost
        self._mass = mass * G_TO_KG
        self._internal_width = internal_width * CM_TO_M
        self._internal_length = internal_length * CM_TO_M
        self._internal_height = internal_height * CM_TO_M
        self._wall_thickness = wall_thickness * MM_TO_M
        self._name = name

        self._external_width = self._internal_width + 2 * self._wall_thickness
        self._external_length = self._internal_length + 2 * self._wall_thickness
        self._external_height = self._internal_height + 2 * self._wall_thickness

        self._internal_volume = self._internal_width * self._internal_length * self._internal_height

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
        self._cost = cost
        self._mass = mass * G_TO_KG
        self._external_width = external_width * CM_TO_M
        self._internal_width = internal_width * CM_TO_M
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
        self._shell = shell
        self._lid = lid
        self._name = name

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

    def get_optimized_stack(self, 
                            anode: Anode,
                            cathode: Cathode,
                            separator: Separator,
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
        
        stack = Stack(anode=anode, cathode=cathode, separator=separator, n_stacks=1, **kwargs)

        if stack._length > self._internal_length:
            raise ValueError("Stack length is too large for the prismatic case. Reduce your current collector lengths.")
        if stack._width > self._internal_width:
            raise ValueError("Stack width is too large for the prismatic case. Reduce your current collector widths.")
        if stack._thickness > self._internal_height:
            raise ValueError("Stack is too thick for the prismatic case even with one layer. Check your inputs.")
        
        while stack._thickness < self._internal_height:
            stack.n_stacks += 1
        stack.n_stacks -= 1

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
