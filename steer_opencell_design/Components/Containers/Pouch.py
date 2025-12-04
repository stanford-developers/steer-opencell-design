from typing import Tuple

from steer_opencell_design.Components.Containers.Base import _Container

class PouchTerminal:
    pass


class PouchEncapsulation(_Container):

    def __init__(
            self,
            cathode_terminal: PouchTerminal,
            anode_terminal: PouchTerminal,
            name: str = "Pouch Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):

        self._update_properties = False
        
        self.cathode_terminal = cathode_terminal
        self.anode_terminal = anode_terminal
        self.name = name
        self.datum = datum

        self._update_properties = True
        self._calculate_all_properties()

