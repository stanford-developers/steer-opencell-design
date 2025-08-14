from typing import Type, List, Optional
from dataclasses import dataclass
from steer_opencell_design.Components.Electrodes import Cathode, Anode, _Electrode
from general.enumerated_classes import ElectrodeType

from electrodes.lists import (
    ELECTRODE_PARAMETER_LIST,
    ELECTRODE_SETTABLE_PARAMETERS
)


@dataclass
class ElectrodeConfig:
    """Configuration for different current collector types."""
    electrode_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]


# Define configurations
ELECTRODE_CONFIGS = {
    ElectrodeType.CATHODE: ElectrodeConfig(
        electrode_type=Cathode,
        parameter_list=ELECTRODE_PARAMETER_LIST,
        settable_parameters=ELECTRODE_SETTABLE_PARAMETERS,
        cell_path=[]
    ),
    ElectrodeType.ANODE: ElectrodeConfig(
        electrode_type=Anode,
        parameter_list=ELECTRODE_PARAMETER_LIST,
        settable_parameters=ELECTRODE_SETTABLE_PARAMETERS,
        cell_path=[]
    ),
}

