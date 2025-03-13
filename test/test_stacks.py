import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        #### stack 1 ####
        # construct cathode
        cathode_active_material1 = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive1 = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder1 = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation1 = ElectrodeFormulation(active_materials={cathode_active_material1: 89},
                                                    binder={cathode_binder1: 5},
                                                    conductive_additive={cathode_conductive_additive1: 6})

        cathode_current_collector1 = CurrentCollector(formula="Al", 
                                                      thickness=15, 
                                                      length=16.0,
                                                      width=10.8,
                                                      bare_tab_area=8.22)

        cathode1 = Cathode(formulation=cathode_formulation1,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector1,
                          calender_density=2.60)

        # construct anode
        anode_active_material1 = AnodeMaterial(name="Faradion_HC",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive1 = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder1 = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation1 = ElectrodeFormulation(active_materials={anode_active_material1: 88},
                                                 binder={anode_binder1: 3},
                                                 conductive_additive={anode_conductive_additive1: 9})
        
        anode_current_collector1 = CurrentCollector(formula="Cu",
                                                   thickness=15,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_tab_area=7.55)
        
        anode1 = Anode(formulation=anode_formulation1,
                      mass_loading=5.25,
                      current_collector=anode_current_collector1,
                      calender_density=0.85)

        # construct separator
        separator1 = Separator(thickness=16, 
                               areal_cost=0.9, 
                               density=0.4, 
                               slit_width=11.0, 
                               porosity=47, 
                               fold_length=18.6)

        # construct the stack
        self.stack1 = Stack(anode=anode1, 
                           cathode=cathode1,
                           separator=separator1, 
                           name="stack",
                           n_layers=26)
        
        #### stack 2 ####
        # construct cathode
        cathode_active_material2 = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive2 = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder2 = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation2 = ElectrodeFormulation(active_materials={cathode_active_material2: 89},
                                                   binder={cathode_binder2: 5},
                                                   conductive_additive={cathode_conductive_additive2: 6})

        cathode_current_collector2 = CurrentCollector(formula="Al", 
                                                      thickness=15, 
                                                      length=16.0,
                                                      width=10.8,
                                                      bare_tab_area=8.22)

        cathode2 = Cathode(formulation=cathode_formulation2,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector2,
                          calender_density=2.60)

        # construct anode
        anode_active_material2 = AnodeMaterial(name="Faradion_HC",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive2 = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder2 = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation2 = ElectrodeFormulation(active_materials={anode_active_material2: 88},
                                                 binder={anode_binder2: 3},
                                                 conductive_additive={anode_conductive_additive2: 9})
        
        anode_current_collector2 = CurrentCollector(formula="Cu",
                                                    thickness=15,
                                                    length=16.0,
                                                    width=10.8,
                                                    bare_tab_area=7.55)
        
        anode2 = Anode(formulation=anode_formulation2,
                      mass_loading=5.25,
                      current_collector=anode_current_collector2,
                      calender_density=0.85)

        # construct separator
        separator2 = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              slit_width=11.0, 
                              porosity=47, 
                              fold_length=18.6)

        # construct the stack
        self.stack2 = Stack(anode=anode2, 
                            cathode=cathode2,
                            separator=separator2, 
                            name="stack",
                            n_layers=50)
        
    def test_stack1(self):
        self.assertEqual(self.stack1.n_layers, 26)
        self.assertEqual(self.stack1.n_cathode, 26)
        self.assertEqual(self.stack1.n_anode, 27)
        self.assertEqual(self.stack1.n_separator, 56)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.cathode], 4), 0.115)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.anode], 4), 0.1144)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.separator], 4), 0.0074)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.cathode], 115.03)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.anode], 114.43)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.separator], 7.36)
        self.assertEqual(self.stack1.pore_volume, 44.06)
        self.assertEqual(round(self.stack1._pore_volume, 6), 0.000044)
        self.assertEqual(self.stack1.thickness, 7.19)

    def test_stack2(self):
        self.assertEqual(self.stack2.n_layers, 50)
        self.assertEqual(self.stack2.n_cathode, 50)
        self.assertEqual(self.stack2.n_anode, 51)
        self.assertEqual(self.stack2.n_separator, 104)
        self.assertEqual(round(self.stack2._mass_breakdown[self.stack2.cathode], 4), 0.2212)
        self.assertEqual(round(self.stack2._mass_breakdown[self.stack2.anode], 4), 0.2162)
        self.assertEqual(round(self.stack2._mass_breakdown[self.stack2.separator], 4), 0.0137)
        self.assertEqual(self.stack2.mass_breakdown[self.stack2.cathode], 221.21)
        self.assertEqual(self.stack2.mass_breakdown[self.stack2.anode], 216.15)
        self.assertEqual(self.stack2.mass_breakdown[self.stack2.separator], 13.67)
        self.assertEqual(self.stack2.pore_volume, 83.28)
        self.assertEqual(round(self.stack2._pore_volume, 6), 0.000083)
        self.assertEqual(self.stack2.thickness, 13.62)

    def test_stack1_n_setter(self):
        self.stack1.n_layers = 50
        self.assertEqual(self.stack1.n_cathode, 50)
        self.assertEqual(self.stack1.n_anode, 51)
        self.assertEqual(self.stack1.n_separator, 104)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.cathode], 4), 0.2212)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.anode], 4), 0.2162)
        self.assertEqual(round(self.stack1._mass_breakdown[self.stack1.separator], 4), 0.0137)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.cathode], 221.21)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.anode], 216.15)
        self.assertEqual(self.stack1.mass_breakdown[self.stack1.separator], 13.67)
        self.assertEqual(self.stack1.pore_volume, 83.28)
        self.assertEqual(round(self.stack1._pore_volume, 6), 0.000083)
        self.assertEqual(self.stack1.thickness, 13.62)
