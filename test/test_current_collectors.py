import unittest
from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial
from SteerEnergyStorage.Materials.CurrentCollectors import PunchedCurrentCollector, NotchedCurrentCollector, TablessCurrentCollector


class TestPunchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")

        self.current_collector = PunchedCurrentCollector(material=self.material,
                                                         width=160,
                                                         height=108,
                                                         thickness=8,
                                                         tab_width=20,
                                                         tab_height=10,
                                                         tab_position=20,
                                                         coated_tab_height=2)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, PunchedCurrentCollector)
        self.assertEqual(self.current_collector.width, 160)
        self.assertEqual(self.current_collector.height, 108)
        self.assertEqual(self.current_collector.thickness, 8)
        self.assertEqual(self.current_collector.tab_width, 20)
        self.assertEqual(self.current_collector.tab_height, 10)
        self.assertEqual(self.current_collector.tab_position, 20)
        self.assertEqual(self.current_collector.coated_tab_height, 2)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000008)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.02)
        self.assertEqual(round(self.current_collector._tab_height, 6), 0.01)
        self.assertEqual(round(self.current_collector._tab_position, 6), 0.02)
        self.assertEqual(round(self.current_collector._coated_tab_height, 6), 0.002)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_a.show()


class TestNotchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(material=self.material,
                                                         thickness=15, 
                                                         length=2100,
                                                         width=108,
                                                         tab_width=30,
                                                         tab_spacing=50,
                                                         tab_height=7,
                                                         bare_lengths_a_side=(15, 80),
                                                         bare_lengths_b_side=(20, 80),
                                                         coated_tab_height=2)
        
    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, NotchedCurrentCollector)
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 2100)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.tab_width, 30)
        self.assertEqual(self.current_collector.tab_spacing, 50)
        self.assertEqual(self.current_collector.tab_height, 7)
        self.assertEqual(self.current_collector.bare_lengths_a_side, (15, 80))
        self.assertEqual(self.current_collector.bare_lengths_b_side, (20, 80))
        self.assertEqual(self.current_collector.coated_tab_height, 2)
        self.assertEqual(self.current_collector.total_height, 108+7)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.03)
        self.assertEqual(round(self.current_collector._tab_spacing, 6), 0.05)
        self.assertEqual(round(self.current_collector._tab_height, 6), 0.007)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[0], 6), 0.015)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[0], 6), 0.02)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._coated_tab_height, 6), 0.002)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()
        fig_a.show()
        fig_b.show()


class TestTablessCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")

        self.current_collector = TablessCurrentCollector(material=self.material,
                                                         thickness=8,
                                                         length=2000,
                                                         width=108,
                                                         coated_width=100,
                                                         bare_lengths_a_side= (15, 80),
                                                         bare_lengths_b_side=(30, 140))
        
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
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[0], 6), 0.015)
        self.assertEqual(round(self.current_collector._bare_lengths_a_side[1], 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[0], 6), 0.03)
        self.assertEqual(round(self.current_collector._bare_lengths_b_side[1], 6), 0.14)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()
        fig_a.show()
        fig_b.show()




# class TestWeldTab(unittest.TestCase):

#     def setUp(self):
#         """
#         Set up
#         """
#         self.weldtab = WeldTab(formula='Cu', thickness=8, length=115, width=10)
        
#     def test_weldtab(self):
#         """
#         Test instantiation
#         """
#         self.assertIsInstance(self.weldtab, WeldTab)
#         self.assertEqual(self.weldtab.formula, "Cu")
#         self.assertEqual(self.weldtab.thickness, 8)
#         self.assertEqual(self.weldtab.length, 115)
#         self.assertEqual(self.weldtab.width, 10)
#         self.assertEqual(round(self.weldtab._thickness, 6), 0.000008)
#         self.assertEqual(round(self.weldtab._length, 6), 0.115)
#         self.assertEqual(round(self.weldtab._width, 6), 0.01)


# class TestTabWeldedCurrentCollector(unittest.TestCase):

#     def setUp(self):
#         """
#         Set up
#         """
#         weldtab = WeldTab(formula='Cu', thickness=8, length=115, width=10)

#         self.current_collector = TabWeldedCurrentCollector(formula="Al",
#                                                            thickness=15,
#                                                            length=820,
#                                                            width=108,
#                                                            weld_tab=weldtab,
#                                                            weld_tab_spacing=350,
#                                                            first_tab_spacing=80,
#                                                            bare_length=60)
        
#     def test_current_collector(self):
#         """
#         Test instantiation
#         """
#         self.assertIsInstance(self.current_collector, TabWeldedCurrentCollector)
#         self.assertEqual(self.current_collector.formula, "Al")
#         self.assertEqual(self.current_collector.thickness, 15)
#         self.assertEqual(self.current_collector.length, 820)
#         self.assertEqual(self.current_collector.width, 108)
#         self.assertEqual(self.current_collector.weld_tab_spacing, 350)
#         self.assertEqual(self.current_collector.first_tab_spacing, 80)
#         self.assertEqual(self.current_collector.bare_length, 60)

#         self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
#         self.assertEqual(round(self.current_collector._length, 6), 0.82)
#         self.assertEqual(round(self.current_collector._width, 6), 0.108)
#         self.assertEqual(round(self.current_collector._weld_tab_spacing, 6), 0.35)
#         self.assertEqual(round(self.current_collector._first_tab_spacing, 6), 0.08)
#         self.assertEqual(round(self.current_collector._bare_length, 6), 0.06)
#         self.assertIsInstance(self.current_collector._weld_tabs[0], WeldTab)

#         self.assertEqual(self.current_collector.area, 885.6)
#         self.assertEqual(self.current_collector.bare_area, 8640)
#         self.assertEqual(self.current_collector.coated_area, 799.2)
#         self.assertEqual(self.current_collector.cost, 0.01)
#         self.assertEqual(self.current_collector.density, 2.7)
#         self.assertEqual(self.current_collector.mass, 3.91)

#         self.assertEqual(round(self.current_collector._area, 6), 0.08856)
#         self.assertEqual(round(self.current_collector._bare_area, 6), 0.00864)
#         self.assertEqual(round(self.current_collector._coated_area, 6), 0.07992)
#         self.assertEqual(round(self.current_collector._cost, 6), 0.012843)
#         self.assertEqual(round(self.current_collector._density, 6), 2700)
#         self.assertEqual(round(self.current_collector._mass, 6), 0.003908)

#         fig = self.current_collector.get_top_down_view()
#         # fig.show()
