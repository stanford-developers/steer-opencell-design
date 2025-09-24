from typing import Tuple, Type
from dash import ctx, no_update

from App.layup.configs import LAYUP_CONFIGS
from App.general.enumerated_classes import LayupType
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.handlers import handle_cell_store_update, handle_property_update
from App.general.trigger_router import TriggerRouter
from App.general.enumerated_classes import TriggerType
from App.general.callback_helpers import create_no_update_response
from steer_opencell_design.Constructions.Layups import MonoLayer, ZFoldMonoLayer


def create_layup_callback(layup_key: LayupType) -> callable:
    """Factory function to create layup callbacks."""

    config = LAYUP_CONFIGS[layup_key]

    def generic_update_layup(
        existing_warnings: list,
        cell_data: dict,
        input_values: list,
        slider_values: list,
        viewing_styles=[],
    ) -> Tuple:
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        if any(d.get("display") == "none" for d in viewing_styles):
            return create_no_update_response(config, existing_warnings)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the layup from the cell
        layup = get_object_from_cell(cell, config)

        if type(layup) != config.layup_type:
            return create_no_update_response(config, existing_warnings)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(layup, config, existing_warnings)

        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings,
                triggered_id,
                cell,
                layup,
                config,
                input_values,
                slider_values,
            )

        # Fallback
        return create_no_update_response(config, existing_warnings)

    return generic_update_layup


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
