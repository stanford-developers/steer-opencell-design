import inspect
from dash import callback, Output, Input, State, no_update, ctx, ALL, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import time
import datetime as dt
from base64 import b64decode
from pickle import loads
from typing import List, Tuple, Dict, Callable, Any
import functools

from App.general.store import LANDING_PAGE_IMAGE_URLS

from App.general.callback_helpers import (
    get_internal_construction_options,
    get_electrochemical_reference_options,
    get_cell_name_options,
    get_active_materials,
    update_tab_styles
)

from App.general.cell_operations import get_cell_from_database, set_cell_to_cache


@callback(
    [
        Output("cathode_tab", "style"),
        Output("anode_tab", "style"),
        Output("layup_tab", "style"),
        Output("electrode_assembly_tab", "style"),
        Output("warnings_tab", "style"),
    ],
    Input("main-tabs-container", "value"),
    [
        State("cathode_tab", "style"),
        State("anode_tab", "style"),
        State("layup_tab", "style"),
        State("electrode_assembly_tab", "style"),
        State("warnings_tab", "style"),
    ],
    prevent_initial_call=True,
)
def show_main_tab_content(
    active_tab,
    cathode_style,
    anode_style,
    layup_style,
    electrode_assembly_style,
    warnings_style,
) -> List:
    """
    Function to show or hide main content based on the active tab.
    Only updates styles when the display property needs to change.
    """
    tab_names = ["cathode", "anode", "layup", "electrode_assembly", "warnings"]

    current_styles = [
        cathode_style,
        anode_style,
        layup_style,
        electrode_assembly_style,
        warnings_style,
    ]
    
    return update_tab_styles(active_tab, tab_names, current_styles)


@callback(
    [
        Output("cathode_current_collector_tab", "style"),
        Output("cathode_formulation_tab", "style"),
        Output("cathode_electrode_tab", "style"),
    ],
    Input("cathode-tabs-container", "value"),
    [
        State("cathode_current_collector_tab", "style"),
        State("cathode_formulation_tab", "style"),
        State("cathode_electrode_tab", "style"),
    ],
    prevent_initial_call=True,
)
def show_cathode_tab_content(
    active_tab,
    current_collector_style,
    formulation_style,
    electrode_style,
):
    """
    Function to show or hide cathode sub-tab content based on the active tab.
    Only updates styles when the display property needs to change.
    """
    tab_names = ["cathode_current_collector", "cathode_formulation", "cathode_electrode"]
    current_styles = [current_collector_style, formulation_style, electrode_style]
    return update_tab_styles(active_tab, tab_names, current_styles)


@callback(
    [
        Output("anode_current_collector_tab", "style"),
        Output("anode_formulation_tab", "style"),
        Output("anode_electrode_tab", "style"),
    ],
    Input("anode-tabs-container", "value"),
    [
        State("anode_current_collector_tab", "style"),
        State("anode_formulation_tab", "style"),
        State("anode_electrode_tab", "style"),
    ],
    prevent_initial_call=True,
)
def show_anode_tab_content(
    active_tab,
    current_collector_style,
    formulation_style,
    electrode_style,
):
    """
    Function to show or hide anode sub-tab content based on the active tab.
    Only updates styles when the display property needs to change.
    """
    tab_names = ["anode_current_collector", "anode_formulation", "anode_electrode"]
    current_styles = [current_collector_style, formulation_style, electrode_style]
    return update_tab_styles(active_tab, tab_names, current_styles)


@callback(
    [
        Output("layup_mechanicals_layout", "style"),
        Output("layup_areal_layout", "style"),
    ],
    Input("layup-tabs-container", "value"),
    [
        State("layup_mechanicals_layout", "style"),
        State("layup_areal_layout", "style"),
    ],
    prevent_initial_call=True,
)
def show_layup_tab_content(
    active_tab,
    current_mechanicals_style,
    current_areal_style,
):
    """
    Function to show or hide layup sub-tab content based on the active tab.
    Only updates styles when the display property needs to change.
    """
    tab_names = ["layup_mechanicals_layout", "layup_areal_layout"]
    current_styles = [current_mechanicals_style, current_areal_style]
    return update_tab_styles(active_tab, tab_names, current_styles)


@callback(
    [
        Output("internal_construction_dropdown", "options"),
        Output("form_factor_dropdown", "value"),
    ],
    [
        Input("form_factor_dropdown", "value"),
        Input({"type": "cell_schematic_button", "key": ALL}, "n_clicks"),
    ],
    [
        State("form_factor_dropdown", "options"),
    ],
    prevent_initial_call=True,
)
def update_internal_construction_options(
    form_factor, 
    form_factor_schematic_button_clicks, 
    form_factor_options
    ) -> Tuple[List[dict], str]:
    
    # get the triggered ID to determine which input caused the callback
    trigger = ctx.triggered_id

    # If the form factor dropdown is triggered, return options based on the selected form factor
    if trigger == "form_factor_dropdown":
        return get_internal_construction_options(form_factor), no_update

    # If a cell schematic button is clicked, return options based on the button key
    elif isinstance(trigger, dict) and trigger["type"] == "cell_schematic_button":
        form_factor = trigger["key"]

        # If the form factor is not in the options, return no update
        if form_factor not in [option["value"] for option in form_factor_options]:
            return no_update, no_update

        # Otherwise, return the options based on the form factor
        return get_internal_construction_options(form_factor), form_factor

    else:
        # If no valid trigger, return no update
        return no_update, no_update


