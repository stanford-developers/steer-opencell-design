from dash import no_update, ctx
from pathlib import Path
from typing import Type
from uuid import uuid4


def get_data_manager() -> Type:
    """
    Establish a connection to the database.
    
    Returns
    -------
    DataManager
        An instance of DataManager connected to the database.
    """
    from OpenCell.DataManager import DataManager
    
    # Establish the connection to the database
    CURRENT_DIR = Path(__file__).resolve().parent
    DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
    dm = DataManager(DATA_PATH)
    return dm

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
        get_data_manager()
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
        get_data_manager()
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
        get_data_manager()
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

    # get datamanage
    dm = get_data_manager()

    # get the pickled cell data from the database
    pickled_cell = (
        dm
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
