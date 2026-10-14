# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The range contract: every ``x_range`` / ``x_hard_range`` is reachable.

A UI offers each field's range as its slider and clamps entries to it, so a
bound the setter then refuses, clamps, snaps or silently re-fits is a slider
that "does nothing". This walks every settable numeric property that reports a
range, on each component of representative reference cells, sets it to each
of its soft and hard bounds on a fresh copy of the cell, and requires the
property to read back as that bound.

Fields are discovered, not listed, so a new setter or range is covered the
moment it exists. A genuine exception goes in ``KNOWN_EXCEPTIONS`` with its
reason; the goal is to keep that empty.
"""

import math
import unittest
import warnings
from copy import deepcopy

from steer_opencell_design.Components.Electrodes import ElectrodeControlMode
from steer_opencell_design.Constructions.Cells.Base import _Cell

# (table, name): one per form factor and assembly kind, chosen to be quick.
CELLS = (
    ("teardowns", "TESLA 4680"),  # cylindrical, tabless notched roll
    ("cell_references", "NMC811 Cylindrical Tabbed Cell"),  # cylindrical, weld tabs
    ("cell_references", "LFP Flat Wound Prismatic Cell"),  # prismatic, flat roll
    ("cell_references", "NMC811 Stacked Pouch Cell"),  # pouch, punched stack
)

_ASSEMBLY = ("_reference_electrode_assembly",)
_LAYUP = _ASSEMBLY + ("_layup",)

# Attribute paths from the cell to every component whose fields are checked.
PATHS = (
    (),
    ("_encapsulation",),
    *(
        ("_encapsulation", part)
        for part in (
            "_canister",
            "_lid_assembly",
            "_cathode_terminal_connector",
            "_anode_terminal_connector",
            "_cathode_terminal",
            "_anode_terminal",
            "_top_laminate",
            "_bottom_laminate",
        )
    ),
    _ASSEMBLY,
    _LAYUP,
    _ASSEMBLY + ("_mandrel",),
    _ASSEMBLY + ("_tape",),
    _LAYUP + ("_cathode",),
    _LAYUP + ("_anode",),
    _LAYUP + ("_cathode", "_current_collector"),
    _LAYUP + ("_anode", "_current_collector"),
    _LAYUP + ("_separator",),
    _LAYUP + ("_top_separator",),
    _LAYUP + ("_bottom_separator",),
)

# The electrode fields whose ranges depend on the control mode.
COATING_FIELDS = ("mass_loading", "calender_density", "coating_thickness", "porosity")

# ("path/joined/by/slashes", field) -> reason. Keep empty.
KNOWN_EXCEPTIONS: dict = {}


def _navigate(obj, path):
    for attribute in path:
        obj = getattr(obj, attribute, None)
        if obj is None:
            return None
    return obj


def _ranged_fields(obj):
    """Public settable properties with a numeric value and a two-sided range."""
    names = []
    for cls in type(obj).__mro__:
        for name, attribute in vars(cls).items():
            if (
                name.startswith("_")
                or name in names
                or not isinstance(attribute, property)
                or attribute.fset is None
            ):
                continue
            names.append(name)
    fields = []
    for name in names:
        try:
            value = getattr(obj, name)
            bounds = getattr(obj, f"{name}_range", None)
        except Exception:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if isinstance(bounds, tuple) and len(bounds) == 2:
            fields.append(name)
    return fields


def _bounds(obj, name):
    """The distinct finite soft and hard bounds of one field, labelled."""
    bounds = []
    for suffix in ("_range", "_hard_range"):
        pair = getattr(obj, name + suffix, None)
        if not (isinstance(pair, tuple) and len(pair) == 2):
            continue
        for label, value in zip(("min", "max"), pair):
            if isinstance(value, (int, float)) and math.isfinite(value):
                if all(value != existing for _, existing in bounds):
                    bounds.append((suffix[1:] + "." + label, float(value)))
    return bounds


def _reaches(obj, name, value):
    """None when setting ``name`` to ``value`` reads back, else what went wrong."""
    try:
        setattr(obj, name, value)
        got = getattr(obj, name)
    except Exception as exc:  # a bound the setter refuses
        return f"raises {exc!r}"
    if not isinstance(got, (int, float)) or abs(got - value) > max(
        1e-6 * max(1.0, abs(value)), 1e-9
    ):
        return f"reads back {got!r}"
    return None


def contract_failures(cell):
    """Every bound of every ranged field on ``cell`` that its setter cannot reach."""
    failures = []
    for path in PATHS:
        component = _navigate(cell, path)
        if component is None:
            continue
        where = "/".join(path)
        for name in _ranged_fields(component):
            if (where, name) in KNOWN_EXCEPTIONS:
                continue
            for label, value in _bounds(component, name):
                copy = _navigate(deepcopy(cell), path)
                problem = _reaches(copy, name, value)
                if problem:
                    failures.append(
                        f"{where or 'cell'}.{name} {label}={value:g}: {problem}"
                    )
    return failures


def coating_failures(cell):
    """The coating fields' bounds under every control mode (the generic walk
    sees only the mode a cell was saved with)."""
    failures = []
    for electrode_name in ("_cathode", "_anode"):
        base = _navigate(cell, _LAYUP + (electrode_name,))
        for mode in ElectrodeControlMode:
            electrode = deepcopy(base)
            electrode.control_mode = mode
            for name in COATING_FIELDS:
                for label, value in _bounds(electrode, name):
                    copy = deepcopy(electrode)
                    problem = _reaches(copy, name, value)
                    if problem:
                        failures.append(
                            f"{electrode_name}[{mode.value}].{name} {label}={value:g}: {problem}"
                        )
    return failures


class TestRangeContract(unittest.TestCase):
    """Each reference cell's ranges are all reachable by their setters."""

    def _check(self, table, name, failures_of):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cell = _Cell.from_database(name, table_name=table)
            failures = failures_of(cell)
        self.assertEqual(failures, [], f"{name}: unreachable range bounds")

    def test_every_range_is_reachable(self):
        for table, name in CELLS:
            with self.subTest(cell=name):
                self._check(table, name, contract_failures)

    def test_coating_ranges_follow_the_control_mode(self):
        for table, name in CELLS:
            with self.subTest(cell=name):
                self._check(table, name, coating_failures)


if __name__ == "__main__":
    unittest.main()
