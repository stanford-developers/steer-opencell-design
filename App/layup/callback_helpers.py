from typing import Tuple, Type
from dash import ctx, no_update
from dash.exceptions import PreventUpdate

from App.layup.configs import LAYUP_CONFIGS, SEPARATOR_CONFIGS
from App.general.enumerated_classes import LayupType
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update
from App.general.trigger_router import TriggerRouter
from App.general.enumerated_classes import TriggerType
from App.general.callback_helpers import prevent_update_from_styles
from steer_opencell_design.Constructions.Layups import MonoLayer, ZFoldMonoLayer, _Layup


def create_layup_callback(layup_key: LayupType) -> callable:
    """Factory function to create layup callbacks."""

    config = LAYUP_CONFIGS[layup_key]

    def generic_update_layup(
        existing_warnings: list,
        cell_data: dict,
        input_values: list,
        slider_values: list,
        radioitem_values=None,
        viewing_styles=[],
        original_values=None,
        original_mins=None,
        original_maxs=None,
        original_slider_marks=None,
        original_slider_steps=None,
        original_input_steps=None,
        original_radioitem_values=None
    ) -> Tuple:
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        prevent_update_from_styles(viewing_styles)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the layup from the cell
        layup = get_object_from_cell(cell, config)

        # If the layup type does not match the config, prevent update
        if type(layup) != config.layup_type and config.layup_type != _Layup:
            raise PreventUpdate

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(layup, config, existing_warnings)

        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings=existing_warnings,
                triggered_id=triggered_id,
                cell=cell,
                object_instance=layup,
                config=config,
                input_values=input_values,
                slider_values=slider_values,
                radioitem_values=radioitem_values,
                original_values=original_values,
                original_mins=original_mins,
                original_maxs=original_maxs,
                original_slider_marks=original_slider_marks,
                original_slider_steps=original_slider_steps,
                original_input_steps=original_input_steps,
                original_radioitem_values=original_radioitem_values 
            )

        # Fallback
        raise PreventUpdate

    return generic_update_layup


def create_layup_separator_callback(separator_key: LayupType, layup_key: LayupType) -> callable:
    """Factory function to create layup callbacks."""

    separator_config = SEPARATOR_CONFIGS[separator_key]
    layup_config = LAYUP_CONFIGS[layup_key]

    def generic_update_separator(
        existing_warnings: list,
        cell_data: dict,
        input_values: list,
        slider_values: list,
        radioitem_values=None,
        viewing_styles=[],
        original_values=None,
        original_mins=None,
        original_maxs=None,
        original_slider_marks=None,
        original_slider_steps=None,
        original_input_steps=None,
        original_radioitem_values=None
    ) -> Tuple:
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        prevent_update_from_styles(viewing_styles)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the layup to check the type
        layup = get_object_from_cell(cell, layup_config)

        # If the layup type does not match the config, prevent update
        if type(layup) != layup_config.layup_type:
            raise PreventUpdate
    
        # get the separator from the cell
        separator = get_object_from_cell(cell, separator_config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(separator, separator_config, existing_warnings)

        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings=existing_warnings,
                triggered_id=triggered_id,
                cell=cell,
                object_instance=separator,
                config=separator_config,
                input_values=input_values,
                slider_values=slider_values,
                radioitem_values=radioitem_values,
                original_values=original_values,
                original_mins=original_mins,
                original_maxs=original_maxs,
                original_slider_marks=original_slider_marks,
                original_slider_steps=original_slider_steps,
                original_input_steps=original_input_steps,
                original_radioitem_values=original_radioitem_values 
            )

        # Fallback
        raise PreventUpdate

    return generic_update_separator


def convert_layup(layup: Type, target_type_name: str):
    """Convert layup from one type to another using from_* constructors."""

    # Get the current type name
    current_layup_name = type(layup).__name__

    # Define conversion methods for each source -> target combination
    conversion_map = {
        (
            "MonoLayer",
            "ZFoldMonoLayer",
        ): lambda cc: ZFoldMonoLayer.from_monolayer(cc),
        (
            "ZFoldMonoLayer",
            "MonoLayer",
        ): lambda cc: MonoLayer.from_zfold_monolayer(cc),
    }

    # Generate the conversion key
    conversion_key = (current_layup_name, target_type_name)

    # create the function to convert
    converter = conversion_map[conversion_key]

    # create the new layup using the converter
    new_layup = converter(layup)

    return new_layup
