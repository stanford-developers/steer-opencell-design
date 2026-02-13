import unittest
from pickle import loads, dumps
from base64 import b64decode, b64encode
from copy import deepcopy

from steer_opencell_design.Materials.Other import CurrentCollectorMaterial
from steer_opencell_design.Components.CurrentCollectors.Punched import PunchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Notched import NotchedCurrentCollector
from steer_opencell_design.Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector, WeldTab
from steer_opencell_design.Components.CurrentCollectors.Tabless import TablessCurrentCollector

import plotly.graph_objects as go


class TestPunchedCurrentCollector(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial(
            name="Copper", 
            density=8.96, 
            specific_cost=18.1, 
            color="#B87333"
        )
    
        self.current_collector = PunchedCurrentCollector(
            material=self.material,
            width=160,
            height=108,
            thickness=8,
            tab_width=20,
            tab_height=12,
            tab_position=20,
            coated_tab_height=3,
            insulation_width=5,
        )

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, PunchedCurrentCollector)
        self.assertEqual(self.current_collector.width, 160)
        self.assertEqual(self.current_collector.height, 108)
        self.assertEqual(self.current_collector.thickness, 8)
        self.assertEqual(self.current_collector.tab_width, 20)
        self.assertEqual(self.current_collector.tab_height, 12)
        self.assertEqual(self.current_collector.tab_position, 20)
        self.assertEqual(self.current_collector.coated_tab_height, 3)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000008)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.02)
        self.assertEqual(round(self.current_collector._tab_height, 6), 0.012)
        self.assertEqual(round(self.current_collector._tab_position, 6), 0.02)
        self.assertEqual(round(self.current_collector._coated_tab_height, 6), 0.003)
        self.assertEqual(self.current_collector.foil_area, 350.4)
        self.assertEqual(self.current_collector.coated_area, 2 * 169.6)
        self.assertEqual(self.current_collector.insulation_area, 7.6)

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)

    def test_figures_and_datum_setter(self):
        fig_a = self.current_collector.get_top_down_view()

        self.current_collector.datum = (100, 50, 0)
        fig_b = self.current_collector.get_top_down_view()

        # fig_a.show()
        # fig_b.show()

        self.assertTrue(True)

    def test_flip_about_y_axis(self):
        self.current_collector.datum = (1000, 1000, 500)
        fig_a = self.current_collector.get_top_down_view()
        fig_b = self.current_collector._flip("y").get_top_down_view()

        # fig_a.show()
        # fig_b.show()

        self.assertTrue(True)

    def test_views(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()

        # fig_a.show()
        # fig_b.show()

        self.assertTrue(True)

    def test_pickle_unpickle(self):
        serialized = dumps(self.current_collector)
        encoded = b64encode(serialized).decode("utf-8")
        decoded = b64decode(encoded)
        deserialized = loads(decoded)

        self.assertEqual(self.current_collector.material.mass, deserialized.material.mass)
        self.assertEqual(self.current_collector.material.cost, deserialized.material.cost)
        self.assertEqual(self.current_collector.material.name, deserialized.material.name)
        self.assertEqual(self.current_collector.width, deserialized.width)
        self.assertEqual(self.current_collector.height, deserialized.height)

    def test_setters(self):
        self.current_collector.width = 200
        self.assertEqual(self.current_collector.width, 200)

    def test_rotate(self):
        figure1 = self.current_collector.get_top_down_view()
        self.current_collector.rotate_90()
        figure2 = self.current_collector.get_top_down_view()

        # figure1.show()
        # figure2.show()

    def test_insulation_width_to_zero(self):
        old_coated_area = self.current_collector.coated_area
        old_insulation_area = self.current_collector.insulation_area

        self.current_collector.insulation_width = 0
        self.assertNotEqual(self.current_collector.coated_area, old_coated_area)
        self.assertNotEqual(self.current_collector.insulation_area, old_insulation_area)

    def test_flip_and_setter(self):
        fig1 = self.current_collector.get_top_down_view()

        self.current_collector._flip("y")
        fig2 = self.current_collector.get_top_down_view()

        self.current_collector.width = 200
        fig3 = self.current_collector.get_top_down_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()


class TestNotchedCurrentCollector(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(
            material=self.material,
            thickness=15,
            length=3000,
            width=108,
            tab_width=30,
            tab_spacing=50,
            tab_height=7,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(20, 80),
            coated_tab_height=2,
            insulation_width=4,
        )

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, NotchedCurrentCollector)
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 3000)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.tab_width, 30)
        self.assertEqual(self.current_collector.tab_spacing, 50)
        self.assertEqual(self.current_collector.tab_height, 7)
        self.assertEqual(self.current_collector.bare_lengths_a_side, (15, 80))
        self.assertEqual(self.current_collector.bare_lengths_b_side, (20, 80))
        self.assertEqual(self.current_collector.coated_tab_height, 2)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.03)
        self.assertEqual(round(self.current_collector._tab_spacing, 6), 0.05)
        self.assertEqual(round(self.current_collector._tab_height, 6), 0.007)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[0], 6), 0.015)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[0], 6), 0.02)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._coated_tab_height, 6), 0.002)
        self.assertEqual(round(self.current_collector.foil_area, 6), 6732)
        self.assertEqual(round(self.current_collector.coated_area, 6), 3079.3 + 3074)
        self.assertEqual(round(self.current_collector.insulation_area, 6), 185.8)
        self.assertEqual(self.current_collector.material.cost, 0.17)
        self.assertEqual(self.current_collector.material.mass, 13.63)

    def test_figures(self):
        fig_b = self.current_collector.get_top_down_view()
        fig_c = self.current_collector.get_a_side_view()
        fig_d = self.current_collector.get_b_side_view()

        # fig_b.show(renderer='browser')
        # fig_c.show(renderer='browser')
        # fig_d.show(renderer='browser')

    def test_setters(self):
        self.current_collector.material = CurrentCollectorMaterial.from_database(name="Copper")
        self.assertEqual(self.current_collector.material.name, "Copper")
        self.assertEqual(self.current_collector.material.mass, 45.24)
        self.assertEqual(self.current_collector.material.cost, 0.82)

        self.current_collector.thickness = 10
        self.assertEqual(self.current_collector.thickness, 10)
        self.assertEqual(self.current_collector.material.mass, 30.16)
        self.assertEqual(self.current_collector.material.cost, 0.55)

        self.current_collector.bare_lengths_a_side = (100, 100)
        self.assertEqual(self.current_collector.material.mass, 30.16)
        self.assertEqual(self.current_collector.material.cost, 0.55)

        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()

        # fig_a.show()
        # fig_b.show()

    def test_datum_shifter(self):
        self.current_collector.length = 300
        fig11 = self.current_collector.get_top_down_view()

        self.current_collector.datum = (200, 150, 50)
        fig21 = self.current_collector.get_top_down_view()

        figure1 = go.Figure(data=fig11.data + fig21.data)

        # figure1.show()

    def test_to_tabless(self):
        new_current_collector = TablessCurrentCollector.from_notched(self.current_collector)
        self.assertIsInstance(new_current_collector, TablessCurrentCollector)

    def test_flip_and_set_datum(self):
        self.current_collector.length = 300
        fig11 = self.current_collector.get_top_down_view()
        self.current_collector._flip("y")
        self.current_collector.datum = (200, 150, 50)
        fig21 = self.current_collector.get_top_down_view()

        figure1 = go.Figure(data=fig11.data + fig21.data)
        # figure1.show()

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)


