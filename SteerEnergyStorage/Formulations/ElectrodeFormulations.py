from SteerEnergyStorage.Materials.ElectrodeMaterials import _ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Utils import get_colorway


class ElectrodeFormulation():
    
    def __init__(self, 
                 active_materials: dict[_ActiveMaterial, float], 
                 binder: dict[Binder, float] = {}, 
                 conductive_additive: dict[ConductiveAdditive, float] = {},
                 name: str = None
                 ):
        """
        Initialize an object that represents an electrode formulation
        
        :param active_materials: dict[ActiveMaterial, float]: dictionary containing the active materials and their mass fractions in percent
        :param binder: Binder: binder used in the formulation
        :param conductive_additive: ConductiveAdditive: conductive additive used in the formulation
        :param porosity: float: porosity of the electrode in %
        """
        self._active_materials = {key: value/100 for key, value in active_materials.items()}
        self._binder = {key: value/100 for key, value in binder.items()} if binder != None else None
        self._conductive_additive = {key: value/100 for key, value in conductive_additive.items()} if conductive_additive != None else None
        self._name = name
        self._validate_formulation()
        self._get_color_map()

    def _get_color_map(self):

        if len(self._active_materials) > 0:
            n = len(self._active_materials)
            active_material_colors = get_colorway("#FFC133", "#FF6833", n)
            am_color_dict = {key.name: value for key, value in zip(self._active_materials.keys(), active_material_colors)}

        if len(self._binder) > 0:
            n = len(self._binder)
            binder_colors = get_colorway("blue", "green", n)
            binder_color_dict = {key.name: value for key, value in zip(self._binder.keys(), binder_colors)}

        if len(self._conductive_additive) > 0:
            n = len(self._conductive_additive)
            ca_colors = get_colorway("purple", "orange", n)
            ca_color_dict = {key.name: value for key, value in zip(self._conductive_additive.keys(), ca_colors)}

        self._color_map = {**am_color_dict, **binder_color_dict, **ca_color_dict}

    def _validate_formulation(self):

        if len(self._active_materials) == 0 and self._binder == {} and self._conductive_additive == {}:
            return None

        if round(sum(self._active_materials.values()) + sum(self._conductive_additive.values()) + sum(self._binder.values()), 0) != 1:
            raise ValueError("The mass fractions of the active materials must sum to 100%")
        
        if len([am.name for am in self._active_materials.keys()]) != len(set([am.name for am in self._active_materials.keys()])):
            raise ValueError("The active materials must have unique names")
        
        if len([b.name for b in self._binder.keys()]) != len(set([b.name for b in self._binder.keys()])):
            raise ValueError("The binders must have unique names")

        if len([ca.name for ca in self._conductive_additive.keys()]) != len(set([ca.name for ca in self._conductive_additive.keys()])):
            raise ValueError("The conductive additives must have unique names")
        
    @property
    def name(self):
        return self._name

    @property
    def active_materials(self):
        return {key: value*100 for key, value in self._active_materials.items()}
    
    @property
    def binder(self):
        return {key: value*100 for key, value in self._binder.items()}
    
    @property
    def conductive_additive(self):
        return {key: value*100 for key, value in self._conductive_additive.items()}

    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"Electrode Formulation"
    
    def __repr__(self):
        return self.__str__()
    