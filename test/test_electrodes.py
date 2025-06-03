import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, NotchedCurrentCollector, WeldTab, TabWeldedCurrentCollector

class TestWithStandardCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        #### stack 1 ####
        # construct cathode
        cathode_active_material1 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_active_material2 = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.35V", 
                                                   specific_cost=15.21, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive1 = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

        cathode_conductive_additive2 = ConductiveAdditive(specific_cost=12, density=1.0, name="Super C45")

        cathode_binder1 = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_binder2 = Binder(name="CMC", specific_cost=10, density=1.5)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material1: 59, cathode_active_material2: 31},
                                                    binders={cathode_binder1: 3, cathode_binder2: 2},
                                                    conductive_additives={cathode_conductive_additive1: 3, cathode_conductive_additive2: 2})

        cathode_current_collector = CurrentCollector(formula="Al", 
                                                      thickness=15, 
                                                      length=16.0,
                                                      width=10.8,
                                                      bare_area=8.22)

        self.cathode = Cathode(formulation=cathode_formulation,
                               mass_loading=10.68,
                               current_collector=cathode_current_collector,
                               calender_density=2.60)

        # construct anode
        anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = CurrentCollector(formula="Cu",
                                                   thickness=15,
                                                   length=16.0,
                                                   width=10.8,
                                                   bare_area=7.55)
        
        self.anode = Anode(formulation=anode_formulation,
                           mass_loading=10.68,
                           current_collector=anode_current_collector,
                           calender_density=0.85)
        
    def test_electrodes(self):

        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.anode, Anode))
        self.assertTrue(isinstance(self.cathode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.anode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode.formulation, ElectrodeFormulation))

        self.assertEqual(len(self.cathode.mass_breakdown), 4)
        self.assertEqual(len(self.anode.mass_breakdown), 4)
        self.assertEqual(len(self.cathode._mass_breakdown['active_materials']), 2)
        self.assertEqual(len(self.cathode._mass_breakdown['binders']), 2)
        self.assertEqual(len(self.cathode._mass_breakdown['conductive_additives']), 2)
        self.assertEqual(len(self.cathode.mass_breakdown['Active Materials']), 2)
        self.assertEqual(len(self.cathode.mass_breakdown['Binders']), 2)
        self.assertEqual(len(self.cathode.mass_breakdown['Conductive Additives']), 2)

        self.assertEqual(len(self.anode._mass_breakdown['active_materials']), 1)
        self.assertEqual(len(self.anode._mass_breakdown['binders']), 1)
        self.assertEqual(len(self.anode._mass_breakdown['conductive_additives']), 1)
        self.assertEqual(len(self.anode.mass_breakdown['Active Materials']), 1)
        self.assertEqual(len(self.anode.mass_breakdown['Binders']), 1)
        self.assertEqual(len(self.anode.mass_breakdown['Conductive Additives']), 1)

    def test_half_cell_curve(self):

        self.cathode._calculate_half_cell_curve(grid_n=100)
        self.anode._calculate_half_cell_curve(grid_n=100)
        data_cathode = self.cathode.half_cell_curve
        data_anode = self.anode.half_cell_curve

        # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve', 
        #         line_shape='spline', color='Direction', markers=True).show()
        
        # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
        #         line_shape='spline', color='Direction', markers=True).show()


