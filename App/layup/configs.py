from typing import Type, List
from dataclasses import dataclass
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer, _Layup
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

    layup_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]


# Define configurations
LAYUP_CONFIGS = {
    LayupType.LAMINATE: LayupConfig(
        layup_type=Laminate,
        parameter_list=LAMINATE_PARAMETER_LIST,
        settable_parameters=LAMINATE_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.MONOLAYER: LayupConfig(
        layup_type=MonoLayer,
        parameter_list=MONOLAYER_PARAMETER_LIST,
        settable_parameters=MONOLAYER_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.ZFOLDMONOLAYER: LayupConfig(
        layup_type=ZFoldMonoLayer,
        parameter_list=ZFOLDMONOLAYER_PARAMETER_LIST,
        settable_parameters=ZFOLDMONOLAYER_SETTABLE_PARAMETERS,
        cell_path=[],
    ),
    LayupType.GENERIC: LayupConfig(
        layup_type=_Layup,
        parameter_list=[],
        settable_parameters=[],
        cell_path=[],
    ),
}
