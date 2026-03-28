# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Electrolyte material definitions for battery cells."""

from steer_core.Constants.Units import *
from steer_materials.Base import _Material, _VolumedMaterialMixin

from typing import Tuple

import numpy as np


class Electrolyte(_VolumedMaterialMixin, _Material):
    """
    Liquid electrolyte material used to fill battery cells.

    The electrolyte fills the pore volume of the electrode assembly and
    separator. Volume and mass ranges are set dynamically based on the
    pore volume of the assembly via ``_set_ranges_from_pore_volume``.
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
        Initialize an electrolyte material.

        Parameters
        ----------
        name : str
            Name of the electrolyte (e.g., "1M LiPF6 in EC:DMC (1:1)").
        density : float
            Density of the electrolyte in g/cm³.
        specific_cost : float
            Specific cost of the electrolyte in $/kg.
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

    def _set_ranges_from_pore_volume(self, _pore_volume: float, _range_scaling: float = 2) -> None:
        """
        Set volume and mass ranges based on pore volume of the electrode assembly.

        Parameters
        ----------
        _pore_volume : float
            Total pore volume of the electrode assembly in m³ (internal SI units).
        _range_scaling : float, optional
            Multiplier for the upper bound of the volume range (default: 2).
        """

        self._volume_range = (_pore_volume, _pore_volume * _range_scaling)

        self._mass_range = (
            self._volume_range[0] * self._density,
            self._volume_range[1] * self._density,
        )

    @property
    def volume_range(self) -> Tuple[float, float]:
        """Get the allowable electrolyte volume range in cm³."""
        return (
            self._volume_range[0] * M_TO_CM**3,
            self._volume_range[1] * M_TO_CM**3,
        )

    @property
    def mass_range(self) -> Tuple[float, float]:
        """Get the allowable electrolyte mass range in g."""
        return (
            self._mass_range[0] * KG_TO_G,
            self._mass_range[1] * KG_TO_G,
        )

