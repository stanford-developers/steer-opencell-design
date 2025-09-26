from typing import Tuple
from dash import ctx
import time
from dash.exceptions import PreventUpdate

from App.general.callback_helpers import create_no_update_response
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.enumerated_classes import FormulationType, MaterialType

from App.formulations.configs import FORMULATION_CONFIGS

from App.formulations.handlers import (
    handle_indexed_dropdown_update,
    handle_cell_store_update_materials,
    handle_material_button_update,
    handle_weight_fraction_update,
    handle_material_property_update,
)

from App.materials.configs import MATERIAL_CONFIGS

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)


def split_consolidated_values(all_dropdown_values, active_div_count, binder_div_count, conductive_div_count):
    """Split consolidated dropdown values back into separate lists for each material type"""
    active_values = all_dropdown_values[:active_div_count]
    binder_values = all_dropdown_values[active_div_count : active_div_count + binder_div_count]
    conductive_values = all_dropdown_values[active_div_count + binder_div_count : active_div_count + binder_div_count + conductive_div_count]
    return active_values, binder_values, conductive_values


def split_consolidated_property_values(
    formulation,
    all_property_values,
    active_div_count,
    binder_div_count,
    conductive_div_count,
):
    """Split consolidated property values back into separate lists for each material type"""
    active_material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL] if type(formulation) == CathodeFormulation else MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]
    binder_material_config = MATERIAL_CONFIGS[MaterialType.BINDER]
    conductive_material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]
    active_n = active_div_count * len(active_material_config.parameter_list)
    binder_n = binder_div_count * len(binder_material_config.parameter_list)
    conductive_n = conductive_div_count * len(conductive_material_config.parameter_list)
    return split_consolidated_values(all_property_values, active_n, binder_n, conductive_n)


def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""

    config = FORMULATION_CONFIGS[formulation_type]

    def generic_update_formulation(
        existing_warnings,
        cell_data,
        input_values=None,
        slider_values=None,
        viewing_styles=[],
    ) -> Tuple:
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        if any(d.get("display") == "none" for d in viewing_styles):
            raise PreventUpdate

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the formulation from the cell
        formulation = get_object_from_cell(cell, config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(formulation, config, existing_warnings)

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
            raise PreventUpdate

    return generic_update_formulation


def create_generic_formulation_div_callback(
    formulation_type: FormulationType,
) -> callable:
    """Factory function to create formulation material management callbacks."""

    formulation_config = FORMULATION_CONFIGS[formulation_type]

    def generic_update_formulation_materials(
        existing_warnings,
        cell_data,
        all_div_styles,
        all_dropdown_values,
        all_weight_fraction_values,
        active_material_div_children,
        binder_div_children,
        conductive_additive_div_children,
        cathode_active_options,
        anode_active_options,
        slider_values,
        input_values,
        viewing_styles=[],
    ) -> Tuple:
        
        # If all display is none for any of the viewing styles, return no update
        if any(d.get("display") == "none" for d in viewing_styles):
            raise PreventUpdate

        # Get the triggered ID
        trigger_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # Get the formulation from the cell
        formulation = get_object_from_cell(cell, formulation_config)

        # Get div counts dynamically from the actual div children
        active_div_count = len(active_material_div_children)
        binder_div_count = len(binder_div_children)
        conductive_div_count = len(conductive_additive_div_children)

        # get the trigger property
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(trigger_id, triggered_prop_id)

        # get the dropdown values for each material type
        (
            active_dropdown_values,
            binder_dropdown_values,
            conductive_dropdown_values,
        ) = split_consolidated_values(
            all_dropdown_values,
            active_div_count,
            binder_div_count,
            conductive_div_count,
        )

        # Get the styles for each material type
        (
            active_div_styles,
            binder_div_styles,
            conductive_div_styles,
        ) = split_consolidated_values(all_div_styles, active_div_count, binder_div_count, conductive_div_count)

        # get the weight fraction values for each material type
        (
            active_weight_fractions,
            binder_weight_fractions,
            conductive_weight_fractions,
        ) = split_consolidated_values(
            all_weight_fraction_values,
            active_div_count,
            binder_div_count,
            conductive_div_count,
        )

        # get the slider values for each material type
        (
            active_slider_values,
            binder_slider_values,
            conductive_slider_values,
        ) = split_consolidated_property_values(
            formulation,
            slider_values,
            active_div_count,
            binder_div_count,
            conductive_div_count,
        )

        # get the input values for each material type
        (
            active_input_values,
            binder_input_values,
            conductive_input_values,
        ) = split_consolidated_property_values(
            formulation,
            input_values,
            active_div_count,
            binder_div_count,
            conductive_div_count,
        )

        # If all display is none for any of the viewing styles, return no update
        if any(d.get("display") == "none" for d in viewing_styles):
            raise PreventUpdate

        # Handle the case that the cell store is triggered
        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update_materials(
                existing_warnings=existing_warnings,
                formulation=formulation,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
                cathode_active_options=cathode_active_options,
                anode_active_options=anode_active_options,
            )

        elif trigger_type == TriggerType.INDEXED_DROPDOWN:
            return handle_indexed_dropdown_update(
                existing_warnings=existing_warnings,
                cell=cell,
                trigger_id=trigger_id,
                formulation=formulation,
                formulation_config=formulation_config,
                active_dropdown_values=active_dropdown_values,
                binder_dropdown_values=binder_dropdown_values,
                conductive_dropdown_values=conductive_dropdown_values,
            )

        elif trigger_type == TriggerType.ACTION:
            return handle_material_button_update(
                existing_warnings=existing_warnings,
                cell=cell,
                trigger_id=trigger_id,
                formulation=formulation,
                formulation_config=formulation_config,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
            )

        elif trigger_type == TriggerType.WEIGHT_FRACTION:
            return handle_weight_fraction_update(
                existing_warnings=existing_warnings,
                cell=cell,
                trigger_id=trigger_id,
                formulation=formulation,
                formulation_config=formulation_config,
                active_weight_fractions=active_weight_fractions,
                binder_weight_fractions=binder_weight_fractions,
                conductive_weight_fractions=conductive_weight_fractions,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
            )

        elif trigger_type == TriggerType.PROPERTY:
            return handle_material_property_update(
                existing_warnings=existing_warnings,
                trigger_id=trigger_id,
                cell=cell,
                formulation=formulation,
                formulation_config=formulation_config,
                active_div_styles=active_div_styles,
                binder_div_styles=binder_div_styles,
                conductive_div_styles=conductive_div_styles,
                active_slider_values=active_slider_values,
                binder_slider_values=binder_slider_values,
                conductive_slider_values=conductive_slider_values,
                active_input_values=active_input_values,
                binder_input_values=binder_input_values,
                conductive_input_values=conductive_input_values,
            )

    return generic_update_formulation_materials
