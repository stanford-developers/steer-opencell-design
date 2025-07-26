import unittest
import plotly.express as px
import plotly.graph_objects as go
from OpenCell.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from OpenCell.Constructions.Electrodes import Cathode, Anode
from OpenCell.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from OpenCell.Materials.CurrentCollectors import NotchedCurrentCollector, WeldTab, TabWeldedCurrentCollector, PunchedCurrentCollector
from OpenCell.Materials.RawMaterials import CurrentCollectorMaterial, InsulationMaterial


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
            binders={
                binder1: 3, 
                binder2: 2
            },
            conductive_additives={
                conductive_additive1: 3, 
                conductive_additive2: 2
            }
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
            insulation_width=10
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 95%")

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=25
        )
        
    def test_electrodes(self):

        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.cathode.current_collector, PunchedCurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, CathodeFormulation))

        self.assertEqual(
            self.cathode.mass_breakdown, 
            {'NaNiMn P2-O3 Composite': 16.7, 
             'PVDF': 0.23, 
             'CMC': 0.13, 
             'Super P': 0.25, 
             'Graphite': 0.19, 
             'Punched Current Collector': 2.77, 
             'Aluminium Oxide, 95%': 0.41}
        )

        self.assertEqual(
            self.cathode.cost_breakdown,
            {'NaNiMn P2-O3 Composite': 0.17, 
             'PVDF': 0.05, 
             'CMC': 0.0, 
             'Super P': 0.01, 
             'Graphite': 0.0, 
             'Punched Current Collector': 0.01, 
             'Aluminium Oxide, 95%': 0.01}
        )

        self.assertEqual(round(sum([a for a in self.cathode._mass_breakdown.values()]), 2), round(self.cathode._mass, 2))
        self.assertEqual(round(sum([a for a in self.cathode._cost_breakdown.values()]), 2), round(self.cathode._cost, 2))

        self.assertEqual(self.cathode.calender_density, 2.60)
        self.assertEqual(self.cathode.mass_loading, 10.68)
        self.assertEqual(self.cathode.insulation_thickness, 25)
        self.assertEqual(self.cathode.coating_mass, 17.49)
        self.assertEqual(self.cathode.coating_thickness, 41.08)
        self.assertEqual(self.cathode.mass, 20.67)

    def test_half_cell_curve(self):

        self.cathode.voltage_cutoff = 4.
        figure = self.cathode.plot_half_cell_curve(areal=True)
        # figure.show()

    def test_views(self):

        figure1 = self.cathode.get_a_side_view(width=900, height=600)
        figure2 = self.cathode.get_b_side_view(width=900, height=600)
        figure3 = self.cathode.get_end_view(width=900, height=600)
        
        # figure1.show()
        # figure2.show()
        # figure3.show()

    def test_datum_setter(self):

        figure1 = self.cathode.get_a_side_view(with_dimensions=False)
        figurea = self.cathode.get_end_view()
        
        new_datum = (
            self.cathode._current_collector.x_body_length,
            self.cathode._current_collector.y_body_length,
            self.cathode._thickness * 1e3
        )

        self.cathode.datum = new_datum

        figure2 = self.cathode.get_a_side_view(with_dimensions=False)
        figureb = self.cathode.get_end_view()

        figure_top = go.Figure(data=figure1.data + figure2.data)
        figure_end = go.Figure(data=figurea.data + figureb.data)
        
        # figure_top.show()
        # figure_end.show()


