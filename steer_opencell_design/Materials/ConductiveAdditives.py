"""Conductive additive material definitions for electrode formulations."""

from steer_materials.Base import _Material, _VolumedMaterialMixin


class ConductiveAdditive(_VolumedMaterialMixin, _Material):
    """
    Conductive additive material used in electrode formulations.

    Conductive additives (e.g., carbon black, Super P, CNTs) improve
    electronic conductivity within the electrode coating.
    """

    _table_name = "conductive_additive_materials"

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
        Initialize a conductive additive material.

        Parameters
        ----------
        name : str
            Name of the conductive additive (e.g., "Super P").
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
