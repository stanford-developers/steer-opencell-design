
import dash as ds
from dash import Input, Output, callback
from App.results.layouts import results_sidebar

@callback(
    Output("results_sidebar_container", "children"),
    Input("tabs_panel", "style"),
    prevent_initial_call=True,
)
def populate_results_sidebar(tabs_panel_style):
    """
    Populate the results sidebar when the main tabs panel is displayed.
    """
    if tabs_panel_style.get("display") == "none":
        return []
    
    return [results_sidebar]

@callback(
    [
        Output("mechanicals_tab", "style"),
        Output("load_balancing_tab", "style"),
        Output("construction_tab", "style"),
        Output("results_tab", "style"),
    ],
    Input("results-tabs-container", "value"),
    prevent_initial_call=True,
)
def update_results_tabs(active_tab):
    """
    Update the display style of results tabs based on the selected tab.
    """
    styles = {
        "mechanicals": {"display": "none", "padding-top": "20px"},
        "load_balancing": {"display": "none", "padding-top": "20px"},
        "construction": {"display": "none", "padding-top": "20px"},
        "results": {"display": "none", "padding-top": "20px"},
    }
    
    if active_tab in styles:
        styles[active_tab]["display"] = "block"
    
    return [
        styles["mechanicals"],
        styles["load_balancing"], 
        styles["construction"],
        styles["results"],
    ]


# @callback(
#     [
#         Output("cathode_current_collector_properties_div", "children"),
#     ],
#     [
#         Input("cathode_current_collector_tab", "style"),
#         Input("cathode_tab", "style"),
#         Input("tabs_panel", "style"),
#         Input("cell_store", "data"),
#     ],
#     prevent_initial_call=True,
# )
# def update_cathode_current_collector_properties(cc_tab_style, tab_style, tabs_panel_style, cell_data):
#     """
#     Update the cathode current collector plots based on the current collector store data.
#     """
#     # If all display is none for any of the viewing styles, return no update
#     prevent_update_from_styles([cc_tab_style, tab_style, tabs_panel_style])

#     # get the config for the cathode generic current collector
#     config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

#     # get the cell from the cache
#     cell = cache.get(cell_data["cache_key"])

#     # get the current collector from the cell
#     current_collector = get_object_from_cell(cell, config)

#     # get the current collector properties
#     properties = current_collector.properties

#     # Create properties table using utility function
#     properties_table = create_properties_table(
#         properties,
#         table_id="cathode_current_collector_properties_table",
#         decimal_places=2,
#     )

#     # return the plots
#     return [properties_table]


# @callback(
#     [
#         Output("anode_current_collector_properties_div", "children"),
#     ],
#     [
#         Input("anode_current_collector_tab", "style"),
#         Input("anode_tab", "style"),
#         Input("tabs_panel", "style"),
#         Input("cell_store", "data"),
#     ],
#     prevent_initial_call=True,
# )
# def update_anode_current_collector_properties(cc_tab_style, tab_style, tabs_panel_style, cell_data):
#     """
#     Update the anode current collector plots based on the current collector store data.
#     """
#     # If all display is none for any of the viewing styles, return no update
#     prevent_update_from_styles([cc_tab_style, tab_style, tabs_panel_style])

#     config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

#     # get the cell from the cache
#     cell = cache.get(cell_data["cache_key"])

#     # get the current collector from the cell
#     current_collector = get_object_from_cell(cell, config)

#     # get the current collector properties
#     properties = current_collector.properties

#     # Create properties table using utility function
#     properties_table = create_properties_table(
#         properties,
#         table_id="anode_current_collector_properties_table",
#         decimal_places=2,
#     )

#     # return the plots
#     return [properties_table]


