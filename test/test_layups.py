from copy import deepcopy
import unittest

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import (
    NotchedCurrentCollector,
    PunchedCurrentCollector,
    TablessCurrentCollector,
)
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups import (
    Laminate,
    MonoLayer,
    ZFoldMonoLayer,
    OverhangControlMode,
)

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial,
    InsulationMaterial,
    SeparatorMaterial,
)
from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)

from steer_core.Constants.Units import *


class TestSimpleLaminate(unittest.TestCase):
    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(
            name="super_P", specific_cost=15, density=2.0, color="#000000"
        )
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(
            name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
        )

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
            length=4500,
            width=306,
            thickness=8,
            tab_width=60,
            tab_spacing=100,
            tab_height=18,
            insulation_width=6,
            coated_tab_height=2,
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=3.68,
            current_collector=current_collector,
            calender_density=2.60,
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

        top_separator = Separator(
            material=separator_material, thickness=25, width=310, length=4800
        )

        bottom_separator = Separator(
            material=separator_material, thickness=25, width=310, length=4800
        )

        self.layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

    def test_laminate(self):
        # This is a placeholder for an actual test
        self.assertTrue(isinstance(self.layup, Laminate))
        self.assertEqual(
            self.layup.anode_overhangs, {"left": 0, "right": 0, "top": 3, "bottom": 3}
        )
        self.assertEqual(
            self.layup.bottom_separator_overhangs,
            {"left": 150, "right": 150, "top": 5, "bottom": 5},
        )
        self.assertEqual(
            self.layup.top_separator_overhangs,
            {"left": 150, "right": 150, "top": 5, "bottom": 5},
        )

    def test_plots(self):
        fig1 = self.layup.anode._get_full_top_down_view()
        fig2 = self.layup.cathode._get_full_top_down_view()
        fig3 = self.layup.get_top_down_view(opacity=0.2)
        fig4 = self.layup.get_areal_capacity_plot()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_change_anode_material(self):
        anode = deepcopy(self.layup.anode)
        fig1 = anode._get_full_top_down_view()

        new_cc_material = CurrentCollectorMaterial.from_database("Copper")
        current_collector = anode.current_collector
        current_collector.material = new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig2 = self.layup.anode._get_full_top_down_view()

        new_new_cc_material = CurrentCollectorMaterial.from_database("Aluminum")
        current_collector = anode.current_collector
        current_collector.material = new_new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig3 = self.layup.anode._get_full_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_double_set(self):
        self.layup.anode.current_collector.width = 100
        self.layup.anode.current_collector = deepcopy(
            self.layup.anode.current_collector
        )
        self.layup.anode = deepcopy(self.layup.anode)

        self.layup.anode.current_collector.width = 500
        self.layup.anode.current_collector = deepcopy(
            self.layup.anode.current_collector
        )
        self.layup.anode = deepcopy(self.layup.anode)

        fig1 = self.layup.anode._get_full_top_down_view()

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

        fig1 = self.layup.anode._get_full_top_down_view()
        fig2 = self.layup.cathode._get_full_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_component(self):
        self.layup.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.layup.anode_overhang_top = 6
        self.assertEqual(
            self.layup.anode_overhangs, {"left": 0, "right": 0, "top": 6, "bottom": 0}
        )
        fig1 = self.layup.get_top_down_view()

        # fig1.show()

    def test_anode_overhang_setters_fixed_overhangs(self):
        self.layup.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.layup.get_top_down_view()

        self.layup.bottom_separator_overhang_left = 10
        self.assertEqual(
            self.layup.bottom_separator_overhangs,
            {"left": 10, "right": 150, "top": 5, "bottom": 5},
        )
        fig2 = self.layup.get_top_down_view()

        # fig1.show()
        # fig2.show()


