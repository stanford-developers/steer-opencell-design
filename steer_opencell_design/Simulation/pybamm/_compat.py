"""Compatibility helpers for lazily importing PyBaMM."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .exceptions import MissingPyBaMMDependencyError

if TYPE_CHECKING:
    import pybamm


def load_pybamm() -> Any:
    """Import PyBaMM only when a simulation entry point is actually used."""

    try:
        import pybamm
    except ImportError as exc:  # pragma: no cover - covered by integration behavior
        raise MissingPyBaMMDependencyError() from exc
    return pybamm
