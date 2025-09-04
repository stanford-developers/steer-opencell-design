from typing import Type, List, Tuple
from dash import no_update, ctx
import time

from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

from App.general.callback_helpers import create_no_update_response, generate_parameters
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.enumerated_classes import FormulationType

from App.formulations.configs import FORMULATION_CONFIGS, FormulationConfig

from App.formulations.handlers import (
    # handle_indexed_dropdown_update, 
    handle_cell_store_update_materials,
    handle_material_button_update,
)

from steer_core.Apps.Utils.SliderControls import create_slider_config

from App.materials.configs import MaterialConfig

from steer_opencell_design.Formulations.ElectrodeFormulations import AnodeFormulation, CathodeFormulation


def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation(
        existing_warnings,
        cell_data, 
        input_values = None, 
        slider_values = None,
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

        else:
            return create_no_update_response(len(config.parameter_list))

    return generic_update_formulation


def create_generic_formulation_div_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation material management callbacks."""
    
    formulation_config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation_materials(
        existing_warnings,
        cell_data,
        active_div_styles,
        binder_div_styles,
        conductive_div_styles,
        cathode_active_options,
        anode_active_options
    ) -> Tuple:

        # Get the triggered ID
        trigger_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # Get the formulation from the cell
        formulation = get_object_from_cell(cell, formulation_config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(trigger_id)

        # Handle the case that the cell store is triggered
        if trigger_type == TriggerType.CELL_STORE:

            return handle_cell_store_update_materials(
                existing_warnings=existing_warnings,
                formulation=formulation,
                formulation_config=formulation_config,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
                cathode_active_options=cathode_active_options,
                anode_active_options=anode_active_options
            )
        
        if trigger_type == TriggerType.ACTION:

            return handle_material_button_update(
                cell=cell,
                trigger_id=trigger_id,
                existing_warnings=existing_warnings,
                formulation=formulation,
                formulation_config=formulation_config,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
                cathode_active_options=cathode_active_options,
                anode_active_options=anode_active_options
            )

        # # Handle the case that an action button is triggered
        # elif trigger_type == TriggerType.ACTION:

        #     return handle_material_button_update(
        #         existing_warnings=existing_warnings, 
        #         trigger_id=trigger_id, 
        #         formulation_config=formulation_config, 
        #         active_children=active_children, 
        #         binder_children=binder_children, 
        #         conductive_children=conductive_children,
        #         cathode_active_options=cathode_active_options,
        #         anode_active_options=anode_active_options
        #     )

    return generic_update_formulation_materials


# def create_generic_formulation_material_callback(formulation_type: FormulationType) -> callable:
#     """Factory function to create formulation material value callbacks."""
    
#     config = FORMULATION_CONFIGS[formulation_type]
    
#     def generic_update_formulation_material_values(
#         existing_warnings,
#         cell_data,

#         active_dropdown_values,
#         active_weight_fractions,
#         active_slider_values,
#         active_input_values,
        
#         binder_dropdown_values,
#         binder_weight_fractions,
#         binder_slider_values,
#         binder_input_values,
        
#         conductive_dropdown_values,
#         conductive_weight_fractions,
#         conductive_slider_values,
#         conductive_input_values

#     ) -> Tuple:

#         # Get the triggered ID
#         trigger_id = ctx.triggered_id

#         # Get the cell from cache
#         cell = get_cell_from_cache(cell_data['cache_key'])

#         # Get the formulation from the cell
#         formulation = get_object_from_cell(cell, config)

#         # Create trigger router and process the trigger
#         trigger_type = TriggerRouter.get_trigger_type(trigger_id)

#         if trigger_type == TriggerType.INDEXED_DROPDOWN:

#             return handle_indexed_dropdown_update(

#                 existing_warnings=existing_warnings,
#                 trigger_id=trigger_id,
#                 cell=cell,
#                 formulation=formulation,
#                 formulation_config=config,

#                 active_dropdown_values=active_dropdown_values,
#                 active_weight_fractions=active_weight_fractions,
#                 active_slider_values=active_slider_values,
#                 active_input_values=active_input_values,

#                 binder_dropdown_values=binder_dropdown_values,
#                 binder_weight_fractions=binder_weight_fractions,
#                 binder_slider_values=binder_slider_values,
#                 binder_input_values=binder_input_values,

#                 conductive_dropdown_values=conductive_dropdown_values,
#                 conductive_weight_fractions=conductive_weight_fractions,
#                 conductive_slider_values=conductive_slider_values,
#                 conductive_input_values=conductive_input_values

#             )
        
#     return generic_update_formulation_material_values



