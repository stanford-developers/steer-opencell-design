from dash import dcc, set_props
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from typing import Dict

from App.current_collectors.configs import CollectorType
from App.general.cell_operations import get_object_from_cell


################################
####### Last triggered ########
################################

last_triggered = dcc.Store(id="last_triggered", data=[])

################################
####### Trigger Classes ########
################################


@dataclass
class TriggerCondition:
    """Configuration for a single trigger condition."""
    check_function: Callable[[Any, Any], bool]


@dataclass
class CallbackTriggerConfig:
    """Configuration for when a callback should be triggered."""
    conditions: List[TriggerCondition] = None
    config: CollectorType = None
    required_visibility: List[Dict] = None


##############################
##### General Conditions #####
##############################


def is_visible(styles: List[Dict]) -> bool:

    """Check if the component is visible based on its styles."""
    
    # If styles is empty, assume visible
    if not styles:
        return True
    
    if styles is None:
        return True
    
    # If all display is none for any of the viewing styles, return no update
    if any(d.get("display") == "none" for d in styles if d is not None):
        return False
    
    return True


def has_changed(old_cell, new_cell, config) -> bool:
    """Check if the relevant part of the cell has changed."""
    try:
        old_obj = get_object_from_cell(old_cell, config)
        new_obj = get_object_from_cell(new_cell, config)
        return old_obj != new_obj
    except Exception as e:
        return True


def has_type_changed(old_cell, new_cell, config) -> bool:
    """Check if the type of the relevant part of the cell has changed."""
    try:
        old_obj = get_object_from_cell(old_cell, config)
        new_obj = get_object_from_cell(new_cell, config)
        return type(old_obj) != type(new_obj)
    except Exception as e:
        return True



##############################
##### Helper Functions #######
##############################

def create_trigger_store(callback_name: str) -> dcc.Store:
    """Create a trigger store for a callback."""
    return dcc.Store(id={"type": "trigger", "callback": callback_name}, data=[])

def evaluate_conditions(
    trigger_config: CallbackTriggerConfig,
    old_cell: Optional[object],
    new_cell: Optional[object]
) -> Dict[str, bool]:
    
    """Evaluate all conditions for a callback trigger."""
    
    conditions_dict = {}
    
    if trigger_config.conditions:
        for condition in trigger_config.conditions:
            condition_result = condition.check_function(old_cell, new_cell, trigger_config.config)
            condition_name = getattr(condition, 'name', condition.check_function.__name__)
            conditions_dict[condition_name] = condition_result
    
    return conditions_dict

def should_fire_on_cell_load(
        
    trigger_config: CallbackTriggerConfig,
    old_cell: Optional[object],
    new_cell: Optional[object]
    
) -> bool:
    
    """Determine if callback should fire on cell load."""

    if not trigger_config.conditions:
        return True
    
    condition_results = evaluate_conditions(trigger_config, old_cell, new_cell)

    return all(condition_results.values())

def trigger_callback(callback_name: str, timestamp: float) -> None:
    """Trigger a callback by updating its trigger store."""
    # print(f"Triggering callback: {callback_name}")
    set_props({"type": "trigger", "callback": callback_name}, {"data": timestamp})


def orchestrate_callbacks_generic(
    trigger_configs: Dict[str, CallbackTriggerConfig],
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    visibility_styles: Dict[str, Dict],
    last_triggered_callback: str,
    timestamp: float,
    debug_name: str = "Generic"
) -> None:
    """
    Generic orchestration function that handles callback triggering logic.
    
    Args:
        trigger_configs: Dictionary mapping callback names to their trigger configurations
        cell_data: Current cell data from cell_store
        old_cell_data: Previous cell data from old_cell_store
        visibility_styles: Dictionary mapping element IDs to their style dictionaries
        last_triggered_callback: Name of the last triggered callback
        timestamp: Current timestamp for triggering
        debug_name: Name for debug messages
    """
    from App.general.cell_operations import get_cell_from_cache
    
    # Get cells from cache
    new_cell = get_cell_from_cache(cell_data["cache_key"])
    old_cell = get_cell_from_cache(old_cell_data["cache_key"])

    # print(f"Orchestrating {debug_name} callbacks...")

    # Handle cell loaded case - fire all callbacks that meet conditions
    if last_triggered_callback == "Cell Loaded":
        for callback_name, trigger_config in trigger_configs.items():
            if should_fire_on_cell_load(trigger_config, old_cell, new_cell):
                # print(f"Cell Loaded - Triggering {callback_name}")
                trigger_callback(callback_name, timestamp)
        return

    # Handle normal cases
    for callback_name, trigger_config in trigger_configs.items():

        # Check visibility
        required_styles = [visibility_styles.get(element_id) for element_id in trigger_config.required_visibility]
        visibility_condition = is_visible(required_styles)
        
        # Check anti-circular logic
        anti_circular_condition = last_triggered_callback != callback_name
        
        # Check callback-specific conditions
        callback_conditions = evaluate_conditions(trigger_config, old_cell, new_cell)
        
        # Combine all conditions
        all_conditions = {
            "visibility": visibility_condition,
            "anti_circular": anti_circular_condition,
            **callback_conditions
        }
        
        # Trigger if all conditions are met
        if all(all_conditions.values()):
            # Debug output (can be controlled per module)
            # print(f"orchestrating {debug_name}, callback name: {callback_name}, conditions: {all_conditions}")
            trigger_callback(callback_name, timestamp)

