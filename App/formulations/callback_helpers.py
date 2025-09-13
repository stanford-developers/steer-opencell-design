from typing import Tuple, Dict
from dash import no_update, ctx
from copy import deepcopy
import time

from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

from App.general.callback_helpers import create_no_update_response, generate_parameters
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.enumerated_classes import FormulationType

from App.formulations.configs import FORMULATION_CONFIGS, FormulationConfig

from App.formulations.handlers import (
    handle_indexed_dropdown_update, 
    handle_cell_store_update_materials,
    handle_material_button_update,
)

from steer_core.Apps.Utils.SliderControls import create_slider_config


def _split_consolidated_dropdown_values(all_dropdown_values, active_div_count, binder_div_count, conductive_div_count):
    """Split consolidated dropdown values back into separate lists for each material type"""
    active_dropdown_values = all_dropdown_values[:active_div_count]
    binder_dropdown_values = all_dropdown_values[active_div_count:active_div_count + binder_div_count]
    conductive_dropdown_values = all_dropdown_values[active_div_count + binder_div_count:active_div_count + binder_div_count + conductive_div_count]
    return active_dropdown_values, binder_dropdown_values, conductive_dropdown_values


def _split_consolidated_div_styles(all_div_styles, active_div_count, binder_div_count, conductive_div_count):
    """Split consolidated div styles back into separate lists for each material type"""
    active_div_styles = all_div_styles[:active_div_count]
    binder_div_styles = all_div_styles[active_div_count:active_div_count + binder_div_count]
    conductive_div_styles = all_div_styles[active_div_count + binder_div_count:active_div_count + binder_div_count + conductive_div_count]
    return active_div_styles, binder_div_styles, conductive_div_styles


def replace_material_key_by_index(materials_dict: Dict, index: int, new_material):
    """Replace material at index i with new material, keeping same weight fraction"""
    items = list(materials_dict.items())
    old_material, weight_fraction = items[index]

    # Replace with new material, same weight fraction
    items[index] = (new_material, weight_fraction)

    # Update dictionary
    materials_dict.clear()
    materials_dict.update(items)

    return materials_dict


# Usage in your formulation context
def update_formulation_material_at_index(formulation, category: str, index: int, new_material):
    """Update specific material in formulation by index"""
    if category == 'active_material':
        active_materials_dict = deepcopy(formulation.active_materials)
        new_active_materials_dict = replace_material_key_by_index(active_materials_dict, index, new_material)
        formulation.active_materials = new_active_materials_dict
    elif category == 'binder':
        binder_materials_dict = deepcopy(formulation.binders)
        new_binder_materials = replace_material_key_by_index(binder_materials_dict, index, new_material)
        formulation.binders = new_binder_materials
    elif category == 'conductive_additive':
        conductive_additives_dict = deepcopy(formulation.conductive_additives)
        new_conductive_additives = replace_material_key_by_index(conductive_additives_dict, index, new_material)
        formulation.conductive_additives = new_conductive_additives
    return formulation



def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation(
        existing_warnings,
        cell_data, 
        input_values = None, 
        slider_values = None,
        viewing_styles = []
    ) -> Tuple:

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split('.')[-1]

        # If all display is none for any of the viewing styles, return no update
        if any(d.get('display') == 'none' for d in viewing_styles):
            return create_no_update_response(config)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the formulation from the cell
        formulation = get_object_from_cell(cell, config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:

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
        all_div_styles,
        all_dropdown_values,
        active_material_div_children,
        binder_div_children,
        conductive_additive_div_children,
        cathode_active_options,
        anode_active_options,
        viewing_styles = []
    ) -> Tuple:

        # Get the triggered ID
        trigger_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # Get the formulation from the cell
        formulation = get_object_from_cell(cell, formulation_config)

        # Get div counts dynamically from the actual div children
        active_div_count = len(active_material_div_children)
        binder_div_count = len(binder_div_children)
        conductive_div_count = len(conductive_additive_div_children)

        # Split consolidated values back into separate lists
        active_div_styles, binder_div_styles, conductive_div_styles = _split_consolidated_div_styles(
            all_div_styles, active_div_count, binder_div_count, conductive_div_count
        )
        
        active_dropdown_values, binder_dropdown_values, conductive_dropdown_values = _split_consolidated_dropdown_values(
            all_dropdown_values, active_div_count, binder_div_count, conductive_div_count
        )

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
        
        if trigger_type == TriggerType.INDEXED_DROPDOWN:

            return handle_indexed_dropdown_update(
                cell=cell,
                trigger_id=trigger_id,
                existing_warnings=existing_warnings,
                formulation=formulation,
                formulation_config=formulation_config,
                active_dropdown_values=active_dropdown_values,
                binder_dropdown_values=binder_dropdown_values,
                conductive_dropdown_values=conductive_dropdown_values
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
                active_dropdown_values=active_dropdown_values,
                binder_dropdown_values=binder_dropdown_values,
                conductive_dropdown_values=conductive_dropdown_values,
                cathode_active_options=cathode_active_options,
                anode_active_options=anode_active_options
            )
        
    return generic_update_formulation_materials

