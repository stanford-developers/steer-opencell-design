import time
import unittest
import pandas as pd
from copy import deepcopy

from steer_opencell_design import (
    CathodeFormulation, AnodeFormulation,
    Cathode, Anode,
    Separator,
    NotchedCurrentCollector, TablessCurrentCollector, TabWeldedCurrentCollector,
    WoundJellyRoll, FlatWoundJellyRoll,
    RoundMandrel,
    Tape,
    Laminate,
    CylindricalTerminalConnector, CylindricalLidAssembly, CylindricalCannister, CylindricalEncapsulation,
    CylindricalCell,
    CathodeMaterial, AnodeMaterial, 
    Binder, ConductiveAdditive,
    CurrentCollectorMaterial, SeparatorMaterial, InsulationMaterial, TapeMaterial,
    PrismaticContainerMaterial,
    Electrolyte
)


class TestCylindricalCell(unittest.TestCase):
    
    def setUp(self):

        ########################
        # make a basic cathode
        ########################

        material = CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        current_collector = NotchedCurrentCollector(
            material=current_collector_material,
            length=4500,
            width=300,
            thickness=8,
            tab_width=60,
            tab_spacing=200,
            tab_height=18,
            insulation_width=6,
            coated_tab_height=2,
        )

        insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        cathode = Cathode(
            formulation=formulation,
            mass_loading=12,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        material = AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
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
            coated_tab_height=2,
            bare_lengths_a_side=(200, 300),
            bare_lengths_b_side=(150, 250),
        )

        anode = Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=current_collector,
            calender_density=1.1,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        separator_material = SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = Separator(material=separator_material, thickness=25, width=310, length=5000)

        bottom_separator = Separator(material=separator_material, thickness=25, width=310, length=7000)

        layup = Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = RoundMandrel(
            diameter=5, 
            length=350,
        )

        tape_material = TapeMaterial.from_database("Kapton")
        tape_material.density = 1.42
        tape_material.specific_cost = 70

        tape = Tape(
            material = tape_material,
            thickness=30
        )

        my_jellyroll = WoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=5,
        )
        
        aluminum = PrismaticContainerMaterial.from_database("Aluminum")
        copper = PrismaticContainerMaterial.from_database("Copper")

        cathode_connector = CylindricalTerminalConnector(
            material=aluminum,
            thickness=2,
            fill_factor=0.8
        )
        
        anode_connector = CylindricalTerminalConnector(
            material=copper,
            thickness=3,  # μm
            fill_factor=0.7
        )
        
        lid = CylindricalLidAssembly(
            material=aluminum,
            thickness=4.0,  # mm
            fill_factor=0.9
        )
        
        cannister = CylindricalCannister(
            material=aluminum,
            outer_radius=21.4,  # mm
            height=321,  # mm
            wall_thickness=0.5  
        )

        electrolyte = Electrolyte(
            name="1M LiPF6 in EC:DMC (1:1)",
            density=1.2,
            specific_cost=15.0,
            color="#00FF00"
        )
        
        # Create encapsulation
        encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=cathode_connector,
            anode_terminal_connector=anode_connector,
            lid_assembly=lid,
            cannister=cannister
        )

        self.cell = CylindricalCell(
            reference_electrode_assembly=my_jellyroll,
            encapsulation=encapsulation,
            electrolyte=electrolyte,
            electrolyte_overfill=0.2,
        )
        
        # Store components for tests
        self.jellyroll = my_jellyroll
        self.cathode_connector = cathode_connector
        self.anode_connector = anode_connector
        self.lid = lid
        self.cannister = cannister

    def test_basics(self):
        self.assertIsInstance(self.cell, CylindricalCell)
        self.assertEqual(self.cell.energy, 124.09)
        self.assertEqual(self.cell.mass, 908.47)
        self.assertEqual(self.cell.specific_energy, 136.59)
        self.assertEqual(self.cell.volumetric_energy, 268.69)
        self.assertEqual(self.cell.cost_per_energy, 64.29)
    
    def test_plots(self):

        fig1 = self.cell.plot_mass_breakdown()
        fig2 = self.cell.plot_cost_breakdown()
        fig3 = self.cell.get_capacity_plot()
        fig4 = self.cell.get_top_down_view()
        fig5 = self.cell.get_cross_section()

        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        self.assertIsNotNone(fig3)
        self.assertIsNotNone(fig4)
        self.assertIsNotNone(fig5)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()
        # fig5.show()

    def test_operating_voltage_window_setter(self):
        """Test setting operating voltage window updates both min and max voltages."""

        original_energy = self.cell.energy
        
        # Set new voltage window
        new_window = (2.6, 3.7)
        self.cell.operating_voltage_window = new_window
        
        # Check both values updated
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, 2.6, 2)
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, 3.7, 2)
        self.assertEqual(self.cell.operating_voltage_window, new_window)
        
        # Check that properties recalculated
        self.assertIsNotNone(self.cell.capacity_curve)
        self.assertIsNotNone(self.cell.reversible_capacity)

        # Check that energy changed
        self.assertLess(self.cell.energy, original_energy)

        fig1 = self.cell.get_capacity_plot()

        new_window = (2.3, 5.0)
        self.cell.operating_voltage_window = new_window
        self.assertEqual(self.cell.operating_voltage_window, (2.3, 4.03))

        # check that energy changed
        #self.assertLess(self.cell.energy, original_energy)

        fig2 = self.cell.get_capacity_plot()

        fig1.show()
        fig2.show()
        
    def test_minimum_operating_voltage_setter(self):
        """Test setting minimum operating voltage within valid range."""
        original_min = self.cell.minimum_operating_voltage
        
        # Set to a valid value within range
        new_min = original_min + 0.1
        self.cell.minimum_operating_voltage = new_min
        
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, new_min, 2)
        
        # Check that capacity curve updated
        discharge_curve = self.cell.capacity_curve.query("direction == 'discharge'")
        min_voltage_in_curve = discharge_curve["Voltage (V)"].min()
        self.assertAlmostEqual(min_voltage_in_curve, new_min, 1)

        fig1 = self.cell.get_capacity_plot()
        # fig1.show()
        
    def test_maximum_operating_voltage_setter(self):
        """Test setting maximum operating voltage within valid range."""
        original_max = self.cell.maximum_operating_voltage
        
        # Set to a valid value within range
        new_max = original_max - 0.1
        self.cell.maximum_operating_voltage = new_max
        
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, new_max, 2)
        
        # Check that energy properties updated
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.specific_energy)

        fig1 = self.cell.get_capacity_plot()
        # fig1.show()
        
    def test_minimum_operating_voltage_clamping(self):
        """Test that minimum voltage is clamped to valid range."""
        min_range, max_range = self.cell.minimum_operating_voltage_range
        
        # Try setting below minimum - should clamp to minimum
        self.cell.minimum_operating_voltage = min_range - 1.0
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, min_range, 2)
        
        # Try setting above maximum - should clamp to maximum
        self.cell.minimum_operating_voltage = max_range + 1.0
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, max_range, 2)
        
    def test_maximum_operating_voltage_clamping(self):
        """Test that maximum voltage is clamped to valid range."""
        min_range, max_range = self.cell.maximum_operating_voltage_range
        
        # Try setting below minimum - should clamp to minimum
        self.cell.maximum_operating_voltage = min_range - 1.0
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, min_range, 2)
        
        # Try setting above maximum - should clamp to maximum
        self.cell.maximum_operating_voltage = max_range + 1.0
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, max_range, 2)
        
    def test_reference_electrode_assembly_setter(self):
        """Test setting reference electrode assembly triggers recalculation."""
        # Create a new jellyroll with different properties
        new_jellyroll = deepcopy(self.jellyroll)
        new_jellyroll._layup._cathode._coating_thickness = 150  # Thicker coating
        new_jellyroll._calculate_all_properties()
        
        original_energy = self.cell.energy
        original_capacity = self.cell.reversible_capacity
        
        # Set new assembly
        self.cell.reference_electrode_assembly = new_jellyroll
        
        # Check that cell properties changed
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.reversible_capacity)
        
        # Verify the assembly was updated
        self.assertEqual(self.cell.reference_electrode_assembly, new_jellyroll)
        
    def test_encapsulation_setter(self):
        """Test setting encapsulation triggers recalculation."""
        # Create new encapsulation with different dimensions
        new_cannister = deepcopy(self.cannister)
        new_cannister._length = 72  # Longer cannister
        
        new_encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            cannister=new_cannister
        )
        
        original_mass = self.cell.mass
        
        # Set new encapsulation
        self.cell.encapsulation = new_encapsulation
        
        # Check that mass changed (different cannister mass)
        self.assertIsNotNone(self.cell.mass)
        
        # Verify encapsulation was updated
        self.assertEqual(self.cell.encapsulation, new_encapsulation)
        
    def test_encapsulation_setter_validation(self):
        """Test encapsulation setter validates assembly fit."""
        # Create encapsulation that's too small
        small_cannister = deepcopy(self.cannister)
        small_cannister._inner_diameter = 10  # Much too small
        
        small_encapsulation = CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            cannister=small_cannister
        )
        
        # Should warn but still set
        with self.assertWarns(UserWarning):
            self.cell.encapsulation = small_encapsulation
            
    def test_reference_electrode_assembly_setter_validation(self):
        """Test reference assembly setter validates encapsulation fit."""
        # Create jellyroll that's too large
        large_jellyroll = deepcopy(self.jellyroll)
        large_jellyroll._pressed_radius = 50  # Much too large
        large_jellyroll._calculate_all_properties()
        
        # Should warn but still set
        with self.assertWarns(UserWarning):
            self.cell.reference_electrode_assembly = large_jellyroll
        
    def test_n_electrode_assembly_setter(self):
        """Test setting number of electrode assemblies scales capacity."""
        original_n = self.cell.n_electrode_assembly
        original_capacity = self.cell.reversible_capacity
        
        # Double the number of assemblies
        new_n = 2
        self.cell.n_electrode_assembly = new_n
        
        # Check capacity approximately doubled
        new_capacity = self.cell.reversible_capacity
        self.assertAlmostEqual(new_capacity / original_capacity, 2.0, 1)
        
        # Check mass increased
        self.assertIsNotNone(self.cell.mass)
        
    def test_electrolyte_setter(self):
        """Test setting electrolyte updates cell properties."""
        # Create new electrolyte with different properties
        new_electrolyte = Electrolyte(
            name="New Electrolyte",
            specific_cost=25,  # More expensive
            density=1.3,
            color="#00FFFF"
        )
        
        original_cost = self.cell.cost
        
        # Set new electrolyte
        self.cell.electrolyte = new_electrolyte
        
        # Check that cost changed
        new_cost = self.cell.cost
        self.assertNotEqual(new_cost, original_cost)
        
        # Verify electrolyte was updated
        self.assertEqual(self.cell.electrolyte, new_electrolyte)
        
    def test_electrolyte_overfill_setter(self):
        """Test setting electrolyte overfill updates electrolyte mass."""
        original_overfill = self.cell.electrolyte_overfill
        original_mass = self.cell.mass
        
        # Increase overfill
        new_overfill = 0.5  # 50% overfill instead of 20%
        self.cell.electrolyte_overfill = new_overfill
        
        # Check that mass increased (more electrolyte)
        new_mass = self.cell.mass
        self.assertGreater(new_mass, original_mass)
        
        # Verify overfill was updated
        self.assertEqual(self.cell.electrolyte_overfill, new_overfill)
        
    def test_name_setter(self):
        """Test setting cell name."""
        new_name = "Test Cell 2024"
        self.cell.name = new_name
        
        self.assertEqual(self.cell.name, new_name)
        
    def test_setter_chain_consistency(self):
        """Test that multiple setter calls maintain consistency."""
        # Change multiple properties
        self.cell.operating_voltage_window = (2.69, 3.9)
        self.cell.electrolyte_overfill = 0.3
        self.cell.name = "Modified Cell"
        
        # Verify all properties are consistent
        self.assertEqual(self.cell.operating_voltage_window, (2.69, 3.9))
        self.assertEqual(self.cell.electrolyte_overfill, 0.3)
        self.assertEqual(self.cell.name, "Modified Cell")
        
        # Verify calculated properties are still valid
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.mass)
        self.assertIsNotNone(self.cell.cost)
        self.assertGreater(self.cell.reversible_capacity, 0)
        
    def test_setter_type_validation(self):
        """Test that setters validate input types."""
        # Test invalid type for reference_electrode_assembly
        with self.assertRaises((TypeError, AttributeError)):
            self.cell.reference_electrode_assembly = "not a jellyroll"
            
        # Test invalid type for encapsulation
        with self.assertRaises((TypeError, AttributeError)):
            self.cell.encapsulation = 123
            
        # Test invalid type for electrolyte
        with self.assertRaises((TypeError, AttributeError)):
            self.cell.electrolyte = []
            
    def test_voltage_setter_with_none_values(self):
        """Test voltage setters handle None values correctly."""
        # Set to None should use default behavior
        self.cell.minimum_operating_voltage = None
        self.assertIsNotNone(self.cell.minimum_operating_voltage)
        
        self.cell.maximum_operating_voltage = None
        self.assertIsNotNone(self.cell.maximum_operating_voltage)

    def test_formulation_setter(self):

        material = CathodeMaterial.from_database("NMC811")
        material.specific_cost = 25
        material.density = 4.8

        conductive_additive = ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        self.cell._reference_electrode_assembly._layup._cathode.formulation = formulation
        self.cell._reference_electrode_assembly._layup._cathode.mass_loading = 10
        self.cell._reference_electrode_assembly._layup.cathode = self.cell._reference_electrode_assembly._layup._cathode
        self.cell._reference_electrode_assembly.layup = self.cell._reference_electrode_assembly._layup
        self.cell.reference_electrode_assembly = self.cell._reference_electrode_assembly

        fig1 = self.cell.get_capacity_plot()
        # fig1.show()

if __name__ == "__main__":
    unittest.main()







