from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from dash import no_update


def handle_indexed_dropdown_update(
        existing_warnings,
        trigger_id,
        cell,
        formulation,
        formulation_config,
        dropdown_values
):
    pass


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


def handle_material_button_update(
    triggered_id,
    formulation,
    config,
    existing_warnings,
    active_children,
    binder_children,
    conductive_children,
    active_materials
):
    """Handle add/remove material button clicks."""
    
    # Parse the button ID to determine action
    parts = triggered_id.split('-')
    button_type = parts[0]  # 'add' or 'remove'
    material_category = parts[2]  # 'active', 'binder' or 'conductive'
    
    if button_type == 'add':
        if material_category == 'active':
            return handle_add_material_to_children("active_material", active_children, binder_children, conductive_children, config, active_materials)
        elif material_category == 'binder':
            return handle_add_material_to_children("binder", active_children, binder_children, conductive_children, config)
        elif material_category == 'conductive':
            return handle_add_material_to_children("conductive_additive", active_children, binder_children, conductive_children, config)
    
    elif button_type == 'remove':
        if material_category == 'active':
            return handle_remove_material_from_children("active", active_children, binder_children, conductive_children)
        elif material_category == 'binder':
            return handle_remove_material_from_children("binder", active_children, binder_children, conductive_children)
        elif material_category == 'conductive':
            return handle_remove_material_from_children("conductive", active_children, binder_children, conductive_children)
    
    # Default: return current state
    return no_update, no_update, active_children or [], binder_children or [], conductive_children or []


def handle_add_material_to_children(material_type, active_children, binder_children, conductive_children, config, active_materials=None):
    """Add a new empty material component to the appropriate children list."""
    from App.formulations.callback_helpers import create_empty_material_component
    
    # Work with current children lists
    current_active = list(active_children) if active_children else []
    current_binder = list(binder_children) if binder_children else []
    current_conductive = list(conductive_children) if conductive_children else []
    
    if material_type == "active_material":
        # Add new empty active material
        new_index = len(current_active)
        empty_component = create_empty_material_component("active_material", config, new_index, active_materials)
        current_active.append(empty_component())
    elif material_type == "binder":
        # Add new empty binder
        new_index = len(current_binder)
        empty_component = create_empty_material_component("binder", config, new_index)
        current_binder.append(empty_component())
    elif material_type == "conductive_additive":
        # Add new empty conductive additive
        new_index = len(current_conductive)
        empty_component = create_empty_material_component("conductive_additive", config, new_index)
        current_conductive.append(empty_component())
    
    return no_update, no_update, current_active, current_binder, current_conductive


def handle_remove_material_from_children(material_category, active_children, binder_children, conductive_children):
    """Remove the last material component from the appropriate children list."""
    
    # Work with current children lists
    current_active = list(active_children) if active_children else []
    current_binder = list(binder_children) if binder_children else []
    current_conductive = list(conductive_children) if conductive_children else []
    
    if material_category == "active":
        # Remove last active material (but keep at least one if any exist)
        if len(current_active) > 1:
            current_active = current_active[:-1]
    elif material_category == "binder":
        # Remove last binder
        if len(current_binder) > 0:
            current_binder = current_binder[:-1]
    elif material_category == "conductive":
        # Remove last conductive additive
        if len(current_conductive) > 0:
            current_conductive = current_conductive[:-1]
    
    return no_update, no_update, current_active, current_binder, current_conductive


