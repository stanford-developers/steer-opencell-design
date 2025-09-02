from typing import Type, Tuple, List, Dict, Any, Optional, Union
import time

from App.general.enumerated_classes import CategoricalProperty

from steer_core.DataManager import DataManager

from dash import no_update, dash_table, html

### Database Helpers ###

def get_internal_construction_options(form_factor):
    """
    Fetch internal construction options based on the form factor.
    
    Parameters
    ----------
    form_factor : str
        The selected form factor for the cell.

    Returns
    -------
    list
        A list of dictionaries containing the internal construction options.
    """    
    options = (
        DataManager()
        .get_data('cells')
        .query(f"form_factor == '{form_factor}'")
        .filter(['internal_construction'])
        .sort_values(by='internal_construction')
        .drop_duplicates()
        .internal_construction
        .tolist()
    )
    
    return [{'label': option, 'value': option} for option in options]

def get_electrochemical_reference_options(internal_construction, form_factor):
    """
    Fetch electrochemical reference options based on the internal construction and form factor.
    
    Parameters
    ----------
    internal_construction : str
        The selected internal construction for the cell.
    form_factor : str
        The selected form factor for the cell.

    Returns
    -------
    list
        A list of dictionaries containing the electrochemical reference options.
    """
    options = (
        DataManager()
        .get_data('cells')
        .query(f"form_factor == '{form_factor}'")
        .query(f"internal_construction == '{internal_construction}'")
        .filter(['reference'])
        .sort_values(by='reference')
        .drop_duplicates()
        .reference
        .tolist()
    )

    return [{'label': option, 'value': option} for option in options]

def get_cell_name_options(internal_construction, electrochemical_reference, form_factor):
    """
    Fetch cell name options based on the internal construction, electrochemical reference, and form factor.
    
    Parameters
    ----------
    internal_construction : str
        The selected internal construction for the cell.
    electrochemical_reference : str
        The selected electrochemical reference for the cell.
    form_factor : str
        The selected form factor for the cell.

    Returns
    -------
    list
        A list of dictionaries containing the cell name options.
    """
    options = (
        DataManager()
        .get_data('cells')
        .query(f"form_factor == '{form_factor}'")
        .query(f"internal_construction == '{internal_construction}'")
        .query(f"reference == '{electrochemical_reference}'")
        .filter(['name'])
        .sort_values(by='name')
        .drop_duplicates()
        .name
        .tolist()
    )

    return [{'label': option, 'value': option} for option in options]

def get_active_materials(electrochemical_reference, electrode: str):
    """
    Fetch active materials based on the electrochemical reference and electrode type.

    Parameters
    ----------
    electrochemical_reference : str
        The selected electrochemical reference for the cell.

    Returns
    -------
    list
        A list of dictionaries containing the cathode materials.
    """
    table = 'cathode_materials' if electrode == 'cathode' else 'anode_materials'

    options = (
        DataManager()
        .get_data(table)
        .query(f"reference == '{electrochemical_reference}'")
        .filter(['name'])
        .sort_values(by='name')
        .drop_duplicates()
        .name
        .tolist()
    )

    return options

### Serialization Helpers ###

def deserialize_object(serialized_object: str) -> Type:
    """
    Deserialize a base64 encoded string into a Python object.
    
    Parameters
    ----------
    serialized_object : str
        The base64 encoded string representing the serialized object.

    Returns
    -------
    Type
        The deserialized Python object.
    """
    from base64 import b64decode
    from pickle import loads

    # Decode the base64 encoded string
    decoded_data = b64decode(serialized_object)
    
    # Deserialize the object using pickle
    return loads(decoded_data)


### Callback Helpers ###

def generate_parameters(object, config: Type) -> Tuple[List[float], List[float], List[float], List[Dict[int, str]]]:
    
    """Generate parameter lists for any object."""
    parameter_values = []
    min_values = []
    max_values = []
    
    parameter_list = config.parameter_list

    # Now use the enum
    categorical_properties = {prop.value for prop in CategoricalProperty}
    
    for param in parameter_list:
        if param in categorical_properties:
            # Handle categorical properties
            value = getattr(object, param)
            parameter_values.append(value)
            min_values.append(0)
            max_values.append(1)
        else:
            # Handle numerical properties
            value = getattr(object, param)
            parameter_values.append(value)
            min_values.append(getattr(object, f"{param}_range")[0])
            max_values.append(getattr(object, f"{param}_range")[1])
    
    return parameter_values, min_values, max_values

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
    min_vals = [getattr(object, f"{param}_range")[0] for param in range_params]
    max_vals = [getattr(object, f"{param}_range")[1] for param in range_params]
    return start_list, end_list, min_vals, max_vals

def validate_dependent_properties(object, config: Type) -> None:
    """Validate and clamp dependent properties to their valid ranges."""
    for param in config.settable_parameters:
        try:
            param_range = getattr(object, f"{param}_hard_range")
            param_value = getattr(object, param)
            if param_value < param_range[0]:
                setattr(object, param, param_range[0])
            elif param_value > param_range[1]:
                setattr(object, param, param_range[1])
        except AttributeError:
            # Handle case where range doesn't exist
            continue

def validate_single_property(object, property_name: str, value: str, config: Type) -> None:

    if hasattr(config, 'radioitem_parameters') and config.radioitem_parameters and property_name in config.radioitem_parameters:
        return value

    if hasattr(config, 'text_parameters') and config.text_parameters and property_name in config.text_parameters:
        return value

    param_range = getattr(object, f"{property_name}_hard_range", None)

    if param_range and hasattr(config, 'parameter_list') and config.parameter_list and property_name in config.parameter_list:
        if value < param_range[0]:
            return param_range[0]
        elif value > param_range[1]:
            return param_range[1]
        else:
            return value

    if param_range and hasattr(config, 'range_slider_parameters') and config.range_slider_parameters and property_name in config.range_slider_parameters:
        lower_bound = value[0] if value[0] > param_range[0] else param_range[0]
        upper_bound = value[1] if value[1] < param_range[1] else param_range[1]
        return (lower_bound, upper_bound)

