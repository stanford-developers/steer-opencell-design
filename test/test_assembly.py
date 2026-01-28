import time
import unittest
import pandas as pd
from copy import deepcopy

from steer_opencell_design import (
    CathodeFormulation, AnodeFormulation,
    Cathode, Anode,
    Separator,
    NotchedCurrentCollector, PunchedCurrentCollector, TablessCurrentCollector, TabWeldedCurrentCollector, WeldTab,
    PunchedStack, ZFoldStack,
    WoundJellyRoll, FlatWoundJellyRoll,
    RoundMandrel, FlatMandrel,
    Tape,
    MonoLayer, ZFoldMonoLayer,
    Laminate,
    CathodeMaterial, AnodeMaterial,
    Binder,
    ConductiveAdditive,
    CurrentCollectorMaterial, SeparatorMaterial, InsulationMaterial, TapeMaterial
)


class TestRoundJellyRoll(unittest.TestCase):
    
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
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        cathode = Cathode(
            formulation=formulation,
            mass_loading=12,
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
            bare_lengths_a_side=(200, 300),
            bare_lengths_b_side=(150, 250),
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=current_collector,
            calender_density=1.1,
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

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=5000)

        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=7000)

        layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = RoundMandrel(
            diameter=5, 
            length=350,
        )

        tape_material = TapeMaterial.from_database("Kapton")
        tape_material.density = 1.42
        tape_material.specific_cost = 70

        tape = Tape(
            material = tape_material,
            thickness=30
        )

        self.my_jellyroll = WoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=5,
        )

    def test_basics(self):
        self.assertTrue(type(self.my_jellyroll), WoundJellyRoll)
        self.assertAlmostEqual(self.my_jellyroll.radius, 20.8, 1)
        self.assertAlmostEqual(self.my_jellyroll.diameter, 41.6, 1)
        self.assertAlmostEqual(self.my_jellyroll.interfacial_area, 23895, 0)
        self.assertAlmostEqual(self.my_jellyroll.cost, 4.33, 2)
        self.assertAlmostEqual(self.my_jellyroll.radius_range[0], 8.73, 2)
        self.assertAlmostEqual(self.my_jellyroll.radius_range[1], 30.55, 2)
        self.assertAlmostEqual(self.my_jellyroll.mass, 655.4, 1)

    def test_serialization(self):
        serialized = self.my_jellyroll.serialize()
        deserialized = WoundJellyRoll.deserialize(serialized)
        test_case = self.my_jellyroll == deserialized
        self.assertTrue(test_case)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, WoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig3 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig4 = self.my_jellyroll.get_capacity_plot()
        fig5 = self.my_jellyroll.plot_mass_breakdown()
        fig6 = self.my_jellyroll.plot_cost_breakdown()
        fig7 = self.my_jellyroll.get_top_down_view()
        fig8 = self.my_jellyroll.get_side_view()

        # fig1.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()
        # fig6.show()
        # fig7.show()
        # fig8.show()

    def test_datum_set(self):

        original_datum = self.my_jellyroll.datum

        new_datum = (50.0, 60.0, 70.0)

        self.my_jellyroll.datum = new_datum

        self.assertEqual(self.my_jellyroll.datum, new_datum)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig2 = self.my_jellyroll.get_top_down_view()
        fig3 = self.my_jellyroll.get_side_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_top_down_view(self):
        
        fig1 = self.my_jellyroll.get_top_down_view()

        # now change the cathode cc to a tabless current collector
        cathode_current_collector = TablessCurrentCollector.from_notched(self.my_jellyroll._layup._cathode._current_collector)
        self.my_jellyroll._layup._cathode.current_collector = cathode_current_collector
        self.my_jellyroll._layup.cathode = self.my_jellyroll._layup._cathode
        self.my_jellyroll.layup = self.my_jellyroll._layup
        fig2 = self.my_jellyroll.get_top_down_view()

        # now change the cathode cc to a tab welded current collector
        cathode_current_collector = TabWeldedCurrentCollector.from_tabless(self.my_jellyroll._layup._cathode._current_collector)
        self.my_jellyroll._layup._cathode.current_collector = cathode_current_collector
        self.my_jellyroll._layup.cathode = self.my_jellyroll._layup._cathode
        self.my_jellyroll.layup = self.my_jellyroll._layup
        fig3 = self.my_jellyroll.get_top_down_view()

        # now also convert the anode cc to a tab welded current collector
        anode_current_collector = TabWeldedCurrentCollector.from_notched(self.my_jellyroll._layup._anode._current_collector)
        self.my_jellyroll._layup._anode.current_collector = anode_current_collector
        self.my_jellyroll._layup.anode = self.my_jellyroll._layup._anode
        self.my_jellyroll.layup = self.my_jellyroll._layup
        fig4 = self.my_jellyroll.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_high_res_spiral(self):

        fig1 = self.my_jellyroll.get_spiral_plot()
        self.my_jellyroll.calculate_high_resolution_roll()
        fig2 = self.my_jellyroll.get_spiral_plot()

        # fig1.show()
        # fig2.show()

    def test_roll_properties(self):
        """Test that roll_properties returns a properly formatted DataFrame with expected values."""
        
        # Test that roll_properties is a pandas DataFrame
        self.assertIsInstance(self.my_jellyroll.roll_properties, pd.DataFrame)
        
        expected_data = {
            'Anode A Side Coating Turns': 50.12,
            'Anode Current Collector Turns': 59.09,
            'Anode B Side Coating Turns': 52.1,
            'Cathode A Side Coating Turns': 59.09,
            'Cathode Current Collector Turns': 59.09,
            'Cathode B Side Coating Turns': 59.09,
            'Bottom Separator Turns': 129.58,
            'Bottom Separator Inner Turns': 67.36,
            'Bottom Separator Outer Turns': 11.66,
            'Top Separator Turns': 70.99,
            'Top Separator Inner Turns': 16.55,
            'Top Separator Outer Turns': 3.94
        }
        
        expected_df = pd.DataFrame.from_dict(expected_data, orient='index', columns=['Turns'])
        expected_df.index.name = 'Component'
        
        # Get actual DataFrame
        actual_df = self.my_jellyroll.roll_properties
        
        # Test DataFrame structure
        self.assertEqual(actual_df.columns.tolist(), ['Turns'])
        
        # Test that all expected components are present
        for component in expected_data.keys():
            self.assertIn(component, actual_df.index, f"Missing component: {component}")
        
        # Test values (rounded to 2 decimal places)
        for component, expected_value in expected_data.items():
            actual_value = actual_df.loc[component, 'Turns']
            self.assertAlmostEqual(
                actual_value, 
                expected_value, 
                places=1, 
                msg=f"Component {component}: expected {expected_value}, got {actual_value}"
            )

    def test_radius_setter(self):
        """Test that setting the radius updates the diameter correctly."""
        original_radius = self.my_jellyroll.radius

        # Set a new radius
        new_radius = original_radius + 5.0
        self.my_jellyroll.radius = new_radius

        # Check that diameter updated correctly
        self.assertAlmostEqual(self.my_jellyroll.radius, new_radius, 0)
        self.assertAlmostEqual(self.my_jellyroll.diameter, new_radius * 2, 0)
        self.assertAlmostEqual(self.my_jellyroll.cost, 6.6, 1)

    def test_to_flat_jelly_roll(self):

        flat_jellyroll = FlatWoundJellyRoll.from_round_jelly_roll(self.my_jellyroll)

        self.assertAlmostEqual(flat_jellyroll.interfacial_area, 23895, 0)
        self.assertAlmostEqual(flat_jellyroll.cost, 4.53, 2)
        self.assertAlmostEqual(flat_jellyroll.thickness, 19.38, 1)
        self.assertAlmostEqual(flat_jellyroll.width, 75.93, 1)

        figure = flat_jellyroll.get_spiral_plot()
        # figure.show()

    def test_breakdowns(self):
        """Test that mass_breakdown and cost_breakdown return expected values."""
        
        expected_mass_breakdown = {
            'Anode': {
                'Coating': {
                    'Synthetic Graphite': 158.51, 
                    'CMC': 8.81, 
                    'super_P': 8.81
                }, 
                'Current Collector': 30.79, 
                'Electrical Insulation': 1.63
            }, 
            'Cathode': {
                'Coating': {
                    'LFP': 303.7, 
                    'CMC': 6.39, 
                    'super_P': 9.59
                }, 
                'Current Collector': 29.68, 
                'Electrical Insulation': 1.6
            }, 
            'Separators': 87.42
        }
        
        expected_cost_breakdown = {
            'Anode': {
                'Coating': {
                    'Synthetic Graphite': 0.63, 
                    'CMC': 0.09, 
                    'super_P': 0.13
                }, 
                'Current Collector': 0.15, 
                'Electrical Insulation': 0.19
            }, 
            'Cathode': {
                'Coating': {
                    'LFP': 1.82, 
                    'CMC': 0.06, 
                    'super_P': 0.14
                }, 
                'Current Collector': 0.15, 
                'Electrical Insulation': 0.18
            }, 
            'Separators': 0.17
        }
        
        # Helper function to recursively compare nested dictionaries
        def assert_breakdown_values(actual, expected, breakdown_type, places=2):
            for key, value in expected.items():
                self.assertIn(key, actual, f"Missing key '{key}' in {breakdown_type}")
                if isinstance(value, dict):
                    # Recursive call for nested dictionaries
                    assert_breakdown_values(actual[key], value, f"{breakdown_type}['{key}']", places)
                else:
                    # Compare numeric values
                    self.assertAlmostEqual(
                        actual[key], 
                        value, 
                        places=places,
                        msg=f"{breakdown_type}['{key}']: expected {value}, got {actual[key]}"
                    )
        
        # Test mass breakdown
        actual_mass_breakdown = self.my_jellyroll.mass_breakdown
        assert_breakdown_values(actual_mass_breakdown, expected_mass_breakdown, "mass_breakdown")
        
        # Test cost breakdown
        actual_cost_breakdown = self.my_jellyroll.cost_breakdown
        assert_breakdown_values(actual_cost_breakdown, expected_cost_breakdown, "cost_breakdown")

    def test_mandrel_setting(self):

        new_jellyroll = deepcopy(self.my_jellyroll)

        new_jellyroll.mandrel.diameter = 10
        new_jellyroll.mandrel = new_jellyroll.mandrel
        self.assertAlmostEqual(new_jellyroll.radius, 21.26, 1)

        new_jellyroll.mandrel.radius = 10
        new_jellyroll.mandrel = new_jellyroll.mandrel
        self.assertAlmostEqual(new_jellyroll.radius, 22.97, 1)

    def test_current_collector_length_set(self):
        """Test that setting the current collector length updates the jellyroll properties."""
        self.my_jellyroll.layup.cathode.current_collector.length = 2000
        self.my_jellyroll.layup.cathode.current_collector = self.my_jellyroll.layup.cathode.current_collector
        self.my_jellyroll.layup.cathode = self.my_jellyroll.layup.cathode
        self.my_jellyroll.layup = self.my_jellyroll.layup
        self.assertEqual(self.my_jellyroll.layup.cathode.current_collector.length, 2000)

    def test_tape_setter(self):

        original_radius = self.my_jellyroll._radius
        original_cost = self.my_jellyroll._cost
        original_figure = self.my_jellyroll.get_spiral_plot()

        new_tape_material = TapeMaterial.from_database("Polyester")
        new_tape_material.density = 1.38
        new_tape_material.specific_cost = 10
        self.my_jellyroll.tape.material = new_tape_material
        self.my_jellyroll.tape = self.my_jellyroll.tape

        new_cost = self.my_jellyroll._cost
        self.assertTrue(new_cost < original_cost)

        self.my_jellyroll.tape.thickness = 10
        self.my_jellyroll.tape = self.my_jellyroll.tape
        
        new_radius = self.my_jellyroll._radius
        self.assertTrue(new_radius < original_radius)

        new_figure = self.my_jellyroll.get_spiral_plot()

        # original_figure.show()
        # new_figure.show()

    def test_additional_wraps_setter(self):
        original_radius = self.my_jellyroll._radius
        original_cost = self.my_jellyroll._cost
        original_figure = self.my_jellyroll.get_spiral_plot()

        self.my_jellyroll.additional_tape_wraps = 20

        new_radius = self.my_jellyroll._radius
        new_cost = self.my_jellyroll._cost
        new_figure = self.my_jellyroll.get_spiral_plot()

        self.assertTrue(new_radius > original_radius)
        self.assertTrue(new_cost > original_cost)

        # original_figure.show()
        # new_figure.show()

    def test_set_wraps_to_zero(self):

        original_length = self.my_jellyroll._tape._length
        original_tape_wraps = self.my_jellyroll._additional_tape_wraps
        original_cost = self.my_jellyroll._cost
        original_mass = self.my_jellyroll._mass
    
        self.my_jellyroll.additional_tape_wraps = 0

        new_length = self.my_jellyroll._tape._length
        new_tape_wraps = self.my_jellyroll._additional_tape_wraps
        new_cost = self.my_jellyroll._cost
        new_mass = self.my_jellyroll._mass

        self.assertEqual(new_tape_wraps, 0)
        self.assertTrue(new_length < original_length)
        self.assertTrue(new_cost < original_cost)
        self.assertTrue(new_mass < original_mass)

    def test_tape_length_setter(self):

        original_length = self.my_jellyroll._tape._length
        original_tape_wraps = self.my_jellyroll._additional_tape_wraps
        original_cost = self.my_jellyroll._cost
        original_mass = self.my_jellyroll._mass

        self.my_jellyroll.tape.length = 2000
        self.my_jellyroll.tape = self.my_jellyroll.tape

        new_length = self.my_jellyroll._tape._length
        new_tape_wraps = self.my_jellyroll._additional_tape_wraps
        new_cost = self.my_jellyroll._cost
        new_mass = self.my_jellyroll._mass

        self.assertTrue(new_length > original_length)
        self.assertTrue(new_tape_wraps > original_tape_wraps)
        self.assertTrue(new_cost > original_cost)
        self.assertTrue(new_mass > original_mass)
        

