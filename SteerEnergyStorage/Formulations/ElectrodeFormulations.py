import numpy as np

from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial
from SteerEnergyStorage.Materials.ElectrodeMaterials import Binder
from SteerEnergyStorage.Materials.ElectrodeMaterials import ConductiveAdditive


class ElectrodeFormulation():
    
    def __init__(self, 
                 active_materials: dict[ActiveMaterial, float], 
                 binder: dict[Binder, float] = None, 
                 conductive_additive: dict[ConductiveAdditive, float] = None,
                 calender_density: float = 2.6,
                 swell_factor: float = 1
                 ):
        """
        Initialize an object that represents an electrode formulation
        :param active_materials: dict[ActiveMaterial, float]: dictionary containing the active materials and their mass fractions
        :param binder: Binder: binder used in the formulation
        :param conductive_additive: ConductiveAdditive: conductive additive used in the formulation
        :param porosity: float: porosity of the electrode in %
        :param swell_factor: float: factor by which the electrode swells
        """
        self._active_materials = active_materials
        self._binder = binder
        self._conductive_additive = conductive_additive
        self._swell_factor = swell_factor
        self._calender_density = calender_density

        self._porosity = self._calculate_porosity()

        if round(sum(active_materials.values()) + sum(conductive_additive.values()) + sum(binder.values()), 0) != 100:
            raise ValueError("The mass fractions of the active materials must sum to 100%")
        
    @property
    def calender_density(self):
        return self._calender_density

    @property
    def swell_factor(self):
        return self._swell_factor

    @property
    def active_materials(self):
        return self._active_materials
    
    @property
    def binder(self):
        return self._binder
    
    @property
    def conductive_additive(self):
        return self._conductive_additive
    
    @property
    def porosity(self):
        return np.round(self._porosity, 2)
    
    def _calculate_porosity(self):
        """
        Function to calculate the overall porisity of the electrode formulation
        """
        active_mass_fractions = [v/100 for v in self._active_materials.values()]
        active_mass_densities = [am._density for am in self._active_materials.keys()]
        
        conductive_aids_fractions = [v/100 for v in self._conductive_additive.values()]
        conductive_aids_densities = [ca._density for ca in self._conductive_additive.keys()]

        binder_fractions = [v/100 for v in self._binder.values()]
        binder_densities = [b._density for b in self._binder.keys()]

        theoretical_specific_volume = sum(amf*(1/amd) for amf, amd in zip(active_mass_fractions, active_mass_densities)) + \
                                      sum(caf*(1/cad) for caf, cad in zip(conductive_aids_fractions, conductive_aids_densities)) + \
                                      sum(bf*(1/bd) for bf, bd in zip(binder_fractions, binder_densities))
        
        return (1 - (theoretical_specific_volume*self.calender_density)) * 100

    def __str__(self):
        return f"Formulation made of {self.material}"
    