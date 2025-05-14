import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import FlatJellyRoll, CylindricalJellyRoll
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import NotchedCurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator

import pandas as pd

class TestFlatJellyRoll(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                 specific_cost=11.26, 
                                                 density=4, 
                                                 irreversible_capacity_scaling=1, 
                                                 reversible_capacity_scaling=1)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                   binders={cathode_binder: 5},
                                                   conductive_additives={cathode_conductive_additive: 6})

        cathode_current_collector = NotchedCurrentCollector(formula="Al", 
                                                            length=110.0,
                                                            width=10.8,
                                                            thickness=5,
                                                            tab_width=0.5,
                                                            tab_length=3.0,
                                                            tab_spacing=3.0,
                                                            bare_length=3)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector,
                          calender_density=2.60)



        # construct anode
        anode_active_material = AnodeMaterial(name="Faradion_HC",
                                              specific_cost=14.27,
                                              density=1.50,
                                              irreversible_capacity_scaling=1,
                                              reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = NotchedCurrentCollector(formula="Cu", 
                                                          length=110.0,
                                                          width=10.8,
                                                          thickness=5,
                                                          tab_width=0.5,
                                                          tab_length=3.0,
                                                          tab_spacing=3.0,
                                                          bare_length=3)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      calender_density=0.85)

        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              width=110, 
                              porosity=47, 
                              fold_length=1110)

        # construct the stack
        self.flat_jelly_roll = FlatJellyRoll(anode=anode, 
                                             cathode=cathode,
                                             separator=separator, 
                                             focal_length=100.0,
                                             name="flat_jelly_roll")

    def test_instantiation(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.flat_jelly_roll, FlatJellyRoll)
        self.assertIsInstance(self.flat_jelly_roll.separator, Separator)

    def test_attributes(self):
        """
        Test flat roll attributes
        """
        self.assertEqual(round(self.flat_jelly_roll._separator._fold_length, 2) , 1.11)
        self.assertEqual(self.flat_jelly_roll._separator.fold_length, 1110)

        self.assertEqual(round(self.flat_jelly_roll._focal_length, 2), 0.1)
        self.assertEqual(round(self.flat_jelly_roll.focal_length, 2), 100)

        self.assertEqual(round(self.flat_jelly_roll._thickness, 4), 0.0027)
        self.assertEqual(self.flat_jelly_roll.thickness, 2.72)

        self.assertEqual(round(self.flat_jelly_roll._electrode_thickness, 5), 0.00025)
        self.assertEqual(self.flat_jelly_roll.electrode_thickness, 0.25)


class TestCylindricalJellyRoll(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                 specific_cost=11.26, 
                                                 density=4, 
                                                 irreversible_capacity_scaling=1, 
                                                 reversible_capacity_scaling=1)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                   binders={cathode_binder: 5},
                                                   conductive_additives={cathode_conductive_additive: 6})

        cathode_current_collector = NotchedCurrentCollector(formula="Cu", 
                                                          length=3000,
                                                          width=108,
                                                          thickness=5,
                                                          tab_width=5,
                                                          tab_length=30,
                                                          tab_spacing=30,
                                                          bare_length=30)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=18,
                          current_collector=cathode_current_collector,
                          calender_density=2.60)



        # construct anode
        anode_active_material = AnodeMaterial(name="Faradion_HC",
                                              specific_cost=14.27,
                                              density=1.50,
                                              irreversible_capacity_scaling=1,
                                              reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = NotchedCurrentCollector(formula="Cu", 
                                                          length=3000,
                                                          width=108,
                                                          thickness=5,
                                                          tab_width=5,
                                                          tab_length=30,
                                                          tab_spacing=30,
                                                          bare_length=30)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=10,
                      current_collector=anode_current_collector,
                      calender_density=0.85)
        
        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              width=110, 
                              porosity=47, 
                              fold_length=3000)
        
        # construct the stack
        self.cylindrical_jelly_roll = CylindricalJellyRoll(anode=anode, 
                                                           cathode=cathode,
                                                           separator=separator, 
                                                           internal_die_diameter=5.0,
                                                           name="cylindrical_jelly_roll")
        
    def test_instantiation(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.cylindrical_jelly_roll, CylindricalJellyRoll)
        self.assertIsInstance(self.cylindrical_jelly_roll.separator, Separator)

    def test_attributes(self):
        """
        Test cylindrical roll attributes
        """
        self.assertEqual(round(self.cylindrical_jelly_roll._internal_die_diameter, 4), 0.005)
        self.assertEqual(self.cylindrical_jelly_roll.internal_die_diameter, 5)
        self.assertEqual(round(self.cylindrical_jelly_roll._electrode_thickness, 5), 0.00042)
        self.assertEqual(self.cylindrical_jelly_roll.electrode_thickness, 0.42)
        self.assertEqual(self.cylindrical_jelly_roll.n_turns, 42.29)
        self.assertEqual(self.cylindrical_jelly_roll.radius, 20.39)
        self.assertEqual(self.cylindrical_jelly_roll.width, 110.0)

        self.assertEqual(self.cylindrical_jelly_roll.cost_breakdown, {'Cathode': 1.46, 'Anode': 1.03, 'Separator': 0.59})
        self.assertEqual(self.cylindrical_jelly_roll.mass_breakdown, {'Cathode': 130.32, 'Anode': 79.0, 'Separator': 4.22})
        self.assertEqual(self.cylindrical_jelly_roll.mass, 213.55)
        self.assertEqual(self.cylindrical_jelly_roll.pore_volume, 50.31)
        
    def test_get_figure(self):
        """
        Test show
        """
        figure = self.cylindrical_jelly_roll.get_top_down_view()
        # figure.show()
        self.assertTrue(True)  # If no error is raised, the test passes
