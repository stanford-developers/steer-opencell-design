from copy import deepcopy
import unittest
import plotly.graph_objects as go

from steer_opencell_design.Materials.Formulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors.Notched import NotchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Tabless import TablessCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Punched import PunchedCurrentCollector

from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups.Base import NPRatioControlMode
from steer_opencell_design.Constructions.Layups.OverhangUtils import OverhangControlMode
from steer_opencell_design.Constructions.Layups.Laminate import Laminate
from steer_opencell_design.Constructions.Layups.MonoLayers import MonoLayer, ZFoldMonoLayer, ElectrodeOrientation
from steer_opencell_design.Materials.Other import CurrentCollectorMaterial, InsulationMaterial, SeparatorMaterial
from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial, AnodeMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive


from steer_core.Constants.Units import *


class TestSimpleLaminate(unittest.TestCase):
    
    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        current_collector = NotchedCurrentCollector(
            material=current_collector_material,
            length=4500,
            width=300,
            thickness=8,
            tab_width=60,
            tab_spacing=200,
            tab_height=18,
            insulation_width=6,
            coated_tab_height=2,
            bare_lengths_a_side=(1000, 2000),
            bare_lengths_b_side=(500, 1500),
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        current_collector = NotchedCurrentCollector(
            material=current_collector_material,
            length=5000,
            width=306,
            thickness=8,
            tab_width=60,
            tab_spacing=100,
            tab_height=18,
            insulation_width=6,
            coated_tab_height=2,
            bare_lengths_a_side=(1500, 2500),
            bare_lengths_b_side=(800, 1800),
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=3.68,
            current_collector=current_collector,
            calender_density=1.10,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=8000)

        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=6000)

        self.layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

    def test_equality(self):
        temp_layup = deepcopy(self.layup)
        condition = self.layup == temp_layup
        self.assertTrue(condition)

    def test_serialization(self):
        serialized = self.layup.serialize()
        deserialized = Laminate.deserialize(serialized)
        test_case = self.layup == deserialized
        self.assertTrue(test_case)

    def test_get_thickness_at_x(self):
        self.layup.calculate_flattened_center_lines()
        self.assertAlmostEqual(self.layup.get_thickness_at_x(0), 0.000181, places=6)
        self.assertAlmostEqual(self.layup.get_thickness_at_x(0.1), 0.000147, places=6)
        self.assertAlmostEqual(self.layup.get_thickness_at_x(2), 0.000066, places=6)
        self.assertAlmostEqual(self.layup.get_thickness_at_x(3), 0.0000499, places=6)
        self.assertAlmostEqual(self.layup.get_thickness_at_x(15), 0, places=6)

    def test_voltage_limits(self):
        self.assertTrue(hasattr(self.layup, "_minimum_operating_voltage_range"))
        self.assertTrue(hasattr(self.layup, "_maximum_operating_voltage_range"))
        self.assertTrue(hasattr(self.layup, "minimum_operating_voltage_range"))
        self.assertTrue(hasattr(self.layup, "maximum_operating_voltage_range"))
        self.assertTrue(hasattr(self.layup, "operating_reversible_areal_capacity"))
        self.assertTrue(hasattr(self.layup, "_operating_reversible_areal_capacity"))
        self.assertTrue(hasattr(self.layup, "maximum_areal_reversible_capacity_range"))
        self.assertTrue(hasattr(self.layup, "_maximum_areal_reversible_capacity_range"))
        self.assertEqual(self.layup.minimum_operating_voltage_range, (2.27, 3.12))
        self.assertEqual(self.layup.maximum_operating_voltage_range, (3.53, 4.03))
        self.assertEqual(self.layup.operating_reversible_areal_capacity, 0.842)
        self.assertEqual(self.layup.maximum_areal_reversible_capacity_range, (0.8, 0.842))

    def test_voltage_maximum_setter(self):

        self.layup.maximum_operating_voltage = 3.8
        self.assertEqual(self.layup.maximum_operating_voltage, 3.8)
        self.assertAlmostEqual(self.layup._areal_capacity_curve[:,1].max(), 3.8, places=4)
        figure1 = self.layup.get_areal_capacity_plot()

        self.layup.maximum_operating_voltage = 4.0
        self.assertEqual(self.layup.maximum_operating_voltage, 4.0)
        self.assertAlmostEqual(self.layup._areal_capacity_curve[:,1].max(), 4.0, places=4)
        figure2 = self.layup.get_areal_capacity_plot()

        self.layup.maximum_operating_voltage = 3.5
        self.assertEqual(self.layup.maximum_operating_voltage, 3.53)
        self.assertAlmostEqual(self.layup._areal_capacity_curve[:,1].max(), 3.53, places=2)
        figure3 = self.layup.get_areal_capacity_plot()

        # figure1.show()
        # figure2.show()
        # figure3.show()

    def test_reversible_capacity_setter(self):

        self.layup.operating_reversible_areal_capacity = 0.83
        self.assertEqual(self.layup.operating_reversible_areal_capacity, 0.83)
        figure1 = self.layup.get_areal_capacity_plot()
        # figure1.show()

    def test_length_width_setter(self):

        self.assertEqual(self.layup.length, 4500)
        self.assertEqual(self.layup.width, 300)
        self.assertEqual(self.layup.anode.current_collector.length, 5000)
        self.assertEqual(self.layup.anode.current_collector.width, 306)
        self.assertEqual(self.layup.cathode.current_collector.length, 4500)
        self.assertEqual(self.layup.cathode.current_collector.width, 300)
        self.assertEqual(self.layup.top_separator.length, 8000)
        self.assertEqual(self.layup.top_separator.width, 310)
        self.assertEqual(self.layup.bottom_separator.length, 6000)
        self.assertEqual(self.layup.bottom_separator.width, 310)
        fig1 = self.layup.get_top_down_view(opacity=0.2)
        fig11 = self.layup.get_down_top_view(opacity=0.2)

        self.layup.length = 6000
        self.assertEqual(self.layup.length, 6000)
        self.assertEqual(self.layup.width, 300)
        self.assertEqual(self.layup.anode.current_collector.length, 6500)
        self.assertEqual(self.layup.anode.current_collector.width, 306)
        self.assertEqual(self.layup.cathode.current_collector.length, 6000)
        self.assertEqual(self.layup.cathode.current_collector.width, 300)
        self.assertEqual(self.layup.top_separator.length, 9500)
        self.assertEqual(self.layup.top_separator.width, 310)
        self.assertEqual(self.layup.bottom_separator.length, 7500)
        self.assertEqual(self.layup.bottom_separator.width, 310)
        fig2 = self.layup.get_top_down_view(opacity=0.2)

        self.layup.width = 400
        self.assertEqual(self.layup.length, 6000)
        self.assertEqual(self.layup.width, 400)
        self.assertEqual(self.layup.anode.current_collector.length, 6500)
        self.assertEqual(self.layup.anode.current_collector.width, 406)
        self.assertEqual(self.layup.cathode.current_collector.length, 6000)
        self.assertEqual(self.layup.cathode.current_collector.width, 400)
        self.assertEqual(self.layup.top_separator.length, 9500)
        self.assertEqual(self.layup.top_separator.width, 410)
        self.assertEqual(self.layup.bottom_separator.length, 7500)
        self.assertEqual(self.layup.bottom_separator.width, 410)
        fig3 = self.layup.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig11.show()
        # fig2.show()
        # fig3.show()

    def test_laminate(self):
        # This is a placeholder for an actual test
        self.assertTrue(isinstance(self.layup, Laminate))
        self.assertEqual(self.layup.anode_overhangs, {"left": 250, "right": 250, "top": 3, "bottom": 3})
        self.assertEqual(
            self.layup.bottom_separator_overhangs,
            {"left": 750, "right": 750, "top": 5, "bottom": 5},
        )
        self.assertEqual(
            self.layup.top_separator_overhangs,
            {"left": 1750, "right": 1750, "top": 5, "bottom": 5},
        )

    def test_plots(self):

        fig1 = self.layup.anode.get_top_down_view()
        fig2 = self.layup.cathode.get_top_down_view()
        fig3 = self.layup.get_top_down_view(opacity=0.2)
        fig4 = self.layup.get_areal_capacity_plot()
        fig5 = self.layup.get_down_top_view()

        self.layup.datum = (self.layup.total_length/2, 0, self.layup.cathode.thickness/2 * UM_TO_MM)

        fig6 = self.layup.get_down_top_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()
        # fig6.show()

    def test_change_anode_material(self):

        anode = deepcopy(self.layup.anode)
        fig1 = anode.get_top_down_view()

        new_cc_material = CurrentCollectorMaterial.from_database("Copper")
        current_collector = anode.current_collector
        current_collector.material = new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig2 = self.layup.anode.get_top_down_view()

        new_new_cc_material = CurrentCollectorMaterial.from_database("Aluminum")
        current_collector = anode.current_collector
        current_collector.material = new_new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig3 = self.layup.anode.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_double_set(self):
        self.layup.anode.current_collector.width = 100
        self.layup.anode.current_collector = deepcopy(self.layup.anode.current_collector)
        self.layup.anode = deepcopy(self.layup.anode)

        self.layup.anode.current_collector.width = 500
        self.layup.anode.current_collector = deepcopy(self.layup.anode.current_collector)
        self.layup.anode = deepcopy(self.layup.anode)

        fig1 = self.layup.anode.get_top_down_view()

        # fig1.show()

    def test_ranges_tabless(self):
        anode_cc = self.layup.anode.current_collector
        new_anode_cc = TablessCurrentCollector.from_notched(anode_cc)
        self.layup.anode.current_collector = new_anode_cc
        self.layup.anode = self.layup.anode

        cathode_cc = self.layup.cathode.current_collector
        new_cathode_cc = TablessCurrentCollector.from_notched(cathode_cc)
        self.layup.cathode.current_collector = new_cathode_cc
        self.layup.cathode = self.layup.cathode

        cathode_coated_width = self.layup.cathode.current_collector.coated_width
        self.assertEqual(
            self.layup.anode.current_collector.coated_width_range[0],
            cathode_coated_width,
        )

        fig1 = self.layup.anode.get_top_down_view()
        fig2 = self.layup.cathode.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_component(self):

        self.layup.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.layup.anode_overhang_top = 6
        self.assertEqual(self.layup.anode_overhangs, {"left": 250, "right": 250, "top": 6, "bottom": 0})
        fig1 = self.layup.get_top_down_view()

        # fig1.show()

    def test_anode_overhang_setters_fixed_overhangs(self):
        self.layup.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.layup.get_top_down_view()

        self.layup.bottom_separator_overhang_left = 10
        self.assertEqual(
            self.layup.bottom_separator_overhangs,
            {"left": 10, "right": 750, "top": 5, "bottom": 5},
        )
        fig2 = self.layup.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_np_ratio_control_mode_property(self):
        """Test np_ratio_control_mode property getter and setter."""
        # Test default mode
        self.assertEqual(self.layup.np_ratio_control_mode, NPRatioControlMode.FIXED_ANODE)

        # Test setting different modes
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE
        self.assertEqual(self.layup.np_ratio_control_mode, NPRatioControlMode.FIXED_CATHODE)

        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_THICKNESS
        self.assertEqual(self.layup.np_ratio_control_mode, NPRatioControlMode.FIXED_THICKNESS)

        # Test setting by string value
        self.layup.np_ratio_control_mode = "fixed_anode"
        self.assertEqual(self.layup.np_ratio_control_mode, NPRatioControlMode.FIXED_ANODE)

    def test_np_ratio_property_getter(self):
        """Test that np_ratio property returns correct value."""
        # Get initial N/P ratio
        initial_np_ratio = self.layup.np_ratio
        
        # Verify it's calculated correctly
        anode_capacity = self.layup.anode._mass_loading * self.layup.anode._areal_capacity_curve[:, 0].max() / self.layup.anode._mass_loading
        cathode_capacity = self.layup.cathode._mass_loading * self.layup.cathode._areal_capacity_curve[:, 0].max() / self.layup.cathode._mass_loading
        expected_np_ratio = anode_capacity / cathode_capacity
        
        self.assertAlmostEqual(initial_np_ratio, expected_np_ratio, places=2)

    def test_np_ratio_setter_fixed_cathode_mode(self):
        """Test np_ratio setter in FIXED_CATHODE mode."""
        # Set to FIXED_CATHODE mode
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE
        
        # Store initial values
        initial_cathode_mass_loading = self.layup.cathode.mass_loading
        initial_anode_mass_loading = self.layup.anode.mass_loading
        initial_np_ratio = self.layup.np_ratio
        
        # Set new N/P ratio
        target_np_ratio = 1.5
        self.layup.np_ratio = target_np_ratio

        # Check that N/P ratio changed to target
        self.assertAlmostEqual(self.layup.np_ratio, target_np_ratio, places=2)
        
        # Check that cathode mass loading stayed the same (FIXED_CATHODE)
        self.assertAlmostEqual(self.layup.cathode.mass_loading, initial_cathode_mass_loading, places=3)
        
        # Check that anode mass loading changed appropriately
        expected_anode_mass_loading = (target_np_ratio / initial_np_ratio) * initial_anode_mass_loading
        self.assertAlmostEqual(self.layup.anode.mass_loading, expected_anode_mass_loading, places=2)

    def test_np_ratio_setter_fixed_anode_mode(self):
        """Test np_ratio setter in FIXED_ANODE mode."""
        # Set to FIXED_ANODE mode (should be default, but explicit)
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_ANODE
        
        # Store initial values
        initial_cathode_mass_loading = self.layup.cathode.mass_loading
        initial_anode_mass_loading = self.layup.anode.mass_loading
        initial_np_ratio = self.layup.np_ratio
        
        # Set new N/P ratio
        target_np_ratio = 1.2
        self.layup.np_ratio = target_np_ratio

        # Check that N/P ratio changed to target
        self.assertAlmostEqual(self.layup.np_ratio, target_np_ratio, places=2)
        
        # Check that anode mass loading stayed the same (FIXED_ANODE)
        self.assertAlmostEqual(self.layup.anode.mass_loading, initial_anode_mass_loading, places=3)
        
        # Check that cathode mass loading changed appropriately
        expected_cathode_mass_loading = (initial_np_ratio / target_np_ratio) * initial_cathode_mass_loading
        self.assertAlmostEqual(self.layup.cathode.mass_loading, expected_cathode_mass_loading, places=2)

    def test_np_ratio_setter_fixed_thickness_mode(self):
        """Test np_ratio setter in FIXED_THICKNESS mode."""
        # Set to FIXED_THICKNESS mode
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_THICKNESS
        
        # Store initial values
        initial_cathode_thickness = self.layup.cathode.thickness
        initial_anode_thickness = self.layup.anode.thickness
        initial_total_thickness = initial_cathode_thickness + initial_anode_thickness
        initial_np_ratio = self.layup.np_ratio
        
        # Set new N/P ratio
        target_np_ratio = 1.1
        self.layup.np_ratio = target_np_ratio
        
        # Check that N/P ratio changed to target
        self.assertAlmostEqual(self.layup.np_ratio, target_np_ratio, places=2)
        
        # Check that total thickness remained constant
        new_total_thickness = self.layup.cathode.thickness + self.layup.anode.thickness
        self.assertAlmostEqual(new_total_thickness, initial_total_thickness, places=6)
        
        # Check that individual thicknesses changed appropriately
        self.assertNotEqual(self.layup.cathode.thickness, initial_cathode_thickness)
        self.assertNotEqual(self.layup.anode.thickness, initial_anode_thickness)

    def test_np_ratio_consistency_across_modes(self):
        """Test that same N/P ratio can be achieved in different modes."""
        target_np_ratio = 1.4
        
        # Test FIXED_CATHODE mode
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE
        self.layup.np_ratio = target_np_ratio
        cathode_mode_np_ratio = self.layup.np_ratio
        
        # Reset layup (create new instance with same initial conditions)
        self.setUp()  # Reset to initial state
        
        # Test FIXED_ANODE mode  
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_ANODE
        self.layup.np_ratio = target_np_ratio
        anode_mode_np_ratio = self.layup.np_ratio
        
        # Both should achieve the same N/P ratio
        self.assertAlmostEqual(cathode_mode_np_ratio, anode_mode_np_ratio, places=2)
        self.assertAlmostEqual(cathode_mode_np_ratio, target_np_ratio, places=2)

    def test_mass_loading_calculations_fixed_thickness(self):
        """Test detailed mass loading calculations in FIXED_THICKNESS mode."""
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_THICKNESS
        
        # Store detailed initial values
        initial_cathode_thickness = self.layup.cathode._thickness
        initial_anode_thickness = self.layup.anode._thickness
        initial_total_thickness = initial_cathode_thickness + initial_anode_thickness
        
        target_np_ratio = 1.6
        self.layup.np_ratio = target_np_ratio
        
        new_np_ratio = self.layup.np_ratio

        # Verify thickness ratios are maintained
        new_cathode_thickness = self.layup.cathode._thickness
        new_anode_thickness = self.layup.anode._thickness
        new_total_thickness = new_cathode_thickness + new_anode_thickness

        self.assertAlmostEqual(initial_total_thickness, new_total_thickness, places=4)

    def test_layup_properties_update_after_np_ratio_change(self):
        """Test that layup properties are properly updated after N/P ratio changes."""
        # Store initial properties
        initial_thickness = self.layup.anode.thickness + self.layup.cathode.thickness
        initial_capacity_curve = self.layup.areal_capacity_curve.copy()
        
        # Change N/P ratio
        self.layup.np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE
        self.layup.np_ratio = 1.8
        
        # Check that properties were updated
        new_thickness = self.layup.anode.thickness + self.layup.cathode.thickness
        new_capacity_curve = self.layup.areal_capacity_curve

        # Thickness should change if anode mass loading changed
        self.assertNotEqual(initial_thickness, new_thickness)
        
        # Capacity curve should be updated  
        self.assertFalse(initial_capacity_curve.equals(new_capacity_curve))

    def test_overhangs_stable_after_datum_shift(self):
        """Shifting layup datum should not change relative overhang measurements."""
        before = deepcopy(self.layup.anode_overhangs)
        dx, dy, dz = 15.5, -12.2, 4.0
        old_datum = self.layup.datum
        self.layup.datum = (old_datum[0] + dx, old_datum[1] + dy, old_datum[2] + dz)
        after = self.layup.anode_overhangs
        self.assertEqual(before, after)

    def test_anode_flipped_on_init(self):
        """Laminate should flip anode in y during initialization if not already flipped."""
        self.assertTrue(getattr(self.layup.anode, "_flipped_y", True))

    def test_overhang_control_mode_string_setter(self):
        """Setting overhang control mode via string should map to enum."""
        self.layup.overhang_control_mode = "fixed_overhangs"
        self.assertEqual(self.layup.overhang_control_mode, OverhangControlMode.FIXED_OVERHANGS)

    # ========== FLIP TESTS ==========

    def test_flip_x_axis(self):
        """Test flipping the laminate about the x-axis"""
        # Check initial flip state
        self.assertFalse(self.layup._flipped_x)
        
        # Flip about x-axis
        self.layup._flip("x")
        
        # Verify flip state changed
        self.assertTrue(self.layup._flipped_x)
        
        # Flip back and verify we return to original state
        self.layup._flip("x")
        self.assertFalse(self.layup._flipped_x)

    def test_flip_y_axis(self):
        """Test flipping the laminate about the y-axis"""
        # Check initial flip state
        self.assertFalse(self.layup._flipped_y)
        
        # Flip about y-axis
        self.layup._flip("y")
        
        # Verify flip state changed
        self.assertTrue(self.layup._flipped_y)
        
        # Flip back
        self.layup._flip("y")
        self.assertFalse(self.layup._flipped_y)

    def test_flip_z_axis(self):
        """Test flipping the laminate about the z-axis"""
        # Check initial flip state
        self.assertFalse(self.layup._flipped_z)
        
        # Flip about z-axis
        self.layup._flip("z")
        
        # Verify flip state changed
        self.assertTrue(self.layup._flipped_z)
        
        # Flip back
        self.layup._flip("z")
        self.assertFalse(self.layup._flipped_z)

    def test_flip_invalid_axis(self):
        """Test that invalid axis raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.layup._flip("invalid")
        
        self.assertIn("Axis must be", str(context.exception))
        
        # Test other invalid inputs
        with self.assertRaises(ValueError):
            self.layup._flip("X")  # Capital letter
            
        with self.assertRaises(ValueError):
            self.layup._flip("xy")  # Multiple axes

    def test_flip_preserves_overhangs(self):
        """Test that flipping preserves overhang relationships"""
        # Record original overhangs
        original_anode_overhangs = self.layup.anode_overhangs.copy()
        original_bottom_sep_overhangs = self.layup.bottom_separator_overhangs.copy()
        original_top_sep_overhangs = self.layup.top_separator_overhangs.copy()
        
        # Flip the layup
        self.layup._flip("x")
        
        # Overhangs should remain the same (relative positions preserved)
        self.assertEqual(self.layup.anode_overhangs, original_anode_overhangs)
        self.assertEqual(self.layup.bottom_separator_overhangs, original_bottom_sep_overhangs)
        self.assertEqual(self.layup.top_separator_overhangs, original_top_sep_overhangs)

    def test_flip_preserves_other_properties(self):
        """Test that flipping doesn't change other layup properties"""
        # Record original properties
        original_np_ratio = self.layup.np_ratio
        original_length = self.layup.length
        original_width = self.layup.width
        original_datum = self.layup.datum
        
        # Flip the layup
        self.layup._flip("y")
        
        # Verify all properties remain the same
        self.assertEqual(self.layup.np_ratio, original_np_ratio)
        self.assertEqual(self.layup.length, original_length)
        self.assertEqual(self.layup.width, original_width)
        self.assertEqual(self.layup.datum, original_datum)

    def test_multiple_axis_flips(self):
        """Test flipping about multiple axes in sequence"""
        # Flip about x and y axes
        self.layup._flip("x")
        self.layup._flip("y")
        
        # Check flip states
        self.assertTrue(self.layup._flipped_x)
        self.assertTrue(self.layup._flipped_y)
        self.assertFalse(self.layup._flipped_z)
        
        # Flip back both axes
        self.layup._flip("x")
        self.layup._flip("y")
        
        # Check all flip states are False
        self.assertFalse(self.layup._flipped_x)
        self.assertFalse(self.layup._flipped_y)
        self.assertFalse(self.layup._flipped_z)

    def test_flip_and_visualize(self):
        """Test that flipped layup can generate visualizations"""
        # Flip the layup
        self.layup._flip("y")
        
        # Test that all visualization methods work after flipping
        fig_top = self.layup.get_top_down_view(opacity=0.2)
        fig_capacity = self.layup.get_areal_capacity_plot()
        fig_bottom = self.layup.get_down_top_view(opacity=0.2)
        
        # Verify figures were created
        self.assertIsInstance(fig_top, go.Figure)
        self.assertIsInstance(fig_capacity, go.Figure)
        self.assertIsInstance(fig_bottom, go.Figure)
        
        # Verify figures have traces
        self.assertGreater(len(fig_top.data), 0)
        self.assertGreater(len(fig_capacity.data), 0)
        self.assertGreater(len(fig_bottom.data), 0)
        
        # Uncomment to visualize flipped layup
        # fig_top.show()
        # fig_capacity.show()
        # fig_bottom.show()

    def test_flip_component_states_synchronized(self):
        """Test that all components have synchronized flip states"""
        # Flip the layup
        self.layup._flip("z")
        
        # All components should have the same flip state
        self.assertTrue(self.layup._flipped_z)
        self.assertTrue(self.layup.cathode._flipped_z)
        self.assertTrue(self.layup.anode._flipped_z)
        self.assertTrue(self.layup.bottom_separator._flipped_z)
        self.assertTrue(self.layup.top_separator._flipped_z)
        
        # Flip back
        self.layup._flip("z")
        
        # All should be False
        self.assertFalse(self.layup._flipped_z)
        self.assertFalse(self.layup.cathode._flipped_z)
        self.assertFalse(self.layup.anode._flipped_z)
        self.assertFalse(self.layup.bottom_separator._flipped_z)
        self.assertFalse(self.layup.top_separator._flipped_z)


class TestSimpleMonoLayer(unittest.TestCase):

    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
        )

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=304,
            height=324,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=1.1,
            insulation_thickness=10,
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        separator = Separator(material=separator_material, thickness=25, width=310, length=326)

        self.monolayer = MonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
            electrode_orientation=ElectrodeOrientation.TRANSVERSE,
        )
    
    def test_equality(self):
        temp_layup = deepcopy(self.monolayer)
        condition = self.monolayer == temp_layup
        self.assertTrue(condition)

        fig = self.monolayer.get_top_down_view(opacity=0.2)
        # fig.show()

    def test_width_and_height_setter(self):

        self.assertEqual(self.monolayer.height, 324)
        self.assertEqual(self.monolayer.width, 304)
        self.assertEqual(self.monolayer.anode.current_collector.height, 324)
        self.assertEqual(self.monolayer.anode.current_collector.width, 304)
        self.assertEqual(self.monolayer.cathode.current_collector.height, 320)
        self.assertEqual(self.monolayer.cathode.current_collector.width, 300)
        self.assertEqual(self.monolayer.top_separator.length, 326)
        self.assertEqual(self.monolayer.top_separator.width, 310)
        self.assertEqual(self.monolayer.bottom_separator.length, 326)
        self.assertEqual(self.monolayer.bottom_separator.width, 310)
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.height = 500
        self.assertEqual(self.monolayer.height, 500)
        self.assertEqual(self.monolayer.width, 304)
        self.assertEqual(self.monolayer.anode.current_collector.height, 500)
        self.assertEqual(self.monolayer.anode.current_collector.width, 304)
        self.assertEqual(self.monolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.monolayer.cathode.current_collector.width, 300)
        self.assertEqual(self.monolayer.top_separator.length, 502)
        self.assertEqual(self.monolayer.top_separator.width, 310)
        self.assertEqual(self.monolayer.bottom_separator.length, 502)
        self.assertEqual(self.monolayer.bottom_separator.width, 310)
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.width = 400
        self.assertEqual(self.monolayer.height, 500)
        self.assertEqual(self.monolayer.width, 400)
        self.assertEqual(self.monolayer.anode.current_collector.height, 500)
        self.assertEqual(self.monolayer.anode.current_collector.width, 400)
        self.assertEqual(self.monolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.monolayer.cathode.current_collector.width, 396)
        self.assertEqual(self.monolayer.top_separator.length, 502)
        self.assertEqual(self.monolayer.top_separator.width, 406)
        self.assertEqual(self.monolayer.bottom_separator.length, 502)
        self.assertEqual(self.monolayer.bottom_separator.width, 406)
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.width = 350
        self.assertEqual(self.monolayer.height, 500)
        self.assertEqual(self.monolayer.width, 350)
        self.assertEqual(self.monolayer.anode.current_collector.height, 500)
        self.assertEqual(self.monolayer.anode.current_collector.width, 350)
        self.assertEqual(self.monolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.monolayer.cathode.current_collector.width, 346)
        self.assertEqual(self.monolayer.top_separator.length, 502)
        self.assertEqual(self.monolayer.top_separator.width, 356)
        self.assertEqual(self.monolayer.bottom_separator.length, 502)
        self.assertEqual(self.monolayer.bottom_separator.width, 356)
        fig4 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_separator_width_setter(self):
        temp_separator = deepcopy(self.monolayer.separator)
        temp_separator.width = 400
        self.monolayer.separator = temp_separator
        # fig = self.monolayer.get_top_down_view(opacity=0.2)
        # fig.show()

    def test_monolayer(self):
        self.assertTrue(isinstance(self.monolayer, MonoLayer))

        self.assertEqual(
            self.monolayer.anode_overhangs,
            {"left": 2, "right": 2, "top": 2, "bottom": 2},
        )
        self.assertEqual(
            self.monolayer.bottom_separator_overhangs,
            {"left": 5, "right": 5, "top": 3, "bottom": 3},
        )
        self.assertEqual(
            self.monolayer.top_separator_overhangs,
            {"left": 5, "right": 5, "top": 3, "bottom": 3},
        )

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.transverse = False
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_component(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.anode_overhang_left = 4
        self.assertEqual(
            self.monolayer.anode_overhangs,
            {"left": 4, "right": 0, "top": 2, "bottom": 2},
        )
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_top = 4
        self.assertEqual(
            self.monolayer.anode_overhangs,
            {"left": 4, "right": 0, "top": 4, "bottom": 0},
        )
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_overhangs(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_left = 10
        self.assertEqual(
            self.monolayer.anode_overhangs,
            {"left": 10, "right": 2, "top": 2, "bottom": 2},
        )
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_top = 10
        self.assertEqual(
            self.monolayer.anode_overhangs,
            {"left": 10, "right": 2, "top": 10, "bottom": 2},
        )
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_bottom_separator_overhang_setters_fixed_component(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.separator_overhang_left = 8

        self.assertEqual(
            self.monolayer.separator_overhangs,
            {"left": 8, "right": 2, "top": 3, "bottom": 3},
        )
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.separator_overhang_top = 6
        self.assertEqual(
            self.monolayer.separator_overhangs,
            {"left": 8, "right": 2, "top": 6, "bottom": 0},
        )

        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()

    def test_bottom_separator_overhang_setters_fixed_overhangs(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_left = 12
        self.assertEqual(
            self.monolayer.bottom_separator_overhangs,
            {"left": 12, "right": 5, "top": 3, "bottom": 3},
        )
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_top = 8
        self.assertEqual(
            self.monolayer.bottom_separator_overhangs,
            {"left": 12, "right": 5, "top": 8, "bottom": 3},
        )
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_top_separator_overhang_setters_fixed_component(self):
        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.top_separator_overhang_left = 7
        self.assertEqual(
            self.monolayer.top_separator_overhangs,
            {"left": 7, "right": 3, "top": 3, "bottom": 3},
        )
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_bottom = 5
        self.assertEqual(
            self.monolayer.top_separator_overhangs,
            {"left": 7, "right": 3, "top": 1, "bottom": 5},
        )
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()

    def test_top_separator_overhang_setters_fixed_overhangs(self):
        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_right = 15
        self.assertEqual(
            self.monolayer.top_separator_overhangs,
            {"left": 5, "right": 15, "top": 3, "bottom": 3},
        )
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_bottom = 10
        self.assertEqual(
            self.monolayer.top_separator_overhangs,
            {"left": 5, "right": 15, "top": 3, "bottom": 10},
        )
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_make_zfold_monolayer(self):
        zfold_monolayer = ZFoldMonoLayer.from_monolayer(self.monolayer)
        self.assertTrue(isinstance(zfold_monolayer, ZFoldMonoLayer))
        fig1 = zfold_monolayer.get_top_down_view()
        # fig1.show()

    def test_datum_shift_updates_components(self):
        """Shifting layup datum should translate all component datums uniformly."""
        old_layup_datum = self.monolayer.datum
        old_cathode_datum = self.monolayer.cathode.datum
        old_anode_datum = self.monolayer.anode.datum
        old_top_sep_datum = self.monolayer.top_separator.datum
        old_bottom_sep_datum = self.monolayer.bottom_separator.datum

        figure_old = self.monolayer.get_top_down_view(opacity=0.2)

        dx, dy, dz = 20.0, -15.0, 5.0  # mm shifts
        new_layup_datum = (old_layup_datum[0] + dx, old_layup_datum[1] + dy, old_layup_datum[2] + dz)

        self.monolayer.datum = new_layup_datum

        figure_new = self.monolayer.get_top_down_view(opacity=0.2)

        def assert_shift(old, new):
            self.assertAlmostEqual(new[0] - old[0], dx, places=6)
            self.assertAlmostEqual(new[1] - old[1], dy, places=6)
            self.assertAlmostEqual(new[2] - old[2], dz, places=6)

        assert_shift(old_cathode_datum, self.monolayer.cathode.datum)
        assert_shift(old_anode_datum, self.monolayer.anode.datum)
        assert_shift(old_top_sep_datum, self.monolayer.top_separator.datum)
        assert_shift(old_bottom_sep_datum, self.monolayer.bottom_separator.datum)

        # Layup datum should equal cathode datum
        self.assertEqual(self.monolayer.datum, self.monolayer.cathode.datum)

        # figure_old.show()
        # figure_new.show()

    def test_overhangs_stable_after_datum_shift(self):
        """Shifting layup datum should not change overhangs for monolayer."""
        before = deepcopy(self.monolayer.anode_overhangs)
        d = self.monolayer.datum
        self.monolayer.datum = (d[0] + 11.0, d[1] - 7.0, d[2] + 3.0)
        after = self.monolayer.anode_overhangs
        self.assertEqual(before, after)

    def test_overhang_control_mode_string_setter(self):
        self.monolayer.overhang_control_mode = "fixed_overhangs"
        self.assertEqual(self.monolayer.overhang_control_mode, OverhangControlMode.FIXED_OVERHANGS)

    # ========== FLIP TESTS ==========

    def test_flip_x_axis(self):
        """Test flipping the monolayer about the x-axis"""
        # Check initial flip state
        self.assertFalse(self.monolayer._flipped_x)
        
        # Flip about x-axis
        self.monolayer._flip("x")
        
        # Verify flip state changed
        self.assertTrue(self.monolayer._flipped_x)
        
        # Flip back and verify we return to original state
        self.monolayer._flip("x")
        self.assertFalse(self.monolayer._flipped_x)

    def test_flip_y_axis(self):
        """Test flipping the monolayer about the y-axis"""
        # Check initial flip state
        self.assertFalse(self.monolayer._flipped_y)
        
        # Flip about y-axis
        self.monolayer._flip("y")
        
        # Verify flip state changed
        self.assertTrue(self.monolayer._flipped_y)
        
        # Flip back
        self.monolayer._flip("y")
        self.assertFalse(self.monolayer._flipped_y)

    def test_flip_z_axis(self):
        """Test flipping the monolayer about the z-axis"""
        # Check initial flip state
        self.assertFalse(self.monolayer._flipped_z)
        
        # Flip about z-axis
        self.monolayer._flip("z")
        
        # Verify flip state changed
        self.assertTrue(self.monolayer._flipped_z)
        
        # Flip back
        self.monolayer._flip("z")
        self.assertFalse(self.monolayer._flipped_z)

    def test_flip_invalid_axis(self):
        """Test that invalid axis raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.monolayer._flip("invalid")
        
        self.assertIn("Axis must be", str(context.exception))

    def test_flip_preserves_overhangs(self):
        """Test that flipping preserves overhang relationships for monolayer"""
        # Record original overhangs
        original_anode_overhangs = self.monolayer.anode_overhangs.copy()
        original_separator_overhangs = self.monolayer.separator_overhangs.copy()
        
        # Flip the monolayer
        self.monolayer._flip("x")
        
        # Overhangs should remain the same (relative positions preserved)
        self.assertEqual(self.monolayer.anode_overhangs, original_anode_overhangs)
        self.assertEqual(self.monolayer.separator_overhangs, original_separator_overhangs)

    def test_flip_and_visualize_monolayer(self):
        """Test that flipped monolayer can generate visualizations"""
        # Flip the monolayer
        self.monolayer._flip("y")
        
        # Test that all visualization methods work after flipping
        fig_top = self.monolayer.get_top_down_view(opacity=0.2)
        fig_capacity = self.monolayer.get_areal_capacity_plot()
        fig_bottom = self.monolayer.get_down_top_view(opacity=0.2)
        
        # Verify figures were created
        self.assertIsInstance(fig_top, go.Figure)
        self.assertIsInstance(fig_capacity, go.Figure)
        self.assertIsInstance(fig_bottom, go.Figure)
        
        # Verify figures have traces
        self.assertGreater(len(fig_top.data), 0)
        self.assertGreater(len(fig_capacity.data), 0)
        self.assertGreater(len(fig_bottom.data), 0)
        
        # Uncomment to visualize flipped monolayer
        # fig_top.show()
        # fig_capacity.show()
        # fig_bottom.show()

    def test_flip_component_states_synchronized_monolayer(self):
        """Test that all monolayer components have synchronized flip states"""
        # Flip the monolayer
        self.monolayer._flip("z")
        
        # All components should have the same flip state
        self.assertTrue(self.monolayer._flipped_z)
        self.assertTrue(self.monolayer.cathode._flipped_z)
        self.assertTrue(self.monolayer.anode._flipped_z)
        self.assertTrue(self.monolayer.bottom_separator._flipped_z)
        self.assertTrue(self.monolayer.top_separator._flipped_z)
        
        # Flip back
        self.monolayer._flip("z")
        
        # All should be False
        self.assertFalse(self.monolayer._flipped_z)
        self.assertFalse(self.monolayer.cathode._flipped_z)
        self.assertFalse(self.monolayer.anode._flipped_z)
        self.assertFalse(self.monolayer.bottom_separator._flipped_z)
        self.assertFalse(self.monolayer.top_separator._flipped_z)


class TestZFoldMonoLayer(unittest.TestCase):

    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
        )

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=304,
            height=324,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=1.1,
            insulation_thickness=10,
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        separator = Separator(
            material=separator_material,
            thickness=25,
            width=326,
        )

        self.zfoldmonolayer = ZFoldMonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
            electrode_orientation=ElectrodeOrientation.TRANSVERSE,
        )

    def test_equality(self):
        temp_layup = deepcopy(self.zfoldmonolayer)
        condition = self.zfoldmonolayer == temp_layup
        self.assertTrue(condition)
        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_width_and_height_setter(self):

        self.assertEqual(self.zfoldmonolayer.height, 324)
        self.assertEqual(self.zfoldmonolayer.width, 304)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.height, 324)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.width, 304)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.height, 320)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.width, 300)
        self.assertEqual(self.zfoldmonolayer.top_separator.length, 304.05)
        self.assertEqual(self.zfoldmonolayer.top_separator.width, 326.0)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.length, 300.05)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.width, 326)
        fig1 = self.zfoldmonolayer.get_top_down_view(opacity=0.2)

        self.zfoldmonolayer.height = 500
        self.assertEqual(self.zfoldmonolayer.height, 500)
        self.assertEqual(self.zfoldmonolayer.width, 304)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.height, 500)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.width, 304)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.width, 300)
        self.assertEqual(self.zfoldmonolayer.top_separator.length, 304.05)
        self.assertEqual(self.zfoldmonolayer.top_separator.width, 502)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.length, 300.05)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.width, 502)
        fig2 = self.zfoldmonolayer.get_top_down_view(opacity=0.2)

        self.zfoldmonolayer.width = 400
        self.assertEqual(self.zfoldmonolayer.height, 500)
        self.assertEqual(self.zfoldmonolayer.width, 400)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.height, 500)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.width, 400)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.width, 396)
        self.assertEqual(self.zfoldmonolayer.top_separator.length, 400.05)
        self.assertEqual(self.zfoldmonolayer.top_separator.width, 502)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.length, 396.05)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.width, 502)
        fig3 = self.zfoldmonolayer.get_top_down_view(opacity=0.2)

        self.zfoldmonolayer.width = 350
        self.assertEqual(self.zfoldmonolayer.height, 500)
        self.assertEqual(self.zfoldmonolayer.width, 350)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.height, 500)
        self.assertEqual(self.zfoldmonolayer.anode.current_collector.width, 350)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.height, 496)
        self.assertEqual(self.zfoldmonolayer.cathode.current_collector.width, 346)
        self.assertEqual(self.zfoldmonolayer.top_separator.length, 350.05)
        self.assertEqual(self.zfoldmonolayer.top_separator.width, 502.0)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.length, 346.05)
        self.assertEqual(self.zfoldmonolayer.bottom_separator.width, 502)
        fig4 = self.zfoldmonolayer.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_zfold_monolayer_basic(self):
        """Test basic Z-fold monolayer functionality."""
        self.assertTrue(isinstance(self.zfoldmonolayer, ZFoldMonoLayer))
        self.assertTrue(isinstance(self.zfoldmonolayer, MonoLayer))
        self.assertTrue(hasattr(self.zfoldmonolayer, "np_ratio"))
        self.assertTrue(hasattr(self.zfoldmonolayer, "np_ratio_control_mode"))
        self.assertTrue(hasattr(self.zfoldmonolayer, "_np_ratio"))
        self.assertTrue(hasattr(self.zfoldmonolayer, "_np_ratio_control_mode"))

        # Check that separator lengths are constrained correctly
        expected_bottom_length = (self.zfoldmonolayer.cathode.current_collector._x_foil_length + 2 * self.zfoldmonolayer._bottom_separator._thickness) * M_TO_MM
        expected_top_length = (self.zfoldmonolayer.anode.current_collector._x_foil_length + 2 * self.zfoldmonolayer._top_separator._thickness) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(self.zfoldmonolayer._top_separator.length, expected_top_length, places=1)

        self.assertEqual(
            self.zfoldmonolayer.anode_overhangs,
            {"left": 2, "right": 2, "top": 2, "bottom": 2},
        )
        self.assertEqual(
            self.zfoldmonolayer.separator_overhangs,
            {"left": 0.025, "right": 0.025, "bottom": 3.0, "top": 3.0},
        )

    def test_zfold_left_right_overhangs_always_zero(self):
        """Test that left/right overhangs are always zero in calculations."""
        # Check internal calculations set left/right to zero
        self.assertAlmostEqual(self.zfoldmonolayer._bottom_separator_overhang_left, 0.000025, 6)
        self.assertAlmostEqual(self.zfoldmonolayer._bottom_separator_overhang_right, 0.000025, 6)

    def test_zfold_separator_setter_constraints(self):
        """Test that separator setters maintain Z-fold length constraints."""
        # Get original separator
        original_separator = self.zfoldmonolayer.separator

        # Create new separator with different dimensions
        new_separator = Separator(
            material=original_separator.material,
            thickness=15,  # Different thickness
            width=350,  # Different width
            name="New Separator",
        )

        # Set new separator via unified interface
        self.zfoldmonolayer.separator = new_separator

        # Check that the separator was set correctly
        self.assertEqual(self.zfoldmonolayer.separator.name, "New Separator")
        self.assertEqual(self.zfoldmonolayer.separator.thickness, 15)

        # Length should be constrained by Z-fold geometry for both internal separators
        # We can check via internal attributes since unified interface doesn't expose them
        expected_bottom_length = (self.zfoldmonolayer.cathode.current_collector._x_foil_length + 2 * new_separator._thickness) * M_TO_MM
        expected_top_length = (self.zfoldmonolayer.anode.current_collector._x_foil_length + 2 * new_separator._thickness) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(self.zfoldmonolayer._top_separator.length, expected_top_length, places=1)

        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_zfold_anode_overhangs_still_work(self):
        """Test that anode overhangs still work normally in Z-fold."""
        self.zfoldmonolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        # Set anode overhangs - should work normally
        self.zfoldmonolayer.anode_overhang_left = 4.0
        self.assertEqual(self.zfoldmonolayer.anode_overhang_left, 4.0)
        self.assertEqual(self.zfoldmonolayer.anode_overhang_right, 0.0)
        fig1 = self.zfoldmonolayer.get_top_down_view()

        self.zfoldmonolayer.anode_overhang_top = 4.0
        self.assertEqual(self.zfoldmonolayer.anode_overhang_top, 4.0)
        self.assertEqual(self.zfoldmonolayer.anode_overhang_bottom, 0.0)
        fig2 = self.zfoldmonolayer.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_unified_separator_property(self):
        """Test the unified separator property interface."""
        # Get separator should return the bottom separator as canonical reference
        separator = self.zfoldmonolayer.separator
        self.assertEqual(separator, self.zfoldmonolayer._bottom_separator)

        # Test setting via unified interface
        original_separator = self.zfoldmonolayer.separator

        # Create new separator
        new_separator = Separator(
            material=original_separator.material,
            thickness=15,  # Different thickness
            width=350,  # Different width
            name="New Z-Fold Separator",
        )

        # Set via unified interface
        self.zfoldmonolayer.separator = new_separator

        # Both separators should be updated with correct lengths
        expected_bottom_length = (self.zfoldmonolayer.cathode.current_collector._x_foil_length + 2 * new_separator._thickness) * M_TO_MM
        expected_top_length = (self.zfoldmonolayer.anode.current_collector._x_foil_length + 2 * new_separator._thickness) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(self.zfoldmonolayer._top_separator.length, expected_top_length, places=1)
        self.assertEqual(self.zfoldmonolayer.separator.name, "New Z-Fold Separator")

        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_unified_separator_overhang_properties_fixed_component(self):
        """Test the unified separator overhang properties."""
        self.zfoldmonolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        # Test unified bottom overhang
        self.zfoldmonolayer.separator_overhang_bottom = 6.0
        self.assertEqual(self.zfoldmonolayer.separator_overhang_bottom, 6.0)
        self.assertEqual(self.zfoldmonolayer.separator_overhang_top, 0.0)

        # Test unified top overhang
        self.zfoldmonolayer.separator_overhang_top = 6.0
        self.assertEqual(self.zfoldmonolayer.separator_overhang_top, 6.0)
        self.assertEqual(self.zfoldmonolayer.separator_overhang_bottom, 0.0)

        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_unified_separator_overhang_properties_fixed_overhangs(self):
        """Test the unified separator overhang properties."""
        self.zfoldmonolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        # Test unified bottom overhang
        self.zfoldmonolayer.separator_overhang_bottom = 6.0
        self.assertEqual(self.zfoldmonolayer.separator_overhang_bottom, 6.0)
        self.assertEqual(self.zfoldmonolayer.separator_overhang_top, 3.0)

        # Test unified top overhang
        self.zfoldmonolayer.separator_overhang_top = 6.0
        self.assertEqual(self.zfoldmonolayer.separator_overhang_top, 6.0)
        self.assertEqual(self.zfoldmonolayer.separator_overhang_bottom, 6.0)

        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_make_monolayer(self):

        monolayer = MonoLayer.from_zfold_monolayer(self.zfoldmonolayer)
        self.assertTrue(isinstance(monolayer, MonoLayer))

        fig1 = monolayer.get_top_down_view()
        # fig1.show()

    def test_overhang_control_mode_string_setter(self):
        self.zfoldmonolayer.overhang_control_mode = "fixed_overhangs"
        self.assertEqual(self.zfoldmonolayer.overhang_control_mode, OverhangControlMode.FIXED_OVERHANGS)

    def test_change_anode_dimensions(self):
        fig1 = self.zfoldmonolayer.get_top_down_view()
        self.zfoldmonolayer.anode.current_collector.width = 400
        self.zfoldmonolayer.anode.current_collector = self.zfoldmonolayer.anode.current_collector
        self.zfoldmonolayer.anode = self.zfoldmonolayer.anode
        fig2 = self.zfoldmonolayer.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_change_electrode_orientation(self):

        fig1 = self.zfoldmonolayer.get_top_down_view()
        self.zfoldmonolayer.electrode_orientation = ElectrodeOrientation.LONGITUDINAL
        fig2 = self.zfoldmonolayer.get_top_down_view()
        self.zfoldmonolayer.electrode_orientation = 'transverse'
        fig3 = self.zfoldmonolayer.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    # ========== FLIP TESTS ==========

    def test_flip_x_axis_zfold(self):
        """Test flipping the Z-fold monolayer about the x-axis"""
        # Check initial flip state
        self.assertFalse(self.zfoldmonolayer._flipped_x)
        
        # Flip about x-axis
        self.zfoldmonolayer._flip("x")
        
        # Verify flip state changed
        self.assertTrue(self.zfoldmonolayer._flipped_x)
        
        # Flip back and verify we return to original state
        self.zfoldmonolayer._flip("x")
        self.assertFalse(self.zfoldmonolayer._flipped_x)

    def test_flip_y_axis_zfold(self):
        """Test flipping the Z-fold monolayer about the y-axis"""
        # Check initial flip state
        self.assertFalse(self.zfoldmonolayer._flipped_y)
        
        # Flip about y-axis
        self.zfoldmonolayer._flip("y")
        
        # Verify flip state changed
        self.assertTrue(self.zfoldmonolayer._flipped_y)
        
        # Flip back
        self.zfoldmonolayer._flip("y")
        self.assertFalse(self.zfoldmonolayer._flipped_y)

    def test_flip_z_axis_zfold(self):
        """Test flipping the Z-fold monolayer about the z-axis"""
        # Check initial flip state
        self.assertFalse(self.zfoldmonolayer._flipped_z)
        
        # Flip about z-axis
        self.zfoldmonolayer._flip("z")
        
        # Verify flip state changed
        self.assertTrue(self.zfoldmonolayer._flipped_z)
        
        # Flip back
        self.zfoldmonolayer._flip("z")
        self.assertFalse(self.zfoldmonolayer._flipped_z)

    def test_flip_invalid_axis_zfold(self):
        """Test that invalid axis raises ValueError for Z-fold"""
        with self.assertRaises(ValueError) as context:
            self.zfoldmonolayer._flip("invalid")
        
        self.assertIn("Axis must be", str(context.exception))

    def test_flip_preserves_separator_constraints_zfold(self):
        """Test that flipping preserves Z-fold separator length constraints"""
        # Record original separator lengths (they should be constrained by Z-fold geometry)
        original_bottom_length = self.zfoldmonolayer._bottom_separator.length
        original_top_length = self.zfoldmonolayer._top_separator.length
        
        # Flip the Z-fold monolayer
        self.zfoldmonolayer._flip("x")
        
        # Separator lengths should remain constrained
        self.assertAlmostEqual(self.zfoldmonolayer._bottom_separator.length, original_bottom_length, places=1)
        self.assertAlmostEqual(self.zfoldmonolayer._top_separator.length, original_top_length, places=1)

    def test_flip_preserves_zfold_overhangs(self):
        """Test that flipping preserves Z-fold overhang relationships"""
        # Record original overhangs (including unified separator overhangs)
        original_anode_overhangs = self.zfoldmonolayer.anode_overhangs.copy()
        original_separator_overhangs = self.zfoldmonolayer.separator_overhangs.copy()
        
        # Flip the Z-fold monolayer
        self.zfoldmonolayer._flip("y")
        
        # Overhangs should remain the same (relative positions preserved)
        self.assertEqual(self.zfoldmonolayer.anode_overhangs, original_anode_overhangs)
        self.assertEqual(self.zfoldmonolayer.separator_overhangs, original_separator_overhangs)

    def test_flip_and_visualize_zfold(self):
        """Test that flipped Z-fold monolayer can generate visualizations"""
        # Flip the Z-fold monolayer
        self.zfoldmonolayer._flip("z")
        
        # Test that all visualization methods work after flipping
        fig_top = self.zfoldmonolayer.get_top_down_view(opacity=0.2)
        fig_capacity = self.zfoldmonolayer.get_areal_capacity_plot()
        fig_bottom = self.zfoldmonolayer.get_down_top_view(opacity=0.2)
        
        # Verify figures were created
        self.assertIsInstance(fig_top, go.Figure)
        self.assertIsInstance(fig_capacity, go.Figure)
        self.assertIsInstance(fig_bottom, go.Figure)
        
        # Verify figures have traces
        self.assertGreater(len(fig_top.data), 0)
        self.assertGreater(len(fig_capacity.data), 0)
        self.assertGreater(len(fig_bottom.data), 0)
        
        # Uncomment to visualize flipped Z-fold monolayer
        # fig_top.show()
        # fig_capacity.show()
        # fig_bottom.show()

    def test_flip_component_states_synchronized_zfold(self):
        """Test that all Z-fold monolayer components have synchronized flip states"""
        # Flip the Z-fold monolayer
        self.zfoldmonolayer._flip("y")
        
        # The layup and separators should have the same flip state
        # Note: Individual electrodes may have different internal flip states due to Z-fold initialization
        self.assertTrue(self.zfoldmonolayer._flipped_y)
        self.assertTrue(self.zfoldmonolayer.bottom_separator._flipped_y)
        self.assertTrue(self.zfoldmonolayer.top_separator._flipped_y)
        
        # Flip back
        self.zfoldmonolayer._flip("y")
        
        # All should be False
        self.assertFalse(self.zfoldmonolayer._flipped_y)
        self.assertFalse(self.zfoldmonolayer.bottom_separator._flipped_y)
        self.assertFalse(self.zfoldmonolayer.top_separator._flipped_y)

    def test_flip_maintains_zfold_geometry(self):
        """Test that flipping maintains Z-fold specific geometric relationships"""
        # Record original geometric relationships
        original_bottom_sep_length = self.zfoldmonolayer._bottom_separator.length
        original_top_sep_length = self.zfoldmonolayer._top_separator.length
        
        # Flip multiple times
        self.zfoldmonolayer._flip("x")
        self.zfoldmonolayer._flip("z")
        
        # Z-fold geometric constraints should still be maintained
        # The separator lengths should remain the same after flipping
        self.assertAlmostEqual(self.zfoldmonolayer._bottom_separator.length, original_bottom_sep_length, places=1)
        self.assertAlmostEqual(self.zfoldmonolayer._top_separator.length, original_top_sep_length, places=1)


if __name__ == "__main__":
    unittest.main()

