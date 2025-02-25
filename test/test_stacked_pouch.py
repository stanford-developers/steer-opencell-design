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
        cathode_active_material = CathodeMaterial(name="Faradion_Gen2_4.25V", 
                                                 specific_cost=11.26, 
                                                 density=4, 
                                                 irreversible_capacity_scaling=1, 
                                                 reversible_capacity_scaling=1)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
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
        anode_active_material = AnodeMaterial(name="Faradion_HC",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
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
                      name="stack",
                      n_stacks=26)

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
                                     reversible_capacity=11.934,
                                     irreversible_capacity=1.22,
                                     grid_n=2000)
    
    def test_cell(self):

        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
        self.assertEqual(self.cell.cost, 3.73)
        self.assertEqual(round(self.cell._cost, 2), 3.73)
        self.assertEqual(self.cell.mass, 262.63)
        self.assertEqual(round(self.cell._mass, 3), 0.263)
        self.assertEqual(self.cell.thickness, 7.15)
        self.assertEqual(round(self.cell._thickness, 4), 0.0072)

        self.assertEqual(self.cell.reversible_capacity, 11.93)
        self.assertEqual(self.cell.irreversible_capacity, 1.22)

        self.assertTrue('Capacity (Ah)' in self.cell.half_cell_curves.columns)
        self.assertTrue('Voltage (V)' in self.cell.half_cell_curves.columns)

        self.assertEqual(round(self.cell.full_cell_curves
                               .query('Direction == "discharge"')['Capacity (Ah)']
                               .reset_index(drop=True)
                               .iloc[100]), 12.0)
        
        self.assertEqual(round(self.cell.full_cell_curves
                               .query('Direction == "charge"')['Capacity (Ah)']
                               .reset_index(drop=True)
                               .iloc[100]), 1)
        
        self.assertEqual(self.cell.cathode_areal_capacity, 1.40)
        figure = self.cell.get_capacity_voltage_plot()
        # figure.show()
        figure = self.cell.get_cost_breakdown_plot()
        # figure.show()
        figure = self.cell.get_mass_breakdown_plot()
        # figure.show()

        self.assertEqual(self.cell.energy, 35.14)
        self.assertEqual(self.cell.energy_density, 190.53)
        self.assertEqual(self.cell.specific_energy, 133.81)
        self.assertEqual(self.cell.normalized_cost, 106.27)

    def test_terminals(self):
        self.assertEqual(self.cell.positive_terminal.mass, 1)
        self.assertEqual(self.cell.positive_terminal.specific_cost, 16)
        self.assertEqual(self.cell.positive_terminal.cost, 0.016)
        self.assertEqual(round(self.cell.positive_terminal._mass, 6), 0.001)
        self.assertEqual(self.cell.positive_terminal.name, "Positive Terminal")
        
        self.assertEqual(self.cell.negative_terminal.mass, 1)
        self.assertEqual(self.cell.negative_terminal.specific_cost, 16)
        self.assertEqual(self.cell.negative_terminal.cost, 0.016)
        self.assertEqual(round(self.cell.negative_terminal._mass, 6), 0.001)
        self.assertEqual(self.cell.negative_terminal.name, "Negative Terminal")
        
    def test_tape(self):
        self.assertEqual(self.cell.pouch.tape.mass, 0.3)
        self.assertEqual(round(self.cell.pouch.tape._mass, 6), 0.0003)
        
    def test_pouch(self):
        self.assertEqual(self.cell.pouch.heat_seal_size_sides, 7)
        self.assertEqual(self.cell.pouch.heat_seal_size_top, 22)
        self.assertEqual(round(self.cell.pouch._heat_seal_size_sides, 6), 0.007)
        self.assertEqual(round(self.cell.pouch._heat_seal_size_top, 6), 0.022)
        self.assertEqual(self.cell.pouch.length, 20.8)
        self.assertEqual(self.cell.pouch.width, 12.4)
        self.assertEqual(self.cell.pouch.area, 257.96)
        self.assertEqual(round(self.cell.pouch._length, 4), 0.208)
        self.assertEqual(round(self.cell.pouch._width, 4), 0.124)
        self.assertEqual(round(self.cell.pouch._area, 4), 0.0258)
        self.assertEqual(self.cell.pouch.mass, 9.29)
        self.assertEqual(round(self.cell.pouch._mass, 5), 0.00929)
        self.assertEqual(self.cell.pouch.cost, 0.12)
        self.assertEqual(round(self.cell.pouch._cost, 2), 0.12)
        
    def test_laminate(self):
        self.assertEqual(self.cell.pouch.laminate.thickness, 113)
        self.assertEqual(self.cell.pouch.laminate.areal_mass, 18)
        self.assertEqual(self.cell.pouch.laminate.areal_cost, 4.64)
        self.assertEqual(round(self.cell.pouch.laminate._thickness, 6), 0.000113)
        self.assertEqual(round(self.cell.pouch.laminate._areal_mass, 6), 0.18)
        
    def test_electrolyte(self):
        self.assertEqual(round(self.cell.electrolyte._density,), 1200)
        self.assertEqual(self.cell.electrolyte.density, 1.2)
        self.assertEqual(self.cell.electrolyte.specific_cost, 8.94)

    def test_stack(self):
        self.assertEqual(self.cell.stack.n_stacks, 26)
        self.assertEqual(self.cell.stack.n_cathode, 26)
        self.assertEqual(self.cell.stack.n_anode, 27)
        self.assertEqual(self.cell.stack.n_separator, 56)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.cathode], 4), 0.115)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.anode], 4), 0.0708)
        self.assertEqual(round(self.cell.stack._mass_breakdown[self.cell.stack.separator], 4), 0.0074)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.cathode], 115.03)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.anode], 70.8)
        self.assertEqual(self.cell.stack.mass_breakdown[self.cell.stack.separator], 7.36)
        self.assertEqual(self.cell.stack.pore_volume, 44.06)
        self.assertEqual(round(self.cell.stack._pore_volume, 6), 0.000044)
        self.assertEqual(self.cell.stack.thickness, 6.92)
   
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

        self.assertEqual(self.cell.stack.separator.area, 11496.49)
        self.assertEqual(round(self.cell.stack.separator._area, 4), 1.1496)
        self.assertEqual(self.cell.stack.separator.mass, 7.36)
        self.assertEqual(round(self.cell.stack.separator._mass, 4), 0.0074)
        self.assertEqual(self.cell.stack.separator.cost, 1.03)
        self.assertEqual(round(self.cell.stack.separator._cost, 2), 1.03)
        self.assertEqual(self.cell.stack.separator.pore_volume, 8.65)
        self.assertEqual(round(self.cell.stack.separator._pore_volume, 7), 0.0000086)

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

