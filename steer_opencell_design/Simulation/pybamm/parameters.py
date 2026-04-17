"""Parameter merging and validation helpers for the PyBaMM integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any

from ._compat import load_pybamm
from .exceptions import MissingPyBaMMParametersError
from .geometry import extract_pybamm_geometry

REQUIRED_NON_GEOMETRY_PARAMETER_KEYS: tuple[str, ...] = (
    "Negative electrode conductivity [S.m-1]",
    "Positive electrode conductivity [S.m-1]",
    "Negative particle diffusivity [m2.s-1]",
    "Positive particle diffusivity [m2.s-1]",
    "Negative particle radius [m]",
    "Positive particle radius [m]",
    "Maximum concentration in negative electrode [mol.m-3]",
    "Maximum concentration in positive electrode [mol.m-3]",
    "Initial concentration in negative electrode [mol.m-3]",
    "Initial concentration in positive electrode [mol.m-3]",
    "Initial concentration in electrolyte [mol.m-3]",
    "Electrolyte diffusivity [m2.s-1]",
    "Electrolyte conductivity [S.m-1]",
    "Cation transference number",
    "Negative electrode exchange-current density [A.m-2]",
    "Positive electrode exchange-current density [A.m-2]",
    "Negative electrode OCP [V]",
    "Positive electrode OCP [V]",
)


def build_pybamm_parameter_values(
    cell: Any,
    user_parameters: Mapping[str, Any] | Any,
    *,
    validate: bool = True,
) -> Any:
    """Merge user-supplied PyBaMM parameters with geometry from an OpenCell design."""

    geometry = extract_pybamm_geometry(cell)
    parameter_values = coerce_pybamm_parameter_values(user_parameters)
    parameter_values.update(geometry.to_parameter_values())

    if validate:
        validate_pybamm_parameter_values(parameter_values)

    return parameter_values


def coerce_pybamm_parameter_values(user_parameters: Mapping[str, Any] | Any) -> Any:
    """Normalize user input into a standalone ``pybamm.ParameterValues`` instance."""

    pybamm = load_pybamm()
    if isinstance(user_parameters, pybamm.ParameterValues):
        return user_parameters.copy()
    if isinstance(user_parameters, Mapping):
        return pybamm.ParameterValues(dict(user_parameters))
    raise TypeError(
        "`user_parameters` must be a mapping of PyBaMM parameter names or an existing "
        "`pybamm.ParameterValues` instance."
    )


def validate_pybamm_parameter_values(
    parameter_values: Any,
    *,
    required_keys: Sequence[str] = REQUIRED_NON_GEOMETRY_PARAMETER_KEYS,
) -> Any:
    """Validate that a parameter set is complete enough to process a DFN model."""

    pybamm = load_pybamm()
    available = {str(key) for key in parameter_values.keys()}
    missing = sorted(set(required_keys) - available)
    if missing:
        raise MissingPyBaMMParametersError(missing)

    model = pybamm.lithium_ion.DFN()
    probe = parameter_values.copy()
    try:
        probe.process_model(model)
        probe.process_geometry(model.default_geometry)
    except KeyError as exc:
        missing_name = _extract_missing_parameter_name(str(exc))
        raise MissingPyBaMMParametersError(
            [missing_name] if missing_name else [],
            detail=str(exc),
        ) from exc

    return parameter_values


def _extract_missing_parameter_name(message: str) -> str | None:
    """Pull the missing parameter name out of a PyBaMM ``KeyError`` message."""

    match = re.search(r"'([^']+)'", message)
    if match:
        return match.group(1)
    return None
