# SPDX-FileCopyrightText: 2024-2026 Nicholas Siemons
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Data access layer for OpenCell — registers domain tables and provides
the ``OpenCellDataManager`` subclass with material / cell convenience methods.
"""

from steer_opencell_design.Data.OpenCellDataManager import (  # noqa: F401
    OpenCellDataManager,
    register_opencell_tables,
    MATERIAL_TABLES,
    CELL_TABLES,
    ALL_TABLES,
)
