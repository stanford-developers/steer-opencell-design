from typing import List, Dict, Any, Tuple, NamedTuple, Type
from dash import no_update
from itertools import chain
from copy import deepcopy

from App.formulations.configs import FormulationConfig
from App.general.callback_helpers import generate_parameters, create_no_update_response
from App.general.cell_operations import set_object_to_cell, set_cell_to_cache
from App.general.database_service import BINDER_MATERIALS, CONDUCTIVE_ADDITIVE_MATERIALS
from App.general.handlers import determine_value
from App.materials.configs import MaterialType, MATERIAL_CONFIGS, MaterialConfig
from App.general.enumerated_classes import SubType

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)

from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)

from steer_core.Apps.Utils.SliderControls import create_slider_config
from steer_core.Apps.ContextManagers import capture_warnings


def update_div_visibility(div_styles: List[Dict[str, Any]], visible_count: int) -> None:
    """Update div visibility based on the number that should be visible."""

    for i, style in enumerate(div_styles):
        style["display"] = "block" if i < visible_count else "none"


def get_slider_config(material, material_config: MaterialConfig):
    """Get slider configuration for a material based on its config."""

    # Get the parameter list and their min/max values
    parameter_list, min_values, max_values = generate_parameters(material, material_config)

    # Create and return the slider configuration
    slider_config = create_slider_config(min_values, max_values, parameter_list)

    return slider_config


def get_slider_configs_from_material_dict(material_dict: Dict[CathodeMaterial | AnodeMaterial | Binder | ConductiveAdditive, float]):
    """Get slider configurations for all materials in the dictionary."""

    if not material_dict:
        return []

    # Get the material types in the dictionary
    key_types = {type(key) for key in material_dict.keys()}

    # Check they are all the same type and get the material type
    if len(key_types) != 1:
        raise ValueError("All keys in material_dict must be of the same type.")
    else:
        material_type = key_types.pop()

    # Get the material config based on the material type
    material_config = get_material_config(material_type)

    slider_configs = [get_slider_config(material, material_config) for material in material_dict.keys()]

    return slider_configs


def get_material_config(material_type: Type) -> MaterialConfig:
    """Get the appropriate material config based on the material instance."""

    if material_type == CathodeMaterial:
        material_type = MaterialType.CATHODE_ACTIVE_MATERIAL
    elif material_type == AnodeMaterial:
        material_type = MaterialType.ANODE_ACTIVE_MATERIAL
    elif material_type == Binder:
        material_type = MaterialType.BINDER
    elif material_type == ConductiveAdditive:
        material_type = MaterialType.CONDUCTIVE_ADDITIVE

    return MATERIAL_CONFIGS[material_type]


def get_zero_response_material(material_config: MaterialConfig) -> Tuple:
    """Build a response tuple with zeroed values based on the material config."""

    # get the number of parameters
    num_params = len(material_config.parameter_list)

    # get the parameters
    parameter_list = [0 for _ in range(num_params)]
    min_vals = [0.0 for _ in range(num_params)]
    max_vals = [1.0 for _ in range(num_params)]

    # create the slider configs
    slider_configs = create_slider_config(min_vals, max_vals, parameter_list)

    return slider_configs


def flatten_slider_configs(
    active_materials_configs: List[Dict[str, List[float]]],
    binder_configs: List[Dict[str, List[float]]],
    conductive_configs: List[Dict[str, List[float]]],
) -> Tuple[List, ...]:
    """Flatten slider responses from all material categories"""

    values = []
    mins = []
    maxs = []
    marks = []
    slider_steps = []
    input_steps = []

    for am in active_materials_configs:
        values.append(am["grid_slider_vals"])
        mins.append(am["min_vals"])
        maxs.append(am["max_vals"])
        marks.append(am["mark_vals"])
        slider_steps.append(am["step_vals"])
        input_steps.append(am["input_step_vals"])

    for b in binder_configs:
        values.append(b["grid_slider_vals"])
        mins.append(b["min_vals"])
        maxs.append(b["max_vals"])
        marks.append(b["mark_vals"])
        slider_steps.append(b["step_vals"])
        input_steps.append(b["input_step_vals"])

    for c in conductive_configs:
        values.append(c["grid_slider_vals"])
        mins.append(c["min_vals"])
        maxs.append(c["max_vals"])
        marks.append(c["mark_vals"])
        slider_steps.append(c["step_vals"])
        input_steps.append(c["input_step_vals"])

    values = [item for sublist in values for item in sublist]
    mins = [item for sublist in mins for item in sublist]
    maxs = [item for sublist in maxs for item in sublist]
    marks = [item for sublist in marks for item in sublist]
    slider_steps = [item for sublist in slider_steps for item in sublist]
    input_steps = [item for sublist in input_steps for item in sublist]

    return values, mins, maxs, marks, slider_steps, input_steps


