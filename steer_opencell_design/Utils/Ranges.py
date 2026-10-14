# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Ranges for setters that move several parts by the same amount.

A delta setter (a laminate's width, a roll's height, a cell's radius) changes
each of its parts by the change asked of the whole. Part ``i``, sitting at
``value_i`` while the whole is at ``value``, can then follow the whole only over
its own range shifted by ``value - value_i``; the whole can reach only where all
those shifted ranges overlap. Ranges built this way are reachable by the setter
by construction, which is the contract every ``*_range`` keeps.
"""

from typing import Iterable, Optional, Tuple

# The smallest dimension (mm) a part may shrink to under a delta setter.
DIMENSION_FLOOR_MM = 1.0


def shifted_range(
    value: float, parts: Iterable[Tuple[float, Optional[Tuple[float, float]]]]
) -> Tuple[float, float]:
    """The values (min, max) the whole can reach when every part moves with it.

    ``parts`` is ``((part_value, (part_min, part_max) or None), ...)``. A part
    with no range of its own (``None``, e.g. one whose range follows another
    part) only has to stay above ``DIMENSION_FLOOR_MM``. An empty overlap
    collapses to the current value.
    """
    low, high = float("-inf"), float("inf")
    for part_value, part_range in parts:
        offset = value - part_value
        part_min, part_max = (
            part_range if part_range is not None else (DIMENSION_FLOOR_MM, float("inf"))
        )
        part_min = max(part_min, DIMENSION_FLOOR_MM)
        low = max(low, part_min + offset)
        high = min(high, part_max + offset)
    if low > high:
        return (value, value)
    return (low, high)
