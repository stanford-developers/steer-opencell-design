import unittest
from copy import deepcopy

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import PunchedCurrentCollector
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies import PunchedStack, ZFoldStack
from steer_opencell_design.Constructions.Layups import MonoLayer, ZFoldMonoLayer

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial, SeparatorMaterial
from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)


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
