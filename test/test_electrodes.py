from copy import deepcopy
import unittest
import plotly.graph_objects as go

from steer_opencell_design.Materials.Formulations import CathodeFormulation, AnodeFormulation
from steer_opencell_design.Components.Electrodes import Cathode, Anode

from steer_opencell_design.Components.CurrentCollectors.Notched import NotchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector, WeldTab
from steer_opencell_design.Components.CurrentCollectors.Punched import PunchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Tabless import TablessCurrentCollector

from steer_opencell_design.Materials.Other import CurrentCollectorMaterial, InsulationMaterial
from steer_opencell_design.Materials.ActiveMaterials import CathodeMaterial, AnodeMaterial
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive


class TestAnodeNoInsulation(unittest.TestCase):
    
    def setUp(self):
        current_collector_material = CurrentCollectorMaterial.from_database("Aluminum")
        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("PVDF")

        anode_current_collector = TablessCurrentCollector(
            material=current_collector_material,
            width=132,
            length=2427,
            coated_width=127,
            thickness=13,
        )

        anode_active_material = AnodeMaterial.from_database("Hard Carbon (Vendor A)")

        anode_formulation = AnodeFormulation(
            active_materials={anode_active_material: 95},
            binders={binder: 2.5},
            conductive_additives={conductive_additive: 2.5},
        )

        self.anode = Anode(
            formulation=anode_formulation,
            current_collector=anode_current_collector,
            calender_density=1.03,
            mass_loading=8.35,
        )

    def test_electrodes(self):
        self.assertTrue(isinstance(self.anode, Anode))

    def test_serialization(self):
        serialized = self.anode.serialize()
        deserialized = Anode.deserialize(serialized)
        test_case = self.anode == deserialized
        self.assertTrue(test_case)

    def test_equality(self):
        temp_electrode = deepcopy(self.anode)
        condition = temp_electrode == self.anode
        self.assertTrue(condition)

    def test_datum_shift_updates_coordinates(self):
        """Changing the electrode datum should translate top-down coating coordinates by the same delta.

        We shift the x component of the datum and verify all x coordinates of the coating trace
        shift accordingly (within floating point tolerance)."""
        # Get initial coordinates
        coating_trace_before = self.anode.top_down_coating_trace
        xs_before = list(coating_trace_before.x)
        old_datum = self.anode.datum
        shift_x = 100.0  # mm

        fig1 = self.anode.get_top_down_view()

        # Apply datum shift
        self.anode.datum = (old_datum[0] + shift_x, old_datum[1], old_datum[2])

        fig2 = self.anode.get_top_down_view()

        # Get new coordinates
        coating_trace_after = self.anode.top_down_coating_trace
        xs_after = list(coating_trace_after.x)

        # Sanity checks
        self.assertEqual(len(xs_before), len(xs_after), "Coordinate length should remain constant after shift")
        # Compute per-point shifts
        deltas = [after - before for before, after in zip(xs_before, xs_after)]
        # Assert all deltas approximately equal shift_x
        for d in deltas:
            self.assertAlmostEqual(d, shift_x, places=6, msg=f"Expected x shift {shift_x} mm, got {d} mm")

        # Additionally verify datum updated
        self.assertAlmostEqual(self.anode.datum[0] - old_datum[0], shift_x, places=6)

        # fig1.show()
        # fig2.show()

    def test_datum_shift_updates_coordinates_y(self):
        """Changing the electrode datum y should translate top-down coating coordinates y values by the same delta."""
        coating_trace_before = self.anode.top_down_coating_trace
        ys_before = list(coating_trace_before.y)
        old_datum = self.anode.datum
        shift_y = 75.0  # mm

        fig1 = self.anode.get_top_down_view()

        # Apply datum shift (y only)
        self.anode.datum = (old_datum[0], old_datum[1] + shift_y, old_datum[2])

        fig2 = self.anode.get_top_down_view()

        coating_trace_after = self.anode.top_down_coating_trace
        ys_after = list(coating_trace_after.y)

        self.assertEqual(len(ys_before), len(ys_after), "Coordinate length should remain constant after y shift")
        deltas = [after - before for before, after in zip(ys_before, ys_after)]
        for d in deltas:
            self.assertAlmostEqual(d, shift_y, places=6, msg=f"Expected y shift {shift_y} mm, got {d} mm")
        self.assertAlmostEqual(self.anode.datum[1] - old_datum[1], shift_y, places=6)

        # fig1.show()
        # fig2.show()
        