class TestSimpleMonoLayer(unittest.TestCase):
    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(
            name="super_P", specific_cost=15, density=2.0, color="#000000"
        )
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(
            name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
        )

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
            material=separator_material, thickness=25, width=310, length=326
        )

        self.monolayer = MonoLayer(
            anode=anode,
            cathode=cathode,
            top_separator=separator,
            bottom_separator=separator,
            transverse=True,
        )

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

    def test_plots(self):
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)
        # fig1.show()

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

        self.monolayer.bottom_separator_overhang_left = 8
        self.assertEqual(
            self.monolayer.bottom_separator_overhangs,
            {"left": 8, "right": 2, "top": 3, "bottom": 3},
        )
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_top = 6
        self.assertEqual(
            self.monolayer.bottom_separator_overhangs,
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


class TestZFoldMonoLayer(unittest.TestCase):
    def setUp(self):
        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(
            name="super_P", specific_cost=15, density=2.0, color="#000000"
        )
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(
            name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
        )

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
            transverse=True,
        )

    def test_zfold_monolayer_basic(self):
        """Test basic Z-fold monolayer functionality."""
        self.assertTrue(isinstance(self.zfoldmonolayer, ZFoldMonoLayer))
        self.assertTrue(isinstance(self.zfoldmonolayer, MonoLayer))

        # Check that separator lengths are constrained correctly
        expected_bottom_length = (
            self.zfoldmonolayer.cathode.current_collector._x_body_length
            + 2 * self.zfoldmonolayer._bottom_separator._thickness
        ) * M_TO_MM
        expected_top_length = (
            self.zfoldmonolayer.anode.current_collector._x_body_length
            + 2 * self.zfoldmonolayer._top_separator._thickness
        ) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(
            self.zfoldmonolayer._top_separator.length, expected_top_length, places=1
        )

        self.assertEqual(
            self.zfoldmonolayer.anode_overhangs,
            {"left": 2, "right": 2, "top": 2, "bottom": 2},
        )
        self.assertEqual(
            self.zfoldmonolayer.separator_overhangs,
            {"left": 0.0, "right": 0.0, "bottom": 3.0, "top": 3.0},
        )

        fig1 = self.zfoldmonolayer.get_top_down_view()
        # fig1.show()

    def test_zfold_no_left_right_overhangs(self):
        """Test that left/right overhang properties are removed."""
        # These properties should not exist
        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.bottom_separator_overhang_left

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.bottom_separator_overhang_right

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.top_separator_overhang_left

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.top_separator_overhang_right

    def test_zfold_no_individual_separator_properties(self):
        """Test that individual separator properties raise AttributeError."""
        # Individual separator properties should not be accessible
        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.bottom_separator

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.top_separator

    def test_zfold_no_individual_overhang_properties(self):
        """Test that individual overhang properties raise AttributeError."""
        # Individual overhang properties should not be accessible
        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.bottom_separator_overhang_bottom

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.bottom_separator_overhang_top

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.top_separator_overhang_bottom

        with self.assertRaises(AttributeError):
            _ = self.zfoldmonolayer.top_separator_overhang_top

    def test_zfold_left_right_overhangs_always_zero(self):
        """Test that left/right overhangs are always zero in calculations."""
        # Check internal calculations set left/right to zero
        self.assertEqual(self.zfoldmonolayer._bottom_separator_overhang_left, 0.0)
        self.assertEqual(self.zfoldmonolayer._bottom_separator_overhang_right, 0.0)
        self.assertEqual(self.zfoldmonolayer._top_separator_overhang_left, 0.0)
        self.assertEqual(self.zfoldmonolayer._top_separator_overhang_right, 0.0)

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
        expected_bottom_length = (
            self.zfoldmonolayer.cathode.current_collector._x_body_length
            + 2 * new_separator._thickness
        ) * M_TO_MM
        expected_top_length = (
            self.zfoldmonolayer.anode.current_collector._x_body_length
            + 2 * new_separator._thickness
        ) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(
            self.zfoldmonolayer._top_separator.length, expected_top_length, places=1
        )

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
        expected_bottom_length = (
            self.zfoldmonolayer.cathode.current_collector._x_body_length
            + 2 * new_separator._thickness
        ) * M_TO_MM
        expected_top_length = (
            self.zfoldmonolayer.anode.current_collector._x_body_length
            + 2 * new_separator._thickness
        ) * M_TO_MM

        self.assertAlmostEqual(
            self.zfoldmonolayer._bottom_separator.length,
            expected_bottom_length,
            places=1,
        )
        self.assertAlmostEqual(
            self.zfoldmonolayer._top_separator.length, expected_top_length, places=1
        )
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


if __name__ == "__main__":
    unittest.main()
