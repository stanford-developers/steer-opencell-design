# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for ``Utils/Validation.py`` and ``Utils/Decorators.py``.

These modules are tiny but currently under-covered:
  * ``Utils/Decorators.py`` is at 0 % \u2014 the module-level alias
    decorators (``calculate_electrochemical_properties`` and
    ``calculate_weld_tab_properties``) are defined but never imported by
    any test.
  * ``Utils/Validation.py`` is at 83 % \u2014 the ``ValueError`` branch in
    ``validate_electrochemical_reference`` is uncovered.
"""

import unittest

from steer_opencell_design.Utils import Decorators
from steer_opencell_design.Utils.Validation import (
    ALLOWED_REFERENCE,
    validate_electrochemical_reference,
)


class TestValidateElectrochemicalReference(unittest.TestCase):
    def test_accepts_each_allowed_reference(self):
        for reference in ALLOWED_REFERENCE:
            try:
                validate_electrochemical_reference(reference)
            except ValueError as exc:
                self.fail(
                    f"validate_electrochemical_reference({reference!r}) "
                    f"unexpectedly raised: {exc}"
                )

    def test_rejects_unknown_reference(self):
        with self.assertRaises(ValueError) as ctx:
            validate_electrochemical_reference("Mg/Mg2+")
        msg = str(ctx.exception)
        self.assertIn("Mg/Mg2+", msg)
        self.assertIn("Li/Li+", msg)

    def test_rejects_non_string(self):
        # ``ValidationMixin.validate_string`` should reject a non-str input.
        with self.assertRaises((TypeError, ValueError)):
            validate_electrochemical_reference(42)  # type: ignore[arg-type]

    def test_allowed_reference_whitelist_is_what_we_expect(self):
        # If this list ever changes, the change should be deliberate; pin it.
        self.assertEqual(set(ALLOWED_REFERENCE), {"Na/Na+", "Li/Li+"})


class TestDecoratorAliases(unittest.TestCase):
    """The aliases must (a) exist and (b) behave like ``recalculate(name)``."""

    def test_calculate_electrochemical_properties_exists_and_is_callable(self):
        self.assertTrue(callable(Decorators.calculate_electrochemical_properties))

    def test_calculate_weld_tab_properties_exists_and_is_callable(self):
        self.assertTrue(callable(Decorators.calculate_weld_tab_properties))

    def test_decorator_invokes_target_recalculation_method(self):
        """Applying ``@calculate_electrochemical_properties`` to a setter must
        call ``_calculate_electrochemical_properties`` after the setter runs.
        """
        calls = []

        class Probe:
            _update_properties = True

            def _calculate_electrochemical_properties(self):
                calls.append("electro")

            @Decorators.calculate_electrochemical_properties
            def my_setter(self, value):
                calls.append(("set", value))

        probe = Probe()
        probe.my_setter(42)

        # Setter must run before the recalculation hook.
        self.assertEqual(calls, [("set", 42), "electro"])

    def test_weld_tab_decorator_invokes_corresponding_recalculation(self):
        calls = []

        class Probe:
            _update_properties = True

            def _calculate_weld_tab_properties(self):
                calls.append("weld")

            @Decorators.calculate_weld_tab_properties
            def my_setter(self, value):
                calls.append(("set", value))

        probe = Probe()
        probe.my_setter("hello")
        self.assertEqual(calls, [("set", "hello"), "weld"])

    def test_decorator_skips_recalculation_when_update_disabled(self):
        """``recalculate`` honours ``_update_properties = False`` to suppress
        cascading recomputation during bulk init / loading.
        """
        calls = []

        class Probe:
            _update_properties = False

            def _calculate_electrochemical_properties(self):
                calls.append("electro")

            @Decorators.calculate_electrochemical_properties
            def my_setter(self, value):
                calls.append(("set", value))

        probe = Probe()
        probe.my_setter(7)

        self.assertEqual(calls, [("set", 7)])  # No "electro" appended.


if __name__ == "__main__":
    unittest.main()
