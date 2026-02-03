from steer_core.Constants.Units import *
from steer_materials.Base import _Material, _VolumedMaterialMixin

from typing import Tuple

import numpy as np


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

    def _set_ranges_from_pore_volume(self, _pore_volume: float, _range_scaling: float = 2) -> None:
        """Set volume and mass ranges based on pore volume."""

        self._volume_range = (_pore_volume, _pore_volume * _range_scaling)

        self._mass_range = (
            self._volume_range[0] * self._density,
            self._volume_range[1] * self._density,
        )

    @property
    def volume_range(self) -> Tuple[float, float]:
        """Get volume range in cm^3."""
        return (
            np.round(self._volume_range[0] * M_TO_CM**3, 2),
            np.round(self._volume_range[1] * M_TO_CM**3, 2),
        )

    @property
    def mass_range(self) -> Tuple[float, float]:
        """Get mass range in g."""
        return (
            np.round(self._mass_range[0] * KG_TO_G, 2),
            np.round(self._mass_range[1] * KG_TO_G, 2),
        )

