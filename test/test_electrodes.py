import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector


class TestElectrodes(unittest.TestCase):

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
        self.cathode1 = Cathode(formulation=cf, mass_loading=10.68, current_collector=ccc, swell_factor=1.0, single_sided_area=172.83)
        
        # construct anode 1
        aam1 = ActiveMaterial(name="Faradion_HC", formula="Na2Ti3O7", specific_cost=14.27, density=1.50, irreversible_capacity_scaling=1, reversible_capacity_scaling=1)
        aca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        ab1 = Binder(name="PVDF", specific_cost=10, density=1.7)
        af = ElectrodeFormulation(active_materials={aam1: 88}, binder={ab1: 3}, conductive_additive={aca1: 9}, calender_density=0.85)
        acc = CurrentCollector(name="Aluminium", formula="Al", specific_cost=6.30, density=2.7, thickness=15)
        self.anode1 = Anode(formulation=af, mass_loading=5.25, current_collector=acc, swell_factor=1.0)

    def test_cathode_thickness(self):
        """
        Test the single sided thickness of the cathode
        """
        self.assertEqual(self.cathode1.single_sided_thickness, 41.1)

    def test_anode_thickness(self):
        """
        Test the single sided thickness of the anode
        """
        self.assertEqual(self.anode1.single_sided_thickness, 61.8)
