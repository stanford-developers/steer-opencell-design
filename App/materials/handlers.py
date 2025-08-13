from typing import Type, Tuple
from dash import no_update

from general.handlers import _build_basic_response, _add_dropdown_menu
from general.callback_helpers import generate_parameters
from general.cell_operations import set_cell_to_cache, set_object_to_cell

from steer_opencell_design.Components.CurrentCollectors import CurrentCollectorMaterial

from steer_core.Apps.Utils.SliderControls import create_slider_config


def handle_selector_update(
    material_name: str,
    cell: Type,
    config: Type,
) -> Tuple:
    """
    Handle updates to the material selector.

    Parameters
    ----------s
    material_selector : str
        The selected material name from the dropdown.
    cell : Type
        The current cell object from the cache.
    material_type : MaterialType
        The type of material being updated (e.g., CATHODE_CURRENT_COLLECTOR_TAB).
    """
    # get the material from the database using the selector
    new_material = CurrentCollectorMaterial.from_database(material_name)

    # get the parameters for the material
    parameter_list, min_values, max_values = generate_parameters(new_material, config)

    # Create slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)

    # set the material to the cell
    new_cell = set_object_to_cell(cell, new_material, config)
    
    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # Build the base response
    response = _build_basic_response(slider_configs, new_key)

    # Add optional components based on configuration
    _add_dropdown_menu(response, new_material, config)

    # return the new cell cache key, material name, and parameters
    return response

