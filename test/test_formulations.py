import unittest
import warnings
from copy import deepcopy

from steer_opencell_design.Materials.Formulations import CathodeFormulation, AnodeFormulation
from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial, AnodeMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive


class TestSimpleCathodeFormulation(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.cathode_active_material1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.cathode_active_material1.density = 4
        self.cathode_active_material1.specific_cost = 11.26

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

        self.cathode_formulation = CathodeFormulation(
            active_materials={
                self.cathode_active_material1: 90,
            },
            binders={cathode_binder1: 3, cathode_binder2: 2},
            conductive_additives={
                cathode_conductive_additive1: 3,
                cathode_conductive_additive2: 2,
            },
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.cathode_formulation, CathodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 1)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(self.cathode_formulation._name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.density, 3.43)
        self.assertEqual(self.cathode_formulation.specific_cost, 11.29)

    def test_serialization(self):
        serialized = self.cathode_formulation.serialize()
        deserialized = CathodeFormulation.deserialize(serialized)
        self.assertEqual(self.cathode_formulation, deserialized)

    def test_mass_setter(self):

        self.cathode_formulation.mass = 0.45

        self.assertEqual(self.cathode_formulation.mass, 0.45)
        self.assertEqual(self.cathode_formulation.cost, 0.01)
        self.assertEqual(self.cathode_formulation.volume, 0.13)

        material_masses = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_masses += material._mass
        for material in self.cathode_formulation.binders.keys():
            material_masses += material._mass
        for material in self.cathode_formulation.conductive_additives.keys():
            material_masses += material._mass
        self.assertAlmostEqual(material_masses, self.cathode_formulation._mass, 10)

        material_costs = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_costs += material._cost
        for material in self.cathode_formulation.binders.keys():
            material_costs += material._cost
        for material in self.cathode_formulation.conductive_additives.keys():
            material_costs += material._cost
        self.assertAlmostEqual(material_costs, self.cathode_formulation._cost, 10)

        material_volumes = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_volumes += material._volume
        for material in self.cathode_formulation.binders.keys():
            material_volumes += material._volume
        for material in self.cathode_formulation.conductive_additives.keys():
            material_volumes += material._volume
        self.assertAlmostEqual(material_volumes, self.cathode_formulation._volume, 10)

        self.assertEqual(
            self.cathode_formulation.mass_breakdown,
            {
                "NaNiMn P2-O3 Composite": 0.41,
                "PVDF": 0.01,
                "CMC": 0.01,
                "Super P": 0.01,
                "Graphite": 0.01,
            },
        )

        self.assertEqual(
            self.cathode_formulation.cost_breakdown,
            {
                "NaNiMn P2-O3 Composite": 0.0,
                "PVDF": 0.0,
                "CMC": 0.0,
                "Super P": 0.0,
                "Graphite": 0.0,
            },
        )

        def sum_nested_dict(data):
            """Recursively sum all numeric values in a nested dictionary"""
            total = 0
            for key, value in data.items():
                if isinstance(value, dict):
                    total += sum_nested_dict(value)  # Recursive call for nested dict
                elif isinstance(value, (int, float)):
                    total += value
            return total

        self.assertAlmostEqual(self.cathode_formulation._cost, sum_nested_dict(self.cathode_formulation._cost_breakdown), 5)
        self.assertAlmostEqual(self.cathode_formulation._mass, sum_nested_dict(self.cathode_formulation._mass_breakdown), 5)

    def test_volume_setter(self):

        self.cathode_formulation.volume = 0.2

        self.assertEqual(self.cathode_formulation.volume, 0.2)
        self.assertEqual(self.cathode_formulation.mass, 0.69)
        self.assertEqual(self.cathode_formulation.cost, 0.01)

        material_masses = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_masses += material._mass
        for material in self.cathode_formulation.binders.keys():
            material_masses += material._mass
        for material in self.cathode_formulation.conductive_additives.keys():
            material_masses += material._mass
        self.assertAlmostEqual(material_masses, self.cathode_formulation._mass, 10)

        material_costs = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_costs += material._cost
        for material in self.cathode_formulation.binders.keys():
            material_costs += material._cost
        for material in self.cathode_formulation.conductive_additives.keys():
            material_costs += material._cost
        self.assertAlmostEqual(material_costs, self.cathode_formulation._cost, 10)

        material_volumes = 0
        for material in self.cathode_formulation.active_materials.keys():
            material_volumes += material._volume
        for material in self.cathode_formulation.binders.keys():
            material_volumes += material._volume
        for material in self.cathode_formulation.conductive_additives.keys():
            material_volumes += material._volume
        self.assertAlmostEqual(material_volumes, self.cathode_formulation._volume, 10)

    def test_voltage_cutoff(self):
        self.cathode_formulation.voltage_cutoff = 4.2
        figure = self.cathode_formulation.plot_specific_capacity_curve(add_materials=True)

        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            12.8,
        )
        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            25.7,
        )
        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            102.8,
        )

        # figure.show()

    def test_set_voltage_cutoff_edge_case(self):
        lower_voltage = self.cathode_formulation.voltage_cutoff_range[0]
        self.cathode_formulation.voltage_cutoff = lower_voltage

        upper_voltage = self.cathode_formulation.voltage_cutoff_range[1]
        self.cathode_formulation.voltage_cutoff = upper_voltage

        self.assertEqual(self.cathode_formulation.voltage_cutoff, upper_voltage)
        self.assertEqual(
            self.cathode_formulation.voltage_cutoff_hard_range,
            (lower_voltage, upper_voltage),
        )

    def test_active_material_setter(self):
        old_cutoff_voltage = self.cathode_formulation.voltage_cutoff
        new_active_material = CathodeMaterial.from_database("NMC811")
        self.cathode_formulation.active_materials = {new_active_material: 90}
        new_cutoff_voltage = self.cathode_formulation.voltage_cutoff

        self.assertNotEqual(old_cutoff_voltage, new_cutoff_voltage)


