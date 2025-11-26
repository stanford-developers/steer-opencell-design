from steer_materials.Base import _Material, _VolumedMaterialMixin
from steer_core.Mixins.Serializer import SerializerMixin
from steer_core.DataManager import DataManager


class ConductiveAdditive(_Material, _VolumedMaterialMixin):

    def __init__(
        self, 
        name: str, 
        specific_cost: float, 
        density: float, 
        color: str = "#2c2c2c"
    ):

        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color
        )

    @staticmethod
    def from_database(name) -> "ConductiveAdditive":
        """
        Pull object from the database.

        :param name: str: Name of the conductive additive material.
        :return: ConductiveAdditive: Instance of the class.
        """
        database = DataManager()

        available_materials = database.get_unique_values(
            "conductive_additive_materials", "name"
        )

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_conductive_additive_materials(most_recent=True).query(
            f"name == '{name}'"
        )
        string_rep = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_rep)
        return material