class TestWithNotched(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        #### stack 1 ####
        # construct cathode
        cathode_active_material = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                    binders={cathode_binder: 6},
                                                    conductive_additives={cathode_conductive_additive: 5})

        cathode_current_collector = NotchedCurrentCollector(formula="Al",
                                                            length=83,
                                                            width=10.8,
                                                            thickness=15,
                                                            tab_width=1,
                                                            tab_length=5,
                                                            tab_spacing=6,
                                                            bare_length=5)

        self.cathode = Cathode(formulation=cathode_formulation,
                               mass_loading=10.68,
                               current_collector=cathode_current_collector,
                               calender_density=2.60)

        # construct anode
        anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        anode_current_collector = NotchedCurrentCollector(formula="Cu",
                                                          length=87,
                                                          width=10.8,
                                                          thickness=15,
                                                          tab_width=1,
                                                          tab_length=5,
                                                          tab_spacing=10,
                                                          bare_length=5)
        
        self.anode = Anode(formulation=anode_formulation,
                           mass_loading=10.68,
                           current_collector=anode_current_collector,
                           calender_density=0.85)
        
    def test_electrodes(self):

        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.anode, Anode))
        self.assertTrue(isinstance(self.cathode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.anode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode.formulation, ElectrodeFormulation))

    def test_current_collectors(self):

        self.assertTrue(isinstance(self.cathode.current_collector, NotchedCurrentCollector))
        self.assertTrue(isinstance(self.anode.current_collector, NotchedCurrentCollector))
        # self.cathode.current_collector.show()
        # self.anode.current_collector.show()

    def test_half_cell_curve(self):

        self.cathode._calculate_half_cell_curve(grid_n=100)
        self.anode._calculate_half_cell_curve(grid_n=100)
        data_cathode = self.cathode.half_cell_curve
        data_anode = self.anode.half_cell_curve

        # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve', 
        #         line_shape='spline', color='Direction', markers=True).show()
        
        # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
        #         line_shape='spline', color='Direction', markers=True).show()


class TestWithTabWelded(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        #### stack 1 ####
        # construct cathode
        cathode_active_material = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
                                                   specific_cost=11.26, 
                                                   density=4, 
                                                   irreversible_capacity_scaling=1, 
                                                   reversible_capacity_scaling=1)
        
        cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

        cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

        cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
                                                    binders={cathode_binder: 6},
                                                    conductive_additives={cathode_conductive_additive: 5})

        weldTab = WeldTab(formula='Al', thickness=8, length=11.5, width=1)

        cathode_current_collector = TabWeldedCurrentCollector(formula="Al",
                                                              length=83,
                                                              width=10.8,
                                                              thickness=15,
                                                              weld_tab=weldTab,
                                                              weld_tab_spacing=24,
                                                              first_tab_spacing=5,
                                                              bare_length=5)

        self.cathode = Cathode(formulation=cathode_formulation,
                               mass_loading=10.68,
                               current_collector=cathode_current_collector,
                               calender_density=2.60)

        # construct anode
        anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
                                               specific_cost=14.27,
                                               density=1.50,
                                               irreversible_capacity_scaling=1,
                                               reversible_capacity_scaling=1)
        
        anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

        anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

        anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
                                                 binders={anode_binder: 3},
                                                 conductive_additives={anode_conductive_additive: 9})
        
        weldTab = WeldTab(formula='Cu', thickness=4, length=11.5, width=1)

        anode_current_collector = TabWeldedCurrentCollector(formula="Cu",
                                                            length=85,
                                                            width=10.8,
                                                            thickness=15,
                                                            weld_tab=weldTab,
                                                            weld_tab_spacing=30,
                                                            first_tab_spacing=5,
                                                            bare_length=5)
        
        self.anode = Anode(formulation=anode_formulation,
                           mass_loading=10.68,
                           current_collector=anode_current_collector,
                           calender_density=0.85)
        
    def test_electrodes(self):
        
        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.anode, Anode))
        self.assertTrue(isinstance(self.cathode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.anode.current_collector, CurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, ElectrodeFormulation))
        self.assertTrue(isinstance(self.anode.formulation, ElectrodeFormulation))

    def test_current_collectors(self):

        self.assertTrue(isinstance(self.cathode.current_collector, TabWeldedCurrentCollector))
        self.assertTrue(isinstance(self.anode.current_collector, TabWeldedCurrentCollector))
        # self.cathode.current_collector.show()
        # self.anode.current_collector.show()

    def test_half_cell_curve(self):

        self.cathode._calculate_half_cell_curve(grid_n=100)
        self.anode._calculate_half_cell_curve(grid_n=100)
        data_cathode = self.cathode.half_cell_curve
        data_anode = self.anode.half_cell_curve

        # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve', 
        #         line_shape='spline', color='Direction', markers=True).show()
        
        # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
        #         line_shape='spline', color='Direction', markers=True).show()