def create_no_update_response(
        config = None, 
        existing_warnings: List[str] = [], 
        n: int = None, 
        n_rangeslider: int = None
) -> Tuple:

    """Create a no_update response specifically for material callbacks."""
    n = len(config.parameter_list) if n is None else n

    response = (
        no_update,  # cache_key
        [no_update] * n,  # slider values
        [no_update] * n,  # slider mins
        [no_update] * n,  # slider maxs
        [no_update] * n,  # slider marks
        [no_update] * n,  # slider steps
        [no_update] * n,  # input steps
    )

    if hasattr(config, 'dropdown_menu') and config.dropdown_menu:
        response += (no_update, )

    if hasattr(config, 'range_slider_parameters') and config.range_slider_parameters:
        n_rangeslider = len(config.range_slider_parameters) if n_rangeslider is None else n_rangeslider
        response += (
            [no_update] * n_rangeslider,  # range_slider_values
            [no_update] * n_rangeslider,  # range slider mins
            [no_update] * n_rangeslider,  # range slider maxs
            [no_update] * n_rangeslider,  # range slider marks
            [no_update] * n_rangeslider,  # range slider steps
            [no_update] * n_rangeslider,  # range slider start values
            [no_update] * n_rangeslider,  # range slider end values
        )

    if hasattr(config, 'radioitem_parameters') and config.radioitem_parameters:
        num_radioitem_params = len(config.radioitem_parameters)
        response += (
            [no_update] * num_radioitem_params,  # radioitem values
        )

    if hasattr(config, 'text_parameters') and config.text_parameters:
        num_text_params = len(config.text_parameters)
        response += (
            [no_update] * num_text_params,  # text item values
        )

    return (existing_warnings,) + tuple(response)


## Output Helpers ##

def create_properties_table(
    properties: Optional[Dict[str, Any]], 
    table_id: Optional[str] = None,
    decimal_places: int = 4,
    custom_styles: Optional[Dict[str, Any]] = None
) -> Union[dash_table.DataTable, html.Div]:
    """
    Create a formatted DataTable from a properties dictionary.
    
    Parameters
    ----------
    properties : dict or None
        Dictionary of property names and values to display
    table_id : str, optional
        ID for the DataTable component
    decimal_places : int, default 4
        Number of decimal places for float formatting
    custom_styles : dict, optional
        Custom styling overrides for the table
        
    Returns
    -------
    dash_table.DataTable or html.Div
        Formatted table component or fallback message
        
    Examples
    --------
    >>> props = {'mass': 1.2345, 'volume': 0.0067, 'density': 2700}
    >>> table = create_properties_table(props)
    
    >>> # With custom styling
    >>> custom_styles = {'style_header': {'backgroundColor': 'blue'}}
    >>> table = create_properties_table(props, custom_styles=custom_styles)
    """
    
    if not properties or not isinstance(properties, dict):
        return _create_fallback_message()
    
    # Convert dictionary to list of records for DataTable
    table_data = []
    for key, value in properties.items():
        formatted_key = _format_property_name(key)
        formatted_value = _format_property_value(value, decimal_places)
        
        table_data.append({
            'Property': formatted_key,
            'Value': formatted_value
        })
    
    # Default styles
    default_styles = _get_default_table_styles()
    
    # Merge custom styles if provided
    if custom_styles:
        for style_key, style_value in custom_styles.items():
            if style_key in default_styles:
                default_styles[style_key].update(style_value)
            else:
                default_styles[style_key] = style_value
    
    # Create table configuration
    table_config = {
        'data': table_data,
        'columns': [
            {"name": "Property", "id": "Property"},
            {"name": "Value", "id": "Value"}
        ],
        **default_styles
    }
    
    # Add ID if provided
    if table_id:
        table_config['id'] = table_id
    
    return dash_table.DataTable(**table_config)

def _format_property_name(key: str) -> str:
    """Format property name by replacing underscores and capitalizing."""
    return key.replace('_', ' ').title()

def _format_property_value(value: Any, decimal_places: int) -> str:
    """Format property value based on its type."""
    if isinstance(value, float):
        return f"{value:.{decimal_places}f}"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, bool):
        return "Yes" if value else "No"
    elif value is None:
        return "N/A"
    else:
        return str(value)

def _get_default_table_styles() -> Dict[str, Dict[str, Any]]:
    """Get default styling for properties tables."""
    return {
        'style_table': {
            'overflowX': 'auto',
            'border': '1px solid #ddd',
            'borderRadius': '5px'
        },
        'style_cell': {
            'textAlign': 'left',
            'padding': '10px',
            'border': '1px solid #ddd',
            'fontFamily': 'Arial, sans-serif'
        },
        'style_header': {
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #ddd'
        },
        'style_data': {
            'backgroundColor': '#ffffff',
        }
    }

def _create_fallback_message() -> html.Div:
    """Create fallback message when no properties are available."""
    return html.Div([
        html.P(
            "No properties available", 
            style={
                'textAlign': 'center', 
                'color': '#666', 
                'fontStyle': 'italic'
            }
        )
    ])

def create_trigger_data(trigger_id: Dict = None, cell_data: Dict = None) -> Dict[str, Any]:

    trigger_data = {'timestamp': time.time()}

    if trigger_id is not None:
        trigger_data['trigger'] = trigger_id
    if cell_data is not None:
        trigger_data['cell_data'] = cell_data

    return trigger_data