class TestNotchedCurrentCollector2(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(
            material=self.material,
            thickness=15,
            length=3000,
            width=108,
            tab_width=30,
            tab_spacing=50,
            tab_height=7,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(20, 80),
            coated_tab_height=4,
            insulation_width=2,
        )

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, NotchedCurrentCollector)
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 3000)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.tab_width, 30)
        self.assertEqual(self.current_collector.tab_spacing, 50)
        self.assertEqual(self.current_collector.tab_height, 7)
        self.assertEqual(self.current_collector.bare_lengths_a_side, (15, 80))
        self.assertEqual(self.current_collector.bare_lengths_b_side, (20, 80))
        self.assertEqual(self.current_collector.coated_tab_height, 4)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.03)
        self.assertEqual(round(self.current_collector._tab_spacing, 6), 0.05)
        self.assertEqual(round(self.current_collector._tab_height, 6), 0.007)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[0], 6), 0.015)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[0], 6), 0.02)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._coated_tab_height, 6), 0.004)
        self.assertEqual(round(self.current_collector.foil_area, 6), 6732)
        self.assertEqual(round(self.current_collector.coated_area, 6), 6339.1)
        self.assertEqual(round(self.current_collector.insulation_area, 6), 69.7)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()

        # fig_a.show()
        # fig_b.show()


