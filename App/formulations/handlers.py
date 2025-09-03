from typing import List
from dash import no_update

from App.formulations.configs import FormulationConfig
from App.general.handlers import _build_basic_response
from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.callback_helpers import generate_parameters, create_no_update_response

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from steer_core.Apps.Utils.SliderControls import create_slider_config 


def handle_indexed_dropdown_update(
        existing_warnings,
        trigger_id,
        cell,
        formulation,
        formulation_config,

        active_dropdown_values,
        active_weight_fractions,
        active_slider_values,
        active_input_values,

        binder_dropdown_values,
        binder_weight_fractions,
        binder_slider_values,
        binder_input_values,

        conductive_dropdown_values,
        conductive_weight_fractions,
        conductive_slider_values,
        conductive_input_values
):
    
    index = trigger_id.get('index')
    material_category = trigger_id.get('material')
    
    active_material_response = {}

    # build the response for the active materials
    for i, av in enumerate(active_dropdown_values):

        # if not triggered by active material, then build no response
        if material_category != 'active_material':
            active_material_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL], existing_warnings))[2:]

        # if triggered by active material
        else:
            # but not the right index, build no response
            if i != index:
                active_material_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL], existing_warnings))[2:]

            else:
                material_name = active_dropdown_values[index]
                if formulation_config.formulation_type == CathodeFormulation:
                    material = CathodeMaterial.from_database(material_name)
                    material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL]
                elif formulation_config.formulation_type == AnodeFormulation:
                    material = AnodeMaterial.from_database(material_name)
                    material_config = MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]

                # get the parameters for the material
                parameter_list, min_values, max_values = generate_parameters(material, material_config)

                # Create slider configurations
                slider_configs = create_slider_config(min_values, max_values, parameter_list)

                active_material_response[index] = _build_basic_response(slider_configs)[1:]

    active_material_response = tuple(
        [x for pair in vals for x in pair]
        for vals in zip(*active_material_response.values())
    )

    binder_response = {}

    # build the response for the binders
    for i, bi in enumerate(binder_dropdown_values):

        # if not triggered by binder material, then build no response
        if material_category != 'binder':
            binder_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.BINDER], existing_warnings))[2:]

        # if triggered by binder material
        else:
            # but not the right index, build no response
            if i != index:
                binder_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.BINDER], existing_warnings))[2:]

            else:
                material_name = binder_dropdown_values[index]
                material = Binder.from_database(material_name)
                material_config = MATERIAL_CONFIGS[MaterialType.BINDER]

                # get the parameters from the material
                parameter_list, min_values, max_values = generate_parameters(material, material_config)

                # get the slider configs
                slider_configs = create_slider_config(min_values, max_values, parameter_list)

                binder_response[index] = _build_basic_response(slider_configs)[1:]

    binder_response = tuple(
        [x for pair in vals for x in pair]
        for vals in zip(*binder_response.values())
    )

    conductive_additive_response = {}

    for i, ca in enumerate(conductive_dropdown_values):

        if material_category != 'conductive_additive':
            conductive_additive_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE], existing_warnings))[2:]

        else:

            if i != index:
                conductive_additive_response[i] = list(create_no_update_response(MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE], existing_warnings))[2:]

            else:
                material_name = conductive_dropdown_values[index]
                material = ConductiveAdditive.from_database(material_name)
                material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]

                # get the parameters for the material
                parameter_list, min_values, max_values = generate_parameters(material, material_config)

                # Create slider configurations
                slider_configs = create_slider_config(min_values, max_values, parameter_list)

                conductive_additive_response[index] = _build_basic_response(slider_configs)[1:]

    conductive_additive_response = tuple(
        [x for pair in vals for x in pair]
        for vals in zip(*conductive_additive_response.values())
    )

    return (existing_warnings, ) + (no_update, ) + active_material_response + binder_response + conductive_additive_response



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

    return (
        no_update, 
        no_update, 
        active_material_children, 
        binder_children, 
        conductive_children
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

    # Return updated children lists
    return no_update, no_update, active_children, binder_children, conductive_children

