import unittest
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, NotchedCurrentCollector

class TestCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.current_collector = CurrentCollector(formula="Al", 
                                                     thickness=15, 
                                                     length=16.0,
                                                     width=10.8,
                                                     bare_area=8.22)

    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, CurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 16.0)
        self.assertEqual(self.current_collector.width, 10.8)
        self.assertEqual(self.current_collector.bare_area, 8.22)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.16)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._bare_area, 6), 0.000822)
        # self.current_collector.show()


class TestNotchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.current_collector = NotchedCurrentCollector(formula="Al", 
                                                         thickness=15, 
                                                         length=85,
                                                         width=10.8,
                                                         tab_width=1,
                                                         tab_length=5,
                                                         tab_spacing=5,
                                                         bare_length=6)
        
    def test_current_collector(self):
        """
        Test instantiation
        """
        self.assertIsInstance(self.current_collector, NotchedCurrentCollector)
        self.assertEqual(self.current_collector.formula, "Al")
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.length, 85)
        self.assertEqual(self.current_collector.width, 10.8)
        self.assertEqual(self.current_collector.tab_width, 1)
        self.assertEqual(self.current_collector.tab_length, 5)
        self.assertEqual(self.current_collector.tab_spacing, 5)
        self.assertEqual(self.current_collector.bare_length, 6)
        self.assertEqual(round(self.current_collector._thickness, 6), 0.000015)
        self.assertEqual(round(self.current_collector._length, 6), 0.85)
        self.assertEqual(round(self.current_collector._width, 6), 0.108)
        self.assertEqual(round(self.current_collector._tab_width, 6), 0.01)
        self.assertEqual(round(self.current_collector._tab_length, 6), 0.05)
        self.assertEqual(round(self.current_collector._tab_spacing, 6), 0.05)
        self.assertEqual(round(self.current_collector._bare_length, 6), 0.06)
        self.current_collector.show()
