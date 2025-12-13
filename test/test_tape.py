from copy import deepcopy
import unittest
import numpy as np
from steer_opencell_design.Constructions.ElectrodeAssemblies.Tape import Tape
from steer_opencell_design.Materials.Other import TapeMaterial
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

pio.renderers.default = "browser"


class TestSimpleTape(unittest.TestCase):
    """Test Tape class with minimal initialization (no width/length)."""

    def setUp(self):
        """Set up test fixtures with basic tape."""
        tape_material = TapeMaterial.from_database(name="Kapton")
        self.tape = Tape(material=tape_material, thickness=25)

    def test_equality(self):
        """Test tape equality comparison."""
        temp_tape = deepcopy(self.tape)
        condition = self.tape == temp_tape
        self.assertTrue(condition)

    def test_basic_properties(self):
        """Test basic properties are set correctly."""
        self.assertEqual(self.tape.thickness, 25.0)
        self.assertEqual(self.tape.name, "Tape")
        self.assertIsNotNone(self.tape.material)
        self.assertEqual(self.tape.material.name, "Kapton")

    def test_no_bulk_properties_without_dimensions(self):
        """Test that bulk properties are None when dimensions not set."""
        self.assertIsNone(self.tape.length)
        self.assertIsNone(self.tape.width)
        self.assertIsNone(self.tape.area)
        self.assertIsNone(self.tape.mass)
        self.assertIsNone(self.tape.cost)

    def test_areal_cost_calculation(self):
        """Test areal cost calculation from material properties."""
        # Areal cost should be calculated from material density, thickness, and specific cost
        expected_areal_cost = (
            self.tape.material._density * 
            self.tape._thickness * 
            self.tape.material._specific_cost
        )
        self.assertAlmostEqual(self.tape.areal_cost, expected_areal_cost, places=2)

    def test_thickness_range(self):
        """Test thickness range property."""
        thickness_range = self.tape.thickness_range
        self.assertEqual(len(thickness_range), 2)
        self.assertLess(thickness_range[0], thickness_range[1])
        self.assertEqual(thickness_range, (0, 100))

    def test_width_range_default(self):
        """Test default width range when no specific range is set."""
        width_range = self.tape.width_range
        self.assertEqual(width_range, (0, 500))


class TestTapeWithDimensions(unittest.TestCase):
    """Test Tape class with full initialization (including width/length)."""

    def setUp(self):
        """Set up test fixtures with dimensioned tape."""
        tape_material = TapeMaterial.from_database(name="Kapton")
        self.tape = Tape(
            material=tape_material, 
            thickness=25, 
            length=100, 
            width=50,
            name="Test Kapton Tape"
        )
        
        # Create alternative material for testing material setter
        self.alternative_material = TapeMaterial(
            name="Test Polyimide",
            density=1420,  # kg/m³
            specific_cost=50.0,  # $/kg
            color="orange"
        )

    def test_equality(self):
        """Test tape equality comparison."""
        temp_tape = deepcopy(self.tape)
        condition = self.tape == temp_tape
        self.assertTrue(condition)

    def test_dimensions_properties(self):
        """Test dimension properties are set correctly."""
        self.assertEqual(self.tape.length, 100.0)
        self.assertEqual(self.tape.width, 50.0)
        self.assertEqual(self.tape.thickness, 25.0)
        self.assertEqual(self.tape.name, "Test Kapton Tape")

    def test_bulk_properties_calculation(self):
        """Test bulk properties are calculated when dimensions are set."""
        # Should have bulk properties when both dimensions are set
        self.assertIsNotNone(self.tape.area)
        self.assertIsNotNone(self.tape.mass)
        self.assertIsNotNone(self.tape.cost)

    def test_mass_calculation(self):
        """Test mass calculation from material properties."""
        # Mass = area * density * thickness
        area_m2 = self.tape._area
        expected_mass_kg = area_m2 * self.tape.material._density * self.tape._thickness
        expected_mass_g = expected_mass_kg * 1000  # Convert to grams
        self.assertAlmostEqual(self.tape.mass, expected_mass_g, places=2)


