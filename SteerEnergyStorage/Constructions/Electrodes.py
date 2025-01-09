from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector


class Electrode():

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector,
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
    
    def __str__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Electrode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    

class Anode(Electrode):
    
    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector
                 ):
        """
        Initialize an object that represents an anode
        :param Formulation: ElectrodeFormulation: formulation of the anode
        :mass_loading: float: mass loading of the anode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the anode
        """
        super().__init__(formulation, mass_loading, current_collector)
    
    def __str__(self):
        return f"Anode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Anode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    

class Cathode(Electrode):

    def __init__(self, 
                 formulation: ElectrodeFormulation,
                 mass_loading: float,
                 current_collector: CurrentCollector
                 ):
        """
        Initialize an object that represents a cathode
        :param Formulation: ElectrodeFormulation: formulation of the cathode
        :mass_loading: float: mass loading of the cathode in mg/cm^3
        :param current_collector: CurrentCollector: current collector used in the cathode
        """
        super().__init__(formulation, mass_loading, current_collector)
    
    def __str__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"
    
    def __repr__(self):
        return f"Cathode with a formulation of {self.formulation} and a current collector of {self.current_collector}"

        