class TestFlatJellyRoll(unittest.TestCase):
    
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
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        cathode = Cathode(
            formulation=formulation,
            mass_loading=12,
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
            bare_lengths_a_side=(200, 300),
            bare_lengths_b_side=(150, 250),
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=current_collector,
            calender_density=1.15,
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

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=5000)

        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=7000)

        layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = FlatMandrel(
            length=350,
            width=100,
            height=5
        )

        tape_material = TapeMaterial.from_database("Kapton")
        tape_material.density = 1.42
        tape_material.specific_cost = 70

        tape = Tape(
            material = tape_material,
            thickness=30
        )

        self.my_jellyroll = FlatWoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=2
        )

    def test_basics(self):
        self.assertTrue(type(self.my_jellyroll), WoundJellyRoll)
        self.assertAlmostEqual(self.my_jellyroll.thickness, 12.5, 1)
        self.assertAlmostEqual(self.my_jellyroll.width, 114.1, 1)
        self.assertAlmostEqual(self.my_jellyroll.cost, 4.18, 1)
        self.assertAlmostEqual(self.my_jellyroll.interfacial_area, 23725.74, 0)
        self.assertAlmostEqual(self.my_jellyroll.thickness_range[0], 2.91, 1)
        self.assertAlmostEqual(self.my_jellyroll.thickness_range[1], 24.37, 1)
        self.assertAlmostEqual(self.my_jellyroll.width_range[0], 104.48, 1)
        self.assertAlmostEqual(self.my_jellyroll.width_range[1], 125.95, 1)

    def test_serialization(self):
        serialized = self.my_jellyroll.serialize()
        deserialized = FlatWoundJellyRoll.deserialize(serialized)
        test_case = self.my_jellyroll == deserialized
        self.assertTrue(test_case)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, FlatWoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig3 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig4 = self.my_jellyroll.get_capacity_plot()
        fig5 = self.my_jellyroll.plot_mass_breakdown()
        fig6 = self.my_jellyroll.plot_cost_breakdown()
        fig7 = self.my_jellyroll.get_top_down_view()
        fig8 = self.my_jellyroll.get_side_view()

        # fig1.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()
        # fig6.show()
        # fig7.show()
        # fig8.show()

    def test_datum_set(self):

        original_datum = self.my_jellyroll.datum

        new_datum = (50.0, 60.0, 70.0)

        self.my_jellyroll.datum = new_datum

        self.assertEqual(self.my_jellyroll.datum, new_datum)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig2 = self.my_jellyroll.get_top_down_view()
        fig3 = self.my_jellyroll.get_side_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_high_res_spiral(self):

        fig1 = self.my_jellyroll.get_spiral_plot()
        self.my_jellyroll.calculate_high_resolution_roll()
        fig2 = self.my_jellyroll.get_spiral_plot()

        # fig1.show()
        # fig2.show()

    def test_roll_properties(self):
        """Test that roll_properties returns a properly formatted DataFrame with expected values."""
        
        # Test that roll_properties is a pandas DataFrame
        self.assertIsInstance(self.my_jellyroll.roll_properties, pd.DataFrame)
        
        expected_data = {
            'Anode A Side Coating Turns': 17.87,
            'Anode Current Collector Turns': 20.04,
            'Anode B Side Coating Turns': 18.28,
            'Cathode A Side Coating Turns': 20.04,
            'Cathode Current Collector Turns': 20.04,
            'Cathode B Side Coating Turns': 20.04,
            'Bottom Separator Turns': 31.32,
            'Bottom Separator Inner Turns': 7.03,
            'Bottom Separator Outer Turns': 6.24,
            'Top Separator Turns': 22.31,
            'Top Separator Inner Turns': 2.16,
            'Top Separator Outer Turns': 2.09
        }

        expected_df = pd.DataFrame.from_dict(expected_data, orient='index', columns=['Turns'])
        expected_df.index.name = 'Component'
        
        # Get actual DataFrame
        actual_df = self.my_jellyroll.roll_properties
        
        # Test DataFrame structure
        self.assertEqual(actual_df.columns.tolist(), ['Turns'])

        # Test that all expected components are present
        for component in expected_data.keys():
            self.assertIn(component, actual_df.index, f"Missing component: {component}")
        
        # Test values (rounded to 2 decimal places)
        for component, expected_value in expected_data.items():
            actual_value = actual_df.loc[component, 'Turns']
            self.assertAlmostEqual(
                actual_value, 
                expected_value, 
                places=1, 
                msg=f"Component {component}: expected {expected_value}, got {actual_value}"
            )

    def test_thickness_setter(self):
        """Test that setting the thickness updates the width correctly."""
        original_thickness = self.my_jellyroll.thickness

        # Set a new thickness
        new_thickness = original_thickness + 5.0
        self.my_jellyroll.thickness = new_thickness

        # Check that width updated correctly
        self.assertAlmostEqual(self.my_jellyroll.thickness, new_thickness, 1)

    def test_width_setter(self):
        """Test that setting the width updates the thickness correctly."""
        original_width = self.my_jellyroll.width

        # Set a new width
        new_width = original_width + 2
        self.my_jellyroll.width = new_width

        # Check that thickness updated correctly
        self.assertAlmostEqual(self.my_jellyroll.width, new_width, 0)

    def test_to_wound_jelly_roll(self):
        """Test converting a FlatWoundJellyRoll to a WoundJellyRoll."""

        wound_jellyroll = WoundJellyRoll.from_flat_wound_jelly_roll(self.my_jellyroll)

        self.assertIsInstance(wound_jellyroll, WoundJellyRoll)
        self.assertAlmostEqual(wound_jellyroll.interfacial_area, 23895, 0)
        self.assertAlmostEqual(wound_jellyroll.cost, 3.97, 1)
        self.assertAlmostEqual(wound_jellyroll.radius, 20.54, 1)
        self.assertAlmostEqual(wound_jellyroll.diameter, 41.08, 1)

        figure = wound_jellyroll.get_spiral_plot()
        # figure.show()

    def test_tape_setter(self):
        """Test that changing the tape material updates cost and geometry correctly."""
        original_thickness = self.my_jellyroll._thickness
        original_cost = self.my_jellyroll._cost
        original_figure = self.my_jellyroll.get_spiral_plot()

        # Change tape material to a cheaper option
        new_tape_material = TapeMaterial.from_database("Polyester")
        new_tape_material.density = 1.38
        new_tape_material.specific_cost = 10
        self.my_jellyroll.tape.material = new_tape_material
        self.my_jellyroll.tape = self.my_jellyroll.tape

        new_cost = self.my_jellyroll._cost
        self.assertTrue(new_cost < original_cost)

        # Change tape thickness to a smaller value
        self.my_jellyroll.tape.thickness = 10
        self.my_jellyroll.tape = self.my_jellyroll.tape
        
        new_thickness = self.my_jellyroll._thickness
        self.assertTrue(new_thickness < original_thickness)

        new_figure = self.my_jellyroll.get_spiral_plot()

        # original_figure.show()
        # new_figure.show()

    def test_additional_wraps_setter(self):
        """Test that changing additional tape wraps updates geometry and cost correctly."""
        original_thickness = self.my_jellyroll._thickness
        original_cost = self.my_jellyroll._cost
        original_tape_length = self.my_jellyroll._tape._length
        original_figure = self.my_jellyroll.get_spiral_plot()

        # Increase additional tape wraps
        self.my_jellyroll.additional_tape_wraps = 20

        new_thickness = self.my_jellyroll._thickness
        new_cost = self.my_jellyroll._cost
        new_tape_length = self.my_jellyroll._tape._length
        new_figure = self.my_jellyroll.get_spiral_plot()

        self.assertTrue(new_thickness > original_thickness)
        self.assertTrue(new_cost > original_cost)
        self.assertTrue(new_tape_length > original_tape_length)

        # original_figure.show()
        # new_figure.show()

    def test_set_wraps_to_zero(self):

        original_length = self.my_jellyroll._tape._length
        original_tape_wraps = self.my_jellyroll._additional_tape_wraps
        original_cost = self.my_jellyroll._cost
        original_mass = self.my_jellyroll._mass
    
        self.my_jellyroll.additional_tape_wraps = 0

        new_length = self.my_jellyroll._tape._length
        new_tape_wraps = self.my_jellyroll._additional_tape_wraps
        new_cost = self.my_jellyroll._cost
        new_mass = self.my_jellyroll._mass

        self.assertEqual(new_tape_wraps, 0)
        self.assertTrue(new_length < original_length)
        self.assertTrue(new_cost < original_cost)
        self.assertTrue(new_mass < original_mass)

    def test_tape_length_setter(self):

        original_length = self.my_jellyroll._tape._length
        original_tape_wraps = self.my_jellyroll._additional_tape_wraps
        original_cost = self.my_jellyroll._cost
        original_mass = self.my_jellyroll._mass

        self.my_jellyroll.tape.length = 2000
        self.my_jellyroll.tape = self.my_jellyroll.tape

        new_length = self.my_jellyroll._tape._length
        new_tape_wraps = self.my_jellyroll._additional_tape_wraps
        new_cost = self.my_jellyroll._cost
        new_mass = self.my_jellyroll._mass

        self.assertTrue(new_length > original_length)
        self.assertTrue(new_tape_wraps > original_tape_wraps)
        self.assertTrue(new_cost > original_cost)
        self.assertTrue(new_mass > original_mass)


