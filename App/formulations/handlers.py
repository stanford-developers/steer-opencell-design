from typing import List
from App.formulations.configs import FormulationConfig
from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.callback_helpers import create_trigger_data, create_no_update_response

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation

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
        existing_warnings: List[float], 
        formulation: CathodeFormulation | AnodeFormulation, 
        formulation_config: FormulationConfig
):

    """Create empty MaterialSelector components based on formulation structure."""
    
    from App.formulations.callback_helpers import create_material_component

    # Determine the active material type based on the formulation
    if isinstance(formulation, CathodeFormulation):
        active_material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL]
    elif isinstance(formulation, AnodeFormulation):
        active_material_config = MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]
    else:
        raise ValueError("Unsupported formulation type for material children creation.")

    # Get the binder and conductive additive configs
    binder_config = MATERIAL_CONFIGS[MaterialType.BINDER]
    conductive_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]

    def create_children_list(material_dictionary, material_config, formulation_config):
        """Create a list of MaterialSelector components."""
        children = []

        for i, (material, weight_percent) in enumerate(material_dictionary.items()):

            empty_component = create_material_component(
                material_config=material_config, 
                formulation_config=formulation_config,
                index=i, 
                material=material, 
                weight_percent=weight_percent, 
                empty=False
            )

            children.append(empty_component())

        return children

    # Create empty components based on the number of active materials in the formulation
    active_material_children = create_children_list(
        formulation.active_materials, 
        active_material_config,
        formulation_config
    )

    # Create empty components based on the number of binder materials in the formulation
    binder_children = create_children_list(
        formulation.binders,
        binder_config,
        formulation_config
    )

    # Create empty components based on the number of conductive materials in the formulation
    conductive_children = create_children_list(
        formulation.conductive_additives,
        conductive_config,
        formulation_config
    )

    # create a store object holding trigger data
    trigger_data = create_trigger_data()

    return (
        no_update, 
        no_update, 
        active_material_children, 
        binder_children, 
        conductive_children, 
        trigger_data
    )


def handle_material_button_update(
    existing_warnings,
    trigger_id,
    formulation_config,
    active_children,
    binder_children,
    conductive_children
):
    """Handle add/remove material button clicks."""
    
    from App.formulations.callback_helpers import create_material_component

    action_category = trigger_id.get('action')
    material_category = trigger_id.get('material')

    # Get the the material config from the triggered id
    if material_category == 'active_material' and formulation_config.formulation_type == CathodeFormulation:
        material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL]
    elif material_category == 'active_material' and formulation_config.formulation_type == AnodeFormulation:
        material_config = MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]
    elif material_category == 'binder':
        material_config = MATERIAL_CONFIGS[MaterialType.BINDER]
    elif material_category == 'conductive_additive':
        material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]

    # Handle the case that a material is being added
    if action_category == 'add':

        if material_category == 'active_material':
            new_index = len(active_children)
            new_component = create_material_component(material_config, formulation_config, new_index)
            active_children.append(new_component())
        elif material_category == 'binder':
            new_index = len(binder_children)
            new_component = create_material_component(material_config, formulation_config, new_index)
            binder_children.append(new_component())
        elif material_category == 'conductive_additive':
            new_index = len(conductive_children)
            new_component = create_material_component(material_config, formulation_config, new_index)
            conductive_children.append(new_component())

    # Handle the case that a material is being removed
    elif action_category == 'remove':
        if material_category == 'active_material':
            if active_children and len(active_children) > 1:
                active_children.pop()
        elif material_category == 'binder':
            if binder_children:
                binder_children.pop()
        elif material_category == 'conductive_additive':
            if conductive_children:
                conductive_children.pop()

    # create a store object holding trigger data
    trigger_data = create_trigger_data()

    # Return updated children lists
    return no_update, no_update, active_children, binder_children, conductive_children, trigger_data

