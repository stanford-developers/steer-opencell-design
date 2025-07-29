from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import Type, List, Optional, Tuple
from dash import no_update, ctx

from cache_service import cache
from uuid import uuid4

from OpenCell.Materials.CurrentCollectors import *
from general.enumerated_classes import *


PUNCHED_PARAMETER_LIST = [
    'width',
    'height',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_position',
    'coated_tab_height',
    'insulation_width',
    'cost',
    'mass',
    'coated_area',
    'insulation_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

PUNCHED_SETTABLE_PARAMETERS = [
    'width',
    'height',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_position',
    'coated_tab_height',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]


NOTCHED_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_spacing',
    'tab_gap',
    'coated_tab_height',
    'insulation_width',
    'cost',
    'mass',
    'coated_area',
    'insulation_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

NOTCHED_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_spacing',
    'tab_gap',
    'coated_tab_height',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]


TABLESS_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'coated_width',
    'tab_height',
    'insulation_width',
    'cost',
    'mass',
    'coated_area',
    'insulation_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

TABLESS_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'coated_width',
    'tab_height',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]


TABBED_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_length',
    'tab_overhang',
    'skip_coat_width',
    'cost',
    'mass',
    'coated_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

TABBED_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_length',
    'tab_overhang',
    'tab_weld_side',
    'skip_coat_width',
    'datum_x',
    'datum_y',
    'datum_z',
]


TAPE_RANGE_SLIDER_PARAMETERS = [
    'a_side_coated_section',
    'b_side_coated_section',
]

CC_MATERIAL_PARAMETER_LIST = [
    'density',
    'specific_cost',
]


@dataclass
class CurrentCollectorConfig:
    """Configuration for different current collector types."""
    collector_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    range_slider_parameters: Optional[List[str]] = None


# Define configurations
COLLECTOR_CONFIGS = {
    CollectorType.PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        parameter_list=PUNCHED_PARAMETER_LIST,
        settable_parameters=PUNCHED_SETTABLE_PARAMETERS
    ),
    CollectorType.NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        parameter_list=NOTCHED_PARAMETER_LIST,
        settable_parameters=NOTCHED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    ),
    CollectorType.TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        parameter_list=TABLESS_PARAMETER_LIST,
        settable_parameters=TABLESS_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    ),
    CollectorType.TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        parameter_list=TABBED_PARAMETER_LIST,
        settable_parameters=TABBED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    )
}

class TriggerRouter:
    """Routes callback triggers to appropriate handlers using enums."""
    
    @staticmethod
    def get_trigger_type(triggered_id) -> TriggerType:
        """Determine the type of trigger."""
        
        if triggered_id == TriggerType.CELL_STORE.value:
            return TriggerType.CELL_STORE
        
        elif isinstance(triggered_id, dict):

            if 'subtype' in triggered_id:
                subtype = triggered_id['subtype']
                
                # Handle RadioItems separately
                if subtype == SubType.RADIOITEM.value:
                    return TriggerType.RADIOITEM
                
                # All other subtypes with 'property' are property updates
                elif 'property' in triggered_id:
                    return TriggerType.PROPERTY
                
                else:
                    print(f"❌ DEBUG TriggerRouter: Subtype '{subtype}' without property not matched")
            
            elif 'property' in triggered_id:
                return TriggerType.PROPERTY
            
            elif 'action' in triggered_id:
                return TriggerType.ACTION
            
            else:
                print(f"❌ DEBUG TriggerRouter: Dict has no recognized keys")

        else:
            print(f"❌ DEBUG TriggerRouter: Not a string or dict")
        
        print(f"❌ DEBUG TriggerRouter: No match found, raising ValueError")
        raise ValueError(f"Unknown trigger type: {triggered_id}")

  
# Update create_no_update_response to include text input
def create_no_update_response(config: CurrentCollectorConfig) -> Tuple:
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

