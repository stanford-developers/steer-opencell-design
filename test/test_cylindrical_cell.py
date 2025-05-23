import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import CylindricalJellyRoll
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import NotchedCurrentCollector
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Constructions.Containers import CylindricalCanister, CylindricalCase, CylindricalTerminalConnector, CylindricalLidAssembly
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.Cells import CylindricalCell

import pandas as pd

class TestCylindricalJellyRoll(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        length = 1100

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

        cathode_current_collector = NotchedCurrentCollector(formula="Cu", 
                                                           length=length,
                                                           width=108,
                                                           thickness=5,
                                                           tab_width=5,
                                                           tab_length=30,
                                                           tab_spacing=30,
                                                           bare_length=30)

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
        
        anode_current_collector = NotchedCurrentCollector(formula="Cu", 
                                                          length=length,
                                                          width=108,
                                                          thickness=5,
                                                          tab_width=5,
                                                          tab_length=30,
                                                          tab_spacing=30,
                                                          bare_length=30)
        
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
                              fold_length=length)
        
        # construct the stack
        cylindrical_jelly_roll = CylindricalJellyRoll(anode=anode, 
                                                      cathode=cathode,
                                                      separator=separator, 
                                                      mandrel_diameter=8)
        
        # build the electrolyte
        electrolyte = Electrolyte(specific_cost=8.94, density=1.2)



        # build the encapsulation
        cylindrical_shell = CylindricalCanister(formula = 'Al', 
                                                outer_diameter=21.6,
                                                wall_thickness=0.3,
                                                length=115)
        
        # build the connectors
        anode_connector = CylindricalTerminalConnector(formula='Al', diameter=10, thickness=1, fill_factor=0.8)
        cathode_connector = CylindricalTerminalConnector(formula='Al', diameter=10, thickness=1, fill_factor=0.8)

        lid = CylindricalLidAssembly(cost=0.1, mass=5, thickness=3)

        case = CylindricalCase(canister=cylindrical_shell, lid_assembly=lid, cathode_terminal_collector=cathode_connector, anode_terminal_collector=anode_connector)

        # build the cell
        self.cell = CylindricalCell(electrode_assembly=cylindrical_jelly_roll,
                                    electrolyte=electrolyte,
                                    electrolyte_overfill=10,
                                    encapsulation=case,
                                    reversible_capacity=5,
                                    irreversible_capacity=0.2)

    def test_instantiate(self):
        """
        Test the instantiation of the cell
        """
        self.assertIsInstance(self.cell, CylindricalCell)
        self.assertEqual(self.cell.cost, 1.02)
        self.assertEqual(round(self.cell._cost, 2), 1.02)
        self.assertEqual(self.cell.electrolyte_overfill, 10)
        self.assertEqual(self.cell._electrolyte_overfill, 0.1)
        self.assertEqual(self.cell.energy, 9.06)

        # TODO: check the energy density
        self.assertEqual(round(self.cell._energy), 32612)
        self.assertEqual(self.cell.energy_density, 214.97)
        self.assertEqual(self.cell.length, 115)
        self.assertEqual(round(self.cell._length, 3), 0.115)
        self.assertEqual(self.cell.mass, 76.1)
        self.assertEqual(round(self.cell._mass, 4), 0.0761)
        self.assertEqual(self.cell.volume, 42.14)
        self.assertEqual(round(self.cell._volume, 6), 4.2e-05)
        self.assertEqual(round(self.cell._diameter, 4), 0.0216)
        self.assertEqual(self.cell.diameter, 2.16)

    def test_plots(self):

        fig1a = self.cell.get_capacity_voltage_plot()
        fig1d = self.cell.get_cost_breakdown_plot(mode='sunburst')
        fig1e = self.cell.get_mass_breakdown_plot(mode='sunburst')
        fig2a = self.cell.get_top_down_view()

        # fig1a.show()
        # fig1d.show()
        # fig1e.show()
        # fig2a.show()

