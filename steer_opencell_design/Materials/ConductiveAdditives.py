from steer_materials.Base import _Material, _VolumedMaterialMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.DataManager import DataManager


class ConductiveAdditive(_VolumedMaterialMixin, _Material):

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

        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )
