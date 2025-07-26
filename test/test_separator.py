import unittest
from OpenCell.Materials.Separators import Separator
from OpenCell.Materials.RawMaterials import SeparatorMaterial

import pandas as pd
import plotly.express as px


class TestSimpleCathodeFormulation(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        separator_material = SeparatorMaterial.from_database(name='Nafion')
        
        self.separator1 = Separator(
            material=separator_material,
            thickness=25,
            width=50
        )

        self.separator2 = Separator(
            material=separator_material,
            thickness=25,
            length=100,
            width=50
        )

    def test_separator1_properties(self):
        """
        Test the properties of the separator
        """
        self.assertTrue(isinstance(self.separator1, Separator))
        
        with self.assertRaises(AttributeError):
            self.separator1.area
            
        with self.assertRaises(AttributeError):
            self.separator1.cost

        with self.assertRaises(AttributeError):
            self.separator1.mass

        self.assertEqual(self.separator1.length, None)

    def test_separator2_properties(self):
        """
        Test the properties of the separator with length and width set
        """
        self.assertTrue(isinstance(self.separator2, Separator))
        
        self.assertEqual(self.separator2.areal_cost, 50)
        self.assertEqual(self.separator2.area, 50.0)
        self.assertEqual(self.separator2.cost, 0.25)
        self.assertEqual(self.separator2.mass, 0.25)

        self.assertEqual(self.separator2.width, 50)
        self.assertEqual(self.separator2.length, 100)

