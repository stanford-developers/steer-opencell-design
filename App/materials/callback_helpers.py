from dash import no_update
from typing import Tuple
from current_collectors.lists import CC_MATERIAL_PARAMETER_LIST


def create_no_update_response() -> Tuple:
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

