from typing import Type, List, Tuple
from dash import no_update, ctx
import time

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_materials.CellMaterials.Electrode import Binder, ConductiveAdditive, _ActiveMaterial

from App.general.callback_helpers import create_no_update_response, generate_parameters
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.enumerated_classes import FormulationType

from App.formulations.configs import FORMULATION_CONFIGS
from App.database_service import BINDER_MATERIALS, CONDUCTIVE_ADDITIVE_MATERIALS

from steer_core.Apps.Components.MaterialSelectors import MaterialSelector, ActiveMaterialSelector
from steer_core.Apps.Utils.SliderControls import create_slider_config


def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation(
        existing_warnings,
        cell_data, 
        input_values, 
        slider_values, 
    ) -> Tuple:

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the formulation from the cell
        formulation = get_object_from_cell(cell, config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:

            return handle_cell_store_update(
                formulation,
                config,
                existing_warnings
            )

        elif trigger_type == TriggerType.PROPERTY:

            return handle_property_update(
                existing_warnings,
                triggered_id,
                cell,
                formulation,
                config,
                input_values,
                slider_values,
            )

        # Default: return no update for all outputs
        return create_no_update_response(len(config.parameter_list))

    return generic_update_formulation


def create_generic_formulation_material_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation material management callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation_materials(
        existing_warnings,
        cell_data,
        active_children,
        binder_children,
        conductive_children,
        active_materials,
        add_active_clicks,
        remove_active_clicks,
        add_binder_clicks,
        remove_binder_clicks,
        add_conductive_clicks,
        remove_conductive_clicks,
    ) -> Tuple:

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # Get the formulation from the cell
        formulation = get_object_from_cell(cell, config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:
            from App.formulations.handlers import handle_cell_store_update_material_children
            return handle_cell_store_update_material_children(
                formulation, 
                config, 
                active_materials
            )

        elif trigger_type == TriggerType.BUTTON:
            from App.formulations.handlers import handle_material_button_update
            return handle_material_button_update(
                triggered_id,
                formulation,
                config,
                existing_warnings,
                active_children,
                binder_children,
                conductive_children,
                active_materials
            )

        # Default: return no update for all outputs
        return create_no_update_response(5)  # 5 outputs for this callback

    return generic_update_formulation_materials


def create_material_component(
        material, 
        material_config, 
        formulation_config, 
        index,
        weight_percent,
        active_materials = None
) -> MaterialSelector:
    
    """Create a new material component."""

    # get the new parameters
    parameter_list, min_values, max_values = generate_parameters(material, material_config)

    # Create slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)

    base_id = {"object": "electrode", "index": index}

    # set the electrode to the base id
    if formulation_config.formulation_type == CathodeFormulation:
        base_id = {**base_id, "electrode": "cathode"}
    elif formulation_config.formulation_type == AnodeFormulation:
        base_id = {**base_id, "electrode": "anode"}

    # set the material type to the base id
    if material_config.material_type == Binder:
        base_id = {**base_id, "material": "binder"}
        options = BINDER_MATERIALS

        return MaterialSelector(
            id_base=base_id,
            material_options=options,
            slider_configs=slider_configs,
            default_material=material.name,
            default_weight_percent=weight_percent,
            div_width='calc(80%)'
        )

    elif material_config.material_type == ConductiveAdditive:
        base_id = {**base_id, "material": "conductive_additive"}
        options = CONDUCTIVE_ADDITIVE_MATERIALS

        return MaterialSelector(
            id_base=base_id,
            material_options=options,
            slider_configs=slider_configs,
            default_material=material.name,
            default_weight_percent=weight_percent,
            div_width='calc(80%)'
        )

    elif material_config.material_type == _ActiveMaterial:
        base_id = {**base_id, "material": "active_material"}
        options = active_materials

        return ActiveMaterialSelector(
            id_base=base_id,
            material_options=options,
            slider_configs=slider_configs,
            default_material=material.name,
            default_weight_percent=weight_percent,
            div_width='calc(100%)'
        )

