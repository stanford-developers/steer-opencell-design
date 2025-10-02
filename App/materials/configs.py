from typing import Type, List, Optional
from dataclasses import dataclass
from enum import Enum

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial,
    InsulationMaterial,
    SeparatorMaterial,
)

from steer_materials.CellMaterials.Electrode import (
    Binder,
    ConductiveAdditive,
    CathodeMaterial,
    AnodeMaterial,
)

from steer_core.Apps.Components.MaterialSelectors import (
    MaterialSelector,
    ActiveMaterialSelector,
)


# Define MaterialType enum
class MaterialType(Enum):
    CATHODE_CURRENT_COLLECTOR = "cathode_current_collector"
    CATHODE_CURRENT_COLLECTOR_TAB = "cathode_current_collector_tab"
    CATHODE_INSULATION = "cathode_insulation"
    ANODE_CURRENT_COLLECTOR = "anode_current_collector"
    ANODE_CURRENT_COLLECTOR_TAB = "anode_current_collector_tab"
    ANODE_INSULATION = "anode_insulation"
    BINDER = "binder"
    CONDUCTIVE_ADDITIVE = "conductive_additive"
    CATHODE_ACTIVE_MATERIAL = "cathode_active_material"
    ANODE_ACTIVE_MATERIAL = "anode_active_material"
    SEPARATOR_MATERIAL = "separator_material"


@dataclass
class MaterialConfig:
    """Configuration for different material types."""
    material_type: Type
    cell_path: Optional[List[str]]
    parameter_list: List[str]
    dropdown_menu: Optional[bool] = None
    custom_selector: Optional[Type[MaterialSelector]] = None
    selector_div_width: str = "calc(100%)"


# Define configurations
MATERIAL_CONFIGS = {
    MaterialType.CATHODE_CURRENT_COLLECTOR: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        cell_path=["cathode", "current_collector", "material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.CATHODE_INSULATION: MaterialConfig(
        material_type=InsulationMaterial,
        cell_path=["cathode", "insulation_material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.CATHODE_CURRENT_COLLECTOR_TAB: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        cell_path=["cathode", "current_collector", "weld_tab", "material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.ANODE_CURRENT_COLLECTOR: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        cell_path=["anode", "current_collector", "material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.ANODE_INSULATION: MaterialConfig(
        material_type=InsulationMaterial,
        cell_path=["anode", "insulation_material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.ANODE_CURRENT_COLLECTOR_TAB: MaterialConfig(
        material_type=CurrentCollectorMaterial,
        cell_path=["anode", "current_collector", "weld_tab", "material"],
        parameter_list=[
            "density",
            "specific_cost",
        ],
        dropdown_menu=True,
    ),
    MaterialType.BINDER: MaterialConfig(
        material_type=Binder,
        cell_path=None,
        parameter_list=[
            "density",
            "specific_cost",
        ],
        custom_selector=MaterialSelector,
        selector_div_width="calc(80%)",
    ),
    MaterialType.CONDUCTIVE_ADDITIVE: MaterialConfig(
        material_type=ConductiveAdditive,
        cell_path=None,
        parameter_list=[
            "density",
            "specific_cost",
        ],
        custom_selector=MaterialSelector,
        selector_div_width="calc(80%)",
    ),
    MaterialType.CATHODE_ACTIVE_MATERIAL: MaterialConfig(
        material_type=CathodeMaterial,
        cell_path=None,
        parameter_list=[
            "density",
            "specific_cost",
            "reversible_capacity_scaling",
            "irreversible_capacity_scaling",
        ],
        custom_selector=ActiveMaterialSelector,
    ),
    MaterialType.ANODE_ACTIVE_MATERIAL: MaterialConfig(
        material_type=AnodeMaterial,
        cell_path=None,
        parameter_list=[
            "density",
            "specific_cost",
            "reversible_capacity_scaling",
            "irreversible_capacity_scaling",
        ],
        custom_selector=ActiveMaterialSelector,
    ),
    MaterialType.SEPARATOR_MATERIAL: MaterialConfig(
        material_type=SeparatorMaterial,
        cell_path=["separator", "material"],
        parameter_list=[
            "density",
            "specific_cost",
            "porosity",
        ],
        dropdown_menu=True,
    ),
}


