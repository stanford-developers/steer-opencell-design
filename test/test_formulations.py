import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

class TestFormulations(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        cathode_active_material1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        cathode_active_material1.voltage_cuttoff = 4.35
        cathode_active_material1.density = 4
        cathode_active_material1.specific_cost = 11.26
        
        cathode_conductive_additive1 = ConductiveAdditive.from_database("Super P")
        cathode_conductive_additive1.specific_cost = 9
        cathode_conductive_additive1.density = 1.9

        cathode_conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        cathode_conductive_additive2.specific_cost = 12
        cathode_conductive_additive2.density = 1.0

        cathode_binder1 = Binder.from_database("PVDF")
        cathode_binder1.specific_cost = 15
        cathode_binder1.density = 1.7

        cathode_binder2 = Binder.from_database("CMC")
        cathode_binder2.specific_cost = 10
        cathode_binder2.density = 1.5

        self.cathode_formulation = ElectrodeFormulation(
            active_materials={
                cathode_active_material1: 90,
            }, 
            binders={
                cathode_binder1: 3, 
                cathode_binder2: 2
            }, 
            conductive_additives={
                cathode_conductive_additive1: 3, 
                cathode_conductive_additive2: 2
            }
        )

        anode_active_material = AnodeMaterial.from_database("Hard Carbon (Vendor A)")
        anode_active_material.density = 1.5
        anode_active_material.specific_cost = 14.27

        anode_binder = Binder.from_database("PVDF")
        anode_binder.specific_cost = 10
        anode_binder.density = 1.7

        anode_conductive_additive = ConductiveAdditive.from_database("Super P")
        anode_conductive_additive.specific_cost = 9
        anode_conductive_additive.density = 1.9

        self.anode_formulation = ElectrodeFormulation(
            active_materials={
                anode_active_material: 88
            },
            binders={
                anode_binder: 3
            },
            conductive_additives={
                anode_conductive_additive: 9
            }
        )
        
    def test_formulation(self):
        self.assertTrue(isinstance(self.cathode_formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode_formulation, ElectrodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 1)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(len(self.anode_formulation._active_materials), 1)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.cathode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.anode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.cathode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.density, 1.54)
        self.assertEqual(self.anode_formulation.specific_cost, 13.67)
        self.assertEqual(self.cathode_formulation.density, 3.76)
        self.assertEqual(self.cathode_formulation.specific_cost, 11.29)
        self.assertEqual(round(sum(self.cathode_formulation.specific_cost_breakdown.values()), 2), self.cathode_formulation.specific_cost)
        self.assertEqual(round(sum(self.anode_formulation.specific_cost_breakdown.values()), 2), self.anode_formulation.specific_cost)
        self.assertEqual(round(sum(self.cathode_formulation.density_breakdown.values()), 2), self.cathode_formulation.density)
        self.assertEqual(round(sum(self.anode_formulation.density_breakdown.values()), 2), self.anode_formulation.density)
