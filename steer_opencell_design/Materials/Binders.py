"""Binder material definitions for electrode formulations."""

from steer_materials.Base import _Material, _VolumedMaterialMixin
from steer_core.Mixins.Serializer import SerializerMixin


class Binder(_VolumedMaterialMixin, _Material):
    """
    Binder material used in electrode formulations.

    Binders (e.g., PVDF, CMC) provide mechanical cohesion between
    active material particles and conductive additives in the electrode coating.
    """

    _table_name = "binder_materials"

    def __init__(
        self, 
        name: str, 
        specific_cost: float, 
        density: float, 
        color: str = "#2c2c2c",
        *,
        volume=None,
        mass=None,
        **kwargs,
    ):
        """
        Initialize a binder material.

        Parameters
        ----------
        name : str
            Name of the binder material (e.g., "PVDF", "CMC").
        specific_cost : float
            Specific cost of the material in $/kg.
        density : float
            Density of the material in g/cm³.
        color : str, optional
            Hex color string for visualization (default: "#2c2c2c").
        volume : float or None, optional
            Initial volume in cm³.
        mass : float or None, optional
            Initial mass in g.
        """
        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )

