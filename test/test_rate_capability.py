import unittest

import steer_opencell_design as ocd

try:
    import pybamm
except ImportError:  # pragma: no cover - environment dependent
    pybamm = None


def build_cylindrical_cell():
    material = ocd.CathodeMaterial.from_database("LFP")
    material.specific_cost = 6
    material.density = 3.6

    conductive_additive = ocd.ConductiveAdditive(
        name="super_P",
        specific_cost=15,
        density=2.0,
        color="#000000",
    )
    binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

    cathode_formulation = ocd.CathodeFormulation(
        active_materials={material: 95},
        binders={binder: 2},
        conductive_additives={conductive_additive: 3},
    )

    current_collector_material = ocd.CurrentCollectorMaterial(
        name="Aluminum",
        specific_cost=5,
        density=2.7,
        color="#AAAAAA",
    )

    cathode_collector = ocd.NotchedCurrentCollector(
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

    insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

    cathode = ocd.Cathode(
        formulation=cathode_formulation,
        mass_loading=12,
        current_collector=cathode_collector,
        calender_density=2.60,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    anode_material = ocd.AnodeMaterial.from_database("Synthetic Graphite")
    anode_material.specific_cost = 4
    anode_material.density = 2.2

    anode_formulation = ocd.AnodeFormulation(
        active_materials={anode_material: 90},
        binders={binder: 5},
        conductive_additives={conductive_additive: 5},
    )

    anode_collector = ocd.NotchedCurrentCollector(
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

    anode = ocd.Anode(
        formulation=anode_formulation,
        mass_loading=7.2,
        current_collector=anode_collector,
        calender_density=1.1,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    separator_material = ocd.SeparatorMaterial(
        name="Polyethylene",
        specific_cost=2,
        density=0.94,
        color="#FDFDB7",
        porosity=45,
    )
    top_separator = ocd.Separator(
        material=separator_material,
        thickness=25,
        width=310,
        length=5000,
    )
    bottom_separator = ocd.Separator(
        material=separator_material,
        thickness=25,
        width=310,
        length=7000,
    )

    layup = ocd.Laminate(
        anode=anode,
        cathode=cathode,
        top_separator=top_separator,
        bottom_separator=bottom_separator,
    )

    mandrel = ocd.RoundMandrel(diameter=5, length=350)
    tape_material = ocd.TapeMaterial.from_database("Kapton")
    tape_material.density = 1.42
    tape_material.specific_cost = 70
    tape = ocd.Tape(material=tape_material, thickness=30)

    jellyroll = ocd.WoundJellyRoll(
        laminate=layup,
        mandrel=mandrel,
        tape=tape,
        additional_tape_wraps=5,
    )

    aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
    copper = ocd.PrismaticContainerMaterial.from_database("Copper")

    cathode_connector = ocd.CylindricalTerminalConnector(
        material=aluminum,
        thickness=2,
        fill_factor=0.8,
    )
    anode_connector = ocd.CylindricalTerminalConnector(
        material=copper,
        thickness=3,
        fill_factor=0.7,
    )
    lid = ocd.CylindricalLidAssembly(
        material=aluminum,
        thickness=4.0,
        fill_factor=0.9,
    )
    canister = ocd.CylindricalCanister(
        material=aluminum,
        outer_radius=21.4,
        height=330,
        wall_thickness=0.5,
    )
    encapsulation = ocd.CylindricalEncapsulation(
        cathode_terminal_connector=cathode_connector,
        anode_terminal_connector=anode_connector,
        lid_assembly=lid,
        canister=canister,
    )

    electrolyte = ocd.Electrolyte(
        name="1M LiPF6 in EC:DMC (1:1)",
        density=1.2,
        specific_cost=15.0,
        color="#00FF00",
    )

    return ocd.CylindricalCell(
        reference_electrode_assembly=jellyroll,
        encapsulation=encapsulation,
        electrolyte=electrolyte,
        electrolyte_overfill=20,
    )


class TestPyBaMMGeometryAdapter(unittest.TestCase):
    def setUp(self):
        self.cell = build_cylindrical_cell()

    def test_extract_pybamm_geometry(self):
        geometry = ocd.extract_pybamm_geometry(self.cell)

        self.assertGreater(geometry.reference_interfacial_area_m2, 0.0)
        self.assertGreater(geometry.electrode_width_m, 0.0)
        self.assertGreater(geometry.electrode_height_m, 0.0)
        self.assertGreater(geometry.negative_electrode_thickness_m, 0.0)
        self.assertGreater(geometry.positive_electrode_thickness_m, 0.0)
        self.assertGreater(geometry.separator_thickness_m, 0.0)
        self.assertAlmostEqual(geometry.nominal_cell_capacity_ah, self.cell.reversible_capacity, places=6)
        self.assertAlmostEqual(geometry.lower_voltage_cutoff_v, self.cell.minimum_operating_voltage, places=6)
        self.assertAlmostEqual(geometry.upper_voltage_cutoff_v, self.cell.maximum_operating_voltage, places=6)
        self.assertEqual(geometry.electrodes_in_parallel, self.cell.n_electrode_assembly)

    @unittest.skipIf(pybamm is not None, "Only relevant when pybamm is absent")
    def test_missing_pybamm_dependency_is_lazy(self):
        with self.assertRaises(ocd.MissingPyBaMMDependencyError):
            ocd.build_pybamm_parameter_values(self.cell, {})


@unittest.skipUnless(pybamm is not None, "pybamm is not installed")
class TestPyBaMMRateCapability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cell = build_cylindrical_cell()
        cls.base_parameters = pybamm.ParameterValues("Chen2020")
        cls.smoke_result = ocd.simulate_rate_capability(
            cls.cell,
            cls.base_parameters,
            [0.2],
            raise_on_failure=True,
        )

    def test_build_pybamm_parameter_values_overwrites_geometry(self):
        geometry = ocd.extract_pybamm_geometry(self.cell)
        overridden = self.base_parameters.copy()
        overridden.update(
            {
                "Electrode width [m]": 1.0,
                "Electrode height [m]": 1.0,
                "Negative electrode thickness [m]": 1.0,
            }
        )

        merged = ocd.build_pybamm_parameter_values(self.cell, overridden)

        self.assertAlmostEqual(merged["Electrode width [m]"], geometry.electrode_width_m, places=12)
        self.assertAlmostEqual(merged["Electrode height [m]"], geometry.electrode_height_m, places=12)
        self.assertAlmostEqual(
            merged["Negative electrode thickness [m]"],
            geometry.negative_electrode_thickness_m,
            places=12,
        )
        self.assertAlmostEqual(
            merged["Nominal cell capacity [A.h]"],
            geometry.nominal_cell_capacity_ah,
            places=12,
        )

    def test_validate_pybamm_parameter_values_reports_missing_keys(self):
        with self.assertRaises(ocd.MissingPyBaMMParametersError) as ctx:
            ocd.validate_pybamm_parameter_values(pybamm.ParameterValues({}))

        self.assertIn("Negative electrode conductivity [S.m-1]", str(ctx.exception))
        self.assertIn("Positive electrode OCP [V]", str(ctx.exception))

    def test_simulate_rate_capability_smoke(self):
        summary = self.smoke_result.summary
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary.loc[0, "Solve status"], "success")
        self.assertGreater(summary.loc[0, "Delivered capacity [A.h]"], 0.0)
        self.assertGreater(len(self.smoke_result.curve_dataframe(0.2)), 1)

    def test_simulate_rate_capability_plotly_smoke(self):
        import plotly.graph_objects as go

        curve = self.smoke_result.curve_dataframe(0.2)

        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=curve["Discharge capacity [A.h]"],
                y=curve["Terminal voltage [V]"],
                mode="lines",
                name="0.2C DFN",
            )
        )
        figure.update_layout(
            title="DFN Discharge Curve",
            xaxis_title="Discharge capacity [A.h]",
            yaxis_title="Terminal voltage [V]",
        )

        self.assertIsInstance(figure, go.Figure)
        self.assertEqual(len(figure.data), 1)
        self.assertGreater(len(figure.data[0].x), 1)
        self.assertEqual(figure.layout.xaxis.title.text, "Discharge capacity [A.h]")
        self.assertEqual(figure.layout.yaxis.title.text, "Terminal voltage [V]")

        # figure.show()
