import unittest
from copy import deepcopy

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)


class TestSimpleCathodeFormulation(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.cathode_active_material1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        self.cathode_active_material1.density = 4
        self.cathode_active_material1.specific_cost = 11.26

        cathode_conductive_additive1 = ConductiveAdditive.from_database("Super P")
        cathode_conductive_additive1.specific_cost = 9
        cathode_conductive_additive1.density = 1.9

        cathode_conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        cathode_conductive_additive2.specific_cost = 12
        cathode_conductive_additive2.density = 1.0

        cathode_binder1 = Binder.from_database("PVDF")
        cathode_binder1.specific_cost = 15
        cathode_binder1.density = 1.7

        cathode_binder2 = Binder.from_database("CMC")
        cathode_binder2.specific_cost = 10
        cathode_binder2.density = 1.5

        self.cathode_formulation = CathodeFormulation(
            active_materials={
                self.cathode_active_material1: 90,
            },
            binders={cathode_binder1: 3, cathode_binder2: 2},
            conductive_additives={
                cathode_conductive_additive1: 3,
                cathode_conductive_additive2: 2,
            },
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.cathode_formulation, CathodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 1)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(self.cathode_formulation._name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.density, 3.76)
        self.assertEqual(self.cathode_formulation.specific_cost, 11.29)
        self.assertEqual(
            round(sum(self.cathode_formulation.specific_cost_breakdown.values()), 2),
            self.cathode_formulation.specific_cost,
        )
        self.assertEqual(
            round(sum(self.cathode_formulation.density_breakdown.values()), 2),
            self.cathode_formulation.density,
        )

    def test_voltage_cutoff(self):
        self.cathode_formulation.voltage_cutoff = 4.2
        figure = self.cathode_formulation.plot_half_cell_curve(add_materials=True)

        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            12.8,
        )
        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            25.7,
        )
        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            102.8,
        )

        # figure.show()

    def test_set_voltage_cutoff_edge_case(self):
        lower_voltage = self.cathode_formulation.voltage_cutoff_range[0]
        self.cathode_formulation.voltage_cutoff = lower_voltage

        upper_voltage = self.cathode_formulation.voltage_cutoff_range[1]
        self.cathode_formulation.voltage_cutoff = upper_voltage

        self.assertEqual(self.cathode_formulation.voltage_cutoff, upper_voltage)
        self.assertEqual(
            self.cathode_formulation.voltage_cutoff_hard_range,
            (lower_voltage, upper_voltage),
        )

    def test_active_material_setter(self):
        old_cutoff_voltage = self.cathode_formulation.voltage_cutoff
        new_active_material = CathodeMaterial.from_database("NMC811")
        self.cathode_formulation.active_materials = {new_active_material: 90}
        new_cutoff_voltage = self.cathode_formulation.voltage_cutoff

        self.assertNotEqual(old_cutoff_voltage, new_cutoff_voltage)


class TestMultiCathodeFormulation(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.cathode_active_material1 = CathodeMaterial.from_database("LFP")
        self.cathode_active_material2 = CathodeMaterial.from_database("NMC811")
        self.cathode_active_material2.extrapolation_window = 0.5

        cathode_conductive_additive1 = ConductiveAdditive.from_database("Super P")
        cathode_conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        cathode_binder1 = Binder.from_database("PVDF")
        cathode_binder2 = Binder.from_database("CMC")

        self.cathode_formulation = CathodeFormulation(
            active_materials={
                self.cathode_active_material1: 80,
                self.cathode_active_material2: 10,
            },
            binders={cathode_binder1: 3, cathode_binder2: 2},
            conductive_additives={
                cathode_conductive_additive1: 3,
                cathode_conductive_additive2: 2,
            },
        )

    def test_formulation(self):

        self.assertTrue(isinstance(self.cathode_formulation, CathodeFormulation))
        self.assertEqual(len(self.cathode_formulation._active_materials), 2)
        self.assertEqual(len(self.cathode_formulation._binders), 2)
        self.assertEqual(len(self.cathode_formulation._conductive_additives), 2)
        self.assertEqual(self.cathode_formulation._name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.name, "Cathode Formulation")
        self.assertEqual(self.cathode_formulation.density, 3.55)
        self.assertEqual(self.cathode_formulation.specific_cost, 8.37)
        self.assertEqual(
            round(sum(self.cathode_formulation.specific_cost_breakdown.values()), 2),
            self.cathode_formulation.specific_cost,
        )
        self.assertEqual(
            round(sum(self.cathode_formulation.density_breakdown.values()), 2),
            self.cathode_formulation.density,
        )

        figure = self.cathode_formulation.plot_half_cell_curve(add_materials=True)

        # figure.show()

    def test_equality(self):
        copy_formulation = deepcopy(self.cathode_formulation)
        condition = self.cathode_formulation == copy_formulation
        self.assertTrue(condition)

    def test_voltage_cutoff(self):
        self.cathode_formulation.voltage_cutoff = 4.09
        figure = self.cathode_formulation.plot_half_cell_curve(add_materials=True)

        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0.2,
        )
        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            0.2,
        )
        self.assertEqual(
            self.cathode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            134.4,
        )

        # figure.show()

    def test_change_active_materials(self):
        self.cathode_formulation.active_materials = {self.cathode_active_material1: 90}
        self.cathode_formulation.voltage_cutoff = 4.09

        self.assertEqual(self.cathode_formulation.density, 3.43)
        self.assertEqual(self.cathode_formulation.specific_cost, 6.47)

        figure = self.cathode_formulation.plot_half_cell_curve(add_materials=True)
        # figure.show()


