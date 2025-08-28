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
            return handle_add_active_material(formulation, config, existing_warnings, active_materials)
        elif material_category == 'binder':
            return handle_add_binder(formulation, config, existing_warnings, active_materials)
        elif material_category == 'conductive':
            return handle_add_conductive_additive(formulation, config, existing_warnings, active_materials)
    
    elif button_type == 'remove':
        if material_category == 'active':
            return handle_remove_active_material(formulation, config, existing_warnings, active_materials)
        elif material_category == 'binder':
            return handle_remove_binder(formulation, config, existing_warnings, active_materials)
        elif material_category == 'conductive':
            return handle_remove_conductive_additive(formulation, config, existing_warnings, active_materials)
    
    # Default: return current state
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_add_active_material(formulation, config, existing_warnings, active_materials):
    """Handle adding a new active material."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_remove_active_material(formulation, config, existing_warnings, active_materials):
    """Handle removing an active material."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_add_binder(formulation, config, existing_warnings, active_materials):
    """Handle adding a new binder."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_remove_binder(formulation, config, existing_warnings, active_materials):
    """Handle removing a binder."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_add_conductive_additive(formulation, config, existing_warnings, active_materials):
    """Handle adding a new conductive additive."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)


def handle_remove_conductive_additive(formulation, config, existing_warnings, active_materials):
    """Handle removing a conductive additive."""
    # For now, return current state - implement logic later
    return handle_cell_store_update_material_children(formulation, config, active_materials)

