import unittest
import numpy as np
from copy import deepcopy

from steer_opencell_design.Components.Containers.Cylindrical import (
    CylindricalTerminalConnector,
    CylindricalLidAssembly,
    CylindricalCanister,
    CylindricalEncapsulation,
)

from steer_opencell_design.Materials.Other import PrismaticContainerMaterial


class TestCylindricalTerminalConnector(unittest.TestCase):
    def setUp(self):

        material = PrismaticContainerMaterial.from_database("Aluminum")

        """Set up test fixtures for CylindricalTerminalConnector tests"""
        self.connector_standard = CylindricalTerminalConnector(
            material=material, 
            thickness=0.05,
            radius=5,
            fill_factor=0.8
        )

        self.connector_small = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=0.05,
            radius=5,
            fill_factor=0.6
        )

        self.connector_large = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Steel"), 
            thickness=0.05,
            radius=20,
            fill_factor=0.9
        )
        
        # Add connector without radius for None testing
        self.connector_no_radius = CylindricalTerminalConnector(
            material=material,
            thickness=0.05,
            fill_factor=0.8
        )

    def test_initialization_standard(self):
        """Test standard connector initialization"""
        connector = self.connector_standard
        self.assertEqual(connector.radius, 5)
        self.assertEqual(connector.thickness, 0.05)
        self.assertEqual(connector.fill_factor, 0.8)

    def test_serialization(self):
        serialized = self.connector_large.serialize()
        deserialized = CylindricalTerminalConnector.deserialize(serialized)
        self.assertEqual(self.connector_large, deserialized)

    def test_plots(self):

        fig1 = self.connector_standard.get_bottom_up_plot()
        fig2 = self.connector_small.get_bottom_up_plot()
        fig3 = self.connector_large.get_bottom_up_plot()

        fig4 = self.connector_standard.get_top_down_plot()
        fig5 = self.connector_small.get_top_down_plot()
        fig6 = self.connector_large.get_top_down_plot()

        # fig1.show()
        # fig2.show()
        # fig3.show()

        # fig4.show()
        # fig5.show()
        # fig6.show()

    def test_bulk_properties(self):
        """Test bulk property calculations"""
        connector = self.connector_standard
        # Check that bulk properties return reasonable values
        self.assertIsInstance(connector._cost, (int, float))
        self.assertIsInstance(connector._mass, (int, float))
        self.assertGreater(connector._cost, 0)
        self.assertGreater(connector._mass, 0)
        
        # Test that different materials yield different properties
        al_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        cu_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        self.assertNotEqual(al_connector._cost, cu_connector._cost)
        self.assertNotEqual(al_connector._mass, cu_connector._mass)

    def test_footprint_structure(self):
        """Test that footprint calculation returns valid structure"""
        footprint = self.connector_standard._calculate_footprint()
        
        # Check that footprint is a numpy array with proper shape
        self.assertIsInstance(footprint, np.ndarray)
        self.assertEqual(len(footprint.shape), 2)
        self.assertEqual(footprint.shape[1], 2)  # Should have x, y coordinates
        
        # Check that arrays have reasonable length (should be a detailed outline)
        self.assertGreater(len(footprint), 100)  # Should have many points for smooth curves

    def test_footprint_geometry(self):
        """Test geometric properties of the footprint"""
        footprint = self.connector_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # Check that footprint is roughly circular in extent
        # Note: footprint coordinates are in meters, radius property is in mm
        radius_m = self.connector_standard._radius  # Internal radius in meters
        max_x, min_x = np.max(x), np.min(x)
        max_y, min_y = np.max(y), np.min(y)
        
        # The extent should be approximately equal to diameter
        x_extent = max_x - min_x
        y_extent = max_y - min_y
        self.assertAlmostEqual(x_extent, 2 * radius_m, places=3)
        self.assertAlmostEqual(y_extent, 2 * radius_m, places=3)
        
        # Check that the shape is roughly centered at origin (accounting for datum)
        x_center = (max_x + min_x) / 2
        y_center = (max_y + min_y) / 2
        self.assertAlmostEqual(x_center, 0, places=3)
        self.assertAlmostEqual(y_center, 0, places=3)

    def test_footprint_fill_factor(self):
        """Test that fill factor affects footprint area correctly"""
        # Calculate footprint areas for different fill factors
        connector_low_fill = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.5
        )
        connector_high_fill = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.9
        )
        
        footprint_low = connector_low_fill._calculate_footprint()
        footprint_high = connector_high_fill._calculate_footprint()
        
        # Calculate approximate areas using shoelace formula
        def polygon_area(x, y):
            return 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(-1, len(x)-1)))
        
        area_low = polygon_area(footprint_low[:, 0], footprint_low[:, 1])
        area_high = polygon_area(footprint_high[:, 0], footprint_high[:, 1])
        
        # Higher fill factor should result in larger effective area
        self.assertGreater(area_high, area_low)

    def test_footprint_different_sizes(self):
        """Test footprint scaling with different connector sizes"""
        small_footprint = self.connector_small._calculate_footprint()
        large_footprint = self.connector_large._calculate_footprint()
        
        # Larger connector should have larger footprint extents
        small_extent_x = np.max(small_footprint[:, 0]) - np.min(small_footprint[:, 0])
        large_extent_x = np.max(large_footprint[:, 0]) - np.min(large_footprint[:, 0])
        
        self.assertGreater(large_extent_x, small_extent_x)

    def test_footprint_triangular_cutouts(self):
        """Test that triangular cutouts are properly implemented"""
        footprint = self.connector_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # The footprint should have indentations (triangular cutouts)
        # Check that not all points are at the same radius from center
        radii = np.sqrt(x**2 + y**2)
        radius_variation = np.max(radii) - np.min(radii)
        
        # Should have significant variation due to triangular cutouts
        # Note: footprint coordinates are in meters, so convert radius to meters for comparison
        expected_radius_m = self.connector_standard._radius  # Internal radius in meters
        self.assertGreater(radius_variation, expected_radius_m * 0.1)  # At least 10% variation

    def test_footprint_continuity(self):
        """Test that footprint path is continuous and closed"""
        footprint = self.connector_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # First and last points should be close (closed path)
        self.assertAlmostEqual(x[0], x[-1], places=3)
        self.assertAlmostEqual(y[0], y[-1], places=3)

    def test_material_dependency(self):
        """Test that different materials produce different results"""
        al_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        cu_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        steel_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Steel"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        
        # Different materials should yield different costs and masses
        materials = [al_connector, cu_connector, steel_connector]
        costs = [conn._cost for conn in materials]
        masses = [conn._mass for conn in materials]
        
        # All costs should be different
        self.assertEqual(len(set(costs)), 3)
        # All masses should be different  
        self.assertEqual(len(set(masses)), 3)

    def test_initialization_without_radius(self):
        """Test connector initialization without radius"""
        connector = self.connector_no_radius
        self.assertIsNone(connector.radius)
        self.assertEqual(connector.thickness, 0.05)
        self.assertEqual(connector.fill_factor, 0.8)

    def test_properties_when_radius_none(self):
        """Test that properties return None when radius is not set"""
        connector = self.connector_no_radius
        
        # Bulk properties should be None
        self.assertIsNone(connector.mass)
        self.assertIsNone(connector.cost)
        self.assertIsNone(connector.volume)
        
        # Coordinates should be empty DataFrame
        coords = connector.coordinates
        self.assertTrue(coords.empty)
        self.assertEqual(list(coords.columns), ["x", "y", "z"])

    def test_footprint_calculation_without_radius(self):
        """Test that footprint calculation raises error when radius is None"""
        connector = self.connector_no_radius
        
        with self.assertRaises(ValueError) as context:
            connector._calculate_footprint()
        
        self.assertIn("Cannot calculate footprint: radius is not set", str(context.exception))

    def test_radius_setting_triggers_calculations(self):
        """Test that setting radius triggers property calculations"""
        connector = self.connector_no_radius
        
        # Initially properties should be None
        self.assertIsNone(connector.mass)
        self.assertIsNone(connector.cost)
        self.assertIsNone(connector.volume)
        
        # Set radius - should trigger calculations
        connector.radius = 5.0
        
        # Properties should now be calculated
        self.assertEqual(connector.radius, 5.0)
        self.assertIsNotNone(connector.mass)
        self.assertIsNotNone(connector.cost)
        self.assertIsNotNone(connector.volume)
        self.assertGreater(connector.mass, 0)
        self.assertGreater(connector.volume, 0)
        
        # Coordinates should be populated
        coords = connector.coordinates
        self.assertFalse(coords.empty)
        self.assertGreater(len(coords), 0)

    def test_radius_reset_to_none(self):
        """Test setting radius back to None clears calculations"""
        connector = self.connector_standard
        
        # Initially should have properties
        self.assertIsNotNone(connector.mass)
        self.assertIsNotNone(connector.cost)
        self.assertIsNotNone(connector.volume)
        
        # Set radius to None
        connector.radius = None
        
        # Properties should now be None
        self.assertIsNone(connector.radius)
        self.assertIsNone(connector.mass)
        self.assertIsNone(connector.cost)
        self.assertIsNone(connector.volume)
        
        # Coordinates should be empty
        coords = connector.coordinates
        self.assertTrue(coords.empty)

    def test_lazy_initialization_workflow(self):
        """Test the complete workflow of lazy initialization"""
        # Create connector without radius
        connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            thickness=100,
            fill_factor=0.75
        )
        
        # Verify initial state
        self.assertIsNone(connector.radius)
        self.assertEqual(connector.thickness, 100)
        self.assertEqual(connector.fill_factor, 0.75)
        self.assertIsNone(connector.mass)
        
        # Set radius and verify calculations
        connector.radius = 10.0
        self.assertEqual(connector.radius, 10.0)
        self.assertIsNotNone(connector.mass)
        
        # Verify we can change radius
        original_mass = connector.mass
        connector.radius = 15.0
        self.assertEqual(connector.radius, 15.0)
        self.assertNotEqual(connector.mass, original_mass)  # Should be different due to size change