def get_formulation_response(
    formulation: CathodeFormulation | AnodeFormulation,
    n_active_div: int,
    n_binder_div: int,
    n_conductive_div: int,
):
    # get the number of materials in each category
    n_active = len(formulation.active_materials)
    n_binder = len(formulation.binders)
    n_conductive = len(formulation.conductive_additives)

    # create the dropdown values response
    active_dropdown_values = [material.name for material in formulation.active_materials.keys()] + [None] * (n_active_div - n_active)
    binder_dropdown_values = [material.name for material in formulation.binders.keys()] + [None] * (n_binder_div - n_binder)
    conductive_dropdown_values = [material.name for material in formulation.conductive_additives.keys()] + [None] * (n_conductive_div - n_conductive)
    dropdown_values_response = active_dropdown_values + binder_dropdown_values + conductive_dropdown_values

    # create the weight fractions response
    active_weight_fractions = list(formulation.active_materials.values()) + [0] * (n_active_div - n_active)
    binder_weight_fractions = list(formulation.binders.values()) + [0] * (n_binder_div - n_binder)
    conductive_weight_fractions = list(formulation.conductive_additives.values()) + [0] * (n_conductive_div - n_conductive)
    weight_fractions_response = active_weight_fractions + binder_weight_fractions + conductive_weight_fractions

    # create the slider responses
    material_config = get_material_config(type(list(formulation.active_materials.keys())[0]))
    active_slider_configs = get_slider_configs_from_material_dict(formulation.active_materials) + [get_zero_response_material(material_config)] * (n_active_div - n_active)
    binder_slider_configs = get_slider_configs_from_material_dict(formulation.binders) + [get_zero_response_material(MATERIAL_CONFIGS[MaterialType.BINDER])] * (n_binder_div - n_binder)
    conductive_slider_configs = get_slider_configs_from_material_dict(formulation.conductive_additives) + [get_zero_response_material(MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE])] * (n_conductive_div - n_conductive)
    flattened_slider_responses = flatten_slider_configs(active_slider_configs, binder_slider_configs, conductive_slider_configs)

    return (
        dropdown_values_response,
        weight_fractions_response,
        flattened_slider_responses,
    )


def create_no_update_response(
    formulation: CathodeFormulation | AnodeFormulation,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
) -> Tuple:
    # Get the number of material divs in each category
    n_active_div = len(active_div_styles)
    n_binder_div = len(binder_div_styles)
    n_conductive_div = len(conductive_div_styles)

    # slideroutputs lengths
    active_n_response = len(MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL].parameter_list) if type(formulation) == CathodeFormulation else len(MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL].parameter_list)
    binder_n_response = len(MATERIAL_CONFIGS[MaterialType.BINDER].parameter_list)
    conductive_n_response = len(MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE].parameter_list)

    return (
        no_update,
        no_update,
        no_update,
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
        [no_update] * (n_active_div * active_n_response + n_binder_div * binder_n_response + n_conductive_div * conductive_n_response),
    )


def replace_material_key_by_index(materials_dict: Dict, index: int, new_material):
    """Replace material at index i with new material, keeping same weight fraction.
    If index is out of range, add material to end with weight fraction of 0."""
    items = list(materials_dict.items())

    # If index is within range, replace existing material
    if 0 <= index < len(items):
        old_material, weight_fraction = items[index]
        items[index] = (new_material, weight_fraction)
    else:
        # If index is out of range, add to end with weight fraction of 0
        items.append((new_material, 0.0))

    # Update dictionary
    materials_dict.clear()
    materials_dict.update(items)

    return materials_dict


