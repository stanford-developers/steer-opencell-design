from SteerEnergyStorage.Constructions.Electrodes import Anode
from SteerEnergyStorage.Constructions.Electrodes import Cathode
from SteerEnergyStorage.Materials.Separators import Separator

KG_TO_G = 1e3
M_TO_CM = 1e2
M_TO_MM = 1e3

class Stack():

    def __init__(self, 
                 anode: Anode,
                 cathode: Cathode,
                 n_stacks: int,
                 seperator: Separator,
                 n_p_ratio: float,
                 name: str = None):
        """
        Initialize an object that represents an electrochemical stack within an electrochemical cell
        :param anode: Anode: anode used in the stack
        :param cathode: Cathode: cathode used in the stack
        :param n_stacks: int: number of stacks in the cell
        :param seperator: Separator: seperator used in the stack
        :param n_p_ratio: float: n/p ratio of the stack
        :param name: str: name of the stack
        """
        self._cathode = cathode
        self._anode = self._check_anode(anode)
        self._seperator = seperator
        self._n_p_ratio = n_p_ratio
        self._name = name

        self._n_stacks = n_stacks
        self._n_cathode = n_stacks
        self._n_anode = n_stacks + 1
        self._n_seperator = self._n_cathode + self._n_anode + 2

        self._active_geometric_area = self._cathode._single_sided_area * 2 * self._n_stacks

        # calculate anode properties
        self._anode._overhang = (self._anode._single_sided_area/self._cathode._single_sided_area) - 1

        # calculate separator properties
        self._seperator._area = self._seperator._slit_width * self._seperator._fold_length * self._n_seperator
        self._seperator._mass = self._seperator._thickness * self._seperator._area * self._seperator._density
        self._seperator._cost = self._seperator._area * self._seperator._areal_cost
        self._seperator._pore_volume = self._seperator._thickness * self._seperator._area * self._seperator._porosity

        # calculate the mass breakdown
        self._mass_breakdown = {
            self._cathode: self._cathode._mass * self._n_cathode,
            self._anode: self._anode._mass * self._n_anode,
            self._seperator: self._seperator._mass
        }
        self._mass = sum(self._mass_breakdown.values())

        # calculate the cathode mass breakdown
        self._cathode_mass_breakdown = {
            "Active Material": {active_material: mass * self._n_cathode for active_material, mass in self._cathode._active_masses.items()},
            "Binder": {binder: mass * self._n_cathode for binder, mass in self._cathode._binder_masses.items()},
            "Conductive Additive": {conductive_additive: mass * self._n_cathode for conductive_additive, mass in self._cathode._conductive_additive_masses.items()},
            "Current Collector": self._cathode._current_collector.mass * self._n_cathode
        }

        # calculate the anode mass breakdown
        self._anode_mass_breakdown = {
            "Active Materials": {active_material: mass * self._n_anode for active_material, mass in self._anode._active_masses.items()},
            "Binders": {binder: mass * self._n_anode for binder, mass in self._anode._binder_masses.items()},
            "Conductive Additives": {conductive_additive: mass * self._n_anode for conductive_additive, mass in self._anode._conductive_additive_masses.items()},
            "Current Collector": self._anode._current_collector.mass * self._n_anode
        }

        # calculate pore volume
        total_cathode_pore_volume = self._cathode._pore_volume * self._n_cathode
        total_anode_pore_volume = self._anode._pore_volume * self._n_anode
        total_seperator_pore_volume = self._seperator._pore_volume
        self._pore_volume = total_anode_pore_volume + total_cathode_pore_volume + total_seperator_pore_volume

        # calculate the thickness of the stack
        total_cathode_thickness = self._cathode._double_sided_thickness * self._n_cathode
        total_anode_thickness = self._anode._double_sided_thickness * self._n_anode
        total_seperator_thickness = self._seperator._thickness * self._n_seperator
        self._thickness = total_anode_thickness + total_cathode_thickness + total_seperator_thickness

        # calcualte the cost breakdown
        self._cost_breakdown = {
            self._cathode: self._cathode._cost * self._n_cathode,
            self._anode: self._anode._cost * self._n_anode,
            self._seperator: self._seperator._cost
        }

        # calculate the total cost
        self._cost = sum(self._cost_breakdown.values())

        # get the cathode cost breakdown
        self._cathode_cost_breakdown = {
            "Active Material": {active_material: cost*self._n_stacks for active_material, cost in self._cathode._active_material_costs.items()},
            "Binder": {binder: cost*self._n_stacks for binder, cost in self._cathode._binder_costs.items()},
            "Conductive Additive": {conductive_additive: cost*self._n_stacks for conductive_additive, cost in self._cathode._conductive_additive_costs.items()},
            "Current Collector": self._cathode._current_collector._cost * self._n_stacks
        }

        # get the anode cost breakdown
        self._anode_cost_breakdown = {
            "Active Materials": {active_material: cost*(self._n_stacks + 1) for active_material, cost in self._anode._active_material_costs.items()},
            "Binders": {binder: cost*(self._n_stacks + 1) for binder, cost in self._anode._binder_costs.items()},
            "Conductive Additives": {conductive_additive: cost*(self._n_stacks + 1) for conductive_additive, cost in self._anode._conductive_additive_costs.items()},
            "Current Collector": self._anode._current_collector._cost * (self._n_stacks + 1)
        }

    def _check_anode(self, anode: Anode):

        if anode._current_collector._length < self._cathode._current_collector._length:
            raise ValueError("Anode length must be greater or equal to cathode length")
        
        if anode._current_collector._width < self._cathode._current_collector._width:
            raise ValueError("Anode width must be greater or equal to cathode width")

        return anode
        
    @property
    def name(self):
        return self._name

    @property
    def cost_breakdown(self):
        return {item: round(value, 3) for item, value in self._cost_breakdown.items()}
    
    @property
    def cathode_cost_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._cathode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_cost_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._anode_cost_breakdown.items()
        }
        return rounded_dict
    
    @property
    def mass_breakdown(self):
        return {item: round(value * KG_TO_G, 3) for item, value in self._mass_breakdown.items()}
    
    @property
    def cathode_mass_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value * KG_TO_G, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._cathode_mass_breakdown.items()
        }
        return rounded_dict
    
    @property
    def anode_mass_breakdown(self):
        rounded_dict = {
            item: (
                {key: round(value * KG_TO_G, 3) for key, value in value.items()}
                if isinstance(value, dict) else round(value, 3)
            )
            for item, value in self._anode_mass_breakdown.items()
        }
        return rounded_dict

    @property
    def cost(self):
        return round(self._cost, 2)

    @property
    def thickness(self):
        return round(self._thickness * M_TO_MM, 2)

    @property
    def active_geometric_area(self):
        return round(self._active_geometric_area * M_TO_CM**2, 2)

    @property
    def pore_volume(self):
        return round(self._pore_volume * M_TO_CM**3, 2)

    @property
    def mass(self):
        return round(self._mass * KG_TO_G, 2)
    
    @property
    def mass_breakdown(self):
        return {item: round(value * KG_TO_G, 2) for item, value in self._mass_breakdown.items()}

    @property
    def n_stacks(self):
        return self._n_stacks
    
    @property
    def n_cathode(self):
        return self._n_cathode
    
    @property
    def n_anode(self):
        return self._n_anode
    
    @property
    def n_seperator(self):
        return self._n_seperator

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
    
    def __str__(self):
        if self.name != None:
            return f"{self.name}"
        else:
            return f"stack"
        
    def __repr__(self):
        return self.__str__()
    