import unittest
from copy import deepcopy
import pandas as pd

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import PunchedCurrentCollector, NotchedCurrentCollector
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies import PunchedStack, ZFoldStack, WoundJellyRoll, FlatWoundJellyRoll
from steer_opencell_design.AuxillaryComponents.WindingEquipment import RoundMandrel, FlatMandrel
from steer_opencell_design.Constructions.Layups import MonoLayer, ZFoldMonoLayer, Laminate

from steer_materials.CellMaterials.Base import (
    CurrentCollectorMaterial, 
    SeparatorMaterial, 
    InsulationMaterial
)
from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
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

        self.my_jellyroll = WoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
        )

    def test_basics(self):
        self.assertTrue(type(self.my_jellyroll), WoundJellyRoll)
        self.assertAlmostEqual(self.my_jellyroll.radius, 18.12, 2)
        self.assertAlmostEqual(self.my_jellyroll.diameter, 36.25, 2)
        self.assertAlmostEqual(self.my_jellyroll.energy, 37.29)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, WoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig2 = self.my_jellyroll.get_spiral_plot(layered=True, extruded=False)
        fig3 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig4 = self.my_jellyroll.get_capacity_plot()

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_roll_properties(self):
        """Test that roll_properties returns a properly formatted DataFrame with expected values."""
        
        # Test that roll_properties is a pandas DataFrame
        self.assertIsInstance(self.my_jellyroll.roll_properties, pd.DataFrame)
        
        # Create expected DataFrame
        expected_data = {
            'anode_a_side_coating_turns': 56.01,
            'anode_current_collector_turns': 65.24,
            'anode_b_side_coating_turns': 57.94,
            'cathode_a_side_coating_turns': 65.24,
            'cathode_current_collector_turns': 65.24,
            'cathode_b_side_coating_turns': 65.24,
            'bottom_separator_turns': 137.18,
            'bottom_separator_inner_turns': 67.32,
            'bottom_separator_outer_turns': 13.38,
            'top_separator_turns': 77.45,
            'top_separator_inner_turns': 16.46,
            'top_separator_outer_turns': 4.52
        }
        
        expected_df = pd.DataFrame.from_dict(expected_data, orient='index', columns=['Turns'])
        expected_df.index.name = 'Component'
        
        # Get actual DataFrame
        actual_df = self.my_jellyroll.roll_properties
        
        # Test DataFrame structure
        self.assertEqual(actual_df.columns.tolist(), ['Turns'])
        self.assertEqual(actual_df.index.name, 'Component')
        
        # Test that all expected components are present
        for component in expected_data.keys():
            self.assertIn(component, actual_df.index, f"Missing component: {component}")
        
        # Test values (rounded to 2 decimal places)
        for component, expected_value in expected_data.items():
            actual_value = actual_df.loc[component, 'Turns']
            self.assertAlmostEqual(
                actual_value, 
                expected_value, 
                places=2, 
                msg=f"Component {component}: expected {expected_value}, got {actual_value}"
            )


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

        self.my_jellyroll = FlatWoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
        )

    def test_basics(self):
        self.assertTrue(type(self.my_jellyroll), WoundJellyRoll)
        self.assertAlmostEqual(self.my_jellyroll.radius, 18.01, 2)
        self.assertAlmostEqual(self.my_jellyroll.diameter, 36.02, 2)
        self.assertAlmostEqual(self.my_jellyroll.energy, 41.34)

    def test_plots(self):

        self.assertIsInstance(self.my_jellyroll, FlatWoundJellyRoll)
        self.assertTrue(type(self.my_jellyroll.spiral) == pd.DataFrame)

        fig1 = self.my_jellyroll.get_spiral_plot()
        fig2 = self.my_jellyroll.get_spiral_plot(layered=False)
        fig3 = self.my_jellyroll.get_capacity_plot()
        # fig1.show()
        # fig2.show()
        # fig3.show()


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
        self.assertEqual(len(self.stack.stack), 83)

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


if __name__ == "__main__":
    unittest.main()