def update_formulation_material_at_index(formulation, category: str, index: int, new_material):
    """Update specific material in formulation by index"""
    if category == "active_material":
        active_materials_dict = deepcopy(formulation.active_materials)
        new_active_materials_dict = replace_material_key_by_index(active_materials_dict, index, new_material)
        formulation.active_materials = new_active_materials_dict
    elif category == "binder":
        binder_materials_dict = deepcopy(formulation.binders)
        new_binder_materials = replace_material_key_by_index(binder_materials_dict, index, new_material)
        formulation.binders = new_binder_materials
    elif category == "conductive_additive":
        conductive_additives_dict = deepcopy(formulation.conductive_additives)
        new_conductive_additives = replace_material_key_by_index(conductive_additives_dict, index, new_material)
        formulation.conductive_additives = new_conductive_additives
    return formulation


def update_formulation_weight_fraction_at_index(formulation, category: str, index: int, new_weight_fraction: float):
    """Update specific material weight fraction in formulation by index"""
    if category == "active_material":
        active_materials_dict = deepcopy(formulation.active_materials)
        if 0 <= index < len(active_materials_dict):
            material = list(active_materials_dict.keys())[index]
            active_materials_dict[material] = new_weight_fraction
            formulation.active_materials = active_materials_dict
    elif category == "binder":
        binder_materials_dict = deepcopy(formulation.binders)
        if 0 <= index < len(binder_materials_dict):
            material = list(binder_materials_dict.keys())[index]
            binder_materials_dict[material] = new_weight_fraction
            formulation.binders = binder_materials_dict
    elif category == "conductive_additive":
        conductive_additives_dict = deepcopy(formulation.conductive_additives)
        if 0 <= index < len(conductive_additives_dict):
            material = list(conductive_additives_dict.keys())[index]
            conductive_additives_dict[material] = new_weight_fraction
            formulation.conductive_additives = conductive_additives_dict
    return formulation


def handle_cell_store_update_materials(
    existing_warnings: List[str],
    formulation: CathodeFormulation | AnodeFormulation,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
    cathode_active_options: List[str],
    anode_active_options: List[str],
) -> Tuple[Any, Any, List[Any], List[Any], List[Any]]:
    """
    Create MaterialSelector components based on formulation structure.

    This function processes formulation data and returns all necessary UI component
    values for the cathode/anode formulation interface, including div styles,
    dropdown options/values, weight fractions, and slider configurations.

    Args:
        existing_warnings: List of existing warnings
        formulation: The electrode formulation object
        formulation_config: Configuration for the formulation type
        active_div_styles: Styles for active material divs
        binder_div_styles: Styles for binder divs
        conductive_div_styles: Styles for conductive additive divs
        cathode_active_options: Available cathode active materials
        anode_active_options: Available anode active materials

    Returns:
        Tuple containing (warnings, cell_store, div_styles, dropdown_options,
        dropdown_values, weight_fractions, *slider_responses)
    """
    # Get the number of material divs in each category
    n_active_div = len(active_div_styles)
    n_binder_div = len(binder_div_styles)
    n_conductive_div = len(conductive_div_styles)

    # get the number of materials in each category
    n_active = len(formulation.active_materials)
    n_binder = len(formulation.binders)
    n_conductive = len(formulation.conductive_additives)

    # make that number of styles visible and turn to response
    update_div_visibility(active_div_styles, n_active)
    update_div_visibility(binder_div_styles, n_binder)
    update_div_visibility(conductive_div_styles, n_conductive)
    div_style_response = active_div_styles + binder_div_styles + conductive_div_styles

    # create the dropdown options response
    active_dropdown_options = [cathode_active_options if type(formulation) == CathodeFormulation else anode_active_options] * n_active_div
    binder_dropdown_options = [BINDER_MATERIALS] * n_binder_div
    conductive_dropdown_options = [CONDUCTIVE_ADDITIVE_MATERIALS] * n_conductive_div
    dropdown_options_response = active_dropdown_options + binder_dropdown_options + conductive_dropdown_options

    (
        dropdown_values_response,
        weight_fractions_response,
        flattened_slider_responses,
    ) = get_formulation_response(formulation, n_active_div, n_binder_div, n_conductive_div)

    return (
        no_update,
        no_update,
        no_update,
        div_style_response,
        dropdown_options_response,
        dropdown_values_response,
        weight_fractions_response,
    ) + flattened_slider_responses


