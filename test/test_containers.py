import unittest
import plotly.express as px
from steer_opencell_design.Components.Containers import (
    PrismaticCase,
    PrismaticLid,
    PrismaticShell,
    CylindricalCanister,
    CylindricalCase,
    CylindricalLidAssembly,
    CylindricalTerminalConnector,
)
from steer_opencell_design.Formulations.ElectrodeFormulations import (
    ElectrodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.other import Terminal
from steer_opencell_design.Components.ElectrodeMaterials import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)
from steer_opencell_design.Components.CurrentCollectors import CurrentCollector
from steer_opencell_design.Components.Separators import Separator


class TestCylindricalCase(unittest.TestCase):
    def setUp(self):
        # build the encapsulation
        cylindrical_shell = CylindricalCanister(formula="Al", outer_diameter=21.6, wall_thickness=0.3, length=115)

        # build the connectors
        anode_connector = CylindricalTerminalConnector(formula="Al", diameter=10, thickness=1, fill_factor=0.8)
        cathode_connector = CylindricalTerminalConnector(formula="Al", diameter=10, thickness=1, fill_factor=0.8)

        lid = CylindricalLidAssembly(cost=0.1, mass=5, thickness=3)

        self.case = CylindricalCase(
            canister=cylindrical_shell,
            lid_assembly=lid,
            cathode_terminal_connector=cathode_connector,
            anode_terminal_connector=anode_connector,
        )

    def test_attributes(self):
        self.assertEqual(round(self.case._cost, 4), 0.1204)
        self.assertEqual(self.case.cost, 0.12)
        self.assertEqual(round(self.case._mass, 4), 0.0127)
        self.assertEqual(self.case.mass, 12.74)
        fig = self.case.get_top_down_view()
        # fig.show()
        fig = self.case.get_side_view()
        # fig.show()


class TestPrismaticCase(unittest.TestCase):
    def setUp(self):
        # construct cathode
        cathode_active_material = CathodeMaterial(
            name="NaNiMn P2-O3 Composite - 4.25V",
            specific_cost=11.26,
            density=4,
            irreversible_capacity_scaling=1,
            reversible_capacity_scaling=1,
        )

        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(
            active_materials={cathode_active_material: 89},
            binders={cathode_binder: 5},
            conductive_additives={cathode_conductive_additive: 6},
        )

        cathode_current_collector = CurrentCollector(formula="Al", thickness=15, length=160, width=108, bare_area=822)

        cathode = Cathode(
            formulation=cathode_formulation,
            mass_loading=10.68,
            current_collector=cathode_current_collector,
            calender_density=2.60,
        )

        # construct anode
        anode_active_material = AnodeMaterial(
            name="Hard Carbon (Vendor A - 330 mAh/g)",
            specific_cost=14.27,
            density=1.50,
            irreversible_capacity_scaling=1,
            reversible_capacity_scaling=1,
        )

        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(
            active_materials={anode_active_material: 88},
            binders={anode_binder: 3},
            conductive_additives={anode_conductive_additive: 9},
        )

        anode_current_collector = CurrentCollector(formula="Cu", thickness=15, length=160, width=108, bare_area=755)

        anode = Anode(
            formulation=anode_formulation,
            mass_loading=5.25,
            current_collector=anode_current_collector,
            calender_density=0.85,
        )

        # construct seperator
        separator = Separator(
            thickness=16,
            areal_cost=0.9,
            density=0.4,
            width=110,
            porosity=47,
            fold_length=186,
        )

        # make the case
        prismatic_shell = PrismaticShell(
            cost=0.14,
            mass=220.23,
            internal_width=113,
            internal_length=189,
            internal_height=19.3,
            wall_thickness=0.8,
        )

        prismatic_lid = PrismaticLid(cost=0.34, mass=40.56, external_width=13, internal_width=8)

        self.prismatic_case = PrismaticCase(lid=prismatic_lid, shell=prismatic_shell)

        self.stack_1 = self.prismatic_case.get_optimized_stack(cathode=cathode, anode=anode, separator=separator)
        self.stack_2 = self.prismatic_case.get_optimized_stack(cathode=cathode, anode=anode, separator=separator, n_stacks=2)

    def test_case(self):
        self.assertEqual(self.prismatic_case.cost, 0.48)
        self.assertEqual(self.prismatic_case.mass, 260.79)
        self.assertEqual(self.prismatic_case.internal_width, 121)
        self.assertEqual(self.prismatic_case.internal_length, 189)
        self.assertEqual(self.prismatic_case.internal_height, 19.3)
        self.assertEqual(self.prismatic_case.internal_volume, 441.37)
        self.assertEqual(self.prismatic_case.external_width, 127.6)
        self.assertEqual(self.prismatic_case.external_length, 190.6)
        self.assertEqual(self.prismatic_case.external_height, 20.9)
        self.assertEqual(self.prismatic_case.external_volume, 508.3)
        self.assertEqual(self.prismatic_case.name, "Prismatic Case")
        self.assertEqual(round(self.prismatic_case._cost, 2), 0.48)
        self.assertEqual(round(self.prismatic_case._mass, 3), 0.261)
        self.assertEqual(round(self.prismatic_case._internal_width, 4), 0.121)
        self.assertEqual(round(self.prismatic_case._internal_length, 4), 0.189)
        self.assertEqual(round(self.prismatic_case._internal_height, 4), 0.0193)
        self.assertEqual(round(self.prismatic_case._internal_volume, 6), 0.000441)
        self.assertEqual(round(self.prismatic_case._external_width, 4), 0.1276)
        self.assertEqual(round(self.prismatic_case._external_length, 4), 0.1906)
        self.assertEqual(round(self.prismatic_case._external_height, 4), 0.0209)
        self.assertEqual(round(self.prismatic_case._external_volume, 6), 0.000508)

    def test_stack_1(self):
        self.assertEqual(self.stack_1._n_layers, 71)
        self.assertEqual(len(self.stack_1._cathodes), 71)
        self.assertEqual(len(self.stack_1._anodes), 72)

    def test_stack_2(self):
        self.assertEqual(self.stack_2._n_layers, 35)
        self.assertEqual(len(self.stack_2._cathodes), 35)
        self.assertEqual(len(self.stack_2._anodes), 36)