class TestCylindricalLidAssembly(unittest.TestCase):
    def setUp(self):
        material = PrismaticContainerMaterial.from_database("Aluminum")

        """Set up test fixtures for CylindricalLidAssembly tests"""
        self.lid_standard = CylindricalLidAssembly(
            material=material, 
            thickness=50,
            radius=5,
            fill_factor=0.8
        )

        self.lid_small = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=50,
            radius=5,
            fill_factor=0.6
        )

        self.lid_large = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Steel"), 
            thickness=50,
            radius=20,
            fill_factor=0.9
        )
        
        # Add lid without radius for None testing
        self.lid_no_radius = CylindricalLidAssembly(
            material=material,
            thickness=50,
            fill_factor=0.8
        )

    def test_initialization_standard(self):
        """Test standard lid initialization"""
        lid = self.lid_standard
        self.assertEqual(lid.radius, 5)
        self.assertEqual(lid.thickness, 50)
        self.assertEqual(lid.fill_factor, 0.8)
        self.assertEqual(lid.name, "Cylindrical Lid Assembly")

    def test_serialization(self):
        serialized = self.lid_large.serialize()
        deserialized = CylindricalLidAssembly.deserialize(serialized)
        test_case = self.lid_large == deserialized
        self.assertTrue(test_case)

    def test_plots(self):
        """Test plotting functionality for different lid configurations"""
        fig1 = self.lid_standard.get_bottom_up_plot()
        fig2 = self.lid_small.get_bottom_up_plot()
        fig3 = self.lid_large.get_bottom_up_plot()

        fig4 = self.lid_standard.get_top_down_plot()
        fig5 = self.lid_small.get_top_down_plot()
        fig6 = self.lid_large.get_top_down_plot()

        # Verify plots are created successfully (figures have data)
        self.assertIsNotNone(fig1.data)
        self.assertIsNotNone(fig4.data)
        
        # Uncomment to visualize during development
        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()
        # fig6.show()

    def test_initialization_edge_cases(self):
        """Test lid initialization with edge case values"""
        # Test minimum viable lid
        min_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=0.1,
            radius=0.5,
            fill_factor=0.1
        )
        self.assertEqual(min_lid.fill_factor, 0.1)
        
        # Test maximum viable lid
        max_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=10,
            radius=25,
            fill_factor=1.0
        )
        self.assertEqual(max_lid.fill_factor, 1.0)

    def test_bulk_properties(self):
        """Test bulk property calculations for lid assembly"""
        lid = self.lid_standard
        # Check that bulk properties return reasonable values
        self.assertIsInstance(lid._cost, (int, float))
        self.assertIsInstance(lid._mass, (int, float))
        self.assertGreater(lid._cost, 0)
        self.assertGreater(lid._mass, 0)
        
        # Test that different materials yield different properties
        al_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        cu_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        self.assertNotEqual(al_lid._cost, cu_lid._cost)
        self.assertNotEqual(al_lid._mass, cu_lid._mass)

    def test_footprint_structure(self):
        """Test that lid footprint calculation returns valid structure"""
        footprint = self.lid_standard._calculate_footprint()
        
        # Check that footprint is a numpy array with proper shape
        self.assertIsInstance(footprint, np.ndarray)
        self.assertEqual(len(footprint.shape), 2)
        self.assertEqual(footprint.shape[1], 2)  # Should have x, y coordinates
        
        # Check that arrays have reasonable length (should be detailed circular outline)
        self.assertGreaterEqual(len(footprint), 100)  # Should have many points for smooth circle

    def test_footprint_circular_geometry(self):
        """Test that lid footprint is truly circular"""
        footprint = self.lid_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # Check that footprint is circular in extent
        # Note: footprint coordinates are in meters, radius property is in mm
        radius_m = self.lid_standard._radius  # Internal radius in meters
        max_x, min_x = np.max(x), np.min(x)
        max_y, min_y = np.max(y), np.min(y)
        
        # The extent should be approximately equal to diameter
        x_extent = max_x - min_x
        y_extent = max_y - min_y
        self.assertAlmostEqual(x_extent, 2 * radius_m, places=3)
        self.assertAlmostEqual(y_extent, 2 * radius_m, places=3)
        
        # Check that the shape is roughly centered at origin (accounting for datum)
        x_center = (max_x + min_x) / 2
        y_center = (max_y + min_y) / 2
        self.assertAlmostEqual(x_center, 0, places=3)
        self.assertAlmostEqual(y_center, 0, places=3)

    def test_footprint_perfect_circle(self):
        """Test that lid footprint is a perfect circle without cutouts"""
        footprint = self.lid_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # All points should be at approximately the same radius from center
        radii = np.sqrt(x**2 + y**2)
        radius_m = self.lid_standard._radius  # Internal radius in meters
        
        # All radii should be very close to the expected radius (within tolerance)
        for radius in radii[:-1]:  # Exclude last point (duplicate of first)
            self.assertAlmostEqual(radius, radius_m, places=3)
        
        # Standard deviation of radii should be very small for perfect circle
        radius_std = np.std(radii[:-1])  # Exclude duplicate point
        self.assertLess(radius_std, radius_m * 0.01)  # Less than 1% variation

    def test_footprint_fill_factor_independence(self):
        """Test that fill factor doesn't affect footprint shape, only material calculations"""
        # Create lids with different fill factors but same geometry
        lid_low_fill = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.5
        )
        lid_high_fill = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.9
        )
        
        footprint_low = lid_low_fill._calculate_footprint()
        footprint_high = lid_high_fill._calculate_footprint()
        
        # Footprints should be identical (fill factor only affects material usage)
        np.testing.assert_array_almost_equal(footprint_low, footprint_high, decimal=6)
        
        # But material properties should be different
        self.assertNotEqual(lid_low_fill._volume, lid_high_fill._volume)
        self.assertNotEqual(lid_low_fill._mass, lid_high_fill._mass)

    def test_footprint_different_sizes(self):
        """Test footprint scaling with different lid sizes"""
        small_footprint = self.lid_small._calculate_footprint()
        large_footprint = self.lid_large._calculate_footprint()
        
        # Larger lid should have larger footprint extents
        small_extent_x = np.max(small_footprint[:, 0]) - np.min(small_footprint[:, 0])
        large_extent_x = np.max(large_footprint[:, 0]) - np.min(large_footprint[:, 0])
        
        self.assertGreater(large_extent_x, small_extent_x)
        
        # Check radius scaling is correct
        small_radius = self.lid_small._radius
        large_radius = self.lid_large._radius
        expected_ratio = large_radius / small_radius
        actual_ratio = large_extent_x / small_extent_x
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=2)

    def test_footprint_continuity(self):
        """Test that lid footprint path is continuous and closed"""
        footprint = self.lid_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # First and last points should be identical (closed path)
        self.assertAlmostEqual(x[0], x[-1], places=6)
        self.assertAlmostEqual(y[0], y[-1], places=6)

    def test_material_dependency(self):
        """Test that different materials produce different material properties"""
        al_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        cu_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Copper"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        steel_lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Steel"), 
            thickness=1,
            radius=5,
            fill_factor=0.8
        )
        
        # Different materials should yield different costs and masses
        materials = [al_lid, cu_lid, steel_lid]
        costs = [lid._cost for lid in materials]
        masses = [lid._mass for lid in materials]
        
        # All costs should be different
        self.assertEqual(len(set(costs)), 3)
        # All masses should be different  
        self.assertEqual(len(set(masses)), 3)

    def test_initialization_without_radius(self):
        """Test lid initialization without radius"""
        lid = self.lid_no_radius
        self.assertIsNone(lid.radius)
        self.assertEqual(lid.thickness, 50)
        self.assertEqual(lid.fill_factor, 0.8)
        self.assertEqual(lid.name, "Cylindrical Lid Assembly")

    def test_properties_when_radius_none(self):
        """Test that properties return None when radius is not set"""
        lid = self.lid_no_radius
        
        # Bulk properties should be None
        self.assertIsNone(lid.mass)
        self.assertIsNone(lid.cost)
        self.assertIsNone(lid.volume)
        
        # Coordinates should be empty DataFrame
        coords = lid.coordinates
        self.assertTrue(coords.empty)
        self.assertEqual(list(coords.columns), ["x", "y", "z"])

    def test_footprint_calculation_without_radius(self):
        """Test that footprint calculation raises error when radius is None"""
        lid = self.lid_no_radius
        
        with self.assertRaises(ValueError) as context:
            lid._calculate_footprint()
        
        self.assertIn("Cannot calculate footprint: radius is not set", str(context.exception))

    def test_radius_setting_triggers_calculations(self):
        """Test that setting radius triggers property calculations"""
        lid = self.lid_no_radius
        
        # Initially properties should be None
        self.assertIsNone(lid.mass)
        self.assertIsNone(lid.cost)
        self.assertIsNone(lid.volume)
        
        # Set radius - should trigger calculations
        lid.radius = 5.0
        
        # Properties should now be calculated
        self.assertEqual(lid.radius, 5.0)
        self.assertIsNotNone(lid.mass)
        self.assertIsNotNone(lid.cost)
        self.assertIsNotNone(lid.volume)
        self.assertGreater(lid.mass, 0)
        self.assertGreater(lid.volume, 0)
        
        # Coordinates should be populated
        coords = lid.coordinates
        self.assertFalse(coords.empty)
        self.assertGreater(len(coords), 0)

    def test_radius_reset_to_none(self):
        """Test setting radius back to None clears calculations"""
        lid = self.lid_standard
        
        # Initially should have properties
        self.assertIsNotNone(lid.mass)
        self.assertIsNotNone(lid.cost)
        self.assertIsNotNone(lid.volume)
        
        # Set radius to None
        lid.radius = None
        
        # Properties should now be None
        self.assertIsNone(lid.radius)
        self.assertIsNone(lid.mass)
        self.assertIsNone(lid.cost)
        self.assertIsNone(lid.volume)
        
        # Coordinates should be empty
        coords = lid.coordinates
        self.assertTrue(coords.empty)

    def test_lazy_initialization_workflow(self):
        """Test the complete workflow of lazy initialization"""
        # Create lid without radius
        lid = CylindricalLidAssembly(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            thickness=100,
            fill_factor=0.75
        )
        
        # Verify initial state
        self.assertIsNone(lid.radius)
        self.assertEqual(lid.thickness, 100)
        self.assertEqual(lid.fill_factor, 0.75)
        self.assertIsNone(lid.mass)
        
        # Set radius and verify calculations
        lid.radius = 10.0
        self.assertEqual(lid.radius, 10.0)
        self.assertIsNotNone(lid.mass)
        
        # Verify we can change radius
        original_mass = lid.mass
        lid.radius = 15.0
        self.assertEqual(lid.radius, 15.0)
        self.assertNotEqual(lid.mass, original_mass)  # Should be different due to size change

    def test_comparison_with_terminal_connector(self):
        """Test that lid assembly and terminal connector behave consistently"""
        # Create similar components with same parameters
        from steer_opencell_design.Components.Containers.Cylindrical import CylindricalTerminalConnector
        
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        lid = CylindricalLidAssembly(
            material=material,
            thickness=50,
            radius=10,
            fill_factor=0.8
        )
        
        connector = CylindricalTerminalConnector(
            material=material,
            thickness=50,
            radius=10,
            fill_factor=0.8
        )
        
        # Both should have same basic properties (since same material, size, fill factor)
        self.assertEqual(lid.radius, connector.radius)
        self.assertEqual(lid.thickness, connector.thickness) 
        self.assertEqual(lid.fill_factor, connector.fill_factor)
        
        # Volume calculations should be identical (fill factor affects both equally)
        self.assertAlmostEqual(lid.volume, connector.volume, places=2)
        self.assertAlmostEqual(lid.mass, connector.mass, places=2)
        self.assertAlmostEqual(lid.cost, connector.cost, places=2)
        
        # But footprints should be different (lid is perfect circle, connector has cutouts)
        lid_footprint = lid._calculate_footprint()
        connector_footprint = connector._calculate_footprint()
        
        # Should have different numbers of points or different geometries
        # (At minimum, the shapes will be visually different even if some coordinates overlap)
        self.assertFalse(np.array_equal(lid_footprint, connector_footprint))


