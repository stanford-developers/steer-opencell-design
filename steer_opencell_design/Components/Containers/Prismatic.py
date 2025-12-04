from steer_opencell_design.Components.Containers.Base import _Container

from typing import Tuple


class PrismaticTerminalConnector:
    pass


class PrismaticLidAssembly:
    pass


class PrismaticCannister:
    pass


class PrismaticEncapsulation(_Container):

    def __init__(
            self,
            cathode_terminal_connector: PrismaticTerminalConnector,
            anode_terminal_connector: PrismaticTerminalConnector,
            lid_assembly: PrismaticLidAssembly,
            cannister: PrismaticCannister,
            name: str = "Prismatic Encapsulation",
            datum: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        ):

        self._update_properties = False
        
        self.cathode_terminal_connector = cathode_terminal_connector
        self.anode_terminal_connector = anode_terminal_connector
        self.lid_assembly = lid_assembly
        self.cannister = cannister
        self.name = name
        self.datum = datum

        self._update_properties = True
        self._calculate_all_properties()

