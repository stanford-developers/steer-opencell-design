import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Constructions.Cells import StackedPrismaticCell
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Constructions.Containers import PrismaticCase, PrismaticLid, PrismaticShell

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material_1 = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4)
        
        cathode_active_material_2 = CathodeMaterial(name="Faradion_Gen2_4.1V",
                                                    specific_cost=9.1,
                                                    density=4)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material_1: 69, cathode_active_material_2: 20},
                                                   binder={cathode_binder: 5},
                                                   conductive_additive={cathode_conductive_additive: 6})

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=16.0,
                                                     width=10.8,
                                                     bare_tab_area=8.22)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=10.68,
                          current_collector=cathode_current_collector,
                          calender_density=2.60)

        # construct anode
        anode_active_material_1 = AnodeMaterial(name="Faradion_HC",
                                                specific_cost=14.27,
                                                density=1.50)
        
        anode_active_material_2 = AnodeMaterial(name="Faradion_HC_commercial",
                                                specific_cost=9.1,
                                                density=1.50)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material_1: 68, anode_active_material_2: 20},
                                                 binder={anode_binder: 3},
                                                 conductive_additive={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=5,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_tab_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=5.25,
                      current_collector=anode_current_collector,
                      calender_density=0.85)

        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              slit_width=11.0, 
                              porosity=47, 
                              fold_length=18.6)

        # construct the stack
        stack = Stack(anode=anode, 
                      cathode=cathode,
                      separator=separator, 
                      n_stacks=60)

        # make electrolyte
        electrolyte = Electrolyte(specific_cost=8.94, density=1.2)
        
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
        
        prismatic_case = PrismaticCase(lid=prismatic_lid, shell=prismatic_shell)

        self.cell = StackedPrismaticCell(prismatic_case=prismatic_case,
                                         stack=stack,
                                         electrolyte=electrolyte,
                                         electrolyte_overfill=10,
                                         reversible_capacity=35.000,
                                         irreversible_capacity=1.215,
                                         grid_n=1000)
    
    def test_cell(self):

        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
        self.assertEqual(self.cell.cost, 8.37)
        self.assertEqual(round(self.cell._cost, 2), 8.37)
        self.assertEqual(self.cell.mass, 834.0)
        self.assertEqual(round(self.cell._mass, 3), 0.834)
        self.assertEqual(self.cell.height, 2.09)
        self.assertEqual(round(self.cell._height, 4), 0.0209)

        self.assertEqual(self.cell.reversible_capacity, 35.000)
        self.assertEqual(self.cell.irreversible_capacity, 1.22)

        self.assertTrue('Capacity (Ah)' in self.cell.half_cell_curves.columns)
        self.assertTrue('Voltage (V)' in self.cell.half_cell_curves.columns)
        
        self.assertEqual(self.cell.cathode_areal_capacity, 1.35)

        figure = self.cell.get_capacity_voltage_plot()
        # figure.show()
        figure = self.cell.get_cost_breakdown_plot()
        figure.show()
        figure = self.cell.get_mass_breakdown_plot()
        # figure.show()

        self.assertEqual(self.cell.energy, 76.81)
        self.assertEqual(self.cell.energy_density, 151.1)
        self.assertEqual(self.cell.specific_energy, 92.09)
        self.assertEqual(self.cell.normalized_cost, 109.03)

    def test_prismatic_case(self):
        self.assertEqual(self.cell.prismatic_case.cost, 0.48)
        self.assertEqual(self.cell.prismatic_case.mass, 260.79)
        self.assertEqual(self.cell.prismatic_case.internal_width, 12.1)
        self.assertEqual(self.cell.prismatic_case.internal_length, 18.9)
        self.assertEqual(self.cell.prismatic_case.internal_height, 1.93)
        self.assertEqual(self.cell.prismatic_case.internal_volume, 441.37)
        self.assertEqual(self.cell.prismatic_case.external_width, 12.76)
        self.assertEqual(self.cell.prismatic_case.external_length, 19.06)
        self.assertEqual(self.cell.prismatic_case.external_height, 2.09)
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
        self.assertEqual(self.cell.prismatic_case.lid.internal_width, 0.8)
        self.assertEqual(self.cell.prismatic_case.lid.external_width, 1.3)
        self.assertEqual(self.cell.prismatic_case.lid.name, "Prismatic Lid")

        self.assertEqual(round(self.cell.prismatic_case.lid._cost, 2), 0.34)
        self.assertEqual(round(self.cell.prismatic_case.lid._mass, 3), 0.041)
        self.assertEqual(round(self.cell.prismatic_case.lid._internal_width, 4), 0.008)
        self.assertEqual(round(self.cell.prismatic_case.lid._external_width, 4), 0.013)
        
    def test_prismatic_shell(self):
        self.assertEqual(self.cell.prismatic_case.shell.cost, 0.14)
        self.assertEqual(self.cell.prismatic_case.shell.mass, 220.23)
        self.assertEqual(self.cell.prismatic_case.shell.wall_thickness, 0.8)
        self.assertEqual(self.cell.prismatic_case.shell.external_width, 11.46)
        self.assertEqual(self.cell.prismatic_case.shell.external_length, 19.06)
        self.assertEqual(self.cell.prismatic_case.shell.external_height, 2.09)
        self.assertEqual(self.cell.prismatic_case.shell.internal_volume, 412.19)
        self.assertEqual(self.cell.prismatic_case.shell.internal_width, 11.3)
        self.assertEqual(self.cell.prismatic_case.shell.internal_length, 18.9)

        self.assertEqual(round(self.cell.prismatic_case.shell._cost, 2), 0.14)
        self.assertEqual(round(self.cell.prismatic_case.shell._mass, 3), 0.220)
        self.assertEqual(round(self.cell.prismatic_case.shell._wall_thickness, 6), 0.0008)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_width, 4), 0.1146)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_length, 4), 0.1906)
        self.assertEqual(round(self.cell.prismatic_case.shell._external_height, 4), 0.0209)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_volume, 6), 0.000412)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_width, 4), 0.113)
        self.assertEqual(round(self.cell.prismatic_case.shell._internal_length, 4), 0.189)
        
    def test_electrolyte(self):
        self.assertEqual(round(self.cell.electrolyte._density,), 1200)
        self.assertEqual(self.cell.electrolyte.density, 1.2)
        self.assertEqual(self.cell.electrolyte.specific_cost, 8.94)

    def test_stack(self):
        self.assertEqual(self.cell.stack.n_stacks, 60)
        self.assertEqual(self.cell.stack.n_cathode, 60)
        self.assertEqual(self.cell.stack.n_anode, 61)
        self.assertEqual(self.cell.stack.n_separator, 124)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.cathode], 4), 0.2654)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.anode], 4), 0.16)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.separator], 4), 0.0163)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.cathode], 265.45)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.anode], 159.96)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.separator], 16.29)
        self.assertEqual(self.cell.stack.pore_volume, 99.62)
        self.assertEqual(round(self.cell.stack._pore_volume, 6), 0.0001)
        self.assertEqual(self.cell.stack.thickness, 15.69)
   
    def test_separator(self):
        self.assertEqual(self.cell.stack.separator.thickness, 16)
        self.assertEqual(self.cell.stack.separator._thickness, 0.000016)
        self.assertEqual(self.cell.stack.separator.density, 0.4)
        self.assertEqual(round(self.cell.stack.separator._density), 400)
        self.assertEqual(self.cell.stack.separator.porosity, 47)
        self.assertEqual(round(self.cell.stack.separator._porosity, 4), 0.47)
        self.assertEqual(self.cell.stack.separator.slit_width, 11)
        self.assertEqual(self.cell.stack.separator._slit_width, 0.11)
        self.assertEqual(self.cell.stack.separator.fold_length, 18.6)
        self.assertEqual(round(self.cell.stack.separator._fold_length, 3), 0.186)

        self.assertEqual(self.cell.stack.separator.area, 25458.84)
        self.assertEqual(round(self.cell.stack.separator._area, 4), 2.5459)
        self.assertEqual(self.cell.stack.separator.mass, 16.29)
        self.assertEqual(round(self.cell.stack.separator._mass, 4), 0.0163)
        self.assertEqual(self.cell.stack.separator.cost, 2.29)
        self.assertEqual(round(self.cell.stack.separator._cost, 2), 2.29)
        self.assertEqual(self.cell.stack.separator.pore_volume, 19.15)
        self.assertEqual(round(self.cell.stack.separator._pore_volume, 7), 0.0000191)

    def test_electrodes(self):
        #cathode
        self.assertEqual(self.cell.stack.cathode.mass_loading, 10.68)
        self.assertEqual(round(self.cell.stack.cathode._mass_loading, 4), 0.1068)
        self.assertEqual(self.cell.stack.cathode.calender_density, 2.60)
        self.assertEqual(round(self.cell.stack.cathode._calender_density), 2600)
        self.assertEqual(self.cell.stack.cathode.porosity, 26.29)
        self.assertEqual(round(self.cell.stack.cathode._porosity, 4), 0.2629)
        self.assertEqual(self.cell.stack.cathode.coating_mass, 3.69)
        self.assertEqual(round(self.cell.stack.cathode._coating_mass, 4), 0.0037)
        self.assertEqual(self.cell.stack.cathode.mass, 4.42)
        self.assertEqual(round(self.cell.stack.cathode._mass, 4), 0.0044)
        self.assertEqual(self.cell.stack.cathode.material_thickness, 41.08)
        self.assertEqual(self.cell.stack.cathode.double_sided_thickness, 97.15)
        self.assertEqual(round(self.cell.stack.cathode._material_thickness, 6), 0.000041)
        self.assertEqual(round(self.cell.stack.cathode._double_sided_thickness, 6), 0.000097)
        self.assertEqual(self.cell.stack.cathode.pore_volume, 0.37)
        self.assertEqual(round(self.cell.stack.cathode._pore_volume, 8), 0.00000037)

        #anode
        self.assertEqual(self.cell.stack.anode.mass_loading, 5.25)
        self.assertEqual(round(self.cell.stack.anode._mass_loading, 4), 0.0525)
        self.assertEqual(self.cell.stack.anode.calender_density, 0.85)
        self.assertEqual(round(self.cell.stack.anode._calender_density), 850)
        self.assertEqual(self.cell.stack.anode.porosity, 44.61)
        self.assertEqual(round(self.cell.stack.anode._porosity, 4), 0.4461)
        self.assertEqual(self.cell.stack.anode.coating_mass, 1.81)
        self.assertEqual(round(self.cell.stack.anode._coating_mass, 4), 0.0018)
        self.assertEqual(self.cell.stack.anode.mass, 2.62)
        self.assertEqual(round(self.cell.stack.anode._mass, 4), 0.0026)
        self.assertEqual(self.cell.stack.anode.material_thickness, 61.76)
        self.assertEqual(self.cell.stack.anode.double_sided_thickness, 128.53)
        self.assertEqual(round(self.cell.stack.anode._material_thickness, 6), 0.000062)
        self.assertEqual(round(self.cell.stack.anode._double_sided_thickness, 6), 0.000129)
        self.assertEqual(self.cell.stack.anode.pore_volume, 0.95)
        self.assertEqual(round(self.cell.stack.anode._pore_volume, 8), 0.00000095)
        self.assertEqual(self.cell.stack.anode.overhang, 0)
        
    def test_current_collectors(self):
        #cathode
        self.assertEqual(self.cell.stack.cathode.current_collector.specific_cost, 2.64)
        self.assertEqual(self.cell.stack.cathode.current_collector._specific_cost, 2.64)
        self.assertEqual(self.cell.stack.cathode.current_collector.coated_area, 172.8)
        self.assertEqual(round(self.cell.stack.cathode.current_collector._coated_area, 4), 0.0173)
        self.assertEqual(self.cell.stack.cathode.current_collector.bare_tab_area, 8.22)
        self.assertEqual(round(self.cell.stack.cathode.current_collector._bare_tab_area, 6), 0.000822)
        self.assertEqual(self.cell.stack.cathode.current_collector.thickness, 15)
        self.assertEqual(round(self.cell.stack.cathode.current_collector._thickness, 6), 0.000015)
        self.assertEqual(self.cell.stack.cathode.current_collector.density, 2.7)
        self.assertEqual(round(self.cell.stack.cathode.current_collector._density), 2700)
        self.assertEqual(round(self.cell.stack.cathode.current_collector._mass, 6), 0.000733)
        self.assertEqual(self.cell.stack.cathode.current_collector.mass, 0.73)

        #anode
        self.assertEqual(self.cell.stack.anode.current_collector.specific_cost, 10.21)
        self.assertEqual(self.cell.stack.anode.current_collector._specific_cost, 10.21)
        self.assertEqual(self.cell.stack.anode.current_collector.coated_area, 172.8)
        self.assertEqual(round(self.cell.stack.anode.current_collector._coated_area, 4), 0.0173)
        self.assertEqual(self.cell.stack.anode.current_collector.bare_tab_area, 7.55)
        self.assertEqual(round(self.cell.stack.anode.current_collector._bare_tab_area, 6), 0.000755)
        self.assertEqual(self.cell.stack.anode.current_collector.thickness, 5)
        self.assertEqual(round(self.cell.stack.anode.current_collector._thickness, 6), 0.000005)
        self.assertEqual(self.cell.stack.anode.current_collector.density, 8.96)
        self.assertEqual(round(self.cell.stack.anode.current_collector._density), 8960)
        self.assertEqual(round(self.cell.stack.anode.current_collector._mass, 6), 0.000808)
        self.assertEqual(self.cell.stack.anode.current_collector.mass, 0.81)
        
    def test_electrode_materials(self):
        """
        Test the effective areal capacity of the cell
        """
        # test the cathode active materials
        cathode_am = next(iter(self.cell.stack.cathode.formulation.active_materials))
        self.assertEqual(cathode_am.density, 4.00)
        self.assertEqual(round(cathode_am._density), 4000)
        self.assertTrue(type(cathode_am._time_stamp) == dt.datetime)
        self.assertTrue(type(cathode_am.time_stamp == str))
        self.assertEqual(round(cathode_am.half_cell_curve['Specific Capacity (mAh/g)'].iloc[10], 3), 28.103)
        self.assertEqual(round(cathode_am.half_cell_curve['Voltage (V)'].iloc[10], 3), 3.033)

        # test the anode active materials
        anode_am = next(iter(self.cell.stack.anode.formulation.active_materials))
        self.assertEqual(anode_am.density, 1.50)
        self.assertEqual(round(anode_am._density), 1500)

        # test the cathode binder
        cathode_binder = next(iter(self.cell.stack.cathode.formulation.binder))
        self.assertEqual(cathode_binder.density, 1.70)
        self.assertEqual(round(cathode_binder._density), 1700)

        # test the anode binder
        anode_binder = next(iter(self.cell.stack.anode.formulation.binder))
        self.assertEqual(anode_binder.density, 1.70)
        self.assertEqual(round(anode_binder._density), 1700)

        # test the cathode conductive additive
        cathode_ca = next(iter(self.cell.stack.cathode.formulation.conductive_additive))
        self.assertEqual(cathode_ca.density, 1.90)
        self.assertEqual(round(cathode_ca._density), 1900)

        # test the anode conductive additive
        anode_ca = next(iter(self.cell.stack.anode.formulation.conductive_additive))
        self.assertEqual(anode_ca.density, 1.90)
        self.assertEqual(round(anode_ca._density), 1900)

    def test_formulation_properties(self):

        cathode_am = next(iter(self.cell.stack.cathode.formulation.active_materials))
        cathode_binder = next(iter(self.cell.stack.cathode.formulation.binder))
        cathode_ca = next(iter(self.cell.stack.cathode.formulation.conductive_additive))
        anode_am = next(iter(self.cell.stack.anode.formulation.active_materials))
        anode_binder = next(iter(self.cell.stack.anode.formulation.binder))
        anode_ca = next(iter(self.cell.stack.anode.formulation.conductive_additive))

        self.cell.stack.cathode.formulation.active_materials[cathode_am] = 89
        self.cell.stack.cathode.formulation._active_materials[cathode_am] = 0.89
        self.cell.stack.cathode.formulation.binder[cathode_binder] = 5
        self.cell.stack.cathode.formulation._binder[cathode_binder] = 0.05
        self.cell.stack.cathode.formulation.conductive_additive[cathode_ca] = 6
        self.cell.stack.cathode.formulation._conductive_additive[cathode_ca] = 0.06
        self.cell.stack.anode.formulation.active_materials[anode_am] = 88
        self.cell.stack.anode.formulation._active_materials[anode_am] = 0.88
        self.cell.stack.anode.formulation.binder[anode_binder] = 3
        self.cell.stack.anode.formulation._binder[anode_binder] = 0.03
        self.cell.stack.anode.formulation.conductive_additive[anode_ca] = 9
        self.cell.stack.anode.formulation._conductive_additive[anode_ca] = 0.09
