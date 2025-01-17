import numpy as np
from SteerEnergyStorage.Materials.other import Seal
from SteerEnergyStorage.Materials.other import Laminate


class Pouch():

    def __init__(self,
                 seal_1: Seal,
                 seal_2: Seal,
                 seal_3: Seal,
                 seal_4: Seal,
                 length: float,
                 width: float,
                 laminate: Laminate
                 ):
        """
        Class representing a pouch used for a pouch cell
        :param seal_1: Seal: first seal of the pouch
        :param seal_2: Seal: second seal of the pouch
        :param seal_3: Seal: third seal of the pouch
        :param seal_4: Seal: fourth seal of the pouch
        :param length: float: length of the pouch in cm
        :param width: float: width of the pouch in cm
        :param laminate: Laminate: laminate used in the pouch
        """
        self._seal_1 = seal_1
        self._seal_2 = seal_2
        self._seal_3 = seal_3
        self._seal_4 = seal_4
        self._length = length
        self._width = width
        self._laminate = laminate

        self._total_length = self._length + self._seal_1._length + self._seal_4._length
        self._total_width = self._width + self._seal_2._length + self._seal_3._length
        self._area = self._total_length/10 * self._total_width/10
        self._mass = (2 * self._area * self._laminate._areal_mass)/1000
        self._cost = self._area/10000 * self._laminate._specific_cost

    @property
    def length(self):
        return np.round(self._length, 2)
    
    @property
    def width(self):
        return np.round(self._width, 2)
    
    @property
    def laminate(self):
        return self._laminate
    
    @property
    def seal_1(self):
        return self._seal_1
    
    @property
    def seal_2(self):
        return self._seal_2
    
    @property
    def seal_3(self):
        return self._seal_3
    
    def __str__(self):
        return f"Pouch with a length of {self.length} cm and a width of {self.width} cm"
    
    def __repr__(self):
        return f"Pouch with a length of {self.length} cm and a width of {self.width} cm"
        