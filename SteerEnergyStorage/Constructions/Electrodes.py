from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector

MG_TO_KG = 1e-6
CM_TO_M = 1e-2
KG_TO_MG = 1e6
M_TO_CM = 1e2
G_TO_KG = 1e-3
KG_TO_G = 1e3
M_TO_UM = 1e6

class Electrode:
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 swell_factor: float,
                 name: str = 'Electrode'):
        """
        Initialize an object that represents an electrode
        :param formulation: ElectrodeFormulation: formulation of the electrode
        :param mass_loading: float: mass loading of the electrode in mg/cm^2
        :param current_collector: CurrentCollector: current collector used in the electrode
        :param length: float: length of the electrode in mm
        :param width: float: width of the electrode in mm
        :param calender_density: float: density of the electrode after calendering in g/cm^3
        :param swell_factor: float: factor by which the electrode swells
        :param name: str: name of the electrode
        """
        self._name = name
        self._formulation = formulation
        self._current_collector = current_collector
        self._mass_loading = mass_loading * (MG_TO_KG / CM_TO_M**2)
        self._calender_density = calender_density * (G_TO_KG / CM_TO_M**3)
        self._swell_factor = swell_factor
        self._single_sided_area = self._current_collector._coated_area
        self._porosity = self._calculate_porosity()
        self._coating_mass = self._single_sided_area * self._mass_loading * 2
        self._mass = self._coating_mass + self._current_collector._mass

        # calculate the thickness of the electrode
        self._material_thickness = self._mass_loading / self._calender_density
        self._double_sided_thickness = self._material_thickness * 2 + self._current_collector._thickness
        self._pore_volume = self._single_sided_area * self._material_thickness * self._swell_factor * 2 * self._porosity

        # get the mass of each component in the electrode
        self._active_masses = {am: (mf * self._coating_mass) for am, mf in self._formulation._active_materials.items()}
        self._binder_masses = {bi: (mf * self._coating_mass) for bi, mf in self._formulation._binder.items()}
        self._conductive_additive_masses = {ca: (mf * self._coating_mass) for ca, mf in self._formulation._conductive_additive.items()}

        # get the cost of each component in the electrode
        self._active_material_costs = {am: m * am._specific_cost for am, m in self._active_masses.items()}
        self._binder_costs = {bi: m * bi._specific_cost for bi, m in self._binder_masses.items()}
        self._conductive_additive_costs = {ca: m * ca._specific_cost for ca, m in self._conductive_additive_masses.items()}
        
        # calculate the total cost of the electrode
        self._cost = (sum(self._active_material_costs.values()) + 
                      sum(self._binder_costs.values()) + 
                      sum(self._conductive_additive_costs.values()) + 
                      self._current_collector._cost)
        
    def _calculate_porosity(self):
        """
        Function to calculate the overall porisity of the electrode formulation
        """
        active_mass_fractions = [v for v in self._formulation._active_materials.values()]
        active_mass_densities = [am._density for am in self._formulation._active_materials.keys()]
        
        conductive_aids_fractions = [v for v in self._formulation._conductive_additive.values()]
        conductive_aids_densities = [ca._density for ca in self._formulation._conductive_additive.keys()]

        binder_fractions = [v for v in self._formulation._binder.values()]
        binder_densities = [b._density for b in self._formulation._binder.keys()]

        theoretical_specific_volume = sum(amf/amd for amf, amd in zip(active_mass_fractions, active_mass_densities)) + \
                                      sum(caf/cad for caf, cad in zip(conductive_aids_fractions, conductive_aids_densities)) + \
                                      sum(bf/bd for bf, bd in zip(binder_fractions, binder_densities))
        
        return (1 - (theoretical_specific_volume * self._calender_density))
    
    @property
    def porosity(self):
        return round(self._porosity * 100, 2)
    
    @property
    def calender_density(self):
        return round(self._calender_density * (KG_TO_G / M_TO_CM**3), 2)

    @property
    def formulation(self):
        return self._formulation

    @property
    def mass_loading(self):
        return round(self._mass_loading * (KG_TO_MG / M_TO_CM**2), 2)

    @property
    def current_collector(self):
        return self._current_collector

    @property
    def single_sided_area(self):
        return round(self._single_sided_area, 2)

    @property
    def swell_factor(self):
        return self._swell_factor

    @property
    def name(self):
        return self._name

    @property
    def coating_mass(self):
        return round(self._coating_mass * KG_TO_G, 2)

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def material_thickness(self):
        return round(self._material_thickness * M_TO_UM, 2)

    @property
    def double_sided_thickness(self):
        return round(self._double_sided_thickness * M_TO_UM, 2)

    @property
    def pore_volume(self):
        return round(self._pore_volume * M_TO_CM**3, 2)

    @property
    def cost(self):
        return round(self._cost, 2)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()


class Anode(Electrode):
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 swell_factor: float = 1.0,
                 name: str = 'Anode'):
        """
        Initialize an object that represents an anode
        :param formulation: ElectrodeFormulation: formulation of the anode
        :param mass_loading: float: mass loading of the anode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the anode
        :param length: float: length of the anode in mm
        :param width: float: width of the anode in mm
        :param calender_density: float: density of the anode after calendering in g/cm^3
        :param swell_factor: float: factor by which the anode swells
        :param overhang: float: overhang of the anode in %
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         calender_density=calender_density,
                         swell_factor=swell_factor,
                         name=name)
        
        # determine the directions for the active material half curves
        for am in self.formulation._active_materials.keys():
            am._half_cell_curve = am._determine_half_cell_direction('anode')

    @property
    def overhang(self):
        if hasattr(self, '_overhang'):
            return self._overhang
        else:
            return AttributeError("Overhang not calculated yet")


class Cathode(Electrode):
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 calender_density: float,
                 swell_factor: float = 1.0,
                 name: str = 'Cathode'):
        """
        Initialize an object that represents a cathode
        :param formulation: ElectrodeFormulation: formulation of the cathode
        :param mass_loading: float: mass loading of the cathode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the cathode
        :param length: float: length of the cathode in mm
        :param width: float: width of the cathode in mm
        :param calender_density: float: density of the cathode after calendering in g/cm^3
        :param swell_factor: float: factor by which the cathode swells
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         calender_density=calender_density,
                         swell_factor=swell_factor,
                         name=name)
        
        # determine the directions for the active material half curves
        for am in self.formulation._active_materials.keys():
            am._half_cell_curve = am._determine_half_cell_direction('cathode')
