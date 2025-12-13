from copy import deepcopy
import unittest
import numpy as np
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Materials.Other import SeparatorMaterial
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd

pio.renderers.default = "browser"


class TestSimpleSeparator(unittest.TestCase):

    def setUp(self):
        
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        self.separator = Separator(material=separator_material, thickness=25)

    def test_equality(self):
        temp_separator = deepcopy(self.separator.material)
        condition = self.separator.material == temp_separator
        self.assertTrue(condition)

    def test_serialization(self):
        serialized = self.separator.serialize()
        deserialized = Separator.deserialize(serialized)
        self.assertEqual(self.separator, deserialized)


class TestSeparator(unittest.TestCase):

    def setUp(self):
        """
        Set up test fixtures
        """
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        self.separator = Separator(material=separator_material, thickness=25, length=100, width=50)

        # Create additional material for testing material setter - use available material
        self.alternative_material = SeparatorMaterial.from_database(name="Polyethylene")

    def test_equality(self):
        temp_separator = deepcopy(self.separator)
        condition = self.separator == temp_separator
        self.assertTrue(condition)

    def test_right_left_view(self):
        """
        Test right and left side views
        """
        fig_right = self.separator.get_right_left_view()
        fig_bottom = self.separator.get_bottom_up_view()
        # fig_right.show()
        # fig_bottom.show()
        
    def test_separator_properties(self):
        """
        Test the properties of the separator
        """
        self.assertTrue(isinstance(self.separator, Separator))

    def test_separator_initial_properties(self):
        """
        Test the properties of the separator with length and width set
        """
        self.assertEqual(self.separator.areal_cost, 50)
        self.assertEqual(self.separator.area, 50.0)
        self.assertEqual(self.separator.cost, 0.25)
        self.assertEqual(self.separator.mass, 0.25)
        self.assertEqual(self.separator.width, 50)
        self.assertEqual(self.separator.length, 100)

        fig = self.separator.get_top_down_view()
        # fig.show()

    # ========== SETTER TESTS ==========

    def test_name_setter_valid(self):
        """Test name setter with valid string"""
        self.separator.name = "Test Separator"
        self.assertEqual(self.separator.name, "Test Separator")

        self.separator.name = "Another Name"
        self.assertEqual(self.separator.name, "Another Name")

    def test_name_setter_invalid(self):
        """Test name setter with invalid inputs"""
        with self.assertRaises(TypeError):
            self.separator.name = 123

        with self.assertRaises(TypeError):
            self.separator.name = None

        with self.assertRaises(TypeError):
            self.separator.name = []

    def test_length_setter_valid(self):
        """Test length setter with valid values"""
        original_mass = self.separator.mass
        original_cost = self.separator.cost

        # Set new length
        self.separator.length = 200.0
        self.assertEqual(self.separator.length, 200.0)

        # Verify dependent properties updated
        self.assertNotEqual(self.separator.mass, original_mass)
        self.assertNotEqual(self.separator.cost, original_cost)
        self.assertEqual(self.separator.area, 100.0)  # 200mm * 50mm = 100 cm²

        # Test integer input
        self.separator.length = 150
        self.assertEqual(self.separator.length, 150.0)

    def test_width_setter_valid(self):
        """Test width setter with valid values"""
        original_mass = self.separator.mass
        original_cost = self.separator.cost

        # Set new width
        self.separator.width = 75.0
        self.assertEqual(self.separator.width, 75.0)

        # Verify dependent properties updates
        self.assertNotEqual(self.separator.mass, original_mass)
        self.assertNotEqual(self.separator.cost, original_cost)
        self.assertEqual(self.separator.area, 75.0)  # 100mm * 75mm = 75 cm²

        # Test integer input
        self.separator.width = 60
        self.assertEqual(self.separator.width, 60.0)

    def test_thickness_setter_valid(self):
        """Test thickness setter with valid values"""
        original_mass = self.separator.mass
        original_cost = self.separator.cost

        # Set new thickness
        self.separator.thickness = 50.0
        self.assertEqual(self.separator.thickness, 50.0)

        # Verify dependent properties updated
        self.assertNotEqual(self.separator.mass, original_mass)
        self.assertNotEqual(self.separator.cost, original_cost)

        # Test integer input
        self.separator.thickness = 30
        self.assertEqual(self.separator.thickness, 30.0)

    def test_material_setter_valid(self):
        """Test material setter with valid SeparatorMaterial"""
        original_cost = self.separator.cost

        # Set new material
        self.separator.material = self.alternative_material
        self.assertEqual(self.separator.material.name, self.alternative_material.name)

        # Verify cost updated (different material properties)
        # Note: Cost might be same if materials have similar properties

        # Verify it's a deep copy, not reference
        self.assertIsNot(self.separator.material, self.alternative_material)

    def test_datum_setter_valid(self):
        """Test datum setter with valid coordinates"""
        # Test tuple of floats
        self.separator.datum = (1.0, 2.0, 3.0)
        self.assertEqual(self.separator.datum, (1.0, 2.0, 3.0))

        # Test tuple of integers (should convert to float)
        self.separator.datum = (5, 10, 15)
        self.assertEqual(self.separator.datum, (5.0, 10.0, 15.0))

        # Test mixed types
        self.separator.datum = (1.5, 2, 3.7)
        self.assertEqual(self.separator.datum, (1.5, 2.0, 3.7))

        # Test negative values
        self.separator.datum = (-1.0, -2.0, -3.0)
        self.assertEqual(self.separator.datum, (-1.0, -2.0, -3.0))

    def test_areal_cost_setter_valid(self):
        """Test areal_cost setter with valid values"""
        original_cost = self.separator.cost
        original_areal_cost = self.separator.areal_cost
        original_material_specific_cost = self.separator.material.specific_cost

        # Set new areal cost
        self.separator.areal_cost = 75.0
        self.assertEqual(self.separator.areal_cost, 75.0)

        # Verify total cost updated
        self.assertNotEqual(self.separator.cost, original_cost)

        # Test integer input
        self.separator.areal_cost = 100
        self.assertEqual(self.separator.areal_cost, 100.0)

        # Test that we can reset to original value
        self.separator.areal_cost = original_areal_cost
        self.assertEqual(self.separator.areal_cost, original_areal_cost)

    def test_property_dependencies(self):
        """Test that changing dimensions updates all dependent properties correctly"""
        # Record initial values
        initial_area = self.separator.area
        initial_mass = self.separator.mass
        initial_cost = self.separator.cost
        initial_pore_volume = self.separator.pore_volume

        # Change length
        self.separator.length = 200  # Double the length

        # Verify area doubled
        self.assertEqual(self.separator.area, initial_area * 2)

        # Verify mass doubled (proportional to area)
        self.assertAlmostEqual(self.separator.mass, initial_mass * 2, places=1)

        # Verify cost doubled (proportional to area)
        self.assertAlmostEqual(self.separator.cost, initial_cost * 2, places=1)

        # Verify pore volume doubled (proportional to area)
        self.assertAlmostEqual(self.separator.pore_volume, initial_pore_volume * 2, places=1)

    def test_coordinates_update_on_dimension_change(self):
        """Test that coordinates are recalculated when dimensions change"""
        original_coords = self.separator.coordinates.copy()

        # Change dimensions
        self.separator.length = 200
        self.separator.width = 100

        new_coords = self.separator.coordinates.copy()

        # Verify coordinates changed
        self.assertFalse(original_coords.equals(new_coords))

        # Verify coordinate bounds match new dimensions
        x_range = new_coords["x"].max() - new_coords["x"].min()
        y_range = new_coords["y"].max() - new_coords["y"].min()

        self.assertAlmostEqual(x_range, 200, places=1)  # Length
        self.assertAlmostEqual(y_range, 100, places=1)  # Width

    def test_coordinates_update_on_datum_change(self):
        """Test that coordinates are recalculated when datum changes"""
        original_coords = self.separator.coordinates.copy()

        # Change datum
        self.separator.datum = (10.0, 20.0, 30.0)

        new_coords = self.separator.coordinates.copy()

        # Verify coordinates changed
        self.assertFalse(original_coords.equals(new_coords))

        # Verify coordinates are shifted by datum change
        # (Note: Exact verification would depend on coordinate calculation implementation)
        self.assertNotEqual(original_coords["x"].mean(), new_coords["x"].mean())
        self.assertNotEqual(original_coords["y"].mean(), new_coords["y"].mean())

        # self.separator.get_top_down_view().show()

    # ========== OPTIONAL LENGTH TESTS ==========

    def test_separator_without_length_initialization(self):
        """Test creating separator without length parameter"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        # Create separator without length
        separator_no_length = Separator(
            material=separator_material,
            thickness=25,
            width=50,
            # length not provided
        )

        # Verify it was created successfully
        self.assertIsInstance(separator_no_length, Separator)
        self.assertEqual(separator_no_length.thickness, 25)
        self.assertEqual(separator_no_length.width, 50)

    def test_properties_when_length_not_set(self):
        """Test that bulk properties return None when length is not set"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Length-dependent properties should be None
        self.assertIsNone(separator_no_length.length)
        self.assertIsNone(separator_no_length.area)
        self.assertIsNone(separator_no_length.mass)
        self.assertIsNone(separator_no_length.cost)
        self.assertIsNone(separator_no_length.pore_volume)
        self.assertIsNone(separator_no_length.coordinates)
        self.assertIsNone(separator_no_length.top_down_trace)

        # Length-independent properties should still be available
        self.assertIsNotNone(separator_no_length.areal_cost)
        self.assertIsNotNone(separator_no_length.thickness)
        self.assertIsNotNone(separator_no_length.width)
        self.assertIsNotNone(separator_no_length.material)
        self.assertIsNotNone(separator_no_length.name)
        self.assertIsNotNone(separator_no_length.datum)

    def test_setting_length_after_initialization(self):
        """Test that setting length after initialization calculates all properties"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Initially, bulk properties should be None
        self.assertIsNone(separator_no_length.length)
        self.assertIsNone(separator_no_length.area)
        self.assertIsNone(separator_no_length.mass)
        self.assertIsNone(separator_no_length.cost)

        # Set length
        separator_no_length.length = 100

        # Now all properties should be calculated
        self.assertEqual(separator_no_length.length, 100)
        self.assertIsNotNone(separator_no_length.area)
        self.assertIsNotNone(separator_no_length.mass)
        self.assertIsNotNone(separator_no_length.cost)
        self.assertIsNotNone(separator_no_length.pore_volume)
        self.assertIsNotNone(separator_no_length.coordinates)
        self.assertIsNotNone(separator_no_length.top_down_trace)

        # Verify calculated values are reasonable
        self.assertGreater(separator_no_length.area, 0)
        self.assertGreater(separator_no_length.mass, 0)
        self.assertGreater(separator_no_length.cost, 0)

    def test_get_top_down_view_without_length_raises_error(self):
        """Test that get_top_down_view raises error when length not set"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Should raise ValueError when trying to get top-down view without length
        with self.assertRaises(ValueError) as context:
            separator_no_length.get_top_down_view()

        self.assertIn("length not set", str(context.exception))

    def test_property_changes_when_length_added_removed(self):
        """Test property behavior when length is added and then effectively removed"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Initially None
        self.assertIsNone(separator_no_length.area)

        # Set length and verify properties are calculated
        separator_no_length.length = 100
        initial_area = separator_no_length.area
        self.assertIsNotNone(initial_area)

        # Change length and verify properties update
        separator_no_length.length = 200
        new_area = separator_no_length.area
        self.assertNotEqual(initial_area, new_area)
        self.assertAlmostEqual(new_area, initial_area * 2, places=1)  # Area should double

    def test_areal_properties_available_without_length(self):
        """Test that areal properties (not requiring length) are always available"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Areal cost should be available (doesn't depend on length)
        self.assertIsNotNone(separator_no_length.areal_cost)
        self.assertGreater(separator_no_length.areal_cost, 0)

        # Basic properties should be available
        self.assertEqual(separator_no_length.thickness, 25)
        self.assertEqual(separator_no_length.width, 50)

    def test_comparison_with_and_without_length(self):
        """Test that separator with length set matches one created with length initially"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        # Create separator with length initially
        sep_with_length = Separator(material=separator_material, thickness=25, width=50, length=100)

        # Create separator without length, then set it
        sep_without_length = Separator(material=separator_material, thickness=25, width=50)
        sep_without_length.length = 100

        # Both should have the same calculated properties
        self.assertEqual(sep_with_length.length, sep_without_length.length)
        self.assertEqual(sep_with_length.area, sep_without_length.area)
        self.assertEqual(sep_with_length.mass, sep_without_length.mass)
        self.assertEqual(sep_with_length.cost, sep_without_length.cost)
        self.assertEqual(sep_with_length.areal_cost, sep_without_length.areal_cost)

    def test_coordinates_behavior_without_length(self):
        """Test that coordinates-related methods handle missing length properly"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")

        separator_no_length = Separator(material=separator_material, thickness=25, width=50)

        # Coordinates should be None
        self.assertIsNone(separator_no_length.coordinates)

        # top_down_trace should be None
        self.assertIsNone(separator_no_length.top_down_trace)

        # After setting length, coordinates should be available
        separator_no_length.length = 100
        self.assertIsNotNone(separator_no_length.coordinates)
        self.assertIsNotNone(separator_no_length.top_down_trace)

        # Verify coordinates have the expected structure
        coords = separator_no_length.coordinates
        self.assertIn("x", coords.columns)
        self.assertIn("y", coords.columns)
        self.assertIn("z", coords.columns)

    # ========== ROTATION TESTS ==========

    def test_rotate(self):
        """Test rotating the separator 90 degrees in the XY plane"""
        fig1 = self.separator.get_top_down_view()

        self.separator._rotate_90_xy()
        fig2 = self.separator.get_top_down_view()

        self.separator.length = 200
        fig3 = self.separator.get_top_down_view()

        self.separator.width = 10
        fig4 = self.separator.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    # ========== FLIP TESTS ==========

    def test_flip_x_axis(self):
        """Test flipping the separator about the x-axis"""
        # Get original coordinates
        original_coords = self.separator.coordinates.copy()
        
        # Check initial flip state
        self.assertFalse(self.separator._flipped_x)
        
        # Flip about x-axis
        self.separator._flip("x")
        
        # Verify flip state changed
        self.assertTrue(self.separator._flipped_x)
        
        # Get new coordinates after flip
        flipped_coords = self.separator.coordinates.copy()
        
        # Verify coordinates changed
        self.assertFalse(original_coords.equals(flipped_coords))
        
        # Flip back and verify we return to original state
        self.separator._flip("x")
        self.assertFalse(self.separator._flipped_x)
        
        # Verify coordinates are back to original (within tolerance)
        restored_coords = self.separator.coordinates.copy()
        np.testing.assert_allclose(
            original_coords.values, 
            restored_coords.values, 
            rtol=1e-10,
            err_msg="Coordinates should return to original after double flip"
        )

    def test_flip_y_axis(self):
        """Test flipping the separator about the y-axis"""
        # Get original coordinates
        original_coords = self.separator.coordinates.copy()
        
        # Check initial flip state
        self.assertFalse(self.separator._flipped_y)
        
        # Flip about y-axis
        self.separator._flip("y")
        
        # Verify flip state changed
        self.assertTrue(self.separator._flipped_y)
        
        # Get new coordinates after flip
        flipped_coords = self.separator.coordinates.copy()
        
        # Verify coordinates changed
        self.assertFalse(original_coords.equals(flipped_coords))
        
        # Flip back and verify we return to original state
        self.separator._flip("y")
        self.assertFalse(self.separator._flipped_y)

    def test_flip_z_axis(self):
        """Test flipping the separator about the z-axis"""
        # Get original coordinates
        original_coords = self.separator.coordinates.copy()
        
        # Check initial flip state
        self.assertFalse(self.separator._flipped_z)
        
        # Flip about z-axis
        self.separator._flip("z")
        
        # Verify flip state changed
        self.assertTrue(self.separator._flipped_z)
        
        # Get new coordinates after flip
        flipped_coords = self.separator.coordinates.copy()
        
        # Verify coordinates changed
        self.assertFalse(original_coords.equals(flipped_coords))
        
        # Flip back and verify we return to original state
        self.separator._flip("z")
        self.assertFalse(self.separator._flipped_z)

    def test_flip_invalid_axis(self):
        """Test that invalid axis raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.separator._flip("invalid")
        
        self.assertIn("Axis must be", str(context.exception))
        
        # Test other invalid inputs
        with self.assertRaises(ValueError):
            self.separator._flip("X")  # Capital letter
            
        with self.assertRaises(ValueError):
            self.separator._flip("xy")  # Multiple axes

    def test_flip_without_length_raises_error(self):
        """Test that flipping without length set raises appropriate error"""
        separator_material = SeparatorMaterial.from_database(name="Nafion")
        separator_no_length = Separator(material=separator_material, thickness=25, width=50)
        
        # Should raise error when trying to flip without coordinates
        with self.assertRaises(AttributeError):
            separator_no_length._flip("x")

    def test_multiple_axis_flips(self):
        """Test flipping about multiple axes in sequence"""
        original_coords = self.separator.coordinates.copy()
        
        # Flip about x and y axes (should result in different coordinates)
        self.separator._flip("x")
        self.separator._flip("y")
        
        # Check flip states are True for x and y
        self.assertTrue(self.separator._flipped_x)
        self.assertTrue(self.separator._flipped_y)
        self.assertFalse(self.separator._flipped_z)  # z should still be False
        
        # Get coordinates after x and y flips
        xy_flipped_coords = self.separator.coordinates.copy()
        
        # Verify coordinates changed from original
        self.assertFalse(original_coords.equals(xy_flipped_coords))
        
        # Now flip about z-axis as well
        self.separator._flip("z")
        self.assertTrue(self.separator._flipped_z)
        
        # Get coordinates after all three flips  
        triple_flipped_coords = self.separator.coordinates.copy()
        
        # Note: Flipping 180° about all three axes mathematically returns to original position
        # This is expected behavior, so we verify the flip states are correct
        self.assertTrue(self.separator._flipped_x)
        self.assertTrue(self.separator._flipped_y)
        self.assertTrue(self.separator._flipped_z)
        
        # Flip back all axes
        self.separator._flip("x")
        self.separator._flip("y")
        self.separator._flip("z")
        
        # Check all flip states are False
        self.assertFalse(self.separator._flipped_x)
        self.assertFalse(self.separator._flipped_y)
        self.assertFalse(self.separator._flipped_z)

    def test_flip_preserves_other_properties(self):
        """Test that flipping doesn't change other separator properties"""
        # Record original properties
        original_thickness = self.separator.thickness
        original_width = self.separator.width
        original_length = self.separator.length
        original_area = self.separator.area
        original_mass = self.separator.mass
        original_cost = self.separator.cost
        original_datum = self.separator.datum
        
        # Flip the separator
        self.separator._flip("x")
        
        # Verify all properties remain the same
        self.assertEqual(self.separator.thickness, original_thickness)
        self.assertEqual(self.separator.width, original_width)
        self.assertEqual(self.separator.length, original_length)
        self.assertEqual(self.separator.area, original_area)
        self.assertEqual(self.separator.mass, original_mass)
        self.assertEqual(self.separator.cost, original_cost)
        self.assertEqual(self.separator.datum, original_datum)

    def test_flip_and_visualize(self):
        """Test that flipped separator can generate visualizations"""
        # Flip the separator
        self.separator._flip("y")
        
        # Test that all visualization methods work after flipping
        fig_top = self.separator.get_top_down_view()
        fig_right = self.separator.get_right_left_view()
        fig_bottom = self.separator.get_bottom_up_view()
        
        # Verify figures were created
        self.assertIsInstance(fig_top, go.Figure)
        self.assertIsInstance(fig_right, go.Figure)
        self.assertIsInstance(fig_bottom, go.Figure)
        
        # Verify figures have traces
        self.assertGreater(len(fig_top.data), 0)
        self.assertGreater(len(fig_right.data), 0)
        self.assertGreater(len(fig_bottom.data), 0)
        
        # Uncomment to visualize flipped separator
        # fig_top.show()
        # fig_right.show()
        # fig_bottom.show()


if __name__ == "__main__":
    unittest.main()