class TestCathodeTwoMaterialNotched(unittest.TestCase):

    def setUp(self):
        
        material1 = CathodeMaterial.from_database("LFP")
        material2 = CathodeMaterial.from_database("NMC811")
        material2.extrapolation_window = 0.5

        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("PVDF")

        formulation = CathodeFormulation(
            active_materials={
                material1: 67, 
                material2: 28
            },
            binders={
                binder: 2
            },
            conductive_additives={
                conductive_additive: 3
            }
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
            coated_tab_height=2
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10
        )

        self.cathode.voltage_cutoff = 4.1

    def test_electrodes(self):
        
        self.assertTrue(isinstance(self.cathode, Cathode))

        self.assertTrue(
            self.cathode.mass_breakdown,
            {'LFP': 103.43, 
             'NMC811': 57.63, 
             'PVDF': 1.53, 
             'Super P': 2.57, 
             'Notched Current Collector': 106.21, 
             'Aluminium Oxide, 99.5%': 1.6}
        )

        self.assertTrue(
            self.cathode.cost_breakdown,
            {'LFP': 0.66, 
             'NMC811': 1.16, 
             'PVDF': 0.31, 
             'Super P': 0.07, 
             'Notched Current Collector': 0.64, 
             'Aluminium Oxide, 99.5%': 0.0}
        )

        self.assertEqual(round(sum([a for a in self.cathode._mass_breakdown.values()]), 2), round(self.cathode._mass, 2))
        self.assertEqual(round(sum([a for a in self.cathode._cost_breakdown.values()]), 2), round(self.cathode._cost, 2))

    def test_half_cell_curve(self):
        figure1 = self.cathode.plot_half_cell_curve()
        figure2 = self.cathode.plot_half_cell_curve(areal=True)
        # figure1.show()
        # figure2.show()

    def test_views(self):
        figure1 = self.cathode.get_a_side_view(width=900, height=600)
        figure2 = self.cathode.get_b_side_view(width=900, height=600)
        figure3 = self.cathode.get_end_view(width=900, height=600)
        # figure1.show()
        # figure2.show()
        # figure3.show()


class testAnodeTabWelded(unittest.TestCase):

    def setUp(self):
        
        active_material = AnodeMaterial.from_database("Synthetic Graphite")
        conductive_additive = ConductiveAdditive.from_database("Super P")
        binder = Binder.from_database("CMC")

        formulation = AnodeFormulation(
            active_materials={
                active_material: 90
            },
            binders={
                binder: 5
            },
            conductive_additives={
                conductive_additive: 5
            }
        )

        tab_material = CurrentCollectorMaterial.from_database("Copper")

        tab = WeldTab(
            material=tab_material,
            width=10,
            length=110,
            thickness=10
        )

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
            tab_weld_side='a'
        )

        self.anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60
        )

        self.anode.voltage_cutoff = 0.02

    def test_electrodes(self):

        self.assertTrue(isinstance(self.anode, Anode))
        self.assertTrue(isinstance(self.anode.current_collector, TabWeldedCurrentCollector))
        self.assertTrue(isinstance(self.anode.formulation, AnodeFormulation))

        self.assertEqual(
            self.anode.mass_breakdown, 
            {'Synthetic Graphite': 97.73, 
             'CMC': 0.77, 
             'Super P': 0.96, 
             'Tab Welded Current Collector': 46.37}
        )

        self.assertEqual(
            self.anode.cost_breakdown,
            {'Synthetic Graphite': 0.22, 
             'CMC': 0.05, 
             'Super P': 0.07, 
             'Tab Welded Current Collector': 0.28}
        )

        self.assertEqual(round(sum([a for a in self.anode._mass_breakdown.values()]), 2), round(self.anode._mass, 2))
        self.assertEqual(round(sum([a for a in self.anode._cost_breakdown.values()]), 2), round(self.anode._cost, 2))

    def test_half_cell_curve(self):

        figure1 = self.anode.plot_half_cell_curve()
        figure2 = self.anode.plot_half_cell_curve(areal=True)

        # figure1.show()
        # figure2.show()

    def test_views(self):

        figure1 = self.anode.get_a_side_view(width=900, height=600)
        figure2 = self.anode.get_b_side_view(width=900, height=600)
        figure3 = self.anode.get_end_view(width=900, height=600)

        # figure1.show()
        # figure2.show()
        # figure3.show()
