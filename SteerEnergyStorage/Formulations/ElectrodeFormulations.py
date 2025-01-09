from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial
from SteerEnergyStorage.Materials.ElectrodeMaterials import Binder
from SteerEnergyStorage.Materials.ElectrodeMaterials import ConductiveAdditive


class ElectrodeFormulation():
    
    def __init__(self, 
                 active_materials: dict[ActiveMaterial, float], 
                 binder: dict[Binder, float] = None, 
                 conductive_additive: dict[ConductiveAdditive, float] = None,
                 porosity: float = 30
                 ):
        """
        Initialize an object that represents an electrode formulation
        :param active_materials: dict[ActiveMaterial, float]: dictionary containing the active materials and their mass fractions
        :param binder: Binder: binder used in the formulation
        :param conductive_additive: ConductiveAdditive: conductive additive used in the formulation
        :param porosity: float: porosity of the electrode in %
        """
        self._active_materials = active_materials
        self._binder = binder
        self._conductive_additive = conductive_additive
        self._porosity = porosity

        if round(sum(active_materials.values()) + sum(conductive_additive.values()) + sum(binder.values()), 0) != 100:
            raise ValueError("The mass fractions of the active materials must sum to 100%")
            
    @property
    def porosity(self):
        return self._porosity

    @property
    def active_materials(self):
        return self._active_materials
    
    @property
    def binder(self):
        return self._binder
    
    @property
    def conductive_additive(self):
        return self._conductive_additive

    def __str__(self):
        return f"Formulation made of {self.material}"
    