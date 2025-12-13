from steer_materials.Base import _Material, _VolumedMaterialMixin
from steer_core.Mixins.Serializer import SerializerMixin


class Binder(_VolumedMaterialMixin, _Material):

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
        Initialize an object that represents a binder.

        :param name: str: name of the material
        :param specific_cost: float: specific cost of the material per kg
        :param density: float: density of the material in g/cm^3 (default: 1.7)
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

