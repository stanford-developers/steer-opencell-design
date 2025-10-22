import unittest
from copy import deepcopy
import numpy as np

from steer_opencell_design.AuxillaryComponents.WindingEquipment import RoundMandrel, FlatMandrel


class TestMandrel(unittest.TestCase):
    """Tests for the Mandrel class."""

    def setUp(self):
        """Set up a basic mandrel for testing."""
        self.mandrel = RoundMandrel(
            diameter=10.0,  # 10mm diameter
            length=100.0,   # 100mm length
            datum=(0.0, 0.0, 0.0)  # centered at origin
        )

    def test_mandrel_instantiation(self):
        """Test basic mandrel instantiation and properties."""
        self.assertIsInstance(self.mandrel, RoundMandrel)
        self.assertEqual(self.mandrel.diameter, 10.0)
        self.assertEqual(self.mandrel.length, 100.0)
        self.assertEqual(self.mandrel.datum, (0.0, 0.0, 0.0))

        fig1 = self.mandrel.get_top_down_view()
        fig2 = self.mandrel.get_bottom_up_view()

        # fig1.show()
        # fig2.show()

    def test_mandrel_coordinates_generation(self):
        """Test that coordinates are properly generated."""
        # Coordinates should be generated automatically during instantiation
        self.assertTrue(hasattr(self.mandrel, '_coordinates'))
        self.assertIsNotNone(self.mandrel._coordinates)
        
        # Check that coordinates array has the right shape (N points, 3 dimensions)
        coords = self.mandrel._coordinates
        self.assertEqual(coords.shape[1], 3)  # 3 columns (x, y, z)
        self.assertGreater(coords.shape[0], 0)  # At least some points

    def test_mandrel_coordinate_ranges(self):
        """Test that coordinates are within expected ranges."""
        coords = self.mandrel._coordinates
        
        # Y coordinates should span the length of the mandrel (±50mm from center)
        y_coords = coords[:, 1]
        self.assertGreaterEqual(y_coords.min(), -0.05)  # -50mm in meters
        self.assertLessEqual(y_coords.max(), 0.05)      # +50mm in meters
        
        # X and Z coordinates should be bounded by the radius (5mm)
        x_coords = coords[:, 0]
        z_coords = coords[:, 2]
        radius = 0.005  # 5mm in meters
        
        # All points should be on the circular surface (no center points)
        max_radial_distance = (x_coords**2 + z_coords**2)**0.5
        self.assertLessEqual(max_radial_distance.max(), radius + 1e-10)  # Allow small numerical error
        
        # Check that we have exactly 66 points (33 per circle, with closed circles)
        self.assertEqual(coords.shape[0], 66)

    def test_mandrel_property_updates(self):
        """Test that changing properties updates coordinates."""
        # Change diameter and check that coordinates are recalculated
        original_coords = self.mandrel._coordinates.copy()
        
        self.mandrel.diameter = 20.0  # Double the diameter
        new_coords = self.mandrel._coordinates
        
        # Coordinates should have changed
        self.assertFalse((original_coords == new_coords).all())
        
        # New coordinates should reflect the larger diameter
        x_coords = new_coords[:, 0]
        z_coords = new_coords[:, 2]
        max_radial_distance = (x_coords**2 + z_coords**2)**0.5
        new_radius = 0.01  # 10mm in meters
        self.assertLessEqual(max_radial_distance.max(), new_radius + 1e-10)

    def test_mandrel_coordinates_property(self):
        """Test the coordinates property returns proper DataFrame in mm."""
        coords_df = self.mandrel.coordinates
        
        # Should be a pandas DataFrame
        import pandas as pd
        self.assertIsInstance(coords_df, pd.DataFrame)
        
        # Should have correct columns
        expected_columns = ["x", "y", "z"]
        self.assertListEqual(list(coords_df.columns), expected_columns)
        
        # Should have some points
        self.assertGreater(len(coords_df), 0)
        
        # All values should be numeric
        self.assertTrue(coords_df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all())
        
        # Coordinates should be in mm (larger values than internal meters)
        # Y coordinates should span the length (±50mm from center)
        y_range = coords_df['y'].max() - coords_df['y'].min()
        self.assertAlmostEqual(y_range, 100.0, delta=1.0)  # 100mm length
        
        # X and Z coordinates should be bounded by radius (5mm)
        max_radial_distance = (coords_df['x']**2 + coords_df['z']**2)**0.5
        self.assertLessEqual(max_radial_distance.max(), 5.1)  # 5mm radius + small tolerance
        
        # Should have exactly 66 points total (33 per circle)
        self.assertEqual(len(coords_df), 66)
        
        # Check that values are properly rounded (should have reasonable precision)
        # No excessive decimal places for display
        max_decimal_places = coords_df.apply(
            lambda col: col.apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0).max()
        ).max()
        self.assertLessEqual(max_decimal_places, 10)  # Should be reasonably rounded


