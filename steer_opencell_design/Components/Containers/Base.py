# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Abstract base class for battery cell container components."""

from abc import ABC, abstractmethod

from steer_core import (
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
)
from steer_core.Mixins.Propagation import PropagationMixin


class _Container(
    ABC,
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    PropagationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
):
    """Abstract base class for cell containers (canisters, encapsulations).

    Defines the interface for property calculation, coordinate generation,
    and mass/cost computation that all container types must implement.
    """

    def __init__(
            self,
            ):
        """Initialize container base state."""
        self._update_properties = False

    @abstractmethod
    def _calculate_all_properties(self):
        """Calculate bulk properties and coordinates (implemented by subclasses)."""
        self._calculate_bulk_properties()
        self._calculate_coordinates()

    @abstractmethod
    def _calculate_bulk_properties(self):
        """
        Calculate the bulk properties of the container, such as mass, volume, and cost.
        """
        pass

    @abstractmethod
    def _calculate_coordinates(self):
        """
        Calculate the coordinates of the container for visualization and analysis.
        """
        pass

    @abstractmethod
    def _calculate_mass(self) -> float:
        """
        Calculate the mass of the container.
        """
        self._mass = 0
        self._mass_breakdown = {}

    @abstractmethod
    def _calculate_cost(self) -> float:
        """
        Calculate the cost of the container.
        """
        self._cost = 0
        self._cost_breakdown = {}

