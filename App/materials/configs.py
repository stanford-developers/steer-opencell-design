from typing import Type, List, Optional
from dataclasses import dataclass

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial,
    InsulationMaterial
)

from general.enumerated_classes import (
    MaterialType
)

from materials.lists import (
    REGULAR_PARAMETER_LIST,
    REGULAR_SETTABLE_PARAMETERS
)


@dataclass
class MaterialConfig:
    """Configuration for different current collector types."""
    material_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    dropdown_menu: Optional[bool]
    cell_path: List[str]


# Define configurations
MATERIAL_CONFIGS = {
    MaterialType.CATHODE_CURRENT_COLLECTOR: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        cell_path=['current_collector', 'material'],
        dropdown_menu=True
    ),
    MaterialType.CATHODE_INSULATION: MaterialConfig(
        material_type=InsulationMaterial,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        cell_path=['insulation_material'],
        dropdown_menu=True
    )
}

