# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the structural-typing Protocols in ``Utils/Protocols.py``.

These guard the contract between the composition tree
(Cell → Assembly → Layup → Electrode) and any caller that wants to type
or branch on "is this thing a layup-shape?". They use real concrete
classes so a future rename like ``layup → ``stack`` is caught here, and
also use a hand-rolled duck-typed dummy to confirm the structural
behaviour (i.e. inheritance is not required).
"""

import unittest
from typing import Any

from steer_opencell_design.Components.CurrentCollectors.Notched import (
    NotchedCurrentCollector,
)
from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import (
    WoundJellyRoll,
)
from steer_opencell_design.Constructions.ElectrodeAssemblies.Tape import Tape
from steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment import (
    RoundMandrel,
)
from steer_opencell_design.Constructions.Layups.Laminate import Laminate
from steer_opencell_design.Materials.ActiveMaterials import (
    AnodeMaterial,
    CathodeMaterial,
)
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive
from steer_opencell_design.Materials.Formulations import (
    AnodeFormulation,
    CathodeFormulation,
)
from steer_opencell_design.Materials.Other import (
    CurrentCollectorMaterial,
    InsulationMaterial,
    SeparatorMaterial,
    TapeMaterial,
)
from steer_opencell_design.Utils.Protocols import (
    SupportsElectrode,
    SupportsElectrodeAssembly,
    SupportsLayup,
)


def _build_minimal_assembly():
    """Build a minimal Cathode/Anode/Laminate/JellyRoll for protocol checks."""
    additive = ConductiveAdditive(
        name="super_P", specific_cost=15, density=2.0, color="#000000"
    )
    binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

    cathode_mat = CathodeMaterial.from_database("LFP")
    cathode_mat.specific_cost = 6
    cathode_mat.density = 3.6
    cathode_formulation = CathodeFormulation(
        active_materials={cathode_mat: 95},
        binders={binder: 2},
        conductive_additives={additive: 3},
    )
    cc_mat = CurrentCollectorMaterial(
        name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
    )
    cathode_cc = NotchedCurrentCollector(
        material=cc_mat,
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
        formulation=cathode_formulation,
        mass_loading=12,
        current_collector=cathode_cc,
        calender_density=2.6,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    anode_mat = AnodeMaterial.from_database("Synthetic Graphite")
    anode_mat.specific_cost = 4
    anode_mat.density = 2.2
    anode_formulation = AnodeFormulation(
        active_materials={anode_mat: 90},
        binders={binder: 5},
        conductive_additives={additive: 5},
    )
    anode_cc = NotchedCurrentCollector(
        material=cc_mat,
        length=4500,
        width=306,
        thickness=8,
        tab_width=60,
        tab_spacing=100,
        tab_height=18,
        insulation_width=6,
        coated_tab_height=2,
    )
    anode = Anode(
        formulation=anode_formulation,
        mass_loading=7.2,
        current_collector=anode_cc,
        calender_density=1.1,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    sep_mat = SeparatorMaterial(
        name="Polyethylene",
        specific_cost=2,
        density=0.94,
        color="#FDFDB7",
        porosity=45,
    )
    top_separator = Separator(material=sep_mat, thickness=25, width=310, length=5000)
    bottom_separator = Separator(
        material=sep_mat, thickness=25, width=310, length=7000
    )

    layup = Laminate(
        anode=anode,
        cathode=cathode,
        top_separator=top_separator,
        bottom_separator=bottom_separator,
    )

    mandrel = RoundMandrel(diameter=5, length=350)
    tape_material = TapeMaterial.from_database("Kapton")
    tape_material.density = 1.42
    tape_material.specific_cost = 70
    tape = Tape(material=tape_material, thickness=30)

    assembly = WoundJellyRoll(
        laminate=layup, mandrel=mandrel, tape=tape, additional_tape_wraps=5
    )

    return cathode, anode, layup, assembly


class TestProtocolsAcceptRealClasses(unittest.TestCase):
    """Real concrete classes must satisfy each Protocol's structural shape."""

    @classmethod
    def setUpClass(cls):
        cls.cathode, cls.anode, cls.layup, cls.assembly = _build_minimal_assembly()

    def test_cathode_is_supports_electrode(self):
        self.assertIsInstance(self.cathode, SupportsElectrode)

    def test_anode_is_supports_electrode(self):
        self.assertIsInstance(self.anode, SupportsElectrode)

    def test_laminate_is_supports_layup(self):
        self.assertIsInstance(self.layup, SupportsLayup)

    def test_woundjellyroll_is_supports_assembly(self):
        self.assertIsInstance(self.assembly, SupportsElectrodeAssembly)


class TestProtocolsRejectIncompleteObjects(unittest.TestCase):
    def test_bare_object_is_not_an_electrode(self):
        self.assertNotIsInstance(object(), SupportsElectrode)

    def test_bare_object_is_not_a_layup(self):
        self.assertNotIsInstance(object(), SupportsLayup)

    def test_bare_object_is_not_an_assembly(self):
        self.assertNotIsInstance(object(), SupportsElectrodeAssembly)


class _DuckTypedLayup:
    """Hand-rolled duck-typed layup with no inheritance from any real class."""

    def __init__(self):
        self.cathode: Any = "anything"
        self.anode: Any = "anything"
        self.top_separator: Any = "anything"
        self.bottom_separator: Any = "anything"

    @property
    def np_ratio(self) -> float:
        return 1.0


class _DuckTypedAssembly:
    def __init__(self):
        self.layup: Any = _DuckTypedLayup()

    @property
    def _interfacial_area(self) -> float:
        return 1.23

    def _calculate_capacity_curves(self) -> None:
        pass


class TestProtocolsAcceptDuckTypedObjects(unittest.TestCase):
    """A class that is *not* in the inheritance hierarchy must still pass."""

    def test_duck_typed_layup_passes_supports_layup(self):
        self.assertIsInstance(_DuckTypedLayup(), SupportsLayup)

    def test_duck_typed_assembly_passes_supports_assembly(self):
        self.assertIsInstance(_DuckTypedAssembly(), SupportsElectrodeAssembly)


if __name__ == "__main__":
    unittest.main()
