from typing import Type, List, Tuple
from dash import no_update, ctx
import time

from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial

from App.general.callback_helpers import create_no_update_response
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.enumerated_classes import FormulationType

from App.formulations.configs import FORMULATION_CONFIGS
from App.formulations.handlers import handle_indexed_dropdown_update, handle_cell_store_update_material_children, handle_material_button_update


def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation(
        existing_warnings,
        cell_data, 
        input_values = None, 
        slider_values = None, 
        dropdown_values = None,
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
        
        elif trigger_type == TriggerType.INDEXED_DROPDOWN:

            return handle_indexed_dropdown_update(
                existing_warnings,
                triggered_id,
                cell,
                formulation,
                config,
                dropdown_values
            )

        # Default: return no update for all outputs
        return create_no_update_response(len(config.parameter_list))

    return generic_update_formulation


def create_generic_formulation_div_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation material management callbacks."""
    
    formulation_config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation_materials(
        existing_warnings,
        cell_data,
        active_children,
        binder_children,
        conductive_children,
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
            return handle_cell_store_update_material_children(existing_warnings, formulation)

        # Handle the case that an action button is triggered
        elif trigger_type == TriggerType.ACTION:
            return handle_material_button_update(existing_warnings, trigger_id, formulation_config, active_children, binder_children, conductive_children)

        # Default: return no update for all outputs
        return (
            no_update,
            no_update,
            [no_update for _ in active_children],
            [no_update for _ in binder_children],
            [no_update for _ in conductive_children],
            no_update
        )

    return generic_update_formulation_materials


# def create_generic_formulation_material_callback(formulation_type: FormulationType) -> callable:
#     """Factory function to create formulation material value callbacks."""
    
#     config = FORMULATION_CONFIGS[formulation_type]
    
#     def generic_update_formulation_material_values(
#         existing_warnings,
#         cell_data,
#         dropdown_values,
#         input_values = None, 
#         slider_values = None,
#     ) -> Tuple:

#         # Get the triggered ID
#         triggered_id = ctx.triggered_id

#         # Get the cell from cache
#         cell = get_cell_from_cache(cell_data['cache_key'])

#         # Get the formulation from the cell
#         formulation = get_object_from_cell(cell, config)

#         # Create trigger router and process the trigger
#         trigger_type = TriggerRouter.get_trigger_type(triggered_id)

#         if trigger_type == TriggerType.CELL_STORE:
#             from App.formulations.handlers import handle_cell_store_update_material_values
#             return handle_cell_store_update_material_values(
#                 formulation,
#                 config,
#                 existing_warnings
#             )

#         elif trigger_type == TriggerType.INDEXED_DROPDOWN:
#             from App.formulations.handlers import handle_material_selector_dropdown_update
#             return handle_material_selector_dropdown_update(
#                 existing_warnings,
#                 triggered_id,
#                 cell,
#                 formulation,
#                 config,
#                 dropdown_values
#             )

#         elif trigger_type == TriggerType.PROPERTY:
#             from App.formulations.handlers import handle_material_property_update
#             return handle_material_property_update(
#                 existing_warnings,
#                 triggered_id,
#                 cell,
#                 formulation,
#                 config,
#                 input_values,
#                 slider_values,
#             )

#         # Default: return no update for all outputs
#         from dash import no_update
#         return (
#             existing_warnings,  # warnings_store
#             no_update,          # cell_store 
#             no_update,          # dropdown values (no_update for ALL pattern when no change needed)
#             no_update,          # slider values (no_update for ALL pattern when no change needed)
#             no_update,          # slider mins (no_update for ALL pattern when no change needed)
#             no_update,          # slider maxs (no_update for ALL pattern when no change needed)
#             no_update,          # slider marks (no_update for ALL pattern when no change needed)
#             no_update,          # slider steps (no_update for ALL pattern when no change needed)
#             no_update           # input steps (no_update for ALL pattern when no change needed)
#         )

#     return generic_update_formulation_material_values


def create_empty_material_component(material_config, index) -> Type:
    """Create an empty material component with default values."""

    # Create base ID
    base_id = {"object": "formulation", "index": index, "material": material_config.material_type.__class__.__name__}

    # Set electrode type to the id
    if material_config.material_type == CathodeMaterial:
        base_id = {**base_id, "electrode": "cathode"}
    elif material_config.material_type == AnodeMaterial:
        base_id = {**base_id, "electrode": "anode"}

    return material_config.custom_selector(
        id_base=base_id,
        material_options=material_config.dropdown_options,
        div_width=material_config.selector_div_width
    )

