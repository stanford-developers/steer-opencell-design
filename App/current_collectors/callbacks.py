import time
import inspect
from dash import callback, Input, Output, State, ALL

from App.current_collectors.layout_configs import CollectorType

from App.current_collectors.callback_helpers import (
    create_generic_current_collector_callback,
    create_dropdown_options_callback,
)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),

        Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
        Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "options"),
        Output("cathode_current_collector_design_div", "style"),

        Output("cathode_punched_design_parameters", "style"),
        Output("cathode_notched_design_parameters", "style"),
        Output("cathode_tabless_design_parameters", "style"),
        Output("cathode_tabbed_design_parameters", "style"),
    ],
    [  
        Input({"type": "trigger", "callback": "update_cathode_current_collector_design"}, "data"),
        Input({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [
        State("cell_store", "data"),
        
        State("cathode_current_collector_design_div", "style"),
        State("cathode_punched_design_parameters", "style"),
        State("cathode_notched_design_parameters", "style"),
        State("cathode_tabless_design_parameters", "style"),
        State("cathode_tabbed_design_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_design(
    trigger_data,
    dropdown_value,
    cell_data,
    current_dropdown_style,
    punched_style,
    notched_style,
    tabless_style,
    tabbed_style
    ):
    """
    Update the cathode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the name of this callback
    callback_name = inspect.currentframe().f_code.co_name

    # create the callback function
    callback_function = create_dropdown_options_callback(CollectorType.CATHODE_GENERIC)
    
    # call the function to create the response
    response = callback_function(
        cell_data=cell_data, 
        dropdown_value=dropdown_value,
        current_dropdown_style=current_dropdown_style,
        punched_style=punched_style,
        notched_style=notched_style,
        tabless_style=tabless_style,
        tabbed_style=tabbed_style
    )
    
    # return the response with the callback name as the first element
    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),

        Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
        Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "options"),
        Output("anode_current_collector_design_div", "style"),

        Output("anode_punched_design_parameters", "style"),
        Output("anode_notched_design_parameters", "style"),
        Output("anode_tabless_design_parameters", "style"),
        Output("anode_tabbed_design_parameters", "style"),
    ],
    [  
        Input({"type": "trigger", "callback": "update_anode_current_collector_design"}, "data"),
        Input({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [
        State("cell_store", "data"),

        State("anode_current_collector_design_div", "style"),
        State("anode_punched_design_parameters", "style"),
        State("anode_notched_design_parameters", "style"),
        State("anode_tabless_design_parameters", "style"),
        State("anode_tabbed_design_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def update_anode_current_collector_design(
    trigger_data,
    dropdown_value,
    cell_data,
    current_dropdown_style,
    punched_style,
    notched_style,
    tabless_style,
    tabbed_style
    ):
    """
    Update the anode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the name of this callback
    callback_name = inspect.currentframe().f_code.co_name

    # create the callback function
    callback_function = create_dropdown_options_callback(CollectorType.ANODE_GENERIC)
    
    # call the function to create the response
    response = callback_function(
        cell_data=cell_data, 
        dropdown_value=dropdown_value,
        current_dropdown_style=current_dropdown_style,
        punched_style=punched_style,
        notched_style=notched_style,
        tabless_style=tabless_style,
        tabbed_style=tabbed_style
    )
    
    # return the response with the callback name as the first element
    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_punched_current_collector"}, "data"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_cathode_punched_current_collector(
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
    original_input_steps
):

    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_PUNCHED)

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
        original_input_steps=original_input_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_punched_current_collector"}, "data"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_anode_punched_current_collector(
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
    original_input_steps
):

    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_PUNCHED)

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
        original_input_steps=original_input_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_tabless_current_collector"}, "data"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "cathode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_cathode_tabless_current_collector(
    data_trigger,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_tabless_current_collector"}, "data"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "anode", "object": "tabless_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_anode_tabless_current_collector(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_notched_current_collector"}, "data"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "cathode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_cathode_notched_current_collector(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


@callback(
    [ 
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_notched_current_collector"}, "data"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "anode", "object": "notched_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
        
    ],
    prevent_initial_call=True,
)
def update_anode_notched_current_collector(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "radioitem"}, "value"),
        Output({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "text_input"}, "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_tabbed_current_collector"}, "data"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "radioitem"}, "value"),
        Input({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "text_input"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "cathode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_cathode_tabbed_current_collector(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    radioitem_values,
    text_item_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_TABBED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        radioitem_values,
        text_item_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "radioitem"}, "value"),
        Output({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "text_input"}, "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_tabbed_current_collector"}, "data"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "n_submit"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "n_blur"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "radioitem"}, "value"),
        Input({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "text_input"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "value"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "value"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input"}, "step"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "value"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "min"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "max"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "marks"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "rangeslider"}, "step"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_start"}, "step"),
        State({"electrode": "anode", "object": "tabbed_current_collector", "property": ALL, "subtype": "input_end"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_anode_tabbed_current_collector(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    radioitem_values,
    text_item_values,
    cell_data,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings,
    original_slider_values,
    original_slider_mins,
    original_slider_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps,
    original_rangeslider_values,
    original_rangeslider_mins,
    original_rangeslider_maxs,
    original_rangeslider_marks,
    original_rangeslider_steps,
    original_input_start_steps,
    original_input_end_steps
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_TABBED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        radioitem_values,
        text_item_values,
        original_values=original_slider_values,
        original_mins=original_slider_mins,
        original_maxs=original_slider_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
        original_rangeslider_values=original_rangeslider_values,
        original_rangeslider_mins=original_rangeslider_mins,
        original_rangeslider_maxs=original_rangeslider_maxs,
        original_rangeslider_marks=original_rangeslider_marks,
        original_rangeslider_steps=original_rangeslider_steps,
        original_input_start_steps=original_input_start_steps,
        original_input_end_steps=original_input_end_steps
    )

    return (callback_name,) + response


