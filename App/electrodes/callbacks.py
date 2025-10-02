from dash import callback, Input, Output, ALL, State, ctx, no_update
from dash.exceptions import PreventUpdate

from App.general.callback_helpers import create_properties_table

from App.electrodes.callback_helpers import create_electrode_callback
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType
from App.current_collectors.configs import COLLECTOR_CONFIGS
from App.current_collectors.configs import CollectorType
from App.general.callback_helpers import prevent_update_from_styles

from App.general.cell_operations import (
    get_object_from_cell,
    set_object_to_cell,
    set_cell_to_cache,
)

from App.general.cache_service import cache

from steer_opencell_design.Components.Electrodes import ElectrodeControlMode


@callback(
    [
        Output("cathode_insulation_material_parameters", "style"),
    ],
    [
        Input("cathode_electrode_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    [
        State("cathode_insulation_material_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def toggle_cathode_insulation_parameters(
    electrode_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data, 
    current_style
    ):

    # prevent update if any of the viewing styles is 'none'
    prevent_update_from_styles([electrode_tab_style, tab_style, tabs_panel_style])

    # Get the configuration for cathode
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # Get the current collector object
    current_collector = get_object_from_cell(cell, config)

    # Ensure current_style is a dict
    if current_style is None:
        current_style = {}

    # Show if insulation_area > 0, else hide
    if hasattr(current_collector, "insulation_area") and current_collector.insulation_area > 0:
        # Remove 'display' if present, or set to 'block'
        style = dict(current_style)
        style.pop("display", None)
        return (style,)
    else:
        # Set 'display' to 'none'
        style = dict(current_style)
        style["display"] = "none"
        return (style,)


@callback(
    [
        Output("anode_insulation_material_parameters", "style"),
    ],
    [
        Input("anode_electrode_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    [
        State("anode_insulation_material_parameters", "style"),
    ],
    prevent_initial_call=True,
)
def toggle_anode_insulation_parameters(
    electrode_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    current_style
    ):

    # prevent update if any of the viewing styles is 'none'
    prevent_update_from_styles([electrode_tab_style, tab_style, tabs_panel_style])

    # Get the configuration for anode
    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # Get the current collector object
    current_collector = get_object_from_cell(cell, config)

    # Ensure current_style is a dict
    if current_style is None:
        current_style = {}

    # Show if insulation_area > 0, else hide
    if hasattr(current_collector, "insulation_area") and current_collector.insulation_area > 0:
        # Remove 'display' if present, or set to 'block'
        style = dict(current_style)
        style.pop("display", None)
        return (style,)
    else:
        # Set 'display' to 'none'
        style = dict(current_style)
        style["display"] = "none"
        return (style,)


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [
        Input("cathode_electrode_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "cathode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_cathode(
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    control_mode_values,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps
):
    callback_function = create_electrode_callback(ElectrodeType.CATHODE)

    response = callback_function(
        existing_warnings=existing_warnings,
        cell_data=cell_data,
        input_values=input_values,
        slider_values=slider_values,
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style],
        control_mode_values=control_mode_values,
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
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
        Output({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [
        Input("anode_electrode_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        Input({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "radioitem"}, "value"),
    ],
    [
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "value"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "min"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "max"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "marks"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "slider"}, "step"),
        State({"electrode": "anode", "object": "electrode", "property": ALL, "subtype": "input"}, "step"),
    ],
    prevent_initial_call=True,
)
def update_anode(
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    control_mode_values,
    input_values,
    existing_warnings,
    original_values,
    original_mins,
    original_maxs,
    original_slider_marks,
    original_slider_steps,
    original_input_steps
):
    callback_function = create_electrode_callback(ElectrodeType.ANODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style],
        control_mode_values=control_mode_values,
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
        Output("cathode_top_down_plot", "figure"),
        Output("cathode_cross_section_plot", "figure"),
        Output("cathode_properties_div", "children"),
    ],
    [
        Input("cathode_electrode_tab", "style"),
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    [
        State("cathode_top_down_plot", "figure"),
        State("cathode_cross_section_plot", "figure"), 
        State("cathode_properties_div", "children"),
    ],
    prevent_initial_call=True,
)
def update_cathode_plots(
    electrode_tab_style,
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    current_top_down_plot,
    current_cross_section_plot,
    current_properties_div,
):
    """
    Update the cathode plots based on the current collector store data.
    Optimized to avoid unnecessary plot regeneration.
    """
    # Early exit if main panels are hidden
    prevent_update_from_styles([tab_style, tabs_panel_style])
    
    # Check what triggered this callback
    triggered = ctx.triggered[0] if ctx.triggered else {}
    triggered_id = triggered.get("prop_id", "")
    
    # If only style changes triggered and no tabs are visible, prevent update
    electrode_visible = electrode_tab_style and electrode_tab_style.get("display") == "block"
    cc_visible = cc_tab_style and cc_tab_style.get("display") == "block"
    
    if not electrode_visible and not cc_visible:
        raise PreventUpdate
    
    # Determine if cell_store data changed (plots need to be regenerated)
    cell_store_changed = "cell_store.data" in triggered_id
    
    # Get cathode object (only when needed)
    config = ELECTRODE_CONFIGS[ElectrodeType.CATHODE]
    cell = cache.get(cell_data["cache_key"])
    cathode = get_object_from_cell(cell, config)
    
    if electrode_visible:
        # Generate plots for electrode tab
        plot_cross_section = cathode.get_cross_section(title="Cross-Section Cathode View")
        
        properties = cathode.properties
        properties_table = create_properties_table(
            properties, 
            table_id="cathode_properties_table", 
            decimal_places=2
        )
        
        # Always generate top-down plot if cell store changed or if it doesn't exist
        if cell_store_changed or not current_top_down_plot:
            plot_top_down = cathode.get_top_down_view(title="Top-Down Cathode View")
        else:
            plot_top_down = no_update
            
        return (
            plot_top_down,
            plot_cross_section,
            properties_table,
        )
    
    elif cc_visible:
        # Always generate top-down plot for CC tab (it's the main plot for this tab)
        plot_top_down = cathode.get_top_down_view(title="Top-Down Cathode View")
        
        # Only update other plots if cell store changed and they exist
        if cell_store_changed and current_cross_section_plot:
            plot_cross_section = cathode.get_cross_section(title="Cross-Section Cathode View")
            
            properties = cathode.properties
            properties_table = create_properties_table(
                properties, 
                table_id="cathode_properties_table", 
                decimal_places=2
            )
            
            return (
                plot_top_down,
                plot_cross_section,
                properties_table,
            )
        else:
            return plot_top_down, no_update, no_update
    
    else:
        raise PreventUpdate


@callback(
    [
        Output("anode_top_down_plot", "figure"),
        Output("anode_cross_section_plot", "figure"),
        Output("anode_properties_div", "children"),
    ],
    [
        Input("anode_electrode_tab", "style"),
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    [
        State("anode_top_down_plot", "figure"),
        State("anode_cross_section_plot", "figure"),
        State("anode_properties_div", "children"),
    ],
    prevent_initial_call=True,
)
def update_anode_plots(
    electrode_tab_style,
    cc_tab_style,
    tab_style,
    tabs_panel_style,
    cell_data,
    current_top_down_plot,
    current_cross_section_plot,
    current_properties_div,
):
    """
    Update the anode plots based on the current collector store data.
    Optimized to avoid unnecessary plot regeneration.
    """
    # Early exit if main panels are hidden
    prevent_update_from_styles([tab_style, tabs_panel_style])
    
    # Check what triggered this callback
    triggered = ctx.triggered[0] if ctx.triggered else {}
    triggered_id = triggered.get("prop_id", "")
    
    # If only style changes triggered and no tabs are visible, prevent update
    electrode_visible = electrode_tab_style and electrode_tab_style.get("display") == "block"
    cc_visible = cc_tab_style and cc_tab_style.get("display") == "block"
    
    if not electrode_visible and not cc_visible:
        raise PreventUpdate
    
    # Determine if cell_store data changed (plots need to be regenerated)
    cell_store_changed = "cell_store.data" in triggered_id
    
    # Get anode object (only when needed)
    config = ELECTRODE_CONFIGS[ElectrodeType.ANODE]
    cell = cache.get(cell_data["cache_key"])
    anode = get_object_from_cell(cell, config)
    
    if electrode_visible:
        # Generate plots for electrode tab
        plot_cross_section = anode.get_cross_section(title="Cross-Section Anode View")
        
        properties = anode.properties
        properties_table = create_properties_table(
            properties,
            table_id="anode_properties_table",
            decimal_places=2
        )
        
        # Always generate top-down plot if cell store changed or if it doesn't exist
        if cell_store_changed or not current_top_down_plot:
            plot_top_down = anode.get_top_down_view(title="Top-Down Anode View")
        else:
            plot_top_down = no_update
            
        return (
            plot_top_down,
            plot_cross_section,
            properties_table,
        )
    
    elif cc_visible:
        # Always generate top-down plot for CC tab (it's the main plot for this tab)
        plot_top_down = anode.get_top_down_view(title="Top-Down Anode View")
        
        # Only update other plots if cell store changed and they exist
        if cell_store_changed and current_cross_section_plot:
            plot_cross_section = anode.get_cross_section(title="Cross-Section Anode View")
            
            properties = anode.properties
            properties_table = create_properties_table(
                properties,
                table_id="anode_properties_table",
                decimal_places=2
            )
            
            return (
                plot_top_down,
                plot_cross_section,
                properties_table,
            )
        else:
            return plot_top_down, no_update, no_update
    
    else:
        raise PreventUpdate


