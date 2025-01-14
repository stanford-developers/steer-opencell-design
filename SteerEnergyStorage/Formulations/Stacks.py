from SteerEnergyStorage.Constructions.Electrodes import Anode
from SteerEnergyStorage.Constructions.Electrodes import Cathode
from SteerEnergyStorage.Materials.Seperators import Separator


class Stack():

    def __init__(self, 
                 anode: Anode,
                 cathode: Cathode,
                 seperator: Separator,
                 anode_mass_loading: float = 1.0, 
                 cathode_mass_loading: float = 1.0,
                 n_p_ratio: float = 1.3):
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell
        :param anode_formulation: ElectrodeFormulation: formulation of the anode
        :param cathode_formulation: ElectrodeFormulation: formulation of the cathode
        :param seperator: Separator: separator used in the stack
        :param anode_mass_loading: float: mass loading of the anode in the stack
        :param cathode_mass_loading: float: mass loading of the cathode in the stack
        :param n_p_ratio: float: ratio of the number of moles in the negative electrode to the number of moles in the positive electrode
        """
        self._anode = anode
        self._cathode = cathode
        self._seperator = seperator
        self._anode_mass_loading = anode_mass_loading
        self._cathode_mass_loading = cathode_mass_loading
        self._n_p_ratio = n_p_ratio

        # get anode area
        self._anode._single_sided_area = self._cathode._single_sided_area * (1 + self._anode._overhang / 100)
        self._anode._coat_mass_per_sheet = self._anode.calculate_coat_mass_per_sheet()
        self._anode._current_collector._mass = self._anode.calculate_foil_mass_per_sheet()

        # get cathode properties
        self._cathode._coat_mass_per_sheet = self._cathode.calculate_coat_mass_per_sheet()
        self._cathode._current_collector._mass = self._cathode.calculate_foil_mass_per_sheet()

    @property
    def anode(self):
        return self._anode
    
    @property
    def cathode(self):
        return self._cathode

    @property
    def n_p_ratio(self):
        return self._n_p_ratio

    @property
    def seperator(self):
        return self._seperator
    
    @property
    def anode_mass_loading(self):
        return self._anode_mass_loading
    
    @property
    def cathode_mass_loading(self):
        return self._cathode_mass_loading
    
    def __str__(self):
        return f"Stack with an anode formulation of {self.anode_formulation} and a cathode formulation of {self.cathode_formulation}"
    
    def __repr__(self):
        return f"Stack with an anode formulation of {self.anode_formulation} and a cathode formulation of {self.cathode_formulation}"
    