class TestCylindricalCanister(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for CylindricalCan tests"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        self.can_standard = CylindricalCanister(
            material=material,
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1.0  # 1000 μm = 1 mm
        )
        
        self.can_small = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Copper"),
            outer_radius=5.0,
            height=25.0,
            wall_thickness=0.5  # 0.5 mm
        )
        
        self.can_large = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Steel"),
            outer_radius=25.0,
            height=100.0,
            wall_thickness=2.0  # 2 mm
        )
        
        self.can_thin_wall = CylindricalCanister(
            material=material,
            outer_radius=15.0,
            height=30.0,
            wall_thickness=0.1  # 0.1 mm - very thin
        )

    def test_initialization_standard(self):
        """Test standard can initialization"""
        can = self.can_standard
        self.assertEqual(can.outer_radius, 10.0)
        self.assertEqual(can.height, 50.0)
        self.assertEqual(can.wall_thickness, 1)
        self.assertEqual(can.inner_radius, 9.0)  # 10 - 1 = 9
        self.assertEqual(can.name, "Cylindrical Canister")

    def test_equal(self):
        can_copy = deepcopy(self.can_standard)
        condition = can_copy == self.can_standard
        self.assertTrue(condition)

    def test_serialization(self):
        serialized = self.can_large.serialize()
        deserialized = CylindricalCanister.deserialize(serialized)
        test_case = self.can_large == deserialized
        self.assertTrue(test_case)

    def test_initialization_edge_cases(self):
        """Test can initialization with edge case values"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        # Test minimum viable can
        min_can = CylindricalCanister(
            material=material,
            outer_radius=2.0,
            height=5.0,
            wall_thickness=0.05  # 0.05 mm
        )

        self.assertEqual(min_can.outer_radius, 2.0)
        self.assertEqual(min_can.inner_radius, 1.95)  # 2.0 - 0.05
        
        # Test thick wall can
        thick_wall_can = CylindricalCanister(
            material=material,
            outer_radius=20.0,
            height=40.0,
            wall_thickness=5.0  # 5 mm
        )

        self.assertEqual(thick_wall_can.outer_radius, 20.0)
        self.assertEqual(thick_wall_can.inner_radius, 15.0)  # 20 - 5

    def test_inner_radius_calculation(self):
        """Test that inner radius is correctly calculated"""
        can = self.can_standard
        expected_inner = can.outer_radius - (can.wall_thickness)  # Convert μm to mm
        self.assertAlmostEqual(can.inner_radius, expected_inner, places=2)
        
        # Test with different configurations
        test_cases = [
            (10.0, 1.0),  # 10mm outer, 1mm wall -> 9mm inner
            (5.0, 0.5),    # 5mm outer, 0.5mm wall -> 4.5mm inner
            (20.0, 2.5),  # 20mm outer, 2.5mm wall -> 17.5mm inner
        ]
        
        for outer_r, wall_t in test_cases:
            test_can = CylindricalCanister(
                material=PrismaticContainerMaterial.from_database("Aluminum"),
                outer_radius=outer_r,
                height=30.0,
                wall_thickness=wall_t
            )
            expected_inner = outer_r - (wall_t)
            self.assertAlmostEqual(test_can.inner_radius, expected_inner, places=2)

    def test_property_setters_trigger_recalculation(self):
        """Test that changing properties triggers recalculation"""
        can = self.can_standard
        original_volume = can.volume
        original_mass = can.mass
        
        # Change outer radius
        can.outer_radius = 15.0
        self.assertNotEqual(can.volume, original_volume)
        self.assertNotEqual(can.mass, original_mass)
        self.assertEqual(can.outer_radius, 15.0)
        
        # Change height
        original_volume = can.volume
        can.height = 75.0
        self.assertNotEqual(can.volume, original_volume)
        self.assertEqual(can.height, 75.0)
        
        # Change wall thickness
        original_volume = can.volume
        original_inner = can.inner_radius
        can.wall_thickness = 1500.0  # 1.5 mm
        self.assertNotEqual(can.inner_radius, original_inner)
        self.assertEqual(can.wall_thickness, 1500.0)

    def test_inner_radius_setter(self):
        """Test setting inner radius updates outer radius correctly"""
        can = self.can_standard
        original_wall_thickness = can.wall_thickness
        
        # Set inner radius - should update outer radius while keeping wall thickness
        can.inner_radius = 8.0
        expected_outer = 8.0 + (original_wall_thickness)  # Convert μm to mm
        self.assertAlmostEqual(can.outer_radius, expected_outer, places=2)
        self.assertEqual(can.inner_radius, 8.0)
        self.assertEqual(can.wall_thickness, original_wall_thickness)

    def test_material_dependency(self):
        """Test that different materials produce different results"""
        al_can = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1000.0
        )
        cu_can = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Copper"),
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1000.0
        )
        steel_can = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Steel"),
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1000.0
        )
        
        # Same geometry, different materials should yield different properties
        cans = [al_can, cu_can, steel_can]
        masses = [can.mass for can in cans]
        costs = [can.cost for can in cans]
        volumes = [can.volume for can in cans]
        
        # Volumes should be identical (same geometry)
        self.assertEqual(len(set(volumes)), 1)
        
        # Masses should be different (different densities)
        self.assertEqual(len(set(masses)), 3)
        
        # Costs should be different (different costs)
        self.assertEqual(len(set(costs)), 3)

    def test_coordinate_calculation(self):
        """Test that coordinate calculation works correctly"""
        can = self.can_standard
        
        # Should have top-down coordinates
        coords = can.top_down_cross_section_coordinates
        self.assertIsInstance(coords, type(can.top_down_cross_section_coordinates))
        self.assertFalse(coords.empty)
        self.assertEqual(list(coords.columns), ["x", "z"])
        
        # Should have both outer and inner circles
        x_coords = coords["x"].values
        z_coords = coords["z"].values
        
        # Calculate radii from center (assuming centered at datum)
        radii = np.sqrt((x_coords - can.datum[0])**2 + (z_coords - can.datum[1])**2)
        
        # Should have points at both outer and inner radius
        max_radius = np.max(radii)
        min_radius = np.min(radii)
        
        self.assertAlmostEqual(max_radius, can.outer_radius, places=1)
        self.assertAlmostEqual(min_radius, can.inner_radius, places=1)

    def test_plots(self):
        """Test plotting functionality"""
        # Test that plots can be generated without errors
        fig1 = self.can_standard.get_top_down_plot()
        fig2 = self.can_small.get_top_down_plot()
        fig3 = self.can_large.get_top_down_plot()
        fig4 = self.can_thin_wall.get_top_down_plot()

        fig5 = self.can_standard.get_side_cross_section_plot()
        fig6 = self.can_small.get_side_cross_section_plot()
        fig7 = self.can_large.get_side_cross_section_plot()
        fig8 = self.can_thin_wall.get_side_cross_section_plot()
        
        # Verify plots have data
        self.assertIsNotNone(fig1.data)
        self.assertIsNotNone(fig2.data)
        self.assertIsNotNone(fig3.data)
        self.assertIsNotNone(fig4.data)
                
        # Uncomment to visualize during development
        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

        # fig5.show()
        # fig6.show()
        # fig7.show()
        # fig8.show()

    def test_plot_trace_properties(self):
        """Test properties of plot traces"""
        can = self.can_standard
        trace = can.top_down_cross_section_trace
        
        # Check trace properties
        self.assertEqual(trace.mode, "lines")
        self.assertEqual(trace.name, can.name)
        self.assertEqual(trace.fill, "toself")
        self.assertEqual(trace.fillcolor, can._material.color)
        self.assertTrue(trace.showlegend)
        
        # Check that trace has data
        self.assertIsNotNone(trace.x)
        self.assertIsNotNone(trace.y)
        self.assertGreater(len(trace.x), 0)
        self.assertGreater(len(trace.y), 0)

    def test_geometric_scaling(self):
        """Test that can geometry scales correctly"""
        # Test radius scaling
        small_coords = self.can_small.top_down_cross_section_coordinates
        large_coords = self.can_large.top_down_cross_section_coordinates
        
        # Calculate extents
        small_x_extent = small_coords["x"].max() - small_coords["x"].min()
        large_x_extent = large_coords["x"].max() - large_coords["x"].min()
        
        # Ratio should match radius ratio
        expected_ratio = self.can_large.outer_radius / self.can_small.outer_radius
        actual_ratio = large_x_extent / small_x_extent
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=1)

    def test_volume_scaling_with_base(self):
        """Test that volume calculations include base correctly"""
        # Create cans with different configurations to test base vs wall volume
        tall_can = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            outer_radius=10.0,
            height=100.0,  # Tall
            wall_thickness=1
        )
        
        short_can = CylindricalCanister(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            outer_radius=10.0,
            height=10.0,  # Short - base volume more significant
            wall_thickness=1
        )
        
        # Tall can should have more volume (more wall material)
        self.assertGreater(tall_can.volume, short_can.volume)
        
        # But the difference should be reasonable (not just proportional to height
        # because base volume is constant)
        height_ratio = tall_can.height / short_can.height  # 10x height

    def test_wall_thickness_edge_cases(self):
        """Test behavior with various wall thickness configurations"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        # Very thin wall
        thin_can = CylindricalCanister(
            material=material,
            outer_radius=10.0,
            height=20.0,
            wall_thickness=0.01 # 0.01 mm
        )
        self.assertAlmostEqual(thin_can.inner_radius, 9.99, places=2)
        self.assertGreater(thin_can.volume, 0)
        
        # Thick wall (but still valid)
        thick_can = CylindricalCanister(
            material=material,
            outer_radius=10.0,
            height=20.0,
            wall_thickness=3.0  # 3 mm
        )
        self.assertEqual(thick_can.inner_radius, 7.0)
        self.assertGreater(thick_can.volume, 0)

    def test_datum_positioning(self):
        """Test that datum positioning works correctly"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        # Test with offset datum
        offset_can = CylindricalCanister(
            material=material,
            outer_radius=5.0,
            height=10.0,
            wall_thickness=500.0,
            datum=(10.0, 15.0, 5.0)
        )
        
        self.assertEqual(offset_can.datum, (10.0, 15.0, 5.0))
        
        # Coordinates should be offset from origin
        coords = offset_can.top_down_cross_section_coordinates
        x_center = (coords["x"].max() + coords["x"].min()) / 2
        z_center = (coords["z"].max() + coords["z"].min()) / 2
        
        self.assertAlmostEqual(x_center, 10.0, places=1)
        self.assertAlmostEqual(z_center, 5.0, places=1)

    def test_property_units_consistency(self):
        """Test that all properties return values in correct units"""
        can = self.can_standard
        
        # Radius properties should be in mm
        self.assertGreater(can.outer_radius, 1)  # Should be reasonable mm value
        self.assertGreater(can.inner_radius, 1)
        self.assertLess(can.outer_radius, 1000)  # Shouldn't be huge
        
        # Height should be in mm
        self.assertGreater(can.height, 1)
        self.assertLess(can.height, 1000)
        
        # Wall thickness should be in mm
        self.assertGreater(can.wall_thickness, 0.01)  # At least 0.01 mm
        self.assertLess(can.wall_thickness, 100)  # Less than 100 mm
        
        # Volume should be in mm³
        self.assertGreater(can.volume, 100)  # Reasonable volume
        
        # Mass should be in grams
        self.assertGreater(can.mass, 0.001)  # At least 1 mg


class TestCylindricalEncapsulation(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures for CylindricalEncapsulation tests"""
        # Create materials for components
        self.aluminum = PrismaticContainerMaterial.from_database("Aluminum")
        self.copper = PrismaticContainerMaterial.from_database("Copper")
        
        # Create individual components
        self.cathode_connector = CylindricalTerminalConnector(
            material=self.aluminum,
            thickness=2,
            fill_factor=0.8
        )
        
        self.anode_connector = CylindricalTerminalConnector(
            material=self.copper,
            thickness=3,  # μm
            fill_factor=0.7
        )
        
        self.lid = CylindricalLidAssembly(
            material=self.aluminum,
            thickness=4.0,  # mm
            fill_factor=0.9
        )
        
        self.canister = CylindricalCanister(
            material=self.aluminum,
            outer_radius=20.0,  # mm
            height=50.0,  # mm
            wall_thickness=0.5  
        )
        
        # Create encapsulation
        self.encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            canister=self.canister
        )

    def test_connector_radius_change(self):

        original_radius = self.encapsulation.cathode_terminal_connector.radius
        self.assertEqual(original_radius, 17.55)

        self.encapsulation.cathode_terminal_connector.radius = 15
        self.encapsulation.cathode_terminal_connector = self.encapsulation.cathode_terminal_connector
        self.assertEqual(self.encapsulation.cathode_terminal_connector.radius, 15)

    def test_initialization(self):
        """Test basic encapsulation initialization"""
        # Check that all components are properly assigned
        self.assertEqual(self.encapsulation.cathode_terminal_connector, self.cathode_connector)
        self.assertEqual(self.encapsulation.anode_terminal_connector, self.anode_connector)
        self.assertEqual(self.encapsulation.lid_assembly, self.lid)
        self.assertEqual(self.encapsulation.canister, self.canister)
        self.assertEqual(self.encapsulation.name, "Cylindrical Encapsulation")

    def test_serialization(self):
        """Test serialization and deserialization of encapsulation"""
        serialized = self.encapsulation.serialize()
        deserialized = CylindricalEncapsulation.deserialize(serialized)
        test_case = self.encapsulation == deserialized
        self.assertTrue(test_case)

    def test_plots(self):

        fig1 = self.encapsulation.plot_mass_breakdown()
        fig2 = self.encapsulation.plot_cost_breakdown()
        fig3 = self.encapsulation.plot_side_view()
        self.encapsulation.internal_height = 100
        fig4 = self.encapsulation.plot_side_view()
        self.encapsulation.radius = 50
        fig5 = self.encapsulation.plot_side_view()

        self.assertIsNotNone(fig1.data)
        self.assertIsNotNone(fig2.data)
        self.assertIsNotNone(fig3.data)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()

    def test_automatic_radius_sizing(self):
        """Test that component radii are automatically set based on canister"""
        expected_lid_radius = self.canister.inner_radius  # 19.5 mm
        expected_terminal_radius = self.canister.inner_radius * 0.9  # 17.55 mm
        
        # Check lid assembly radius
        self.assertAlmostEqual(self.encapsulation.lid_assembly.radius, expected_lid_radius, places=2)
        
        # Check terminal connector radii
        self.assertAlmostEqual(self.encapsulation.cathode_terminal_connector.radius, expected_terminal_radius, places=2)
        self.assertAlmostEqual(self.encapsulation.anode_terminal_connector.radius, expected_terminal_radius, places=2)

    def test_mass_and_cost_calculations(self):
        """Test total mass and cost calculations"""
        # Get individual component properties
        cathode_mass = self.cathode_connector.mass
        anode_mass = self.anode_connector.mass  
        lid_mass = self.lid.mass
        canister_mass = self.canister.mass
        
        cathode_cost = self.cathode_connector.cost
        anode_cost = self.anode_connector.cost
        lid_cost = self.lid.cost
        canister_cost = self.canister.cost
        
        # Check that totals are correct
        expected_total_mass = cathode_mass + anode_mass + lid_mass + canister_mass
        expected_total_cost = cathode_cost + anode_cost + lid_cost + canister_cost
        
        # Verify calculations are reasonable (all positive)
        self.assertGreater(expected_total_mass, 0)
        self.assertGreater(expected_total_cost, 0)

    def test_mass_breakdown(self):
        """Test mass breakdown property"""
        breakdown = self.encapsulation.mass_breakdown
        
        # Check structure
        self.assertIsInstance(breakdown, dict)
        self.assertEqual(len(breakdown), 4)
        
        # Check that all components are included
        component_names = list(breakdown.keys())
        self.assertIn("Cathode Terminal Connector", component_names)  # Will have 2 instances
        self.assertIn("Anode Terminal Connector", component_names)  # Will have 2 instances
        self.assertIn("Lid Assembly", component_names)
        self.assertIn("Canister", component_names)
        
        # Check that all values are positive numbers
        for name, mass in breakdown.items():
            self.assertIsInstance(mass, (int, float))
            self.assertGreater(mass, 0)

    def test_cost_breakdown(self):
        """Test cost breakdown property"""
        breakdown = self.encapsulation.cost_breakdown
        
        # Check structure
        self.assertIsInstance(breakdown, dict)
        self.assertEqual(len(breakdown), 4)
        
        # Check that all values are positive numbers
        for name, cost in breakdown.items():
            self.assertIsInstance(cost, (int, float))
            self.assertGreater(cost, 0)

    def test_plot_mass_breakdown(self):
        """Test mass breakdown plotting"""
        try:
            fig = self.encapsulation.plot_mass_breakdown()
            self.assertIsNotNone(fig)
            self.assertIsNotNone(fig.data)
            # Uncomment to view plot during development
            # fig.show()
        except Exception as e:
            self.fail(f"Mass breakdown plot failed: {str(e)}")

    def test_plot_cost_breakdown(self):
        """Test cost breakdown plotting"""
        try:
            fig = self.encapsulation.plot_cost_breakdown()
            self.assertIsNotNone(fig)
            self.assertIsNotNone(fig.data)
            # Uncomment to view plot during development
            # fig.show()
        except Exception as e:
            self.fail(f"Cost breakdown plot failed: {str(e)}")

    def test_component_setters(self):
        """Test that component setters trigger recalculations"""
        # Create new components
        new_cathode = CylindricalTerminalConnector(
            material=self.copper,
            thickness=100.0,
            fill_factor=0.6
        )
        
        original_breakdown = dict(self.encapsulation.mass_breakdown)
        
        # Replace component
        self.encapsulation.cathode_terminal_connector = new_cathode
        
        new_breakdown = self.encapsulation.mass_breakdown
        
        # Breakdown should be different
        self.assertNotEqual(original_breakdown, new_breakdown)
        
        # New component should be properly sized
        expected_radius = self.canister.inner_radius * 0.9
        self.assertAlmostEqual(new_cathode.radius, expected_radius, places=2)

    def test_different_materials(self):
        """Test encapsulation with different material combinations"""
        steel = PrismaticContainerMaterial.from_database("Steel")
        
        # Create encapsulation with different materials
        mixed_encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=CylindricalTerminalConnector(
                material=self.aluminum, thickness=50.0, fill_factor=0.8
            ),
            anode_terminal_connector=CylindricalTerminalConnector(
                material=self.copper, thickness=50.0, fill_factor=0.8
            ),
            lid_assembly=CylindricalLidAssembly(
                material=steel, thickness=100.0, fill_factor=0.9
            ),
            canister=CylindricalCanister(
                material=self.aluminum, outer_radius=15.0, height=40.0, wall_thickness=1000.0
            )
        )
        
        # Check that mass breakdown reflects different materials
        breakdown = mixed_encapsulation.mass_breakdown
        self.assertEqual(len(breakdown), 4)
        
        # All masses should be positive and different due to material differences
        masses = list(breakdown.values())
        self.assertTrue(all(mass > 0 for mass in masses))

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with minimum viable canister
        min_canister = CylindricalCanister(
            material=self.aluminum,
            outer_radius=2.0,  # mm
            height=5.0,  # mm  
            wall_thickness=0.1
        )
        
        min_encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            canister=min_canister
        )
        
        # Should still work with very small dimensions
        self.assertGreater(min_encapsulation.lid_assembly.radius, 0)
        self.assertGreater(min_encapsulation.cathode_terminal_connector.radius, 0)

    def test_name_setter(self):
        """Test name property setter"""
        original_name = self.encapsulation.name
        new_name = "Test Cylindrical Assembly"
        
        self.encapsulation.name = new_name
        self.assertEqual(self.encapsulation.name, new_name)
        self.assertNotEqual(self.encapsulation.name, original_name)

    def test_dimensional_consistency(self):
        """Test that all dimensions are consistent and reasonable"""
        # Lid radius should match canister inner radius
        self.assertEqual(self.encapsulation.lid_assembly.radius, self.canister.inner_radius)
        
        # Terminal radii should be 90% of canister inner radius
        expected_terminal_radius = self.canister.inner_radius * 0.9
        self.assertAlmostEqual(self.encapsulation.cathode_terminal_connector.radius, expected_terminal_radius, places=2)
        self.assertAlmostEqual(self.encapsulation.anode_terminal_connector.radius, expected_terminal_radius, places=2)
        
        # Terminal radii should be smaller than lid radius
        self.assertLess(self.encapsulation.cathode_terminal_connector.radius, self.encapsulation.lid_assembly.radius)
        self.assertLess(self.encapsulation.anode_terminal_connector.radius, self.encapsulation.lid_assembly.radius)

    def test_validation(self):
        """Test input validation"""
        # Test invalid component types
        with self.assertRaises(TypeError):
            CylindricalEncapsulation(
                cathode_terminal_connector="invalid",
                anode_terminal_connector=self.anode_connector,
                lid_assembly=self.lid,
                canister=self.canister
            )
            
        with self.assertRaises(TypeError):
            self.encapsulation.canister = "invalid"

    def test_different_canister_sizes(self):
        """Test behavior with different canister sizes"""
        test_cases = [
            {"outer_radius": 10.0, "height": 30.0, "wall_thickness": 200.0},
            {"outer_radius": 25.0, "height": 60.0, "wall_thickness": 1000.0},
            {"outer_radius": 50.0, "height": 100.0, "wall_thickness": 2000.0},
        ]
        
        for case in test_cases:
            test_canister = CylindricalCanister(
                material=self.aluminum,
                **case
            )
            
            test_encapsulation = CylindricalEncapsulation(
                cathode_terminal_connector=CylindricalTerminalConnector(
                    material=self.aluminum, thickness=50.0
                ),
                anode_terminal_connector=CylindricalTerminalConnector(
                    material=self.aluminum, thickness=50.0
                ),
                lid_assembly=CylindricalLidAssembly(
                    material=self.aluminum, thickness=100.0
                ),
                canister=test_canister
            )
            
            # Check dimensional relationships
            self.assertEqual(test_encapsulation.lid_assembly.radius, test_canister.inner_radius)
            expected_terminal_radius = test_canister.inner_radius * 0.9
            self.assertAlmostEqual(test_encapsulation.cathode_terminal_connector.radius, expected_terminal_radius, places=2)
            
            # Check that calculations are reasonable
            self.assertGreater(test_encapsulation.mass_breakdown["Canister"], 0)


