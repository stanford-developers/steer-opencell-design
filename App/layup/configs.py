from typing import Type, List, Optional
from dataclasses import dataclass
from enum import Enum

from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer, _Layup


# Define LayupType enum
class LayupType(Enum):
    LAMINATE = "laminate"
    MONOLAYER = "monolayer"
    ZFOLDMONOLAYER = "zfoldmonolayer"
    GENERIC = "generic"


# Define SeparatorType enum
class SeparatorType(Enum):
    TOP_LAMINATE = "top_laminate"
    BOTTOM_LAMINATE = "bottom_laminate"
    TOP_MONOLAYER = "monolayer"
    BOTTOM_MONOLAYER = "bottom_monolayer"
    ZFOLDMONOLAYER = "zfoldmonolayer"
    GENERIC = "generic"


@dataclass
class LayupConfig:
    """Configuration for different layup types."""
    layup_type: Type
    cell_path: List[str]
    parameter_list: List[str]
    radioitem_parameters: Optional[List[str]] = None


# Define layup configurations
LAYUP_CONFIGS = {
    LayupType.LAMINATE: LayupConfig(
        layup_type=Laminate,
        cell_path=[],
        parameter_list=[
            "anode_overhang_left",
            "anode_overhang_right",
            "anode_overhang_top",
            "anode_overhang_bottom",
            "top_separator_overhang_left",
            "top_separator_overhang_right",
            "top_separator_overhang_top",
            "top_separator_overhang_bottom",
            "bottom_separator_overhang_left",
            "bottom_separator_overhang_right",
            "bottom_separator_overhang_top",
            "bottom_separator_overhang_bottom",
        ],
    ),
    LayupType.MONOLAYER: LayupConfig(
        layup_type=MonoLayer,
        cell_path=[],
        parameter_list=[
            "anode_overhang_left",
            "anode_overhang_right",
            "anode_overhang_top",
            "anode_overhang_bottom",
            "top_separator_overhang_left",
            "top_separator_overhang_right",
            "top_separator_overhang_top",
            "top_separator_overhang_bottom",
            "bottom_separator_overhang_left",
            "bottom_separator_overhang_right",
            "bottom_separator_overhang_top",
            "bottom_separator_overhang_bottom",
        ],
    ),
    LayupType.ZFOLDMONOLAYER: LayupConfig(
        layup_type=ZFoldMonoLayer,
        cell_path=[],
        parameter_list=[
            "anode_overhang_left",
            "anode_overhang_right",
            "anode_overhang_top",
            "anode_overhang_bottom",
            "separator_overhang_top",
            "separator_overhang_bottom",
        ],
    ),
    LayupType.GENERIC: LayupConfig(
        layup_type=_Layup,
        cell_path=[],
        parameter_list=[
            "np_ratio",
        ],
        radioitem_parameters=[
            "overhang_control_mode",
            "np_ratio_control_mode",
        ],
    ),
}


@dataclass
class SeparatorConfig:
    """Configuration for different separator types."""
    cell_path: List[str]
    parameter_list: List[str]

# Define separator configurations
SEPARATOR_CONFIGS = {
    SeparatorType.TOP_LAMINATE: SeparatorConfig(
        cell_path=["top_separator"],
        parameter_list=[
            "length",
            "width",
            "thickness",
        ],
    ),
    SeparatorType.BOTTOM_LAMINATE: SeparatorConfig(
        cell_path=["bottom_separator"],
        parameter_list=[
            "length",
            "width",
            "thickness",
        ],
    ),
    SeparatorType.TOP_MONOLAYER: SeparatorConfig(
        cell_path=["top_separator"],
        parameter_list=[
            "length",
            "width",
            "thickness",
        ],
    ),
    SeparatorType.BOTTOM_MONOLAYER: SeparatorConfig(
        cell_path=["bottom_separator"],
        parameter_list=[
            "length",
            "width",
            "thickness",
        ],
    ),
    SeparatorType.ZFOLDMONOLAYER: SeparatorConfig(
        cell_path=["separator"],
        parameter_list=[
            "thickness",
            "width",
        ],
    ),
    SeparatorType.GENERIC: SeparatorConfig(
        cell_path=["generic"],
        parameter_list=[],
    ),
}