def handle_add_material_div(
    trigger_id: Dict[str, str | float],
    formulation: CathodeFormulation | AnodeFormulation,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
):
    # Get the number of material divs in each category
    n_active_div = len(active_div_styles)
    n_binder_div = len(binder_div_styles)
    n_conductive_div = len(conductive_div_styles)

    # get the number of visible divs in each category
    n_active = sum(1 for style in active_div_styles if style.get("display") != "none")
    n_binder = sum(1 for style in binder_div_styles if style.get("display") != "none")
    n_conductive = sum(1 for style in conductive_div_styles if style.get("display") != "none")

    # get the button action type and the material category
    material_category = trigger_id.get("material")

    # if add button then make one more div visible
    if material_category == "active_material":
        update_div_visibility(active_div_styles, n_active + 1)
        div_response = active_div_styles + [no_update] * n_binder_div + [no_update] * n_conductive_div
    elif material_category == "binder":
        update_div_visibility(binder_div_styles, n_binder + 1)
        div_response = [no_update] * n_active_div + binder_div_styles + [no_update] * n_conductive_div
    elif material_category == "conductive_additive":
        update_div_visibility(conductive_div_styles, n_conductive + 1)
        div_response = [no_update] * n_active_div + [no_update] * n_binder_div + conductive_div_styles

    # create a default no update response
    default_response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))

    # modify the style response in the default response
    default_response[3] = div_response

    # return response
    return tuple(default_response)


def handle_remove_material(
    existing_warnings: List[str],
    trigger_id: Dict[str, str | float],
    cell: Any,
    cell_key: str,
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
):
    # Get the number of material divs in each category
    n_active_div = len(active_div_styles)
    n_binder_div = len(binder_div_styles)
    n_conductive_div = len(conductive_div_styles)

    # get the number of visible divs in each category
    n_active = sum(1 for style in active_div_styles if style.get("display") != "none")
    n_binder = sum(1 for style in binder_div_styles if style.get("display") != "none")
    n_conductive = sum(1 for style in conductive_div_styles if style.get("display") != "none")

    # get the button action type and the material category
    material_category = trigger_id.get("material")

    # if remove button and more than one div visible then make one less div visible
    if material_category == "active_material" and n_active > 1 and (n_active - 1) >= len(formulation.active_materials):
        update_div_visibility(active_div_styles, n_active - 1)
        div_response = active_div_styles + [no_update] * n_binder_div + [no_update] * n_conductive_div
        default_response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))
        default_response[3] = div_response
        return tuple(default_response)

    elif material_category == "binder" and n_binder > 0 and (n_binder - 1) >= len(formulation.binders):
        update_div_visibility(binder_div_styles, n_binder - 1)
        div_response = [no_update] * n_active_div + binder_div_styles + [no_update] * n_conductive_div
        default_response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))
        default_response[3] = div_response
        return tuple(default_response)

    elif material_category == "conductive_additive" and n_conductive > 0 and (n_conductive - 1) >= len(formulation.conductive_additives):
        update_div_visibility(conductive_div_styles, n_conductive - 1)
        div_response = [no_update] * n_active_div + [no_update] * n_binder_div + conductive_div_styles
        default_response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))
        default_response[3] = div_response
        return tuple(default_response)

    # If user trying to remove the last material in a category, return no update
    elif material_category == "active_material" and n_active == 1:
        return create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles)

    elif material_category == "active_material" and n_active == len(formulation.active_materials):
        # remove the last active material from the formulation
        active_materials = deepcopy(formulation.active_materials)
        material_to_remove = list(active_materials.keys())[-1]
        del active_materials[material_to_remove]

        # reassign the formulation active materials
        source = f"{formulation_config.__class__.__name__}_{material_category}"
        with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
            formulation.active_materials = active_materials

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, formulation, formulation_config)

        # set the cell to cache
        new_key = set_cell_to_cache(new_cell)

        # make one less div visible
        update_div_visibility(active_div_styles, n_active - 1)
        div_response = active_div_styles + [no_update] * n_binder_div + [no_update] * n_conductive_div

        # get the updated formulation response
        (
            dropdown_values_response,
            weight_fractions_response,
            flattened_slider_responses,
        ) = get_formulation_response(formulation, n_active_div, n_binder_div, n_conductive_div)

    elif material_category == "binder" and n_binder == len(formulation.binders):
        # remove the last binder from the formulation
        binders = deepcopy(formulation.binders)
        material_to_remove = list(binders.keys())[-1]
        del binders[material_to_remove]

        # reassign the formulation binders
        source = f"{formulation_config.__class__.__name__}_{material_category}"
        with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
            formulation.binders = binders

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, formulation, formulation_config)

        # set the cell to cache
        new_key = set_cell_to_cache(new_cell)

        # make one less div visible
        update_div_visibility(binder_div_styles, n_binder - 1)
        div_response = [no_update] * n_active_div + binder_div_styles + [no_update] * n_conductive_div

        # get the updated formulation response
        (
            dropdown_values_response,
            weight_fractions_response,
            flattened_slider_responses,
        ) = get_formulation_response(formulation, n_active_div, n_binder_div, n_conductive_div)

    elif material_category == "conductive_additive" and n_conductive == len(formulation.conductive_additives):
        # remove the last conductive additive from the formulation
        conductive_additives = deepcopy(formulation.conductive_additives)
        material_to_remove = list(conductive_additives.keys())[-1]
        del conductive_additives[material_to_remove]

        # reassign the formulation conductive additives
        source = f"{formulation_config.__class__.__name__}_{material_category}"
        with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
            formulation.conductive_additives = conductive_additives

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, formulation, formulation_config)

        # set the cell to cache
        new_key = set_cell_to_cache(new_cell)

        # make one less div visible
        update_div_visibility(conductive_div_styles, n_conductive - 1)
        div_response = [no_update] * n_active_div + [no_update] * n_binder_div + conductive_div_styles

        # get the updated formulation response
        (
            dropdown_values_response,
            weight_fractions_response,
            flattened_slider_responses,
        ) = get_formulation_response(formulation, n_active_div, n_binder_div, n_conductive_div)

    response = (
        warnings_list,
        {"cache_key": new_key},
        {"cache_key": cell_key},
        div_response,
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        dropdown_values_response,
        weight_fractions_response,
    ) + flattened_slider_responses

    return response


