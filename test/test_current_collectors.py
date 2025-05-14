import unittest
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, NotchedCurrentCollector, TabWeldedCurrentCollector, WeldTab, PunchedCurrentCollector


class TestPunchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.current_collector = PunchedCurrentCollector(formula="Al", 
                                                         thickness=15, 
                                                         length=160,
                                                         width=108,
                                                         tab_width=30, 
                                                         tab_height=27.4,
                                                         tab_position=30)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, CurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 160)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.bare_area, 822)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.16)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._bare_area, 6), 0.000822)
        
        fig = self.current_collector.get_top_down_view()
        # fig.show()


class TestCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=160,
                                                     width=108,
                                                     bare_area=822)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, CurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 160)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.bare_area, 822)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.16)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._bare_area, 6), 0.000822)
        
        fig = self.current_collector.get_top_down_view()
        # fig.show()


class TestNotchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.current_collector = NotchedCurrentCollector(formula="Al", 
                                                         thickness=15, 
                                                         length=850,
                                                         width=108,
                                                         tab_width=10,
                                                         tab_length=50,
                                                         tab_spacing=50,
                                                         bare_length=60)
        
    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, NotchedCurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 850)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.tab_width, 10)
        self.assertEqual(self.current_collector.tab_length, 50)
        self.assertEqual(self.current_collector.tab_spacing, 50)
        self.assertEqual(self.current_collector.bare_length, 60)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.85)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.01)
        self.assertEqual(round(self.current_collector._tab_length, 6), 0.05)
        self.assertEqual(round(self.current_collector._tab_spacing, 6), 0.05)
        self.assertEqual(round(self.current_collector._bare_length, 6), 0.06)

        fig = self.current_collector.get_top_down_view()
        # fig.show()


class TestWeldTab(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.weldtab = WeldTab(formula='Cu', thickness=8, length=115, width=10)
        
    def test_weldtab(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.weldtab, WeldTab)
        self.assertEqual(self.weldtab.formula, "Cu")
        self.assertEqual(self.weldtab.thickness, 8)
        self.assertEqual(self.weldtab.length, 115)
        self.assertEqual(self.weldtab.width, 10)
        self.assertEqual(round(self.weldtab._thickness, 6), 0.000008)
        self.assertEqual(round(self.weldtab._length, 6), 0.115)
        self.assertEqual(round(self.weldtab._width, 6), 0.01)


class TestTabWeldedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        weldtab = WeldTab(formula='Cu', thickness=8, length=115, width=10)

        self.current_collector = TabWeldedCurrentCollector(formula="Al",
                                                           thickness=15,
                                                           length=820,
                                                           width=108,
                                                           weld_tab=weldtab,
                                                           weld_tab_spacing=350,
                                                           first_tab_spacing=80,
                                                           bare_length=60)
        
    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, TabWeldedCurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 820)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.weld_tab_spacing, 350)
        self.assertEqual(self.current_collector.first_tab_spacing, 80)
        self.assertEqual(self.current_collector.bare_length, 60)

        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.82)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._weld_tab_spacing, 6), 0.35)
        self.assertEqual(round(self.current_collector._first_tab_spacing, 6), 0.08)
        self.assertEqual(round(self.current_collector._bare_length, 6), 0.06)
        self.assertIsInstance(self.current_collector._weld_tabs[0], WeldTab)

        self.assertEqual(self.current_collector.area, 885.6)
        self.assertEqual(self.current_collector.bare_area, 8640)
        self.assertEqual(self.current_collector.coated_area, 799.2)
        self.assertEqual(self.current_collector.cost, 0.01)
        self.assertEqual(self.current_collector.density, 2.7)
        self.assertEqual(self.current_collector.mass, 3.91)

        self.assertEqual(round(self.current_collector._area, 6), 0.08856)
        self.assertEqual(round(self.current_collector._bare_area, 6), 0.00864)
        self.assertEqual(round(self.current_collector._coated_area, 6), 0.07992)
        self.assertEqual(round(self.current_collector._cost, 6), 0.012843)
        self.assertEqual(round(self.current_collector._density, 6), 2700)
        self.assertEqual(round(self.current_collector._mass, 6), 0.003908)

        fig = self.current_collector.get_top_down_view()
        # fig.show()