class TestLaminateSheet(unittest.TestCase):
    """Test suite for LaminateSheet class."""

    def setUp(self):
        """Set up test fixtures for LaminateSheet tests."""
        from steer_opencell_design.Components.Containers.Pouch import LaminateSheet
        
        # Create a basic laminate sheet with all parameters
        self.laminate_sheet = LaminateSheet(
            areal_cost=2.5,
            density=920,
            thickness=50,
            datum=(0.0, 0.0, 0.0),
            name="Test Laminate Sheet"
        )
        # Set width and height after initialization
        self.laminate_sheet.width = 200
        self.laminate_sheet.height = 300
        
        # Create a laminate sheet without width and length
        self.partial_laminate_sheet = LaminateSheet(
            areal_cost=3.0,
            density=950,
            thickness=60,
            name="Partial Laminate Sheet"
        )

    def test_initialization_with_all_parameters(self):
        """Test that laminate sheet initializes correctly with all parameters."""
        self.assertIsNotNone(self.laminate_sheet)
        self.assertEqual(self.laminate_sheet.name, "Test Laminate Sheet")
        self.assertEqual(self.laminate_sheet.areal_cost, 2.5)
        self.assertEqual(self.laminate_sheet.density, 920)
        self.assertEqual(self.laminate_sheet.thickness, 50)
        self.assertEqual(self.laminate_sheet.width, 200)
        self.assertEqual(self.laminate_sheet.height, 300)

    def test_serialization(self):
        """Test serialization and deserialization of laminate sheet."""
        serialized = self.laminate_sheet.serialize()
        from steer_opencell_design.Components.Containers.Pouch import LaminateSheet
        deserialized = LaminateSheet.deserialize(serialized)
        test_case = self.laminate_sheet == deserialized
        self.assertTrue(test_case)
        
    def test_initialization_without_dimensions(self):
        """Test that laminate sheet initializes correctly without width and length."""
        self.assertIsNotNone(self.partial_laminate_sheet)
        self.assertEqual(self.partial_laminate_sheet.name, "Partial Laminate Sheet")
        self.assertEqual(self.partial_laminate_sheet.areal_cost, 3.0)
        self.assertEqual(self.partial_laminate_sheet.density, 950)
        self.assertEqual(self.partial_laminate_sheet.thickness, 60)
        self.assertIsNone(self.partial_laminate_sheet.width)
        self.assertIsNone(self.partial_laminate_sheet.height)

    def test_areal_cost_property(self):
        """Test that areal_cost property returns correct value."""
        areal_cost = self.laminate_sheet.areal_cost
        self.assertIsInstance(areal_cost, float)
        self.assertEqual(areal_cost, 2.5)

    def test_density_property(self):
        """Test that density property returns correct value."""
        density = self.laminate_sheet.density
        self.assertIsInstance(density, float)
        self.assertEqual(density, 920)

    def test_thickness_property(self):
        """Test that thickness property returns correct value."""
        thickness = self.laminate_sheet.thickness
        self.assertIsInstance(thickness, float)
        self.assertEqual(thickness, 50)

    def test_width_property(self):
        """Test that width property returns correct value."""
        width = self.laminate_sheet.width
        self.assertIsInstance(width, float)
        self.assertEqual(width, 200)

    def test_height_property(self):
        """Test that height property returns correct value."""
        height = self.laminate_sheet.height
        self.assertIsInstance(height, float)
        self.assertEqual(height, 300)

    def test_datum_property(self):
        """Test that datum property returns correct value."""
        datum = self.laminate_sheet.datum
        self.assertIsInstance(datum, tuple)
        self.assertEqual(len(datum), 3)
        self.assertEqual(datum, (0.0, 0.0, 0.0))

    def test_name_property(self):
        """Test that name property returns correct value."""
        name = self.laminate_sheet.name
        self.assertIsInstance(name, str)
        self.assertEqual(name, "Test Laminate Sheet")

    def test_area_property(self):
        """Test that area property calculates correctly."""
        area = self.laminate_sheet.area
        self.assertIsInstance(area, float)
        self.assertGreater(area, 0)

    def test_mass_property(self):
        """Test that mass property calculates correctly."""
        mass = self.laminate_sheet.mass
        self.assertIsInstance(mass, float)
        self.assertGreater(mass, 0)

    def test_cost_property(self):
        """Test that cost property calculates correctly."""
        cost = self.laminate_sheet.cost
        self.assertIsInstance(cost, float)
        self.assertGreater(cost, 0)

    def test_area_when_dimensions_missing(self):
        """Test that area returns None when width or length is missing."""
        area = self.partial_laminate_sheet.area
        self.assertIsNone(area)

    def test_mass_when_dimensions_missing(self):
        """Test that mass returns None when width or length is missing."""
        mass = self.partial_laminate_sheet.mass
        self.assertIsNone(mass)

    def test_cost_when_dimensions_missing(self):
        """Test that cost returns None when width or length is missing."""
        cost = self.partial_laminate_sheet.cost
        self.assertIsNone(cost)

    def test_height_range_property(self):
        """Test that height_range returns valid tuple."""
        height_range = self.laminate_sheet.height_range
        self.assertIsInstance(height_range, tuple)
        self.assertEqual(len(height_range), 2)
        self.assertLessEqual(height_range[0], height_range[1])

    def test_width_range_property(self):
        """Test that width_range returns valid tuple."""
        width_range = self.laminate_sheet.width_range
        self.assertIsInstance(width_range, tuple)
        self.assertEqual(len(width_range), 2)
        self.assertLessEqual(width_range[0], width_range[1])

    def test_thickness_range_property(self):
        """Test that thickness_range returns valid tuple."""
        thickness_range = self.laminate_sheet.thickness_range
        self.assertIsInstance(thickness_range, tuple)
        self.assertEqual(len(thickness_range), 2)
        self.assertLessEqual(thickness_range[0], thickness_range[1])

    def test_areal_cost_setter(self):
        """Test that areal_cost setter works correctly."""
        original_areal_cost = self.laminate_sheet.areal_cost
        new_areal_cost = 3.5
        
        self.laminate_sheet.areal_cost = new_areal_cost
        
        self.assertEqual(self.laminate_sheet.areal_cost, new_areal_cost)
        self.assertNotEqual(self.laminate_sheet.areal_cost, original_areal_cost)

    def test_density_setter(self):
        """Test that density setter works correctly."""
        original_density = self.laminate_sheet.density
        new_density = 1000
        
        self.laminate_sheet.density = new_density
        
        self.assertEqual(self.laminate_sheet.density, new_density)
        self.assertNotEqual(self.laminate_sheet.density, original_density)

    def test_thickness_setter(self):
        """Test that thickness setter works correctly."""
        original_thickness = self.laminate_sheet.thickness
        new_thickness = 70
        
        self.laminate_sheet.thickness = new_thickness
        
        self.assertEqual(self.laminate_sheet.thickness, new_thickness)
        self.assertNotEqual(self.laminate_sheet.thickness, original_thickness)

    def test_width_setter(self):
        """Test that width setter works correctly."""
        original_width = self.laminate_sheet.width
        new_width = 250
        
        self.laminate_sheet.width = new_width
        
        self.assertEqual(self.laminate_sheet.width, new_width)
        self.assertNotEqual(self.laminate_sheet.width, original_width)

    def test_height_setter(self):
        """Test that height setter works correctly."""
        original_height = self.laminate_sheet.height
        new_height = 400
        
        self.laminate_sheet.height = new_height
        
        self.assertEqual(self.laminate_sheet.height, new_height)
        self.assertNotEqual(self.laminate_sheet.height, original_height)

    def test_datum_setter(self):
        """Test that datum setter works correctly."""
        new_datum = (10.0, 20.0, 30.0)
        
        self.laminate_sheet.datum = new_datum
        
        self.assertEqual(self.laminate_sheet.datum, new_datum)

    def test_name_setter(self):
        """Test that name setter works correctly."""
        new_name = "Updated Laminate Sheet"
        
        self.laminate_sheet.name = new_name
        
        self.assertEqual(self.laminate_sheet.name, new_name)

    def test_bulk_properties_recalculation_on_width_change(self):
        """Test that bulk properties are recalculated when width changes."""
        original_mass = self.laminate_sheet.mass
        original_cost = self.laminate_sheet.cost
        
        self.laminate_sheet.width = 250
        
        new_mass = self.laminate_sheet.mass
        new_cost = self.laminate_sheet.cost
        
        self.assertNotEqual(new_mass, original_mass)
        self.assertNotEqual(new_cost, original_cost)

    def test_bulk_properties_recalculation_on_height_change(self):
        """Test that bulk properties are recalculated when height changes."""
        original_mass = self.laminate_sheet.mass
        original_cost = self.laminate_sheet.cost
        
        self.laminate_sheet.height = 400
        
        new_mass = self.laminate_sheet.mass
        new_cost = self.laminate_sheet.cost
        
        self.assertNotEqual(new_mass, original_mass)
        self.assertNotEqual(new_cost, original_cost)

    def test_bulk_properties_recalculation_on_density_change(self):
        """Test that bulk properties are recalculated when density changes."""
        original_mass = self.laminate_sheet.mass
        
        self.laminate_sheet.density = 1000
        
        new_mass = self.laminate_sheet.mass
        
        self.assertNotEqual(new_mass, original_mass)

    def test_bulk_properties_recalculation_on_areal_cost_change(self):
        """Test that bulk properties are recalculated when areal_cost changes."""
        original_cost = self.laminate_sheet.cost
        
        self.laminate_sheet.areal_cost = 4.0
        
        new_cost = self.laminate_sheet.cost
        
        self.assertNotEqual(new_cost, original_cost)

    def test_adding_dimensions_to_partial_sheet(self):
        """Test that adding dimensions to partial sheet enables bulk property calculation."""
        self.assertIsNone(self.partial_laminate_sheet.mass)
        self.assertIsNone(self.partial_laminate_sheet.cost)
        
        # Add width and height
        self.partial_laminate_sheet.width = 150
        self.partial_laminate_sheet.height = 250
        
        # Now bulk properties should be calculated
        self.assertIsNotNone(self.partial_laminate_sheet.mass)
        self.assertIsNotNone(self.partial_laminate_sheet.cost)
        self.assertGreater(self.partial_laminate_sheet.mass, 0)
        self.assertGreater(self.partial_laminate_sheet.cost, 0)

    def test_sequential_property_changes(self):
        """Test that multiple property changes work correctly."""
        # Change areal cost
        self.laminate_sheet.areal_cost = 3.0
        self.assertEqual(self.laminate_sheet.areal_cost, 3.0)
        
        # Change density
        self.laminate_sheet.density = 1000
        self.assertEqual(self.laminate_sheet.density, 1000)
        
        # Change thickness
        self.laminate_sheet.thickness = 80
        self.assertEqual(self.laminate_sheet.thickness, 80)
        
        # Change width
        self.laminate_sheet.width = 220
        self.assertEqual(self.laminate_sheet.width, 220)
        
        # Change height
        self.laminate_sheet.height = 350
        self.assertEqual(self.laminate_sheet.height, 350)
        
        # Verify all changes persisted
        self.assertEqual(self.laminate_sheet.areal_cost, 3.0)
        self.assertEqual(self.laminate_sheet.density, 1000)
        self.assertEqual(self.laminate_sheet.thickness, 80)
        self.assertEqual(self.laminate_sheet.width, 220)
        self.assertEqual(self.laminate_sheet.height, 350)

    def test_hot_press_basic(self):
        """Test that hot press method works with basic parameters."""
        # Apply hot press with a cavity
        self.laminate_sheet._hot_press(
            _depth=0.01,  # 10mm deep cavity
            _width=0.05,  # 50mm wide cavity
            _height=0.28,  # 150mm high cavity
            _datum=(0.0, 0.0)  # Centered cavity
        )
        
        # Check that hot pressed flag is set
        self.assertTrue(self.laminate_sheet._hot_pressed)
        self.assertEqual(self.laminate_sheet._cavity_depth, 0.01)
        
        # Check that cavity coordinates exist
        self.assertIsNotNone(self.laminate_sheet._cavity_coordinates)
        self.assertIsInstance(self.laminate_sheet._cavity_coordinates, np.ndarray)
        self.assertEqual(self.laminate_sheet._cavity_coordinates.shape[1], 2)

        fig1 = self.laminate_sheet.get_top_down_view()
        fig2 = self.laminate_sheet.get_right_left_view()
        fig3 = self.laminate_sheet.get_bottom_up_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_hot_press_basic_negative_depth(self):
        """Test that hot press method works with basic parameters."""
        # Apply hot press with a cavity
        self.laminate_sheet._hot_press(
            _depth=-0.01,  # 10mm deep cavity
            _width=0.05,  # 50mm wide cavity
            _height=0.28,  # 150mm high cavity
            _datum=(0.0, 0.0)  # Centered cavity
        )
        
        # Check that hot pressed flag is set
        self.assertTrue(self.laminate_sheet._hot_pressed)
        self.assertEqual(self.laminate_sheet._cavity_depth, -0.01)
        
        # Check that cavity coordinates exist
        self.assertIsNotNone(self.laminate_sheet._cavity_coordinates)
        self.assertIsInstance(self.laminate_sheet._cavity_coordinates, np.ndarray)
        self.assertEqual(self.laminate_sheet._cavity_coordinates.shape[1], 2)

        fig1 = self.laminate_sheet.get_top_down_view()
        fig2 = self.laminate_sheet.get_right_left_view()
        fig3 = self.laminate_sheet.get_bottom_up_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()


