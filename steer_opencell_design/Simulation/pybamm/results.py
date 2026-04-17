"""Result containers for PyBaMM-backed rate-capability simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class RateCurveResult:
    """Detailed output for one simulated discharge rate."""

    c_rate: float
    time_s: np.ndarray
    voltage_v: np.ndarray
    current_a: np.ndarray
    discharge_capacity_ah: np.ndarray
    discharge_energy_wh: np.ndarray
    status: str
    lower_voltage_cutoff_v: float
    termination: str | None = None
    error_message: str | None = None

    @classmethod
    def failed(
        cls,
        *,
        c_rate: float,
        lower_voltage_cutoff_v: float,
        error_message: str,
    ) -> "RateCurveResult":
        """Create an empty failure record for a rate that did not solve."""

        empty = np.array([], dtype=float)
        return cls(
            c_rate=c_rate,
            time_s=empty,
            voltage_v=empty,
            current_a=empty,
            discharge_capacity_ah=empty,
            discharge_energy_wh=empty,
            status="failed",
            lower_voltage_cutoff_v=lower_voltage_cutoff_v,
            termination=None,
            error_message=error_message,
        )

    @property
    def delivered_capacity_ah(self) -> float:
        """Delivered discharge capacity at the end of the simulation."""

        if self.discharge_capacity_ah.size == 0:
            return float("nan")
        return float(self.discharge_capacity_ah[-1])

    @property
    def delivered_energy_wh(self) -> float:
        """Delivered discharge energy at the end of the simulation."""

        if self.discharge_energy_wh.size == 0:
            return float("nan")
        return float(self.discharge_energy_wh[-1])

    @property
    def final_voltage_v(self) -> float:
        """Final terminal voltage."""

        if self.voltage_v.size == 0:
            return float("nan")
        return float(self.voltage_v[-1])

    @property
    def cutoff_voltage_reached(self) -> bool | None:
        """Whether the discharge reached the requested lower voltage cut-off."""

        if self.voltage_v.size == 0:
            return None
        return bool(self.final_voltage_v <= self.lower_voltage_cutoff_v + 1e-6)

    def to_dataframe(self) -> pd.DataFrame:
        """Return the time-history data in a pandas-friendly format."""

        return pd.DataFrame(
            {
                "Time [s]": self.time_s,
                "Current [A]": self.current_a,
                "Terminal voltage [V]": self.voltage_v,
                "Discharge capacity [A.h]": self.discharge_capacity_ah,
                "Discharge energy [W.h]": self.discharge_energy_wh,
            }
        )


@dataclass
class RateCapabilityResult:
    """Collection of rate-capability runs for one cell design."""

    cell_name: str
    lower_voltage_cutoff_v: float
    upper_voltage_cutoff_v: float
    runs: dict[float, RateCurveResult] = field(default_factory=dict)

    @property
    def summary(self) -> pd.DataFrame:
        """Convenience alias for the summary table."""

        return self.summary_dataframe()

    def summary_dataframe(self) -> pd.DataFrame:
        """Return a compact rate-capability summary table."""

        successful_runs = [
            run
            for _, run in sorted(self.runs.items())
            if run.status == "success" and np.isfinite(run.delivered_capacity_ah)
        ]
        baseline_capacity = successful_runs[0].delivered_capacity_ah if successful_runs else float("nan")

        rows: list[dict[str, Any]] = []
        for c_rate, run in sorted(self.runs.items()):
            retention = (
                run.delivered_capacity_ah / baseline_capacity
                if successful_runs and np.isfinite(run.delivered_capacity_ah) and baseline_capacity
                else float("nan")
            )
            rows.append(
                {
                    "C-rate": c_rate,
                    "Delivered capacity [A.h]": run.delivered_capacity_ah,
                    "Delivered energy [W.h]": run.delivered_energy_wh,
                    "Capacity retention vs baseline": retention,
                    "Final voltage [V]": run.final_voltage_v,
                    "Lower voltage cut-off reached": run.cutoff_voltage_reached,
                    "Solve status": run.status,
                    "Termination": run.termination,
                    "Error": run.error_message,
                }
            )

        return pd.DataFrame(rows)

    def curve_dataframe(self, c_rate: float) -> pd.DataFrame:
        """Return the detailed time-history for one C-rate."""

        return self.runs[c_rate].to_dataframe()

    def curve_dataframes(self) -> dict[float, pd.DataFrame]:
        """Return time-history data for every simulated C-rate."""

        return {c_rate: run.to_dataframe() for c_rate, run in sorted(self.runs.items())}
