import unittest
from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial
from SteerEnergyStorage.Materials.CurrentCollectors import PunchedCurrentCollector, NotchedCurrentCollector, TablessCurrentCollector, WeldTab, TabWeldedCurrentCollector


class TestPunchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")

        self.current_collector = PunchedCurrentCollector(
            material=self.material,
            width=160,
            height=108,
            thickness=8,
            tab_width=20,
            tab_height=12,
            tab_position=20,
            coated_tab_height=3,
            insulation_width=5
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
        self.assertEqual(self.current_collector.body_area, 17520)
        self.assertEqual(self.current_collector.coated_area, 2 * 16960)
        self.assertEqual(self.current_collector.insulation_area, 760)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        # fig_a.show()


class TestNotchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(material=self.material,
                                                         thickness=15, 
                                                         length=3000,
                                                         width=108,
                                                         tab_width=30,
                                                         tab_spacing=50,
                                                         tab_height=7,
                                                         bare_lengths_a_side=(15, 80),
                                                         bare_lengths_b_side=(20, 80),
                                                         coated_tab_height=2,
                                                         insulation_width=4)
        
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
        self.assertEqual(round(self.current_collector.body_area, 6), 336600)
        self.assertEqual(round(self.current_collector.coated_area, 6), 307930 + 307400)
        self.assertEqual(round(self.current_collector.insulation_area, 6), 18580)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()
        # fig_a.show()
        # fig_b.show()


class TestNotchedCurrentCollector2(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.current_collector = NotchedCurrentCollector(material=self.material,
                                                         thickness=15, 
                                                         length=3000,
                                                         width=108,
                                                         tab_width=30,
                                                         tab_spacing=50,
                                                         tab_height=7,
                                                         bare_lengths_a_side=(15, 80),
                                                         bare_lengths_b_side=(20, 80),
                                                         coated_tab_height=4,
                                                         insulation_width=2)
        
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
        self.assertEqual(round(self.current_collector.body_area, 6), 336600)
        self.assertEqual(round(self.current_collector.coated_area, 6), 633910)
        self.assertEqual(round(self.current_collector.insulation_area, 6), 6970)

    def test_figures(self):
        fig_a = self.current_collector.get_a_side_view()
        fig_b = self.current_collector.get_b_side_view()
        # fig_a.show()
        # fig_b.show()


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
                                                         bare_lengths_a_side=(15, 80),
                                                         bare_lengths_b_side=(30, 140),
                                                         insulation_width=3)
        
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
        # fig_a.show()
        # fig_b.show()


class TestWeldTab(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.material = CurrentCollectorMaterial.from_database(name="Copper")
    
        self.weldtab = WeldTab(
            material=self.material,
            width=5,
            length=115,
            thickness=20
        )
        
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
        self.assertEqual(self.weldtab._area, 0.000575)

    def test_plots(self):
        """
        Test plots
        """
        fig = self.weldtab.get_view()
        # fig.show()


class TestTabWeldedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        self.tab_material = CurrentCollectorMaterial.from_database(name="Copper")
        self.cc_material = CurrentCollectorMaterial.from_database(name="Aluminum")

        self.weld_tab = WeldTab(
            material=self.tab_material,
            width=5,
            length=115,
            thickness=20
        )

        self.current_collector = TabWeldedCurrentCollector(
            material=self.cc_material,
            weld_tab=self.weld_tab,
            length=820,
            width=108,
            thickness=15,
            weld_tab_positions=[30, 100, 500],
            skip_coat_width=20,
            tab_weld_side='a',
            tab_overhang=10,
            bare_lengths_a_side=(15, 80),
            bare_lengths_b_side=(20, 80)
        )

    def test_current_collector(self):
        self.assertIsInstance(self.current_collector, TabWeldedCurrentCollector)
        self.assertEqual(self.current_collector.length, 820)
        self.assertEqual(self.current_collector.width, 108)
        self.assertEqual(self.current_collector.thickness, 15)
        self.assertEqual(self.current_collector.weld_tab_positions, [30, 100, 500])
        self.assertEqual(self.current_collector.skip_coat_width, 20)
        self.assertEqual(self.current_collector.tab_weld_side, 'a')
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
        self.assertEqual(self.current_collector.body_area, 88560)
        self.assertEqual(self.current_collector.coated_area, 143640)
        self.assertEqual(self.current_collector.insulation_area, 0)

    def test_plots(self):
        """
        Test plots
        """
        # fig = self.current_collector.get_a_side_view()
        fig1 = self.current_collector.get_a_side_view()
        fig2 = self.current_collector.get_b_side_view()
        fig1.show()
        fig2.show()
 



