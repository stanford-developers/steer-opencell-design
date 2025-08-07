from typing import Type, Tuple, List, Dict
from uuid import uuid4

from general.enumerated_classes import CategoricalProperty

from steer_opencell_design.DataManager import DataManager

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



### Cell Helpers ###

def get_cell_from_database(cell_name: str) -> Type:
    """
    Fetch a cell object from the database based on the cell name.

    Parameters
    ----------
    cell_name : str
        The name of the cell to fetch from the database.

    Returns
    -------
    Type
        The cell object retrieved from the database.
    """
    from base64 import b64decode
    from pickle import loads

    # get the pickled cell data from the database
    pickled_cell = (
        DataManager()
        .get_data('cells')
        .query(f"name == '{cell_name}'")
        .iloc[0]
        ['object']
    )

    # decode the base64 encoded data
    cell = deserialize_object(pickled_cell)

    return cell

def set_cell_to_cache(cell: Type) -> str:
    """
    Store a cell object in the cache. Returns the new cache key.

    Parameters
    ----------
    cell : Type
        The cell object to store in the cache.

    Returns
    -------
    str
        The cache key assigned to the stored cell object.
    """
    from cache_service import cache

    # Generate a new cache key
    new_cc_key = str(uuid4())

    # Store the object in the cache
    cache.set(new_cc_key, cell)

    # Return the cache key to update the store
    return new_cc_key

def get_cell_from_cache(cache_key: str) -> Type:
    """
    Retrieve a cell object from the cache using the cache key.

    Parameters
    ----------
    cache_key : str
        The cache key for the cell object.

    Returns
    -------
    Type
        The cell object retrieved from the cache.
    """
    from cache_service import cache

    # Retrieve the object from the cache
    cell = cache.get(cache_key)

    if cell is None:
        raise ValueError(f"No cell found in cache with key: {cache_key}")

    return cell


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