@callback(
    [
        Output("electrochemical_reference_dropdown", "options"),
        Output("internal_construction_dropdown", "value"),
    ],
    [
        Input("internal_construction_dropdown", "value"),
        Input({"type": "cell_schematic_button", "key": ALL}, "n_clicks"),
    ],
    [
        State("form_factor_dropdown", "value"),
        State("internal_construction_dropdown", "options"),
    ],
    prevent_initial_call=True,
)
def update_electrochemical_reference_options(
    internal_construction,
    internal_construction_button_clicks,
    form_factor,
    internal_construction_options,
):
    trigger = ctx.triggered_id

    # If the internal construction dropdown is triggered, return options based on the selected internal construction
    if trigger == "internal_construction_dropdown":
        return (
            get_electrochemical_reference_options(internal_construction, form_factor),
            no_update,
        )

    elif isinstance(trigger, dict) and trigger["type"] == "cell_schematic_button":
        internal_construction = trigger["key"]

        # If the internal construction is not in the options, return no update
        if internal_construction not in [option["value"] for option in internal_construction_options]:
            return no_update, no_update

        # Otherwise, return the options based on the internal construction and form factor
        return (
            get_electrochemical_reference_options(internal_construction, form_factor),
            internal_construction,
        )

    else:
        # If no valid trigger, return no update
        return no_update, no_update


@callback(
    [
        Output("cell_name_dropdown", "options"),
        Output("electrochemical_reference_dropdown", "value"),
        Output("cathode_active_material_store", "data"),
        Output("anode_active_material_store", "data"),
    ],
    [
        Input("electrochemical_reference_dropdown", "value"),
        Input({"type": "cell_schematic_button", "key": ALL}, "n_clicks"),
    ],
    [
        State("internal_construction_dropdown", "value"),
        State("form_factor_dropdown", "value"),
        State("electrochemical_reference_dropdown", "options"),
    ],
    prevent_initial_call=True,
)
def update_cell_name_options_and_store_active_material_names(
    electrochemical_reference,
    electrochemical_reference_button_clicks,
    internal_construction,
    form_factor,
    electrochemical_reference_options,
):
    trigger = ctx.triggered_id

    # If the electrochemical reference dropdown is triggered, return options based on the selected electrochemical reference
    if trigger == "electrochemical_reference_dropdown":
        cathode_materials = get_active_materials(electrochemical_reference, "cathode")
        anode_materials = get_active_materials(electrochemical_reference, "anode")
        cell_names = get_cell_name_options(internal_construction, electrochemical_reference, form_factor)
        return cell_names, no_update, cathode_materials, anode_materials

    elif isinstance(trigger, dict) and trigger["type"] == "cell_schematic_button":
        electrochemical_reference = trigger["key"]

        # If the electrochemical reference is not in the options, return no update
        if electrochemical_reference not in [option["value"] for option in electrochemical_reference_options]:
            return no_update, no_update, no_update, no_update

        # Get active materials for the schematic button trigger
        cathode_materials = get_active_materials(electrochemical_reference, "cathode")
        anode_materials = get_active_materials(electrochemical_reference, "anode")
        cell_names = get_cell_name_options(internal_construction, electrochemical_reference, form_factor)
        return cell_names, electrochemical_reference, cathode_materials, anode_materials

    else:
        return no_update, no_update, no_update, no_update


@callback(
    [
        Output({"type": "cell_schematic_image", "key": ALL}, "style"),
    ],
    [
        Input("form_factor_dropdown", "options"),
        Input("internal_construction_dropdown", "options"),
        Input("electrochemical_reference_dropdown", "options"),
        Input("form_factor_dropdown", "value"),
        Input("internal_construction_dropdown", "value"),
        Input("electrochemical_reference_dropdown", "value"),
    ],
    [
        State({"type": "cell_schematic_image", "key": ALL}, "style"),
    ],
)
def update_landing_image_alpha(
    form_factor_options,
    internal_construction_options,
    electrochemical_reference_options,
    form_factor_value,
    internal_construction_value,
    electrochemical_reference_value,
    current_styles,
):
    
    # Ensure current_styles is initialized correctly
    if not current_styles:
        current_styles = [{"width": "40%", "opacity": "20%"} for _ in LANDING_PAGE_IMAGE_URLS]

    # Flatten options into a single list
    available_options = [item["value"] for item in form_factor_options + internal_construction_options + electrochemical_reference_options]

    # Reset all styles to default opacity (10%)
    for style in current_styles:
        style["opacity"] = "10%"

    # Update styles for matching keys in available options
    for idx, key in enumerate(LANDING_PAGE_IMAGE_URLS.keys()):
        if key in available_options:
            current_styles[idx]["opacity"] = "50%"  # Set to 50% if key is in available options

        # Set opacity to 100% if the key matches any of the value inputs
        if key in [
            form_factor_value,
            internal_construction_value,
            electrochemical_reference_value,
        ]:
            current_styles[idx]["opacity"] = "100%"

    return [current_styles]


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True)
    ],
    [
        Input("cell_name_dropdown", "value")
    ],
    prevent_initial_call=True,
)
def load_cell_from_name_dropdown(cell_name: str) -> Dict:
    """
    Callback to fetch the cell from the database based on the selected cell name.

    Parameters
    ----------
    contents : str
        The selected cell name from the dropdown.
    """
    # get the name of this callback
    callback_name = inspect.currentframe().f_code.co_name
    
    if cell_name is None:
        raise PreventUpdate

    cell = get_cell_from_database(cell_name)
    new_key = set_cell_to_cache(cell)

    return (callback_name, {"cache_key": new_key})


