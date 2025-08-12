from typing import Type, Tuple, List, Dict

from general.enumerated_classes import CategoricalProperty
from steer_core.DataManager import DataManager


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

def generate_parameters(
    object, 
    parameter_list: list
) -> Tuple[List[float], List[float], List[float], List[Dict[int, str]]]:
    
    """Generate parameter lists for any object."""
    parameter_values = []
    min_values = []
    max_values = []
    
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

