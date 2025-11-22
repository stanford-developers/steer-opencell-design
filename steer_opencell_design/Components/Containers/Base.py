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

