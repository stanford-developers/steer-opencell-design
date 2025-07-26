import unittest
import plotly.express as px
from OpenCell.Formulations.ElectrodeFormulations import ElectrodeFormulation
from OpenCell.Constructions.Electrodes import Cathode, Anode
from OpenCell.Formulations.ElectrodeAssemblies import Stack
from OpenCell.Constructions.Cells import StackedPouchCell
from OpenCell.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from OpenCell.Materials.CurrentCollectors import CurrentCollector
from OpenCell.Materials.Separators import Separator
from OpenCell.Materials.Electrolytes import Electrolyte
from OpenCell.Constructions.Containers import Pouch
from OpenCell.Materials.other import Laminate, Tape, Terminal

import datetime as dt

class TestCellsSingleAM(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode
        cathode_active_material = CathodeMaterial(name="LFP", specific_cost=14, density=3.6)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                   binders={cathode_binder: 5},
                                                   conductive_additives={cathode_conductive_additive: 6})

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=160,
                                                     width=108,
                                                     bare_area=822)

        cathode = Cathode(formulation=cathode_formulation,
                          mass_loading=9,
                          current_collector=cathode_current_collector,
                          calender_density=2.3)

        # construct anode
        anode_active_material = AnodeMaterial(name="Synthetic Graphite", specific_cost=11, density=2.26)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=6,
                                                   length=160,
                                                   width=108,
                                                   bare_area=755)
        
        anode = Anode(formulation=anode_formulation,
                      mass_loading=7,
                      current_collector=anode_current_collector,
                      calender_density=1.6)

        # construct separator
        separator = Separator(thickness=19, 
                              areal_cost=1, 
                              density=0.9, 
                              width=110, 
                              porosity=42, 
                              fold_length=186)

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
        
        # Make the cell
        pos_terminal = Terminal(mass = 1, specific_cost = 16, name="Positive Terminal")
        neg_terminal = Terminal(mass = 1, specific_cost = 16, name="Negative Terminal")

        pouch = Pouch(laminate=laminate, 
                      heat_seal_size_sides=7, 
                      heat_seal_size_top=22, 
                      positive_terminal=pos_terminal,
                      negative_terminal=neg_terminal,
                      tape=tape)

        self.cell = StackedPouchCell(pouch=pouch,
                                     stack=stack,
                                     electrolyte=electrolyte,
                                     electrolyte_overfill=10,
                                     reversible_capacity=11.934,
                                     irreversible_capacity=1.22,
                                     n_stacks=1)
        
    def test_cell(self):

        self.assertTrue(isinstance(self.cell, StackedPouchCell))
        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
        self.assertEqual(self.cell.cost, 3.92)
        self.assertEqual(round(self.cell._cost, 2), 3.92)
        self.assertEqual(self.cell.mass, 262.69)
        self.assertEqual(round(self.cell._mass, 3), 0.263)

        self.assertEqual(self.cell.reversible_capacity, 11.93)
        self.assertEqual(self.cell.irreversible_capacity, 1.22)

        self.assertTrue('Capacity (Ah)' in self.cell.full_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.full_cell_curve.columns)
        self.assertTrue('Capacity (Ah)' in self.cell.cathode_half_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.cathode_half_cell_curve.columns)
        self.assertTrue('Capacity (Ah)' in self.cell.anode_half_cell_curve.columns)
        self.assertTrue('Voltage (V)' in self.cell.anode_half_cell_curve.columns)

        self.assertEqual(self.cell.energy, 31.46)
        self.assertEqual(self.cell.energy_density, 194.31)
        self.assertEqual(self.cell.specific_energy, 119.78)
        self.assertEqual(self.cell.normalized_cost, 124.44)      

    def test_plots(self):

        fig1a = self.cell.get_capacity_voltage_plot()
        fig1b = self.cell.get_cost_breakdown_plot(mode='sunburst')
        fig1c = self.cell.get_mass_breakdown_plot(mode='sunburst')

        # fig1a.show()
        # fig1b.show()
        # fig1c.show()
        
    def test_tape(self):
        self.assertEqual(self.cell.pouch.tape.mass, 0.3)
        self.assertEqual(round(self.cell.pouch.tape._mass, 6), 0.0003)
        
    def test_laminate(self):
        self.assertEqual(self.cell.pouch.laminate.thickness, 113)
        self.assertEqual(self.cell.pouch.laminate.areal_mass, 18)
        self.assertEqual(self.cell.pouch.laminate.areal_cost, 4.64)
        self.assertEqual(round(self.cell.pouch.laminate._thickness, 6), 0.000113)
        self.assertEqual(round(self.cell.pouch.laminate._areal_mass, 6), 0.18)
        
    def test_electrolyte(self):
        self.assertEqual(round(self.cell._electrolyte._density,), 1200)
        self.assertEqual(self.cell._electrolyte.density, 1.2)
        self.assertEqual(self.cell._electrolyte.specific_cost, 8.94)

