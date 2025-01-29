from SteerEnergyStorage.Materials.other import Laminate, Tape

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