def handle_cell_store_update(current_collector, config: CurrentCollectorConfig) -> Tuple:
    """Handle cell store update for any collector type."""
    
    # IMPORTANT: Validate all dependent properties first
    validate_dependent_properties(
        current_collector, 
        config.settable_parameters, 
        None
    )
    
    # Generate basic parameters
    value_list, min_values, max_values, marks_list = generate_parameters(
        current_collector, 
        config.parameter_list
    )
    
    # Start building response
    response = [
        no_update,  # cache_key stays the same
        value_list,  # input values
        value_list,  # slider values
        min_values,  # slider mins
        max_values,  # slider maxs
        min_values,  # input mins
        max_values,  # input maxs
        marks_list,  # marks
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            current_collector, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input (ONLY for tabbed collectors)
    if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
        response.append(current_collector.tab_weld_side)
        
        # Use consistent property name
        tab_positions = getattr(current_collector, 'weld_tab_positions', [])
        formatted_text = format_tab_positions(tab_positions)
        response.append(formatted_text)
    
    return tuple(response)

def handle_property_update(
    triggered_id: dict,
    current_collector,
    config: CurrentCollectorConfig,
    cell: Type,
    input_values: list,
    slider_values: list,
    rangeslider_values: list = None,
    input_start_values: list = None,
    input_end_values: list = None,
    tab_positions_text: str = None  # Add this parameter
) -> Tuple:
    """Handle property updates for any collector type."""
    
    property_name = triggered_id['property']
    subtype = SubType(triggered_id['subtype']) 

    # Handle text input for tab positions
    if subtype == SubType.TEXT_INPUT and property_name == 'weld_tab_positions':
        positions = parse_tab_positions(tab_positions_text)
        setattr(current_collector, property_name, positions)
    
    # Handle range slider properties
    elif config.range_slider_parameters and property_name in config.range_slider_parameters:

        range_property_index = config.range_slider_parameters.index(property_name)
        
        if subtype == SubType.RANGESLIDER:
            value = rangeslider_values[range_property_index]
        elif subtype == SubType.INPUT_START:
            current_value = getattr(current_collector, property_name)
            value = (input_start_values[range_property_index], current_value[1])
        elif subtype == SubType.INPUT_END:
            current_value = getattr(current_collector, property_name)
            value = (current_value[0], input_end_values[range_property_index])
        
        setattr(current_collector, property_name, value)
    
    # Handle regular slider/input properties
    elif property_name in config.parameter_list:
        property_index = config.parameter_list.index(property_name)
        if subtype == SubType.SLIDER:
            value = slider_values[property_index]
        elif subtype == SubType.INPUT:
            value = input_values[property_index]
        setattr(current_collector, property_name, value)
    
    # Validate dependent properties
    validate_dependent_properties(current_collector, config.settable_parameters, property_name)
    
    # Generate updated parameters
    value_list, min_values, max_values, marks_list = generate_parameters(
        current_collector, config.parameter_list
    )
    
    # Update cache
    new_cache_key = set_current_collector_to_cell(cell, current_collector)
    
    # Build response
    response = [
        {'cache_key': new_cache_key},
        value_list,
        value_list,
        min_values,
        max_values,
        min_values,
        max_values,
        marks_list,
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            current_collector, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input (ONLY for tabbed collectors)
    if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
        response.append(current_collector.tab_weld_side)
        
        # Add formatted tab positions text
        tab_positions = getattr(current_collector, 'weld_tab_positions', [])
        response.append(format_tab_positions(tab_positions))
    
    return tuple(response)

def handle_flip_action(
    triggered_id: dict,
    current_collector,
    config: CurrentCollectorConfig,
    cell: dict
) -> Tuple:
    """Handle flip actions for any collector type."""
    
    action = ActionType(triggered_id['action']) 

    # Perform the flip using enum
    if action == ActionType.FLIP_X:
        current_collector.flip(axis='x')
    elif action == ActionType.FLIP_Y:
        current_collector.flip(axis='y')
    
    # Update cache
    new_cache_key = set_current_collector_to_cell(cell, current_collector)
    
    # Create the standard no_update response but replace the cache_key
    response = list(create_no_update_response(config))
    response[0] = {'cache_key': new_cache_key}  # Replace the first element (cache_key)
    
    return tuple(response)

def generate_parameters(
    object, 
    parameter_list: list
) -> Tuple[List[float], List[float], List[float], List[Dict[int, str]]]:
    """Generate parameter lists for any collector."""
    parameter_values = []
    min_values = []
    max_values = []
    marks_list = []
    
    # Now use the enum
    categorical_properties = {prop.value for prop in CategoricalProperty}
    
    for param in parameter_list:
        if param in categorical_properties:
            # Handle categorical properties
            parameter_values.append(getattr(object, param))
            min_values.append(0)
            max_values.append(1)
            marks_list.append({})
        else:
            # Handle numerical properties
            parameter_values.append(getattr(object, param))
            min_values.append(getattr(object, f"{param}_range")[0])
            max_values.append(getattr(object, f"{param}_range")[1])
            marks_list.append(getattr(object, f"{param}_marks"))
    
    return parameter_values, min_values, max_values, marks_list

def generate_rangeslider_values(
        object, 
        range_params: list
    ) -> Tuple[List[Tuple[float, float]], List[float], List[float], List[float], List[float], List[Dict[int, str]]]:
    """Generate range slider values for any collector."""
    if not range_params:
        return [], [], [], [], [], []

    parameter_list = [getattr(object, param) for param in range_params]
    start_list = [p[0] for p in parameter_list]
    end_list = [p[1] for p in parameter_list]
    min_val = [getattr(object, f"{param}_range")[0] for param in range_params]
    max_val = [getattr(object, f"{param}_range")[1] for param in range_params]
    range_marks_list = [getattr(object, f"{param}_marks") for param in range_params]
    return parameter_list, start_list, end_list, min_val, max_val, range_marks_list

def validate_dependent_properties(object, settable_params: list, updated_property: str) -> None:
    """Validate and clamp dependent properties to their valid ranges."""
    for param in settable_params:
        if param != updated_property:
            try:
                param_range = getattr(object, f"{param}_range")
                param_value = getattr(object, param)
                if param_value < param_range[0]:
                    setattr(object, param, param_range[0])
                elif param_value > param_range[1]:
                    setattr(object, param, param_range[1])
            except AttributeError:
                # Handle case where range doesn't exist
                continue

def handle_side_selector_update(
    triggered_id: dict,
    current_collector,
    config: CurrentCollectorConfig,
    cell: Type,
    tab_weld_side: str
) -> Tuple:
    """Handle side selector (RadioItems) updates."""
    
    property_name = triggered_id['property']
    
    if property_name == 'tab_weld_side':
        setattr(current_collector, property_name, tab_weld_side)
    
    # Update cache
    new_cache_key = set_current_collector_to_cell(cell, current_collector)
    
    # Generate updated parameters
    value_list, min_values, max_values, marks_list = generate_parameters(
        current_collector, config.parameter_list
    )
    
    # Build response
    response = [
        {'cache_key': new_cache_key},
        value_list,
        value_list,
        min_values,
        max_values,
        min_values,
        max_values,
        marks_list,
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            current_collector, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input
    response.append(current_collector.tab_weld_side)
    
    # Add formatted tab positions text
    tab_positions = getattr(current_collector, 'tab_positions', [])
    response.append(format_tab_positions(tab_positions))
    
    return tuple(response)

def parse_tab_positions(text_input: str) -> List[float]:
    """Parse comma-separated tab positions from text input."""
    if not text_input or not text_input.strip():
        return []
    
    try:
        # Split by comma and clean up whitespace
        positions = [x.strip() for x in text_input.split(',') if x.strip()]
        # Convert to float and filter out invalid values
        positions = [float(x) for x in positions if x.replace('.', '').replace('-', '').isdigit()]
        # Sort positions and remove duplicates
        positions = sorted(list(set(positions)))
        return positions
    except (ValueError, AttributeError):
        return []  # Return empty list if parsing fails
    
def format_tab_positions(positions: List[float]) -> str:
    """Format list of positions as comma-separated string."""
    if not positions:
        return ''
    return ', '.join([str(pos) for pos in sorted(positions)])

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
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = cache.get(cell_data['cache_key'])

        # get the current collector from the cell, either cathode or anode depending on electrode
        current_collector = get_current_collector_from_cell(cell, electrode_key)

        # If the current collector is not of the right type, then return no_updates 
        if type(current_collector) != config.collector_type:
            return create_no_update_response(config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        # Handle different triggers using enum
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
    
    valid_types = [
        MaterialType.CATHODE_CURRENT_COLLECTOR_TAB, 
        MaterialType.CATHODE_CURRENT_COLLECTOR
    ]

    if material_type not in valid_types:
        raise ValueError(f"Unknown material type: {material_type}")

    def update_material(cell_data, material_selector, input_values, slider_values):
        triggered_id = ctx.triggered_id
        cell = cache.get(cell_data['cache_key'])
        material = get_material_from_cell(material_type, cell)

        if material is None:
            return create_material_no_update_response()

        if triggered_id == 'cell_store':
            parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
            return (no_update, material.name, parameter_list, parameter_list, min_values, max_values, marks_list)
        
        elif triggered_id == f'{material_type.value}_material_selector':  # Use .value
            material = CurrentCollectorMaterial.from_database(material_selector)
            parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
            new_cc_key = set_material_to_cell(material_type, cell, material)
            return ({'cache_key': new_cc_key}, material.name, parameter_list, parameter_list, min_values, max_values, marks_list)
        
        elif isinstance(triggered_id, dict) and 'property' in triggered_id:
            property = triggered_id['property']
            property_index = CC_MATERIAL_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            setattr(material, property, value)
            new_cc_key = set_material_to_cell(material_type, cell, material)
            parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
            return ({'cache_key': new_cc_key}, material.name, parameter_list, parameter_list, min_values, max_values, marks_list)

    return update_material



def get_current_collector_from_cell(cell: Type, electrode: str) -> Type:
    """Get the current collector from the cell based on the electrode type."""
    
    if electrode == ElectrodeType.CATHODE:
        return cell
    elif electrode == ElectrodeType.ANODE:
        return cell
    else:
        raise ValueError(f"Unknown electrode type: {electrode}")

def get_material_from_cell(material_type: MaterialType, cell: Type) -> Type:
    """Get the material from the cell based on the material type."""

    if material_type == MaterialType.CATHODE_CURRENT_COLLECTOR_TAB:
        return get_cathode_current_collector_tab_material(cell)
    elif material_type == MaterialType.CATHODE_CURRENT_COLLECTOR:
        return get_cathode_current_collector_material(cell)
    else:
        raise ValueError(f"Unknown material type: {material_type}")

def get_cathode_current_collector_tab_material(cell: Type) -> CurrentCollectorMaterial:
    """Get the current collector tab material from the cell."""
    try:
        material = cell.weld_tab.material
        return material
    except Exception:
        return None

def get_cathode_current_collector_material(cell: Type) -> CurrentCollectorMaterial:
    """Get the current collector material from the cell."""
    try:
        material = cell.material
        return material
    except Exception:
        return None

def set_current_collector_to_cell(cell: Type, current_collector: Type) -> str:
    """Set the current collector to the cell and return a new cache key."""
    try:
        cell = current_collector
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)
        return new_cc_key
    except Exception as e:
        print(f"Error setting current collector: {e}")
        return None

def set_material_to_cell(material_type: MaterialType, cell: Type, material: Type) -> str:
    
    if material_type == MaterialType.CATHODE_CURRENT_COLLECTOR_TAB:
        new_cc_key = set_cathode_current_collector_tab_material(cell, material)
    elif material_type == MaterialType.CATHODE_CURRENT_COLLECTOR:
        new_cc_key = set_cathode_current_collector_material(cell, material)
    else:
        raise ValueError(f"Unknown material type: {material_type}")
    
    return new_cc_key

def set_cathode_current_collector_tab_material(cell: Type, material: CurrentCollectorMaterial) -> str:
    """Set the current collector tab material for the cell."""
    try:
        current_collector = cell
        weld_tab = current_collector.weld_tab
        weld_tab.material = material
        current_collector.weld_tab = weld_tab
        cell = current_collector

        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)
        return new_cc_key
    except Exception as e:
        print(f"Error setting current collector material: {e}")
        return None
    
def set_cathode_current_collector_material(cell: Type, material: CurrentCollectorMaterial) -> str:
    """Set the current collector material for the cell."""
    try:
        current_collector = cell
        current_collector.material = material
        cell = current_collector

        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)
        return new_cc_key
    except Exception as e:
        print(f"Error setting current collector material: {e}")
        return None
    


