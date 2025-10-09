from dash import callback, Input, Output, ALL, State
import inspect
from App.materials.callback_helpers import create_material_callback
from App.materials.configs import MaterialType


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "input"}, "step"),
        Output("cathode_current_collector_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_current_collector_material"}, "data"),
        Input("cathode_current_collector_material_selector", "value"),
        Input({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    response = response

    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "material", "property": ALL, "subtype": "input"}, "step"),
        Output("anode_current_collector_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_current_collector_material"}, "data"),
        Input("anode_current_collector_material_selector", "value"),
        Input({"electrode": "anode", "object": "material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_anode_current_collector_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_material_callback(MaterialType.ANODE_CURRENT_COLLECTOR)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values
    )

    response = response
    
    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "input"}, "step"),
        Output("cathode_current_collector_tab_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_current_collector_tab_material"}, "data"),
        Input("cathode_current_collector_tab_material_selector", "value"),
        Input({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "tab_material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_tab_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR_TAB)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "input"}, "step"),
        Output("anode_current_collector_tab_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_current_collector_tab_material"}, "data"),
        Input("anode_current_collector_tab_material_selector", "value"),
        Input({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "tab_material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_anode_current_collector_tab_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    callback_function = create_material_callback(MaterialType.ANODE_CURRENT_COLLECTOR_TAB)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    callback_name = inspect.currentframe().f_code.co_name
    return (callback_name, ) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "step"),
        Output("cathode_insulation_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_cathode_current_collector_insulation_material"}, "data"),
        Input("cathode_insulation_material_selector", "value"),
        Input({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "cathode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_cathode_current_collector_insulation_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_material_callback(MaterialType.CATHODE_INSULATION)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "step"),
        Output("anode_insulation_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_anode_current_collector_insulation_material"}, "data"),
        Input("anode_insulation_material_selector", "value"),
        Input({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"electrode": "anode", "object": "insulation_material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_anode_current_collector_insulation_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    callback_name = inspect.currentframe().f_code.co_name
    
    callback_function = create_material_callback(MaterialType.ANODE_INSULATION)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    return (callback_name,) + response


@callback(
    [
        Output("last_triggered", "data", allow_duplicate=True),
        Output("warnings_store", "data", allow_duplicate=True),
        Output("cell_store", "data", allow_duplicate=True),
        Output("old_cell_store", "data", allow_duplicate=True),

        Output({"object": "separator_material", "property": ALL, "subtype": "slider"}, "value"),
        Output({"object": "separator_material", "property": ALL, "subtype": "slider"}, "min"),
        Output({"object": "separator_material", "property": ALL, "subtype": "slider"}, "max"),
        Output({"object": "separator_material", "property": ALL, "subtype": "slider"}, "marks"),
        Output({"object": "separator_material", "property": ALL, "subtype": "slider"}, "step"),
        Output({"object": "separator_material", "property": ALL, "subtype": "input"}, "step"),
        Output("separator_material_selector", "value"),
    ],
    [
        Input({"type": "trigger", "callback": "update_separator_material"}, "data"),
        Input("separator_material_selector", "value"),
        Input({"object": "separator_material", "property": ALL, "subtype": "input"}, "n_submit"),
        Input({"object": "separator_material", "property": ALL, "subtype": "input"}, "n_blur"),
        Input({"object": "separator_material", "property": ALL, "subtype": "slider"}, "value"),
    ],
    [
        State("cell_store", "data"),
        State({"object": "separator_material", "property": ALL, "subtype": "input"}, "value"),
        State("warnings_store", "data"),
    ],
    prevent_initial_call=True,
)
def update_separator_material(
    trigger_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    cell_data,
    input_values,
    existing_warnings,
):
    callback_name = inspect.currentframe().f_code.co_name

    callback_function = create_material_callback(MaterialType.SEPARATOR_MATERIAL)

    response = callback_function(
        existing_warnings,
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    return (callback_name, ) + response


