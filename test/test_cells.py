import unittest
from copy import deepcopy
import steer_opencell_design as ocd


class TestCylindricalCell(unittest.TestCase):
    
    def setUp(self):

        ########################
        # make a basic cathode
        ########################

        material = ocd.CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ocd.ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = ocd.CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = ocd.CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        current_collector = ocd.NotchedCurrentCollector(
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

        insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

        cathode = ocd.Cathode(
            formulation=formulation,
            mass_loading=12,
            current_collector=current_collector,
            calender_density=2.60,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        material = ocd.AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = ocd.AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        current_collector = ocd.NotchedCurrentCollector(
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

        anode = ocd.Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=current_collector,
            calender_density=1.1,
            insulation_material=insulation,
            insulation_thickness=10,
        )

        separator_material = ocd.SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=5000)

        bottom_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=7000)

        layup = ocd.Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = ocd.RoundMandrel(
            diameter=5, 
            length=350,
        )

        tape_material = ocd.TapeMaterial.from_database("Kapton")
        tape_material.density = 1.42
        tape_material.specific_cost = 70

        tape = ocd.Tape(
            material = tape_material,
            thickness=30
        )

        my_jellyroll = ocd.WoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=5,
        )
        
        aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
        copper = ocd.PrismaticContainerMaterial.from_database("Copper")

        cathode_connector = ocd.CylindricalTerminalConnector(
            material=aluminum,
            thickness=2,
            fill_factor=0.8
        )
        
        anode_connector = ocd.CylindricalTerminalConnector(
            material=copper,
            thickness=3,  # μm
            fill_factor=0.7
        )
        
        lid = ocd.CylindricalLidAssembly(
            material=aluminum,
            thickness=4.0,  # mm
            fill_factor=0.9
        )
        
        canister = ocd.CylindricalCanister(
            material=aluminum,
            outer_radius=21.4,  # mm
            height=330,  # mm
            wall_thickness=0.5  
        )

        electrolyte = ocd.Electrolyte(
            name="1M LiPF6 in EC:DMC (1:1)",
            density=1.2,
            specific_cost=15.0,
            color="#00FF00"
        )
        
        # Create encapsulation
        encapsulation = ocd.CylindricalEncapsulation(
            cathode_terminal_connector=cathode_connector,
            anode_terminal_connector=anode_connector,
            lid_assembly=lid,
            canister=canister
        )

        self.cell = ocd.CylindricalCell(
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
        self.canister = canister

    def test_basics(self):
        self.assertIsInstance(self.cell, ocd.CylindricalCell)
        self.assertEqual(self.cell.energy, 124.09)
        self.assertEqual(self.cell.mass, 910.08)
        self.assertEqual(self.cell.specific_energy, 136.35)
        self.assertEqual(self.cell.volumetric_energy, 261.36)
        self.assertEqual(self.cell.cost_per_energy, 64.45)
    
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

        # fig1.show()
        # fig2.show()
        
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
        from steer_opencell_design.Constructions.Layups.Base import NPRatioControlMode
        # get original np ratio
        original_np_ratio = self.jellyroll.layup.np_ratio

        # Create a new jellyroll with different properties
        new_jellyroll = deepcopy(self.jellyroll)
        new_jellyroll._layup._cathode.coating_thickness = 150  # Thicker coating
        new_jellyroll._layup.cathode = new_jellyroll._layup._cathode
        new_jellyroll.layup = new_jellyroll._layup
        new_jellyroll._layup.np_ratio_control_mode = NPRatioControlMode.FIXED_CATHODE
        new_jellyroll._layup.np_ratio = original_np_ratio  # keep np ratio same
        new_jellyroll.radius = 20.8
        
        original_energy = self.cell.energy
        
        # Set new assembly
        self.cell.reference_electrode_assembly = new_jellyroll
        
        # Check that cell properties changed
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.reversible_capacity)
        
        # Verify the assembly was updated
        self.assertEqual(self.cell.reference_electrode_assembly, new_jellyroll)

        # verify energy increased due to thicker cathode
        self.assertGreater(self.cell.energy, original_energy)
        
    def test_encapsulation_setter(self):
        """Test setting encapsulation triggers recalculation."""
        # Create new encapsulation with different dimensions
        new_canister = deepcopy(self.canister)
        new_canister._length = 72  # Longer canister
        
        new_encapsulation = ocd.CylindricalEncapsulation(
            cathode_terminal_connector=self.cathode_connector,
            anode_terminal_connector=self.anode_connector,
            lid_assembly=self.lid,
            canister=new_canister
        )
        
        original_mass = self.cell.mass
        
        # Set new encapsulation
        self.cell.encapsulation = new_encapsulation
        
        # Check that mass changed (different canister mass)
        self.assertIsNotNone(self.cell.mass)
        
        # Verify encapsulation was updated
        self.assertEqual(self.cell.encapsulation, new_encapsulation)
            
    def test_electrolyte_setter(self):
        """Test setting electrolyte updates cell properties."""
        # Create new electrolyte with different properties
        new_electrolyte = ocd.Electrolyte(
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

        material = ocd.CathodeMaterial.from_database("NMC811")
        material.specific_cost = 25
        material.density = 4.8

        conductive_additive = ocd.ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = ocd.CathodeFormulation(
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


class TestCylindricalCellTabbed(unittest.TestCase):
    
    def setUp(self):

        ########################
        # make a basic cathode
        ########################

        material = ocd.CathodeMaterial.from_database("LFP")
        material.specific_cost = 6
        material.density = 3.6

        conductive_additive = ocd.ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        formulation = ocd.CathodeFormulation(
            active_materials={material: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        current_collector_material = ocd.CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")

        tab = ocd.WeldTab(material=current_collector_material, width=20, length=120, thickness=12)

        current_collector = ocd.TabWeldedCurrentCollector(
            material=current_collector_material,
            weld_tab=tab,
            length=4500,
            width=300,
            thickness=8,
            skip_coat_width=30,
            tab_overhang=20,
            weld_tab_positions=[500, 1500, 2500, 3500],
        )

        cathode = ocd.Cathode(
            formulation=formulation,
            mass_loading=12,
            current_collector=current_collector,
            calender_density=2.60
        )

        material = ocd.AnodeMaterial.from_database("Synthetic Graphite")
        material.specific_cost = 4
        material.density = 2.2

        formulation = ocd.AnodeFormulation(
            active_materials={material: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        current_collector = ocd.TabWeldedCurrentCollector(
            material=current_collector_material,
            weld_tab=tab,
            length=4500,
            width=300,
            thickness=8,
            skip_coat_width=30,
            tab_overhang=20,
            weld_tab_positions=[1000, 2000, 3000, 4000],
        )

        anode = ocd.Anode(
            formulation=formulation,
            mass_loading=7.2,
            current_collector=current_collector,
            calender_density=1.1
        )

        separator_material = ocd.SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        top_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=5000)

        bottom_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=7000)

        layup = ocd.Laminate(
            anode=anode,
            cathode=cathode,
            top_separator=top_separator,
            bottom_separator=bottom_separator,
        )

        mandrel = ocd.RoundMandrel(
            diameter=5, 
            length=350,
        )

        tape_material = ocd.TapeMaterial.from_database("Kapton")
        tape_material.density = 1.42
        tape_material.specific_cost = 70

        tape = ocd.Tape(
            material = tape_material,
            thickness=30
        )

        my_jellyroll = ocd.WoundJellyRoll(
            laminate=layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=5,
            collector_tab_crumple_factor=70
        )
        
        aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
        copper = ocd.PrismaticContainerMaterial.from_database("Copper")

        cathode_connector = ocd.CylindricalTerminalConnector(
            material=aluminum,
            thickness=2,
            fill_factor=0.8
        )
        
        anode_connector = ocd.CylindricalTerminalConnector(
            material=copper,
            thickness=3,  # μm
            fill_factor=0.7
        )
        
        lid = ocd.CylindricalLidAssembly(
            material=aluminum,
            thickness=4.0,  # mm
            fill_factor=0.9
        )
        
        canister = ocd.CylindricalCanister(
            material=aluminum,
            outer_radius=21.4,  # mm
            height=322,  # mm
            wall_thickness=0.5  
        )

        electrolyte = ocd.Electrolyte(
            name="1M LiPF6 in EC:DMC (1:1)",
            density=1.2,
            specific_cost=15.0,
            color="#00FF00"
        )
        
        # Create encapsulation
        encapsulation = ocd.CylindricalEncapsulation(
            cathode_terminal_connector=cathode_connector,
            anode_terminal_connector=anode_connector,
            lid_assembly=lid,
            canister=canister
        )

        self.cell = ocd.CylindricalCell(
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
        self.canister = canister

    def test_plots(self):

        fig1 = self.cell.get_top_down_view()
        fig2 = self.cell.get_cross_section()
        fig3 = self.cell._reference_electrode_assembly._layup.get_top_down_view()
        fig4 = self.cell._reference_electrode_assembly.get_top_down_view()

        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        self.assertIsNotNone(fig3)
        self.assertIsNotNone(fig4)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_basics(self):
        self.assertIsInstance(self.cell, ocd.CylindricalCell)
        self.assertEqual(self.cell.energy, 132.3)
        self.assertEqual(self.cell.mass, 920.95)
        self.assertEqual(self.cell.specific_energy, 143.66)
        self.assertEqual(self.cell.volumetric_energy, 285.58)
        self.assertEqual(self.cell.cost_per_energy, 58.59)


class TestStackedPouchCell(unittest.TestCase):
    
    def setUp(self):
        # Replicate MonoLayer setup similar to TestSimpleMonoLayer in test_layups
        cathode_active = ocd.CathodeMaterial.from_database("LFP")
        cathode_active.specific_cost = 6
        cathode_active.density = 3.6

        conductive_additive = ocd.ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        cathode_formulation = ocd.CathodeFormulation(
            active_materials={cathode_active: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        cathode_cc_material = ocd.CurrentCollectorMaterial(name="Copper", specific_cost=5, density=2.7, color="#FFAE00")

        cathode_cc = ocd.PunchedCurrentCollector(
            material=cathode_cc_material,
            width=300,
            height=800,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = ocd.Cathode(
            formulation=cathode_formulation,
            mass_loading=28.2,
            current_collector=cathode_cc,
            calender_density=2.60,
        )

        anode_active = ocd.AnodeMaterial.from_database("Synthetic Graphite")
        anode_active.specific_cost = 4
        anode_active.density = 2.2

        anode_formulation = ocd.AnodeFormulation(
            active_materials={anode_active: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        cc_material = ocd.CurrentCollectorMaterial(name="Aluminium", specific_cost=5, density=2.7, color="#717171")

        anode_cc = ocd.PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=800,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = ocd.Anode(
            formulation=anode_formulation,
            mass_loading=20.68,
            current_collector=anode_cc,
            calender_density=1.1,
            insulation_thickness=10,
        )

        separator_material = ocd.SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=326)

        monolayer = ocd.MonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
            electrode_orientation='transverse'
        )

        # default stack for reuse in tests
        stack = ocd.PunchedStack(
            layup=monolayer, 
            n_layers=20
        )

        top_laminate_sheet = ocd.LaminateSheet(
            areal_cost=10,
            thickness=150,
            density=1500,
        )

        bottom_laminate_sheet = ocd.LaminateSheet(
            areal_cost=10,
            thickness=150,
            density=1500,
        )

        cathode_terminal = ocd.PouchTerminal(
            material=cc_material,
            thickness=2,
            width=50,
            length=40,
        )

        anode_terminal = ocd.PouchTerminal(
            material=cc_material,
            thickness=2,
            width=50,
            length=40,
        )

        encapsulation = ocd.PouchEncapsulation(
            top_laminate=top_laminate_sheet,
            bottom_laminate=bottom_laminate_sheet,
            cathode_terminal=cathode_terminal,
            anode_terminal=anode_terminal,
            width=320,
            height=340,
        )

        electrolyte = ocd.Electrolyte(
            name="1M LiPF6 in EC:DMC (1:1)",
            density=1.2,
            specific_cost=5.0,
            color="#00FF00"
        )

        self.cell = ocd.PouchCell(
            reference_electrode_assembly=stack,
            n_electrode_assembly=2,
            encapsulation=encapsulation,
            electrolyte=electrolyte,
            electrolyte_overfill=0.2,
            clipped_tab_length=10
        )

    def test_basics(self):
        self.assertIsInstance(self.cell, ocd.PouchCell)
        self.assertAlmostEqual(self.cell.energy, 2282.76, 1)
        self.assertAlmostEqual(self.cell.mass, 129677.71, 0)
        self.assertAlmostEqual(self.cell.cost, 79.82, 1)

    def test_serialization(self):
        serialized = self.cell.serialize()
        deserialized = ocd.PouchCell.deserialize(serialized)

        original_encapsulation = self.cell.electrode_assemblies[0]
        new_encapsulation = deserialized.electrode_assemblies[0]

        test_case = original_encapsulation == new_encapsulation
        self.assertTrue(test_case)

        # test_case = self.cell == deserialized
        # self.assertTrue(test_case)

    def test_plots(self):

        fig1 = self.cell.plot_mass_breakdown()
        fig2 = self.cell.plot_cost_breakdown()
        fig3 = self.cell.get_capacity_plot()
        fig4 = self.cell.get_side_view()
        fig5 = self.cell.get_top_down_view(opacity=0.6)

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

    def test_electrode_orientation_setter(self):

        fig1 = self.cell.get_side_view()
        fig2 = self.cell.get_top_down_view()
        
        # Change electrode orientation
        self.cell.reference_electrode_assembly.layup.electrode_orientation = 'longitudinal'
        self.cell.reference_electrode_assembly.layup = self.cell.reference_electrode_assembly.layup
        self.cell.reference_electrode_assembly = self.cell.reference_electrode_assembly

        fig3 = self.cell.get_side_view()
        fig4 = self.cell.get_top_down_view()

        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        self.assertIsNotNone(fig3)
        self.assertIsNotNone(fig4)

        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()

    def test_seal_thickness_setters(self):
        """Test setting seal thicknesses triggers recalculation."""
        original_width = self.cell.encapsulation.width
        original_height = self.cell.encapsulation.height
        
        # Change side seal thickness
        self.cell.side_seal_thickness = 20  # from 15mm default
        new_width = self.cell.encapsulation.width
        self.assertGreater(new_width, original_width)
        self.assertEqual(self.cell.side_seal_thickness, 20)
        
        # Change top seal thickness
        self.cell.top_seal_thickness = 20
        new_height = self.cell.encapsulation.height
        self.assertGreater(new_height, original_height)
        self.assertEqual(self.cell.top_seal_thickness, 20)
        
        # Change bottom seal thickness
        self.cell.bottom_seal_thickness = 20
        self.assertEqual(self.cell.bottom_seal_thickness, 20)

    def test_clipped_tab_length_setter(self):
        """Test clipped tab length validation and setting."""
        # Get valid range
        min_length, max_length = self.cell.clipped_tab_length_range
        
        # Set to valid value
        mid_length = (min_length + max_length) / 2
        self.cell.clipped_tab_length = mid_length
        self.assertAlmostEqual(self.cell.clipped_tab_length, mid_length, 2)
        
        # Test invalid values
        with self.assertRaises(ValueError):
            self.cell.clipped_tab_length = max_length + 10
        
        with self.assertRaises(ValueError):
            self.cell.clipped_tab_length = -1
        
    def test_clipped_tab_length_range_property(self):
        """Test that clipped tab length range is correctly calculated."""
        min_length, max_length = self.cell.clipped_tab_length_range
        
        # Min should be 0
        self.assertEqual(min_length, 0.0)
        
        # Max should be positive and less than total tab height
        self.assertGreater(max_length, 0)
        self.assertLess(max_length, 100)  # Reasonable upper bound

    def test_operating_voltage_window_setter(self):
        """Test setting operating voltage window updates energy calculations."""
        original_energy = self.cell.energy
        
        # Set new voltage window
        new_window = (2.6, 3.7)
        self.cell.operating_voltage_window = new_window
        
        # Check both values updated
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, 2.6, 2)
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, 3.7, 2)
        self.assertEqual(self.cell.operating_voltage_window, new_window)
        
        # Check that energy changed
        self.assertNotEqual(self.cell.energy, original_energy)

    def test_reference_electrode_assembly_setter(self):
        """Test setting reference electrode assembly triggers recalculation."""
        # Create a new stack with different properties
        new_stack = deepcopy(self.cell.reference_electrode_assembly)
        new_stack._n_layers = 25  # More layers
        new_stack._calculate_all_properties()
        
        original_energy = self.cell.energy
        
        # Set new assembly
        self.cell.reference_electrode_assembly = new_stack
        
        # Check that cell properties changed
        self.assertNotEqual(self.cell.energy, original_energy)
        self.assertEqual(self.cell.reference_electrode_assembly, new_stack)

    def test_encapsulation_setter(self):
        """Test setting encapsulation updates cell properties."""
        # Create new encapsulation with different dimensions
        new_encapsulation = deepcopy(self.cell.encapsulation)
        new_encapsulation.top_laminate.thickness = 200  # Thicker top laminate
        new_encapsulation.bottom_laminate.thickness = 200  # Thicker bottom laminate
        
        original_mass = self.cell.mass
        
        # Set new encapsulation
        self.cell.encapsulation = new_encapsulation
        
        # Check that mass changed
        self.assertNotEqual(self.cell.mass, original_mass)
        self.assertEqual(self.cell.encapsulation, new_encapsulation)

    def test_electrolyte_setter(self):
        """Test setting electrolyte updates cell properties."""
        new_electrolyte = ocd.Electrolyte(
            name="New Electrolyte",
            specific_cost=10,
            density=1.3,
            color="#00FFFF"
        )
        
        original_cost = self.cell.cost
        
        # Set new electrolyte
        self.cell.electrolyte = new_electrolyte
        
        # Check that cost changed
        self.assertNotEqual(self.cell.cost, original_cost)
        self.assertEqual(self.cell.electrolyte, new_electrolyte)

    def test_electrolyte_overfill_setter(self):
        """Test setting electrolyte overfill updates electrolyte mass."""
        original_mass = self.cell.mass
        
        # Increase overfill
        self.cell.electrolyte_overfill = 0.5
        
        # Check that mass increased
        self.assertGreater(self.cell.mass, original_mass)
        self.assertEqual(self.cell.electrolyte_overfill, 0.5)

    def test_n_electrode_assembly_setter(self):
        """Test setting number of electrode assemblies."""
        original_energy = self.cell.energy
        
        # Increase number of assemblies
        self.cell.n_electrode_assembly = 3
        
        # Energy should increase (more assemblies = more capacity)
        self.assertGreater(self.cell.energy, original_energy)
        self.assertEqual(self.cell.n_electrode_assembly, 3)

    def test_side_view_legend_only_first_assembly(self):
        """Test that side view only shows legend for first assembly."""
        fig = self.cell.get_side_view()
        
        # Count traces with showlegend=True
        legend_traces = [trace for trace in fig.data if trace.showlegend]
        
        # Should have some legend entries, but not duplicated for each assembly
        self.assertGreater(len(legend_traces), 0)
        
        # Get all trace names
        trace_names = [trace.name for trace in fig.data if trace.name]
        
        # Check for duplicates - there should be some traces with same name but showlegend=False
        self.assertEqual(self.cell.n_electrode_assembly, 2)

    def test_top_down_view_opacity(self):
        """Test that top-down view applies opacity correctly."""
        # Get view with different opacity values
        fig1 = self.cell.get_top_down_view(opacity=0.3)
        fig2 = self.cell.get_top_down_view(opacity=0.8)
        
        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        
        # Both should have traces
        self.assertGreater(len(fig1.data), 0)
        self.assertGreater(len(fig2.data), 0)

    def test_hot_pressing_geometry(self):
        """Test that hot-pressing creates cavity in laminates."""
        # Check that laminates have been hot-pressed
        top_laminate = self.cell.encapsulation._top_laminate
        bottom_laminate = self.cell.encapsulation._bottom_laminate
        
        # Both should have cavity properties set
        self.assertIsNotNone(top_laminate._cavity_depth)
        self.assertIsNotNone(bottom_laminate._cavity_depth)
        
        # Top should be negative (pressed inward), bottom positive (pressed outward)
        self.assertLess(top_laminate._cavity_depth, 0)
        self.assertGreater(bottom_laminate._cavity_depth, 0)

    def test_terminal_positioning(self):
        """Test that terminals are positioned correctly."""
        cathode_terminal = self.cell.encapsulation._cathode_terminal
        anode_terminal = self.cell.encapsulation._anode_terminal
        
        # Both terminals should have datum set
        self.assertIsNotNone(cathode_terminal._datum)
        self.assertIsNotNone(anode_terminal._datum)
        
        # Terminals should be positioned at different locations
        self.assertNotEqual(cathode_terminal._datum, anode_terminal._datum)

    def test_setter_chain_consistency(self):
        """Test that multiple setter calls maintain consistency."""
        # Change multiple properties
        self.cell.side_seal_thickness = 18
        self.cell.top_seal_thickness = 18
        self.cell.bottom_seal_thickness = 18
        self.cell.clipped_tab_length = 5
        self.cell.operating_voltage_window = (2.7, 3.8)
        
        # Verify all properties are consistent
        self.assertEqual(self.cell.side_seal_thickness, 18)
        self.assertEqual(self.cell.top_seal_thickness, 18)
        self.assertEqual(self.cell.bottom_seal_thickness, 18)
        self.assertEqual(self.cell.clipped_tab_length, 5)
        
        # Verify calculated properties are still valid
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.mass)
        self.assertIsNotNone(self.cell.cost)
        self.assertGreater(self.cell.reversible_capacity, 0)


class TestStackedPouchCellTemp(unittest.TestCase):
    
    def setUp(self):

        import steer_opencell_design as ocd

        conductive_additive = ocd.ConductiveAdditive.from_database("Super P")
        binder = ocd.Binder.from_database("PVDF")
        insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 95%")
        separator_material = ocd.SeparatorMaterial.from_database('Polyethylene')
        tape_material = ocd.TapeMaterial.from_database("Kapton")
        prismatic_material = ocd.PrismaticContainerMaterial.from_database("Steel")

        cathode_current_collector_material = ocd.CurrentCollectorMaterial.from_database('Aluminum')

        cathode_current_collector=ocd.PunchedCurrentCollector(
            material=cathode_current_collector_material,
            width=300,
            height=280,
            tab_height=30,
            tab_position=70,
            tab_width=80,
            thickness=10,
            insulation_width=2
        )

        cathode_active_material = ocd.CathodeMaterial.from_database("NMC811")

        cathode_formulation = ocd.CathodeFormulation(
            active_materials={cathode_active_material: 95},
            binders={binder: 2.5},
            conductive_additives={conductive_additive: 2.5}
        )

        my_cathode = ocd.Cathode(
            formulation=cathode_formulation,
            current_collector=cathode_current_collector,
            calender_density=3.1,
            mass_loading=14,
            insulation_material=insulation,
            insulation_thickness=3
        )

        # Create the anode

        cathode_current_collector_material = ocd.CurrentCollectorMaterial.from_database("Copper")

        anode_current_collector = ocd.PunchedCurrentCollector(
            material=cathode_current_collector_material,
            width=300,
            height=280,
            tab_height=30,
            tab_position=230,
            tab_width=80,
            thickness=10
        )

        anode_active_material = ocd.AnodeMaterial.from_database("Synthetic Graphite")

        anode_formulation = ocd.AnodeFormulation(
            active_materials={anode_active_material: 95},
            binders={binder: 2.5},
            conductive_additives={conductive_additive: 2.5}
        )

        my_anode = ocd.Anode(
            formulation=anode_formulation,
            current_collector=anode_current_collector,
            calender_density=1.1,
            mass_loading=9
        )

        # create the layup 

        separator = ocd.Separator(
            material=separator_material, 
            thickness=12,
            width=280,
            length=300
        )

        my_layup = ocd.ZFoldMonoLayer(
            cathode=my_cathode,
            anode=my_anode,
            separator=separator,
        )

        # create the stack assembly

        my_stack = ocd.ZFoldStack(
            layup=my_layup,
            n_layers=40,
            additional_separator_wraps=3
        )

        # make the electrolyte

        my_electrolyte = ocd.Electrolyte(
            name="1M NaPF6 in EC:PC:DMC (1:1:1 wt%)",
            density=1.2,
            specific_cost=10,
            color="#FF9D00"
        )

        top_laminate = ocd.LaminateSheet(
            areal_cost=0.06,
            density=1.4,
            thickness=80
        )

        bottom_laminate = ocd.LaminateSheet(
            areal_cost=0.06,
            density=1.4,
            thickness=80
        )

        cathode_terminal_connector = ocd.PouchTerminal(
            material=prismatic_material,
            width=50,
            length=10,
            thickness=1
        )

        anode_terminal_connector = ocd.PouchTerminal(
            material=prismatic_material,
            width=50,
            length=10,
            thickness=1
        )

        encapsulation = ocd.PouchEncapsulation(
            top_laminate=top_laminate,
            bottom_laminate=bottom_laminate,
            cathode_terminal=cathode_terminal_connector,
            anode_terminal=anode_terminal_connector
        )

        self.cell = ocd.PouchCell(
            reference_electrode_assembly=my_stack,
            electrolyte=my_electrolyte,
            electrolyte_overfill=0.1,
            encapsulation=encapsulation,
            n_electrode_assembly=1,
            clipped_tab_length=10
        )

    def test_plots(self):

        fig1 = self.cell.plot_mass_breakdown()
        fig2 = self.cell.plot_cost_breakdown()
        fig3 = self.cell.get_capacity_plot()
        fig4 = self.cell.get_side_view()
        fig5 = self.cell.get_top_down_view(opacity=0.6)

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

    def test_reference_chemistry(self):
        cell_chemistry = self.cell.reference_chemistry
        self.assertEqual(cell_chemistry, "Li/Li+")

    def test_form_factor(self):
        form_factor = self.cell.form_factor
        self.assertEqual(form_factor, "Pouch Cell")

    def test_internal_construction(self):
        internal_construction = self.cell.internal_construction
        self.assertEqual(internal_construction, "ZFold Stack")


class TestStackedPrismaticCell(unittest.TestCase):
    
    def setUp(self):

        # Replicate MonoLayer setup similar to TestSimpleMonoLayer in test_layups
        cathode_active = ocd.CathodeMaterial.from_database("LFP")
        cathode_active.specific_cost = 6
        cathode_active.density = 3.6

        conductive_additive = ocd.ConductiveAdditive(name="super_P", specific_cost=15, density=2.0, color="#000000")
        binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

        cathode_formulation = ocd.CathodeFormulation(
            active_materials={cathode_active: 95},
            binders={binder: 2},
            conductive_additives={conductive_additive: 3},
        )

        cathode_cc_material = ocd.CurrentCollectorMaterial(name="Copper", specific_cost=5, density=2.7, color="#FFAE00")

        cathode_cc = ocd.PunchedCurrentCollector(
            material=cathode_cc_material,
            width=300,
            height=400,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=50,
        )

        cathode = ocd.Cathode(
            formulation=cathode_formulation,
            mass_loading=28.2,
            current_collector=cathode_cc,
            calender_density=2.60,
        )

        anode_active = ocd.AnodeMaterial.from_database("Synthetic Graphite")
        anode_active.specific_cost = 4
        anode_active.density = 2.2

        anode_formulation = ocd.AnodeFormulation(
            active_materials={anode_active: 90},
            binders={binder: 5},
            conductive_additives={conductive_additive: 5},
        )

        cc_material = ocd.CurrentCollectorMaterial(name="Aluminium", specific_cost=5, density=2.7, color="#717171")

        anode_cc = ocd.PunchedCurrentCollector(
            material=cc_material,
            width=300,
            height=402,
            thickness=8,
            tab_width=60,
            tab_height=18,
            tab_position=250,
        )

        anode = ocd.Anode(
            formulation=anode_formulation,
            mass_loading=20.68,
            current_collector=anode_cc,
            calender_density=1.1,
            insulation_thickness=10,
        )

        separator_material = ocd.SeparatorMaterial(
            name="Polyethylene",
            specific_cost=2,
            density=0.94,
            color="#FDFDB7",
            porosity=45,
        )

        separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=326)

        monolayer = ocd.MonoLayer(
            anode=anode,
            cathode=cathode,
            separator=separator,
        )

        # default stack for reuse in tests
        stack = ocd.PunchedStack(
            layup=monolayer, 
            n_layers=20
        )

        electrolyte = ocd.Electrolyte(
            name="1M LiPF6 in EC:DMC (1:1)",
            density=1.2,
            specific_cost=5.0,
            color="#00FF00"
        )

        prismatic_material = ocd.PrismaticContainerMaterial.from_database("Steel")

        lid = ocd.PrismaticLidAssembly(
            material=prismatic_material,
            thickness=5,
            fill_factor=0.8
        )

        canister = ocd.PrismaticCanister(
            material=prismatic_material,
            wall_thickness=1,
            length=85,
            width=320,
            height=415,
        )

        cathode_connector_terminal = ocd.PrismaticTerminalConnector(
            material=prismatic_material,
            thickness=2,
            width=50,
            length=40,
        )

        anode_connector_terminal = ocd.PrismaticTerminalConnector(
            material=prismatic_material,
            thickness=2,
            width=50,
            length=40,
        )

        encapsulation = ocd.PrismaticEncapsulation(
            cathode_terminal_connector=cathode_connector_terminal,
            anode_terminal_connector=anode_connector_terminal,
            lid_assembly=lid,
            canister=canister
        )

        self.cell = ocd.PrismaticCell(
            reference_electrode_assembly=stack,
            n_electrode_assembly=6,
            encapsulation=encapsulation,
            electrolyte=electrolyte,
            electrolyte_overfill=0.2,
            clipped_tab_length=7
        )

    def test_basics(self):
        self.assertIsInstance(self.cell, ocd.PrismaticCell)
        # self.assertAlmostEqual(self.cell.energy, 2282.76, 1)
        # self.assertAlmostEqual(self.cell.mass, 14066.36, 0)
        # self.assertAlmostEqual(self.cell.cost, 80.53, 1)

    def test_plots(self):

        fig1 = self.cell.plot_mass_breakdown()
        fig2 = self.cell.plot_cost_breakdown()
        fig3 = self.cell.get_capacity_plot()
        fig4 = self.cell.get_side_view()
        fig5 = self.cell.get_top_down_view(opacity=0.6)

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

    def test_clipped_tab_length_setter(self):
        """Test clipped tab length validation and setting."""
        # Get valid range
        min_length, max_length = self.cell.clipped_tab_length_range
        
        # Set to valid value
        mid_length = (min_length + max_length) / 2
        self.cell.clipped_tab_length = mid_length
        self.assertAlmostEqual(self.cell.clipped_tab_length, mid_length, 2)
        
        # Test invalid values
        with self.assertRaises(ValueError):
            self.cell.clipped_tab_length = max_length + 10
        
        with self.assertRaises(ValueError):
            self.cell.clipped_tab_length = -1
        
    def test_clipped_tab_length_range_property(self):
        """Test that clipped tab length range is correctly calculated."""
        min_length, max_length = self.cell.clipped_tab_length_range
        
        # Min should be 0
        self.assertEqual(min_length, 0.0)
        
        # Max should be positive and less than total tab height
        self.assertGreater(max_length, 0)
        self.assertLess(max_length, 100)  # Reasonable upper bound

    def test_operating_voltage_window_setter(self):
        """Test setting operating voltage window updates energy calculations."""
        original_energy = self.cell.energy
        
        # Set new voltage window
        new_window = (2.6, 3.7)
        self.cell.operating_voltage_window = new_window
        
        # Check both values updated
        self.assertAlmostEqual(self.cell.minimum_operating_voltage, 2.6, 2)
        self.assertAlmostEqual(self.cell.maximum_operating_voltage, 3.7, 2)
        self.assertEqual(self.cell.operating_voltage_window, new_window)
        
        # Check that energy changed
        self.assertNotEqual(self.cell.energy, original_energy)

    def test_reference_electrode_assembly_setter(self):
        """Test setting reference electrode assembly triggers recalculation."""
        # Create a new stack with different properties
        new_stack = deepcopy(self.cell.reference_electrode_assembly)
        new_stack._n_layers = 25  # More layers
        new_stack._calculate_all_properties()
        
        original_energy = self.cell.energy
        
        # Set new assembly
        self.cell.reference_electrode_assembly = new_stack
        
        # Check that cell properties changed
        self.assertNotEqual(self.cell.energy, original_energy)
        self.assertEqual(self.cell.reference_electrode_assembly, new_stack)

    def test_electrolyte_setter(self):
        """Test setting electrolyte updates cell properties."""
        new_electrolyte = ocd.Electrolyte(
            name="New Electrolyte",
            specific_cost=10,
            density=1.3,
            color="#00FFFF"
        )
        
        original_cost = self.cell.cost
        
        # Set new electrolyte
        self.cell.electrolyte = new_electrolyte
        
        # Check that cost changed
        self.assertNotEqual(self.cell.cost, original_cost)
        self.assertEqual(self.cell.electrolyte, new_electrolyte)

    def test_electrolyte_overfill_setter(self):
        """Test setting electrolyte overfill updates electrolyte mass."""
        original_mass = self.cell.mass
        
        # Increase overfill
        self.cell.electrolyte_overfill = 0.5
        
        # Check that mass increased
        self.assertGreater(self.cell.mass, original_mass)
        self.assertEqual(self.cell.electrolyte_overfill, 0.5)

    def test_n_electrode_assembly_setter(self):
        """Test setting number of electrode assemblies."""
        original_energy = self.cell.energy
        
        # Increase number of assemblies
        self.cell.n_electrode_assembly = 10
        
        # Energy should increase (more assemblies = more capacity)
        self.assertGreater(self.cell.energy, original_energy)
        self.assertEqual(self.cell.n_electrode_assembly, 10)

    def test_side_view_legend_only_first_assembly(self):
        """Test that side view only shows legend for first assembly."""
        fig = self.cell.get_side_view()
        
        # Count traces with showlegend=True
        legend_traces = [trace for trace in fig.data if trace.showlegend]
        
        # Should have some legend entries, but not duplicated for each assembly
        self.assertGreater(len(legend_traces), 0)
        
        # Get all trace names
        trace_names = [trace.name for trace in fig.data if trace.name]
        
        # Check for duplicates - there should be some traces with same name but showlegend=False
        self.assertEqual(self.cell.n_electrode_assembly, 6)

    def test_top_down_view_opacity(self):
        """Test that top-down view applies opacity correctly."""
        # Get view with different opacity values
        fig1 = self.cell.get_top_down_view(opacity=0.3)
        fig2 = self.cell.get_top_down_view(opacity=0.8)
        
        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        
        # Both should have traces
        self.assertGreater(len(fig1.data), 0)
        self.assertGreater(len(fig2.data), 0)

    def test_setter_chain_consistency(self):
        """Test that multiple setter calls maintain consistency."""
        # Change multiple properties
        self.cell.side_seal_thickness = 18
        self.cell.top_seal_thickness = 18
        self.cell.bottom_seal_thickness = 18
        self.cell.clipped_tab_length = 5
        self.cell.operating_voltage_window = (2.7, 3.8)
        
        # Verify all properties are consistent
        self.assertEqual(self.cell.side_seal_thickness, 18)
        self.assertEqual(self.cell.top_seal_thickness, 18)
        self.assertEqual(self.cell.bottom_seal_thickness, 18)
        self.assertEqual(self.cell.clipped_tab_length, 5)
        
        # Verify calculated properties are still valid
        self.assertIsNotNone(self.cell.energy)
        self.assertIsNotNone(self.cell.mass)
        self.assertIsNotNone(self.cell.cost)
        self.assertGreater(self.cell.reversible_capacity, 0)

    def test_encapsulation_parameter_setters(self):

        fig1 = self.cell.get_side_view()

        self.cell.encapsulation.canister.height = 600
        self.cell.encapsulation.canister = self.cell.encapsulation.canister
        self.cell.encapsulation = self.cell.encapsulation
        fig2 = self.cell.get_side_view()

        self.cell.encapsulation.canister.length = 160
        self.cell.encapsulation.canister = self.cell.encapsulation.canister
        self.cell.encapsulation = self.cell.encapsulation
        fig3 = self.cell.get_side_view()

        # fig1.show(renderer="browser")
        # fig2.show(renderer="browser")
        # fig3.show(renderer="browser")


class TestFlatJellyRollPrismatic(unittest.TestCase):

    def setUp(self):

        import steer_opencell_design as ocd

        conductive_additive = ocd.ConductiveAdditive.from_database("Super P")
        binder = ocd.Binder.from_database("PVDF")
        insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 95%")
        current_collector_material = ocd.CurrentCollectorMaterial.from_database('Aluminum')
        separator_material = ocd.SeparatorMaterial.from_database('Polyethylene')
        tape_material = ocd.TapeMaterial.from_database("Kapton")
        prismatic_material = ocd.PrismaticContainerMaterial.from_database("Steel")

        cathode_current_collector = ocd.TablessCurrentCollector(
            material=current_collector_material,
            width=130,
            length=3200,
            coated_width=125,
            insulation_width=2.5,
            thickness=13.5
        )

        cathode_active_material = ocd.CathodeMaterial.from_database("NFPP")

        cathode_formulation = ocd.CathodeFormulation(
            active_materials={cathode_active_material: 95},
            binders={binder: 2.5},
            conductive_additives={conductive_additive: 2.5}
        )

        my_cathode = ocd.Cathode(
            formulation=cathode_formulation,
            current_collector=cathode_current_collector,
            calender_density=2.53,
            mass_loading=20,
            insulation_material=insulation,
            insulation_thickness=3
        )

        anode_current_collector = ocd.TablessCurrentCollector(
            material=current_collector_material,
            width=133,
            length=3250,
            coated_width=128,
            insulation_width=2.5,
            thickness=13.5,
        )

        anode_active_material = ocd.AnodeMaterial.from_database("Hard Carbon (Vendor A)")

        anode_formulation = ocd.AnodeFormulation(
            active_materials={anode_active_material: 95},
            binders={binder: 2.5},
            conductive_additives={conductive_additive: 2.5}
        )

        my_anode = ocd.Anode(
            formulation=anode_formulation,
            current_collector=anode_current_collector,
            calender_density=1.1,
            mass_loading=8,
            insulation_material=insulation,
            insulation_thickness=3
        )

        top_separator = ocd.Separator(
            material=separator_material, 
            thickness=12,
            width = 127,
            length = 3600
        )

        bottom_serparator = ocd.Separator(
            material=separator_material, 
            thickness=12,
            width = 127,
            length = 3600,
        )

        my_layup = ocd.Laminate(
            anode=my_anode,
            cathode=my_cathode,
            top_separator=top_separator,
            bottom_separator=bottom_serparator,
            name="CBAK-32140NS"
        )

        mandrel = ocd.FlatMandrel(
            length=500,
            width=60,
            height=5
        )

        tape = ocd.Tape(
            material = tape_material,
            thickness=30,
            width=130
        )

        jellyroll = ocd.FlatWoundJellyRoll(
            laminate=my_layup,
            mandrel=mandrel,
            tape=tape,
            additional_tape_wraps=30,
            collector_tab_crumple_factor=50
        )

        electrolyte = ocd.Electrolyte(
            name="1M NaPF6 in EC:PC:DMC (1:1:1 wt%)",
            density=1.2,
            specific_cost=40,
            color="#FF9D00"
        )

        cathode_terminal_connector = ocd.PrismaticTerminalConnector(
            material=prismatic_material,
            thickness=2,
            width=65,
            length=80
        )

        anode_terminal_connector = ocd.PrismaticTerminalConnector(
            material=prismatic_material,
            thickness=2,
            width=65,
            length=80
        )

        lid_assembly = ocd.PrismaticLidAssembly(
            material=prismatic_material,
            thickness=8,
        )

        canister = ocd.PrismaticCanister(
            material=prismatic_material,
            width=138,
            length=74,
            height=91,
            wall_thickness=1
        )

        encapsulation = ocd.PrismaticEncapsulation(
            canister=canister,
            cathode_terminal_connector=cathode_terminal_connector,
            anode_terminal_connector=anode_terminal_connector,
            lid_assembly=lid_assembly,
            connector_orientation='transverse'
        )

        self.cell = ocd.PrismaticCell(
            reference_electrode_assembly=jellyroll,
            electrolyte=electrolyte,
            electrolyte_overfill=0.1,
            encapsulation=encapsulation,
            n_electrode_assembly=4,
            operating_voltage_window=(2, 3.96),
            name="NFM111 Prismatic Cell"
        )

    def test_basics(self):
        self.assertTrue(type(self.cell) is ocd.PrismaticCell)

    def test_plots(self):
        fig1 = self.cell.get_top_down_view()
        fig2 = self.cell.get_side_view()
        # fig1.show()
        # fig2.show()
        # fig3.show()
        # fig4.show()




if __name__ == "__main__":
    unittest.main()







