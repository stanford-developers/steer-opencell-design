from typing import Type, List, Optional
from dataclasses import dataclass

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial,
    InsulationMaterial
)

from steer_materials.CellMaterials.Electrode import (
    Binder,
    ConductiveAdditive,
    _ActiveMaterial
)

from App.general.enumerated_classes import (
    MaterialType
)

from App.materials.lists import (
    REGULAR_PARAMETER_LIST,
    REGULAR_SETTABLE_PARAMETERS,
    ACTIVE_PARAMETER_LIST,
    ACTIVE_SETTABLE_PARAMETERS
)


@dataclass
class MaterialConfig:
    """Configuration for different current collector types."""
    material_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    dropdown_menu: Optional[bool] = None
    cell_path: Optional[List[str]] = None
    material_selector: Optional[bool] = None
    active_material_selector: Optional[bool] = None


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
    ),
    MaterialType.CATHODE_CURRENT_COLLECTOR_TAB: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        cell_path=['current_collector', 'weld_tab', 'material'],
        dropdown_menu=True
    ),
    MaterialType.BINDER: MaterialConfig(
        material_type=Binder,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        material_selector=True
    ),
    MaterialType.CONDUCTIVE_ADDITIVE: MaterialConfig(
        material_type=ConductiveAdditive,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        material_selector=True
    ),
    MaterialType.ACTIVE_MATERIAL: MaterialConfig(
        material_type=_ActiveMaterial,
        parameter_list=ACTIVE_PARAMETER_LIST,
        settable_parameters=ACTIVE_SETTABLE_PARAMETERS,
        active_material_selector=True
    ),
}

