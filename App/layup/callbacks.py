from dash import no_update, Input, Output, State, callback, ALL

from App.cache_service import cache

from App.general.enumerated_classes import LayupType
from App.general.cell_operations import get_object_from_cell
from App.layup.configs import LAYUP_CONFIGS


@callback(
    [
        Output("layup_plot", "figure"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input(
            "layup_opacity_slider", "value"
        ),  # Fixed: Changed from drag_value to value for better responsiveness
    ],
    [
        State("layup_plot", "relayoutData"),  # Capture current zoom/pan state
        State("layup_plot", "restyleData"),  # Capture current legend visibility state
    ],
    prevent_initial_call=True,
)
def update_layup_plots(
    tab_style,
    tabs_panel_style,
    cell_data,
    opacity_value,  # Add opacity parameter
    relayout_data,  # Current zoom/pan state
    restyle_data,  # Current legend visibility state
):
    """
    Update the layup plots based on the current data and opacity setting.
    Preserves zoom, pan, and legend visibility states when opacity changes.
    """

    # If all display is none for any of the viewing styles, return no update
    if any(d.get("display") == "none" for d in [tab_style, tabs_panel_style]):
        return no_update

    # Get the configuration
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # get the layup from the cell
    layup = get_object_from_cell(cell, config)

    # get the figure with the specified opacity
    fig = layup.get_top_down_view(opacity=opacity_value)

    # Preserve the current view state if it exists
    if relayout_data:
        # Preserve zoom and pan settings
        layout_updates = {}

        # Preserve x-axis range
        if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
            layout_updates["xaxis_range"] = [
                relayout_data["xaxis.range[0]"],
                relayout_data["xaxis.range[1]"],
            ]
        elif "xaxis.range" in relayout_data:
            layout_updates["xaxis_range"] = relayout_data["xaxis.range"]

        # Preserve y-axis range
        if "yaxis.range[0]" in relayout_data and "yaxis.range[1]" in relayout_data:
            layout_updates["yaxis_range"] = [
                relayout_data["yaxis.range[0]"],
                relayout_data["yaxis.range[1]"],
            ]
        elif "yaxis.range" in relayout_data:
            layout_updates["yaxis_range"] = relayout_data["yaxis.range"]

        # Apply preserved layout settings
        fig.update_layout(**layout_updates)

    # Preserve legend visibility states if they exist
    if restyle_data and len(restyle_data) >= 2:
        # restyle_data format: [{'visible': [True, False, ...]}, [trace_indices]]
        visibility_data = restyle_data[0]
        trace_indices = restyle_data[1]

        if "visible" in visibility_data:
            visible_states = visibility_data["visible"]
            if isinstance(trace_indices, list):
                for i, trace_idx in enumerate(trace_indices):
                    if i < len(visible_states) and trace_idx < len(fig.data):
                        fig.data[trace_idx].visible = visible_states[i]

    return (fig,)


@callback(
    [
        Output("areal_capacity_design_plot", "figure"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_areal_capacity_plot(
    tab_style,
    tabs_panel_style,
    cell_data,
):
    """
    Update the areal capacity design plot based on the current data.
    """

    # If all display is none for any of the viewing styles, return no update
    if any(d.get("display") == "none" for d in [tab_style, tabs_panel_style]):
        return no_update

    # Get the configuration
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # get the layup from the cell
    layup = get_object_from_cell(cell, config)

    # get the areal capacity figure
    fig = layup.get_areal_capacity_plot()

    return (fig,)
