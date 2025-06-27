import unittest
import plotly.express as px
from SteerEnergyStorage.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Materials.CurrentCollectors import NotchedCurrentCollector, WeldTab, TabWeldedCurrentCollector, PunchedCurrentCollector
from SteerEnergyStorage.Materials.RawMaterials import CurrentCollectorMaterial, InsulationMaterial


class TestCathodePunchedCurrentCollector(unittest.TestCase):

    def setUp(self):
        """
        Set up
        """
        active_material1 = CathodeMaterial.from_database("NaNiMn P2-O3 Composite")
        conductive_additive1 = ConductiveAdditive.from_database("Super P")
        conductive_additive2 = ConductiveAdditive.from_database("Graphite")
        binder1 = Binder.from_database("PVDF")
        binder2 = Binder.from_database("CMC")

        formulation = CathodeFormulation(
            active_materials={
                active_material1: 90, 
            },
            binders={
                binder1: 3, 
                binder2: 2
            },
            conductive_additives={
                conductive_additive1: 3, 
                conductive_additive2: 2
            }
        )

        cc_material = CurrentCollectorMaterial.from_database("Aluminum")

        current_collector = PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=280,
            thickness=12,
            tab_width=10,
            tab_height=10,
            tab_position=15,
            coated_tab_height=3,
            insulation_width=5
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 95%")

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=10.68,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=25
        )
        
    def test_electrodes(self):

        self.assertTrue(isinstance(self.cathode, Cathode))
        self.assertTrue(isinstance(self.cathode.current_collector, PunchedCurrentCollector))
        self.assertTrue(isinstance(self.cathode.formulation, CathodeFormulation))

        self.assertEqual(
            self.cathode.mass_breakdown, 
            {'NaNiMn P2-O3 Composite': 17.0, 
             'PVDF': 0.23, 
             'CMC': 0.14, 
             'Super P': 0.26, 
             'Graphite': 0.19, 
             'Punched Current Collector': 2.72, 
             'Aluminium Oxide, 95%': 0.11}
        )

        self.assertEqual(
            self.cathode.cost_breakdown,
            {'NaNiMn P2-O3 Composite': 0.18, 
             'PVDF': 0.05, 
             'CMC': 0.0, 
             'Super P': 0.01, 
             'Graphite': 0.0, 
             'Punched Current Collector': 0.01, 
             'Aluminium Oxide, 95%': 0.0}
        )

        self.assertEqual(round(sum([a for a in self.cathode.mass_breakdown.values()]), 2), self.cathode.mass)
        self.assertEqual(round(sum([a for a in self.cathode.cost_breakdown.values()]), 2), self.cathode.cost)
        self.assertEqual(self.cathode.calender_density, 2.60)
        self.assertEqual(self.cathode.mass_loading, 10.68)
        self.assertEqual(self.cathode.insulation_thickness, 25)
        self.assertEqual(self.cathode.coating_mass, 17.81)
        self.assertEqual(self.cathode.coating_thickness, 41.08)
        self.assertEqual(self.cathode.mass, 20.65)


    def test_half_cell_curve(self):

        self.cathode.voltage_cuttoff = 4.3
        figure = self.cathode.plot_half_cell_curve()
        # figure.show()


class TestCathodeTwoMaterialNotched(unittest.TestCase):

    def setUp(self):
        
        material1 = CathodeMaterial.from_database("LFP")
        material2 = CathodeMaterial.from_database("NMC811")
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
            tab_width=20,
            tab_spacing=100,
            tab_height=12,
            insulation_width=3,
            coated_tab_height=2
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        self.cathode = Cathode(
            formulation=formulation,
            mass_loading=6.2,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10
        )

        self.cathode.voltage_cuttoff = 4.1

    def test_electrodes(self):
        self.assertTrue(isinstance(self.cathode, Cathode))

    def test_half_cell_curve(self):
        figure1 = self.cathode.plot_half_cell_curve()
        figure2 = self.cathode.plot_half_cell_curve(areal=True)
        # figure1.show()
        # figure2.show()





# class TestWithNotched(unittest.TestCase):

#     def setUp(self):
#         """
#         Set up
#         """
#         #### stack 1 ####
#         # construct cathode
#         cathode_active_material = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
#                                                    specific_cost=11.26, 
#                                                    density=4, 
#                                                    irreversible_capacity_scaling=1, 
#                                                    reversible_capacity_scaling=1)
        
#         cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

#         cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

#         cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
#                                                     binders={cathode_binder: 6},
#                                                     conductive_additives={cathode_conductive_additive: 5})

#         cathode_current_collector = NotchedCurrentCollector(formula="Al",
#                                                             length=83,
#                                                             width=10.8,
#                                                             thickness=15,
#                                                             tab_width=1,
#                                                             tab_length=5,
#                                                             tab_spacing=6,
#                                                             bare_length=5)

#         self.cathode = Cathode(formulation=cathode_formulation,
#                                mass_loading=10.68,
#                                current_collector=cathode_current_collector,
#                                calender_density=2.60)

#         # construct anode
#         anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
#                                                specific_cost=14.27,
#                                                density=1.50,
#                                                irreversible_capacity_scaling=1,
#                                                reversible_capacity_scaling=1)
        
#         anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

#         anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

#         anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
#                                                  binders={anode_binder: 3},
#                                                  conductive_additives={anode_conductive_additive: 9})
        
#         anode_current_collector = NotchedCurrentCollector(formula="Cu",
#                                                           length=87,
#                                                           width=10.8,
#                                                           thickness=15,
#                                                           tab_width=1,
#                                                           tab_length=5,
#                                                           tab_spacing=10,
#                                                           bare_length=5)
        