class TestMultiCathodeFormulation(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.cathode_active_material1 = CathodeMaterial.from_database("LFP")
        self.cathode_active_material2 = CathodeMaterial.from_database("NMC811")
        self.cathode_active_material2.extrapolation_window = 0.5

        cathode_conductive_additive1 = ConductiveAdditive.from_database("Super P")
        cathode_conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        cathode_binder1 = Binder.from_database("PVDF")
        cathode_binder2 = Binder.from_database("CMC")

        self.cathode_formulation = CathodeFormulation(
            active_materials={
                self.cathode_active_material1: 80,
                self.cathode_active_material2: 10,
            },
            binders={cathode_binder1: 3, cathode_binder2: 2},
            conductive_additives={
                cathode_conductive_additive1: 3,
                cathode_conductive_additive2: 2,
            },
        )

    def test_formulation(self):

        self.assertTrue(isinstance(self.cathode_formulation, CathodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 2)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(self.cathode_formulation._name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.density, 3.37)
        self.assertEqual(self.cathode_formulation.specific_cost, 8.37)

        figure = self.cathode_formulation.plot_specific_capacity_curve(add_materials=True)

        # figure.show()

    def test_equality(self):
        copy_formulation = deepcopy(self.cathode_formulation)
        condition = self.cathode_formulation == copy_formulation
        self.assertTrue(condition)

    def test_voltage_cutoff(self):

        self.cathode_formulation.voltage_cutoff = 4.09
        
        figure = self.cathode_formulation.plot_specific_capacity_curve(add_materials=True)

        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0.2,
        )
        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            0.2,
        )
        self.assertEqual(
            self.cathode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            134.4,
        )

        # figure.show()

    def test_change_active_materials(self):
        self.cathode_formulation.active_materials = {self.cathode_active_material1: 90}
        self.cathode_formulation.voltage_cutoff = 4.09

        self.assertEqual(self.cathode_formulation.density, 3.3)
        self.assertEqual(self.cathode_formulation.specific_cost, 6.47)

        figure = self.cathode_formulation.plot_specific_capacity_curve(add_materials=True)
        # figure.show()


class TestSimpleAnodeFormulation(unittest.TestCase):
    def setUp(self):
        anode_active_material = AnodeMaterial.from_database("Hard Carbon (Vendor A)")
        anode_active_material.density = 1.5
        anode_active_material.specific_cost = 14.27

        anode_binder = Binder.from_database("PVDF")
        anode_binder.specific_cost = 10
        anode_binder.density = 1.7

        anode_conductive_additive = ConductiveAdditive.from_database("Super P")
        anode_conductive_additive.specific_cost = 9
        anode_conductive_additive.density = 1.9

        self.anode_formulation = AnodeFormulation(
            active_materials={anode_active_material: 88},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
        )

        self.anode_formulation2 = AnodeFormulation(
            active_materials={anode_active_material: 88},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
            voltage_cutoff=0.0,
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.anode_formulation, AnodeFormulation))
        self.assertEqual(len(self.anode_formulation._active_materials), 1)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.anode_formulation._name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.density, 1.53)
        self.assertEqual(self.anode_formulation.specific_cost, 13.67)

        figure = self.anode_formulation.plot_specific_capacity_curve(add_materials=True)
        # figure.show()

    def test_plot_specific_capacity_curve(self):
        self.anode_formulation.voltage_cutoff = 0.0
        figure = self.anode_formulation.plot_specific_capacity_curve(add_materials=True)

        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0,
        )
        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            1.8,
        )
        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            262.1,
        )
        # figure.show()

    def test_anode_specific_capacity_curve_set(self):
        figure = self.anode_formulation2.plot_specific_capacity_curve(add_materials=True)
        # figure.show()


