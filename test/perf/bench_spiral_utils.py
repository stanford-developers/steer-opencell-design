# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Speed benchmark for the variable-thickness spiral and racetrack kernels.

Run with:

    python -m test.perf.bench_spiral_utils

Optionally:

    python -m test.perf.bench_spiral_utils --update-baseline
    python -m test.perf.bench_spiral_utils --profile

The harness builds three representative laminates (small / medium / large),
times :func:`SpiralCalculator.calculate_variable_thickness_spiral` and
:func:`SpiralCalculator.calculate_variable_thickness_racetrack` over ``N``
warm runs, and prints a CSV row per case::

    case,fn,mean_ms,p50_ms,p95_ms,n_points

If ``BASELINE.json`` exists next to this file, the harness also prints the
percent delta vs. baseline. Pass ``--update-baseline`` to overwrite it with
the current run.

This file is **not** picked up by ``pytest`` (collected files must start
with ``test_``).
"""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import os
import pstats
import statistics
import sys
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import numpy as np

# Required so conftest's API caching is not used here (we don't import pytest).
os.environ.setdefault("OPENCELL_ENV", "production")

from steer_opencell_design.Components.CurrentCollectors.Notched import (
    NotchedCurrentCollector,
)
from steer_opencell_design.Components.Electrodes import Anode, Cathode
from steer_opencell_design.Components.Separators import Separator
from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import (
    FlatWoundJellyRoll,
    WoundJellyRoll,
)
from steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils import (
    SpiralCalculator,
)
from steer_opencell_design.Constructions.ElectrodeAssemblies.Tape import Tape
from steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment import (
    FlatMandrel,
    RoundMandrel,
)
from steer_opencell_design.Constructions.Layups.Laminate import Laminate
from steer_opencell_design.Materials.ActiveMaterials import (
    AnodeMaterial,
    CathodeMaterial,
)
from steer_opencell_design.Materials.Binders import Binder
from steer_opencell_design.Materials.ConductiveAdditives import ConductiveAdditive
from steer_opencell_design.Materials.Formulations import (
    AnodeFormulation,
    CathodeFormulation,
)
from steer_opencell_design.Materials.Other import (
    CurrentCollectorMaterial,
    InsulationMaterial,
    SeparatorMaterial,
    TapeMaterial,
)

BASELINE_PATH = os.path.join(os.path.dirname(__file__), "BASELINE.json")
WARMUP_RUNS = 1
TIMED_RUNS = 12


@dataclass
class BenchCase:
    name: str
    laminate: Laminate
    round_mandrel_radius_m: float  # for spiral
    flat_mandrel_radius_m: float  # for racetrack
    flat_straight_length_m: float


def _build_layup(collector_length_mm: float, collector_width_mm: float) -> Laminate:
    """Build a positioned + flattened laminate for benchmarking.

    The collector lengths drive the total laminate length, which is what
    governs how many spiral turns the integrator has to step through.
    """
    additive = ConductiveAdditive(
        name="super_P", specific_cost=15, density=2.0, color="#000000"
    )
    binder = Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

    cathode_mat = CathodeMaterial.from_database("LFP")
    cathode_mat.specific_cost = 6
    cathode_mat.density = 3.6
    cathode_formulation = CathodeFormulation(
        active_materials={cathode_mat: 95},
        binders={binder: 2},
        conductive_additives={additive: 3},
    )
    cc_mat = CurrentCollectorMaterial(
        name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
    )
    cathode_cc = NotchedCurrentCollector(
        material=cc_mat,
        length=collector_length_mm,
        width=collector_width_mm,
        thickness=8,
        tab_width=60,
        tab_spacing=200,
        tab_height=18,
        insulation_width=6,
        coated_tab_height=2,
    )
    insulation = InsulationMaterial.from_database("Aluminium Oxide, 99.5%")
    cathode = Cathode(
        formulation=cathode_formulation,
        mass_loading=12,
        current_collector=cathode_cc,
        calender_density=2.6,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    anode_mat = AnodeMaterial.from_database("Synthetic Graphite")
    anode_mat.specific_cost = 4
    anode_mat.density = 2.2
    anode_formulation = AnodeFormulation(
        active_materials={anode_mat: 90},
        binders={binder: 5},
        conductive_additives={additive: 5},
    )
    anode_cc = NotchedCurrentCollector(
        material=cc_mat,
        length=collector_length_mm,
        width=collector_width_mm + 6,
        thickness=8,
        tab_width=60,
        tab_spacing=100,
        tab_height=18,
        insulation_width=6,
        coated_tab_height=2,
    )
    anode = Anode(
        formulation=anode_formulation,
        mass_loading=7.2,
        current_collector=anode_cc,
        calender_density=1.1,
        insulation_material=insulation,
        insulation_thickness=10,
    )

    sep_mat = SeparatorMaterial(
        name="Polyethylene",
        specific_cost=2,
        density=0.94,
        color="#FDFDB7",
        porosity=45,
    )
    top_separator = Separator(
        material=sep_mat,
        thickness=25,
        width=collector_width_mm + 10,
        length=collector_length_mm + 500,
    )
    bottom_separator = Separator(
        material=sep_mat,
        thickness=25,
        width=collector_width_mm + 10,
        length=collector_length_mm + 2500,
    )

    layup = Laminate(
        anode=anode,
        cathode=cathode,
        top_separator=top_separator,
        bottom_separator=bottom_separator,
    )
    layup.calculate_flattened_center_lines()
    return layup


def _build_cases() -> List[BenchCase]:
    """Three representative cases of growing total length."""
    cases: List[BenchCase] = []

    # Small: ~3 m total length, 18650-ish geometry.
    small_layup = _build_layup(collector_length_mm=2500, collector_width_mm=60)
    cases.append(
        BenchCase(
            name="small",
            laminate=small_layup,
            round_mandrel_radius_m=0.0015,  # 1.5 mm radius mandrel
            flat_mandrel_radius_m=0.0025,  # 2.5 mm semicircle radius
            flat_straight_length_m=0.010,  # 10 mm straight section
        )
    )

    # Medium: ~5 m, 21700-ish.
    medium_layup = _build_layup(collector_length_mm=4500, collector_width_mm=300)
    cases.append(
        BenchCase(
            name="medium",
            laminate=medium_layup,
            round_mandrel_radius_m=0.0025,
            flat_mandrel_radius_m=0.0035,
            flat_straight_length_m=0.030,
        )
    )

    # Large: ~12 m, prismatic.
    large_layup = _build_layup(collector_length_mm=12000, collector_width_mm=300)
    cases.append(
        BenchCase(
            name="large",
            laminate=large_layup,
            round_mandrel_radius_m=0.003,
            flat_mandrel_radius_m=0.004,
            flat_straight_length_m=0.050,
        )
    )

    return cases


def _time_call(fn: Callable[[], np.ndarray]) -> Tuple[List[float], int]:
    """Run ``fn`` ``WARMUP_RUNS + TIMED_RUNS`` times. Return (timings_ms, n_points)."""
    for _ in range(WARMUP_RUNS):
        out = fn()
    timings_ms: List[float] = []
    for _ in range(TIMED_RUNS):
        t0 = time.perf_counter()
        out = fn()
        timings_ms.append((time.perf_counter() - t0) * 1000.0)
    return timings_ms, int(out.shape[0])


def _summary(timings_ms: List[float]) -> Dict[str, float]:
    sorted_ms = sorted(timings_ms)
    return {
        "mean_ms": statistics.fmean(sorted_ms),
        "p50_ms": sorted_ms[len(sorted_ms) // 2],
        "p95_ms": sorted_ms[max(0, int(round(0.95 * (len(sorted_ms) - 1))))],
        "min_ms": sorted_ms[0],
    }


def _run_one(case: BenchCase) -> Dict[str, Dict[str, float]]:
    """Time spiral + racetrack for a single case.

    Each kernel is timed at two angular resolutions:
    - default ``dtheta=0.5`` (used during the radius-range bracketing in
      ``JellyRolls._calculate_radius_range``);
    - high-res ``dtheta=0.1`` (the ``_get_high_resolution_params`` value
      that the final winding pipeline actually uses).
    """
    results: Dict[str, Dict[str, float]] = {}

    # Pre-deepcopy so we don't time the deepcopy itself.
    lam = deepcopy(case.laminate)

    spiral_fn = lambda: SpiralCalculator.calculate_variable_thickness_spiral(
        laminate=lam,
        start_radius=case.round_mandrel_radius_m,
    )
    timings, n_pts = _time_call(spiral_fn)
    results["spiral"] = {**_summary(timings), "n_points": n_pts}

    spiral_hires_fn = lambda: SpiralCalculator.calculate_variable_thickness_spiral(
        laminate=lam,
        start_radius=case.round_mandrel_radius_m,
        dtheta=0.1,
    )
    timings, n_pts = _time_call(spiral_hires_fn)
    results["spiral_hires"] = {**_summary(timings), "n_points": n_pts}

    racetrack_fn = lambda: SpiralCalculator.calculate_variable_thickness_racetrack(
        laminate=lam,
        mandrel_radius=case.flat_mandrel_radius_m,
        straight_length=case.flat_straight_length_m,
    )
    timings, n_pts = _time_call(racetrack_fn)
    results["racetrack"] = {**_summary(timings), "n_points": n_pts}

    racetrack_hires_fn = lambda: SpiralCalculator.calculate_variable_thickness_racetrack(
        laminate=lam,
        mandrel_radius=case.flat_mandrel_radius_m,
        straight_length=case.flat_straight_length_m,
        ds_target=1e-4,
    )
    timings, n_pts = _time_call(racetrack_hires_fn)
    results["racetrack_hires"] = {**_summary(timings), "n_points": n_pts}

    return results


def _profile_one(case: BenchCase) -> str:
    """Return a short cProfile dump for one spiral + one racetrack call."""
    pr = cProfile.Profile()
    pr.enable()
    SpiralCalculator.calculate_variable_thickness_spiral(
        laminate=deepcopy(case.laminate),
        start_radius=case.round_mandrel_radius_m,
    )
    SpiralCalculator.calculate_variable_thickness_racetrack(
        laminate=deepcopy(case.laminate),
        mandrel_radius=case.flat_mandrel_radius_m,
        straight_length=case.flat_straight_length_m,
    )
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumulative")
    ps.print_stats(20)
    return s.getvalue()


def _load_baseline() -> Dict[str, Dict[str, Dict[str, float]]]:
    if not os.path.exists(BASELINE_PATH):
        return {}
    with open(BASELINE_PATH) as f:
        return json.load(f)


def _save_baseline(results: Dict[str, Dict[str, Dict[str, float]]]) -> None:
    with open(BASELINE_PATH, "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite BASELINE.json with the current run.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Also dump a cProfile of the medium case.",
    )
    args = parser.parse_args(argv)

    print("# Building cases...", flush=True)
    cases = _build_cases()
    for c in cases:
        print(
            f"#   {c.name}: total_length={c.laminate._total_length:.4f} m, "
            f"top_surface_pts={c.laminate._top_surface.shape[0]}",
            flush=True,
        )

    baseline = _load_baseline()
    print("\ncase,fn,mean_ms,p50_ms,p95_ms,min_ms,n_points,delta_vs_baseline_pct")

    all_results: Dict[str, Dict[str, Dict[str, float]]] = {}
    for case in cases:
        case_res = _run_one(case)
        all_results[case.name] = case_res
        for fn_name, summary in case_res.items():
            base = baseline.get(case.name, {}).get(fn_name)
            if base is not None and base.get("mean_ms"):
                delta = (
                    (summary["mean_ms"] - base["mean_ms"]) / base["mean_ms"] * 100.0
                )
                delta_str = f"{delta:+.1f}"
            else:
                delta_str = "n/a"
            print(
                f"{case.name},{fn_name},"
                f"{summary['mean_ms']:.2f},"
                f"{summary['p50_ms']:.2f},"
                f"{summary['p95_ms']:.2f},"
                f"{summary['min_ms']:.2f},"
                f"{summary['n_points']},"
                f"{delta_str}"
            )

    if args.profile:
        print("\n# cProfile of medium case (cumulative time, top 20):")
        print(_profile_one(cases[1]))

    if args.update_baseline:
        _save_baseline(all_results)
        print(f"\n# Wrote baseline to {BASELINE_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