#         self.anode = Anode(formulation=anode_formulation,
#                            mass_loading=10.68,
#                            current_collector=anode_current_collector,
#                            calender_density=0.85)
        
#     def test_electrodes(self):

#         self.assertTrue(isinstance(self.cathode, Cathode))
#         self.assertTrue(isinstance(self.anode, Anode))
#         self.assertTrue(isinstance(self.cathode.current_collector, CurrentCollector))
#         self.assertTrue(isinstance(self.anode.current_collector, CurrentCollector))
#         self.assertTrue(isinstance(self.cathode.formulation, ElectrodeFormulation))
#         self.assertTrue(isinstance(self.anode.formulation, ElectrodeFormulation))

#     def test_current_collectors(self):

#         self.assertTrue(isinstance(self.cathode.current_collector, NotchedCurrentCollector))
#         self.assertTrue(isinstance(self.anode.current_collector, NotchedCurrentCollector))
#         # self.cathode.current_collector.show()
#         # self.anode.current_collector.show()

#     def test_half_cell_curve(self):

#         self.cathode._calculate_half_cell_curve(grid_n=100)
#         self.anode._calculate_half_cell_curve(grid_n=100)
#         data_cathode = self.cathode.half_cell_curve
#         data_anode = self.anode.half_cell_curve

#         # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve', 
#         #         line_shape='spline', color='Direction', markers=True).show()
        
#         # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
#         #         line_shape='spline', color='Direction', markers=True).show()


# class TestWithTabWelded(unittest.TestCase):

#     def setUp(self):
#         """
#         Set up
#         """
#         #### stack 1 ####
#         # construct cathode
#         cathode_active_material = CathodeMaterial(name="NaNiMn P2-O3 Composite - 4.25V", 
#                                                    specific_cost=11.26, 
#                                                    density=4, 
#                                                    irreversible_capacity_scaling=1, 
#                                                    reversible_capacity_scaling=1)
        
#         cathode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9, name="Super C65")

#         cathode_binder = Binder(name="PVDF", specific_cost=15, density=1.7)

#         cathode_formulation = ElectrodeFormulation(active_materials={cathode_active_material: 89},
#                                                     binders={cathode_binder: 6},
#                                                     conductive_additives={cathode_conductive_additive: 5})

#         weldTab = WeldTab(formula='Al', thickness=8, length=11.5, width=1)

#         cathode_current_collector = TabWeldedCurrentCollector(formula="Al",
#                                                               length=83,
#                                                               width=10.8,
#                                                               thickness=15,
#                                                               weld_tab=weldTab,
#                                                               weld_tab_spacing=24,
#                                                               first_tab_spacing=5,
#                                                               bare_length=5)

#         self.cathode = Cathode(formulation=cathode_formulation,
#                                mass_loading=10.68,
#                                current_collector=cathode_current_collector,
#                                calender_density=2.60)

#         # construct anode
#         anode_active_material = AnodeMaterial(name="Hard Carbon (Vendor A - 330 mAh/g)",
#                                                specific_cost=14.27,
#                                                density=1.50,
#                                                irreversible_capacity_scaling=1,
#                                                reversible_capacity_scaling=1)
        
#         anode_conductive_additive = ConductiveAdditive(specific_cost=9, density=1.9)

#         anode_binder = Binder(name="PVDF", specific_cost=10, density=1.7)

#         anode_formulation = ElectrodeFormulation(active_materials={anode_active_material: 88},
#                                                  binders={anode_binder: 3},
#                                                  conductive_additives={anode_conductive_additive: 9})
        
#         weldTab = WeldTab(formula='Cu', thickness=4, length=11.5, width=1)

#         anode_current_collector = TabWeldedCurrentCollector(formula="Cu",
#                                                             length=85,
#                                                             width=10.8,
#                                                             thickness=15,
#                                                             weld_tab=weldTab,
#                                                             weld_tab_spacing=30,
#                                                             first_tab_spacing=5,
#                                                             bare_length=5)
        
#         self.anode = Anode(formulation=anode_formulation,
#                            mass_loading=10.68,
#                            current_collector=anode_current_collector,
#                            calender_density=0.85)
        
#     def test_electrodes(self):
        
#         self.assertTrue(isinstance(self.cathode, Cathode))
#         self.assertTrue(isinstance(self.anode, Anode))
#         self.assertTrue(isinstance(self.cathode.current_collector, CurrentCollector))
#         self.assertTrue(isinstance(self.anode.current_collector, CurrentCollector))
#         self.assertTrue(isinstance(self.cathode.formulation, ElectrodeFormulation))
#         self.assertTrue(isinstance(self.anode.formulation, ElectrodeFormulation))

#     def test_current_collectors(self):

#         self.assertTrue(isinstance(self.cathode.current_collector, TabWeldedCurrentCollector))
#         self.assertTrue(isinstance(self.anode.current_collector, TabWeldedCurrentCollector))
#         # self.cathode.current_collector.show()
#         # self.anode.current_collector.show()

#     def test_half_cell_curve(self):

#         self.cathode._calculate_half_cell_curve(grid_n=100)
#         self.anode._calculate_half_cell_curve(grid_n=100)
#         data_cathode = self.cathode.half_cell_curve
#         data_anode = self.anode.half_cell_curve

#         # px.line(data_cathode, x='Capacity (Ah)', y='Voltage (V)', title='Cathode Half Cell Curve', 
#         #         line_shape='spline', color='Direction', markers=True).show()
        
#         # px.line(data_anode, x='Capacity (Ah)', y='Voltage (V)', title='Anode Half Cell Curve',
#         #         line_shape='spline', color='Direction', markers=True).show()