class TestDualAnodeFormulation(unittest.TestCase):
    def setUp(self):
        anode_active_material1 = AnodeMaterial.from_database("Hard Carbon (Vendor A)")
        anode_active_material2 = AnodeMaterial.from_database("Hard Carbon (Vendor B)")
        anode_binder = Binder.from_database("PVDF")
        anode_conductive_additive = ConductiveAdditive.from_database("Super P")

        self.anode_formulation = AnodeFormulation(
            active_materials={anode_active_material1: 44, anode_active_material2: 44},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.anode_formulation, AnodeFormulation))
        self.assertEqual(len(self.anode_formulation._active_materials), 2)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.anode_formulation._name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.density, 1.54)
        self.assertEqual(self.anode_formulation.specific_cost, 7.87)

    def test_plot_specific_capacity_curve(self):
        figure = self.anode_formulation.plot_specific_capacity_curve(add_materials=True)

        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0.4,
        )
        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            0.5,
        )
        self.assertEqual(
            self.anode_formulation.specific_capacity_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            76.3,
        )

        # figure.show()


class TestActiveMaterialPropertiesAndSetters(unittest.TestCase):
    """Test the active_material_1, active_material_2, and active_material_3 properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("LFP")
        self.mat2 = CathodeMaterial.from_database("NMC811")
        self.mat3 = CathodeMaterial.from_database("NFM111 (Vendor B)")
        self.mat4 = CathodeMaterial.from_database("NMC622")

    def test_active_material_1_property_single_material(self):
        """Test active_material_1 property with single material."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIs(f.active_material_1, self.mat1)

    def test_active_material_1_property_multiple_materials(self):
        """Test active_material_1 property with multiple materials."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        self.assertIs(f.active_material_1, self.mat1)

    def test_active_material_1_setter_replaces_first_material(self):
        """Test active_material_1 setter replaces first material while keeping mass fraction."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        original_fraction = f._active_materials[self.mat1]
        
        f.active_material_1 = self.mat3
        
        # Check that mat3 is now the first material with original fraction
        self.assertIs(f.active_material_1, self.mat3)
        self.assertEqual(list(f._active_materials.keys())[0], self.mat3)
        self.assertEqual(f._active_materials[self.mat3], original_fraction)
        # Check that mat2 is still there with same fraction
        self.assertEqual(f._active_materials[self.mat2], 0.4)

    def test_active_material_2_property_returns_none_if_missing(self):
        """Test active_material_2 property returns None when only one material exists."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.active_material_2)

    def test_active_material_2_property_with_two_materials(self):
        """Test active_material_2 property with two materials."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        self.assertIs(f.active_material_2, self.mat2)

    def test_active_material_2_setter_replaces_existing_material(self):
        """Test active_material_2 setter replaces existing second material."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        original_fraction = f._active_materials[self.mat2]
        
        f.active_material_2 = self.mat3
        
        # Check that mat3 is now the second material with original fraction
        self.assertIs(f.active_material_2, self.mat3)
        self.assertEqual(list(f._active_materials.keys())[1], self.mat3)
        self.assertEqual(f._active_materials[self.mat3], original_fraction)
        # Check that mat1 is still first
        self.assertEqual(f._active_materials[self.mat1], 0.6)

    def test_active_material_2_setter_adds_if_missing(self):
        """Test active_material_2 setter adds material with 0 mass fraction if missing."""
        f = CathodeFormulation({self.mat1: 100})
        
        f.active_material_2 = self.mat2
        
        # Check that mat2 was added as second material with 0 mass fraction
        self.assertIs(f.active_material_2, self.mat2)
        self.assertEqual(f._active_materials[self.mat2], 0.0)
        self.assertEqual(list(f._active_materials.keys())[1], self.mat2)
        # Check that mat1 is still first with original fraction
        self.assertEqual(f._active_materials[self.mat1], 1.0)

    def test_active_material_3_property_returns_none_if_missing(self):
        """Test active_material_3 property returns None when fewer than 3 materials exist."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        self.assertIsNone(f.active_material_3)

    def test_active_material_3_property_with_three_materials(self):
        """Test active_material_3 property with three materials."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        self.assertIs(f.active_material_3, self.mat3)

    def test_active_material_3_setter_replaces_existing_material(self):
        """Test active_material_3 setter replaces existing third material."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        original_fraction = f._active_materials[self.mat3]
        
        f.active_material_3 = self.mat4
        
        # Check that mat4 is now the third material with original fraction
        self.assertIs(f.active_material_3, self.mat4)
        self.assertEqual(list(f._active_materials.keys())[2], self.mat4)
        self.assertEqual(f._active_materials[self.mat4], original_fraction)
        # Check that first two materials are unchanged
        self.assertEqual(f._active_materials[self.mat1], 0.6)
        self.assertEqual(f._active_materials[self.mat2], 0.3)

    def test_active_material_3_setter_adds_if_missing(self):
        """Test active_material_3 setter adds material with 0 mass fraction if missing."""
        f = CathodeFormulation({self.mat1: 80, self.mat2: 20})
        
        f.active_material_3 = self.mat3
        
        # Check that mat3 was added as third material with 0 mass fraction
        self.assertIs(f.active_material_3, self.mat3)
        self.assertEqual(f._active_materials[self.mat3], 0.0)
        self.assertEqual(list(f._active_materials.keys())[2], self.mat3)
        # Check that first two materials are unchanged
        self.assertEqual(f._active_materials[self.mat1], 0.8)
        self.assertEqual(f._active_materials[self.mat2], 0.2)

    def test_material_order_preservation(self):
        """Test that material order is preserved correctly in all operations."""
        f = CathodeFormulation({self.mat1: 50, self.mat2: 30, self.mat3: 20})
        
        # Replace second material
        f.active_material_2 = self.mat4
        materials_order = list(f._active_materials.keys())
        self.assertEqual(materials_order, [self.mat1, self.mat4, self.mat3])
        
        # Replace first material
        f.active_material_1 = self.mat2
        materials_order = list(f._active_materials.keys())
        self.assertEqual(materials_order, [self.mat2, self.mat4, self.mat3])

    def test_active_material_1_none_removes_material(self):
        """Test that setting active_material_1 to None removes the first active material."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_1 = None
        
        # Should only have the second material now, which becomes the first
        self.assertEqual(f.active_material_1, self.mat2)
        self.assertIsNone(f.active_material_2)
        self.assertEqual(len(f._active_materials), 1)
        self.assertIn(self.mat2, f._active_materials)
        self.assertNotIn(self.mat1, f._active_materials)

    def test_active_material_2_none_removes_material(self):
        """Test that setting active_material_2 to None removes the second active material."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_2 = None
        
        # Should have first and third materials, third becomes second
        self.assertEqual(f.active_material_1, self.mat1)
        self.assertEqual(f.active_material_2, self.mat3)  # Third material becomes second
        self.assertEqual(len(f._active_materials), 2)
        self.assertIn(self.mat1, f._active_materials)
        self.assertIn(self.mat3, f._active_materials)
        self.assertNotIn(self.mat2, f._active_materials)

    def test_active_material_3_none_removes_material(self):
        """Test that setting active_material_3 to None removes the third active material."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_3 = None
        
        # Should only have first two materials
        self.assertEqual(f.active_material_1, self.mat1)
        self.assertEqual(f.active_material_2, self.mat2)
        self.assertIsNone(f.active_material_3)
        self.assertEqual(len(f._active_materials), 2)
        self.assertIn(self.mat1, f._active_materials)
        self.assertIn(self.mat2, f._active_materials)
        self.assertNotIn(self.mat3, f._active_materials)

    def test_active_material_none_with_no_material(self):
        """Test that setting None when material doesn't exist does nothing."""
        f = CathodeFormulation({self.mat1: 100})
        
        # Setting active_material_2 to None when it doesn't exist should do nothing
        f.active_material_2 = None
        
        self.assertEqual(f.active_material_1, self.mat1)
        self.assertIsNone(f.active_material_2)
        self.assertEqual(len(f._active_materials), 1)