def handle_material_button_update(
    existing_warnings: List[str],
    cell,
    cell_key: str,
    trigger_id: Dict[str, str | float],
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
):
    """Handle add/remove material button clicks with clean, modular approach"""
    # get the button action type and the material category
    action_category = trigger_id.get("action")

    if action_category == "add":
        return handle_add_material_div(
            trigger_id,
            formulation,
            active_div_styles,
            binder_div_styles,
            conductive_div_styles,
        )

    elif action_category == "remove":

        return handle_remove_material(
            existing_warnings=existing_warnings,
            trigger_id=trigger_id,
            cell=cell,
            cell_key=cell_key,
            formulation=formulation,
            formulation_config=formulation_config,
            active_div_styles=active_div_styles,
            binder_div_styles=binder_div_styles,
            conductive_div_styles=conductive_div_styles,
        )


def handle_indexed_dropdown_update(
    cell: Any,
    cell_key: str,
    trigger_id: dict | str,
    existing_warnings: List[str],
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_dropdown_values: List[str],
    binder_dropdown_values: List[str],
    conductive_dropdown_values: List[str],
):
    """Handle updates triggered by material dropdown changes"""

    # Get values from the triggered ID
    triggered_index = int(trigger_id["index"])
    triggered_category = trigger_id["material"]

    # get new material
    if triggered_category == "active_material":
        material_name = active_dropdown_values[triggered_index]
        new_material = CathodeMaterial.from_database(material_name) if formulation_config.formulation_type == CathodeFormulation else AnodeMaterial.from_database(material_name)
    elif triggered_category == "binder":
        material_name = binder_dropdown_values[triggered_index]
        new_material = Binder.from_database(material_name)
    elif triggered_category == "conductive_additive":
        material_name = conductive_dropdown_values[triggered_index]
        new_material = ConductiveAdditive.from_database(material_name)

    source = f"{formulation_config.__class__.__name__}"
    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
        # get a new formulation with the updated material
        new_formulation = update_formulation_material_at_index(formulation, triggered_category, triggered_index, new_material)

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, new_formulation, formulation_config)

    # set the cell to cache
    new_key = set_cell_to_cache(new_cell)

    # get the updated formulation response
    n_active_div = len(active_dropdown_values)
    n_binder_div = len(binder_dropdown_values)
    n_conductive_div = len(conductive_dropdown_values)

    (
        dropdown_values_response,
        weight_fractions_response,
        flattened_slider_responses,
    ) = get_formulation_response(new_formulation, n_active_div, n_binder_div, n_conductive_div)

    return (
        existing_warnings,
        {"cache_key": new_key},
        {"cache_key": cell_key},
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        [no_update] * (n_active_div + n_binder_div + n_conductive_div),
        dropdown_values_response,
        weight_fractions_response,
    ) + flattened_slider_responses


