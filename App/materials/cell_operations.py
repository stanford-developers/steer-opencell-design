from typing import Type
from general.enumerated_classes import MaterialType


def get_material_from_cell(material_type: MaterialType, cell: Type) -> Type:
    """
    Get the material from the cell based on the material type.

    Parameters
    ----------
    material_type : MaterialType
        The type of material being retrieved (e.g., CATHODE_CURRENT_COLLECTOR_TAB).
    cell : Type
        The current cell object from the cache.

    Returns
    -------
    CurrentCollectorMaterial
        The current collector material associated with the cell.
    """
    if material_type == MaterialType.CATHODE_CURRENT_COLLECTOR_TAB:
        return get_cathode_current_collector_tab_material(cell)
    elif material_type == MaterialType.CATHODE_CURRENT_COLLECTOR:
        return get_cathode_current_collector_material(cell)
    elif material_type == MaterialType.CATHODE_INSULATION:
        return get_cathode_insulation_material(cell)
    else:
        raise ValueError(f"Unknown material type: {material_type}")


def get_cathode_current_collector_tab_material(cell: Type) -> Type:
    """
    Get the current collector tab material from the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    """
    try:
        material = cell.current_collector.weld_tab.material
        return material
    except Exception:
        return None


def get_cathode_current_collector_material(cell: Type) -> Type:
    """
    Get the current collector material from the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.

    Returns
    -------
    CurrentCollectorMaterial
        The current collector material associated with the cell.
    """
    material = cell.current_collector.material
    return material


def get_cathode_insulation_material(cell: Type) -> Type:
    """
    Get the cathode insulation material from the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.

    Returns
    -------
    CurrentCollectorMaterial
        The current collector material associated with the cell.
    """
    material = cell.insulation_material
    return material


def set_material_to_cell(material_type: MaterialType, cell: Type, material: Type) -> Type:
    """
    Set the material for the cell based on the material type.

    Parameters
    ----------
    material_type : MaterialType
        The type of material being set (e.g., CATHODE_CURRENT_COLLECTOR_TAB).
    cell : Type
        The current cell object from the cache.
    material : Type
        The material object to set in the cell.

    Returns
    -------
    cell : Type
        The updated cell object with the material set.
    """
    if material_type == MaterialType.CATHODE_CURRENT_COLLECTOR_TAB:
        cell = set_cathode_current_collector_tab_material_to_cell(cell, material)
    elif material_type == MaterialType.CATHODE_CURRENT_COLLECTOR:
        cell = set_cathode_current_collector_material_to_cell(cell, material)
    else:
        raise ValueError(f"Unknown material type: {material_type}")
    
    return cell


def set_cathode_current_collector_tab_material_to_cell(cell: Type, material: Type) -> Type:
    """
    Set the current collector tab material for the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    material : CurrentCollectorMaterial
        The current collector tab material to set in the cell.

    Returns
    -------
    cell : Type
        The updated cell object with the current collector tab material set.
    """
    cathode = cell
    current_collector = cathode.current_collector
    weld_tab = current_collector.weld_tab
    weld_tab.material = material
    current_collector.weld_tab = weld_tab
    cathode.current_collector = current_collector
    cell = cathode
    return cell


def set_cathode_current_collector_material_to_cell(cell: Type, material: Type) -> Type:
    """
    Set the current collector material for the cell.

    Parameters
    ----------
    cell : Type
        The current cell object from the cache.
    material : CurrentCollectorMaterial
        The current collector material to set in the cell.

    Returns
    -------
    cell : Type
        The updated cell object with the current collector material set.
    """
    cathode = cell
    current_collector = cathode.current_collector
    current_collector.material = material
    cathode.current_collector = current_collector
    cell = cathode
    return cell