@callback(
    [Output("cell_store", "data", allow_duplicate=True)],
    [Input("upload_cell", "contents")],
    prevent_initial_call=True,
)
def upload_cell(pickled_cell):
    """
    Callback to handle the upload of a cell object from a file.

    Parameters
    ----------
    pickled_cell : str
        The base64 encoded string of the pickled cell object.

    Returns
    -------
    List[Dict]
        A list containing a dictionary with the cache key of the uploaded cell.
    """
    from App.general.callback_helpers import set_cell_to_cache

    # If pickled_cell is None, return no update
    if pickled_cell is None:
        return no_update

    # Extract the uploaded file content
    content_type, content_string = pickled_cell.split(",")

    # Decode the base64 content
    try:
        decoded_data = b64decode(b64decode(content_string))
    except Exception as decode_error:
        print(f"Error decoding base64 content: {decode_error}")
        return no_update

    cell = loads(decoded_data)

    new_key = set_cell_to_cache(cell)

    # Return the cache key to update the store
    return [{"cache_key": new_key}]


@callback(
    [
        Output("cell_type_panel", "style"),
        Output("tabs_panel", "style"),
    ],
    [
        Input("continue_to_design", "n_clicks"),
        Input("back_to_cell_type", "n_clicks"),
    ],
    [
        State("cell_type_panel", "style"),
        State("tabs_panel", "style"),
    ],
    prevent_initial_call=True,
)
def show_and_hide_cell_type_and_tabs(continue_clicks, back_clicks, continue_style, back_style):
    """
    Show or hide the cell type and tabs based on button clicks.
    Only updates styles when the display property needs to change.
    """
    ctx_id = ctx.triggered_id

    # Determine target display values based on button clicked
    if ctx_id == "continue_to_design":
        target_continue_display = "none"
        target_back_display = "block"
    elif ctx_id == "back_to_cell_type":
        target_continue_display = "flex"
        target_back_display = "none"
    else:
        # No valid trigger, return no updates
        return no_update, no_update

    # Check current display values and only update if needed
    current_continue_display = (continue_style or {}).get("display")
    current_back_display = (back_style or {}).get("display")

    # Update continue_style only if needed
    if current_continue_display == target_continue_display:
        updated_continue_style = no_update
    else:
        updated_continue_style = {**(continue_style or {}), "display": target_continue_display}

    # Update back_style only if needed
    if current_back_display == target_back_display:
        updated_back_style = no_update
    else:
        updated_back_style = {**(back_style or {}), "display": target_back_display}

    return updated_continue_style, updated_back_style


@callback(
    Output("warnings_tab", "children"),
    Input("warnings_store", "data"),
)
def update_warnings_tab(warnings_data):
    if not warnings_data:
        return html.Div(
            [
                html.Br(),
                html.Br(),
                html.H4("No Warnings"),
            ]
        )

    warning_cards = []

    for warning in warnings_data:
        severity_color = {
            "Warning": "warning",
            "Error": "danger",
            "UserWarning": "info",
        }.get(warning["category"], "secondary")

        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H5(f"{warning['category']}", className=f"text-{severity_color}"),
                        html.Small(
                            dt.datetime.fromtimestamp(warning["timestamp"]).strftime("%H:%M:%S"),
                            className="text-muted",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.P(warning["message"]),
                        html.Small(
                            f"Source: {warning.get('source', 'Unknown')}",
                            className="text-muted",
                        ),
                    ]
                ),
            ],
            className=f"border-{severity_color} mb-2",
        )

        warning_cards.append(card)

    return html.Div(
        [
            html.Br(),
            html.Br(),
            *warning_cards,
            html.Br(),
        ]
    )


@callback(
    Output("main-tabs-container", "children"),
    Input("warnings_store", "data"),
    State("main-tabs-container", "children"),
)
def update_warnings_tab_label(warnings_data, current_tabs):
    """Update the warnings tab label to show warning count."""
    warning_count = len(warnings_data) if warnings_data else 0

    # Update the warnings tab label
    for tab in current_tabs:
        if tab["props"]["value"] == "warnings":
            if warning_count > 0:
                tab["props"]["label"] = f"Warnings ({warning_count})"
            else:
                tab["props"]["label"] = "Warnings"

    return current_tabs

