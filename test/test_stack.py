import unittest
import pandas as pd
import plotly.express as px

from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Constructions.ElectrodeAssemblies import Stack
from steer_opencell_design.Components.CurrentCollectors import PunchedCurrentCollector
from steer_opencell_design.Components.Separators import Separator

from steer_materials.CellMaterials.Electrode import (
    CathodeMaterial,
    AnodeMaterial,
    Binder,
    ConductiveAdditive,
)


class TestCellsSingleAM(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
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

        cathode_current_collector = CurrentCollector(
            formula="Al", thickness=15, length=16.0, width=10.8, bare_area=8.22
        )

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

        anode_current_collector = CurrentCollector(
            formula="Cu", thickness=5, length=16.0, width=10.8, bare_area=7.55
        )

        anode = Anode(
            formulation=anode_formulation,
            mass_loading=5.25,
            current_collector=anode_current_collector,
            calender_density=0.85,
        )

        # construct separator
        separator = Separator(
            thickness=16,
            areal_cost=0.9,
            density=0.4,
            width=11.0,
            porosity=47,
            fold_length=18.6,
        )

        # construct the stack
        self.stack = Stack(
            anode=anode, cathode=cathode, separator=separator, name="stack", n_layers=26
        )

    def test_instantiation(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.stack, Stack)
        self.assertIsInstance(self.stack.separator, Separator)

        for c in self.stack.cathodes:
            self.assertIsInstance(c, Cathode)
        for a in self.stack.anodes:
            self.assertIsInstance(a, Anode)

        self.assertEqual(len(self.stack.cathodes), 26)
        self.assertEqual(len(self.stack.anodes), 27)

        # check the mass breakdowns are working
        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._cathode_mass_breakdown["active_materials"].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._cathodes[0]
                        ._mass_breakdown["active_materials"]
                        .values()
                    )
                )
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(self.stack._anode_mass_breakdown["active_materials"].values())
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._anodes[0]
                        ._mass_breakdown["active_materials"]
                        .values()
                    )
                )
                * 27,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._cathode_mass_breakdown[
                            "conductive_additives"
                        ].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._cathodes[0]
                        ._mass_breakdown["conductive_additives"]
                        .values()
                    )
                )
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._anode_mass_breakdown[
                            "conductive_additives"
                        ].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._anodes[0]
                        ._mass_breakdown["conductive_additives"]
                        .values()
                    )
                )
                * 27,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(iter(self.stack._cathode_mass_breakdown["binders"].values())), 5
            ),
            round(
                next(iter(self.stack._cathodes[0]._mass_breakdown["binders"].values()))
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(next(iter(self.stack._anode_mass_breakdown["binders"].values())), 5),
            round(
                next(iter(self.stack._anodes[0]._mass_breakdown["binders"].values()))
                * 27,
                5,
            ),
        )

        # check the cost breakdowns are working
        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._cathode_cost_breakdown["active_materials"].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._cathodes[0]
                        ._cost_breakdown["active_materials"]
                        .values()
                    )
                )
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(self.stack._anode_cost_breakdown["active_materials"].values())
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._anodes[0]
                        ._cost_breakdown["active_materials"]
                        .values()
                    )
                )
                * 27,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._cathode_cost_breakdown[
                            "conductive_additives"
                        ].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._cathodes[0]
                        ._cost_breakdown["conductive_additives"]
                        .values()
                    )
                )
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(
                    iter(
                        self.stack._anode_cost_breakdown[
                            "conductive_additives"
                        ].values()
                    )
                ),
                5,
            ),
            round(
                next(
                    iter(
                        self.stack._anodes[0]
                        ._cost_breakdown["conductive_additives"]
                        .values()
                    )
                )
                * 27,
                5,
            ),
        )

        self.assertEqual(
            round(
                next(iter(self.stack._cathode_cost_breakdown["binders"].values())), 5
            ),
            round(
                next(iter(self.stack._cathodes[0]._cost_breakdown["binders"].values()))
                * 26,
                5,
            ),
        )

        self.assertEqual(
            round(next(iter(self.stack._anode_cost_breakdown["binders"].values())), 5),
            round(
                next(iter(self.stack._anodes[0]._cost_breakdown["binders"].values()))
                * 27,
                5,
            ),
        )

    def test_half_cell_curve(self):
        """
        Test the half cell curve
        """
        self.stack._calculate_half_cell_curve(grid_n=100)
        data_cathode = self.stack.cathode_half_cell_curve
        data_anode = self.stack.anode_half_cell_curve

        # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve',
        #         line_shape='spline', color='Direction', markers=True).show()

        # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
        #         line_shape='spline', color='Direction', markers=True).show()

        cathode_max_capacity = data_cathode["Capacity (Ah)"].max()
        anode_max_capacity = data_anode["Capacity (Ah)"].max()
        single_cathode_capacity = (
            self.stack.cathodes[0].half_cell_curve["Capacity (Ah)"].max()
        )
        single_anode_capacity = (
            self.stack.anodes[0].half_cell_curve["Capacity (Ah)"].max()
        )
        self.assertEqual(
            round(cathode_max_capacity, 5), round(single_cathode_capacity * 26, 5)
        )
        self.assertEqual(
            round(anode_max_capacity, 5), round(single_anode_capacity * 26, 5)
        )

    def test_full_cell_curve(self):
        """
        Test the full cell curve
        """
        self.stack._calculate_half_cell_curve(grid_n=100)
        self.stack._calculate_full_cell_curve()
        data_cathode = self.stack.cathode_half_cell_curve.assign(Electrode="Cathode")
        data_anode = self.stack.anode_half_cell_curve.assign(Electrode="Anode")
        data_full = self.stack.full_cell_curve.assign(Electrode="Full Cell")
        data = pd.concat([data_cathode, data_anode, data_full])

        # px.line(data, x='Capacity (Ah)', y='Voltage (V)', title='Full Cell Curve',
        #         line_shape='spline', markers=True, color='Electrode').show()
