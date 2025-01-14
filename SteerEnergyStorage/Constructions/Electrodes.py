import numpy as np
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector


class Electrode():

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 swell_factor: float = 1.0,
                 bare_tab_area: float = 8.22
                 ):
        """
        Initialize an object that represents an electrode
        :param Formulation: ElectrodeFormulation: formulation of the electrode
        :mass_loading: float: mass loading of the electrode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the electrode
        :param swell_factor: float: factor by which the electrode swells
        :param bare_tab_area: float: area of the bare tab in cm^2
        """
        self._formulation = formulation
        self._current_collector = current_collector
        self._mass_loading = mass_loading
        self._swell_factor = swell_factor
        self._bare_tab_area = bare_tab_area

        self._single_sided_thickness = self._calculate_single_sided_thickness()
        self._double_sided_thickness = self._calculate_double_sided_thickness()

    @property
    def bare_tab_area(self):
        return np.round(self._bare_tab_area, 2)

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
        try:
            return np.round(self._single_sided_area, 2)
        except AttributeError:
            raise AttributeError("The single sided area has not been calculated yet. You need to create a stack with a cathode to do so.")
        
    @property
    def double_sided_area(self):
        try:
            return np.round(self._double_sided_area, 2)
        except AttributeError:
            raise AttributeError("The double sided area has not been calculated yet. You need to create a stack with a cathode to do so.")
        
    @property
    def coat_mass_per_sheet(self):
        try:
            return np.round(self._coat_mass_per_sheet, 2)
        except AttributeError:
            return "The coat mass per sheet has not been calculated yet. You need to create a stack with a cathode to do so."
        
    @property
    def foil_mass_per_sheet(self):
        try:
            return np.round(self._foil_mass_per_sheet, 2)
        except AttributeError:
            return "The foil mass per sheet has not been calculated yet. You need to create a stack with a cathode to do so."
    
    def _calculate_single_sided_thickness(self):
        """
        Calculate the single sided thickness of the electrode
        """
        return (self._mass_loading / self._formulation._calender_density)/1000 * 10000 # in um
    
    def _calculate_double_sided_thickness(self):
        """
        Calculate the double sided thickness of the electrode
        """
        return self._single_sided_thickness * 2 + self._current_collector.thickness
    
    def calculate_coat_mass_per_sheet(self):
        """
        Calculate the mass of the electrode coating per sheet
        """
        return 2*(self._mass_loading * self.single_sided_area) / 1000
    
    def calculate_foil_mass_per_sheet(self):
        """
        Calculate the mass of the current collector per sheet
        """
        return (self.single_sided_area + self._bare_tab_area) * self._current_collector.thickness/1000 * self._current_collector._density
    
    def __str__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    

class Anode(Electrode):
    
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
                 swell_factor: float = 1.0,
                 overhang: float = 0,
                 bare_tab_area: float = 7.55
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
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         swell_factor=swell_factor,
                         bare_tab_area=bare_tab_area)
        
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
                 single_sided_area: float,
                 current_collector: CurrentCollector,
                 swell_factor: float = 1.0,
                 bare_tab_area: float = 8.22
                 ):
        """
        Initialize an object that represents a cathode
        :param Formulation: ElectrodeFormulation: formulation of the cathode
        :mass_loading: float: mass loading of the cathode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the cathode
        :param area: float: area of the cathode in cm^2
        :param swell_factor: float: factor by which the cathode swells
        :param bare_tab_area: float: area of the bare tab in cm^2
        """
        super().__init__(formulation=formulation,
                         mass_loading=mass_loading,
                         current_collector=current_collector,
                         swell_factor=swell_factor,
                         bare_tab_area=bare_tab_area)
        
        self._single_sided_area = single_sided_area

    @property
    def single_sided_area(self):
        return np.round(self._single_sided_area, 2)
    
    def __str__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"

        