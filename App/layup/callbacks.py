from dash import Input, Output, State, callback, ALL
from dash.exceptions import PreventUpdate
import inspect

from App.general.cache_service import cache

from App.general.cell_operations import get_object_from_cell, set_object_to_cell, get_cell_from_cache, set_cell_to_cache
from App.general.callback_helpers import prevent_update_from_styles, update_style_display
from App.layup.configs import LAYUP_CONFIGS, LayupType, SeparatorType
from App.layup.callback_helpers import create_layup_callback, convert_layup, create_layup_separator_callback

from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer

LAYUP_DESIGNS = [
    "Z-Fold",
    "Laminate",
    "Stacked",
]

@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("layup_design", "options"),
        Output("layup_design_div", "style"),
        Output("layup_design", "value"),
    ],
    Input({"type": "trigger", "callback": "update_layup_dropdown_options"}, "data"),
    [
        State("cell_store", "data"),
        State("layup_design_div", "style"),
        State("layup_design", "options"),
    ],
    prevent_initial_call=True,
)
def update_layup_dropdown_options(trigger_data, data, current_style, current_options):
    """
    Update the layup design dropdown menu options, style, and value
    based on the current layup store data.
    """
    # get the config of the item
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = get_cell_from_cache(data["cache_key"])

    # get the layup from the cell
    layup = get_object_from_cell(cell, config)

    # Define type mappings
    type_config = {
        Laminate: {
            "display": "none",
            "options": [{"label": "Laminate", "value": "laminate"}],
            "value": "laminate",
        },
        MonoLayer: {
            "display": "block",
            "options": [{"label": item, "value": item.lower()} for item in LAYUP_DESIGNS if item != "Laminate"],
            "value": "stacked",
        },
        ZFoldMonoLayer: {
            "display": "block",
            "options": [{"label": item, "value": item.lower()} for item in LAYUP_DESIGNS if item != "Laminate"],
            "value": "z-fold",
        },
    }

    # Get configuration for current layup type
    layup_type = type(layup)

    # get the configuration for the current layup type
    config = type_config.get(layup_type)

    # set the style according to the config display value
    current_style["display"] = config["display"]

    # Get callback name for orchestra system
    callback_name = inspect.currentframe().f_code.co_name

    return callback_name, config["options"], current_style, config["value"]


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),

        Output("laminate_design_parameters", "style"),
        Output("zfold_design_parameters", "style"),
        Output("stacked_design_parameters", "style"),
        
        Output("laminate_separator_design_parameters", "style"),
        Output("zfold_separator_design_parameters", "style"),
        Output("stacked_separator_design_parameters", "style"),
    ],
    Input({"type": "trigger", "callback": "update_layup_design_parameters_layout"}, "data"),
    [
        State("cell_store", "data"),
        State("laminate_design_parameters", "style"),
        State("zfold_design_parameters", "style"),
        State("stacked_design_parameters", "style"),
        State("laminate_separator_design_parameters", "style"),
        State("zfold_separator_design_parameters", "style"),
        State("stacked_separator_design_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def update_layup_design_parameters_layout(
    trigger_data,
    cell_data,
    laminate_parameter_style,
    zfold_parameter_style,
    stacked_parameter_style,
    laminate_separator_parameter_style,
    zfold_separator_parameter_style,
    stacked_separator_parameter_style,
    ):
    """
    Update the layup design parameters based on the current design selection.
    """
    # get the config
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = get_cell_from_cache(cell_data["cache_key"])

    # get the layup from the cell
    layup = get_object_from_cell(cell, config)

    # get the layup type
    layup_type = type(layup).__name__

    # update styles based on layup type
    laminate_parameter_style = update_style_display(laminate_parameter_style, "block" if layup_type == "Laminate" else "none")
    zfold_parameter_style = update_style_display(zfold_parameter_style, "block" if layup_type == "ZFoldMonoLayer" else "none")
    stacked_parameter_style = update_style_display(stacked_parameter_style, "block" if layup_type == "MonoLayer" else "none")
    laminate_separator_parameter_style = update_style_display(laminate_separator_parameter_style, "block" if layup_type == "Laminate" else "none")
    zfold_separator_parameter_style = update_style_display(zfold_separator_parameter_style, "block" if layup_type == "ZFoldMonoLayer" else "none")
    stacked_separator_parameter_style = update_style_display(stacked_separator_parameter_style, "block" if layup_type == "MonoLayer" else "none")

    # Get callback name for orchestra system
    callback_name = inspect.currentframe().f_code.co_name

    # return
    return (
        callback_name,
        laminate_parameter_style, 
        zfold_parameter_style, 
        stacked_parameter_style, 
        laminate_separator_parameter_style, 
        zfold_separator_parameter_style, 
        stacked_separator_parameter_style
    )


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
    ],
    Input("layup_design", "value"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_layup_design(design_value, cell_data):
    """Handle current collector design changes and convert between types."""

    # if design_value is laminate, return no_update
    if design_value == "laminate":
        raise PreventUpdate

    # Get current cell and collector
    cell_key = cell_data["cache_key"]
    cell = cache.get(cell_key)

    layup = get_object_from_cell(cell, LAYUP_CONFIGS[LayupType.GENERIC])

    type_name = type(layup).__name__

    # Map design values to collector types
    design_to_type = {
        "z-fold": "ZFoldMonoLayer",
        "stacked": "MonoLayer",
    }

    # get the name of the target collector type
    target_type_name = design_to_type.get(design_value)

    # If already the correct type, no conversion needed
    if type_name == target_type_name:
        raise PreventUpdate

    # Additional check: If this is likely triggered by cell upload (not user interaction)
    # Check if the current dropdown value already matches the collector type
    current_dropdown_value_map = {
        "ZFoldMonoLayer": "z-fold",
        "MonoLayer": "stacked",
    }

    expected_dropdown_value = current_dropdown_value_map.get(type_name)

    if design_value == expected_dropdown_value:
        raise PreventUpdate

    # Do the conversion
    new_layup = convert_layup(layup, target_type_name)

    # Assign the new layup to the cell and get the key
    new_cell = set_object_to_cell(cell, new_layup, LAYUP_CONFIGS[LayupType.GENERIC])

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Get callback name for orchestra system
    callback_name = inspect.currentframe().f_code.co_name

    # Update the dash store with the new cell key
    return (callback_name, {"cache_key": new_key}, cell_data)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_zfold_monolayer"}, "data"),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_zfold_monolayer(
    data_trigger,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_callback(LayupType.ZFOLDMONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_zfold_monolayer_separator"}, "data"),
        Input({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "zfoldmonolayer_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_zfold_monolayer_separator(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_separator_callback(SeparatorType.ZFOLDMONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "laminate", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_laminate"}, "data"),
        Input({"object": "laminate", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "laminate", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "laminate", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "laminate", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "laminate", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "laminate", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "laminate", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "laminate", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "laminate", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "laminate", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_laminate(
    data_trigger,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_callback(LayupType.LAMINATE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "laminate_top_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_laminate_top_separator"}, "data"),
        Input({"object": "laminate_top_separator", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "laminate_top_separator", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "laminate_top_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_laminate_top_separator(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_separator_callback(SeparatorType.TOP_LAMINATE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "laminate_bottom_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_laminate_bottom_separator"}, "data"),
        Input({"object": "laminate_bottom_separator", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "laminate_bottom_separator", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "laminate_bottom_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_laminate_bottom_separator(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_separator_callback(SeparatorType.BOTTOM_LAMINATE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "stacked_top_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_stacked_top_separator"}, "data"),
        Input({"object": "stacked_top_separator", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "stacked_top_separator", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "stacked_top_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_stacked_top_separator(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_separator_callback(SeparatorType.TOP_MONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "stacked_bottom_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_stacked_bottom_separator"}, "data"),
        Input({"object": "stacked_bottom_separator", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "stacked_bottom_separator", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "stacked_bottom_separator", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_stacked_bottom_separator(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_separator_callback(SeparatorType.BOTTOM_MONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "stacked", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_monolayer"}, "data"),
        Input({"object": "stacked", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"object": "stacked", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "stacked", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "stacked", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "stacked", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "stacked", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "stacked", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "stacked", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "stacked", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "stacked", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_monolayer(
    data_trigger,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
):

    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_layup_callback(LayupType.MONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"object": "layup", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "layup", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "layup", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "layup", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "layup", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "layup", "property": ALL, "subtype": "input"}, "step"),
        Output({"object": "layup", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [   
        Input({"type": "trigger", "callback": "update_generic_layup"}, "data"),
        Input({"object": "layup", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"object": "layup", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "layup", "property": ALL, "subtype": "slider"}, "value"),
        Input({"object": "layup", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "layup", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"object": "layup", "property": ALL, "subtype": "slider"},"value",),
        State({"object": "layup", "property": ALL, "subtype": "slider"}, "min"),
        State({"object": "layup", "property": ALL, "subtype": "slider"}, "max"),
        State({"object": "layup", "property": ALL, "subtype": "slider"}, "marks"),
        State({"object": "layup", "property": ALL, "subtype": "slider"}, "step"),
        State({"object": "layup", "property": ALL, "subtype": "input"}, "step"),
        State({"object": "layup", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    prevent_initial_call=True,
)
def update_generic_layup(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    radioitem_values,
    cell_data,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_radioitem_values,
):
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_layup_callback(LayupType.GENERIC)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        radioitem_values=radioitem_values,
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_radioitem_values=original_radioitem_values,
    )

    return (callback_name, ) + response



