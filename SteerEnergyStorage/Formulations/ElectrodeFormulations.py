from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive


class ElectrodeFormulation():
    
    def __init__(self, 
                 active_materials: dict[ActiveMaterial, float], 
                 binder: dict[Binder, float] = None, 
                 conductive_additive: dict[ConductiveAdditive, float] = None,
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

        if round(sum(active_materials.values()) + sum(conductive_additive.values()) + sum(binder.values()), 0) != 100:
            raise ValueError("The mass fractions of the active materials must sum to 100%")
        
        if len([am.name for am in active_materials.keys()]) != len(set([am.name for am in active_materials.keys()])):
            raise ValueError("The active materials must have unique names unique")
        
        if len([b.name for b in binder.keys()]) != len(set([b.name for b in binder.keys()])):
            raise ValueError("The binders must have unique names unique")

        if len([ca.name for ca in conductive_additive.keys()]) != len(set([ca.name for ca in conductive_additive.keys()])):
            raise ValueError("The conductive additives must have unique names unique")
        
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
    