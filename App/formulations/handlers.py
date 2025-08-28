from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from dash import no_update

def handle_cell_store_update_material_children(
        formulation, 
        config,
        active_materials
    ):
    
    from App.formulations.callback_helpers import create_material_component

    active_material_children = []
    for i, (active_material, weight_percent) in enumerate(formulation.active_materials.items()):
        active_material_config = MATERIAL_CONFIGS[MaterialType.ACTIVE_MATERIAL]
        new_component = create_material_component(active_material, active_material_config, config, i, weight_percent, active_materials)
        active_material_children.append(new_component())

    binder_children = []
    for i, (binder, weight_percent) in enumerate(formulation.binders.items()):
        binder_config = MATERIAL_CONFIGS[MaterialType.BINDER]
        new_component = create_material_component(binder, binder_config, config, i, weight_percent)
        binder_children.append(new_component())

    conductive_children = []
    for i, (conductive_additive, weight_percent) in enumerate(formulation.conductive_additives.items()):
        conductive_additive_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]
        new_component = create_material_component(conductive_additive, conductive_additive_config, config, i, weight_percent)
        conductive_children.append(new_component())
        
    return no_update, no_update, active_material_children, binder_children, conductive_children
