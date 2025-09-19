from copy import deepcopy
import unittest

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_opencell_design.Components.Electrodes import Cathode, Anode
from steer_opencell_design.Components.CurrentCollectors import NotchedCurrentCollector, PunchedCurrentCollector, TablessCurrentCollector
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.Layups import Laminate, MonoLayer, OverhangControlMode

from steer_materials.CellMaterials.Base import CurrentCollectorMaterial, InsulationMaterial, SeparatorMaterial
from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive


class TestSimpleLaminate(unittest.TestCase):

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

        self.layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator
        )

    def test_laminate(self):
        # This is a placeholder for an actual test
        self.assertTrue(isinstance(self.layup, Laminate))
        self.assertEqual(self.layup.anode_overhangs, {'left': 0, 'right': 0, 'top': 3, 'bottom': 3})
        self.assertEqual(self.layup.bottom_separator_overhangs, {'left': 150, 'right': 150, 'top': 5, 'bottom': 5})
        self.assertEqual(self.layup.top_separator_overhangs, {'left': 150, 'right': 150, 'top': 5, 'bottom': 5})

    def test_plots(self):

        fig1 = self.layup.anode._get_full_top_down_view()
        fig2 = self.layup.cathode._get_full_top_down_view()
        fig3 = self.layup.get_top_down_view(opacity=0.2)

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_change_anode_material(self):

        anode = deepcopy(self.layup.anode)
        fig1 = anode._get_full_top_down_view()

        new_cc_material = CurrentCollectorMaterial.from_database("Copper")
        current_collector = anode.current_collector
        current_collector.material = new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig2 = self.layup.anode._get_full_top_down_view()

        new_new_cc_material = CurrentCollectorMaterial.from_database("Aluminum")
        current_collector = anode.current_collector
        current_collector.material = new_new_cc_material
        anode.current_collector = current_collector
        self.layup.anode = anode
        fig3 = self.layup.anode._get_full_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_double_set(self):

        self.layup.anode.current_collector.width = 100
        self.layup.anode.current_collector = deepcopy(self.layup.anode.current_collector)
        self.layup.anode = deepcopy(self.layup.anode)

        self.layup.anode.current_collector.width = 500
        self.layup.anode.current_collector = deepcopy(self.layup.anode.current_collector)
        self.layup.anode = deepcopy(self.layup.anode)

        fig1 = self.layup.anode._get_full_top_down_view()

        # fig1.show()

    def test_ranges_tabless(self):

        anode_cc = self.layup.anode.current_collector
        new_anode_cc = TablessCurrentCollector.from_notched(anode_cc)
        self.layup.anode.current_collector = new_anode_cc
        self.layup.anode = self.layup.anode

        cathode_cc = self.layup.cathode.current_collector
        new_cathode_cc = TablessCurrentCollector.from_notched(cathode_cc)
        self.layup.cathode.current_collector = new_cathode_cc
        self.layup.cathode = self.layup.cathode

        cathode_coated_width = self.layup.cathode.current_collector.coated_width
        self.assertEqual(self.layup.anode.current_collector.coated_width_range[0], cathode_coated_width)

        fig1 = self.layup.anode._get_full_top_down_view()
        fig2 = self.layup.cathode._get_full_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_component(self):

        self.layup.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.layup.anode_overhang_top = 6
        self.assertEqual(self.layup.anode_overhangs, {'left': 0, 'right': 0, 'top': 6, 'bottom': 0})
        fig1 = self.layup.get_top_down_view()

        # fig1.show()

    def test_anode_overhang_setters_fixed_overhangs(self):

        self.layup.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.layup.get_top_down_view()

        self.layup.bottom_separator_overhang_left = 10
        self.assertEqual(self.layup.bottom_separator_overhangs, {'left': 10, 'right': 150, 'top': 5, 'bottom': 5})
        fig2 = self.layup.get_top_down_view()
        
        # fig1.show()
        # fig2.show()


