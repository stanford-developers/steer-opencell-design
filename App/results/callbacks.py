
import inspect
from dash import Input, Output, callback, State

from steer_core.Constants.Units import M_TO_MM

from App.general.callback_helpers import update_tab_styles
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType
from App.layup.configs import LAYUP_CONFIGS, LayupType


@callback(
    [
        Output("mechanicals_tab", "style"),
        Output("load_balancing_tab", "style"),
        Output("construction_tab", "style"),
        Output("results_tab", "style"),
        Output("warnings_tab", "style"),
    ],
    Input("results-tabs-container", "value"),
    [
        State("mechanicals_tab", "style"),
        State("load_balancing_tab", "style"),
        State("construction_tab", "style"),
        State("results_tab", "style"),
        State("warnings_tab", "style"),
    ],
    prevent_initial_call=True,
)
def update_results_tabs(active_tab, mechanicals_style, load_balancing_style, construction_style, results_style, warnings_style):
    """
    Update the display style of results tabs based on the selected tab.
    """
    tab_names = ["mechanicals", "load_balancing", "construction", "results", "warnings"]

    current_styles = [
        mechanicals_style,
        load_balancing_style,
        construction_style,
        results_style,
        warnings_style,
    ]
    
    return update_tab_styles(active_tab, tab_names, current_styles)


##############################
#### Current Collector Graphs ####
##############################

@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cathode_a_side", "figure"),
        Output("cathode_b_side", "figure"),
    ],
    Input({"type": "trigger", "callback": "update_cathode_mechanicals_plots"}, "data"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_cathode_mechanicals_plots(trigger_data, cell_data):
    """
    Update both cathode A side and B side current collector graphs.
    """
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get cathode current collector
    cathode_collector = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.CATHODE])
    
    # Get both A side and B side view figures from the current collector
    fig_a_side = cathode_collector.get_a_side_view(title="Cathode A-Side")
    fig_b_side = cathode_collector.get_b_side_view(title="Cathode B-Side")
    
    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name,) + (fig_a_side, fig_b_side)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("anode_a_side", "figure"),
        Output("anode_b_side", "figure"),
    ],
    Input({"type": "trigger", "callback": "update_anode_mechanicals_plots"}, "data"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_anode_mechanicals_plots(trigger_data, cell_data):
    """
    Update both anode A side and B side current collector graphs.
    """
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get anode current collector
    anode_collector = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.ANODE])
    
    # Get both A side and B side view figures from the current collector
    fig_a_side = anode_collector.get_a_side_view(title="Anode A-Side")
    fig_b_side = anode_collector.get_b_side_view(title="Anode B-Side")
    
    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name,) + (fig_a_side, fig_b_side)


##############################
#### Cross Section Graphs ####
##############################

@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cathode_cross_section", "figure"),
    ],
    Input({"type": "trigger", "callback": "update_cathode_cross_section"}, "data"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_cathode_cross_section(trigger_data, cell_data):
    """
    Update cathode cross section plot.
    """
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get both cathode and anode electrodes to calculate y-axis range
    cathode = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.CATHODE])
    anode = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.ANODE])
    
    # Calculate y-axis range as max thickness * 1.2
    cathode_thickness = cathode._thickness
    anode_thickness = anode._thickness
    max_thickness = max(cathode_thickness, anode_thickness)
    max_thickness = max_thickness * M_TO_MM
    y_axis_range = [-max_thickness/2 * 1.2, max_thickness/2 * 1.2]
    
    # Generate cross section figure
    fig = cathode.get_cross_section(y_axis_range=y_axis_range, title="Cathode Cross Section")
    
    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name, fig)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("anode_cross_section", "figure"),
    ],
    Input({"type": "trigger", "callback": "update_anode_cross_section"}, "data"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_anode_cross_section(trigger_data, cell_data):
    """
    Update anode cross section plot.
    """
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get both cathode and anode electrodes to calculate y-axis range
    cathode = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.CATHODE])
    anode = get_object_from_cell(cell, ELECTRODE_CONFIGS[ElectrodeType.ANODE])
    
    # Calculate y-axis range as max thickness * 1.2
    cathode_thickness = cathode._thickness
    anode_thickness = anode._thickness
    max_thickness = max(cathode_thickness, anode_thickness)
    max_thickness = max_thickness * M_TO_MM
    y_axis_range = [-max_thickness/2 * 1.2, max_thickness/2 * 1.2]
    
    # Generate cross section figure
    fig = anode.get_cross_section(y_axis_range=y_axis_range, title="Anode Cross Section")

    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name, fig)


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("areal_capacity_plot", "figure"),
    ],
    Input({"type": "trigger", "callback": "update_areal_capacity_plot"}, "data"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_areal_capacity_plot(trigger_data, cell_data):
    """
    Update areal capacity plot.
    """
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get the layup object
    layup = get_object_from_cell(cell, LAYUP_CONFIGS[LayupType.GENERIC])
    
    # Get the areal capacity plot
    fig = layup.get_areal_capacity_plot(title="Areal Capacity")

    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name, fig)


##############################
#### Construction Graphs ####
##############################

@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("layup_design_figure", "figure"),
    ],
    [
        Input({"type": "trigger", "callback": "update_layup_design_figure"}, "data"),
        Input("layup_design_opacity_slider", "drag_value"),
    ],
    [
        State("cell_store", "data"),
        State("layup_design_figure", "figure"),
    ],
    prevent_initial_call=True,
)
def update_layup_design_figure(trigger_data, opacity_value, cell_data, current_figure):
    """
    Update layup design figure with opacity control and zoom preservation.
    """
    from dash import ctx
    
    # Get cell from cache
    cell_key = cell_data["cache_key"]
    cell = get_cell_from_cache(cell_key)
    
    # Get the layup object
    layup = get_object_from_cell(cell, LAYUP_CONFIGS[LayupType.GENERIC])
    
    # Check if layup object exists
    if layup is None:
        callback_name = inspect.currentframe().f_code.co_name
        # Return empty figure or current figure if layup is not available
        if current_figure is not None:
            return (callback_name, current_figure)
        else:
            # Return a minimal empty figure
            from plotly.graph_objects import Figure
            empty_fig = Figure()
            empty_fig.update_layout(title="Layup Design - No Data Available")
            return (callback_name, empty_fig)
    
    # Always generate new figure with current opacity value
    # Pass opacity value directly to the method
    fig = layup.get_top_down_view(title="Layup Design", opacity=opacity_value)
    
    # Check if current figure has data - if empty, return fresh figure with auto-scaled axes
    current_figure_has_data = (current_figure is not None and 
                              'data' in current_figure and 
                              current_figure['data'] and 
                              len(current_figure['data']) > 0)
    
    # Only preserve zoom settings and legend selections if current figure has actual data
    if current_figure_has_data and 'layout' in current_figure:
        current_layout = current_figure['layout']
        # Preserve zoom settings
        if 'xaxis' in current_layout and 'range' in current_layout['xaxis']:
            fig['layout']['xaxis']['range'] = current_layout['xaxis']['range']
        if 'yaxis' in current_layout and 'range' in current_layout['yaxis']:
            fig['layout']['yaxis']['range'] = current_layout['yaxis']['range']
        
        # Preserve legend selections (trace visibility)
        if 'data' in current_figure and 'data' in fig:
            current_traces = current_figure['data']
            new_traces = fig['data']
            
            # Match traces by name and preserve visibility
            for i, new_trace in enumerate(new_traces):
                if i < len(current_traces):
                    current_trace = current_traces[i]
                    # Check if the trace names match (if they have names)
                    if ('name' in new_trace and 'name' in current_trace and 
                        new_trace['name'] == current_trace['name']):
                        # Preserve visibility setting
                        if 'visible' in current_trace:
                            new_trace['visible'] = current_trace['visible']
                    elif 'name' not in new_trace and 'name' not in current_trace:
                        # If no names, match by position and preserve visibility
                        if 'visible' in current_trace:
                            new_trace['visible'] = current_trace['visible']
    
    callback_name = inspect.currentframe().f_code.co_name
    
    return (callback_name, fig)
    