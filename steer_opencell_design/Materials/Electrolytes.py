from steer_core.Constants.Units import *
from steer_materials.Base import _Material, _VolumedMaterialMixin


class Electrolyte(_VolumedMaterialMixin, _Material):
    """
    Materials from which insulation is made.
    """

    def __init__(
            self, 
            name: str, 
            density: float, 
            specific_cost: float, 
            color: str = "#2c2c2c",
            *,
            volume=None,
            mass=None,
            **kwargs,
        ):
        """
        Insulation material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the insulation material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
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


