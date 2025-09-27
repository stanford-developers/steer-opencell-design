import time
from dash import callback, Input, Output, State, no_update, ALL, ctx
from dash.exceptions import PreventUpdate

from App.cache_service import cache
from App.current_collectors.configs import COLLECTOR_CONFIGS

from App.current_collectors.callback_helpers import (
    create_generic_current_collector_callback,
    create_dropdown_options_callback,
    update_style_display,
)

from App.general.enumerated_classes import CollectorType
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.callback_helpers import create_properties_table, prevent_update_from_styles




@callback(
    [
        Output("cell_store", "data", allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "options"),
        Output("cathode_current_collector_design_div", "style"),
        Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [  
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [
        State("cathode_current_collector_design_div", "style"),
    ],
    prevent_initial_call=True,
)
def update_cathode_dropdown_options(
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    data, 
    dropdown_value,
    current_style,
    ):
    """
    Update the anode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    callback_function = create_dropdown_options_callback(CollectorType.CATHODE_GENERIC)

    response = callback_function(
        data, 
        current_style,
        dropdown_value,
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style]
    )

    return response


@callback(
    [
        Output("cell_store", "data", allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "options"),
        Output("anode_current_collector_design_div", "style"),
        Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [  
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    ],
    [
        State("anode_current_collector_design_div", "style"),
    ],
    prevent_initial_call=True,
)
def update_anode_dropdown_options(
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    data, 
    dropdown_value,
    current_style,
    ):
    """
    Update the anode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    callback_function = create_dropdown_options_callback(CollectorType.ANODE_GENERIC)

    response = callback_function(
        data, 
        current_style,
        dropdown_value,
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style]
    )

    return response


@callback(
    [
        Output("cathode_punched_design_parameters", "style"),
        Output("cathode_notched_design_parameters", "style"),
        Output("cathode_tabless_design_parameters", "style"),
        Output("cathode_tabbed_design_parameters", "style"),
    ],
    [
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data")
    ],
    [
        State("cathode_punched_design_parameters", "style"),
        State("cathode_notched_design_parameters", "style"),
        State("cathode_tabless_design_parameters", "style"),
        State("cathode_tabbed_design_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_design_parameters(
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    punched_style,
    notched_style,
    tabless_style,
    tabbed_style
    ):
    """
    Update the cathode current collector design parameters based on the current collector store data.
    """
    
    # If all display is none for any of the viewing styles, return no update
    prevent_update_from_styles([cc_tab_style, tab_style, tabs_panel_style])

    # get the config
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # get the cell from the cache
    cell = get_cell_from_cache(cell_data["cache_key"])

    # get the current collector
    current_collector = get_object_from_cell(cell, config)

    # get the current collector type
    cc_type = type(current_collector).__name__

    # Map collector types to their active component
    collector_type_mapping = {
        "PunchedCurrentCollector": "punched",
        "NotchedCurrentCollector": "notched", 
        "TablessCurrentCollector": "tabless",
        "TabWeldedCurrentCollector": "tabbed"
    }
    
    active_component = collector_type_mapping.get(cc_type)
    if not active_component:
        # Fallback to original behavior if unknown type
        return (no_update, no_update, no_update, no_update)
    
    # Update styles based on which component should be active
    punched_style = update_style_display(punched_style, "block" if active_component == "punched" else "none")
    notched_style = update_style_display(notched_style, "block" if active_component == "notched" else "none") 
    tabless_style = update_style_display(tabless_style, "block" if active_component == "tabless" else "none")
    tabbed_style = update_style_display(tabbed_style, "block" if active_component == "tabbed" else "none")

    return (punched_style, notched_style, tabless_style, tabbed_style)
    

@callback(
    [
        Output("anode_punched_design_parameters", "style"),
        Output("anode_notched_design_parameters", "style"),
        Output("anode_tabless_design_parameters", "style"),
        Output("anode_tabbed_design_parameters", "style"),
    ],
    Input({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'}, "value"),
    prevent_initial_call=True,
)
def update_anode_current_collector_design_parameters(design):
    """
    Update the anode current collector design parameters based on the current collector store data.
    """
    if design is None:
        raise PreventUpdate

    # Map design values to their active component
    design_mapping = {
        "punched": "punched",
        "notched": "notched", 
        "tabless": "tabless",
        "tabbed": "tabbed"
    }
    
    active_component = design_mapping.get(design)
    if not active_component:
        # Fallback for unknown design
        return [no_update, no_update, no_update, no_update]
    
    # Update styles based on which component should be active
    # Note: Using None as current_style since these are fresh creates
    punched_style = update_style_display(None, "block" if active_component == "punched" else "none")
    notched_style = update_style_display(None, "block" if active_component == "notched" else "none") 
    tabless_style = update_style_display(None, "block" if active_component == "tabless" else "none")
    tabbed_style = update_style_display(None, "block" if active_component == "tabbed" else "none")

    return [punched_style, notched_style, tabless_style, tabbed_style]


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
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
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps
):
    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_PUNCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps
    )

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "punched_current_collector", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
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
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps
):
    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_PUNCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps
    )

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_cathode_tabless_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
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
    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_anode_tabless_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
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
    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_cathode_notched_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
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
    
    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_anode_notched_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
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
    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_cathode_tabbed_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
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
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
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
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
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
def update_anode_tabbed_collector(
    cc_tab_style,
    tabs_panel_style,
    main_tabs_container_style,
    cell_data,
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
        viewing_styles=[cc_tab_style, tabs_panel_style, main_tabs_container_style],
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

    return response


@callback(
    [
        Output("cathode_current_collector_properties_div", "children"),
    ],
    [
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_properties(cc_tab_style, tab_style, tabs_panel_style, cell_data):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    # If all display is none for any of the viewing styles, return no update
    prevent_update_from_styles([cc_tab_style, tab_style, tabs_panel_style])

    # get the config for the cathode generic current collector
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # get the current collector properties
    properties = current_collector.properties

    # Create properties table using utility function
    properties_table = create_properties_table(
        properties,
        table_id="cathode_current_collector_properties_table",
        decimal_places=2,
    )

    # return the plots
    return [properties_table]


@callback(
    [
        Output("anode_current_collector_properties_div", "children"),
    ],
    [
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_anode_current_collector_properties(cc_tab_style, tab_style, tabs_panel_style, cell_data):
    """
    Update the anode current collector plots based on the current collector store data.
    """
    # If all display is none for any of the viewing styles, return no update
    prevent_update_from_styles([cc_tab_style, tab_style, tabs_panel_style])

    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # get the current collector properties
    properties = current_collector.properties

    # Create properties table using utility function
    properties_table = create_properties_table(
        properties,
        table_id="anode_current_collector_properties_table",
        decimal_places=2,
    )

    # return the plots
    return [properties_table]


