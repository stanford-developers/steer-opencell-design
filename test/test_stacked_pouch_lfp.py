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
        cathode_active_material = CathodeMaterial(name="lfp", specific_cost=14, density=3.6)
        
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
                          mass_loading=9,
                          current_collector=cathode_current_collector,
                          calender_density=2.3)

        # construct anode
        anode_active_material = AnodeMaterial(name="synthetic_graphite", specific_cost=11, density=2.26)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=6,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_tab_area=7.55)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=7,
                      current_collector=anode_current_collector,
                      calender_density=1.6)

        # construct separator
        separator = Separator(thickness=19, 
                              areal_cost=1, 
                              density=0.9, 
                              slit_width=11.0, 
                              porosity=42, 
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
                                     reversible_capacity=11.934,
                                     irreversible_capacity=1.22,
                                     n_stacks=1)
        
    def test_cell(self):

        self.assertTrue(isinstance(self.cell, StackedPouchCell))
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

        self.assertTrue('Capacity (Ah)' in self.cell.full_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.full_cell_curve.columns)
        self.assertTrue('Capacity (Ah)' in self.cell.cathode_half_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.cathode_half_cell_curve.columns)
        self.assertTrue('Capacity (Ah)' in self.cell.anode_half_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.anode_half_cell_curve.columns)

        self.assertEqual(self.cell.energy, 35.17)
        self.assertEqual(self.cell.energy_density, 190.7)
        self.assertEqual(self.cell.specific_energy, 133.93)
        self.assertEqual(self.cell.normalized_cost, 106.17)      

    def test_plots(self):

        fig1a = self.cell.get_capacity_voltage_plot()
        fig1b = self.cell.get_cost_breakdown_plot(mode='sunburst')
        fig1c = self.cell.get_mass_breakdown_plot(mode='sunburst')

        # fig1a.show()
        # fig1b.show()
        # fig1c.show()

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

    def test_separator(self):
        for s in self.cell.stacks:
            self.assertEqual(s.separator.thickness, 16)
            self.assertEqual(s.separator._thickness, 0.000016)
            self.assertEqual(s.separator.density, 0.4)
            self.assertEqual(round(s.separator._density), 400)
            self.assertEqual(s.separator.porosity, 47)
            self.assertEqual(round(s.separator._porosity, 4), 0.47)
            self.assertEqual(s.separator.slit_width, 11)
            self.assertEqual(s.separator._slit_width, 0.11)
            self.assertEqual(s.separator.fold_length, 18.6)
            self.assertEqual(round(s.separator._fold_length, 3), 0.186)

            self.assertEqual(s.separator.area, 11496.49)
            self.assertEqual(round(s.separator._area, 4), 1.1496)
            self.assertEqual(s.separator.mass, 7.36)
            self.assertEqual(round(s.separator._mass, 4), 0.0074)
            self.assertEqual(s.separator.cost, 1.03)
            self.assertEqual(round(s.separator._cost, 2), 1.03)
            self.assertEqual(s.separator.pore_volume, 8.65)
            self.assertEqual(round(s.separator._pore_volume, 7), 0.0000086)
