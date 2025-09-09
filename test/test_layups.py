import unittest

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import NotchedCurrentCollector
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups import Layup

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial, InsulationMaterial, SeparatorMaterial
from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive


class TestCathodeTwoMaterialNotched(unittest.TestCase):

    def setUp(self):

        ########################
        # make a basic cathode
        ########################
        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(name='super_P', specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name='CMC', specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3}
        )

        current_collector_material = CurrentCollectorMaterial(name='Aluminum', specific_cost=5, density=2.7, color="#AAAAAA")

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

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5}
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

        separator_material = SeparatorMaterial(name="Polyethylene", specific_cost=2, density=0.94, color="#FDFDB7", porosity=45)

        top_separator = Separator(
            material=separator_material,
            thickness=25,
            width=310,
            length=4800
        )

        bottom_separator = Separator(
            material=separator_material,
            thickness=25,
            width=310,
            length=4800
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

        fig1 = self.layup.anode._get_full_top_down_view()
        fig2 = self.layup.cathode._get_full_top_down_view()
        fig3 = self.layup._get_full_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_overhangs(self):

        self.layup.anode.top_overhang = 0

        figure1 = self.layup.get_a_side_view()
        figure1.show()

