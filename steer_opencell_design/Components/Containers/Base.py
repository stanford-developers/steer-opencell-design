from abc import ABC, abstractmethod

from steer_core import (
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
)

class _Container(
    ABC,
    CoordinateMixin,
    ColorMixin,
    ValidationMixin,
    SerializerMixin,
    DunderMixin,
    PlotterMixin,
):

    def __init__(
            self,
            ):
        
        self._update_properties = False

    @abstractmethod
    def _calculate_all_properties(self):
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