class TestCathodePunchedCurrentCollector(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        active_material1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        conductive_additive1 = ConductiveAdditive.from_database("Super P")
        conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        binder1 = Binder.from_database("PVDF")
        binder2 = Binder.from_database("CMC")

        formulation = CathodeFormulation(
            active_materials={
                active_material1: 90,
            },
            binders={binder1: 3, binder2: 2},
            conductive_additives={conductive_additive1: 3, conductive_additive2: 2},
        )

        cc_material = CurrentCollectorMaterial.from_database("Aluminum")

        current_collector = PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=280,
            thickness=12,
            tab_width=50,
            tab_height=30,
            tab_position=50,
            coated_tab_height=3,
            insulation_width=10,
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 95%")

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=25,
        )

    def test_electrodes(self):
        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.cathode.current_collector, PunchedCurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, CathodeFormulation))

        self.assertEqual(
            self.cathode.mass_breakdown,
            {
                "Coating": {
                    "NaNiMn P2-O3 Composite": 15.74,
                    "PVDF": 0.52,
                    "CMC": 0.35,
                    "Super P": 0.52,
                    "Graphite": 0.35,
                },
                "Current Collector": 2.77,
                "Electrical Insulation": 0.41,
            },
        )

        self.assertEqual(
            self.cathode.cost_breakdown,
            {
                "Coating": {
                    "NaNiMn P2-O3 Composite": 0.17,
                    "PVDF": 0.01,
                    "CMC": 0.0,
                    "Super P": 0.01,
                    "Graphite": 0.0,
                },
                "Current Collector": 0.03,
                "Electrical Insulation": 0.01,
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

        self.assertAlmostEqual(self.cathode._cost, sum_nested_dict(self.cathode._cost_breakdown), 5)
        self.assertAlmostEqual(self.cathode._mass, sum_nested_dict(self.cathode._mass_breakdown), 5)

        self.assertEqual(self.cathode.calender_density, 2.60)
        self.assertEqual(self.cathode.mass_loading, 10.68)
        self.assertEqual(self.cathode.insulation_thickness, 25)
        self.assertEqual(self.cathode.formulation.mass, 17.49)
        self.assertEqual(self.cathode.coating_thickness, 41.08)
        self.assertEqual(self.cathode.mass, 20.67)

    def test_breakdown_plots(self):
        plot_cost = self.cathode.plot_cost_breakdown(title="Cost Breakdown Plot")
        plot_mass = self.cathode.plot_mass_breakdown(title="Mass Breakdown Plot")
        # plot_cost.show()
        # plot_mass.show()

    def test_half_cell_curve(self):
        self.cathode.voltage_cutoff = 4.0
        voltage = self.cathode.formulation._capacity_curve[:, 1].max()
        self.assertEqual(voltage, 4.0)
        figure = self.cathode.plot_areal_capacity_curve()
        # figure.show()

    def test_views(self):

        figure0 = self.cathode.get_top_down_view()
        figure1 = self.cathode.get_top_down_view()
        figure2 = self.cathode.get_a_side_view()
        figure3 = self.cathode.get_b_side_view()
        figure4 = self.cathode.get_right_left_view()
        figure5 = self.cathode.get_cross_section()

        # figure0.show()
        # figure1.show()
        # figure2.show()
        # figure3.show()
        # figure4.show()
        # figure5.show()

    def test_flip(self):

        figure1 = self.cathode.get_top_down_view()
        self.cathode._flip("x")
        figure2 = self.cathode.get_top_down_view()
        self.cathode._flip("y")
        figure3 = self.cathode.get_top_down_view()

        # figure1.show()
        # figure2.show()
        # figure3.show()

    def test_datum_setter(self):

        figure1 = self.cathode.get_top_down_view()

        new_datum = (
            self.cathode._current_collector.x_foil_length,
            self.cathode._current_collector.y_foil_length,
            self.cathode._thickness * 1e3,
        )

        self.cathode.datum = new_datum

        figure2 = self.cathode.get_top_down_view()

        figure_top = go.Figure(data=figure1.data + figure2.data)

        # figure_top.show()

    def test_flip_and_setter(self):
        fig1 = self.cathode.get_top_down_view()

        self.cathode._flip("y")
        fig2 = self.cathode.get_top_down_view()

        current_collector = deepcopy(self.cathode.current_collector)
        current_collector.width = 400
        self.cathode.current_collector = current_collector
        fig3 = self.cathode.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_datum_shift_updates_coordinates_x(self):
        """Changing the cathode datum x should translate top-down coating coordinates x values by the same delta.

        Uses full top-down figure before and after to validate shift visually (data-level)."""
        fig_before = self.cathode.get_top_down_view()
        # Extract coating trace x values (trace name contains 'Coating')
        xs_before = None
        for trace in fig_before.data:
            if 'Coating' in trace.name:
                xs_before = list(trace.x)
                break
        self.assertIsNotNone(xs_before, "Could not find coating trace in pre-shift figure")

        old_datum = self.cathode.datum
        shift_x = 42.5  # mm
        self.cathode.datum = (old_datum[0] + shift_x, old_datum[1], old_datum[2])

        fig_after = self.cathode.get_top_down_view()
        xs_after = None
        for trace in fig_after.data:
            if 'Coating' in trace.name:
                xs_after = list(trace.x)
                break
        self.assertIsNotNone(xs_after, "Could not find coating trace in post-shift figure")

        self.assertEqual(len(xs_before), len(xs_after), "Coordinate length should remain constant after x shift")
        deltas = [after - before for before, after in zip(xs_before, xs_after)]
        for d in deltas:
            self.assertAlmostEqual(d, shift_x, places=6, msg=f"Expected x shift {shift_x} mm, got {d} mm")
        self.assertAlmostEqual(self.cathode.datum[0] - old_datum[0], shift_x, places=6)

        # fig_before.show()
        # fig_after.show()

    def test_datum_shift_updates_coordinates_y(self):
        """Changing the cathode datum y should translate top-down coating coordinates y values by the same delta.

        Uses full top-down figure before and after to validate shift visually (data-level)."""
        fig_before = self.cathode.get_top_down_view()
        ys_before = None
        for trace in fig_before.data:
            if 'Coating' in trace.name:
                ys_before = list(trace.y)
                break
        self.assertIsNotNone(ys_before, "Could not find coating trace in pre-shift figure")

        old_datum = self.cathode.datum
        shift_y = 33.3  # mm
        self.cathode.datum = (old_datum[0], old_datum[1] + shift_y, old_datum[2])

        fig_after = self.cathode.get_top_down_view()
        ys_after = None
        for trace in fig_after.data:
            if 'Coating' in trace.name:
                ys_after = list(trace.y)
                break
        self.assertIsNotNone(ys_after, "Could not find coating trace in post-shift figure")

        self.assertEqual(len(ys_before), len(ys_after), "Coordinate length should remain constant after y shift")
        deltas = [after - before for before, after in zip(ys_before, ys_after)]
        for d in deltas:
            self.assertAlmostEqual(d, shift_y, places=6, msg=f"Expected y shift {shift_y} mm, got {d} mm")
        self.assertAlmostEqual(self.cathode.datum[1] - old_datum[1], shift_y, places=6)

        # fig_before.show()
        # fig_after.show()


class TestCathodeTwoMaterialNotched(unittest.TestCase):
    def setUp(self):
        material1 = CathodeMaterial.from_database("LFP")
        material2 = CathodeMaterial.from_database("NMC811")
        material2.extrapolation_window = 0.5

        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("PVDF")

        formulation = CathodeFormulation(
            active_materials={material1: 67, material2: 28},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial.from_database("Copper")

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

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        self.cathode.voltage_cutoff = 4.1

    def test_electrodes(self):
        
        self.assertTrue(isinstance(self.cathode, Cathode))

        self.assertTrue(
            self.cathode.mass_breakdown,
            {
                "Formulation": {
                    "LFP": 110.66,
                    "NMC811": 46.25,
                    "PVDF": 3.3,
                    "Super P": 4.96,
                },
                "Current Collector": 98.51,
                "Electrical Insulation": 1.6,
            },
        )

        self.assertTrue(
            self.cathode.cost_breakdown,
            {
                "Formulation": {
                    "LFP": 0.66,
                    "NMC811": 1.16,
                    "PVDF": 0.04,
                    "Super P": 0.07,
                },
                "Current Collector": 1.78,
                "Electrical Insulation": 0.18,
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

        self.assertAlmostEqual(self.cathode._cost, sum_nested_dict(self.cathode._cost_breakdown), 5)
        self.assertAlmostEqual(self.cathode._mass, sum_nested_dict(self.cathode._mass_breakdown), 5)

    def test_half_cell_curve(self):
        figure1 = self.cathode.plot_areal_capacity_curve()
        figure2 = self.cathode.plot_areal_capacity_curve()
        # figure1.show()
        # figure2.show()

    def test_views(self):
        figure1 = self.cathode.get_a_side_view()
        figure2 = self.cathode.get_b_side_view()
        # figure1.show()
        # figure2.show()


class testAnodeTabWelded(unittest.TestCase):

    def setUp(self):
        active_material = AnodeMaterial.from_database("Synthetic Graphite")
        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("CMC")

        formulation = AnodeFormulation(
            active_materials={active_material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        tab_material = CurrentCollectorMaterial.from_database("Copper")

        tab = WeldTab(material=tab_material, width=10, length=110, thickness=10)

        cc_material = CurrentCollectorMaterial.from_database("Copper")

        current_collector = TabWeldedCurrentCollector(
            material=cc_material,
            length=3000,
            width=160,
            thickness=10,
            weld_tab=tab,
            weld_tab_positions=[40, 400, 2800],
            skip_coat_width=30,
            tab_overhang=30,
            tab_weld_side="a",
        )

        self.anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60,
        )

        self.anode.voltage_cutoff = 0.02

    def test_electrodes(self):
        self.assertTrue(isinstance(self.anode, Anode))
        self.assertTrue(isinstance(self.anode.current_collector, TabWeldedCurrentCollector))
        self.assertTrue(isinstance(self.anode.formulation, AnodeFormulation))

        self.assertEqual(
            self.anode.mass_breakdown,
            {
                "Coating": {
                    "Synthetic Graphite": 89.51,
                    "CMC": 4.97,
                    "Super P": 4.97,
                },
                "Current Collector": 43.6,
            },
        )

        self.assertEqual(
            self.anode.cost_breakdown,
            {
                "Coating": {
                    "Synthetic Graphite": 0.22,
                    "CMC": 0.01,
                    "Super P": 0.07,
                },
                "Current Collector": 0.79,
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

        self.assertAlmostEqual(self.anode._cost, sum_nested_dict(self.anode._cost_breakdown), 5)
        self.assertAlmostEqual(self.anode._mass, sum_nested_dict(self.anode._mass_breakdown), 5)

    def test_equality(self):
        temp_electrode = deepcopy(self.anode)
        condition = temp_electrode == self.anode
        self.assertTrue(condition)

    def test_half_cell_curve(self):
        figure1 = self.anode.plot_areal_capacity_curve()
        # figure1.show()

    def test_views(self):
        figure1 = self.anode.get_a_side_view()
        figure2 = self.anode.get_b_side_view()
        figure3 = self.anode.get_top_down_view()

        # figure1.show()
        # figure2.show()
        # figure3.show()


class TestElectrodeControlModes(unittest.TestCase):
    """Test the electrode control mode system."""

    def setUp(self):
        """Set up test fixtures for control mode testing."""
        # Create test materials
        active_material = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("PVDF")

        self.formulation = CathodeFormulation(
            active_materials={active_material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        cc_material = CurrentCollectorMaterial.from_database("Aluminum")

        self.current_collector = PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=280,
            thickness=12,
            tab_width=50,
            tab_height=30,
            tab_position=50,
            coated_tab_height=3,
            insulation_width=0,  # No insulation to avoid database dependency
        )

        # Create test electrode with known initial values
        self.cathode = Cathode(
            formulation=self.formulation,
            mass_loading=20.0,  # mg/cm²
            current_collector=self.current_collector,
            calender_density=2.5,  # g/cm³
        )

    def test_default_control_mode(self):
        """Test that default control mode is MAINTAIN_CALENDER_DENSITY."""
        from steer_opencell_design.Components.Electrodes import ElectrodeControlMode

        self.assertEqual(self.cathode._control_mode, ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY)

        # Test default behavior - coating thickness change should adjust mass loading
        initial_calender_density = self.cathode.calender_density
        initial_coating_thickness = self.cathode.coating_thickness
        initial_mass_loading = self.cathode.mass_loading

        # Change coating thickness
        new_coating_thickness = initial_coating_thickness * 1.2
        self.cathode.coating_thickness = new_coating_thickness

        # Calender density should remain the same (within tolerance)
        self.assertAlmostEqual(self.cathode.calender_density, initial_calender_density, places=6)

        # Mass loading should have changed proportionally
        expected_mass_loading = initial_mass_loading * 1.2
        self.assertAlmostEqual(self.cathode.mass_loading, expected_mass_loading, places=2)

    def test_maintain_mass_loading_mode(self):
        """Test MAINTAIN_MASS_LOADING control mode."""
        from steer_opencell_design.Components.Electrodes import ElectrodeControlMode

        # Switch to maintain mass loading mode
        self.cathode.control_mode = ElectrodeControlMode.MAINTAIN_MASS_LOADING

        initial_mass_loading = self.cathode.mass_loading
        initial_coating_thickness = self.cathode.coating_thickness
        initial_calender_density = self.cathode.calender_density

        # Test 1: Change coating thickness -> should adjust calender density
        new_coating_thickness = initial_coating_thickness * 1.5
        self.cathode.coating_thickness = new_coating_thickness

        # Mass loading should remain the same
        self.assertAlmostEqual(self.cathode.mass_loading, initial_mass_loading, places=6)

        # Calender density should have changed
        expected_calender_density = initial_calender_density / 1.5
        self.assertAlmostEqual(self.cathode.calender_density, expected_calender_density, places=2)

        # Test 2: Change calender density -> should adjust coating thickness
        current_coating_thickness = self.cathode.coating_thickness
        new_calender_density = self.cathode.calender_density * 1.3
        self.cathode.calender_density = new_calender_density

        # Mass loading should remain the same
        self.assertAlmostEqual(self.cathode.mass_loading, initial_mass_loading, places=6)

        # Coating thickness should have changed
        expected_coating_thickness = current_coating_thickness / 1.3
        self.assertAlmostEqual(self.cathode.coating_thickness, expected_coating_thickness, delta=0.5)

    def test_maintain_coating_thickness_mode(self):
        """Test MAINTAIN_COATING_THICKNESS control mode."""
        from steer_opencell_design.Components.Electrodes import ElectrodeControlMode

        # Switch to maintain coating thickness mode
        self.cathode.control_mode = ElectrodeControlMode.MAINTAIN_COATING_THICKNESS

        initial_mass_loading = self.cathode.mass_loading
        initial_coating_thickness = self.cathode.coating_thickness
        initial_calender_density = self.cathode.calender_density

        # Test 1: Change mass loading -> should adjust calender density
        new_mass_loading = initial_mass_loading * 1.4
        self.cathode.mass_loading = new_mass_loading

        # Coating thickness should remain the same
        self.assertAlmostEqual(self.cathode.coating_thickness, initial_coating_thickness, places=6)

        # Calender density should have changed
        expected_calender_density = initial_calender_density * 1.4
        self.assertAlmostEqual(self.cathode.calender_density, expected_calender_density, places=4)

        # Test 2: Change calender density -> should adjust mass loading
        current_mass_loading = self.cathode.mass_loading
        new_calender_density = self.cathode.calender_density * 0.8
        self.cathode.calender_density = new_calender_density

        # Coating thickness should remain the same
        self.assertAlmostEqual(self.cathode.coating_thickness, initial_coating_thickness, places=6)

        # Mass loading should have changed
        expected_mass_loading = current_mass_loading * 0.8
        self.assertAlmostEqual(self.cathode.mass_loading, expected_mass_loading, places=2)

    def test_coating_thickness_setter_with_maintain_coating_thickness_mode(self):
        """Test that coating thickness setter works correctly in MAINTAIN_COATING_THICKNESS mode."""
        from steer_opencell_design.Components.Electrodes import ElectrodeControlMode

        # Set up electrode in MAINTAIN_COATING_THICKNESS mode
        self.cathode.control_mode = ElectrodeControlMode.MAINTAIN_COATING_THICKNESS

        # Get initial values
        initial_coating_thickness = self.cathode.coating_thickness
        initial_mass_loading = self.cathode.mass_loading
        initial_calender_density = self.cathode.calender_density

        # Try to change coating thickness
        new_coating_thickness = initial_coating_thickness * 1.5
        self.cathode.coating_thickness = new_coating_thickness

        # Coating thickness should have changed
        self.assertAlmostEqual(self.cathode.coating_thickness, new_coating_thickness, places=1)

        # In MAINTAIN_COATING_THICKNESS mode, neither mass loading nor calender density
        # should automatically adjust to this change - it should be an independent setting
        # (though the physics relationship may be temporarily broken)

        # At minimum, the coating thickness should actually be set to the new value
        self.assertNotEqual(self.cathode.coating_thickness, initial_coating_thickness)

    def test_coating_thickness_setter_in_other_modes(self):
        """Test that coating thickness setter still works correctly in other control modes."""
        from steer_opencell_design.Components.Electrodes import ElectrodeControlMode

        # Test MAINTAIN_CALENDER_DENSITY mode (default)
        self.cathode.control_mode = ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY

        initial_coating_thickness = self.cathode.coating_thickness
        initial_calender_density = self.cathode.calender_density

        # Change coating thickness
        new_coating_thickness = initial_coating_thickness * 1.2
        self.cathode.coating_thickness = new_coating_thickness

        # Coating thickness should change
        self.assertAlmostEqual(self.cathode.coating_thickness, new_coating_thickness, places=1)

        # Calender density should remain constant (within tolerance)
        self.assertAlmostEqual(self.cathode.calender_density, initial_calender_density, places=5)

        # Test MAINTAIN_MASS_LOADING mode
        self.cathode.control_mode = ElectrodeControlMode.MAINTAIN_MASS_LOADING

        initial_mass_loading = self.cathode.mass_loading
        initial_coating_thickness = self.cathode.coating_thickness

        # Change coating thickness
        new_coating_thickness_2 = initial_coating_thickness * 1.3
        self.cathode.coating_thickness = new_coating_thickness_2

        # Coating thickness should change
        self.assertAlmostEqual(self.cathode.coating_thickness, new_coating_thickness_2, places=1)

        # Mass loading should remain constant (within tolerance)
        self.assertAlmostEqual(self.cathode.mass_loading, initial_mass_loading, places=5)

    def test_areal_capacity_curve_scales_with_mass_loading(self):
        """Test that areal capacity curve scales proportionally when mass_loading changes."""
        # Get initial areal capacity curve
        initial_mass_loading = self.cathode.mass_loading
        initial_curve = self.cathode.areal_capacity_curve
        initial_max_capacity = initial_curve["Areal Capacity (mAh/cm²)"].max()
        
        # Change mass loading by a known factor
        scaling_factor = 1.5
        new_mass_loading = initial_mass_loading * scaling_factor
        self.cathode.mass_loading = new_mass_loading
        
        # Get new areal capacity curve
        new_curve = self.cathode.areal_capacity_curve
        new_max_capacity = new_curve["Areal Capacity (mAh/cm²)"].max()
        
        # Assert that max capacity scaled proportionally
        expected_max_capacity = initial_max_capacity * scaling_factor
        self.assertAlmostEqual(new_max_capacity, expected_max_capacity, places=2)
        
        # Assert that the number of points in the curve remains the same
        self.assertEqual(len(initial_curve), len(new_curve))
        
        # Assert that voltage values remain unchanged
        self.assertTrue((initial_curve["Voltage (V)"] == new_curve["Voltage (V)"]).all())
        
        # Assert that all capacity values scaled by the same factor
        capacity_ratio = new_curve["Areal Capacity (mAh/cm²)"] / initial_curve["Areal Capacity (mAh/cm²)"]
        self.assertTrue((capacity_ratio - scaling_factor).abs().max() < 0.01)












