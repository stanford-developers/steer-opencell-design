from SteerEnergyStorage.Materials.ElectrodeMaterials import _ActiveMaterial, Binder, ConductiveAdditive

from SteerEnergyStorage.Utils import get_colorway
from SteerEnergyStorage.Constants import *

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
        self._check_active_materials(active_materials)
        self._check_binders(binders)
        self._check_conductive_additives(conductive_additives)
        self._check_name(name)
        self._check_formulation()
        self._get_properties()
        self._get_specific_cost_breakdown()
        self._get_density_breakdown()

    def _get_properties(self) -> None:
        """
        Retrieve the properties of the electrode formulation.
        This method is called to ensure that all properties are calculated and available.
        """
        self._calculate_density()
        self._calculate_specific_cost()
        self._get_color()

    def _check_active_materials(self, active_materials) -> None:

        for key, value in active_materials.items():

            if not isinstance(key, _ActiveMaterial):
                raise TypeError(f"Expected an instance of _ActiveMaterial, got {type(key)}.")
            if not isinstance(value, (int, float)):
                raise TypeError(f"Expected a numeric value for mass fraction, got {type(value)}.")
            if value < 0 or value > 100:
                raise ValueError(f"Mass fraction for {key.name} must be between 0 and 100, got {value}.")

        self._active_materials = {key: value / 100 for key, value in active_materials.items()}

    def _check_binders(self, binders) -> None:
        
        if binders == None or binders == {}:
            return {}
        
        for key, value in binders.items():
            if not isinstance(key, Binder):
                raise TypeError(f"Expected an instance of Binder, got {type(key)}.")
            if not isinstance(value, (int, float)):
                raise TypeError(f"Expected a numeric value for mass fraction, got {type(value)}.")
            if value < 0 or value > 100:
                raise ValueError(f"Mass fraction for {key.name} must be between 0 and 100, got {value}.")
        
        self._binders = {key: value / 100 for key, value in binders.items()}

    def _check_conductive_additives(self, conductive_additives) -> None:

        if conductive_additives is None or conductive_additives == {}:
            return {}

        for key, value in conductive_additives.items():
            if not isinstance(key, ConductiveAdditive):
                raise TypeError(f"Expected an instance of ConductiveAdditive, got {type(key)}.")
            if not isinstance(value, (int, float)):
                raise TypeError(f"Expected a numeric value for mass fraction, got {type(value)}.")
            if value < 0 or value > 100:
                raise ValueError(f"Mass fraction for {key.name} must be between 0 and 100, got {value}.")
        
        self._conductive_additives = {key: value / 100 for key, value in conductive_additives.items()}

    def _check_name(self, name: str) -> None:

        """
        Validate the name of the electrode formulation.
        
        :param name: Name of the electrode formulation.
        :raises ValueError: If the name is not a string or is empty.
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected a string for name, got {type(name)}.")
        if not name.strip():
            raise ValueError("Name cannot be an empty string.")
        
        self._name = name.replace(" ", "_").lower()

    def _calculate_density(self) -> float:
        """
        Calculate the density of the electrode formulation.

        :return: The density of the electrode formulation in g/cm³.
        """
        def extract_material_data(material_dict):
            return [(material._density, fraction) for material, fraction in material_dict.items()]

        # Collect (density, mass_fraction) pairs from all sources
        components = (
            extract_material_data(self._active_materials) +
            extract_material_data(self._binders) +
            extract_material_data(self._conductive_additives)
        )

        # Weighted average density
        self._density = sum(d * mf for d, mf in components)
        return self._density

    def _calculate_specific_cost(self) -> float:
        """
        Calculate the specific cost of the electrode formulation.

        :return: The specific cost of the electrode formulation in $/kg.
        """
        def extract_cost_data(material_dict):
            return [(material._specific_cost, fraction) for material, fraction in material_dict.items()]

        components = (
            extract_cost_data(self._active_materials) +
            extract_cost_data(self._binders) +
            extract_cost_data(self._conductive_additives)
        )

        self._specific_cost = sum(cost * mf for cost, mf in components)
        return self._specific_cost

    def _get_color(self) -> str:
        """
        Calculate the average HTML color of the electrode formulation,
        weighted by the mass fraction of each component.

        :return: A hex color string representing the weighted average color.
        """
        def hex_to_rgb(hex_code: str) -> tuple:
            hex_code = hex_code.lstrip('#')
            return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb: tuple) -> str:
            return '#{:02x}{:02x}{:02x}'.format(*map(lambda x: int(round(x)), rgb))

        def extract_color_data(material_dict):
            return [(hex_to_rgb(material._color), fraction) for material, fraction in material_dict.items()]

        # Gather all (rgb, fraction) pairs
        components = (
            extract_color_data(self._active_materials) +
            extract_color_data(self._binders) +
            extract_color_data(self._conductive_additives)
        )

        # Weighted average of RGB channels
        total_r = sum(rgb[0] * f for rgb, f in components)
        total_g = sum(rgb[1] * f for rgb, f in components)
        total_b = sum(rgb[2] * f for rgb, f in components)

        avg_rgb = (total_r, total_g, total_b)

        self._color = rgb_to_hex(avg_rgb)

    def _check_formulation(self) -> None:
        """
        Validate the electrode formulation to ensure it meets the required criteria.
        """
        if not self._active_materials:
            raise ValueError("You must include at least one active material in the formulation.")

        if (self._active_materials or self._binders or self._conductive_additives):
            total_fraction = sum(self._active_materials.values()) + sum(self._binders.values()) + sum(self._conductive_additives.values())
            if not (0.999 <= total_fraction <= 1.001):
                raise ValueError(f"Your weight fractions sum to {round(total_fraction * 100, 1)} %. Ensure they sum to 100 %.")

        self._check_unique_names(self._active_materials, "active materials")
        self._check_unique_names(self._binders, "binders")
        self._check_unique_names(self._conductive_additives, "conductive additives")

    def _check_unique_names(self, components: Dict, component_type: str) -> None:
        """
        Validate that the components have unique names.
        
        :param components: Dictionary of components to validate.
        :param component_type: Type of components being validated (for error messages).
        """
        names = [component.name for component in components.keys()]
        if len(names) != len(set(names)):
            raise ValueError(f"The {component_type} must have unique names.")

    def _get_specific_cost_breakdown(self) -> None:

        active_material_specific_costs = [c._specific_cost for c in self._active_materials.keys()]

        active_material_costs = {
            key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_specific_costs)
        }

        binder_specific_costs = [c._specific_cost for c in self._binders.keys()]
        binder_costs = {
            key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_specific_costs)
        } if self._binders else {}

        conductive_additive_costs = [c._specific_cost for c in self._conductive_additives.keys()]
        conductive_additive_costs = {
            key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_costs)
        } if self._conductive_additives else {}

        self._specific_cost_breakdown = active_material_costs | binder_costs | conductive_additive_costs

    def _get_density_breakdown(self) -> Dict[str, float]:
        """
        Calculate the density breakdown of the electrode formulation.

        :return: A dictionary with the density contribution of each component.
        """
        active_material_densities = [c._density for c in self._active_materials.keys()]
        active_material_density_breakdown = {
            key.name: value * self._active_materials[key] for key, value in zip(self._active_materials.keys(), active_material_densities)
        }

        binder_densities = [c._density for c in self._binders.keys()]
        binder_density_breakdown = {
            key.name: value * self._binders[key] for key, value in zip(self._binders.keys(), binder_densities)
        } if self._binders else {}

        conductive_additive_densities = [c._density for c in self._conductive_additives.keys()]
        conductive_additive_density_breakdown = {
            key.name: value * self._conductive_additives[key] for key, value in zip(self._conductive_additives.keys(), conductive_additive_densities)
        } if self._conductive_additives else {}

        self._density_breakdown = active_material_density_breakdown | binder_density_breakdown | conductive_additive_density_breakdown

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
        return round(self._density * KG_TO_G / (M_TO_CM ** 3), 2)
    
    @property
    def specific_cost(self) -> float:
        return round(self._specific_cost, 2)

    @property
    def specific_cost_breakdown(self) -> Dict[str, float]:
        return {key: round(value, 4) for key, value in self._specific_cost_breakdown.items()}
    
    @property
    def density_breakdown(self) -> Dict[str, float]:
        return {key: round(value * KG_TO_G / (M_TO_CM ** 3), 4) for key, value in self._density_breakdown.items()}

    @property
    def color(self) -> str:
        return self._color

    def __str__(self) -> str:
        return self._name if self._name else "Electrode Formulation"
    
    def __repr__(self) -> str:
        return self.__str__()

