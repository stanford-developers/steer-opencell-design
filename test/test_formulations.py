import unittest
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

class TestFormulations(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        cathode_active_material1 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_active_material2 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.35V", 
                                                   specific_cost=15.21, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive1 = ConductiveAdditive(specific_cost=9, density=1.9, name="Carbon Black")

        cathode_conductive_additive2 = ConductiveAdditive(specific_cost=12, density=1.0, name="Graphite")

        cathode_binder1 = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_binder2 = Binder(name="CMC", specific_cost=10, density=1.5)

        self.cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material1: 59, cathode_active_material2: 31},
                                                        binders={cathode_binder1: 3, cathode_binder2: 2},
                                                        conductive_additives={cathode_conductive_additive1: 3, cathode_conductive_additive2: 2})

        # construct anode
        anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        self.anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                      binders={anode_binder: 3},
                                                      conductive_additives={anode_conductive_additive: 9})
        
    def test_formulation(self):
        self.assertTrue(isinstance(self.cathode_formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode_formulation, ElectrodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 2)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(len(self.anode_formulation._active_materials), 1)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.cathode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.anode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.cathode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.density, 1.5)
        self.assertEqual(self.anode_formulation.specific_cost, 13.67)
        self.assertEqual(self.cathode_formulation.density, 3.8)
        self.assertEqual(self.cathode_formulation.specific_cost, 12.52)


class TestFormulationsDatabase(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        cathode_active_material1 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_active_material2 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.35V", 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive1 = ConductiveAdditive(specific_cost=9, density=1.9, name="Carbon Black")

        cathode_conductive_additive2 = ConductiveAdditive(specific_cost=12, density=1.0, name="Graphite")

        cathode_binder1 = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_binder2 = Binder(name="CMC", specific_cost=10, density=1.5)

        self.cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material1: 59, cathode_active_material2: 31},
                                                        binders={cathode_binder1: 3, cathode_binder2: 2},
                                                        conductive_additives={cathode_conductive_additive1: 3, cathode_conductive_additive2: 2})

        # construct anode
        anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        self.anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                      binders={anode_binder: 3},
                                                      conductive_additives={anode_conductive_additive: 9})
        
    def test_formulation(self):
        self.assertTrue(isinstance(self.cathode_formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode_formulation, ElectrodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 2)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(len(self.anode_formulation._active_materials), 1)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.cathode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.anode_formulation._name, 'electrode_formulation')
        self.assertEqual(self.cathode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.name, 'Electrode Formulation')
        self.assertEqual(self.anode_formulation.density, 1.5)
        self.assertEqual(self.anode_formulation.specific_cost, 7.27)
        self.assertEqual(self.cathode_formulation.density, 4.1)
        self.assertEqual(self.cathode_formulation.specific_cost, 11.06)