class TestPunchedStack(unittest.TestCase):
    """Tests for the PunchedStack electrode assembly built from a MonoLayer."""

    def setUp(self):
        # Replicate MonoLayer setup similar to TestSimpleMonoLayer in test_layups
        cathode_active = CathodeMaterial.from_database("LFP")
        cathode_active.specific_cost = 6
        cathode_active.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        cathode_formulation = CathodeFormulation(
            active_materials={cathode_active: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        cathode_cc_material = CurrentCollectorMaterial(name="Copper", specific_cost=5, density=2.7, color="#FFAE00")

        cathode_cc = PunchedCurrentCollector(
            material=cathode_cc_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = Cathode(
            formulation=cathode_formulation,
            mass_loading=14.2,
            current_collector=cathode_cc,
            calender_density=2.60,
        )

        anode_active = AnodeMaterial.from_database("Synthetic Graphite")
        anode_active.specific_cost = 4
        anode_active.density = 2.2

        anode_formulation = AnodeFormulation(
            active_materials={anode_active: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        cc_material = CurrentCollectorMaterial(name="Aluminium", specific_cost=5, density=2.7, color="#717171")

        anode_cc = PunchedCurrentCollector(
            material=cc_material,
            width=304,
            height=324,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = Anode(
            formulation=anode_formulation,
            mass_loading=10.68,
            current_collector=anode_cc,
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

        monolayer = MonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
        )

        # default stack for reuse in tests
        self.stack = PunchedStack(
            layup=monolayer, 
            n_layers=20
        )

    def test_punched_stack_basic_structure(self):
        self.assertIsInstance(self.stack, PunchedStack)
        self.assertAlmostEqual(self.stack.thickness, 7.64, 2)
        self.assertAlmostEqual(self.stack.thickness_range[0], 0.63)
        self.assertAlmostEqual(self.stack.thickness_range[1], 22.41, 2)
        self.assertAlmostEqual(self.stack.thickness_hard_range[1], 369.66, 2)
        self.assertEqual(len(self.stack.stack), 83)
        self.assertAlmostEqual(self.stack.pore_volume, 245.51, 2)

    def test_serialization(self):
        serialized = self.stack.serialize()
        deserialized = PunchedStack.deserialize(serialized)
        test_case = self.stack == deserialized
        self.assertTrue(test_case)

    def test_breakdown_plots(self):
        fig5 = self.stack.plot_mass_breakdown()
        fig6 = self.stack.plot_cost_breakdown()
        # fig5.show()
        # fig6.show()

    def test_right_left_view(self):
        """Test right and left side views of the punched stack."""
        fig_right = self.stack.get_side_view()
        # fig_right.show()

    def test_get_capacity_curve(self):
        """Test getting the full-cell capacity curve of the punched stack."""
        curve = self.stack.get_capacity_plot()
        # curve.show()

    def test_breakdowns(self):
        
        def sum_nested_dict(data):
            """Recursively sum all numeric values in a nested dictionary"""
            total = 0
            for key, value in data.items():
                if isinstance(value, dict):
                    total += sum_nested_dict(value)  # Recursive call for nested dict
                elif isinstance(value, (int, float)):
                    total += value
            return total

        self.assertAlmostEqual(self.stack._cost, sum_nested_dict(self.stack._cost_breakdown), 5)
        self.assertAlmostEqual(self.stack._mass, sum_nested_dict(self.stack._mass_breakdown), 5)
        self.assertAlmostEqual(self.stack.cost, sum_nested_dict(self.stack.cost_breakdown), 1)
        self.assertAlmostEqual(self.stack.mass, sum_nested_dict(self.stack.mass_breakdown), 1)

        mass_breakdown_fig = self.stack.plot_mass_breakdown()
        cost_breakdown_fig = self.stack.plot_cost_breakdown()

        # mass_breakdown_fig.show()
        # cost_breakdown_fig.show()

    def test_from_layup_constructor(self):

        layup = deepcopy(self.stack.layup)

        stack_from_layup = PunchedStack.from_layup(
            layup=layup,
            n_layers=20,
        )

        self.assertIsInstance(stack_from_layup, PunchedStack)
        self.assertAlmostEqual(stack_from_layup.thickness, 7.64, 2)
        self.assertAlmostEqual(stack_from_layup.thickness_range[0], 0.63)
        self.assertAlmostEqual(stack_from_layup.thickness_range[1], 22.41, 2)
        self.assertAlmostEqual(stack_from_layup.thickness_hard_range[1], 369.66, 2)
        self.assertEqual(len(stack_from_layup.stack), 83)

    def test_different_layup_type(self):

        self.assertEqual(type(self.stack), PunchedStack)
        original_cost = self.stack._cost
        original_mass = self.stack._mass
        original_layer_count = self.stack.n_layers

        anode = deepcopy(self.stack.layup.anode)
        cathode = deepcopy(self.stack.layup.cathode)
        separator = deepcopy(self.stack.layup.separator)

        new_layup = ZFoldMonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
        )

        self.stack.layup = new_layup
        self.assertEqual(type(self.stack), ZFoldStack)

        new_cost = self.stack._cost
        new_mass = self.stack._mass
        new_layer_count = self.stack.n_layers

        self.assertLess(new_cost, original_cost)
        self.assertLess(new_mass, original_mass)
        self.assertEqual(new_layer_count, original_layer_count)


class TestZFoldStack(unittest.TestCase):
    """Tests for the ZFoldStack electrode assembly built from a MonoLayer."""

    def setUp(self):
        # Replicate MonoLayer setup similar to TestSimpleMonoLayer in test_layups
        cathode_active = CathodeMaterial.from_database("LFP")
        cathode_active.specific_cost = 6
        cathode_active.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        cathode_formulation = CathodeFormulation(
            active_materials={cathode_active: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        cathode_cc_material = CurrentCollectorMaterial(name="Copper", specific_cost=5, density=2.7, color="#FFAE00")

        cathode_cc = PunchedCurrentCollector(
            material=cathode_cc_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = Cathode(
            formulation=cathode_formulation,
            mass_loading=14.2,
            current_collector=cathode_cc,
            calender_density=2.60,
        )

        anode_active = AnodeMaterial.from_database("Synthetic Graphite")
        anode_active.specific_cost = 4
        anode_active.density = 2.2

        anode_formulation = AnodeFormulation(
            active_materials={anode_active: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        cc_material = CurrentCollectorMaterial(name="Aluminium", specific_cost=5, density=2.7, color="#717171")

        anode_cc = PunchedCurrentCollector(
            material=cc_material,
            width=304,
            height=324,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = Anode(
            formulation=anode_formulation,
            mass_loading=10.68,
            current_collector=anode_cc,
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

        separator = Separator(material=separator_material, thickness=25, width=310)

        monolayer = ZFoldMonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
        )

        # default stack for reuse in tests
        self.stack = ZFoldStack(
            layup=monolayer, 
            n_layers=20,
            additional_separator_wraps=5
        )

    def test_z_fold_stack_basic_structure(self):
        self.assertIsInstance(self.stack, ZFoldStack)
        self.assertEqual(len(self.stack.stack), 93)

    def test_right_left_view(self):
        """Test right and left side views of the punched stack."""
        fig_right = self.stack.get_side_view()
        # fig_right.show()

    def test_datum_set(self):

        fig1 = self.stack.get_side_view()
        fig2 = self.stack.get_top_down_view()
        self.stack.datum = (100.0, 200.0, 300.0)
        fig3 = self.stack.get_side_view()
        fig4 = self.stack.get_top_down_view()
        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_additional_separator_wrap_setter(self):
        fig1 = self.stack.get_side_view()
        self.stack.additional_separator_wraps = 40
        fig2 = self.stack.get_side_view()
        # fig1.show()
        # fig2.show()

    def test_get_capacity_curve(self):
        """Test getting the full-cell capacity curve of the punched stack."""
        curve = self.stack.get_capacity_plot()
        # curve.show()

    def test_breakdowns(self):
        
        def sum_nested_dict(data):
            """Recursively sum all numeric values in a nested dictionary"""
            total = 0
            for key, value in data.items():
                if isinstance(value, dict):
                    total += sum_nested_dict(value)  # Recursive call for nested dict
                elif isinstance(value, (int, float)):
                    total += value
            return total

        self.assertAlmostEqual(self.stack._cost, sum_nested_dict(self.stack._cost_breakdown), 5)
        self.assertAlmostEqual(self.stack._mass, sum_nested_dict(self.stack._mass_breakdown), 5)
        self.assertAlmostEqual(self.stack.cost, sum_nested_dict(self.stack.cost_breakdown), 1)
        self.assertAlmostEqual(self.stack.mass, sum_nested_dict(self.stack.mass_breakdown), 1)

        mass_breakdown_fig = self.stack.plot_mass_breakdown()
        cost_breakdown_fig = self.stack.plot_cost_breakdown()

        # mass_breakdown_fig.show()
        # cost_breakdown_fig.show()

    def test_different_layup_type(self):
        """Test converting ZFoldStack to PunchedStack by changing layup type."""
        
        self.assertEqual(type(self.stack), ZFoldStack)
        original_cost = self.stack._cost
        original_mass = self.stack._mass

        anode = deepcopy(self.stack.layup.anode)
        cathode = deepcopy(self.stack.layup.cathode)
        separator = deepcopy(self.stack.layup.separator)

        new_layup = MonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
        )

        self.stack.layup = new_layup
        self.assertEqual(type(self.stack), PunchedStack)

        new_cost = self.stack._cost
        new_mass = self.stack._mass

        # PunchedStack should have higher cost and mass than ZFoldStack 
        # (since ZFoldStack has additional separator wraps that reduce material usage)
        self.assertLess(new_cost, original_cost)
        self.assertLess(new_mass, original_mass)


class TestRoundJellyRollWithTabWelded(unittest.TestCase):

    def setUp(self):
        
        self.tab_material = CurrentCollectorMaterial.from_database(name="Copper")
        self.cc_material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.weld_tab = WeldTab(material=self.tab_material, width=5, length=115, thickness=20)

        cathode_current_collector = TabWeldedCurrentCollector(
            material=self.cc_material,
            weld_tab=self.weld_tab,
            length=1820,
            width=108,
            thickness=15,
            weld_tab_positions=[100, 1000, 1400],
            skip_coat_width=30,
            tab_weld_side="a",
            tab_overhang=10,
        )

        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        formulation = CathodeFormulation(active_materials={material: 100})

        cathode = Cathode(
            formulation=formulation,
            mass_loading=12,
            current_collector=cathode_current_collector,
            calender_density=2.60,
        )

        anode_current_collector = deepcopy(cathode_current_collector)
        anode_current_collector.length = 1860

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(active_materials={material: 100})

        anode = Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=anode_current_collector,
            calender_density=1.1
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=2200)
        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=2200)

        self.layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = RoundMandrel(
            diameter=5,
            length=350,
        )

        self.my_jellyroll = WoundJellyRoll(
            laminate=self.layup,
            mandrel=mandrel,
        )

    def test_type(self):
        self.assertIsInstance(self.my_jellyroll, WoundJellyRoll)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, WoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig3 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig4 = self.my_jellyroll.get_capacity_plot()

        # fig1.show()
        # fig3.show()
        # fig4.show()


class TestFlatJellyRollWithTabWelded(unittest.TestCase):

    def setUp(self):
        
        self.tab_material = CurrentCollectorMaterial.from_database(name="Copper")
        self.cc_material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.weld_tab = WeldTab(material=self.tab_material, width=5, length=115, thickness=20)

        cathode_current_collector = TabWeldedCurrentCollector(
            material=self.cc_material,
            weld_tab=self.weld_tab,
            length=1820,
            width=108,
            thickness=15,
            weld_tab_positions=[100, 1000, 1400],
            skip_coat_width=30,
            tab_weld_side="a",
            tab_overhang=10,
        )

        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        formulation = CathodeFormulation(active_materials={material: 100})

        cathode = Cathode(
            formulation=formulation,
            mass_loading=12,
            current_collector=cathode_current_collector,
            calender_density=2.60,
        )

        anode_current_collector = deepcopy(cathode_current_collector)
        anode_current_collector.length = 1860

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(active_materials={material: 100})

        anode = Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=anode_current_collector,
            calender_density=1.1
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=2200)
        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=2200)

        self.layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = FlatMandrel(
            length=350,
            width=100,
            height=5
        )

        self.my_jellyroll = FlatWoundJellyRoll(
            laminate=self.layup,
            mandrel=mandrel,
        )

    def test_type(self):
        self.assertIsInstance(self.my_jellyroll, FlatWoundJellyRoll)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, FlatWoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig3 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig4 = self.my_jellyroll.get_capacity_plot()

        # fig1.show()
        # fig3.show()
        # fig4.show()


if __name__ == "__main__":
    unittest.main()

