import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import Stack
from SteerEnergyStorage.Constructions.Cells import StackedPouchCell
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, Binder, ConductiveAdditive
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
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

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
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=5,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_area=7.55)

        # construct separator
        separator = Separator(thickness=16, 
                              areal_cost=0.9, 
                              density=0.4, 
                              slit_width=11.0, 
                              porosity=47, 
                              fold_length=18.6)

        # construct the stack
        stack = Stack(anode=anode_current_collector, 
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
                                     irreversible_capacity=1.215,
                                     grid_n=200)
    
    def test_cell(self):

        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(round(self.cell._electrolyte_overfill, 4), 0.1)
        self.assertEqual(self.cell.cost, 2.76)
        self.assertEqual(round(self.cell._cost, 2), 2.76)
        self.assertEqual(self.cell.mass, 179.68)
        self.assertEqual(round(self.cell._mass, 3), 0.180)
        self.assertEqual(self.cell.thickness, 3.82)
        self.assertEqual(round(self.cell._thickness, 4), 0.0038)

        self.assertEqual(self.cell.reversible_capacity, 11.93)
        self.assertEqual(self.cell.irreversible_capacity, 1.22)
        
        figure1 = self.cell.get_capacity_voltage_plot()
        figure2 = self.cell.get_cost_breakdown_plot()
        figure3 = self.cell.get_mass_breakdown_plot()
        # figure1.show()
        # figure2.show()
        # figure3.show()

        self.assertEqual(self.cell.energy, 38.87)
        self.assertEqual(self.cell.energy_density, 395.0)
        self.assertEqual(self.cell.specific_energy, 216.35)
        self.assertEqual(self.cell.normalized_cost, 70.99)

    def test_electrolyte(self):
        self.assertEqual(round(self.cell.electrolyte._density,), 1200)
        self.assertEqual(self.cell.electrolyte.density, 1.2)
        self.assertEqual(self.cell.electrolyte.specific_cost, 8.94)
