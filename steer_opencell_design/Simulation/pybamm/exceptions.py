"""Exception types for the optional PyBaMM integration layer."""

from __future__ import annotations

from collections.abc import Iterable


class PyBaMMIntegrationError(RuntimeError):
    """Base error for PyBaMM integration failures."""


class MissingPyBaMMDependencyError(PyBaMMIntegrationError, ImportError):
    """Raised when a PyBaMM-backed API is used without PyBaMM installed."""

    def __init__(self) -> None:
        super().__init__(
            "PyBaMM is required for this simulation workflow. "
            "Install the optional dependency with `pip install \"steer-opencell-design[pybamm]\"` "
            "or add `pybamm` to your environment."
        )


class UnsupportedCellForPyBaMMError(PyBaMMIntegrationError):
    """Raised when a cell design cannot be mapped into the phase-1 DFN workflow."""


class MissingPyBaMMParametersError(PyBaMMIntegrationError):
    """Raised when required PyBaMM parameters are missing from the user input."""

    def __init__(
        self,
        missing_parameters: Iterable[str],
        *,
        detail: str | None = None,
    ) -> None:
        unique = tuple(sorted({str(item) for item in missing_parameters if item}))
        self.missing_parameters = unique
        message = "Missing PyBaMM parameters"
        if unique:
            message = f"{message}: {', '.join(unique)}"
        if detail:
            message = f"{message}. {detail}"
        super().__init__(message)
