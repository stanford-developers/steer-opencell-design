# SPDX-FileCopyrightText: 2024-2026 Nicholas Siemons and Adrian Yao
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Material definitions for auxiliary battery cell components.

This module defines material classes for current collectors, insulation,
separators, tapes, containers, flex frames, and laminates. Each class
wraps basic material properties (density, cost, color) and can be loaded
from the built-in database via ``from_database()``.
"""

from steer_materials.Base import Metal, _Material, _VolumedMaterialMixin
import numpy as np


class CurrentCollectorMaterial(_VolumedMaterialMixin, Metal):
    """
    Metal material used for current collector foils.

    Current collector materials are typically aluminum (cathode side)
    or copper (anode side).
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
        Initialize a current collector material.

        Parameters
        ----------
        name : str
            Name of the current collector material (e.g., "Aluminum", "Copper").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
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


class InsulationMaterial(_VolumedMaterialMixin, _Material):
    """
    Ceramic or polymer insulation coating material applied to electrode edges.

    Insulation materials (e.g., Al₂O₃) are applied to uncoated regions of
    the current collector to prevent short circuits at electrode boundaries.
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
        Initialize an insulation material.

        Parameters
        ----------
        name : str
            Name of the insulation material (e.g., "Aluminium Oxide, 99.5%").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
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


class SeparatorMaterial(_VolumedMaterialMixin, _Material):
    """
    Porous separator membrane material.

    Separators electrically isolate the anode from the cathode while
    allowing ion transport through their pore structure. The porosity
    determines the electrolyte uptake capacity.
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
        Initialize a separator material.

        Parameters
        ----------
        name : str
            Name of the separator material (e.g., "Polyethylene").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
        porosity : float
            Porosity of the separator material in % (0–100).
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

        self.porosity = porosity

    @property
    def porosity(self):
        """Get the separator porosity in %."""
        return np.round(self._porosity * 100, 2)
    
    @property
    def porosity_range(self):
        """Get the allowable porosity range in % — always (0, 100)."""
        return (0, 100)

    @porosity.setter
    def porosity(self, porosity: float) -> None:
        self.validate_percentage(porosity, "Porosity")
        self._porosity = porosity / 100.0


class TapeMaterial(_VolumedMaterialMixin, _Material):
    """
    Adhesive tape material used for winding termination on jelly rolls.

    Tape wraps secure the outer layers of wound electrode assemblies
    and provide mechanical stability.
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
        Initialize a tape material.

        Parameters
        ----------
        name : str
            Name of the tape material (e.g., "Kapton").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
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


class PrismaticContainerMaterial(_VolumedMaterialMixin, _Material):
    """
    Metal material used for prismatic and cylindrical cell casings.

    Typical materials include aluminum and steel for canisters, lids,
    and terminal connectors.
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
        Initialize a container material.

        Parameters
        ----------
        name : str
            Name of the container material (e.g., "Steel", "Aluminum").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
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


class FlexFrameMaterial(_VolumedMaterialMixin, _Material):
    """
    Polymer material used for flex-frame cell housings.

    Flex frames are rigid polymer borders (e.g., PEEK) that hold the
    electrode stack and are sealed with laminate sheets.
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
        Initialize a flex-frame material.

        Parameters
        ----------
        name : str
            Name of the flex-frame material (e.g., "PEEK").
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
        color : str, optional
            Hex color string for visualization (default: "#B3AA9E").
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


class LaminateMaterial(_VolumedMaterialMixin, _Material):
    """
    Multi-layer laminate film material for pouch cell encapsulation.

    Laminate films are used as the outer packaging in pouch cells and
    flex-frame cells, providing a lightweight hermetic seal.
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
        Initialize a laminate material.

        Parameters
        ----------
        name : str
            Name of the laminate material.
        density : float
            Density of the material in g/cm³.
        specific_cost : float
            Specific cost of the material in $/kg.
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

    
