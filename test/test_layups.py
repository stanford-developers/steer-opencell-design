import unittest
import plotly.express as px
import plotly.graph_objects as go
from OpenCell.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from OpenCell.Constructions.Electrodes import Cathode, Anode
from OpenCell.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from OpenCell.Materials.CurrentCollectors import NotchedCurrentCollector, WeldTab, TabWeldedCurrentCollector, PunchedCurrentCollector
from OpenCell.Materials.RawMaterials import CurrentCollectorMaterial, InsulationMaterial, SeparatorMaterial
from OpenCell.Formulations.Layups import Layup
from OpenCell.Materials.Separators import Separator


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

        cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10
        )

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

        current_collector_material = CurrentCollectorMaterial.from_database("Aluminum")

        current_collector = NotchedCurrentCollector(
            material=current_collector_material,
            length=4500,
            width=306,
            thickness=8,
            tab_width=60,
            tab_spacing=100,
            tab_height=18,
            insulation_width=6,
            coated_tab_height=2
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10
        )

        separator_material = SeparatorMaterial.from_database(name='Cellulose')

        top_separator = Separator(
            material=separator_material,
            thickness=25,
            width=310
        )

        bottom_separator = Separator(
            material=separator_material,
            thickness=25,
            width=310
        )

        self.layup = Layup(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator
        )

    def test_layup(self):
        # This is a placeholder for an actual test
        self.assertTrue(isinstance(self.layup, Layup))

    def test_plots(self):

        figure1 = self.layup.get_a_side_view()
        figure2 = self.layup.get_b_side_view()
        figure3 = self.layup.get_end_view()

        figure1.show()
        # figure2.show()
        # figure3.show()

    def test_overhangs(self):

        self.layup.anode.top_overhang = 0

        figure1 = self.layup.get_a_side_view()
        figure1.show()

