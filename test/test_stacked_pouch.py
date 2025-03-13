import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Constructions.Cells import StackedPouchCell
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Constructions.Containers import Pouch
from SteerEnergyStorage.Materials.other import Laminate, Tape, Terminal

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material = CathodeMaterial(name="Faradion_Gen2_4.25V", specific_cost=11.26, density=4)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                   binders={cathode_binder: 5},
                                                   conductive_additives={cathode_conductive_additive: 6})

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
        anode_active_material = AnodeMaterial(name="Faradion_HC", specific_cost=14.27, density=1.50)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
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
                           name="stack",
                           n_layers=26)

        # make electrolyte
        electrolyte = Electrolyte(specific_cost=8.94, density=1.2)
        
        # make the pouch
        laminate = Laminate(thickness=113, areal_mass=18, areal_cost=4.64)
        tape = Tape(mass=0.3)
        
        pouch = Pouch(laminate=laminate, 
                      heat_seal_size_sides=7, 
                      heat_seal_size_top=22, 
                      tape=tape)

        # Make the cell
        pos_terminal = Terminal(mass = 1, specific_cost = 16, name="Positive Terminal")
        neg_terminal = Terminal(mass = 1, specific_cost = 16, name="Negative Terminal")

        self.cell = StackedPouchCell(pouch=pouch,
                                     stack=stack,
                                     electrolyte=electrolyte,
                                     electrolyte_overfill=10,
                                     positive_terminal=pos_terminal,
                                     negative_terminal=neg_terminal,
                                     reversible_capacity=6.934,
                                     irreversible_capacity=2.22,
                                     n_stacks=1)
        
    def test_cell(self):

        self.assertTrue(isinstance(self.cell, StackedPouchCell))

    def test_plots(self):

        fig = self.cell.get_capacity_voltage_plot()
        # fig.show()

        fig = self.cell.get_cost_breakdown_plot(mode='pie')
        fig.show()

        fig = self.cell.get_mass_breakdown_plot(mode='pie')
        fig.show()

    
    # def test_cell(self):

    #     self.assertEqual(self.cell.electrolyte_overfill, 10)
    #     self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
    #     self.assertEqual(self.cell.cost, 3.73)
    #     self.assertEqual(round(self.cell._cost, 2), 3.73)
    #     self.assertEqual(self.cell.mass, 262.63)
    #     self.assertEqual(round(self.cell._mass, 3), 0.263)
    #     self.assertEqual(self.cell.thickness, 7.15)
    #     self.assertEqual(round(self.cell._thickness, 4), 0.0072)

    #     self.assertEqual(self.cell.reversible_capacity, 11.93)
    #     self.assertEqual(self.cell.irreversible_capacity, 1.22)

    #     self.assertTrue('Capacity (Ah)' in self.cell.half_cell_curves.columns)
    #     self.assertTrue('Voltage (V)' in self.cell.half_cell_curves.columns)
        
    #     # self.assertEqual(self.cell.cathode_areal_capacity, 1.40)
    #     figure = self.cell.get_capacity_voltage_plot()
    #     figure.show()
    #     figure = self.cell.get_cost_breakdown_plot(mode='pie')
    #     figure.show()
    #     figure = self.cell.get_mass_breakdown_plot(mode='pie')
    #     figure.show()

    #     self.assertEqual(self.cell.energy, 35.14)
    #     self.assertEqual(self.cell.energy_density, 190.53)
    #     self.assertEqual(self.cell.specific_energy, 133.81)
    #     self.assertEqual(self.cell.normalized_cost, 106.27)

    # def test_terminals(self):
    #     self.assertEqual(self.cell.positive_terminal.mass, 1)
    #     self.assertEqual(self.cell.positive_terminal.specific_cost, 16)
    #     self.assertEqual(self.cell.positive_terminal.cost, 0.016)
    #     self.assertEqual(round(self.cell.positive_terminal._mass, 6), 0.001)
    #     self.assertEqual(self.cell.positive_terminal.name, "Positive Terminal")
        
    #     self.assertEqual(self.cell.negative_terminal.mass, 1)
    #     self.assertEqual(self.cell.negative_terminal.specific_cost, 16)
    #     self.assertEqual(self.cell.negative_terminal.cost, 0.016)
    #     self.assertEqual(round(self.cell.negative_terminal._mass, 6), 0.001)
    #     self.assertEqual(self.cell.negative_terminal.name, "Negative Terminal")
        
    # def test_tape(self):
    #     self.assertEqual(self.cell.pouch.tape.mass, 0.3)
    #     self.assertEqual(round(self.cell.pouch.tape._mass, 6), 0.0003)
        
    # def test_pouch(self):
    #     self.assertEqual(self.cell.pouch.heat_seal_size_sides, 7)
    #     self.assertEqual(self.cell.pouch.heat_seal_size_top, 22)
    #     self.assertEqual(round(self.cell.pouch._heat_seal_size_sides, 6), 0.007)
    #     self.assertEqual(round(self.cell.pouch._heat_seal_size_top, 6), 0.022)
    #     self.assertEqual(self.cell.pouch.length, 20.8)
    #     self.assertEqual(self.cell.pouch.width, 12.4)
    #     self.assertEqual(self.cell.pouch.area, 257.96)
    #     self.assertEqual(round(self.cell.pouch._length, 4), 0.208)
    #     self.assertEqual(round(self.cell.pouch._width, 4), 0.124)
    #     self.assertEqual(round(self.cell.pouch._area, 4), 0.0258)
    #     self.assertEqual(self.cell.pouch.mass, 9.29)
    #     self.assertEqual(round(self.cell.pouch._mass, 5), 0.00929)
    #     self.assertEqual(self.cell.pouch.cost, 0.12)
    #     self.assertEqual(round(self.cell.pouch._cost, 2), 0.12)
        
    # def test_laminate(self):
    #     self.assertEqual(self.cell.pouch.laminate.thickness, 113)
    #     self.assertEqual(self.cell.pouch.laminate.areal_mass, 18)
    #     self.assertEqual(self.cell.pouch.laminate.areal_cost, 4.64)
    #     self.assertEqual(round(self.cell.pouch.laminate._thickness, 6), 0.000113)
    #     self.assertEqual(round(self.cell.pouch.laminate._areal_mass, 6), 0.18)
        
    # def test_electrolyte(self):
    #     self.assertEqual(round(self.cell.electrolyte._density,), 1200)
    #     self.assertEqual(self.cell.electrolyte.density, 1.2)
    #     self.assertEqual(self.cell.electrolyte.specific_cost, 8.94)

    # def test_stack(self):
    #     for s in self.cell.stacks:
    #         self.assertEqual(round(s._mass_breakdown['cathode'], 4), 0.115)
    #         self.assertEqual(round(s._mass_breakdown['anode'], 4), 0.0708)
    #         self.assertEqual(round(s._mass_breakdown['separator'], 4), 0.0074)
    #         self.assertEqual(s.mass_breakdown['Cathode'], 115.03)
    #         self.assertEqual(s.mass_breakdown['Anode'], 70.8)
    #         self.assertEqual(s.mass_breakdown['Separator'], 7.36)
    #         self.assertEqual(s.pore_volume, 44.06)
    #         self.assertEqual(round(s._pore_volume, 6), 0.000044)
    #         self.assertEqual(s.thickness, 6.92)
   
    # def test_separator(self):
    #     for s in self.cell.stacks:
    #         self.assertEqual(s.separator.thickness, 16)
    #         self.assertEqual(s.separator._thickness, 0.000016)
    #         self.assertEqual(s.separator.density, 0.4)
    #         self.assertEqual(round(s.separator._density), 400)
    #         self.assertEqual(s.separator.porosity, 47)
    #         self.assertEqual(round(s.separator._porosity, 4), 0.47)
    #         self.assertEqual(s.separator.slit_width, 11)
    #         self.assertEqual(s.separator._slit_width, 0.11)
    #         self.assertEqual(s.separator.fold_length, 18.6)
    #         self.assertEqual(round(s.separator._fold_length, 3), 0.186)

    #         self.assertEqual(s.separator.area, 11496.49)
    #         self.assertEqual(round(s.separator._area, 4), 1.1496)
    #         self.assertEqual(s.separator.mass, 7.36)
    #         self.assertEqual(round(s.separator._mass, 4), 0.0074)
    #         self.assertEqual(s.separator.cost, 1.03)
    #         self.assertEqual(round(s.separator._cost, 2), 1.03)
    #         self.assertEqual(s.separator.pore_volume, 8.65)
    #         self.assertEqual(round(s.separator._pore_volume, 7), 0.0000086)

    # def test_electrodes(self):
    #     #cathode
    #     for c in self.stack.cathodes:
    #         self.assertEqual(c.mass_loading, 10.68)
    #         self.assertEqual(round(c._mass_loading, 4), 0.1068)
    #         self.assertEqual(c.calender_density, 2.60)
    #         self.assertEqual(round(c._calender_density), 2600)
    #         self.assertEqual(c.porosity, 26.29)
    #         self.assertEqual(round(c._porosity, 4), 0.2629)
    #         self.assertEqual(c.coating_mass, 3.69)
    #         self.assertEqual(round(c._coating_mass, 4), 0.0037)
    #         self.assertEqual(c.mass, 4.42)
    #         self.assertEqual(round(c._mass, 4), 0.0044)
    #         self.assertEqual(c.material_thickness, 41.08)
    #         self.assertEqual(c.double_sided_thickness, 97.15)
    #         self.assertEqual(round(c._material_thickness, 6), 0.000041)
    #         self.assertEqual(round(c._double_sided_thickness, 6), 0.000097)
    #         self.assertEqual(c.pore_volume, 0.37)
    #         self.assertEqual(round(c._pore_volume, 8), 0.00000037)

    #     #anode
    #     for a in self.stack.anodes:
    #         self.assertEqual(a.mass_loading, 5.25)
    #         self.assertEqual(round(a._mass_loading, 4), 0.0525)
    #         self.assertEqual(a.calender_density, 0.85)
    #         self.assertEqual(round(a._calender_density), 850)
    #         self.assertEqual(a.porosity, 44.61)
    #         self.assertEqual(round(a._porosity, 4), 0.4461)
    #         self.assertEqual(a.coating_mass, 1.81)
    #         self.assertEqual(round(a._coating_mass, 4), 0.0018)
    #         self.assertEqual(a.mass, 2.62)
    #         self.assertEqual(round(a._mass, 4), 0.0026)
    #         self.assertEqual(a.material_thickness, 61.76)
    #         self.assertEqual(a.double_sided_thickness, 128.53)
    #         self.assertEqual(round(a._material_thickness, 6), 0.000062)
    #         self.assertEqual(round(a._double_sided_thickness, 6), 0.000129)
    #         self.assertEqual(a.pore_volume, 0.95)
    #         self.assertEqual(round(a._pore_volume, 8), 0.00000095)
    #         self.assertEqual(a.overhang, 0)
        
    # def test_current_collectors(self):

    #     for s in self.cell.stacks:
    #         for c in s.cathodes:
    #             self.assertEqual(c.current_collector.specific_cost, 2.64)
    #             self.assertEqual(c.current_collector._specific_cost, 2.64)
    #             self.assertEqual(c.current_collector.coated_area, 172.8)
    #             self.assertEqual(round(c.current_collector._coated_area, 4), 0.0173)
    #             self.assertEqual(c.current_collector.bare_tab_area, 8.22)
    #             self.assertEqual(round(c.current_collector._bare_tab_area, 6), 0.000822)
    #             self.assertEqual(c.current_collector.thickness, 15)
    #             self.assertEqual(round(c.current_collector._thickness, 6), 0.000015)
    #             self.assertEqual(c.current_collector.density, 2.7)
    #             self.assertEqual(round(c.current_collector._density), 2700)
    #             self.assertEqual(round(c.current_collector._mass, 6), 0.000733)
    #             self.assertEqual(c.current_collector.mass, 0.73)

    #         for a in s.anodes:
    #             self.assertEqual(a.current_collector.specific_cost, 10.21)
    #             self.assertEqual(a.current_collector._specific_cost, 10.21)
    #             self.assertEqual(a.current_collector.coated_area, 172.8)
    #             self.assertEqual(round(a.current_collector._coated_area, 4), 0.0173)
    #             self.assertEqual(a.current_collector.bare_tab_area, 7.55)
    #             self.assertEqual(round(a.current_collector._bare_tab_area, 6), 0.000755)
    #             self.assertEqual(a.current_collector.thickness, 5)
    #             self.assertEqual(round(a.current_collector._thickness, 6), 0.000005)
    #             self.assertEqual(a.current_collector.density, 8.96)
    #             self.assertEqual(round(a.current_collector._density), 8960)
    #             self.assertEqual(round(a.current_collector._mass, 6), 0.000808)
    #             self.assertEqual(a.current_collector.mass, 0.81)
        
    # def test_electrode_materials(self):
    #     """
    #     Test the effective areal capacity of the cell
    #     """
    #     # test the cathode active materials
    #     self.assertEqual(self.cathode_active_material.density, 4.00)
    #     self.assertEqual(round(self.cathode_active_material._density), 4000)
    #     self.assertTrue(type(self.cathode_active_material._time_stamp) == dt.datetime)
    #     self.assertTrue(type(self.cathode_active_material.time_stamp == str))
    #     self.assertEqual(round(self.cathode_active_material.half_cell_curve['Specific Capacity (mAh/g)'].iloc[10], 3), 28.103)
    #     self.assertEqual(round(self.cathode_active_material.half_cell_curve['Voltage (V)'].iloc[10], 3), 3.033)

    #     # test the anode active materials
    #     self.assertEqual(self.anode_active_material.density, 1.50)
    #     self.assertEqual(round(self.anode_active_material._density), 1500)

    #     # test the cathode binder
    #     self.assertEqual(self.cathode_binder.density, 1.70)
    #     self.assertEqual(round(self.cathode_binder._density), 1700)

    #     # test the anode binder
    #     self.assertEqual(self.anode_binder.density, 1.70)
    #     self.assertEqual(round(self.anode_binder._density), 1700)

    #     # test the cathode conductive additive
    #     self.assertEqual(self.cathode_conductive_additive.density, 1.90)
    #     self.assertEqual(round(self.cathode_conductive_additive._density), 1900)

    #     # test the anode conductive additive
    #     self.assertEqual(self.anode_conductive_additive.density, 1.90)
    #     self.assertEqual(round(self.anode_conductive_additive._density), 1900)

    # def test_formulation_properties(self):

    #     for s in self.cell.stacks:
    #         for c in s.cathodes:
    #             self.assertEqual(c.formulation.active_materials[self.cathode_active_material], 89)
    #             self.assertEqual(c.formulation._active_materials[self.cathode_active_material], 0.89)
    #             self.assertEqual(c.formulation.binder[self.cathode_binder], 5)
    #             self.assertEqual(c.formulation._binder[self.cathode_binder], 0.05)
    #             self.assertEqual(c.formulation.conductive_additive[self.cathode_conductive_additive], 6)
    #             self.assertEqual(c.formulation._conductive_additive[self.cathode_conductive_additive], 0.06)
    #         for a in s.anodes:
    #             self.assertEqual(a.formulation.active_materials[self.anode_active_material], 88)
    #             self.assertEqual(a.formulation._active_materials[self.anode_active_material], 0.88)
    #             self.assertEqual(a.formulation.binder[self.anode_binder], 3)
    #             self.assertEqual(a.formulation._binder[self.anode_binder], 0.03)
    #             self.assertEqual(a.formulation.conductive_additive[self.anode_conductive_additive], 9)
    #             self.assertEqual(a.formulation._conductive_additive[self.anode_conductive_additive], 0.09)
