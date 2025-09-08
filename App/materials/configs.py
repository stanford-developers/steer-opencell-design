from typing import Type, List, Optional
from dataclasses import dataclass

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial,
    InsulationMaterial
)

from steer_materials.CellMaterials.Electrode import (
    Binder,
    ConductiveAdditive,
    CathodeMaterial,
    AnodeMaterial
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

from steer_core.Apps.Components.MaterialSelectors import (
    MaterialSelector,
    ActiveMaterialSelector
)

from App.database_service import (
    BINDER_MATERIALS,
    CONDUCTIVE_ADDITIVE_MATERIALS,
)

@dataclass
class MaterialConfig:
    """Configuration for different current collector types."""
    material_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    dropdown_menu: Optional[bool] = None
    cell_path: Optional[List[str]] = None
    custom_selector: Optional[Type[MaterialSelector]] = None
    selector_div_width: str = 'calc(100%)'


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
        selector_div_width='calc(80%)',
        custom_selector=MaterialSelector,
    ),
    MaterialType.CONDUCTIVE_ADDITIVE: MaterialConfig(
        material_type=ConductiveAdditive,
        parameter_list=REGULAR_PARAMETER_LIST,
        settable_parameters=REGULAR_SETTABLE_PARAMETERS,
        selector_div_width='calc(80%)',
        custom_selector=MaterialSelector,
    ),
    MaterialType.CATHODE_ACTIVE_MATERIAL: MaterialConfig(
        material_type=CathodeMaterial,
        parameter_list=ACTIVE_PARAMETER_LIST,
        settable_parameters=ACTIVE_SETTABLE_PARAMETERS,
        custom_selector=ActiveMaterialSelector,
    ),
    MaterialType.ANODE_ACTIVE_MATERIAL: MaterialConfig(
        material_type=AnodeMaterial,
        parameter_list=ACTIVE_PARAMETER_LIST,
        settable_parameters=ACTIVE_SETTABLE_PARAMETERS,
        custom_selector=ActiveMaterialSelector,
    ),
}



