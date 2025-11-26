from steer_core.DataManager import DataManager
from steer_core.Mixins.Serializer import SerializerMixin
from steer_materials.Base import Metal, _Material


class CurrentCollectorMaterial(Metal):
    """
    Materials from which current collectors are made.
    """

    def __init__(self, name: str, density: float, specific_cost: float, color: str):
        """
        Current collector material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the current collector material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(name, density, specific_cost, color)

    @staticmethod
    def from_database(name) -> "CurrentCollectorMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the current collector material.

        Returns
        -------
        CurrentCollectorMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()

        available_materials = database.get_unique_values(
            "current_collector_materials", "name"
        )

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_current_collector_materials(most_recent=True).query(
            f"name == '{name}'"
        )

        string_rep = data["object"].iloc[0]

        material = SerializerMixin.deserialize(string_rep)

        return material


class InsulationMaterial(_Material):
    """
    Materials from which insulation is made.
    """

    def __init__(self, name: str, density: float, specific_cost: float, color: str):
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
        super().__init__(name, density, specific_cost, color)

    @staticmethod
    def from_database(name) -> "InsulationMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the insulation material.

        Returns
        -------
        InsulationMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()
        available_materials = database.get_unique_values("insulation_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_data(table_name="insulation_materials").query(
            f"name == '{name}'"
        )

        string_data = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_data)
        return material


class SeparatorMaterial(_Material):
    """
    Materials from which separators are made.
    """

    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        porosity: float,
        color: str,
    ):
        """
        Separator material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the separator material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        porosity : float
            Porosity of the separator material in %.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

        self.porosity = porosity

    @property
    def porosity(self):
        return round(self._porosity * 100, 2)
    
    @property
    def porosity_range(self):
        return (0, 100)

    @porosity.setter
    def porosity(self, porosity: float) -> None:
        self.validate_percentage(porosity, "Porosity")
        self._porosity = porosity / 100.0

    @staticmethod
    def from_database(name) -> "SeparatorMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the separator material.

        Returns
        -------
        SeparatorMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()

        available_materials = database.get_unique_values("separator_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_data(table_name="separator_materials").query(
            f"name == '{name}'"
        )

        string_data = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_data)
        return material


class TapeMaterial(_Material):
    """
    Materials from which tapes are made.
    """

    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        color: str,
    ):
        """
        Separator material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the tape material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

    @staticmethod
    def from_database(name) -> "TapeMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the tape material.

        Returns
        -------
        TapeMaterial: Instance of the class.
        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()

        available_materials = database.get_unique_values("tape_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_data(table_name="tape_materials").query(
            f"name == '{name}'"
        )

        string_data = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_data)
        return material


class PrismaticContainerMaterial(Metal):
    """
    Materials from which containers are made.
    """

    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        color: str,
    ):
        """
        Container material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the container material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

    @staticmethod
    def from_database(name) -> "PrismaticContainerMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the container material.

        Returns
        -------
        ContainerMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()

        available_materials = database.get_unique_values("prismatic_container_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_data(table_name="prismatic_container_materials").query(
            f"name == '{name}'"
        )

        string_data = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_data)
        return material
    

class LaminateMaterial(_Material):
    """
    Materials from which containers are made.
    """

    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        color: str,
    ):
        """
        Container material for encapsulation of the cell

        Parameters
        ----------
        name : str
            Name of the container material.
        density : float
            Density of the material in g/cm^3.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str
            Color of the material.
        """
        super().__init__(
            name, 
            density, 
            specific_cost, 
            color
        )

    @staticmethod
    def from_database(name) -> "LaminateMaterial":
        """
        Pull object from the database.

        Parameters
        ----------
        name : str
            Name of the container material.

        Returns
        -------
        LaminateMaterial: Instance of the class.

        Raises
        ------
        ValueError: If the material is not found in the database.
        """
        database = DataManager()

        available_materials = database.get_unique_values("laminate_materials", "name")

        if name not in available_materials:
            raise ValueError(
                f"Material '{name}' not found in the database. Available materials: {available_materials}"
            )

        data = database.get_data(table_name="laminate_materials").query(
            f"name == '{name}'"
        )

        string_data = data["object"].iloc[0]
        material = SerializerMixin.deserialize(string_data)
        return material
    
