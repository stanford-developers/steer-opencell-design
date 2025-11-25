from steer_materials.Base import _Material, _VolumedMaterialMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.DataManager import DataManager


class Binder(_Material, _VolumedMaterialMixin):

    def __init__(
        self, 
        name: str, 
        specific_cost: float, 
        density: float, 
        color: str = "#2c2c2c"
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
            color=color
        )

    @staticmethod
    def from_database(name) -> "Binder":
        """
        Pull object from the database.

        :param name: str: Name of the binder material.
        :return: Binder: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values("binder_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_binder_materials(most_recent=True).query(
            f"name == '{name}'"
        )
        string_rep = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_rep)
        return material


