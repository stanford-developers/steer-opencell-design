
import inspect
from dash import Input, Output, callback, State
from App.general.callback_helpers import update_tab_styles
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType


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