class TestNotchedCurrentCollector3(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(
            material=self.material,
            thickness=15,
            length=3000,
            width=108,
            tab_width=30,
            tab_spacing=50,
            tab_height=7,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(20, 80),
            coated_tab_height=0,
            insulation_width=0,
        )

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)

    def test_serialization(self):
        serialized = self.current_collector.serialize()
        deserialized = NotchedCurrentCollector.deserialize(serialized)
        self.assertEqual(self.current_collector, deserialized)

    def test_current_collector(self):
        """
        Test figures
        """
        fig1 = self.current_collector.get_top_down_view()

        self.current_collector.insulation_width = 4
        self.current_collector.coated_tab_height = 2
        fig2 = self.current_collector.get_top_down_view()

        # fig1.show()
        # fig2.show()


class TestTablessCurrentCollector(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")

        self.current_collector = TablessCurrentCollector(
            material=self.material,
            thickness=8,
            length=2000,
            width=108,
            coated_width=100,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(30, 140),
            insulation_width=8,
        )

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, TablessCurrentCollector)
        self.assertEqual(self.current_collector.thickness, 8)
        self.assertEqual(self.current_collector.length, 2000)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.coated_width, 100)
        self.assertEqual(self.current_collector.bare_lengths_a_side, (15, 80))
        self.assertEqual(self.current_collector.bare_lengths_b_side, (30, 140))
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000008)
        self.assertEqual(round(self.current_collector._coated_width, 6), 0.1)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()
        fig_c = self.current_collector.get_right_left_view()
        fig_d = self.current_collector.get_top_down_view()

        # fig_a.show(renderer='browser')
        # fig_b.show(renderer='browser')
        # fig_c.show(renderer='browser')
        # fig_d.show(renderer='browser')

    def test_width_setter(self):
        """
        Test width setter
        """
        fig1 = self.current_collector.get_top_down_view()
        self.assertEqual(self.current_collector.coated_width, 100)

        self.current_collector.width = 208
        fig2 = self.current_collector.get_top_down_view()
        self.assertEqual(self.current_collector.width, 208)
        self.assertEqual(self.current_collector.coated_width, 200)

        # fig1.show()
        # fig2.show()

    def test_tab_height_setter(self):
        """
        Test tab height setter
        """
        fig1 = self.current_collector.get_top_down_view()
        self.assertEqual(self.current_collector.tab_height, 8)

        self.current_collector.tab_height = 20
        fig2 = self.current_collector.get_top_down_view()
        self.assertEqual(self.current_collector.tab_height, 20)

        # fig1.show()
        # fig2.show()

    def test_to_notched(self):
        new_current_collector = NotchedCurrentCollector.from_tabless(self.current_collector)
        self.assertIsInstance(new_current_collector, NotchedCurrentCollector)


class TestWeldTab(unittest.TestCase):
    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")

        self.weldtab = WeldTab(material=self.material, width=5, length=115, thickness=20)

    def test_equality(self):
        copy_cc = deepcopy(self.weldtab)
        condition = copy_cc == self.weldtab
        self.assertTrue(condition)

    def test_weldtab(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.weldtab, WeldTab)
        self.assertEqual(self.weldtab.width, 5)
        self.assertEqual(self.weldtab.length, 115)
        self.assertEqual(self.weldtab.thickness, 20)
        self.assertEqual(round(self.weldtab._width, 6), 0.005)
        self.assertEqual(round(self.weldtab._length, 6), 0.115)
        self.assertEqual(round(self.weldtab._thickness, 6), 0.00002)
        self.assertEqual(self.weldtab._foil_area, 0.00115)

    def test_plots(self):
        """
        Test plots
        """
        fig1 = self.weldtab.get_view()
        fig2 = self.weldtab.get_side_view()

        # fig1.show()
        # fig2.show()


