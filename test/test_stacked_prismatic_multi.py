import unittest
import plotly.express as px

from OpenCell.Formulations.ElectrodeFormulations import ElectrodeFormulation
from OpenCell.Constructions.Electrodes import Cathode, Anode
from OpenCell.Formulations.ElectrodeAssemblies import Stack
from OpenCell.Constructions.Cells import StackedPrismaticCell
from OpenCell.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

from OpenCell.Materials.Separators import Separator
from OpenCell.Materials.Electrolytes import Electrolyte
from OpenCell.Constructions.Containers import PrismaticCase, PrismaticLid, PrismaticShell

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material_1 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4)
        
        cathode_active_material_2 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.1V",
                                                    specific_cost=9.1,
                                                    density=4)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material_1: 69, cathode_active_material_2: 20},
                                                   binders={cathode_binder: 5},
                                                   conductive_additives={cathode_conductive_additive: 6})

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=160,
                                                     width=108,
                                                     bare_area=822)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector,
                          calender_density=2.60)

        # construct anode
        anode_active_material_1 = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                                specific_cost=14.27,
                                                density=1.50)
        
        anode_active_material_2 = AnodeMaterial(name="Hard Carbon (Vendor B - 300 mAh/g)",
                                                specific_cost=9.1,
                                                density=1.50)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material_1: 68, anode_active_material_2: 20},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=5,
                                                   length=160,
                                                   width=108,
                                                   bare_area=755)
        
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
                              fold_length=186)

        # make electrolyte
        electrolyte = Electrolyte(specific_cost=8.94, density=1.2)
        
        # make the case
        prismatic_shell = PrismaticShell(cost=0.14,
                                         mass=220.23,
                                         internal_width=113,
                                         internal_length=189,
                                         internal_height=19.3,
                                         wall_thickness=0.8)
        
        prismatic_lid = PrismaticLid(cost=0.34,
                                     mass=40.56,
                                     external_width=13, 
                                     internal_width=8)
        
        prismatic_case = PrismaticCase(lid=prismatic_lid, shell=prismatic_shell)

        stack = prismatic_case.get_optimized_stack(anode=anode, cathode=cathode, separator=separator)

        self.cell = StackedPrismaticCell(stack=stack,
                                         prismatic_case=prismatic_case,
                                         electrolyte=electrolyte,
                                         electrolyte_overfill=10,
                                         reversible_capacity=35.000,
                                         irreversible_capacity=1.22,
                                         n_stacks=1)
    
    def test_cell(self):

        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
        self.assertEqual(self.cell.cost, 10.19)
        self.assertEqual(round(self.cell._cost, 2), 10.19)
        self.assertEqual(self.cell.mass, 966.53)
        self.assertEqual(round(self.cell._mass, 3), 0.967)
        self.assertEqual(self.cell.height, 20.9)
        self.assertEqual(round(self.cell._height, 4), 0.0209)

        self.assertEqual(self.cell.reversible_capacity, 35.000)
        self.assertEqual(self.cell.irreversible_capacity, 1.22)

        self.assertTrue('Capacity (Ah)' in self.cell.full_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.full_cell_curve.columns)
        
        #TODO
        # self.assertEqual(self.cell.effective_areal_capacity, 1.35)

        self.assertEqual(self.cell.energy, 95.01)
        self.assertEqual(self.cell.energy_density, 186.92)
        self.assertEqual(self.cell.specific_energy, 98.3)
        self.assertEqual(self.cell.normalized_cost, 107.22)

    def test_plots(self):
        figure1 = self.cell.get_capacity_voltage_plot()
        figure2 = self.cell.get_cost_breakdown_plot()
        figure3 = self.cell.get_mass_breakdown_plot()
        # figure1.show()
        # figure2.show()
        # figure3.show()

    def test_prismatic_case(self):
        self.assertEqual(self.cell.prismatic_case.cost, 0.48)
        self.assertEqual(self.cell.prismatic_case.mass, 260.79)
        self.assertEqual(self.cell.prismatic_case.internal_width, 121.0)
        self.assertEqual(self.cell.prismatic_case.internal_length, 189.0)
        self.assertEqual(self.cell.prismatic_case.internal_height, 19.3)
        self.assertEqual(self.cell.prismatic_case.internal_volume, 441.37)
        self.assertEqual(self.cell.prismatic_case.external_width, 127.6)
        self.assertEqual(self.cell.prismatic_case.external_length, 190.6)
        self.assertEqual(self.cell.prismatic_case.external_height, 20.9)
        self.assertEqual(self.cell.prismatic_case.external_volume, 508.3)
        self.assertEqual(self.cell.prismatic_case.name, "Prismatic Case")

        self.assertEqual(round(self.cell.prismatic_case._cost, 2), 0.48)
        self.assertEqual(round(self.cell.prismatic_case._mass, 3), 0.261)
        self.assertEqual(round(self.cell.prismatic_case._internal_width, 4), 0.121)
        self.assertEqual(round(self.cell.prismatic_case._internal_length, 4), 0.189)
        self.assertEqual(round(self.cell.prismatic_case._internal_height, 4), 0.0193)
        self.assertEqual(round(self.cell.prismatic_case._internal_volume, 6), 0.000441)
        self.assertEqual(round(self.cell.prismatic_case._external_width, 4), 0.1276)
        self.assertEqual(round(self.cell.prismatic_case._external_length, 4), 0.1906)
        self.assertEqual(round(self.cell.prismatic_case._external_height, 4), 0.0209)
        self.assertEqual(round(self.cell.prismatic_case._external_volume, 6), 0.000508)

    def test_prismatic_lid(self):
        self.assertEqual(self.cell.prismatic_case.lid.cost, 0.34)
        self.assertEqual(self.cell.prismatic_case.lid.mass, 40.56)
        self.assertEqual(self.cell.prismatic_case.lid.internal_width, 8.0)
        self.assertEqual(self.cell.prismatic_case.lid.external_width, 13.0)
        self.assertEqual(self.cell.prismatic_case.lid.name, "Prismatic Lid")

        self.assertEqual(round(self.cell.prismatic_case.lid._cost, 2), 0.34)
        self.assertEqual(round(self.cell.prismatic_case.lid._mass, 3), 0.041)
        self.assertEqual(round(self.cell.prismatic_case.lid._internal_width, 4), 0.008)
        self.assertEqual(round(self.cell.prismatic_case.lid._external_width, 4), 0.013)
        
    def test_prismatic_shell(self):
        self.assertEqual(self.cell.prismatic_case.shell.cost, 0.14)
        self.assertEqual(self.cell.prismatic_case.shell.mass, 220.23)
        self.assertEqual(self.cell.prismatic_case.shell.wall_thickness, 0.8)
        self.assertEqual(self.cell.prismatic_case.shell.external_width, 114.6)
        self.assertEqual(self.cell.prismatic_case.shell.external_length, 190.6)
        self.assertEqual(self.cell.prismatic_case.shell.external_height, 20.9)
        self.assertEqual(self.cell.prismatic_case.shell.internal_volume, 412.19)
        self.assertEqual(self.cell.prismatic_case.shell.internal_width, 113.0)
        self.assertEqual(self.cell.prismatic_case.shell.internal_length, 189.0)

        self.assertEqual(round(self.cell.prismatic_case.shell._cost, 2), 0.14)
        self.assertEqual(round(self.cell.prismatic_case.shell._mass, 3), 0.220)
        self.assertEqual(round(self.cell.prismatic_case.shell._wall_thickness, 6), 0.0008)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_width, 4), 0.1146)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_length, 4), 0.1906)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_height, 4), 0.0209)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_volume, 6), 0.000412)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_width, 4), 0.113)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_length, 4), 0.189)
        