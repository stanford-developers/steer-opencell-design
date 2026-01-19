from steer_materials.Base import Metal, _Material, _VolumedMaterialMixin
import numpy as np


class CurrentCollectorMaterial(_VolumedMaterialMixin, Metal):
    """
    Materials from which current collectors are made.
    """

    _table_name = "current_collector_materials"

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
        super().__init__(
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )


class InsulationMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which insulation is made.
    """

    _table_name = "insulation_materials"

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


class SeparatorMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which separators are made.
    """

    _table_name = "separator_materials"

    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        porosity: float,
        color: str = "#2c2c2c",
        *,
        volume=None,
        mass=None,
        **kwargs,
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
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )

        self.porosity = porosity

    @property
    def porosity(self):
        return np.round(self._porosity * 100, 2)
    
    @property
    def porosity_range(self):
        return (0, 100)

    @porosity.setter
    def porosity(self, porosity: float) -> None:
        self.validate_percentage(porosity, "Porosity")
        self._porosity = porosity / 100.0


class TapeMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which tapes are made.
    """

    _table_name = "tape_materials"

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
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )


class PrismaticContainerMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which containers are made.
    """

    _table_name = "prismatic_container_materials"

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
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )


class FlexFrameMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which flex frame materials are made.
    """
    def __init__(
        self,
        name: str,
        density: float,
        specific_cost: float,
        color: str = "#B3AA9E",
        *,
        volume=None,
        mass=None,
        **kwargs,
    ):
        """
        Flex frame material for encapsulation of the flex frame cell

        Parameters
        ----------
        name : str
            Name of the flex frame material.
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


class LaminateMaterial(_VolumedMaterialMixin, _Material):
    """
    Materials from which containers are made.
    """

    _table_name = "laminate_materials"

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
            name=name, 
            density=density, 
            specific_cost=specific_cost, 
            color=color,
            volume=volume,
            mass=mass,
            **kwargs,
        )

    