class TestActiveMaterialWeightPropertiesAndSetters(unittest.TestCase):
    """Test the active_material_1_weight, active_material_2_weight, and active_material_3_weight properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("LFP")
        self.mat2 = CathodeMaterial.from_database("NMC811")
        self.mat3 = CathodeMaterial.from_database("NFM111 (Vendor B)")

    def test_active_material_1_weight_property(self):
        """Test active_material_1_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        self.assertEqual(f.active_material_1_weight, 60.0)

    def test_active_material_1_weight_setter(self):
        """Test active_material_1_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_1_weight = 70.0
        
        self.assertEqual(f.active_material_1_weight, 70.0)
        self.assertEqual(f._active_materials[self.mat1], 0.7)
        # Other materials unchanged
        self.assertEqual(f._active_materials[self.mat2], 0.4)

    def test_active_material_2_weight_property_with_material(self):
        """Test active_material_2_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        self.assertEqual(f.active_material_2_weight, 40.0)

    def test_active_material_2_weight_property_without_material(self):
        """Test active_material_2_weight property returns None when no second material."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.active_material_2_weight)

    def test_active_material_2_weight_setter(self):
        """Test active_material_2_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_2_weight = 30.0
        
        self.assertEqual(f.active_material_2_weight, 30.0)
        self.assertEqual(f._active_materials[self.mat2], 0.3)
        # Other materials unchanged
        self.assertEqual(f._active_materials[self.mat1], 0.6)

    def test_active_material_2_weight_setter_error_when_missing(self):
        """Test active_material_2_weight setter raises error when no second material."""
        f = CathodeFormulation({self.mat1: 100})
        
        with self.assertRaises(ValueError) as context:
            f.active_material_2_weight = 50.0
        
        self.assertIn("fewer than 2 active materials", str(context.exception))

    def test_active_material_3_weight_property_with_material(self):
        """Test active_material_3_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        self.assertEqual(f.active_material_3_weight, 10.0)

    def test_active_material_3_weight_property_without_material(self):
        """Test active_material_3_weight property returns None when no third material."""
        f = CathodeFormulation({self.mat1: 80, self.mat2: 20})
        self.assertIsNone(f.active_material_3_weight)

    def test_active_material_3_weight_setter(self):
        """Test active_material_3_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_3_weight = 15.0
        
        self.assertEqual(f.active_material_3_weight, 15.0)
        self.assertEqual(f._active_materials[self.mat3], 0.15)
        # Other materials unchanged
        self.assertEqual(f._active_materials[self.mat1], 0.6)
        self.assertEqual(f._active_materials[self.mat2], 0.3)

    def test_active_material_3_weight_setter_error_when_missing(self):
        """Test active_material_3_weight setter raises error when no third material."""
        f = CathodeFormulation({self.mat1: 80, self.mat2: 20})
        
        with self.assertRaises(ValueError) as context:
            f.active_material_3_weight = 10.0
        
        self.assertIn("fewer than 3 active materials", str(context.exception))

    def test_weight_validation_errors(self):
        """Test that weight setters validate percentage values."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 30, self.mat3: 10})
        
        # Test negative values
        with self.assertRaises(ValueError):
            f.active_material_1_weight = -10.0
        
        # Test values over 100
        with self.assertRaises(ValueError):
            f.active_material_1_weight = 110.0

    def test_weight_zero_value(self):
        """Test that weight can be set to zero."""
        f = CathodeFormulation({self.mat1: 60, self.mat2: 40})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.active_material_2_weight = 0.0
        
        self.assertEqual(f.active_material_2_weight, 0.0)
        self.assertEqual(f._active_materials[self.mat2], 0.0)


class TestBinderPropertiesAndSetters(unittest.TestCase):
    """Test the binder_1 and binder_2 properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.mat1.density = 2.0
        self.mat1.specific_cost = 10.0
        
        self.binder1 = Binder.from_database("PVDF")
        self.binder1.density = 1.5
        self.binder1.specific_cost = 15.0
        
        self.binder2 = Binder.from_database("CMC")
        self.binder2.density = 1.7
        self.binder2.specific_cost = 12.0
        
        self.binder3 = Binder.from_database("SBR")
        self.binder3.density = 1.6
        self.binder3.specific_cost = 18.0

    def test_binder_1_property_with_binders(self):
        """Test binder_1 property returns the first binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        self.assertEqual(f.binder_1, self.binder1)

    def test_binder_1_property_without_binders(self):
        """Test binder_1 property returns None when no binders exist."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.binder_1)

    def test_binder_1_setter_replaces_existing(self):
        """Test binder_1 setter replaces existing first binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        f.binder_1 = self.binder3
        
        self.assertEqual(f.binder_1, self.binder3)
        binders_list = list(f._binders.keys())
        self.assertEqual(binders_list[0], self.binder3)  # First position
        self.assertEqual(f._binders[self.binder3], 0.03)  # Same weight as before

    def test_binder_1_setter_adds_new_when_none_exist(self):
        """Test binder_1 setter adds new binder when none exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        f.binder_1 = self.binder1
        
        self.assertEqual(f.binder_1, self.binder1)
        self.assertEqual(f._binders[self.binder1], 0.0)

    def test_binder_2_property_with_binders(self):
        """Test binder_2 property returns the second binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        self.assertEqual(f.binder_2, self.binder2)

    def test_binder_2_property_with_only_one_binder(self):
        """Test binder_2 property returns None when only one binder exists."""
        f = CathodeFormulation({self.mat1: 97}, binders={self.binder1: 3})
        self.assertIsNone(f.binder_2)

    def test_binder_2_setter_replaces_existing(self):
        """Test binder_2 setter replaces existing second binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        f.binder_2 = self.binder3
        
        self.assertEqual(f.binder_2, self.binder3)
        binders_list = list(f._binders.keys())
        self.assertEqual(binders_list[1], self.binder3)  # Second position
        self.assertEqual(f._binders[self.binder3], 0.02)  # Same weight as before

    def test_binder_2_setter_adds_when_one_exists(self):
        """Test binder_2 setter adds second binder when only one exists."""
        f = CathodeFormulation({self.mat1: 97}, binders={self.binder1: 3})
        
        f.binder_2 = self.binder2
        
        self.assertEqual(f.binder_2, self.binder2)
        self.assertEqual(f._binders[self.binder2], 0.0)

    def test_binder_2_setter_error_when_none_exist(self):
        """Test binder_2 setter raises error when no binders exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        with self.assertRaises(ValueError) as context:
            f.binder_2 = self.binder2
        
        self.assertIn("no binders", str(context.exception))

    def test_binder_order_maintained_after_setter(self):
        """Test that binder order is maintained correctly after using setters."""
        f = CathodeFormulation({self.mat1: 93}, binders={self.binder2: 4, self.binder1: 3})
        
        # binder2 should be first, binder1 should be second originally
        self.assertEqual(f.binder_1, self.binder2)
        self.assertEqual(f.binder_2, self.binder1)
        
        # Change the first binder
        f.binder_1 = self.binder3
        
        # binder3 should now be first, binder1 should still be second
        self.assertEqual(f.binder_1, self.binder3)
        self.assertEqual(f.binder_2, self.binder1)
        
        binders_list = list(f._binders.keys())
        self.assertEqual(binders_list, [self.binder3, self.binder1])

    def test_validation_error_for_invalid_binder_type(self):
        """Test that setters validate binder type."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 5})
        
        with self.assertRaises(TypeError):
            f.binder_1 = "not a binder"
        
        with self.assertRaises(TypeError):
            f.binder_2 = "not a binder"

    def test_binder_1_none_removes_material(self):
        """Test that setting binder_1 to None removes the first binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.binder_1 = None
        
        # Should only have the second binder now, which becomes the first
        self.assertEqual(f.binder_1, self.binder2)
        self.assertIsNone(f.binder_2)
        self.assertEqual(len(f._binders), 1)
        self.assertIn(self.binder2, f._binders)
        self.assertNotIn(self.binder1, f._binders)

    def test_binder_2_none_removes_material(self):
        """Test that setting binder_2 to None removes the second binder."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.binder_2 = None
        
        # Should only have the first binder
        self.assertEqual(f.binder_1, self.binder1)
        self.assertIsNone(f.binder_2)
        self.assertEqual(len(f._binders), 1)
        self.assertIn(self.binder1, f._binders)
        self.assertNotIn(self.binder2, f._binders)

    def test_binder_none_with_no_material(self):
        """Test that setting None when binder doesn't exist does nothing."""
        f = CathodeFormulation({self.mat1: 97}, binders={self.binder1: 3})
        
        # Setting binder_2 to None when it doesn't exist should do nothing
        f.binder_2 = None
        
        self.assertEqual(f.binder_1, self.binder1)
        self.assertIsNone(f.binder_2)
        self.assertEqual(len(f._binders), 1)


