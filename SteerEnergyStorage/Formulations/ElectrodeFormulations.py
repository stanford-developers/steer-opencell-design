from SteerEnergyStorage.Materials.ElectrodeMaterials import _ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Utils import get_colorway
from typing import Dict, Optional


class ElectrodeFormulation:
    
    def __init__(self, 
                 active_materials: Dict[_ActiveMaterial, float], 
                 binders: Optional[Dict[Binder, float]] = None, 
                 conductive_additives: Optional[Dict[ConductiveAdditive, float]] = None,
                 name: Optional[str] = 'electrode_formulation'):
        """
        Initialize an object that represents an electrode formulation.
        
        :param active_materials: Dictionary containing the active materials and their mass fractions in percent.
        :param binders: Dictionary containing the binders and their mass fractions in percent.
        :param conductive_additives: Dictionary containing the conductive additives and their mass fractions in percent.
        :param name: Name of the electrode formulation.
        """
        self._active_materials = {key: value / 100 for key, value in active_materials.items()}
        self._binders = {key: value / 100 for key, value in (binders or {}).items()}
        self._conductive_additives = {key: value / 100 for key, value in (conductive_additives or {}).items()}
        self._name = name.replace(" ", "_").lower()
        self._validate_formulation()
        self._get_color_map()

    def _get_color_map(self) -> None:
        """
        Generate a color map for the components of the electrode formulation.
        """
        self._color_map = {}
        self._update_color_map(self._active_materials, "#FFC133", "#FF6833")
        self._update_color_map(self._binders, "blue", "green")
        self._update_color_map(self._conductive_additives, "purple", "orange")

    def _update_color_map(self, components: Dict, start_color: str, end_color: str) -> None:
        """
        Update the color map with the given components and color range.
        
        :param components: Dictionary of components to update the color map with.
        :param start_color: Starting color of the range.
        :param end_color: Ending color of the range.
        """
        if components:
            n = len(components)
            colors = get_colorway(start_color, end_color, n)
            color_dict = {key.name: value for key, value in zip(components.keys(), colors)}
            self._color_map.update(color_dict)

    def _validate_formulation(self) -> None:
        """
        Validate the electrode formulation to ensure it meets the required criteria.
        """
        if (self._active_materials or self._binders or self._conductive_additives):
            total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())
            if not (0.99 <= total_fraction <= 1.01):
                raise ValueError("The mass fractions of the components must sum to 100%.")

        self._validate_unique_names(self._active_materials, "active materials")
        self._validate_unique_names(self._binders, "binders")
        self._validate_unique_names(self._conductive_additives, "conductive additives")

    def _validate_unique_names(self, components: Dict, component_type: str) -> None:
        """
        Validate that the components have unique names.
        
        :param components: Dictionary of components to validate.
        :param component_type: Type of components being validated (for error messages).
        """
        names = [component.name for component in components.keys()]
        if len(names) != len(set(names)):
            raise ValueError(f"The {component_type} must have unique names.")

    @property
    def name(self) -> Optional[str]:
        return self._name.replace("_", " ").title()

    @property
    def active_materials(self) -> Dict[_ActiveMaterial, float]:
        return {key: value * 100 for key, value in self._active_materials.items()}
    
    @property
    def binders(self) -> Dict[Binder, float]:
        return {key: value * 100 for key, value in self._binders.items()}
    
    @property
    def conductive_additives(self) -> Dict[ConductiveAdditive, float]:
        return {key: value * 100 for key, value in self._conductive_additives.items()}

    def __str__(self) -> str:
        return self._name if self._name else "Electrode Formulation"
    
    def __repr__(self) -> str:
        return self.__str__()
