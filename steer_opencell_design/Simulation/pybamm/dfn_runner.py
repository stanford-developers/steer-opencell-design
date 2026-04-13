"""Reusable DFN runner for OpenCell rate-capability simulations."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

import numpy as np

from ._compat import load_pybamm
from .geometry import PyBaMMGeometry
from .results import RateCurveResult


@dataclass
class DFNRunner:
    """Execute constant-current DFN discharge simulations at one or more C-rates."""

    parameter_values: Any
    geometry: PyBaMMGeometry
    model_options: Mapping[str, Any] | None = None
    simulation_kwargs: Mapping[str, Any] | None = None
    solver: Any | None = None

    def run_rate(self, c_rate: float) -> RateCurveResult:
        """Run one isothermal DFN discharge at a requested C-rate."""

        if c_rate <= 0:
            raise ValueError("C-rates must be positive.")

        pybamm = load_pybamm()
        model = pybamm.lithium_ion.DFN(options=dict(self.model_options or {}))
        experiment = pybamm.Experiment(
            [f"Discharge at {c_rate:g} C until {self.geometry.lower_voltage_cutoff_v:g} V"]
        )

        simulation_inputs = dict(self.simulation_kwargs or {})
        simulation_inputs.update(
            {
                "parameter_values": self.parameter_values.copy(),
                "experiment": experiment,
            }
        )

        solver = self.solver if self.solver is not None else _default_solver(pybamm)
        if solver is not None:
            simulation_inputs["solver"] = solver

        simulation = pybamm.Simulation(model, **simulation_inputs)
        solution = simulation.solve()

        time_s = _extract_time(solution)
        voltage_v = _extract_solution_array(solution, "Terminal voltage [V]", "Voltage [V]")
        current_a = _extract_solution_array(
            solution,
            "Current [A]",
            default=np.full_like(time_s, self.geometry.nominal_cell_capacity_ah * c_rate, dtype=float),
        )

        discharge_capacity_ah = _cumulative_integral(time_s, np.abs(current_a)) / 3600.0
        discharge_energy_wh = _cumulative_integral(time_s, np.abs(current_a) * voltage_v) / 3600.0
        termination = getattr(solution, "termination", None)

        return RateCurveResult(
            c_rate=float(c_rate),
            time_s=time_s,
            voltage_v=voltage_v,
            current_a=current_a,
            discharge_capacity_ah=discharge_capacity_ah,
            discharge_energy_wh=discharge_energy_wh,
            status="success",
            lower_voltage_cutoff_v=self.geometry.lower_voltage_cutoff_v,
            termination=str(termination) if termination is not None else None,
        )


def _default_solver(pybamm: Any) -> Any | None:
    """Prefer IDAKLU when it is available, otherwise use PyBaMM's default solver."""

    if hasattr(pybamm, "IDAKLUSolver"):
        return pybamm.IDAKLUSolver()
    return None


def _extract_time(solution: Any) -> np.ndarray:
    """Return the simulation time vector in seconds."""

    time_s = np.asarray(getattr(solution, "t", []), dtype=float).reshape(-1)
    if time_s.size > 0:
        return time_s
    return _extract_solution_array(solution, "Time [s]")


def _extract_solution_array(solution: Any, *names: str, default: np.ndarray | None = None) -> np.ndarray:
    """Read a processed variable from a solution using one of several fallback names."""

    for name in names:
        try:
            variable = solution[name]
        except Exception:
            continue

        entries = getattr(variable, "entries", None)
        if entries is None:
            continue
        return np.asarray(entries, dtype=float).reshape(-1)

    if default is not None:
        return np.asarray(default, dtype=float).reshape(-1)
    raise KeyError(f"Could not extract any of the requested PyBaMM outputs: {names}")


def _cumulative_integral(time_s: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Compute a cumulative trapezoidal integral without adding a SciPy dependency."""

    if time_s.size == 0:
        return np.array([], dtype=float)

    deltas = np.diff(time_s)
    averages = (values[1:] + values[:-1]) / 2.0
    increments = deltas * averages
    return np.concatenate(([0.0], np.cumsum(increments)))