def handle_weight_fraction_update(
    existing_warnings: List[str],
    cell: Any,
    trigger_id: Dict,
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_weight_fractions: List[float],
    binder_weight_fractions: List[float],
    conductive_weight_fractions: List[float],
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
):
    # get the index and category from the trigger
    triggered_index = int(trigger_id["index"])
    triggered_category = trigger_id["material"]

    # get the new weight fraction
    if triggered_category == "active_material":
        new_weight_fraction = active_weight_fractions[triggered_index]
    elif triggered_category == "binder":
        new_weight_fraction = binder_weight_fractions[triggered_index]
    elif triggered_category == "conductive_additive":
        new_weight_fraction = conductive_weight_fractions[triggered_index]

    source = f"{formulation_config.__class__.__name__}"
    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
        # get a new formulation with the updated weight fraction
        new_formulation = update_formulation_weight_fraction_at_index(formulation, triggered_category, triggered_index, new_weight_fraction)

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, new_formulation, formulation_config)

    # set the cell to cache
    new_key = set_cell_to_cache(new_cell)

    # get basic no response values
    response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))

    # update the warnings response
    response[0] = warnings_list

    # update the cell store response
    response[1] = {"cache_key": new_key}

    return tuple(response)


def handle_material_property_update(
    cell: Any,
    cell_key: str,
    trigger_id: Dict[str, str | float],
    existing_warnings: List[str],
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
    active_slider_values: List[float],
    binder_slider_values: List[float],
    conductive_slider_values: List[float],
    active_input_values: List[float],
    binder_input_values: List[float],
    conductive_input_values: List[float],
):
    # get the index and category from the trigger
    triggered_index = int(trigger_id["index"])
    triggered_category = trigger_id["material"]

    # get the material whose property is being updated
    if triggered_category == "active_material":
        material = list(formulation.active_materials.keys())[triggered_index]
        material_config = get_material_config(type(material))
        param_len = len(material_config.parameter_list)
        slider_values = active_slider_values[triggered_index * param_len : (triggered_index + 1) * param_len]
        input_values = active_input_values[triggered_index * param_len : (triggered_index + 1) * param_len]

    elif triggered_category == "binder":
        material = list(formulation.binders.keys())[triggered_index]
        material_config = MATERIAL_CONFIGS[MaterialType.BINDER]
        param_len = len(material_config.parameter_list)
        slider_values = binder_slider_values[triggered_index * param_len : (triggered_index + 1) * param_len]
        input_values = binder_input_values[triggered_index * param_len : (triggered_index + 1) * param_len]

    elif triggered_category == "conductive_additive":
        material = list(formulation.conductive_additives.keys())[triggered_index]
        material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]
        param_len = len(material_config.parameter_list)
        slider_values = conductive_slider_values[triggered_index * param_len : (triggered_index + 1) * param_len]
        input_values = conductive_input_values[triggered_index * param_len : (triggered_index + 1) * param_len]

    # determine the subtype from the triggered ID
    subtype = SubType(trigger_id["subtype"])

    # determine the property and subtype from the triggered ID
    property_name = trigger_id["property"]

    # determine the value from the inputs and the subtype
    value = determine_value(material_config, subtype, property_name, input_values, slider_values)

    # set the property on the material
    source = f"{formulation_config.__class__.__name__}"
    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:
        # set the property on the material
        setattr(material, property_name, value)

        # set the material dicts back to the formulation
        if triggered_category == "active_material":
            formulation.active_materials = formulation.active_materials
        elif triggered_category == "binder":
            formulation.binders = formulation.binders
        elif triggered_category == "conductive_additive":
            formulation.conductive_additives = formulation.conductive_additives

        # assign the formulation back to the cell
        new_cell = set_object_to_cell(cell, formulation, formulation_config)

        # update the cell in the store
        new_key = set_cell_to_cache(new_cell)

    # get the basic response
    response = list(create_no_update_response(formulation, active_div_styles, binder_div_styles, conductive_div_styles))

    # update the warnings response
    response[0] = warnings_list

    # update the cell store response
    response[1] = {"cache_key": new_key}

    # update the cell store response
    response[2] = {"cache_key": cell_key}

    if subtype == SubType.INPUT:
        response[7] = active_input_values + binder_input_values + conductive_input_values

    return response

