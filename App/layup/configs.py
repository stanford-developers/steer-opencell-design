from typing import Type, List
from dataclasses import dataclass
from steer_opencell_design.Components.Electrodes import Cathode, Anode, _Electrode
from App.general.enumerated_classes import LayupType

from App.layup.lists import (
    LAMINATE_PARAMETER_LIST,
    LAMINATE_SETTABLE_PARAMETERS,
    MONOLAYER_PARAMETER_LIST,
    MONOLAYER_SETTABLE_PARAMETERS,
    ZFOLDMONOLAYER_PARAMETER_LIST,
    ZFOLDMONOLAYER_SETTABLE_PARAMETERS,
)


@dataclass
class LayupConfig:
    """Configuration for different current collector types."""
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]


# Define configurations
LAYUP_CONFIGS = {
    LayupType.LAMINATE: LayupConfig(
        parameter_list=LAMINATE_PARAMETER_LIST,
        settable_parameters=LAMINATE_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.MONOLAYER: LayupConfig(
        parameter_list=MONOLAYER_PARAMETER_LIST,
        settable_parameters=MONOLAYER_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.ZFOLDMONOLAYER: LayupConfig(
        parameter_list=ZFOLDMONOLAYER_PARAMETER_LIST,
        settable_parameters=ZFOLDMONOLAYER_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.GENERIC: LayupConfig(
        parameter_list=[],
        settable_parameters=[],
        cell_path=[],
    ),
}



