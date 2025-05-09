from SteerEnergyStorage.Materials.ElectrodeMaterials import _ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Utils import get_colorway
from typing import Dict, Optional

KG_TO_G = 1000
M_TO_CM = 1e2

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
        self._calculate_density()
        self._calculate_specific_cost()

    def _calculate_density(self) -> float:
        """
        Calculate the density of the electrode formulation.
        
        :return: The density of the electrode formulation in g/cm³.
        """
        active_materials_list = list(self._active_materials.keys())
        active_materials_mass_fractions = list(self._active_materials.values())
        active_material_densities = [material._density for material in active_materials_list]

        binders_list = list(self._binders.keys())
        binders_mass_fractions = list(self._binders.values())
        binders_densities = [material._density for material in binders_list]

        conductive_additives_list = list(self._conductive_additives.keys())
        conductive_additives_mass_fractions = list(self._conductive_additives.values())
        conductive_additives_densities = [material._density for material in conductive_additives_list]

        all_materials = active_materials_list + binders_list + conductive_additives_list
        all_mass_fractions = active_materials_mass_fractions + binders_mass_fractions + conductive_additives_mass_fractions
        all_densities = active_material_densities + binders_densities + conductive_additives_densities

        total_density = sum(mass_fraction * density for mass_fraction, density in zip(all_mass_fractions, all_densities))

        self._density = total_density

    def _calculate_specific_cost(self) -> float:
        """
        Calculate the specific cost of the electrode formulation.
        
        :return: The specific cost of the electrode formulation in $/kg.
        """
        active_materials_list = list(self._active_materials.keys())
        active_materials_mass_fractions = list(self._active_materials.values())
        active_material_costs = [material._specific_cost for material in active_materials_list]

        binders_list = list(self._binders.keys())
        binders_mass_fractions = list(self._binders.values())
        binders_costs = [material._specific_cost for material in binders_list]

        conductive_additives_list = list(self._conductive_additives.keys())
        conductive_additives_mass_fractions = list(self._conductive_additives.values())
        conductive_additives_costs = [material._specific_cost for material in conductive_additives_list]

        all_materials = active_materials_list + binders_list + conductive_additives_list
        all_mass_fractions = active_materials_mass_fractions + binders_mass_fractions + conductive_additives_mass_fractions
        all_costs = active_material_costs + binders_costs + conductive_additives_costs

        total_cost = sum(mass_fraction * cost for mass_fraction, cost in zip(all_mass_fractions, all_costs))

        self._specific_cost = total_cost

    def _get_color_map(self) -> None:
        """
        Generate a color map for the components of the electrode formulation.
        """
        self._color_map = {}
        self._update_color_map(self._active_materials, "#FFC133", "#FF6833")
        self._update_color_map(self._binders, "#0000FF", "#008000")
        self._update_color_map(self._conductive_additives, "#800080", "#FFA500")

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
        if not self._active_materials:
            raise ValueError("You must include at least one active material in the formulation.")

        if (self._active_materials or self._binders or self._conductive_additives):
            total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())
            if not (0.999 <= total_fraction <= 1.001):
                raise ValueError(f"Your weight fractions sum to {round(total_fraction * 100, 1)} %. Ensure they sum to 100 %.")

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
    
    @property
    def density(self) -> float:
        return round(self._density * KG_TO_G / (M_TO_CM ** 3), 1)
    
    @property
    def specific_cost(self) -> float:
        return round(self._specific_cost, 2)

    def __str__(self) -> str:
        return self._name if self._name else "Electrode Formulation"
    
    def __repr__(self) -> str:
        return self.__str__()
