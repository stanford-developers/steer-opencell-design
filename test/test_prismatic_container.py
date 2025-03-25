import unittest
import plotly.express as px
from SteerEnergyStorage.Constructions.Containers import PrismaticCase, PrismaticLid, PrismaticShell
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import Stack
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):

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
                                                     length=16.0,
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
                                                   thickness=15,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      calender_density=0.85)

        # construct seperator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              width=11.0, 
                              porosity=47, 
                              fold_length=18.6)

        # make the case
        prismatic_shell = PrismaticShell(cost=0.14,
                                         mass=220.23,
                                         internal_width=11.3,
                                         internal_length=18.9,
                                         internal_height=1.93,
                                         wall_thickness=0.8)
        
        prismatic_lid = PrismaticLid(cost=0.34,
                                     mass=40.56,
                                     external_width=1.3, 
                                     internal_width=0.8)
        
        self.prismatic_case = PrismaticCase(lid=prismatic_lid, shell=prismatic_shell)

        self.stack_1 = self.prismatic_case.get_optimized_stack(cathode=cathode, anode=anode, separator=separator)
        self.stack_2 = self.prismatic_case.get_optimized_stack(cathode=cathode, anode=anode, separator=separator, n_stacks=2)

    def test_case(self):
        self.assertEqual(self.prismatic_case.cost, 0.48)
        self.assertEqual(self.prismatic_case.mass, 260.79)
        self.assertEqual(self.prismatic_case.internal_width, 12.1)
        self.assertEqual(self.prismatic_case.internal_length, 18.9)
        self.assertEqual(self.prismatic_case.internal_height, 1.93)
        self.assertEqual(self.prismatic_case.internal_volume, 441.37)
        self.assertEqual(self.prismatic_case.external_width, 12.76)
        self.assertEqual(self.prismatic_case.external_length, 19.06)
        self.assertEqual(self.prismatic_case.external_height, 2.09)
        self.assertEqual(self.prismatic_case.external_volume, 508.3)
        self.assertEqual(self.prismatic_case.name, "Prismatic Case")
        self.assertEqual(round(self.prismatic_case._cost, 2), 0.48)
        self.assertEqual(round(self.prismatic_case._mass, 3), 0.261)
        self.assertEqual(round(self.prismatic_case._internal_width, 4), 0.121)
        self.assertEqual(round(self.prismatic_case._internal_length, 4), 0.189)
        self.assertEqual(round(self.prismatic_case._internal_height, 4), 0.0193)
        self.assertEqual(round(self.prismatic_case._internal_volume, 6), 0.000441)
        self.assertEqual(round(self.prismatic_case._external_width, 4), 0.1276)
        self.assertEqual(round(self.prismatic_case._external_length, 4), 0.1906)
        self.assertEqual(round(self.prismatic_case._external_height, 4), 0.0209)
        self.assertEqual(round(self.prismatic_case._external_volume, 6), 0.000508)
        
    def test_stack_1(self):
        self.assertEqual(self.stack_1._n_layers, 71)
        self.assertEqual(len(self.stack_1._cathodes), 71)
        self.assertEqual(len(self.stack_1._anodes), 72)

    def test_stack_2(self):
        self.assertEqual(self.stack_2._n_layers, 35)
        self.assertEqual(len(self.stack_2._cathodes), 35)
        self.assertEqual(len(self.stack_2._anodes), 36)
