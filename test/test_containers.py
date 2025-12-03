import unittest
import numpy as np

from steer_opencell_design.Components.Containers.Cylindrical import (
    CylindricalTerminalConnector,
    CylindricalLidAssembly,
    CylindricalCannister,
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

    def test_initialization_edge_cases(self):
        """Test connector initialization with edge case values"""
        # Test minimum viable connector
        min_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=0.0001,
            radius=0.5,
            fill_factor=0.1
        )
        self.assertEqual(min_connector.fill_factor, 0.1)
        
        # Test maximum viable connector
        max_connector = CylindricalTerminalConnector(
            material=PrismaticContainerMaterial.from_database("Aluminum"), 
            thickness=0.01,
            radius=25,
            fill_factor=1.0
        )
        self.assertEqual(max_connector.fill_factor, 1.0)

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


class TestCylindricalCannister(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for CylindricalCan tests"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        self.can_standard = CylindricalCannister(
            material=material,
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1.0  # 1000 μm = 1 mm
        )
        
        self.can_small = CylindricalCannister(
            material=PrismaticContainerMaterial.from_database("Copper"),
            outer_radius=5.0,
            height=25.0,
            wall_thickness=0.5  # 0.5 mm
        )
        
        self.can_large = CylindricalCannister(
            material=PrismaticContainerMaterial.from_database("Steel"),
            outer_radius=25.0,
            height=100.0,
            wall_thickness=2.0  # 2 mm
        )
        
        self.can_thin_wall = CylindricalCannister(
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
        self.assertEqual(can.name, "Cylindrical Cannister")

    def test_initialization_edge_cases(self):
        """Test can initialization with edge case values"""
        material = PrismaticContainerMaterial.from_database("Aluminum")
        
        # Test minimum viable can
        min_can = CylindricalCannister(
            material=material,
            outer_radius=2.0,
            height=5.0,
            wall_thickness=0.05  # 0.05 mm
        )

        self.assertEqual(min_can.outer_radius, 2.0)
        self.assertEqual(min_can.inner_radius, 1.95)  # 2.0 - 0.05
        
        # Test thick wall can
        thick_wall_can = CylindricalCannister(
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
            test_can = CylindricalCannister(
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
        al_can = CylindricalCannister(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1000.0
        )
        cu_can = CylindricalCannister(
            material=PrismaticContainerMaterial.from_database("Copper"),
            outer_radius=10.0,
            height=50.0,
            wall_thickness=1000.0
        )
        steel_can = CylindricalCannister(
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
        tall_can = CylindricalCannister(
            material=PrismaticContainerMaterial.from_database("Aluminum"),
            outer_radius=10.0,
            height=100.0,  # Tall
            wall_thickness=1
        )
        
        short_can = CylindricalCannister(
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
        thin_can = CylindricalCannister(
            material=material,
            outer_radius=10.0,
            height=20.0,
            wall_thickness=0.01 # 0.01 mm
        )
        self.assertAlmostEqual(thin_can.inner_radius, 9.99, places=2)
        self.assertGreater(thin_can.volume, 0)
        
        # Thick wall (but still valid)
        thick_can = CylindricalCannister(
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
        offset_can = CylindricalCannister(
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
        
        self.cannister = CylindricalCannister(
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
            cannister=self.cannister
        )

    def test_initialization(self):
        """Test basic encapsulation initialization"""
        # Check that all components are properly assigned
        self.assertEqual(self.encapsulation.cathode_terminal_connector, self.cathode_connector)
        self.assertEqual(self.encapsulation.anode_terminal_connector, self.anode_connector)
        self.assertEqual(self.encapsulation.lid_assembly, self.lid)
        self.assertEqual(self.encapsulation.cannister, self.cannister)
        self.assertEqual(self.encapsulation.name, "Cylindrical Encapsulation")

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
        """Test that component radii are automatically set based on cannister"""
        expected_lid_radius = self.cannister.inner_radius  # 19.5 mm
        expected_terminal_radius = self.cannister.inner_radius * 0.9  # 17.55 mm
        
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
        cannister_mass = self.cannister.mass
        
        cathode_cost = self.cathode_connector.cost
        anode_cost = self.anode_connector.cost
        lid_cost = self.lid.cost
        cannister_cost = self.cannister.cost
        
        # Check that totals are correct
        expected_total_mass = cathode_mass + anode_mass + lid_mass + cannister_mass
        expected_total_cost = cathode_cost + anode_cost + lid_cost + cannister_cost
        
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
        self.assertIn("Cannister", component_names)
        
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
        expected_radius = self.cannister.inner_radius * 0.9
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
            cannister=CylindricalCannister(
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
        # Test with minimum viable cannister
        min_cannister = CylindricalCannister(
            material=self.aluminum,
            outer_radius=2.0,  # mm
            height=5.0,  # mm  
            wall_thickness=0.1
        )
        
        min_encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            cannister=min_cannister
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
        # Lid radius should match cannister inner radius
        self.assertEqual(self.encapsulation.lid_assembly.radius, self.cannister.inner_radius)
        
        # Terminal radii should be 90% of cannister inner radius
        expected_terminal_radius = self.cannister.inner_radius * 0.9
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
                cannister=self.cannister
            )
            
        with self.assertRaises(TypeError):
            self.encapsulation.cannister = "invalid"

    def test_different_cannister_sizes(self):
        """Test behavior with different cannister sizes"""
        test_cases = [
            {"outer_radius": 10.0, "height": 30.0, "wall_thickness": 200.0},
            {"outer_radius": 25.0, "height": 60.0, "wall_thickness": 1000.0},
            {"outer_radius": 50.0, "height": 100.0, "wall_thickness": 2000.0},
        ]
        
        for case in test_cases:
            test_cannister = CylindricalCannister(
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
                cannister=test_cannister
            )
            
            # Check dimensional relationships
            self.assertEqual(test_encapsulation.lid_assembly.radius, test_cannister.inner_radius)
            expected_terminal_radius = test_cannister.inner_radius * 0.9
            self.assertAlmostEqual(test_encapsulation.cathode_terminal_connector.radius, expected_terminal_radius, places=2)
            
            # Check that calculations are reasonable
            self.assertGreater(test_encapsulation.mass_breakdown["Cannister"], 0)


if __name__ == '__main__':
    unittest.main()
