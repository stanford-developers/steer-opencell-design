import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Constructions.Cells import StackedPouchCell
from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Seperators import Separator
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte


class TestCells(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode 1
        cam1 = ActiveMaterial(name="Faradion_Gen2_4.25V", 
                              formula="Li2MnSiO4", 
                              specific_cost=11.26, 
                              density=4, 
                              irreversible_capacity_scaling=1, 
                              reversible_capacity_scaling=1)
        
        cca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        cb1 = Binder(name="PVDF", specific_cost=15, density=1.7)
        cf = ElectrodeFormulation(active_materials={cam1: 89}, binder={cb1: 5}, conductive_additive={cca1: 6}, calender_density=2.60)
        ccc = CurrentCollector(name="Aluminium", formula="Al", specific_cost=6.30, density=2.7, thickness=15, coated_area=172.83, bare_tab_area=8.22)
        cathode = Cathode(formulation=cf, mass_loading=10.68, current_collector=ccc, swell_factor=1.0, single_sided_area=172.83)
        
        # construct anode 1
        aam1 = ActiveMaterial(name="Faradion_HC", 
                              formula="Na2Ti3O7", 
                              specific_cost=14.27, 
                              density=1.50, 
                              irreversible_capacity_scaling=1, 
                              reversible_capacity_scaling=1)
        
        aca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        ab1 = Binder(name="PVDF", specific_cost=10, density=1.7)
        af = ElectrodeFormulation(active_materials={aam1: 88}, binder={ab1: 3}, conductive_additive={aca1: 9}, calender_density=0.85)
        acc = CurrentCollector(name="Aluminium", formula="Al", specific_cost=6.30, density=2.7, thickness=15, coated_area=172.83, bare_tab_area=7.55)
        anode = Anode(formulation=af, mass_loading=5.25, current_collector=acc, swell_factor=1.0, cathode_mate_area=172.83)

        # construct stack
        seperator = Separator(name="Celgard_2325", thickness=16, specific_cost=0.2, density=1.4, slit_width=100, porosity=47, fold_length=186, n_stacks=26)
        self.stack = Stack(anode=anode, cathode=cathode, seperator=seperator, n_p_ratio=1.13, n_stacks=26)
        
    def test_cell_effective_areal_capacity(self):
        """
        Test the effective areal capacity of the cell
        """
        self.assertEqual(type(self.stack._active_geometric_area), float)