class TestBinderWeightPropertiesAndSetters(unittest.TestCase):
    """Test the binder_1_weight and binder_2_weight properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.mat1.density = 2.0
        self.mat1.specific_cost = 10.0
        
        self.binder1 = Binder.from_database("PVDF")
        self.binder1.density = 1.5
        self.binder1.specific_cost = 15.0
        
        self.binder2 = Binder.from_database("CMC")
        self.binder2.density = 1.7
        self.binder2.specific_cost = 12.0

    def test_binder_1_weight_property(self):
        """Test binder_1_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        self.assertEqual(f.binder_1_weight, 3.0)

    def test_binder_1_weight_property_without_binders(self):
        """Test binder_1_weight property returns None when no binders exist."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.binder_1_weight)

    def test_binder_1_weight_setter(self):
        """Test binder_1_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.binder_1_weight = 5.0
        
        self.assertEqual(f.binder_1_weight, 5.0)
        self.assertEqual(f._binders[self.binder1], 0.05)
        # Other materials unchanged
        self.assertEqual(f._binders[self.binder2], 0.02)

    def test_binder_1_weight_setter_error_when_missing(self):
        """Test binder_1_weight setter raises error when no binders exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        with self.assertRaises(ValueError) as context:
            f.binder_1_weight = 5.0
        
        self.assertIn("no binders", str(context.exception))

    def test_binder_2_weight_property_with_binders(self):
        """Test binder_2_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        self.assertEqual(f.binder_2_weight, 2.0)

    def test_binder_2_weight_property_with_one_binder(self):
        """Test binder_2_weight property returns None when only one binder exists."""
        f = CathodeFormulation({self.mat1: 97}, binders={self.binder1: 3})
        self.assertIsNone(f.binder_2_weight)

    def test_binder_2_weight_setter(self):
        """Test binder_2_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.binder_2_weight = 4.0
        
        self.assertEqual(f.binder_2_weight, 4.0)
        self.assertEqual(f._binders[self.binder2], 0.04)
        # Other materials unchanged
        self.assertEqual(f._binders[self.binder1], 0.03)

    def test_binder_2_weight_setter_error_when_missing(self):
        """Test binder_2_weight setter raises error when fewer than 2 binders exist."""
        f = CathodeFormulation({self.mat1: 97}, binders={self.binder1: 3})
        
        with self.assertRaises(ValueError) as context:
            f.binder_2_weight = 2.0
        
        self.assertIn("fewer than 2 binders", str(context.exception))

    def test_binder_weight_validation_errors(self):
        """Test that binder weight setters validate percentage values."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        # Test negative values
        with self.assertRaises(ValueError):
            f.binder_1_weight = -1.0
        
        # Test values over 100
        with self.assertRaises(ValueError):
            f.binder_1_weight = 110.0

    def test_binder_weight_zero_value(self):
        """Test that binder weight can be set to zero."""
        f = CathodeFormulation({self.mat1: 95}, binders={self.binder1: 3, self.binder2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.binder_2_weight = 0.0
        
        self.assertEqual(f.binder_2_weight, 0.0)
        self.assertEqual(f._binders[self.binder2], 0.0)


class TestConductiveAdditivePropertiesAndSetters(unittest.TestCase):
    """Test the conductive_additive_1 and conductive_additive_2 properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.mat1.density = 2.0
        self.mat1.specific_cost = 10.0
        
        self.additive1 = ConductiveAdditive.from_database("Super P")
        self.additive1.density = 1.9
        self.additive1.specific_cost = 9.0
        
        self.additive2 = ConductiveAdditive.from_database("Graphite")
        self.additive2.density = 1.0
        self.additive2.specific_cost = 12.0
        
        self.additive3 = ConductiveAdditive.from_database("Carbon Nanotubes")
        self.additive3.density = 2.1
        self.additive3.specific_cost = 200.0

    def test_conductive_additive_1_property_with_additives(self):
        """Test conductive_additive_1 property returns the first conductive additive."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        self.assertEqual(f.conductive_additive_1, self.additive1)

    def test_conductive_additive_1_property_without_additives(self):
        """Test conductive_additive_1 property returns None when no conductive additives exist."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.conductive_additive_1)

    def test_conductive_additive_1_setter_replaces_existing(self):
        """Test conductive_additive_1 setter replaces existing first conductive additive."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        f.conductive_additive_1 = self.additive3
        
        self.assertEqual(f.conductive_additive_1, self.additive3)
        additives_list = list(f._conductive_additives.keys())
        self.assertEqual(additives_list[0], self.additive3)  # First position
        self.assertEqual(f._conductive_additives[self.additive3], 0.03)  # Same weight as before

    def test_conductive_additive_1_setter_adds_new_when_none_exist(self):
        """Test conductive_additive_1 setter adds new conductive additive when none exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        f.conductive_additive_1 = self.additive1
        
        self.assertEqual(f.conductive_additive_1, self.additive1)
        self.assertEqual(f._conductive_additives[self.additive1], 0.0)

    def test_conductive_additive_2_property_with_additives(self):
        """Test conductive_additive_2 property returns the second conductive additive."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        self.assertEqual(f.conductive_additive_2, self.additive2)

    def test_conductive_additive_2_property_with_only_one_additive(self):
        """Test conductive_additive_2 property returns None when only one conductive additive exists."""
        f = CathodeFormulation({self.mat1: 97}, conductive_additives={self.additive1: 3})
        self.assertIsNone(f.conductive_additive_2)

    def test_conductive_additive_2_setter_replaces_existing(self):
        """Test conductive_additive_2 setter replaces existing second conductive additive."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        f.conductive_additive_2 = self.additive3
        
        self.assertEqual(f.conductive_additive_2, self.additive3)
        additives_list = list(f._conductive_additives.keys())
        self.assertEqual(additives_list[1], self.additive3)  # Second position
        self.assertEqual(f._conductive_additives[self.additive3], 0.02)  # Same weight as before

    def test_conductive_additive_2_setter_adds_when_one_exists(self):
        """Test conductive_additive_2 setter adds second conductive additive when only one exists."""
        f = CathodeFormulation({self.mat1: 97}, conductive_additives={self.additive1: 3})
        
        f.conductive_additive_2 = self.additive2
        
        self.assertEqual(f.conductive_additive_2, self.additive2)
        self.assertEqual(f._conductive_additives[self.additive2], 0.0)

    def test_conductive_additive_2_setter_error_when_none_exist(self):
        """Test conductive_additive_2 setter raises error when no conductive additives exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        with self.assertRaises(ValueError) as context:
            f.conductive_additive_2 = self.additive2
        
        self.assertIn("no conductive additives", str(context.exception))

    def test_conductive_additive_order_maintained_after_setter(self):
        """Test that conductive additive order is maintained correctly after using setters."""
        f = CathodeFormulation({self.mat1: 93}, conductive_additives={self.additive2: 4, self.additive1: 3})
        
        # additive2 should be first, additive1 should be second originally
        self.assertEqual(f.conductive_additive_1, self.additive2)
        self.assertEqual(f.conductive_additive_2, self.additive1)
        
        # Change the first conductive additive
        f.conductive_additive_1 = self.additive3
        
        # additive3 should now be first, additive1 should still be second
        self.assertEqual(f.conductive_additive_1, self.additive3)
        self.assertEqual(f.conductive_additive_2, self.additive1)
        
        additives_list = list(f._conductive_additives.keys())
        self.assertEqual(additives_list, [self.additive3, self.additive1])

    def test_validation_error_for_invalid_conductive_additive_type(self):
        """Test that setters validate conductive additive type."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 5})
        
        with self.assertRaises(TypeError):
            f.conductive_additive_1 = "not an additive"
        
        with self.assertRaises(TypeError):
            f.conductive_additive_2 = "not an additive"


class TestConductiveAdditiveWeightPropertiesAndSetters(unittest.TestCase):
    """Test the conductive_additive_1_weight and conductive_additive_2_weight properties and setters."""
    
    def setUp(self):
        """Set up test materials for use in tests."""
        self.mat1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.mat1.density = 2.0
        self.mat1.specific_cost = 10.0
        
        self.additive1 = ConductiveAdditive.from_database("Super P")
        self.additive1.density = 1.9
        self.additive1.specific_cost = 9.0
        
        self.additive2 = ConductiveAdditive.from_database("Graphite")
        self.additive2.density = 1.0
        self.additive2.specific_cost = 12.0

    def test_conductive_additive_1_weight_property(self):
        """Test conductive_additive_1_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        self.assertEqual(f.conductive_additive_1_weight, 3.0)

    def test_conductive_additive_1_weight_property_without_additives(self):
        """Test conductive_additive_1_weight property returns None when no conductive additives exist."""
        f = CathodeFormulation({self.mat1: 100})
        self.assertIsNone(f.conductive_additive_1_weight)

    def test_conductive_additive_1_weight_setter(self):
        """Test conductive_additive_1_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.conductive_additive_1_weight = 5.0
        
        self.assertEqual(f.conductive_additive_1_weight, 5.0)
        self.assertEqual(f._conductive_additives[self.additive1], 0.05)
        # Other materials unchanged
        self.assertEqual(f._conductive_additives[self.additive2], 0.02)

    def test_conductive_additive_1_weight_setter_error_when_missing(self):
        """Test conductive_additive_1_weight setter raises error when no conductive additives exist."""
        f = CathodeFormulation({self.mat1: 100})
        
        with self.assertRaises(ValueError) as context:
            f.conductive_additive_1_weight = 5.0
        
        self.assertIn("no conductive additives", str(context.exception))

    def test_conductive_additive_2_weight_property_with_additives(self):
        """Test conductive_additive_2_weight property returns correct percentage."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        self.assertEqual(f.conductive_additive_2_weight, 2.0)

    def test_conductive_additive_2_weight_property_with_one_additive(self):
        """Test conductive_additive_2_weight property returns None when only one conductive additive exists."""
        f = CathodeFormulation({self.mat1: 97}, conductive_additives={self.additive1: 3})
        self.assertIsNone(f.conductive_additive_2_weight)

    def test_conductive_additive_2_weight_setter(self):
        """Test conductive_additive_2_weight setter updates the weight percentage."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.conductive_additive_2_weight = 4.0
        
        self.assertEqual(f.conductive_additive_2_weight, 4.0)
        self.assertEqual(f._conductive_additives[self.additive2], 0.04)
        # Other materials unchanged
        self.assertEqual(f._conductive_additives[self.additive1], 0.03)

    def test_conductive_additive_2_weight_setter_error_when_missing(self):
        """Test conductive_additive_2_weight setter raises error when fewer than 2 conductive additives exist."""
        f = CathodeFormulation({self.mat1: 97}, conductive_additives={self.additive1: 3})
        
        with self.assertRaises(ValueError) as context:
            f.conductive_additive_2_weight = 2.0
        
        self.assertIn("fewer than 2 conductive additives", str(context.exception))

    def test_conductive_additive_weight_validation_errors(self):
        """Test that conductive additive weight setters validate percentage values."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        # Test negative values
        with self.assertRaises(ValueError):
            f.conductive_additive_1_weight = -1.0
        
        # Test values over 100
        with self.assertRaises(ValueError):
            f.conductive_additive_1_weight = 110.0

    def test_conductive_additive_weight_zero_value(self):
        """Test that conductive additive weight can be set to zero."""
        f = CathodeFormulation({self.mat1: 95}, conductive_additives={self.additive1: 3, self.additive2: 2})
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f.conductive_additive_2_weight = 0.0
        
        self.assertEqual(f.conductive_additive_2_weight, 0.0)
        self.assertEqual(f._conductive_additives[self.additive2], 0.0)


if __name__ == "__main__":
    unittest.main()