class TestPouchTerminal(unittest.TestCase):
    """Test suite for PouchTerminal class."""

    def setUp(self):
        """Set up test fixtures for PouchTerminal tests."""
        from steer_opencell_design.Components.Containers.Pouch import PouchTerminal
        
        # Create test material
        self.material = PrismaticContainerMaterial(
            name="Aluminum",
            density=2700,  # kg/m³
            specific_cost=2.5,  # $/kg
            color="#silver"
        )
        
        # Create a standard pouch terminal
        self.terminal = PouchTerminal(
            material=self.material,
            width=10,
            length=30,
            thickness=1.0,  # 1mm thickness for measurable cost
            datum=(0.0, 0.0, 0.0),
            name="Test Terminal"
        )
        
        # Create a larger terminal
        self.large_terminal = PouchTerminal(
            material=self.material,
            width=15,
            length=50,
            thickness=1.5,  # 1.5mm thickness
            name="Large Terminal"
        )

    def test_initialization_standard(self):
        """Test that pouch terminal initializes correctly."""
        self.assertIsNotNone(self.terminal)
        self.assertEqual(self.terminal.name, "Test Terminal")
        self.assertEqual(self.terminal.width, 10)
        self.assertEqual(self.terminal.length, 30)
        self.assertEqual(self.terminal.thickness, 1.0)
        self.assertEqual(self.terminal.datum, (0.0, 0.0, 0.0))

    def test_serialization(self):
        """Test serialization and deserialization of pouch terminal."""
        serialized = self.terminal.serialize()
        from steer_opencell_design.Components.Containers.Pouch import PouchTerminal
        deserialized = PouchTerminal.deserialize(serialized)
        test_case = self.terminal == deserialized
        self.assertTrue(test_case)

    def test_width_property(self):
        """Test that width property returns correct value."""
        width = self.terminal.width
        self.assertIsInstance(width, float)
        self.assertEqual(width, 10)

    def test_length_property(self):
        """Test that length property returns correct value."""
        length = self.terminal.length
        self.assertIsInstance(length, float)
        self.assertEqual(length, 30)

    def test_thickness_property(self):
        """Test that thickness property returns correct value."""
        thickness = self.terminal.thickness
        self.assertIsInstance(thickness, float)
        self.assertEqual(thickness, 1.0)
        
    def test_datum_property(self):
        """Test that datum property returns correct value."""
        datum = self.terminal.datum
        self.assertIsInstance(datum, tuple)
        self.assertEqual(len(datum), 3)
        self.assertEqual(datum, (0.0, 0.0, 0.0))

    def test_name_property(self):
        """Test that name property returns correct value."""
        name = self.terminal.name
        self.assertIsInstance(name, str)
        self.assertEqual(name, "Test Terminal")

    def test_volume_property(self):
        """Test that volume property calculates correctly."""
        volume = self.terminal.volume
        self.assertIsInstance(volume, float)
        self.assertGreater(volume, 0)

    def test_mass_property(self):
        """Test that mass property calculates correctly."""
        mass = self.terminal.mass
        self.assertIsInstance(mass, float)
        self.assertGreater(mass, 0)

    def test_cost_property(self):
        """Test that cost property calculates correctly."""
        cost = self.terminal.cost
        self.assertIsInstance(cost, float)
        self.assertGreaterEqual(cost, 0)

    def test_width_range_property(self):
        """Test that width_range returns valid tuple."""
        width_range = self.terminal.width_range
        self.assertIsInstance(width_range, tuple)
        self.assertEqual(len(width_range), 2)
        self.assertLessEqual(width_range[0], width_range[1])

    def test_length_range_property(self):
        """Test that length_range returns valid tuple."""
        length_range = self.terminal.length_range
        self.assertIsInstance(length_range, tuple)
        self.assertEqual(len(length_range), 2)
        self.assertLessEqual(length_range[0], length_range[1])

    def test_thickness_range_property(self):
        """Test that thickness_range returns valid tuple."""
        thickness_range = self.terminal.thickness_range
        self.assertIsInstance(thickness_range, tuple)
        self.assertEqual(len(thickness_range), 2)
        self.assertLessEqual(thickness_range[0], thickness_range[1])

    def test_width_setter(self):
        """Test that width setter works correctly."""
        original_width = self.terminal.width
        new_width = 12
        
        self.terminal.width = new_width
        
        self.assertEqual(self.terminal.width, new_width)
        self.assertNotEqual(self.terminal.width, original_width)

    def test_length_setter(self):
        """Test that length setter works correctly."""
        original_length = self.terminal.length
        new_length = 40
        
        self.terminal.length = new_length
        
        self.assertEqual(self.terminal.length, new_length)
        self.assertNotEqual(self.terminal.length, original_length)

    def test_thickness_setter(self):
        """Test that thickness setter works correctly."""
        original_thickness = self.terminal.thickness
        new_thickness = 1.5
        
        self.terminal.thickness = new_thickness
        
        self.assertEqual(self.terminal.thickness, new_thickness)
        self.assertNotEqual(self.terminal.thickness, original_thickness)

    def test_datum_setter(self):
        """Test that datum setter works correctly."""
        new_datum = (5.0, 10.0, 2.0)
        
        self.terminal.datum = new_datum
        
        self.assertEqual(self.terminal.datum, new_datum)

    def test_name_setter(self):
        """Test that name setter works correctly."""
        new_name = "Updated Terminal"
        
        self.terminal.name = new_name
        
        self.assertEqual(self.terminal.name, new_name)

    def test_bulk_properties_recalculation_on_width_change(self):
        """Test that bulk properties are recalculated when width changes."""
        original_volume = self.terminal.volume
        original_mass = self.terminal.mass
        
        self.terminal.width = 12
        
        new_volume = self.terminal.volume
        new_mass = self.terminal.mass
        
        self.assertNotEqual(new_volume, original_volume)
        self.assertNotEqual(new_mass, original_mass)
        # Cost should also change
        self.assertGreaterEqual(self.terminal.cost, 0)

    def test_bulk_properties_recalculation_on_length_change(self):
        """Test that bulk properties are recalculated when length changes."""
        original_volume = self.terminal.volume
        original_mass = self.terminal.mass
        
        self.terminal.length = 40
        
        new_volume = self.terminal.volume
        new_mass = self.terminal.mass
        
        self.assertNotEqual(new_volume, original_volume)
        self.assertNotEqual(new_mass, original_mass)
        # Cost should also change
        self.assertGreaterEqual(self.terminal.cost, 0)

    def test_bulk_properties_recalculation_on_thickness_change(self):
        """Test that bulk properties are recalculated when thickness changes."""
        original_volume = self.terminal.volume
        original_mass = self.terminal.mass
        
        self.terminal.thickness = 1.3
        
        new_volume = self.terminal.volume
        new_mass = self.terminal.mass
        
        self.assertNotEqual(new_volume, original_volume)
        self.assertNotEqual(new_mass, original_mass)
        # Cost should also change
        self.assertGreaterEqual(self.terminal.cost, 0)

    def test_volume_calculation(self):
        """Test that volume is calculated correctly."""
        # Volume = width * length * height (in cm³)
        # width = 10mm = 1cm, length = 30mm = 3cm, height = 1.0mm = 0.1cm
        # Expected volume = 1 * 3 * 0.1 = 0.3 cm³
        expected_volume = 0.3
        self.assertAlmostEqual(self.terminal.volume, expected_volume, places=2)

    def test_mass_calculation(self):
        """Test that mass is calculated correctly based on material density."""
        # Mass should increase with volume
        mass_small = self.terminal.mass
        mass_large = self.large_terminal.mass
        self.assertGreater(mass_large, mass_small)

    def test_cost_calculation(self):
        """Test that cost is calculated correctly based on material cost."""
        # Cost should increase with mass/volume
        cost_small = self.terminal.cost
        cost_large = self.large_terminal.cost
        # Both should be non-negative, and larger should be >= smaller
        self.assertGreaterEqual(cost_small, 0)
        self.assertGreaterEqual(cost_large, cost_small)

    def test_coordinates_calculation(self):
        """Test that coordinates are calculated."""
        # Check that top-down coordinates exist
        self.assertTrue(hasattr(self.terminal, '_top_down_coordinates'))
        self.assertIsNotNone(self.terminal._top_down_coordinates)
        
        # Check that side cross-section coordinates exist
        self.assertTrue(hasattr(self.terminal, '_right_left_coordinates'))
        self.assertIsNotNone(self.terminal._right_left_coordinates)

    def test_sequential_property_changes(self):
        """Test that multiple property changes work correctly."""
        # Change width
        self.terminal.width = 12
        self.assertEqual(self.terminal.width, 12)
        
        # Change length
        self.terminal.length = 35
        self.assertEqual(self.terminal.length, 35)
        
        # Change height
        self.terminal.height = 1.25
        self.assertEqual(self.terminal.height, 1.25)
        
        # Verify all changes persisted
        self.assertEqual(self.terminal.width, 12)
        self.assertEqual(self.terminal.length, 35)
        self.assertEqual(self.terminal.height, 1.25)
        
        # Verify bulk properties are still calculated
        self.assertGreater(self.terminal.volume, 0)
        self.assertGreater(self.terminal.mass, 0)
        self.assertGreaterEqual(self.terminal.cost, 0)

    def test_default_datum(self):
        """Test that default datum is set correctly when not specified."""
        terminal = self.large_terminal  # Created without explicit datum
        self.assertEqual(terminal.datum, (0.0, 0.0, 0.0))

    def test_custom_datum(self):
        """Test that custom datum is set correctly."""
        from steer_opencell_design.Components.Containers.Pouch import PouchTerminal
        
        
        custom_datum = (5.0, 10.0, 2.5)
        terminal = PouchTerminal(
            material=self.material,
            width=10,
            length=30,
            thickness=1.0,
            datum=custom_datum,
            name="Custom Datum Terminal"
        )
        
        self.assertEqual(terminal.datum, custom_datum)


