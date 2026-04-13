"""Public entry points for PyBaMM-backed rate-capability analysis."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .dfn_runner import DFNRunner
from .geometry import extract_pybamm_geometry
from .parameters import build_pybamm_parameter_values
from .results import RateCapabilityResult, RateCurveResult


def simulate_rate_capability(
    cell: Any,
    user_parameters: Mapping[str, Any] | Any,
    c_rates: Iterable[float],
    *,
    model_options: Mapping[str, Any] | None = None,
    simulation_kwargs: Mapping[str, Any] | None = None,
    solver: Any | None = None,
    raise_on_failure: bool = False,
) -> RateCapabilityResult:
    """Run a DFN discharge sweep across one or more C-rates."""

    normalized_rates = [float(rate) for rate in c_rates]
    if not normalized_rates:
        raise ValueError("At least one C-rate must be provided.")

    geometry = extract_pybamm_geometry(cell)
    parameter_values = build_pybamm_parameter_values(cell, user_parameters, validate=True)
    runner = DFNRunner(
        parameter_values=parameter_values,
        geometry=geometry,
        model_options=model_options,
        simulation_kwargs=simulation_kwargs,
        solver=solver,
    )

    runs: dict[float, RateCurveResult] = {}
    for c_rate in normalized_rates:
        try:
            runs[c_rate] = runner.run_rate(c_rate)
        except Exception as exc:
            if raise_on_failure:
                raise
            runs[c_rate] = RateCurveResult.failed(
                c_rate=c_rate,
                lower_voltage_cutoff_v=geometry.lower_voltage_cutoff_v,
                error_message=str(exc),
            )

    return RateCapabilityResult(
        cell_name=cell.name,
        lower_voltage_cutoff_v=geometry.lower_voltage_cutoff_v,
        upper_voltage_cutoff_v=geometry.upper_voltage_cutoff_v,
        runs=runs,
    )
