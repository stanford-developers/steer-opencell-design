from time import time
import inspect
from dash import callback, Input, Output, State, no_update, ALL
from dash.exceptions import PreventUpdate

from App.general.cache_service import cache

from App.formulations.callback_helpers import (
    create_generic_formulation_callback,
    create_generic_formulation_div_callback,
)
from App.formulations.configs import FORMULATION_CONFIGS, FormulationType
from App.general.cell_operations import get_object_from_cell
from App.general.callback_helpers import create_properties_table, prevent_update_from_styles

from steer_core.Apps.ContextManagers import capture_warnings


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_formulation_main"}, "data"),
        Input({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "formulation", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_cathode_formulation_main(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_generic_formulation_callback(FormulationType.CATHODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_formulation_main"}, "data"),
        Input({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "formulation", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_anode_formulation_main(
    trigger_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):

    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_generic_formulation_callback(FormulationType.ANODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL}, "style"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "options"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "value"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_formulation_div"}, "data"),
        Input({"electrode": "cathode", "object": "formulation", "action": ALL, "material": ALL}, "n_clicks"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "n_submit"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "n_blur"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State("warnings_store", "data"),
        State({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL}, "style"),
        State({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        State({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "value"),
        State("cathode-active-material-div", "children"),
        State("cathode-binder-div", "children"),
        State("cathode-conductive-additive-div", "children"),
        State("cathode_active_material_store", "data"),
        State("anode_active_material_store", "data"),
        State({"electrode": "cathode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "value"),
    ],
    prevent_initial_call=True,
)
def update_cathode_formulation_div(
    trigger_data,
    action_button_clicks,
    dropdown_values,
    weight_fraction_n_sub,
    weight_fraction_n_blur,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    existing_warnings,
    all_div_styles,
    all_dropdown_values,
    all_weight_fractions,
    active_material_div_children,
    binder_div_children,
    conductive_additive_div_children,
    cathode_material_options,
    anode_material_options,
    input_values,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_generic_formulation_div_callback(FormulationType.CATHODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        all_div_styles,
        all_dropdown_values,
        all_weight_fractions,
        active_material_div_children,
        binder_div_children,
        conductive_additive_div_children,
        cathode_material_options,
        anode_material_options,
        slider_values=slider_values,
        input_values=input_values,
    )

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL}, "style"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "options"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "value"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "step"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_formulation_div"}, "data"),
        Input({"electrode": "anode", "object": "formulation", "action": ALL, "material": ALL}, "n_clicks"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "n_submit"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "n_blur"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State("warnings_store", "data"),
        State({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL}, "style"),
        State({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "dropdown"}, "value"),
        State({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "subtype": "weight_fraction"}, "value"),
        State("anode-active-material-div", "children"),
        State("anode-binder-div", "children"),
        State("anode-conductive-additive-div", "children"),
        State("cathode_active_material_store", "data"),
        State("anode_active_material_store", "data"),
        State({"electrode": "anode", "object": "formulation", "material": ALL, "index": ALL, "property": ALL, "subtype": "input"}, "value"),
    ],
    prevent_initial_call=True,
)
def update_anode_formulation_div(
    trigger_data,
    action_button_clicks,
    dropdown_values,
    weight_fraction_n_sub,
    weight_fraction_n_blur,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    existing_warnings,
    all_div_styles,
    all_dropdown_values,
    all_weight_fractions,
    active_material_div_children,
    binder_div_children,
    conductive_additive_div_children,
    cathode_material_options,
    anode_material_options,
    input_values,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_generic_formulation_div_callback(FormulationType.ANODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        all_div_styles,
        all_dropdown_values,
        all_weight_fractions,
        active_material_div_children,
        binder_div_children,
        conductive_additive_div_children,
        cathode_material_options,
        anode_material_options,
        slider_values=slider_values,
        input_values=input_values,
    )

    return (callback_name, ) + response