class TestTabWeldedCurrentCollector(unittest.TestCase):
    
    def setUp(self):
        """
        Set up
        """
        self.tab_material = CurrentCollectorMaterial.from_database(name="Copper")
        self.cc_material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.weld_tab = WeldTab(material=self.tab_material, width=5, length=115, thickness=20)

        self.current_collector = TabWeldedCurrentCollector(
            material=self.cc_material,
            weld_tab=self.weld_tab,
            length=820,
            width=108,
            thickness=15,
            weld_tab_positions=[30, 100, 500],
            skip_coat_width=20,
            tab_weld_side="a",
            tab_overhang=10,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(20, 80),
        )

    def test_equality(self):
        copy_cc = deepcopy(self.current_collector)
        condition = copy_cc == self.current_collector
        self.assertTrue(condition)

    def test_current_collector(self):
        self.assertIsInstance(self.current_collector, TabWeldedCurrentCollector)
        self.assertEqual(self.current_collector.length, 820)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.weld_tab_positions, [30, 100, 500])
        self.assertEqual(self.current_collector.skip_coat_width, 20)
        self.assertEqual(self.current_collector.tab_weld_side, "a")
        self.assertEqual(self.current_collector.tab_overhang, 10)
        self.assertEqual(self.current_collector.bare_lengths_a_side, (15, 80))
        self.assertEqual(self.current_collector.bare_lengths_b_side, (20, 80))
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._weld_tab_positions[0], 6), 0.03)
        self.assertEqual(round(self.current_collector._weld_tab_positions[1], 6), 0.1)
        self.assertEqual(round(self.current_collector._skip_coat_width, 6), 0.02)
        self.assertEqual(round(self.current_collector._tab_overhang, 6), 0.01)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[0], 6), 0.015)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[0], 6), 0.02)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[1], 6), 0.08)
        self.assertEqual(self.current_collector.foil_area, 1771.2)
        self.assertEqual(self.current_collector.coated_area, 1431.0)

    def test_plots(self):
        """
        Test plots
        """
        fig1 = self.current_collector.get_top_down_view()
        fig2 = self.current_collector.get_a_side_view()
        fig3 = self.current_collector.get_b_side_view()

        # fig1.show()
        # fig2.show()
        # fig3.show()

    def test_length_setter(self):
        self.current_collector.length = 2000
        self.assertEqual(self.current_collector.length, 2000)
        fig1 = self.current_collector.get_top_down_view()
        # fig1.show()

    def test_material_setter(self):
        new_material = CurrentCollectorMaterial.from_database(name="Aluminum")
        tab = self.current_collector.weld_tab
        tab.material = new_material
        self.current_collector.weld_tab = tab
        self.assertEqual(self.current_collector.weld_tab.material.name, "Aluminum")

        fig1 = self.current_collector.get_a_side_view()
        # fig1.show()

    def test_to_notched(self):
        new_current_collector = NotchedCurrentCollector.from_tab_welded(self.current_collector)
        self.assertIsInstance(new_current_collector, NotchedCurrentCollector)

        fig1 = new_current_collector.get_top_down_view()

        new_current_collector.insulation_width = 4
        new_current_collector.coated_tab_height = 2
        fig2 = new_current_collector.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_to_tabless(self):
        new_current_collector = TablessCurrentCollector.from_tab_welded(self.current_collector)
        self.assertIsInstance(new_current_collector, TablessCurrentCollector)

    def test_flip(self):
        fig1 = self.current_collector.get_top_down_view()
        self.current_collector._flip("y")
        fig2 = self.current_collector.get_top_down_view()

        # fig1.show()
        # fig2.show()

    def test_flip_and_set_datum(self):
        self.current_collector.length = 300
        fig11 = self.current_collector.get_top_down_view()
        self.current_collector._flip("y")
        self.current_collector.datum = (200, 150, 50)
        fig21 = self.current_collector.get_top_down_view()

        figure1 = go.Figure(data=fig11.data + fig21.data)
        # figure1.show()

