from dash import dcc
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from typing import Dict

from App.current_collectors.layout_configs import CollectorType
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
        return False

