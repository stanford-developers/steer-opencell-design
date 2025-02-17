import unittest
import plotly.express as px
from SteerEnergyStorage.Constructions.Containers import PrismaticCase, PrismaticLid, PrismaticShell
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):

        # construct cathode
        cathode_active_material = ActiveMaterial(name="Faradion_Gen2_4.25V", 
                                                 formula="Li2MnSiO4", 
                                                 specific_cost=11.26, 
                                                 density=4, 
                                                 irreversible_capacity_scaling=1, 
                                                 reversible_capacity_scaling=1,
                                                 half_cell_path='./Data/Cathode_Faradion_Gen2_4.25V.csv')
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                   binder={cathode_binder: 5},
                                                   conductive_additive={cathode_conductive_additive: 6})

        cathode_current_collector = CurrentCollector(name="Aluminium", 
                                                     formula="Al", 
                                                     specific_cost=6.30, 
                                                     density=2.7, 
                                                     thickness=15, 
                                                     length=16.0,
                                                     width=10.8,
                                                     bare_tab_area=8.22)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector,
                          swell_factor=1.0,
                          calender_density=2.60)

        # construct anode
        anode_active_material = ActiveMaterial(name="Faradion_HC",
                                               formula="Na2Ti3O7",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1,
                                               half_cell_path='./Data/Anode_Faradion_HC.csv')
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binder={anode_binder: 3},
                                                 conductive_additive={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(name="Copper",
                                                   formula="Cu",
                                                   specific_cost=6.30,
                                                   density=2.70,
                                                   thickness=15,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_tab_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      swell_factor=1.0,
                      calender_density=0.85)

        # construct seperator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              slit_width=11.0, 
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

        self.stack = self.prismatic_case.get_optimized_stack(cathode=cathode, anode=anode, separator=separator)

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

        self.assertEqual(self.stack.n_stacks, 71)
        self.assertEqual(self.stack.n_cathode, 71)
        self.assertEqual(self.stack.n_anode, 72)
        self.assertEqual(self.stack.n_separator, 146)
        self.assertEqual(round(self.stack._mass_breakdown[self.stack.cathode], 4), 0.3141)
        self.assertEqual(round(self.stack._mass_breakdown[self.stack.anode], 4), 0.1832)
        self.assertEqual(round(self.stack._mass_breakdown[self.stack.separator], 4), 0.0192)
        self.assertEqual(self.stack.mass_breakdown[self.stack.cathode], 314.11)
        self.assertEqual(self.stack.mass_breakdown[self.stack.anode], 183.23)
        self.assertEqual(self.stack.mass_breakdown[self.stack.separator], 19.19)
        self.assertEqual(self.stack.pore_volume, 117.6)
        self.assertEqual(round(self.stack._pore_volume, 6), 0.000118)
        self.assertEqual(self.stack.thickness, 19.24)