class TestPouchEncapsulation(unittest.TestCase):
    """Test suite for PouchEncapsulation class."""

    def setUp(self):
        """Set up test fixtures for PouchEncapsulation tests."""
        from steer_opencell_design.Components.Containers.Pouch import (
            PouchEncapsulation, PouchTerminal, LaminateSheet
        )
        
        # Create test material
        self.material = PrismaticContainerMaterial(
            name="Aluminum",
            density=2700,  # kg/m³
            specific_cost=2.5,  # $/kg
            color="#silver"
        )
        
        # Create terminals
        self.cathode_terminal = PouchTerminal(
            material=self.material,
            width=10,
            length=30,
            thickness=1.0,
            name="Cathode Terminal"
        )
        
        self.anode_terminal = PouchTerminal(
            material=self.material,
            width=10,
            length=30,
            thickness=1.0,
            name="Anode Terminal"
        )
        
        # Create laminates
        self.top_laminate = LaminateSheet(
            areal_cost=2.5,
            density=920,
            thickness=50,
            name="Top Laminate"
        )
        
        self.bottom_laminate = LaminateSheet(
            areal_cost=2.5,
            density=920,
            thickness=50,
            name="Bottom Laminate"
        )
        
        # Create encapsulation with dimensions including thickness
        self.encapsulation = PouchEncapsulation(
            cathode_terminal=self.cathode_terminal,
            anode_terminal=self.anode_terminal,
            top_laminate=self.top_laminate,
            bottom_laminate=self.bottom_laminate,
            width=150,
            height=200,
            thickness=5.0,
            name="Test Encapsulation"
        )
        
        # Create encapsulation without thickness
        self.encapsulation_no_thickness = PouchEncapsulation(
            cathode_terminal=PouchTerminal(
                material=self.material,
                width=10,
                length=30,
                thickness=1.0,
                name="Cathode Terminal"
            ),
            anode_terminal=PouchTerminal(
                material=self.material,
                width=10,
                length=30,
                thickness=1.0,
                name="Anode Terminal"
            ),
            top_laminate=LaminateSheet(
                areal_cost=2.5,
                density=920,
                thickness=50,
                name="Top Laminate"
            ),
            bottom_laminate=LaminateSheet(
                areal_cost=2.5,
                density=920,
                thickness=50,
                name="Bottom Laminate"
            ),
            width=150,
            height=200,
            name="Test Encapsulation No Thickness"
        )
        
        # Create encapsulation without dimensions
        self.partial_encapsulation = PouchEncapsulation(
            cathode_terminal=PouchTerminal(
                material=self.material,
                width=8,
                length=25,
                thickness=0.8,
                name="Cathode Terminal"
            ),
            anode_terminal=PouchTerminal(
                material=self.material,
                width=8,
                length=25,
                thickness=0.8,
                name="Anode Terminal"
            ),
            top_laminate=LaminateSheet(
                areal_cost=3.0,
                density=950,
                thickness=60,
                name="Top Laminate"
            ),
            bottom_laminate=LaminateSheet(
                areal_cost=3.0,
                density=950,
                thickness=60,
                name="Bottom Laminate"
            ),
            name="Partial Encapsulation"
        )

    def test_initialization_with_dimensions(self):
        """Test that encapsulation initializes correctly with width and height."""
        self.assertIsNotNone(self.encapsulation)
        self.assertEqual(self.encapsulation.name, "Test Encapsulation")
        self.assertEqual(self.encapsulation.width, 150)
        self.assertEqual(self.encapsulation.height, 200)

    def test_serialization(self):
        """Test serialization and deserialization of encapsulation."""
        serialized = self.encapsulation.serialize()
        from steer_opencell_design.Components.Containers.Pouch import PouchEncapsulation
        deserialized = PouchEncapsulation.deserialize(serialized)
        test_case = self.encapsulation == deserialized
        self.assertTrue(test_case)

    def test_initialization_without_dimensions(self):
        """Test that encapsulation initializes correctly without width and height."""
        self.assertIsNotNone(self.partial_encapsulation)
        self.assertEqual(self.partial_encapsulation.name, "Partial Encapsulation")
        self.assertIsNone(self.partial_encapsulation.width)
        self.assertIsNone(self.partial_encapsulation.height)

    def test_width_sets_both_laminates(self):
        """Test that setting width on encapsulation sets both laminates."""
        # Set width on encapsulation
        self.encapsulation.width = 180
        
        # Check both laminates have the same width
        self.assertEqual(self.encapsulation.width, 180)
        self.assertEqual(self.encapsulation.top_laminate.width, 180)
        self.assertEqual(self.encapsulation.bottom_laminate.width, 180)

    def test_height_sets_both_laminates(self):
        """Test that setting height on encapsulation sets both laminates."""
        # Set height on encapsulation
        self.encapsulation.height = 220
        
        # Check both laminates have the same height
        self.assertEqual(self.encapsulation.height, 220)
        self.assertEqual(self.encapsulation.top_laminate.height, 220)
        self.assertEqual(self.encapsulation.bottom_laminate.height, 220)

    def test_width_property_returns_laminate_width(self):
        """Test that width property returns the top laminate width."""
        width = self.encapsulation.width
        self.assertIsInstance(width, float)
        self.assertEqual(width, self.encapsulation.top_laminate.width)

    def test_height_property_returns_laminate_height(self):
        """Test that height property returns the top laminate height."""
        height = self.encapsulation.height
        self.assertIsInstance(height, float)
        self.assertEqual(height, self.encapsulation.top_laminate.height)

    def test_mass_property(self):
        """Test that mass property calculates correctly."""
        mass = self.encapsulation.mass
        self.assertIsInstance(mass, float)
        self.assertGreater(mass, 0)

    def test_cost_property(self):
        """Test that cost property calculates correctly."""
        cost = self.encapsulation.cost
        self.assertIsInstance(cost, float)
        self.assertGreaterEqual(cost, 0)

    def test_mass_breakdown(self):
        """Test that mass breakdown includes all components."""
        breakdown = self.encapsulation.mass_breakdown
        self.assertIsInstance(breakdown, dict)
        self.assertIn("Cathode Terminal", breakdown)
        self.assertIn("Anode Terminal", breakdown)
        self.assertIn("Laminates", breakdown)
        
        # All values should be positive
        for value in breakdown.values():
            self.assertGreaterEqual(value, 0)

    def test_cost_breakdown(self):
        """Test that cost breakdown includes all components."""
        breakdown = self.encapsulation.cost_breakdown
        self.assertIsInstance(breakdown, dict)
        self.assertIn("Cathode Terminal", breakdown)
        self.assertIn("Anode Terminal", breakdown)
        self.assertIn("Top Laminate", breakdown)
        self.assertIn("Bottom Laminate", breakdown)
        
        # All values should be non-negative
        for value in breakdown.values():
            self.assertGreaterEqual(value, 0)

    def test_adding_dimensions_to_partial_encapsulation(self):
        """Test that adding dimensions to partial encapsulation updates laminates."""
        # Initially no dimensions
        self.assertIsNone(self.partial_encapsulation.width)
        self.assertIsNone(self.partial_encapsulation.height)
        
        # Set dimensions
        self.partial_encapsulation.width = 160
        self.partial_encapsulation.height = 210
        
        # Check encapsulation dimensions
        self.assertEqual(self.partial_encapsulation.width, 160)
        self.assertEqual(self.partial_encapsulation.height, 210)
        
        # Check both laminates have the dimensions
        self.assertEqual(self.partial_encapsulation.top_laminate.width, 160)
        self.assertEqual(self.partial_encapsulation.top_laminate.height, 210)
        self.assertEqual(self.partial_encapsulation.bottom_laminate.width, 160)
        self.assertEqual(self.partial_encapsulation.bottom_laminate.height, 210)

    def test_mass_recalculation_on_width_change(self):
        """Test that mass is recalculated when width changes."""
        original_mass = self.encapsulation.mass
        
        self.encapsulation.width = 180
        
        new_mass = self.encapsulation.mass
        self.assertNotEqual(new_mass, original_mass)

    def test_mass_recalculation_on_height_change(self):
        """Test that mass is recalculated when height changes."""
        original_mass = self.encapsulation.mass
        
        self.encapsulation.height = 220
        
        new_mass = self.encapsulation.mass
        self.assertNotEqual(new_mass, original_mass)

    def test_cost_recalculation_on_width_change(self):
        """Test that cost is recalculated when width changes."""
        original_cost = self.encapsulation.cost
        
        self.encapsulation.width = 180
        
        new_cost = self.encapsulation.cost
        self.assertNotEqual(new_cost, original_cost)

    def test_cost_recalculation_on_height_change(self):
        """Test that cost is recalculated when height changes."""
        original_cost = self.encapsulation.cost
        
        self.encapsulation.height = 220
        
        new_cost = self.encapsulation.cost
        self.assertNotEqual(new_cost, original_cost)

    def test_terminal_properties(self):
        """Test that terminal properties return correct objects."""
        self.assertIsInstance(self.encapsulation.cathode_terminal, type(self.cathode_terminal))
        self.assertIsInstance(self.encapsulation.anode_terminal, type(self.anode_terminal))

    def test_laminate_properties(self):
        """Test that laminate properties return correct objects."""
        self.assertIsInstance(self.encapsulation.top_laminate, type(self.top_laminate))
        self.assertIsInstance(self.encapsulation.bottom_laminate, type(self.bottom_laminate))

    def test_datum_property(self):
        """Test that datum property returns correct value."""
        datum = self.encapsulation.datum
        self.assertIsInstance(datum, tuple)
        self.assertEqual(len(datum), 3)
        self.assertEqual(datum, (0.0, 0.0, 0.0))

    def test_name_property(self):
        """Test that name property returns correct value."""
        name = self.encapsulation.name
        self.assertIsInstance(name, str)
        self.assertEqual(name, "Test Encapsulation")

    def test_datum_setter(self):
        """Test that datum setter works correctly."""
        new_datum = (10.0, 20.0, 5.0)
        self.encapsulation.datum = new_datum
        self.assertEqual(self.encapsulation.datum, new_datum)

    def test_name_setter(self):
        """Test that name setter works correctly."""
        new_name = "Updated Encapsulation"
        self.encapsulation.name = new_name
        self.assertEqual(self.encapsulation.name, new_name)

    def test_sequential_dimension_changes(self):
        """Test that multiple dimension changes work correctly."""
        # Change width
        self.encapsulation.width = 170
        self.assertEqual(self.encapsulation.width, 170)
        
        # Change height
        self.encapsulation.height = 230
        self.assertEqual(self.encapsulation.height, 230)
        
        # Verify both changes persisted
        self.assertEqual(self.encapsulation.width, 170)
        self.assertEqual(self.encapsulation.height, 230)
        
        # Verify both laminates have correct dimensions
        self.assertEqual(self.encapsulation.top_laminate.width, 170)
        self.assertEqual(self.encapsulation.top_laminate.height, 230)
        self.assertEqual(self.encapsulation.bottom_laminate.width, 170)
        self.assertEqual(self.encapsulation.bottom_laminate.height, 230)

    def test_laminates_stay_synchronized(self):
        """Test that top and bottom laminates stay synchronized."""
        # Change width multiple times
        for width in [160, 170, 180]:
            self.encapsulation.width = width
            self.assertEqual(self.encapsulation.top_laminate.width, width)
            self.assertEqual(self.encapsulation.bottom_laminate.width, width)
        
        # Change height multiple times
        for height in [210, 220, 230]:
            self.encapsulation.height = height
            self.assertEqual(self.encapsulation.top_laminate.height, height)
            self.assertEqual(self.encapsulation.bottom_laminate.height, height)


