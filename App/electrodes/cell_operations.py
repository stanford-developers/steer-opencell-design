from typing import Type

from general.enumerated_classes import ElectrodeType

def get_electrode_from_cell(cell: Type, electrode: ElectrodeType) -> Type:
    """
    Get the electrode from the cell based on the electrode type.

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
        current_collector = cell
        return current_collector
    elif electrode == ElectrodeType.ANODE:
        current_collector = cell
        return current_collector
    else:
        raise ValueError(f"Unknown electrode type: {electrode}")


def set_electrode_to_cell(cell: Type, electrode: Type) -> Type:
    """
    Set the electrode to the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    electrode : Type
        The electrode object to set in the cell.

    Returns
    -------
    Type
        The updated cell object with the electrode set.
    """
    cell = electrode
    return cell
