from dash import callback, Input, Output, ALL, State, ctx, no_update
import inspect

from App.general.callback_helpers import update_style_display

from App.electrodes.callback_helpers import create_electrode_callback
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType
from App.current_collectors.configs import COLLECTOR_CONFIGS
from App.current_collectors.configs import CollectorType

from App.general.cell_operations import (
    get_object_from_cell,
    set_object_to_cell,
    set_cell_to_cache,
)

from App.general.cache_service import cache


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cathode_insulation_material_parameters", "style"),
    ],
    [
        Input({"type": "trigger", "callback": "toggle_cathode_insulation_parameters_style"}, "data"),
    ],
    [
        State("cell_store", "data"),
        State("cathode_insulation_material_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def toggle_cathode_insulation_parameters_style(
    trigger_data,
    cell_data, 
    current_style
    ):
    # get the callback name
    callback_name = inspect.currentframe().f_code.co_name

    # Get the configuration for cathode
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # Get the current collector object
    current_collector = get_object_from_cell(cell, config)

    # Show if insulation_area > 0, else hide
    if hasattr(current_collector, "insulation_area") and current_collector.insulation_area > 0:
        new_style = update_style_display(current_style, "block")
        return (callback_name, new_style)
    else:
        new_style = update_style_display(current_style, "none")
        return (callback_name, new_style)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("anode_insulation_material_parameters", "style"),
    ],
    [
        Input({"type": "trigger", "callback": "toggle_anode_insulation_parameters_style"}, "data"),
    ],
    [
        State("cell_store", "data"),
        State("anode_insulation_material_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def toggle_anode_insulation_parameters_style(
    trigger_data,
    cell_data, 
    current_style
    ):

    # get the callback name
    callback_name = inspect.currentframe().f_code.co_name

    # Get the configuration for anode
    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # Get the current collector object
    current_collector = get_object_from_cell(cell, config)

    # Show if insulation_area > 0, else hide
    if hasattr(current_collector, "insulation_area") and current_collector.insulation_area > 0:
        new_style = update_style_display(current_style, "block")
        return (callback_name, new_style)
    else:
        new_style = update_style_display(current_style, "none")
        return (callback_name, new_style)


# @callback(
#     [
#         Output("warnings_store", "data", allow_duplicate=True),
#         Output("cell_store", "data", allow_duplicate=True),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
#         Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
#     ],
#     [
#         Input("cathode_electrode_tab", "style"),
#         Input("cathode_tab", "style"),
#         Input("tabs_panel", "style"),
#         Input("cell_store", "data"),
#         Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_submit"),
#         Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_blur"),
#         Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
#     ],
#     [
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "value"),
#         State("warnings_store", "data"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
#         State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
#     ],
#     prevent_initial_call=True,
# )
# def update_cathode(
#     cc_tab_style,
#     tab_style,
#     tabs_panel_style,
#     cell_data,
#     input_n_sub,
#     input_n_blur,
#     slider_values,
#     control_mode_values,
#     input_values,
#     existing_warnings,
#     original_values,
#     original_mins,
#     original_maxs,
#     original_slider_marks,
#     original_slider_steps,
#     original_input_steps
# ):
#     callback_function = create_electrode_callback(ElectrodeType.CATHODE)

#     response = callback_function(
#         existing_warnings=existing_warnings,
#         cell_data=cell_data,
#         input_values=input_values,
#         slider_values=slider_values,
#         viewing_styles=[cc_tab_style, tab_style, tabs_panel_style],
#         control_mode_values=control_mode_values,
#         original_values=original_values,
#         original_mins=original_mins,
#         original_maxs=original_maxs,
#         original_slider_marks=original_slider_marks,
#         original_slider_steps=original_slider_steps,
#         original_input_steps=original_input_steps
#     )

#     return response


# @callback(
#     [
#         Output("warnings_store", "data", allow_duplicate=True),
#         Output("cell_store", "data", allow_duplicate=True),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
#         Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
#     ],
#     [
#         Input("anode_electrode_tab", "style"),
#         Input("anode_tab", "style"),
#         Input("tabs_panel", "style"),
#         Input("cell_store", "data"),
#         Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_submit"),
#         Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_blur"),
#         Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
#     ],
#     [
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "value"),
#         State("warnings_store", "data"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
#         State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
#     ],
#     prevent_initial_call=True,
# )
# def update_anode(
#     cc_tab_style,
#     tab_style,
#     tabs_panel_style,
#     cell_data,
#     input_n_sub,
#     input_n_blur,
#     slider_values,
#     control_mode_values,
#     input_values,
#     existing_warnings,
#     original_values,
#     original_mins,
#     original_maxs,
#     original_slider_marks,
#     original_slider_steps,
#     original_input_steps
# ):
#     callback_function = create_electrode_callback(ElectrodeType.ANODE)

#     response = callback_function(
#         existing_warnings,
#         cell_data,
#         input_values,
#         slider_values,
#         viewing_styles=[cc_tab_style, tab_style, tabs_panel_style],
#         control_mode_values=control_mode_values,
#         original_values=original_values,
#         original_mins=original_mins,
#         original_maxs=original_maxs,
#         original_slider_marks=original_slider_marks,
#         original_slider_steps=original_slider_steps,
#         original_input_steps=original_input_steps
#     )

#     return response


