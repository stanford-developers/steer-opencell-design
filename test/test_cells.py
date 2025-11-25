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
    CylindricalCell
)

from steer_materials import (
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
            outer_radius=20.0,  # mm
            height=50.0,  # mm
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
            operating_voltage_window=(2.5, 4.1),
        )

    def test_basics(self):
        self.assertIsInstance(self.cell, CylindricalCell)
    
    def test_plots(self):

        fig1 = self.cell.plot_mass_breakdown()
        fig2 = self.cell.plot_cost_breakdown()

        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)

        fig1.show()
        fig2.show()