class TestSimpleAnodeFormulation(unittest.TestCase):
    def setUp(self):
        anode_active_material = AnodeMaterial.from_database("Hard Carbon (Vendor A)")
        anode_active_material.density = 1.5
        anode_active_material.specific_cost = 14.27

        anode_binder = Binder.from_database("PVDF")
        anode_binder.specific_cost = 10
        anode_binder.density = 1.7

        anode_conductive_additive = ConductiveAdditive.from_database("Super P")
        anode_conductive_additive.specific_cost = 9
        anode_conductive_additive.density = 1.9

        self.anode_formulation = AnodeFormulation(
            active_materials={anode_active_material: 88},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
        )

        self.anode_formulation2 = AnodeFormulation(
            active_materials={anode_active_material: 88},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
            voltage_cutoff=0.0,
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.anode_formulation, AnodeFormulation))
        self.assertEqual(len(self.anode_formulation._active_materials), 1)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.anode_formulation._name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.density, 1.54)
        self.assertEqual(self.anode_formulation.specific_cost, 13.67)
        self.assertEqual(
            round(sum(self.anode_formulation.specific_cost_breakdown.values()), 2),
            self.anode_formulation.specific_cost,
        )
        self.assertEqual(
            round(sum(self.anode_formulation.density_breakdown.values()), 2),
            self.anode_formulation.density,
        )

        figure = self.anode_formulation.plot_half_cell_curve(add_materials=True)
        # figure.show()

    def test_plot_half_cell_curve(self):
        self.anode_formulation.voltage_cutoff = 0.0
        figure = self.anode_formulation.plot_half_cell_curve(add_materials=True)

        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0,
        )
        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            1.8,
        )
        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            262.1,
        )
        # figure.show()

    def test_anode_half_Cell_curve_set(self):
        figure = self.anode_formulation2.plot_half_cell_curve(add_materials=True)
        # figure.show()


class TestDualAnodeFormulation(unittest.TestCase):
    def setUp(self):
        anode_active_material1 = AnodeMaterial.from_database("Hard Carbon (Vendor A)")
        anode_active_material2 = AnodeMaterial.from_database("Hard Carbon (Vendor B)")
        anode_binder = Binder.from_database("PVDF")
        anode_conductive_additive = ConductiveAdditive.from_database("Super P")

        self.anode_formulation = AnodeFormulation(
            active_materials={anode_active_material1: 44, anode_active_material2: 44},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
        )

    def test_formulation(self):
        self.assertTrue(isinstance(self.anode_formulation, AnodeFormulation))
        self.assertEqual(len(self.anode_formulation._active_materials), 2)
        self.assertEqual(len(self.anode_formulation._binders), 1)
        self.assertEqual(len(self.anode_formulation._conductive_additives), 1)
        self.assertEqual(self.anode_formulation._name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.name, "Anode Formulation")
        self.assertEqual(self.anode_formulation.density, 1.55)
        self.assertEqual(self.anode_formulation.specific_cost, 7.87)
        self.assertEqual(
            round(sum(self.anode_formulation.specific_cost_breakdown.values()), 2),
            self.anode_formulation.specific_cost,
        )
        self.assertEqual(
            round(sum(self.anode_formulation.density_breakdown.values()), 2),
            self.anode_formulation.density,
        )

    def test_plot_half_cell_curve(self):
        figure = self.anode_formulation.plot_half_cell_curve(add_materials=True)

        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[10],
            0.4,
        )
        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[20],
            0.5,
        )
        self.assertEqual(
            self.anode_formulation.half_cell_curve["Specific Capacity (mAh/g)"].round(1).iloc[80],
            76.3,
        )

        # figure.show()
