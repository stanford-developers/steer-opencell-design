from typing import Type
from database_service import DataManager
from steer_core.Mixins.Serializer import SerializerMixin
from uuid import uuid4

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
    cell = SerializerMixin.deserialize(pickled_cell)

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

