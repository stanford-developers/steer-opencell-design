from typing import Type
from general.enumerated_classes import ElectrodeType


def get_current_collector_from_cell(cell: Type, electrode: ElectrodeType) -> Type:
    """
    Get the current collector from the cell based on the electrode type.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    electrode : str
        The type of electrode (e.g., 'CATHODE', 'ANODE').

    Returns
    -------
    Type
        The current collector object associated with the cell.

    Raises
    ------
    ValueError
        If the electrode type is unknown.
    """
    
    if electrode == ElectrodeType.CATHODE:
        current_collector = cell.current_collector
        return current_collector
    elif electrode == ElectrodeType.ANODE:
        current_collector = cell.current_collector
        return current_collector
    else:
        raise ValueError(f"Unknown electrode type: {electrode}")


def set_current_collector_to_cell(cell: Type, current_collector: Type) -> str:
    """
    Set the current collector to the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    current_collector : Type
        The current collector object to set in the cell.

    Returns
    -------
    cell : Type
        The updated cell object with the current collector set.
    """
    cell.current_collector = current_collector
    return cell


