# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Structural type protocols for the OpenCell composition tree.

These ``typing.Protocol`` subclasses formalise the "duck-typed" contracts
that the composition axis (Cell → Assembly → Layup → Electrode) relies on.
They are intended purely for **type-hinting and IDE navigation** — no
behavioural change is implied.

Each protocol lists the public attributes that downstream code touches when
it treats an object as "an assembly", "a layup", etc. Keeping these
contracts in one place makes it easier to spot when a new concrete class
drifts from the expectations of the rest of the code.

Usage example::

    from steer_opencell_design.Utils.Protocols import SupportsLayup

    def print_n_over_p(layup: SupportsLayup) -> None:
        print(layup.np_ratio)

Because these are ``runtime_checkable`` protocols, ``isinstance(obj, SupportsLayup)``
works too, but should be used sparingly — structural typing sidesteps most of
the need for ``isinstance`` checks.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SupportsElectrode(Protocol):
    """Protocol for electrode-shaped objects (Anode, Cathode).

    An electrode owns a formulation, a current collector, and provides an
    areal-capacity curve used by its containing layup / assembly.
    """

    formulation: Any
    current_collector: Any

    @property
    def _areal_capacity_curve(self) -> Any:  # noqa: D401 - protocol accessor
        """ndarray of (charge [A·s/m^2], voltage [V], direction) rows."""
        ...


@runtime_checkable
class SupportsLayup(Protocol):
    """Protocol for layup-shaped objects (MonoLayer, ZFoldMonoLayer, Laminate).

    A layup is the electrochemical + geometric sandwich
    ``separator / anode / separator / cathode`` on which all cell-level
    curve construction depends.
    """

    cathode: Any
    anode: Any
    top_separator: Any
    bottom_separator: Any

    @property
    def np_ratio(self) -> float:  # noqa: D401 - protocol accessor
        """N/P ratio of the layup (see ``Layups/Base.py``)."""
        ...


@runtime_checkable
class SupportsElectrodeAssembly(Protocol):
    """Protocol for electrode-assembly-shaped objects (Stacks, JellyRolls).

    An assembly wraps exactly one ``layup`` (or ``laminate`` for jelly rolls,
    which is a ``_Layup`` subclass) and exposes an interfacial area plus the
    ability to compute full-cell capacity curves.
    """

    layup: Any

    @property
    def _interfacial_area(self) -> float:  # noqa: D401 - protocol accessor
        """Total active-area cross-section of the assembly, in m²."""
        ...

    def _calculate_capacity_curves(self) -> None:  # noqa: D401 - protocol method
        """Rebuild the anode / cathode / full-cell capacity curves."""
        ...
