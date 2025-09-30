from typing import Type, List
from dataclasses import dataclass
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer, _Layup
from App.general.enumerated_classes import LayupType, SeparatorType

from App.layup.lists import (
    LAMINATE_PARAMETER_LIST,
    LAMINATE_SETTABLE_PARAMETERS,
    LAMINATE_SEPARATOR_PARAMETERS,
    LAMINATE_SEPARATOR_SETTABLE_PARAMETERS,
    MONOLAYER_PARAMETER_LIST,
    MONOLAYER_SETTABLE_PARAMETERS,
    MONOLAYER_SEPARATOR_PARAMETERS,
    MONOLAYER_SEPARATOR_SETTABLE_PARAMETERS,
    ZFOLDMONOLAYER_PARAMETER_LIST,
    ZFOLDMONOLAYER_SETTABLE_PARAMETERS,
    ZFOLDMONOLAYER_SEPARATOR_PARAMETERS,
    ZFOLDMONOLAYER_SEPARATOR_SETTABLE_PARAMETERS,
    LAYUP_MODES_LIST,
    GENERIC_PARAMETER_LIST,
    GENERIC_SETTABLE_PARAMETERS,
)


@dataclass
class LayupConfig:
    """Configuration for different current collector types."""
    layup_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    radioitem_parameters: List[str]
    cell_path: List[str]


# Define configurations
LAYUP_CONFIGS = {
    LayupType.LAMINATE: LayupConfig(
        layup_type=Laminate,
        parameter_list=LAMINATE_PARAMETER_LIST,
        settable_parameters=LAMINATE_SETTABLE_PARAMETERS,
        radioitem_parameters=[],
        cell_path=[],
    ),
    LayupType.MONOLAYER: LayupConfig(
        layup_type=MonoLayer,
        parameter_list=MONOLAYER_PARAMETER_LIST,
        settable_parameters=MONOLAYER_SETTABLE_PARAMETERS,
        radioitem_parameters=[],
        cell_path=[],
    ),
    LayupType.ZFOLDMONOLAYER: LayupConfig(
        layup_type=ZFoldMonoLayer,
        parameter_list=ZFOLDMONOLAYER_PARAMETER_LIST,
        settable_parameters=ZFOLDMONOLAYER_SETTABLE_PARAMETERS,
        radioitem_parameters=[],
        cell_path=[],
    ),
    LayupType.GENERIC: LayupConfig(
        layup_type=_Layup,
        parameter_list=GENERIC_PARAMETER_LIST,
        settable_parameters=GENERIC_SETTABLE_PARAMETERS,
        radioitem_parameters=LAYUP_MODES_LIST,
        cell_path=[],
    ),
}


@dataclass
class SeparatorConfig:
    """Configuration for different separator types."""
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]

SEPARATOR_CONFIGS = {
    SeparatorType.TOP_LAMINATE: SeparatorConfig(
        parameter_list=LAMINATE_SEPARATOR_PARAMETERS,
        settable_parameters=LAMINATE_SEPARATOR_SETTABLE_PARAMETERS,
        cell_path=["top_separator"],
    ),
    SeparatorType.BOTTOM_LAMINATE: SeparatorConfig(
        parameter_list=LAMINATE_SEPARATOR_PARAMETERS,
        settable_parameters=LAMINATE_SEPARATOR_SETTABLE_PARAMETERS,
        cell_path=["bottom_separator"],
    ),
    SeparatorType.TOP_MONOLAYER: SeparatorConfig(
        parameter_list=MONOLAYER_SEPARATOR_PARAMETERS,
        settable_parameters=MONOLAYER_SEPARATOR_SETTABLE_PARAMETERS,
        cell_path=["top_separator"],
    ),
    SeparatorType.BOTTOM_MONOLAYER: SeparatorConfig(
        parameter_list=MONOLAYER_SEPARATOR_PARAMETERS,
        settable_parameters=MONOLAYER_SEPARATOR_SETTABLE_PARAMETERS,
        cell_path=["bottom_separator"],
    ),
    SeparatorType.ZFOLDMONOLAYER: SeparatorConfig(
        parameter_list=ZFOLDMONOLAYER_SEPARATOR_PARAMETERS,
        settable_parameters=ZFOLDMONOLAYER_SEPARATOR_SETTABLE_PARAMETERS,
        cell_path=["separator"],
    ),
    SeparatorType.GENERIC: SeparatorConfig(
        parameter_list=[],
        settable_parameters=[],
        cell_path=["generic"],
    ),
}