class TestFlatMandrel(unittest.TestCase):
    """Tests for the FlatMandrel class."""

    def setUp(self):
        """Set up a basic flat mandrel for testing."""
        self.flat_mandrel = FlatMandrel(
            long_diameter=20.0,   # 20mm long diameter
            short_diameter=1.0,  # 10mm short diameter
            length=100.0,         # 100mm length
            datum=(0.0, 0.0, 0.0) # centered at origin
        )

    def test_flat_mandrel_instantiation(self):
        """Test basic flat mandrel instantiation and properties."""
        self.assertIsInstance(self.flat_mandrel, FlatMandrel)
        self.assertEqual(self.flat_mandrel.long_diameter, 20.0)
        self.assertEqual(self.flat_mandrel.short_diameter, 1.0)
        self.assertEqual(self.flat_mandrel.length, 100.0)
        self.assertEqual(self.flat_mandrel.datum, (0.0, 0.0, 0.0))

    def test_flat_mandrel_views(self):
        """Test that flat mandrel can generate views."""
        fig1 = self.flat_mandrel.get_top_down_view()
        fig2 = self.flat_mandrel.get_bottom_up_view()
        
        # Check that figures are created
        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)

        # fig1.show()
        # fig2.show()

    def test_flat_mandrel_coordinates_generation(self):
        """Test that coordinates are properly generated for elliptical shape."""
        # Coordinates should be generated automatically during instantiation
        self.assertTrue(hasattr(self.flat_mandrel, '_coordinates'))
        self.assertIsNotNone(self.flat_mandrel._coordinates)
        
        # Check that coordinates array has the right shape (N points, 3 dimensions)
        coords = self.flat_mandrel._coordinates
        self.assertEqual(coords.shape[1], 3)  # 3 columns (x, y, z)
        self.assertGreater(coords.shape[0], 0)  # At least some points

    def test_flat_mandrel_elliptical_coordinates(self):
        """Test that coordinates form proper elliptical shape."""
        coords = self.flat_mandrel._coordinates
        
        # Y coordinates should span the length of the mandrel (±50mm from center)
        y_coords = coords[:, 1]
        self.assertGreaterEqual(y_coords.min(), -0.05)  # -50mm in meters
        self.assertLessEqual(y_coords.max(), 0.05)      # +50mm in meters
        
        # X coordinates should be bounded by semi-major axis (10mm)
        x_coords = coords[:, 0]
        self.assertLessEqual(np.abs(x_coords).max(), 0.0101)  # 10mm + tolerance in meters
        
        # Z coordinates should be bounded by semi-minor axis (5mm)
        z_coords = coords[:, 2]
        self.assertLessEqual(np.abs(z_coords).max(), 0.0051)  # 5mm + tolerance in meters

    def test_flat_mandrel_property_updates(self):
        """Test that updating properties recalculates coordinates."""
        # Get initial coordinates
        initial_coords = self.flat_mandrel._coordinates.copy()
        
        # Change long diameter
        self.flat_mandrel.long_diameter = 30.0
        new_coords = self.flat_mandrel._coordinates
        
        # Coordinates should have changed
        self.assertFalse(np.array_equal(initial_coords, new_coords))
        
        # New coordinates should reflect updated long diameter
        x_coords = new_coords[:, 0]
        self.assertLessEqual(np.abs(x_coords).max(), 0.0151)  # 15mm + tolerance in meters

    def test_flat_mandrel_coordinates_property(self):
        """Test the coordinates property returns proper DataFrame."""
        import pandas as pd
        
        coords_df = self.flat_mandrel.coordinates
        
        # Should be a DataFrame
        self.assertIsInstance(coords_df, pd.DataFrame)
        
        # Should have correct columns
        expected_columns = ["x", "y", "z"]
        self.assertListEqual(list(coords_df.columns), expected_columns)
        
        # Should have some points
        self.assertGreater(len(coords_df), 0)
        
        # All values should be numeric
        self.assertTrue(coords_df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all())
        
        # Y coordinates should span the length (±50mm from center)
        y_range = coords_df['y'].max() - coords_df['y'].min()
        self.assertAlmostEqual(y_range, 100.0, delta=1.0)  # 100mm length
        
        # Should have exactly 66 points total (33 per ellipse)
        self.assertEqual(len(coords_df), 258)

    def test_flat_mandrel_setters(self):
        """Test property setters work correctly."""
        # Test long_diameter setter
        self.flat_mandrel.long_diameter = 25.0
        self.assertEqual(self.flat_mandrel.long_diameter, 25.0)
        
        # Test short_diameter setter
        self.flat_mandrel.short_diameter = 12.0
        self.assertEqual(self.flat_mandrel.short_diameter, 12.0)
        
        # Test length setter
        self.flat_mandrel.length = 150.0
        self.assertEqual(self.flat_mandrel.length, 150.0)
        
        # Test datum setter
        new_datum = (5.0, 10.0, 15.0)
        self.flat_mandrel.datum = new_datum
        self.assertEqual(self.flat_mandrel.datum, new_datum)


if __name__ == "__main__":
    unittest.main()