class TestSimpleMonoLayer(unittest.TestCase):

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

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=300,
            height=320,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50
        )

        cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
        )

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5}
        )

        current_collector = PunchedCurrentCollector(
            material=current_collector_material,
            width=304,
            height=324,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=1.1,
            insulation_thickness=10
        )

        separator_material = SeparatorMaterial(name="Polyethylene", specific_cost=2, density=0.94, color="#FDFDB7", porosity=45)

        separator = Separator(
            material=separator_material,
            thickness=25,
            width=310,
            length=326
        )

        self.monolayer = MonoLayer(
            anode=anode,
            cathode=cathode,
            top_separator=separator,
            bottom_separator=separator,
            transverse=True,
        )

    def test_monolayer(self):
        self.assertTrue(isinstance(self.monolayer, MonoLayer))

        self.assertEqual(self.monolayer.anode_overhangs, {'left': 2, 'right': 2, 'top': 2, 'bottom': 2})
        self.assertEqual(self.monolayer.bottom_separator_overhangs, {'left': 5, 'right': 5, 'top': 3, 'bottom': 3})
        self.assertEqual(self.monolayer.top_separator_overhangs, {'left': 5, 'right': 5, 'top': 3, 'bottom': 3})

    def test_plots(self):
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)
        # fig1.show()
        
    def test_anode_overhang_setters_fixed_component(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.anode_overhang_left = 4
        self.assertEqual(self.monolayer.anode_overhangs, {'left': 4, 'right': 0, 'top': 2, 'bottom': 2})
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_top = 4
        self.assertEqual(self.monolayer.anode_overhangs, {'left': 4, 'right': 0, 'top': 4, 'bottom': 0})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()

    def test_anode_overhang_setters_fixed_overhangs(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_left = 10
        self.assertEqual(self.monolayer.anode_overhangs, {'left': 10, 'right': 2, 'top': 2, 'bottom': 2})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.anode_overhang_top = 10
        self.assertEqual(self.monolayer.anode_overhangs, {'left': 10, 'right': 2, 'top': 10, 'bottom': 2})
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_bottom_separator_overhang_setters_fixed_component(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.bottom_separator_overhang_left = 8
        self.assertEqual(self.monolayer.bottom_separator_overhangs, {'left': 8, 'right': 2, 'top': 3, 'bottom': 3})
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_top = 6
        self.assertEqual(self.monolayer.bottom_separator_overhangs, {'left': 8, 'right': 2, 'top': 6, 'bottom': 0})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()

    def test_bottom_separator_overhang_setters_fixed_overhangs(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_left = 12
        self.assertEqual(self.monolayer.bottom_separator_overhangs, {'left': 12, 'right': 5, 'top': 3, 'bottom': 3})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.bottom_separator_overhang_top = 8
        self.assertEqual(self.monolayer.bottom_separator_overhangs, {'left': 12, 'right': 5, 'top': 8, 'bottom': 3})
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_top_separator_overhang_setters_fixed_component(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_COMPONENT

        self.monolayer.top_separator_overhang_left = 7
        self.assertEqual(self.monolayer.top_separator_overhangs, {'left': 7, 'right': 3, 'top': 3, 'bottom': 3})
        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_bottom = 5
        self.assertEqual(self.monolayer.top_separator_overhangs, {'left': 7, 'right': 3, 'top': 1, 'bottom': 5})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()

    def test_top_separator_overhang_setters_fixed_overhangs(self):

        self.monolayer.overhang_control_mode = OverhangControlMode.FIXED_OVERHANGS

        fig1 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_right = 15
        self.assertEqual(self.monolayer.top_separator_overhangs, {'left': 5, 'right': 15, 'top': 3, 'bottom': 3})
        fig2 = self.monolayer.get_top_down_view(opacity=0.2)

        self.monolayer.top_separator_overhang_bottom = 10
        self.assertEqual(self.monolayer.top_separator_overhangs, {'left': 5, 'right': 15, 'top': 3, 'bottom': 10})
        fig3 = self.monolayer.get_top_down_view(opacity=0.2)
        
        # fig1.show()
        # fig2.show()
        # fig3.show()




