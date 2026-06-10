# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Decorators for automatic property recalculation."""

from steer_core.Decorators.General import recalculate

calculate_electrochemical_properties = recalculate("electrochemical_properties")
"""Decorator that triggers ``_calculate_electrochemical_properties`` after the
decorated setter runs.  Apply to setters that change electrochemical state
(e.g. voltage cutoff, capacity scaling)."""

calculate_weld_tab_properties = recalculate("weld_tab_properties")
"""Decorator that triggers ``_calculate_weld_tab_properties`` after the
decorated setter runs."""