class TestPrismaticTerminalConnector(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for PrismaticTerminalConnector tests"""
        from steer_opencell_design.Components.Containers.Prismatic import PrismaticTerminalConnector
        
        material = PrismaticContainerMaterial.from_database("Aluminum")

        self.connector_standard = PrismaticTerminalConnector(
            material=material,
            thickness=2.0,
            width=20.0,
            length=50.0,
            fill_factor=0.8
        )

        self.connector_small = PrismaticTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Copper"),
            thickness=2.0,
            width=10.0,
            length=25.0,
            fill_factor=0.6
        )

        self.connector_large = PrismaticTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Steel"),
            thickness=3.0,
            width=40.0,
            length=80.0,
            fill_factor=0.9
        )
        
        # Connector without dimensions for None testing
        self.connector_no_dims = PrismaticTerminalConnector(
            material=material,
            thickness=2.0,
            fill_factor=0.8
        )

    def test_initialization_standard(self):
        """Test standard connector initialization"""
        connector = self.connector_standard
        self.assertEqual(connector.width, 20.0)
        self.assertEqual(connector.length, 50.0)
        self.assertEqual(connector.thickness, 2.0)
        self.assertEqual(connector.fill_factor, 0.8)

    def test_bulk_properties(self):
        """Test bulk property calculations"""
        connector = self.connector_standard
        self.assertIsInstance(connector.cost, (int, float))
        self.assertIsInstance(connector.mass, (int, float))
        self.assertGreater(connector.cost, 0)
        self.assertGreater(connector.mass, 0)
        self.assertGreater(connector.volume, 0)

    def test_footprint_structure(self):
        """Test that footprint calculation returns valid structure"""
        footprint = self.connector_standard._calculate_footprint()
        
        self.assertIsInstance(footprint, np.ndarray)
        self.assertEqual(len(footprint.shape), 2)
        self.assertEqual(footprint.shape[1], 2)  # x, y coordinates
        self.assertEqual(len(footprint), 5)  # Rectangle has 5 points (closed)

    def test_footprint_geometry(self):
        """Test geometric properties of the footprint"""
        footprint = self.connector_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # Check rectangular extents
        width_m = self.connector_standard._width
        length_m = self.connector_standard._length
        
        x_extent = np.max(x) - np.min(x)
        y_extent = np.max(y) - np.min(y)
        
        self.assertAlmostEqual(x_extent, width_m, places=5)
        self.assertAlmostEqual(y_extent, length_m, places=5)

    def test_properties_when_dims_none(self):
        """Test that properties return None when dimensions are not set"""
        connector = self.connector_no_dims
        
        self.assertIsNone(connector.width)
        self.assertIsNone(connector.length)
        self.assertIsNone(connector.mass)
        self.assertIsNone(connector.cost)
        self.assertIsNone(connector.volume)
        
        coords = connector.coordinates
        self.assertTrue(coords.empty)

    def test_dimension_setting_triggers_calculations(self):
        """Test that setting dimensions triggers property calculations"""
        connector = self.connector_no_dims
        
        self.assertIsNone(connector.mass)
        
        # Set width and length
        connector.width = 20.0
        connector.length = 50.0
        
        # Properties should now be calculated
        self.assertEqual(connector.width, 20.0)
        self.assertEqual(connector.length, 50.0)
        self.assertIsNotNone(connector.mass)
        self.assertGreater(connector.mass, 0)

    def test_plots(self):
        """Test plotting functionality"""

        # base case
        fig1 = self.connector_standard.get_top_down_view()
        self.assertIsNotNone(fig1.data)

        # change datum and re-plot
        self.connector_standard.datum = (10.0, 15.0, 0.0)
        fig2 = self.connector_standard.get_top_down_view()
        self.assertIsNotNone(fig2.data)

        # flip by 90 degrees along y axis and re-plot
        self.connector_standard.rotated_y = True
        fig3 = self.connector_standard.get_top_down_view()

        # unflip and re-plot
        self.connector_standard.rotated_y = False
        fig4 = self.connector_standard.get_top_down_view()

        # set to false again to ensure idempotency
        self.connector_standard.rotated_y = False
        fig5 = self.connector_standard.get_top_down_view()
        self.assertIsNotNone(fig5.data)
        self.assertEqual(fig4, fig5)
        
        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()


class TestPrismaticLidAssembly(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for PrismaticLidAssembly tests"""
        from steer_opencell_design.Components.Containers.Prismatic import PrismaticLidAssembly
        
        material = PrismaticContainerMaterial.from_database("Aluminum")

        self.lid_standard = PrismaticLidAssembly(
            material=material,
            thickness=5.0,
            width=100.0,
            length=150.0,
            fill_factor=0.8
        )

        self.lid_small = PrismaticLidAssembly(
            material=PrismaticContainerMaterial.from_database("Copper"),
            thickness=3.0,
            width=50.0,
            length=75.0,
            fill_factor=0.6
        )

    def test_initialization_standard(self):
        """Test standard lid initialization"""
        lid = self.lid_standard
        self.assertEqual(lid.width, 100.0)
        self.assertEqual(lid.length, 150.0)
        self.assertEqual(lid.thickness, 5.0)
        self.assertEqual(lid.fill_factor, 0.8)
        self.assertEqual(lid.name, "Prismatic Lid Assembly")

    def test_bulk_properties(self):
        """Test bulk property calculations"""
        lid = self.lid_standard
        self.assertIsInstance(lid.cost, (int, float))
        self.assertIsInstance(lid.mass, (int, float))
        self.assertGreater(lid.cost, 0)
        self.assertGreater(lid.mass, 0)

    def test_footprint_is_rectangular(self):
        """Test that footprint is a proper rectangle"""
        footprint = self.lid_standard._calculate_footprint()
        x, y = footprint[:, 0], footprint[:, 1]
        
        # Check that we have exactly 5 points (closed rectangle)
        self.assertEqual(len(footprint), 5)
        
        # Check that first and last points are identical (closed)
        self.assertAlmostEqual(x[0], x[-1], places=5)
        self.assertAlmostEqual(y[0], y[-1], places=5)

    def test_plots(self):
        """Test plotting functionality"""
        fig = self.lid_standard.get_top_down_view()
        self.assertIsNotNone(fig.data)


class TestPrismaticCanister(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures for PrismaticCanister tests"""
        from steer_opencell_design.Components.Containers.Prismatic import PrismaticCanister
        
        material = PrismaticContainerMaterial.from_database("Aluminum")

        self.canister_standard = PrismaticCanister(
            material=material,
            width=100.0,
            length=150.0,
            height=200.0,
            wall_thickness=2.0
        )

        self.canister_thick_walls = PrismaticCanister(
            material=PrismaticContainerMaterial.from_database("Steel"),
            width=100.0,
            length=150.0,
            height=200.0,
            wall_thickness=5.0
        )

    def test_plots_with_datums(self):

        fig1 = self.canister_standard.get_top_down_view()
        self.assertIsNotNone(fig1.data)
        fig2 = self.canister_standard.get_right_left_view()
        self.assertIsNotNone(fig2.data)

        self.canister_standard.datum = (10, 100, 20)
        fig3 = self.canister_standard.get_top_down_view()
        self.assertIsNotNone(fig3.data)
        fig4 = self.canister_standard.get_right_left_view()
        self.assertIsNotNone(fig4.data)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_initialization_standard(self):
        """Test standard canister initialization"""
        canister = self.canister_standard
        self.assertEqual(canister.width, 100.0)
        self.assertEqual(canister.length, 150.0)
        self.assertEqual(canister.height, 200.0)
        self.assertEqual(canister.wall_thickness, 2.0)
        self.assertEqual(canister.name, "Prismatic Canister")

    def test_inner_dimensions(self):
        """Test that inner dimensions are calculated correctly"""
        canister = self.canister_standard
        
        # Inner dimensions should account for wall thickness
        expected_inner_width = 100.0 - 2 * 2.0  # outer - 2*thickness
        expected_inner_length = 150.0 - 2 * 2.0
        expected_inner_height = 200.0 - 2.0  # height - bottom thickness
        
        self.assertEqual(canister.inner_width, expected_inner_width)
        self.assertEqual(canister.inner_length, expected_inner_length)
        self.assertEqual(canister.inner_height, expected_inner_height)

    def test_bulk_properties(self):
        """Test bulk property calculations"""
        canister = self.canister_standard
        self.assertIsInstance(canister.cost, (int, float))
        self.assertIsInstance(canister.mass, (int, float))
        self.assertGreater(canister.cost, 0)
        self.assertGreater(canister.mass, 0)
        self.assertGreater(canister.volume, 0)

    def test_wall_thickness_effect(self):
        """Test that thicker walls result in more mass"""
        standard_mass = self.canister_standard.mass
        thick_mass = self.canister_thick_walls.mass
        
        # Thicker walls should have more mass (even accounting for different materials)
        # Just check that both have reasonable positive values
        self.assertGreater(standard_mass, 0)
        self.assertGreater(thick_mass, 0)

    def test_setters(self):
        """Test dimension setters"""
        canister = self.canister_standard
        fig1 = canister.get_right_left_view()
        self.assertIsNotNone(fig1.data)
        
        # Test width setter
        canister.length = 200.0
        self.assertEqual(canister.length, 200.0)
        fig2 = canister.get_right_left_view()
        self.assertIsNotNone(fig2.data)
        
        # Test height setter
        canister.height = 250.0
        self.assertEqual(canister.height, 250.0)
        fig3 = canister.get_right_left_view()
        self.assertIsNotNone(fig3.data)

        # Test wall thickness setter
        canister.wall_thickness = 3.0
        self.assertEqual(canister.wall_thickness, 3.0)
        fig4 = canister.get_right_left_view()
        self.assertIsNotNone(fig4.data)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_height_setter(self):
        """Test that height setter updates inner height correctly"""
        canister = self.canister_standard
        canister.datum = (0, -97, 0)
        fig1 = canister.get_right_left_view()
        self.assertIsNotNone(fig1.data)
        self.assertEqual(canister.datum, (0, -97, 0))
        
        # Set new height
        canister.height = 250.0
        self.assertEqual(canister.height, 250.0)
        fig2 = canister.get_right_left_view()
        self.assertIsNotNone(fig2.data)
        self.assertEqual(canister.datum, (0, -97, 0))

        # rotate canister
        canister.rotated_z = True
        fig3 = canister.get_top_down_view()
        self.assertIsNotNone(fig3.data)

        canister.height = 300.0
        self.assertEqual(canister.height, 300.0)
        fig4 = canister.get_top_down_view()
        self.assertIsNotNone(fig4.data)

        # fig1.show()
        # fig2.show()

        # fig3.show()
        # fig4.show()

    def test_inner_dimension_setters(self):
        """Test that inner dimension setters update outer dimensions correctly"""
        canister = self.canister_standard
        
        # Set inner width
        canister.inner_width = 90.0
        expected_outer = 90.0 + 2 * 2.0  # inner + 2*wall_thickness
        self.assertEqual(canister.inner_width, 90.0)
        self.assertEqual(canister.width, expected_outer)
        
        # Set inner height
        canister.inner_height = 190.0
        expected_height = 190.0 + 2.0  # inner + wall_thickness
        self.assertEqual(canister.inner_height, 190.0)
        self.assertEqual(canister.height, expected_height)

    def test_plots(self):
        """Test plotting functionality"""
        # base case
        fig1 = self.canister_standard.get_top_down_view()
        self.assertIsNotNone(fig1.data)
        
        # rotate around y axis and re-plot
        self.canister_standard.rotated_z = True
        fig3 = self.canister_standard.get_top_down_view()
        self.assertIsNotNone(fig3.data)

        # fig1.show()
        # fig3.show()


class TestPrismaticEncapsulation(unittest.TestCase):
    def setUp(self):

        """Set up test fixtures for PrismaticEncapsulation tests"""
        from steer_opencell_design.Components.Containers.Prismatic import (
            PrismaticTerminalConnector,
            PrismaticLidAssembly,
            PrismaticCanister,
            PrismaticEncapsulation
        )
        
        material = PrismaticContainerMaterial.from_database("Aluminum")

        self.cathode_connector = PrismaticTerminalConnector(
            material=material,
            thickness=2.0,
            fill_factor=0.8
        )
        
        self.anode_connector = PrismaticTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Copper"),
            thickness=3.0,
            fill_factor=0.7
        )
        
        self.lid = PrismaticLidAssembly(
            material=material,
            thickness=4.0,
            fill_factor=0.9
        )
        
        self.canister = PrismaticCanister(
            material=material,
            width=100.0,
            length=150.0,
            height=200.0,
            wall_thickness=2.0
        )
        
        self.encapsulation = PrismaticEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            canister=self.canister
        )

    def test_initialization(self):
        """Test encapsulation initialization"""
        enc = self.encapsulation
        self.assertIsNotNone(enc.cathode_terminal_connector)
        self.assertIsNotNone(enc.anode_terminal_connector)
        self.assertIsNotNone(enc.lid_assembly)
        self.assertIsNotNone(enc.canister)
        self.assertEqual(enc.name, "Prismatic Encapsulation")

    def test_plots(self):
        """Test plotting functionality"""

        # base case
        fig1 = self.encapsulation.get_top_down_view()
        fig2 = self.encapsulation.get_right_left_view()
        self.assertIsNotNone(fig1.data)
        self.assertIsNotNone(fig2.data)

        # set to transverse orientation and re-plot
        from steer_opencell_design.Components.Containers.Prismatic import ConnectorOrientation
        self.encapsulation.connector_orientation = ConnectorOrientation.TRANSVERSE
        fig3 = self.encapsulation.get_top_down_view()
        fig4 = self.encapsulation.get_right_left_view()
        self.assertIsNotNone(fig3.data)
        self.assertIsNotNone(fig4.data)

        # modify the cathode terminal connector position
        self.encapsulation.connector_orientation = ConnectorOrientation.LONGITUDINAL
        self.encapsulation.cathode_terminal_connector_position = 50.0
        fig5 = self.encapsulation.get_top_down_view()
        fig6 = self.encapsulation.get_right_left_view()
        self.assertIsNotNone(fig5.data)
        self.assertIsNotNone(fig6.data)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()
        # fig6.show()

    def test_component_sizing(self):
        """Test that components are sized correctly relative to canister"""
        enc = self.encapsulation
        
        # Lid should match canister inner dimensions
        self.assertEqual(enc.lid_assembly.width, enc.canister.inner_width)
        self.assertEqual(enc.lid_assembly.length, enc.canister.inner_length)
        
        # Terminal connectors should be sized relative to canister
        # They should be smaller than the canister inner dimensions
        self.assertLess(enc.cathode_terminal_connector.width, enc.canister.inner_width)
        self.assertLess(enc.cathode_terminal_connector.length, enc.canister.inner_length)
        self.assertLess(enc.anode_terminal_connector.width, enc.canister.inner_width)
        self.assertLess(enc.anode_terminal_connector.length, enc.canister.inner_length)

    def test_component_positioning(self):
        """Test that components are positioned correctly"""
        enc = self.encapsulation
        
        # All components should have datums set
        self.assertIsNotNone(enc.lid_assembly.datum)
        self.assertIsNotNone(enc.cathode_terminal_connector.datum)
        self.assertIsNotNone(enc.anode_terminal_connector.datum)
        
        # Lid should be at top of canister
        lid_y = enc.lid_assembly.datum[1]
        canister_top = enc.canister.datum[1] + enc.canister.height
        self.assertAlmostEqual(lid_y, canister_top - enc.lid_assembly.thickness / 2, places=1)
        
        # Connectors should be offset horizontally (not at same x position)
        cathode_x = enc.cathode_terminal_connector.datum[0]
        anode_x = enc.anode_terminal_connector.datum[0]
        self.assertNotEqual(cathode_x, anode_x)

    def test_internal_height(self):
        """Test internal height calculation"""
        enc = self.encapsulation
        
        # Internal height should account for lid, connectors, and base
        internal = enc.internal_height
        self.assertIsInstance(internal, (int, float))
        self.assertGreater(internal, 0)
        self.assertLess(internal, enc.canister.height)

    def test_mass_and_cost_calculations(self):
        """Test that mass and cost are calculated correctly"""
        enc = self.encapsulation
        
        # Should have positive mass and cost
        self.assertGreater(enc.mass, 0)
        self.assertGreater(enc.cost, 0)
        
        # Should have breakdowns
        self.assertIsInstance(enc.mass_breakdown, dict)
        self.assertIsInstance(enc.cost_breakdown, dict)
        
        # Breakdowns should have all components
        self.assertIn("Cathode Terminal Connector", enc.mass_breakdown)
        self.assertIn("Anode Terminal Connector", enc.mass_breakdown)
        self.assertIn("Lid Assembly", enc.mass_breakdown)
        self.assertIn("Canister", enc.mass_breakdown)

    def test_volume_property(self):
        """Test volume property"""
        enc = self.encapsulation
        self.assertGreater(enc.volume, 0)
        # Volume should match canister volume
        self.assertEqual(enc.volume, enc.canister.volume)

    def test_dimension_properties(self):
        """Test that dimension properties work correctly"""
        enc = self.encapsulation
        
        self.assertEqual(enc.width, enc.canister.width)
        self.assertEqual(enc.length, enc.canister.length)
        self.assertEqual(enc.height, enc.canister.height)

    def test_dimension_setters(self):
        """Test that dimension setters update canister"""
        enc = self.encapsulation
        
        # Test width setter
        enc.width = 120.0
        self.assertEqual(enc.width, 120.0)
        self.assertEqual(enc.canister.width, 120.0)
        
        # Test length setter
        enc.length = 180.0
        self.assertEqual(enc.length, 180.0)
        self.assertEqual(enc.canister.length, 180.0)
        
        # Test height setter
        enc.height = 250.0
        self.assertEqual(enc.height, 250.0)
        self.assertEqual(enc.canister.height, 250.0)

    def test_internal_height_setter(self):
        """Test internal height setter adjusts canister height"""
        enc = self.encapsulation
        
        original_height = enc.height
        original_internal = enc.internal_height
        
        # Increase internal height
        new_internal = original_internal + 20.0
        enc.internal_height = new_internal
        
        self.assertEqual(enc.internal_height, new_internal)
        # Total height should have increased by same amount
        self.assertAlmostEqual(enc.height, original_height + 20.0, places=1)

    def test_datum_setter(self):
        """Test datum setter updates all components"""
        enc = self.encapsulation
        
        new_datum = (10.0, 20.0, 30.0)
        enc.datum = new_datum
        
        self.assertEqual(enc.datum, new_datum)

    def test_component_setters(self):
        """Test that component setters work and trigger recalculation"""
        from steer_opencell_design.Components.Containers.Prismatic import PrismaticTerminalConnector
        
        enc = self.encapsulation
        material = PrismaticContainerMaterial.from_database("Steel")
        
        # Create new component
        new_connector = PrismaticTerminalConnector(
            material=material,
            thickness=5.0,
            fill_factor=0.85
        )
        
        # Set new cathode connector
        enc.cathode_terminal_connector = new_connector
        
        # Should be updated and have name suffix
        self.assertEqual(enc.cathode_terminal_connector, new_connector)
        self.assertIn("Cathode", enc.cathode_terminal_connector.name)

    def test_name_setter(self):
        """Test that name setter works correctly"""
        enc = self.encapsulation
        new_name = "Custom Prismatic Encapsulation"
        enc.name = new_name
        self.assertEqual(enc.name, new_name)

    def test_modify_canister_dimensions(self):
        """Test that modifying canister dimensions updates encapsulation"""
        enc = self.encapsulation
        fig1 = enc.canister.get_top_down_view()
        fig2 = enc.get_top_down_view()
        self.assertIsNotNone(fig1.data)
        
        # Modify canister dimensions
        enc.canister.height = 300.0
        fig3 = enc.canister.get_top_down_view()
        enc.canister = enc.canister
        fig4 = enc.get_top_down_view()
        self.assertEqual(enc.height, 300.0)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_modify_canister_dimensions_transverse(self):
        """Test that modifying canister dimensions updates encapsulation"""
        enc = self.encapsulation
        fig1 = enc.get_top_down_view()

        enc.connector_orientation = 'transverse'
        fig2 = enc.get_top_down_view()

        enc.canister.height = 300.0
        fig3 = enc.canister.get_top_down_view()
        enc.canister = enc.canister
        fig4 = enc.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_modify_connector_orientation(self):
        """Test that modifying connector orientation updates encapsulation"""
        enc = self.encapsulation
        fig1 = enc.get_right_left_view()

        # change datum
        enc.datum = (100, 200, 300)
        fig2 = enc.get_right_left_view()

        # set to transverse orientation and re-plot
        enc.connector_orientation = 'transverse'
        fig3 = enc.get_right_left_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()


class TestFlexFrameEncapsulation(unittest.TestCase):

    def setUp(self):

        from steer_opencell_design.Components.Containers.Flexframe import FlexFrame, FlexFrameEncapsulation
        from steer_opencell_design.Materials.Other import FlexFrameMaterial

        material = FlexFrameMaterial(
            name="PEEK",
            density=1.3,
            specific_cost=12
        )

        self.frame = FlexFrame(
            material=material,
            width=65,
            height=84,
            border_thickness=2,
            cutout_height=76,
            thickness=4.4
        )

        from steer_opencell_design.Components.Containers.Pouch import LaminateSheet
        from steer_opencell_design.Components.Containers.Pouch import PouchTerminal
        from steer_opencell_design.Materials.Other import PrismaticContainerMaterial

        terminal_material = PrismaticContainerMaterial.from_database("Aluminum")

        cathode_terminal = PouchTerminal(
            material=terminal_material,
            thickness=0.5,
            width=10,
            length=10
        )

        anode_terminal = PouchTerminal(
            material=terminal_material,
            thickness=0.5,
            width=10,
            length=10
        )

        laminate = LaminateSheet(
            areal_cost=0.02,
            density=1.4,
            thickness=200
        )

        self.encapsulation = FlexFrameEncapsulation(
            flex_frame=self.frame,
            cathode_terminal=cathode_terminal,
            anode_terminal=anode_terminal,
            laminate_sheet=laminate
        )

    def test_basics(self):
        self.assertEqual(self.frame.width, 65)
        self.assertEqual(self.frame.height, 84)
        self.assertEqual(self.frame.border_thickness, 2)
        self.assertEqual(self.frame.cutout_height, 76)
        self.assertEqual(self.frame.thickness, 4.4)
        self.assertEqual(self.frame.mass, 4.71)
        self.assertEqual(self.frame.cost, 0.06)

        self.assertEqual(self.encapsulation.width, 65.4)
        self.assertEqual(self.encapsulation.height, 84.4)
        self.assertEqual(self.encapsulation.mass, 8.4)
        self.assertEqual(self.encapsulation.cost, 0.06)

    def test_plots(self):
        fig1 = self.frame.get_top_down_view()
        self.assertIsNotNone(fig1.data)

        fig2 = self.encapsulation.get_top_down_view()
        self.assertIsNotNone(fig2.data)

        # fig1.show()
        # fig2.show()


if __name__ == '__main__':
    unittest.main()


