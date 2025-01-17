import numpy as np
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector


class Electrode():

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 single_sided_area: float,
                 swell_factor: float = 1.0
                 ):
        """
        Initialize an object that represents an electrode
        :param Formulation: ElectrodeFormulation: formulation of the electrode
        :mass_loading: float: mass loading of the electrode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the electrode
        :param swell_factor: float: factor by which the electrode swells
        """
        self._formulation = formulation
        self._current_collector = current_collector
        self._mass_loading = mass_loading
        self._swell_factor = swell_factor
        self._single_sided_area = single_sided_area
        
        self._coating_mass = self._single_sided_area * (self._mass_loading/1000) * 2
        self._mass = self._coating_mass + self._current_collector.mass

        self._single_sided_thickness = (self._mass_loading / self._formulation._calender_density)/1000 * 10000 # in um
        self._double_sided_thickness = self._single_sided_thickness * 2 + self._current_collector.thickness

        self._pore_volume = self._single_sided_area * self._single_sided_thickness/10000 * self._swell_factor * 2 * self._formulation.porosity/100

    @property
    def pore_volume(self):
        return np.round(self._pore_volume, 2)

    @property
    def mass(self):
        return np.round(self._mass, 2)
    
    @property
    def coating_mass(self):
        return np.round(self._coating_mass, 2)

    @property
    def single_sided_area(self):
        return np.round(self._single_sided_area, 2)

    @property
    def single_sided_area(self):
        return np.round(self._single_sided_area)

    @property
    def single_sided_thickness(self):
        return np.round(self._single_sided_thickness, 1)
    
    @property
    def double_sided_thickness(self):
        return np.round(self._double_sided_thickness, 1)

    @property
    def swell_factor(self):
        return self._swell_factor

    @property
    def mass_loading(self):
        return self._mass_loading

    @property
    def formulation(self):
        return self._formulation
    
    @property
    def current_collector(self):
        return self._current_collector
    
    @property
    def single_sided_area(self):
        return np.round(self._single_sided_area, 2)
    
    def __str__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    

class Anode(Electrode):
    
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 cathode_mate_area: float,
                 swell_factor: float = 1.0,
                 bare_tab_area: float = 7.55,
                 overhang: float = 0
                 ):
        """
        Initialize an object that represents an anode
        :param formulation: ElectrodeFormulation: formulation of the anode
        :mass_loading: float: mass loading of the anode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the anode
        :param swell_factor: float: factor by which the anode swells
        :param overhang: float: overhang of the anode in %
        :param bare_tab_area: float: area of the bare tab in cm^2
        """
        anode_single_sided_area = cathode_mate_area * (1 + overhang / 100)

        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         single_sided_area=anode_single_sided_area,
                         swell_factor=swell_factor)
        
        self._overhang = overhang

    @property
    def overhang(self):
        return np.round(self._overhang, 2)
    
    def __str__(self):
        return f"Anode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Anode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    

class Cathode(Electrode):

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 single_sided_area: float,
                 swell_factor: float = 1.0
                 ):
        """
        Initialize an object that represents a cathode
        :param Formulation: ElectrodeFormulation: formulation of the cathode
        :mass_loading: float: mass loading of the cathode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the cathode
        :param area: float: area of the cathode in cm^2
        :param swell_factor: float: factor by which the cathode swells
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         single_sided_area=single_sided_area,
                         swell_factor=swell_factor)
    
    def __str__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"

        