class TestTapeSetters(unittest.TestCase):
    """Test Tape class property setters."""

    def setUp(self):
        """Set up test fixtures."""
        tape_material = TapeMaterial.from_database(name="Kapton")
        self.tape = Tape(material=tape_material, thickness=25)

    def test_name_setter(self):
        """Test name setter validation."""
        self.tape.name = "Custom Tape Name"
        self.assertEqual(self.tape.name, "Custom Tape Name")

    def test_thickness_setter(self):
        """Test thickness setter and validation."""
        original_thickness = self.tape.thickness
        original_areal_cost = self.tape.areal_cost
        self.tape.thickness = 50
        self.assertEqual(self.tape.thickness, 50.0)
        self.assertAlmostEqual(self.tape.areal_cost, (original_areal_cost / original_thickness) * self.tape.thickness, places=1)

    def test_length_setter(self):
        """Test length setter and validation."""
        self.tape.length = 200
        self.assertEqual(self.tape.length, 200.0)

    def test_width_setter(self):
        """Test width setter and validation."""
        self.tape.width = 75
        self.assertEqual(self.tape.width, 75.0)

    def test_material_setter(self):
        """Test material setter and validation."""
        new_material = TapeMaterial(
            name="Test Material",
            density=1000,
            specific_cost=30.0,
            color="blue"
        )
        
        original_areal_cost = self.tape.areal_cost
        self.tape.material = new_material
        
        self.assertEqual(self.tape.material.name, "Test Material")
        # Areal cost should be recalculated with new material
        self.assertNotEqual(self.tape.areal_cost, original_areal_cost)

    def test_areal_cost_setter(self):
        """Test areal cost setter updates material specific cost."""
        original_specific_cost = self.tape.material._specific_cost
        new_areal_cost = 0.1
        
        self.tape.areal_cost = new_areal_cost
        
        self.assertAlmostEqual(self.tape.areal_cost, new_areal_cost, places=2)
        # Material specific cost should be updated
        self.assertNotEqual(self.tape.material._specific_cost, original_specific_cost)


class TestTapeBulkPropertyRecalculation(unittest.TestCase):
    """Test bulk property recalculation when dimensions change."""

    def setUp(self):
        """Set up test fixtures."""
        tape_material = TapeMaterial.from_database(name="Kapton")
        self.tape = Tape(material=tape_material, thickness=25, length=100, width=50)

    def test_bulk_properties_recalculated_on_dimension_change(self):
        """Test that bulk properties are recalculated when dimensions change."""
        original_area = self.tape.area
        original_mass = self.tape.mass
        original_cost = self.tape.cost
        
        # Change length
        self.tape.length = 200
        
        # Properties should be different
        self.assertNotEqual(self.tape.area, original_area)
        self.assertNotEqual(self.tape.mass, original_mass)
        self.assertNotEqual(self.tape.cost, original_cost)
        
        # New area should be double (200mm vs 100mm length)
        self.assertAlmostEqual(self.tape.area, original_area * 2, places=1)

    def test_bulk_properties_none_when_dimension_removed(self):
        """Test that bulk properties become None when a dimension is removed."""
        # Initially should have bulk properties
        self.assertIsNotNone(self.tape.area)
        self.assertIsNotNone(self.tape.mass)
        self.assertIsNotNone(self.tape.cost)
        
        # Remove one dimension by setting to None would require modifying setters
        # For now, test by creating a new tape without one dimension
        tape_material = TapeMaterial.from_database(name="Kapton")
        partial_tape = Tape(material=tape_material, thickness=25, length=100)
        
        # Should not have bulk properties
        self.assertIsNone(partial_tape.area)
        self.assertIsNone(partial_tape.mass)
        self.assertIsNone(partial_tape.cost)

    def test_bulk_properties_calculated_when_both_dimensions_set(self):
        """Test that bulk properties are calculated when both dimensions are set."""
        tape_material = TapeMaterial.from_database(name="Kapton")
        partial_tape = Tape(material=tape_material, thickness=25)
        
        # Initially no bulk properties
        self.assertIsNone(partial_tape.area)
        self.assertIsNone(partial_tape.mass)
        self.assertIsNone(partial_tape.cost)
        
        # Set one dimension - still no bulk properties
        partial_tape.length = 100
        self.assertIsNone(partial_tape.area)
        
        # Set second dimension - should calculate bulk properties
        partial_tape.width = 50
        self.assertIsNotNone(partial_tape.area)
        self.assertIsNotNone(partial_tape.mass)
        self.assertIsNotNone(partial_tape.cost)


if __name__ == '__main__':
    unittest.main()
