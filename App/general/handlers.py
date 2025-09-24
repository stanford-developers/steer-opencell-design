from dash import no_update
from typing import Type, Tuple, List, Any
import time

from App.general.enumerated_classes import SubType
from App.general.cell_operations import set_cell_to_cache, set_object_to_cell

from App.general.callback_helpers import (
    validate_dependent_properties,
    generate_parameters,
    generate_rangeslider_values,
    validate_single_property,
)

from steer_core.Apps.Utils.SliderControls import (
    create_slider_config,
    create_range_slider_config,
)
from steer_core.Apps.ContextManagers import capture_warnings


def _build_basic_response(slider_configs: dict, cache_key: str = None) -> List[Any]:
    """Build the basic response components from slider configurations."""

    dict_key = {"cache_key": cache_key} if cache_key is not None else no_update

    return [
        dict_key,
        slider_configs["grid_slider_vals"],
        slider_configs["min_vals"],
        slider_configs["max_vals"],
        slider_configs["mark_vals"],
        slider_configs["step_vals"],
        slider_configs["input_step_vals"],
    ]


def _add_dropdown_menu(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add dropdown menu value if applicable."""
    if hasattr(config, "dropdown_menu") and config.dropdown_menu:
        response.append(object_instance.name)


def _add_range_slider_components(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add range slider components if applicable."""
    if not (hasattr(config, "range_slider_parameters") and config.range_slider_parameters):
        return

    # Generate range slider values
    start_values, end_values, min_values, max_values = generate_rangeslider_values(object_instance, config.range_slider_parameters)

    # Create range slider configurations
    range_slider_configs = create_range_slider_config(min_values, max_values, start_values, end_values)

    # Add all range slider components to response
    response.extend(
        [
            range_slider_configs["grid_slider_vals"],
            range_slider_configs["min_vals"],
            range_slider_configs["max_vals"],
            range_slider_configs["mark_vals"],
            range_slider_configs["step_vals"],
            range_slider_configs["input_step_vals"],
            range_slider_configs["input_step_vals"],
        ]
    )


def _add_radioitem_components(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add radio item components if applicable."""
    if not (hasattr(config, "radioitem_parameters") and config.radioitem_parameters):
        return

    # Add radio item values
    radioitem_values = [getattr(object_instance, param) for param in config.radioitem_parameters]
    response.extend([radioitem_values])


def _add_text_item_components(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add text item components if applicable."""
    if not (hasattr(config, "text_parameters") and config.text_parameters):
        return

    # Add text item values
    text_item_values = [getattr(object_instance, param) for param in config.text_parameters]
    response.extend([text_item_values])


def handle_cell_store_update(object_instance: Type, config: Type, existing_warnings: List[str] = []) -> Tuple:
    """
    Handle cell store update for any collector type.

    Args:
        object_instance: The collector object instance
        config: Configuration object containing parameters and settings

    Returns:
        Tuple containing all the UI component values for the callback

    Raises:
        AttributeError: If required attributes are missing from config or object
    """
    source = f"{config.__class__.__name__}_cell_store_update"

    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:

        # Validate all dependent properties first
        validate_dependent_properties(object_instance, config)

        # Generate basic parameters
        parameter_list, min_values, max_values = generate_parameters(object_instance, config)

        # Create slider configurations
        slider_configs = create_slider_config(min_values, max_values, parameter_list)

        # Build the base response
        response = _build_basic_response(slider_configs)

        # Add optional components based on configuration
        _add_dropdown_menu(response, object_instance, config)
        _add_range_slider_components(response, object_instance, config)
        _add_radioitem_components(response, object_instance, config)
        _add_text_item_components(response, object_instance, config)

    return (warnings_list,) + tuple(response)


def handle_property_update(
    existing_warnings: List[str],
    triggered_id: dict,
    cell: Type,
    object_instance: Type,
    config: Type,
    input_values: List[float],
    slider_values: List[float],
    range_slider_values: List[float] = None,
    input_start_values: List[float] = None,
    input_end_values: List[float] = None,
    radioitem_values: str = None,
    text_item_values: str = None,
) -> Tuple:

    # determine the property and subtype from the triggered ID
    property_name = triggered_id["property"]

    # determine the subtype from the triggered ID
    subtype = SubType(triggered_id["subtype"])

    source = f"{config.__class__.__name__}_{property_name}_{subtype}"
    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:

        # determine the value from the inputs and the subtype
        value = determine_value(
            config,
            subtype,
            property_name,
            input_values,
            slider_values,
            range_slider_values,
            input_start_values,
            input_end_values,
            radioitem_values,
            text_item_values,
        )

        # Do a pre check to make sure the value is in an appropriate range
        value = validate_single_property(object_instance, property_name, value, config)

        # set the new value to the object instance
        setattr(object_instance, property_name, value)

        # validate all dependent properties first
        validate_dependent_properties(object_instance, config)

        # make new cell
        new_cell = set_object_to_cell(cell, object_instance, config)

        # get the new key
        new_key = set_cell_to_cache(new_cell)

        # get the new parameters
        parameter_list, min_values, max_values = generate_parameters(object_instance, config)

        # Create slider configurations
        slider_configs = create_slider_config(min_values, max_values, parameter_list)

        # Build the base response
        response = _build_basic_response(slider_configs, new_key)

        # Add optional components based on configuration
        _add_dropdown_menu(response, object_instance, config)
        _add_range_slider_components(response, object_instance, config)
        _add_radioitem_components(response, object_instance, config)
        _add_text_item_components(response, object_instance, config)

    return (warnings_list,) + tuple(response)


def determine_value(
    config: Type,
    subtype: SubType,
    property_name: str,
    input_values: List[float],
    slider_values: List[float],
    range_slider_values: List[float] = [],
    input_start_values: List[float] = [],
    input_end_values: List[float] = [],
    radioitem_values: str = [],
    text_item_values: str = [],
) -> Any:
    # Determine the value from the input type
    if subtype == SubType.INPUT:
        property_index = config.settable_parameters.index(property_name)
        value = input_values[property_index]
    elif subtype == SubType.SLIDER:
        property_index = config.settable_parameters.index(property_name)
        value = slider_values[property_index]
    elif subtype == SubType.RANGESLIDER:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
    elif subtype == SubType.INPUT_START:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
        value[0] = input_start_values[property_index]
    elif subtype == SubType.INPUT_END:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
        value[1] = input_end_values[property_index]
    elif subtype == SubType.RADIOITEM:
        property_index = config.radioitem_parameters.index(property_name)
        value = radioitem_values[property_index]
    elif subtype == SubType.TEXT_INPUT:
        property_index = config.text_parameters.index(property_name)
        value = text_item_values[property_index]

    return value
