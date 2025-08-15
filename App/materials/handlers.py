from typing import Type, Tuple, List
from dash import no_update

from general.handlers import _build_basic_response, _add_dropdown_menu
from general.callback_helpers import generate_parameters
from general.cell_operations import set_cell_to_cache, set_object_to_cell

from steer_opencell_design.Components.CurrentCollectors import CurrentCollectorMaterial

from steer_core.Apps.Utils.SliderControls import create_slider_config
from steer_core.Apps.ContextManagers import capture_warnings


def handle_selector_update(
    material_name: str,
    cell: Type,
    config: Type,
    existing_warnings: List[str]
) -> Tuple:
    """
    Handle updates to the material selector.

    Parameters
    ----------
    material_selector : str
        The selected material name from the dropdown.
    cell : Type
        The current cell object from the cache.
    material_type : MaterialType
        The type of material being updated (e.g., CATHODE_CURRENT_COLLECTOR_TAB).
    """
    source = f"{config.__class__.__name__}_cell_store_update"
    with capture_warnings(existing_warnings, source=source, clear_source_warnings=True) as warnings_list:

        # get the material from the database using the selector
        new_material = config.material_type.from_database(material_name)

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
    return (warnings_list,) + tuple(response)

