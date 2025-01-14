import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.ElectrodeMaterials import ActiveMaterial, Binder, ConductiveAdditive


class TestElectrodeFormulations(unittest.TestCase):
    
    def setUp(self):
        """
        Set up
        """
        am1 = ActiveMaterial(name="Faradion_Gen2_4.25V", formula="Li2MnSiO4", specific_cost=11.26, density=4, irreversible_capacity_scaling=1, reversible_capacity_scaling=1)
        ca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        b1 = Binder(name="PVDF", specific_cost=15, density=1.7)

        self.cathode_formulation_1 = ElectrodeFormulation(active_materials={am1: 89}, 
                                                          binder={b1: 5}, 
                                                          conductive_additive={ca1: 6}, 
                                                          calender_density=2.60)
        

        am1 = ActiveMaterial(name="Faradion_HC", formula="Na2Ti3O7", specific_cost=14.27, density=1.50, irreversible_capacity_scaling=1, reversible_capacity_scaling=1)
        ca1 = ConductiveAdditive(name="SuperC65", specific_cost=9, density=1.9)
        b1 = Binder(name="PVDF", specific_cost=10, density=1.7)

        self.anode_formulation_1 = ElectrodeFormulation(active_materials={am1: 88},
                                                        binder={b1: 3},
                                                        conductive_additive={ca1: 9},
                                                        calender_density=0.85)

    def test_cathode_formulation_porosity(self):
        """
        test the porosity of the cathode formulation is being calculated correctly
        """
        self.assertEqual(self.cathode_formulation_1.porosity, 26.29)

    def test_anode_formulation_porosity(self):
        """
        test the porosity of the anode formulation is being calculated correctly
        """
        self.assertEqual(self.anode_formulation_1.porosity, 44.61)
        