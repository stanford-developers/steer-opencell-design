import unittest
from copy import deepcopy

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import PunchedCurrentCollector
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies import PunchedStack
from steer_opencell_design.Constructions.Layups import MonoLayer

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

        cc_material = CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")
        cathode_cc = PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = Cathode(
            formulation=cathode_formulation,
            mass_loading=6.2,
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
            transverse=True,
        )

        # default stack for reuse in tests
        self.stack = PunchedStack(
            layup=monolayer, 
            n_layers=20
        )

    # def test_punched_stack_basic_structure(self):
    #     self.assertIsInstance(self.stack, PunchedStack)
    #     # Validate expected keys present
    #     self.assertIn("anodes", self.stack.stack)
    #     self.assertIn("cathodes", self.stack.stack)
    #     self.assertIn("separators", self.stack.stack)
    #     # Basic sanity: non-empty collections
    #     self.assertGreater(len(self.stack.stack["anodes"]), 0)
    #     self.assertEqual(len(self.stack.stack["cathodes"]), self.stack.n_layers)

    # def test_punched_stack_layer_datums_increasing(self):
    #     """Check that layer component z datums increase monotonically with layer index."""
    #     anode_zs = [a.datum[2] for a in self.stack.stack["anodes"].values()]
    #     for earlier, later in zip(anode_zs, anode_zs[1:]):
    #         self.assertLessEqual(earlier, later)

    # def test_punched_stack_recalc_on_n_layers_change(self):
    #     """Changing n_layers should recompute stack size."""
    #     initial_count = len(self.stack.stack["cathodes"])
    #     self.stack.n_layers = initial_count + 2
    #     self.assertEqual(len(self.stack.stack["cathodes"]), initial_count + 2)


if __name__ == "__main__":
    unittest.main()
