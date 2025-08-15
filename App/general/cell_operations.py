from typing import Type, Any
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

def set_object_to_cell(cell: Type, obj: Any, config: Type) -> Type:
    """
    Generic function to set any object to a cell based on configuration.
    This version triggers setters for all intermediate objects in the path.
    
    Parameters
    ----------
    cell : Type
        The cell object to modify.
    obj : Any
        The object to set in the cell (e.g., current collector, material, etc.).
    config : Type
        Configuration object that defines how to set the object to the cell.
        Must have a 'cell_path' attribute that specifies the path to set the object.
        
    Returns
    -------
    Type
        The updated cell object with the object set.
        
    Raises
    ------
    AttributeError
        If the config doesn't have the required 'cell_path' attribute.
    ValueError
        If the cell_path is invalid or the path doesn't exist in the cell.
        
    Examples
    --------
    For a current collector:
        config.cell_path = ['current_collector']
        
    For a material with nested path:
        config.cell_path = ['current_collector', 'weld_tab', 'material']
        
    For a simple property:
        config.cell_path = ['insulation_material']
        
    For setting the entire cell (replacement):
        config.cell_path = [''] or config.cell_path = []
    """
    
    if not hasattr(config, 'cell_path'):
        raise AttributeError("Config must have a 'cell_path' attribute")
    
    # Handle direct cell replacement case
    if not config.cell_path or (len(config.cell_path) == 1 and config.cell_path[0] == ''):
        # Return the new object directly (replaces the entire cell)
        return obj
    
    # Build a path of objects for reassignment
    object_path = [cell]
    current_obj = cell
    
    # Navigate and collect all intermediate objects
    for path_component in config.cell_path[:-1]:
        if not hasattr(current_obj, path_component):
            raise ValueError(f"Invalid cell path: '{path_component}' not found in {type(current_obj).__name__}")
        current_obj = getattr(current_obj, path_component)
        object_path.append(current_obj)
    
    # Set the final object (this triggers the final setter)
    final_attribute = config.cell_path[-1]
    if not hasattr(current_obj, final_attribute):
        raise ValueError(f"Invalid cell path: '{final_attribute}' not found in {type(current_obj).__name__}")
    
    setattr(current_obj, final_attribute, obj)
    
    # Now reassign all intermediate objects to trigger their setters
    # Work backwards through the path
    for i in range(len(config.cell_path) - 2, -1, -1):
        parent_obj = object_path[i]
        child_obj = object_path[i + 1]
        attribute_name = config.cell_path[i]
        
        # This will trigger the setter for this attribute
        setattr(parent_obj, attribute_name, child_obj)
    
    return cell

def get_object_from_cell(cell: Type, config: Type) -> Any:
    """
    Generic function to get any object from a cell based on configuration.
    """
    if not hasattr(config, 'cell_path'):
        raise AttributeError("Config must have a 'cell_path' attribute")
    
    # Handle direct cell access case
    if (not config.cell_path or 
        (len(config.cell_path) == 1 and config.cell_path[0] in ['', '__self__', '__root__'])):
        return cell
    
    # Navigate to the target object
    current_obj = cell
    
    for path_component in config.cell_path:
        if not hasattr(current_obj, path_component):
            raise ValueError(f"Invalid cell path: '{path_component}' not found in {type(current_obj).__name__}")
        current_obj = getattr(current_obj, path_component)
    
    return current_obj

