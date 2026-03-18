# SPDX-FileCopyrightText: 2024-2026 Nicholas Siemons
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Domain-specific validation utilities for OpenCell electrochemistry."""

from steer_core.Mixins.TypeChecker import ValidationMixin

ALLOWED_REFERENCE = ["Na/Na+", "Li/Li+"]


def validate_electrochemical_reference(reference: str) -> None:
    """Validate the electrochemical reference electrode.

    Parameters
    ----------
    reference : str
        The reference electrode to validate.

    Raises
    ------
    ValueError
        If *reference* is not one of the allowed values.
    """
    ValidationMixin.validate_string(reference, "Electrochemical reference")

    if reference not in ALLOWED_REFERENCE:
        raise ValueError(
            f"Invalid electrochemical reference: {reference}. "
            f"Must be one of {ALLOWED_REFERENCE}."
        )
