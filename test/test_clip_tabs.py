# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Direct tests for ``_BaseCell._clip_tabs``.

This method was hoisted from PouchCell/PrismaticCell/FlexFrameCell into the
base class. The contract is:

  * If the subclass has no ``_clipped_tab_length`` attribute → no-op
    (this is the documented behaviour for ``CylindricalCell``).
  * If ``_clipped_tab_length`` is ``None`` → no-op.
  * Otherwise → propagate the clipped length to every electrode assembly
    via ``_clip_current_collector_tabs``.

We exercise the contract with mock assemblies so the test is not coupled
to the (~140-line) cell construction fixtures. The full integration path
is already covered by ``test_cells.py``.
"""

import unittest
from unittest.mock import MagicMock

from steer_opencell_design.Constructions.Cells.Base import _Cell


class _StubCellWithoutClippedTab(_Cell):
    """Mimics ``CylindricalCell``: no ``_clipped_tab_length`` attribute at all."""

    def __init__(self, assemblies):
        # Bypass the heavy ``_Cell.__init__`` — we are unit-testing
        # ``_clip_tabs`` in isolation.
        self._electrode_assemblies = assemblies

    def _calculate_all_properties(self) -> None:  # satisfy ABC
        pass


class _StubCellWithClippedTab(_Cell):
    """Mimics ``PouchCell`` / ``PrismaticCell`` / ``FlexFrameCell``."""

    def __init__(self, assemblies, clipped_tab_length):
        self._electrode_assemblies = assemblies
        self._clipped_tab_length = clipped_tab_length

    def _calculate_all_properties(self) -> None:  # satisfy ABC
        pass


class TestClipTabsContract(unittest.TestCase):
    def test_no_op_when_attribute_is_missing(self):
        assembly_a, assembly_b = MagicMock(), MagicMock()
        cell = _StubCellWithoutClippedTab([assembly_a, assembly_b])

        cell._clip_tabs()

        assembly_a._clip_current_collector_tabs.assert_not_called()
        assembly_b._clip_current_collector_tabs.assert_not_called()

    def test_no_op_when_attribute_is_none(self):
        assembly_a, assembly_b = MagicMock(), MagicMock()
        cell = _StubCellWithClippedTab(
            [assembly_a, assembly_b], clipped_tab_length=None
        )

        cell._clip_tabs()

        assembly_a._clip_current_collector_tabs.assert_not_called()
        assembly_b._clip_current_collector_tabs.assert_not_called()

    def test_propagates_to_every_assembly(self):
        assembly_a, assembly_b, assembly_c = MagicMock(), MagicMock(), MagicMock()
        clipped_length_si = 5e-3  # 5 mm in SI.
        cell = _StubCellWithClippedTab(
            [assembly_a, assembly_b, assembly_c],
            clipped_tab_length=clipped_length_si,
        )

        cell._clip_tabs()

        for assembly in (assembly_a, assembly_b, assembly_c):
            assembly._clip_current_collector_tabs.assert_called_once_with(
                clipped_length_si
            )

    def test_no_assemblies_is_a_silent_no_op(self):
        cell = _StubCellWithClippedTab([], clipped_tab_length=1e-3)
        # Must not raise even with an empty list of assemblies.
        cell._clip_tabs()


if __name__ == "__main__":
    unittest.main()
