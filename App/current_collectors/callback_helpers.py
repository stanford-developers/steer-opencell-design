from typing import Type, List, Tuple
from dash import no_update, ctx

from OpenCell.Materials.CurrentCollectors import *

from general.enumerated_classes import *
from general.callback_helpers import get_cell_from_cache
from general.trigger_router import TriggerRouter, TriggerType

from current_collectors.configs import COLLECTOR_CONFIGS
from current_collectors.parameter_lists import CC_MATERIAL_PARAMETER_LIST
from current_collectors.current_collector_handlers import *


# =============================================================================
# Current Collector Callback Helpers
# =============================================================================

def create_no_update_response(config: Type) -> Tuple:
    """Create a no_update response for a given collector configuration."""
    num_params = len(config.parameter_list)
    num_range_params = len(config.range_slider_parameters) if config.range_slider_parameters else 0
    
    response = [
        no_update,  # cache_key (single value)
        [no_update] * num_params,  # input values (list)
        [no_update] * num_params,  # slider values (list)
        [no_update] * num_params,  # slider mins (list)
        [no_update] * num_params,  # slider maxs (list)
        [no_update] * num_params,  # input mins (list)
        [no_update] * num_params,  # input maxs (list)
        [no_update] * num_params,  # marks (list)
    ]
    
    # Add range slider outputs if applicable
    if config.range_slider_parameters:
        response.extend([
            [no_update] * num_range_params,  # rangeslider values (list)
            [no_update] * num_range_params,  # input_start values (list)
            [no_update] * num_range_params,  # input_end values (list)
            [no_update] * num_range_params,  # rangeslider mins (list)
            [no_update] * num_range_params,  # rangeslider maxs (list)
            [no_update] * num_range_params,  # rangeslider marks (list)
        ])
    
    # Add no_update for RadioItems and text input (only for tabbed collector)
    if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
        response.append(no_update)  # RadioItems
        response.append(no_update)  # Text input
    
    return tuple(response)

def create_generic_current_collector_callback(config_key: CollectorType, electrode_key: ElectrodeType) -> callable:
    """Factory function to create current collector callbacks."""
    
    config = COLLECTOR_CONFIGS[config_key]
    
    def generic_update_current_collector(
        cell_data, 
        input_values, 
        slider_values, 
        flip_x, 
        flip_y,
        rangeslider_values=None, 
        input_start_values=None, 
        input_end_values=None,
        tab_weld_side=None,
        tab_positions_text=None  # Add this parameter
    ) -> Tuple:
        
        from current_collectors.cell_operations import get_current_collector_from_cell

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the current collector from the cell, either cathode or anode depending on electrode
        current_collector = get_current_collector_from_cell(cell, electrode_key)

        # If the current collector is not of the right type, then return no_updates 
        if type(current_collector) != config.collector_type:
            return create_no_update_response(config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(current_collector, config)
        
        # trigger if the weld_tab_side selector is updated
        elif trigger_type == TriggerType.RADIOITEM:
            return handle_side_selector_update(triggered_id, current_collector, config, cell, tab_weld_side)
        
        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:

            return handle_property_update(
                triggered_id, current_collector, config, cell,
                input_values, slider_values, rangeslider_values,
                input_start_values, input_end_values, tab_positions_text
            )
        
        # trigger if an action is performed, e.g. flip
        elif trigger_type == TriggerType.ACTION:
            return handle_flip_action(triggered_id, current_collector, config, cell)
        
        # Fallback
        return create_no_update_response(config)

    return generic_update_current_collector

def convert_current_collector(current_collector: Type, target_type_name: str):
    """Convert current collector from one type to another using from_* constructors."""
    
    # Get the current type name
    current_type_name = type(current_collector).__name__

    # Define conversion methods for each source -> target combination
    conversion_map = {
        # From NotchedCurrentCollector  
        ('NotchedCurrentCollector', 'TablessCurrentCollector'): lambda cc: TablessCurrentCollector.from_notched(cc),
        ('NotchedCurrentCollector', 'TabWeldedCurrentCollector'): lambda cc: TabWeldedCurrentCollector.from_notched(cc),
        
        # From TablessCurrentCollector
        ('TablessCurrentCollector', 'NotchedCurrentCollector'): lambda cc: NotchedCurrentCollector.from_tabless(cc),
        ('TablessCurrentCollector', 'TabWeldedCurrentCollector'): lambda cc: TabWeldedCurrentCollector.from_tabless(cc),
        
        # From TabWeldedCurrentCollector
        ('TabWeldedCurrentCollector', 'NotchedCurrentCollector'): lambda cc: NotchedCurrentCollector.from_tab_welded(cc),
        ('TabWeldedCurrentCollector', 'TablessCurrentCollector'): lambda cc: TablessCurrentCollector.from_tab_welded(cc),
    }

    # Generate the conversion key
    conversion_key = (current_type_name, target_type_name)

    # create the function to convert
    converter = conversion_map[conversion_key]

    # create the new current collector using the converter
    new_current_collector = converter(current_collector)

    return new_current_collector



# =============================================================================
# Current Collector Materials Helpers
# =============================================================================

def create_material_no_update_response() -> Tuple:
    """Create a no_update response specifically for material callbacks."""
    # Material callbacks have exactly 7 outputs:
    # 1. cache_key (single value)
    # 2. material_selector value (single value) 
    # 3. input values (list)
    # 4. slider values (list)
    # 5. slider mins (list)
    # 6. slider maxs (list)
    # 7. marks (list)
    
    num_material_params = len(CC_MATERIAL_PARAMETER_LIST)  # Should be 2
    
    return (
        no_update,  # cache_key
        no_update,  # material_selector value
        [no_update] * num_material_params,  # input values
        [no_update] * num_material_params,  # slider values
        [no_update] * num_material_params,  # slider mins
        [no_update] * num_material_params,  # slider maxs
        [no_update] * num_material_params,  # marks
    )

def create_material_callback(material_type: MaterialType) -> callable:
    """Factory for creating material update callbacks."""

    def update_material(cell_data, material_name, input_values, slider_values):

        from current_collectors.material_handlers import (
            handle_cell_store_update, 
            handle_selector_update, 
            handle_property_update
        )

        # get the triggered ID
        triggered_id = ctx.triggered_id

        # get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # Get the trigger type using the TriggerRouter
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(cell, material_type)

        elif trigger_type == TriggerType.COMPONENT_SELECTOR:
            return handle_selector_update(material_name, cell, material_type)

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(triggered_id, cell, material_type, slider_values, input_values)

        return create_material_no_update_response()

    return update_material


