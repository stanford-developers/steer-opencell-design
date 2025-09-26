from dash import no_update, Input, Output, State, callback, ALL, ctx
from dash.exceptions import PreventUpdate

from App.cache_service import cache

from App.general.enumerated_classes import CollectorType, LayupType
from App.general.cell_operations import get_object_from_cell, set_object_to_cell, set_cell_to_cache
from App.layup.configs import LAYUP_CONFIGS
from App.layup.lists import LAYUP_DESIGNS
from App.layup.callback_helpers import create_layup_callback

from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, ZFoldMonoLayer, OverhangControlMode


@callback(
    [
        Output("layup_design", "options"),
        Output("layup_design_div", "style"),
        Output("layup_design", "value"),
    ],
    [
        Input("cell_store", "data"),
    ],
    [
        State("layup_design_div", "style"),
        State("layup_design", "options"),
    ],
    prevent_initial_call=True,
)
def update_layup_dropdown_options(data, current_style, current_options):
    """
    Update the cathode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the config of the item
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = cache.get(data["cache_key"])

    # get the current collector from the cell
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

    return config["options"], current_style, config["value"]


@callback(
    [
        Output("layup_plot", "figure"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input("layup_opacity_slider", "value"),  # Fixed: Changed from drag_value to value for better responsiveness
    ],
    [
        State("layup_plot", "figure"),  # Capture current figure state
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
    current_figure,  # Current figure state
    relayout_data,  # Current zoom/pan state
    restyle_data,  # Current legend visibility state
):
    """
    Update the layup plots based on the current data and opacity setting.
    Preserves zoom, pan, and legend visibility states when opacity changes.
    """

    # If all display is none for any of the viewing styles, return no update
    if any(d.get("display") == "none" for d in [tab_style, tabs_panel_style]):
        raise PreventUpdate

    # Get the configuration
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # get the layup from the cell
    layup = get_object_from_cell(cell, config)

    # get the figure with the specified opacity
    fig = layup.get_top_down_view(opacity=opacity_value)

    # Preserve legend visibility states from current figure if available
    if current_figure and "data" in current_figure:
        current_traces = current_figure["data"]
        # Match traces by name and legendgroup to preserve visibility
        for new_trace in fig.data:
            for old_trace in current_traces:
                # Match traces by name and legendgroup
                if getattr(new_trace, "name", None) == old_trace.get("name") and getattr(new_trace, "legendgroup", None) == old_trace.get("legendgroup"):
                    if "visible" in old_trace:
                        new_trace.visible = old_trace["visible"]
                    break

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

    # Fallback: Preserve legend visibility states from restyle_data if current_figure method didn't work
    if restyle_data and len(restyle_data) >= 2 and not current_figure:
        # restyle_data format: [{'visible': [True, False, ...]}, [trace_indices]]
        visibility_data = restyle_data[0]
        trace_indices = restyle_data[1]

        if "visible" in visibility_data:
            visible_states = visibility_data["visible"]

            # Handle both single trace and multiple trace cases
            if isinstance(trace_indices, list):
                # Multiple traces case
                for i, trace_idx in enumerate(trace_indices):
                    if i < len(visible_states) and trace_idx < len(fig.data):
                        fig.data[trace_idx].visible = visible_states[i]
            elif isinstance(trace_indices, int):
                # Single trace case
                if trace_indices < len(fig.data):
                    if isinstance(visible_states, list) and len(visible_states) > 0:
                        fig.data[trace_indices].visible = visible_states[0]
                    elif isinstance(visible_states, (bool, str)):
                        fig.data[trace_indices].visible = visible_states

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


@callback(
    [
        Output("cell_store", "data", allow_duplicate=True),
        Output("layup_control_mode_selector", "value"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("layup_control_mode_selector", "value"),
        Input("cell_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_layup_control_mode(
    tab_style,
    tabs_panel_style,
    selected_mode, 
    cell_data
):
    """
    Update the layup control mode based on the radio button selection,
    and update the radio button to reflect the current control mode.
    """
    # If all display is none for any of the viewing styles, return no update
    if any(d.get("display") == "none" for d in [tab_style, tabs_panel_style]):
        raise PreventUpdate
    
    # Get the configuration
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data["cache_key"])

    # Get the cathode from the cell
    layup = get_object_from_cell(cell, config)

    # get the mode map
    mode_mapping = {
        "FIXED_COMPONENT": OverhangControlMode.FIXED_COMPONENT,
        "FIXED_OVERHANGS": OverhangControlMode.FIXED_OVERHANGS,
    }

    # map the control mode to the UI string
    mode_reverse_mapping = {
        OverhangControlMode.FIXED_COMPONENT: "FIXED_COMPONENT",
        OverhangControlMode.FIXED_OVERHANGS: "FIXED_OVERHANGS",
    }

    if ctx.triggered_id == "cell_store":
        return no_update, mode_reverse_mapping.get(layup.overhang_control_mode)

    elif ctx.triggered_id == "layup_control_mode_selector":

        mode = mode_mapping.get(selected_mode, OverhangControlMode.FIXED_OVERHANGS)

        # set the control mode to the layup
        layup.overhang_control_mode = mode

        # set the cathode to the cell
        new_cell = set_object_to_cell(cell, layup, config)

        # set the new cell to the cache
        new_key = set_cell_to_cache(new_cell)

        return {"cache_key": new_key}, no_update


@callback(
    [
        Output("laminate_design_parameters", "style"),
        Output("zfold_design_parameters", "style"),
        Output("stacked_design_parameters", "style"),
    ],
    Input("layup_design", "value"),
    prevent_initial_call=True,
)
def update_layup_design_parameters(design):
    """
    Update the layup design parameters based on the current design selection.
    """
    styles = {"display": "none"}
    active_style = {"display": "block"}

    if design is None:
        return [no_update] * 3

    if design == "laminate":
        return [active_style, styles, styles]
    elif design == "z-fold":
        return [styles, active_style, styles]
    elif design == "stacked":
        return [styles, styles, active_style]


@callback(
    Output("cell_store", "data", allow_duplicate=True),
    Input("layup_design", "value"),
    State("cell_store", "data"),
    prevent_initial_call=True,
)
def update_layup_design(design_value, cell_data):
    """Handle current collector design changes and convert between types."""

    # Check if design_value or cell_data is None
    if not design_value or not cell_data:
        return no_update

    # if design_value is laminate, return no_update
    if design_value == "laminate":
        return no_update

    # Get current cell and collector
    cell = cache.get(cell_data["cache_key"])

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
        return no_update

    # Additional check: If this is likely triggered by cell upload (not user interaction)
    # Check if the current dropdown value already matches the collector type
    current_dropdown_value_map = {
        "ZFoldMonoLayer": "z-fold",
        "MonoLayer": "stacked",
    }

    expected_dropdown_value = current_dropdown_value_map.get(type_name)

    if design_value == expected_dropdown_value:
        return no_update

    # Import function to convert current collector
    from App.layup.callback_helpers import convert_layup
    from App.general.cell_operations import set_cell_to_cache

    # Do the conversion
    new_layup = convert_layup(layup, target_type_name)

    # Assign the new layup to the cell and get the key
    new_cell = set_object_to_cell(cell, new_layup, LAYUP_CONFIGS[LayupType.GENERIC])

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {"cache_key": new_key}


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"},"n_submit",),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "zfoldmonolayer", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
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
    original_input_steps,
):
    callback_function = create_layup_callback(LayupType.ZFOLDMONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[tabs_panel_style, main_tabs_container_style],
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "laminate", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "laminate", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input(
            {"object": "laminate", "property": ALL, "subtype": "input"},
            "n_submit",
        ),
        Input({"object": "laminate", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "laminate", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
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
    original_input_steps,
):
    callback_function = create_layup_callback(LayupType.LAMINATE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[tabs_panel_style, main_tabs_container_style],
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return response


@callback(
    [
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"},"value",),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "stacked", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "stacked", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
        Input("cell_store", "data"),
        Input(
            {"object": "stacked", "property": ALL, "subtype": "input"},
            "n_submit",
        ),
        Input({"object": "stacked", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "stacked", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
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
    original_input_steps,
):

    callback_function = create_layup_callback(LayupType.MONOLAYER)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[tabs_panel_style, main_tabs_container_style],
        original_values=original_values,
        original_mins=original_mins,
        original_maxs=original_maxs,
        original_slider_marks=original_slider_marks,
        original_slider_steps=original_slider_steps,
        original_input_steps=original_input_steps,
    )

    return response
