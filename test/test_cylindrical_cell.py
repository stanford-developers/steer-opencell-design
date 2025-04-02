import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import FlatJellyRoll, CylindricalJellyRoll
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
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

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=55.0,
                                                     width=10.8,
                                                     bare_area=8.22)

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
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=5,
                                                   length=55.5,
                                                   width=11.0,
                                                   bare_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      calender_density=0.85)

        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              width=11.0, 
                              porosity=47, 
                              fold_length=56)

        # construct the stack
        self.flat_jelly_roll = FlatJellyRoll(anode=anode, 
                                             cathode=cathode,
                                             separator=separator, 
                                             focal_length=10.0,
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
        self.assertEqual(round(self.flat_jelly_roll._separator._fold_length, 2) , 0.56)
        self.assertEqual(self.flat_jelly_roll._separator.fold_length, 56)

        self.assertEqual(round(self.flat_jelly_roll._focal_length, 2), 0.1)
        self.assertEqual(round(self.flat_jelly_roll.focal_length, 2), 10)

        self.assertEqual(round(self.flat_jelly_roll._thickness, 4), 0.0015)
        self.assertEqual(self.flat_jelly_roll.thickness, 0.15)

        self.assertEqual(round(self.flat_jelly_roll._electrode_thickness, 5), 0.00026)
        self.assertEqual(self.flat_jelly_roll.electrode_thickness, 0.26)


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

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=55.0,
                                                     width=10.8,
                                                     bare_area=8.22)

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
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=5,
                                                   length=55.5,
                                                   width=11.0,
                                                   bare_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      calender_density=0.85)
        
        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              width=11.0, 
                              porosity=47, 
                              fold_length=56)
        
        # construct the stack
        self.cylindrical_jelly_roll = CylindricalJellyRoll(anode=anode, 
                                                           cathode=cathode,
                                                           separator=separator, 
                                                           internal_die_diameter=6.0,
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
        self.assertEqual(round(self.cylindrical_jelly_roll._internal_die_diameter, 4), 0.006)
        self.assertEqual(self.cylindrical_jelly_roll.internal_die_diameter, 6)
        self.assertEqual(round(self.cylindrical_jelly_roll._electrode_thickness, 5), 0.00026)
        self.assertEqual(self.cylindrical_jelly_roll.electrode_thickness, 0.26)
        self.assertEqual(round(self.cylindrical_jelly_roll._cart_spiral['x'].iloc[10], 4), 0.0031)
        self.assertEqual(round(self.cylindrical_jelly_roll._cart_spiral['y'].iloc[10], 6), 0.000034)
        self.assertEqual(round(self.cylindrical_jelly_roll.cart_spiral['X (cm)'].iloc[10], 2), 0.31)
        self.assertEqual(round(self.cylindrical_jelly_roll.cart_spiral['Y (cm)'].iloc[10], 4), 0.0034)
        self.assertEqual(round(self.cylindrical_jelly_roll._polar_spiral['theta'].iloc[10], 4), 0.011)
        self.assertEqual(round(self.cylindrical_jelly_roll._polar_spiral['r'].iloc[10], 4), 0.0031)
        self.assertEqual(self.cylindrical_jelly_roll.n_turns, 16.83)
        self.assertEqual(self.cylindrical_jelly_roll.radius, 0.76)
        self.assertEqual(self.cylindrical_jelly_roll.width, 11)

        self.assertEqual(self.cylindrical_jelly_roll.cost_breakdown, {'Cathode': 0.15, 'Anode': 0.12, 'Separator': 0.11})
        self.assertEqual(self.cylindrical_jelly_roll.mass_breakdown, {'Cathode': 15.13, 'Anode': 9.18, 'Separator': 0.79})
        self.assertEqual(self.cylindrical_jelly_roll.mass, 25.09)
        self.assertEqual(self.cylindrical_jelly_roll.pore_volume, 5.57)
        
    def test_show(self):
        """
        Test show
        """
        # self.cylindrical_jelly_roll.show()
        self.assertTrue(True)  # If no error is raised, the test passes
