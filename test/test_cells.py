import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.Stacks import Stack
from SteerEnergyStorage.Constructions.Cells import StackedPouchCell
from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.Seperators import Separator
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte


class TestCells(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        # construct cathode 1
        cam1 = ActiveMaterial(name="Faradion_Gen2_4.25V", formula="Li2MnSiO4", specific_cost=11.26, density=4, irreversible_capacity_scaling=1, reversible_capacity_scaling=1)
        cca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        cb1 = Binder(name="PVDF", specific_cost=15, density=1.7)
        cf = ElectrodeFormulation(active_materials={cam1: 89}, binder={cb1: 5}, conductive_additive={cca1: 6}, calender_density=2.60)
        ccc = CurrentCollector(name="Aluminium", formula="Al", specific_cost=6.30, density=2.7, thickness=15)
        cathode = Cathode(formulation=cf, mass_loading=10.68, current_collector=ccc, swell_factor=1.0, single_sided_area=172.83, bare_tab_area=8.22)
        
        # construct anode 1
        aam1 = ActiveMaterial(name="Faradion_HC", formula="Na2Ti3O7", specific_cost=14.27, density=1.50, irreversible_capacity_scaling=1, reversible_capacity_scaling=1)
        aca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        ab1 = Binder(name="PVDF", specific_cost=10, density=1.7)
        af = ElectrodeFormulation(active_materials={aam1: 88}, binder={ab1: 3}, conductive_additive={aca1: 9}, calender_density=0.85)
        acc = CurrentCollector(name="Aluminium", formula="Al", specific_cost=6.30, density=2.7, thickness=15)
        anode = Anode(formulation=af, mass_loading=5.25, current_collector=acc, swell_factor=1.0, bare_tab_area=7.55)

        # construct stack
        seperator = Separator(name="Celgard_2325", thickness=16, specific_cost=0.2, density=1.4, slit_width=100, porosity=47, fold_length=186)
        stack = Stack(anode=anode, cathode=cathode, seperator=seperator, anode_mass_loading=5.25, cathode_mass_loading=10.68, n_p_ratio=1.13)

        # construct cell
        electrolyte = Electrolyte(name="LiPF6", formula="LiPF6", specific_cost=8.94, density=1.2)

        self.cell = StackedPouchCell(stack=stack,
                                     width=102.50,
                                     length=188,
                                     n_stack=26,
                                     electrolyte=electrolyte,
                                     electrolyte_overfill=10,
                                     voltage_upper_cut_off=4.2,
                                     voltage_lower_cut_off=1.00,
                                     reversible_capacity=11934,
                                     irreversible_capacity=1215,
                                     )
        
    def test_cell_effective_areal_capacity(self):
        """
        Test the effective areal capacity of the cell
        """
        self.assertEqual(self.cell.effective_areal_capacity, 1.33)
