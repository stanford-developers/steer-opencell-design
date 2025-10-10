from typing import Type, List
from dataclasses import dataclass
from enum import Enum

from steer_opencell_design.Components.Electrodes import Cathode, Anode


# Define ElectrodeType enum
class ElectrodeType(Enum):
    CATHODE = "cathode"
    ANODE = "anode"
    GENERIC = "generic"


@dataclass
class ElectrodeConfig:
    """Configuration for different electrode types."""
    electrode_type: Type
    cell_path: List[str]
    parameter_list: List[str]
    radioitem_parameters: List[str]


# Define configurations
ELECTRODE_CONFIGS = {
    ElectrodeType.CATHODE: ElectrodeConfig(
        electrode_type=Cathode,
        cell_path=["cathode"],
        parameter_list=[
            "insulation_thickness",
            "mass_loading",
            "coating_thickness",
            "calender_density",
            "porosity",
        ],
        radioitem_parameters=[
            "control_mode",
        ],
    ),
    ElectrodeType.ANODE: ElectrodeConfig(
        electrode_type=Anode,
        cell_path=["anode"],
        parameter_list=[
            "insulation_thickness",
            "mass_loading",
            "coating_thickness",
            "calender_density",
            "porosity",
        ],
        radioitem_parameters=[
            "control_mode",
        ],
    ),
}

