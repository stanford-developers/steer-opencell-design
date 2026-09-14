# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Speed benchmark for the JellyRoll dimension setters.

Times the three Brent-driven setters that drive a layup-length search to a
target outer dimension:

* ``WoundJellyRoll.radius``       (round cell)
* ``FlatWoundJellyRoll.thickness`` (prismatic / pouch)
* ``FlatWoundJellyRoll.width``    (prismatic / pouch)

Each setter call iterates Brent's method on the layup length and calls the
underlying spiral / racetrack kernel multiple times per iteration (see
``[ElectrodeAssemblies/JellyRolls.py]``). The harness runs each setter on a
fresh ``deepcopy`` of the same baseline assembly so each timed call sees an
identical starting point.

Run with::

    python -m test.perf.bench_jellyroll_setters
    python -m test.perf.bench_jellyroll_setters --update-baseline
    python -m test.perf.bench_jellyroll_setters --profile

Output schema is the same as ``bench_spiral_utils``::

    case,fn,mean_ms,p50_ms,p95_ms,min_ms,n_iters,delta_vs_baseline_pct

``n_iters`` is the number of Brent iterations the converged setter took
(captured via a wrapper around ``scipy.optimize.brentq``). It can be 0 when
the bench couldn't observe the iteration count (e.g. setter raised).

The bench is **not** picked up by pytest (filename starts with ``bench_``).
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
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

os.environ.setdefault("OPENCELL_ENV", "development")

# Reuse the laminate fixtures from the SpiralUtils bench.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bench_spiral_utils import BenchCase, _build_cases  # noqa: E402

from steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls import (  # noqa: E402
    FlatWoundJellyRoll,
    WoundJellyRoll,
)
from steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment import (  # noqa: E402
    FlatMandrel,
    RoundMandrel,
)

BASELINE_PATH = os.path.join(os.path.dirname(__file__), "BASELINE_SETTERS.json")
WARMUP_RUNS = 1
# Setters are ~100x slower than a single spiral, so keep the timed-run count
# small. p95 over 5 samples is noisy but the means are stable to ~5%.
TIMED_RUNS = 5


@dataclass
class SetterCase:
    """A single (assembly_template, setter_attr, target) tuple to time."""

    case_name: str
    assembly_kind: str  # "wound" or "flat"
    setter_attr: str  # "radius" / "thickness" / "width"
    target: float  # mm
    factory: Callable[[], Any]


def _build_wound(case: BenchCase) -> WoundJellyRoll:
    """Build a WoundJellyRoll around a deepcopy of the case's laminate."""
    mandrel = RoundMandrel(
        # diameter in mm
        diameter=case.round_mandrel_radius_m * 2 * 1000,
        length=300,
    )
    return WoundJellyRoll(laminate=deepcopy(case.laminate), mandrel=mandrel)


def _build_flat(case: BenchCase) -> FlatWoundJellyRoll:
    """Build a FlatWoundJellyRoll around a deepcopy of the case's laminate."""
    # FlatMandrel takes height (= 2 * semicircle radius) and width (= height +
    # straight section).
    height_mm = case.flat_mandrel_radius_m * 2 * 1000
    width_mm = height_mm + case.flat_straight_length_m * 1000
    mandrel = FlatMandrel(length=300, width=width_mm, height=height_mm)
    return FlatWoundJellyRoll(laminate=deepcopy(case.laminate), mandrel=mandrel)


def _pick_target(current: float, range_min: float, range_max: float) -> float:
    """Pick a Brent target inside ``(range_min, range_max)`` away from current.

    Moves halfway from ``current`` toward whichever end of the range has more
    headroom. This keeps the bracket non-trivial (so Brent actually iterates)
    while never falling outside the achievable bounds (which would raise
    ``ValueError: f(a) and f(b) must have different signs``).
    """
    headroom_up = range_max - current
    headroom_down = current - range_min
    if headroom_up >= headroom_down:
        return current + 0.5 * headroom_up
    return current - 0.5 * headroom_down


def _build_setter_cases(cases: List[BenchCase]) -> List[SetterCase]:
    """For each laminate case, build one wound + two flat setter targets."""
    out: List[SetterCase] = []
    for case in cases:
        wound = _build_wound(case)
        wound_target = _pick_target(wound.radius, *wound.radius_range)
        out.append(
            SetterCase(
                case_name=case.name,
                assembly_kind="wound",
                setter_attr="radius",
                target=wound_target,
                factory=lambda c=case: _build_wound(c),
            )
        )

        flat = _build_flat(case)
        thickness_target = _pick_target(flat.thickness, *flat.thickness_range)
        width_target = _pick_target(flat.width, *flat.width_range)
        out.append(
            SetterCase(
                case_name=case.name,
                assembly_kind="flat",
                setter_attr="thickness",
                target=thickness_target,
                factory=lambda c=case: _build_flat(c),
            )
        )
        out.append(
            SetterCase(
                case_name=case.name,
                assembly_kind="flat",
                setter_attr="width",
                target=width_target,
                factory=lambda c=case: _build_flat(c),
            )
        )
    return out


# ─── Brent iteration probe ───────────────────────────────────────────────────
#
# ``brentq`` is imported into the JellyRolls module namespace, so patching the
# name there lets us observe iteration / function-call counts without touching
# production code. The probe re-runs brentq with ``full_output=True``.
_BRENT_STATS: Dict[str, int] = {"iterations": 0, "function_calls": 0}


def _install_brentq_probe() -> None:
    import steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls as _jr

    orig = _jr.brentq

    def counted_brentq(f, a, b, *args, **kwargs):
        kwargs.pop("full_output", None)
        root, r = orig(f, a, b, *args, full_output=True, **kwargs)
        _BRENT_STATS["iterations"] = int(r.iterations)
        _BRENT_STATS["function_calls"] = int(r.function_calls)
        return root

    _jr.brentq = counted_brentq


def _time_setter(setter_case: SetterCase) -> Dict[str, float]:
    """Run ``WARMUP_RUNS + TIMED_RUNS`` setter calls and return summary."""
    for _ in range(WARMUP_RUNS):
        jr = setter_case.factory()
        setattr(jr, setter_case.setter_attr, setter_case.target)

    timings_ms: List[float] = []
    n_obj_calls = 0
    for _ in range(TIMED_RUNS):
        jr = setter_case.factory()
        t0 = time.perf_counter()
        setattr(jr, setter_case.setter_attr, setter_case.target)
        timings_ms.append((time.perf_counter() - t0) * 1000.0)
        n_obj_calls = _BRENT_STATS["function_calls"]

    sorted_ms = sorted(timings_ms)
    return {
        "mean_ms": statistics.fmean(sorted_ms),
        "p50_ms": sorted_ms[len(sorted_ms) // 2],
        "p95_ms": sorted_ms[max(0, int(round(0.95 * (len(sorted_ms) - 1))))],
        "min_ms": sorted_ms[0],
        "n_obj_calls": n_obj_calls,
    }


def _run_all(cases: List[BenchCase]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Time every (case, setter) combination. Return nested dict keyed by case."""
    results: Dict[str, Dict[str, Dict[str, float]]] = {}
    for setter_case in _build_setter_cases(cases):
        case_bucket = results.setdefault(setter_case.case_name, {})
        fn_key = f"{setter_case.assembly_kind}.{setter_case.setter_attr}"
        case_bucket[fn_key] = _time_setter(setter_case)
    return results


# Stage names → (funcname, filename substring) used to slice the cProfile
# output into a per-stage cost table. cumtime for nested stages overlaps by
# design — the table is for attribution, not for summing.
_STAGE_MARKERS: List[Tuple[str, str, str]] = [
    ("objective_function (per-iter total)", "objective_function", "JellyRolls"),
    ("laminate length setter cascade", "length", "Laminate"),
    ("position_layup_on_mandrel", "position_layup_on_mandrel", "JellyRolls"),
    ("calculate_flattened_center_lines", "calculate_flattened_center_lines", "Laminate"),
    ("spiral kernel (round)", "calculate_variable_thickness_spiral", "SpiralUtils"),
    ("racetrack kernel (flat)", "calculate_variable_thickness_racetrack", "SpiralUtils"),
    ("build_component_spirals", "build_component_spirals", "SpiralUtils"),
    ("build_component_racetracks", "build_component_racetracks", "SpiralUtils"),
    ("extrusion (round)", "build_extruded_component_spirals", "SpiralUtils"),
    ("extrusion (flat)", "build_extruded_component_racetracks", "SpiralUtils"),
    ("_insert_segment_gaps", "_insert_segment_gaps", "SpiralUtils"),
    ("rotation optimizer (flat)", "rotate_spiral_to_minimize_thickness", "SpiralUtils"),
    ("rotation objective evals", "compute_thickness_at_angle", "SpiralUtils"),
    ("get_radius_of_points (shapely)", "get_radius_of_points", "Coordinates"),
    ("_set_main_dimensions_for_objective", "_set_main_dimensions_for_objective", "JellyRolls"),
    ("_center_spirals", "_center_spirals", "JellyRolls"),
    ("pressed racetrack (flat)", "_calculate_pressed_racetrack", "JellyRolls"),
    ("tail: _calculate_all_properties", "_calculate_all_properties", "JellyRolls"),
    ("tail: _calculate_roll_properties", "_calculate_roll_properties", "JellyRolls"),
    ("tail: _calculate_spiral_properties", "_calculate_spiral_properties", "JellyRolls"),
    ("tail: top-down coords", "_calculate_top_down_coordinates", "JellyRolls"),
    ("tail: right-left coords", "_calculate_right_left_coordinates", "JellyRolls"),
    ("tail: interfacial area", "_calculate_interfacial_area", "JellyRolls"),
    ("tail: bulk properties", "_calculate_bulk_properties", "JellyRolls"),
    ("brentq", "counted_brentq", "bench_jellyroll_setters"),
]


def _stage_table(ps: pstats.Stats, total_s: float) -> str:
    """Render the targeted per-stage attribution table from pstats data."""
    rows = []
    for label, funcname, file_sub in _STAGE_MARKERS:
        agg_ncalls = 0
        agg_cum = 0.0
        agg_tot = 0.0
        for (fn, _lineno, name), (
            cc,
            nc,
            tt,
            ct,
            _callers,
        ) in ps.stats.items():  # type: ignore[attr-defined]
            if name == funcname and file_sub in fn:
                agg_ncalls += nc
                agg_cum += ct
                agg_tot += tt
        if agg_ncalls > 0:
            rows.append((label, agg_ncalls, agg_tot, agg_cum))

    rows.sort(key=lambda r: -r[3])
    lines = [
        f"{'stage':<42}{'ncalls':>8}{'tottime_ms':>12}{'cumtime_ms':>12}{'cum_%':>7}"
    ]
    for label, nc, tt, ct in rows:
        pct = 100.0 * ct / total_s if total_s > 0 else 0.0
        lines.append(f"{label:<42}{nc:>8}{tt * 1e3:>12.1f}{ct * 1e3:>12.1f}{pct:>6.1f}%")
    return "\n".join(lines)


def _profile_setter(setter_case: SetterCase) -> str:
    """cProfile a single setter call; return top-30 + per-stage tables."""
    jr = setter_case.factory()
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    setattr(jr, setter_case.setter_attr, setter_case.target)
    pr.disable()
    total_s = time.perf_counter() - t0

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumulative")
    ps.print_stats(30)

    header = (
        f"\n## {setter_case.case_name} {setter_case.assembly_kind}."
        f"{setter_case.setter_attr} -> {setter_case.target:.2f} mm "
        f"(wall {total_s * 1e3:.1f} ms, brent function_calls="
        f"{_BRENT_STATS['function_calls']}, iterations="
        f"{_BRENT_STATS['iterations']})\n"
    )
    return (
        header
        + "\n### Per-stage attribution (cumtime overlaps across nesting):\n"
        + _stage_table(ps, total_s)
        + "\n\n### Top 30 by cumulative time:\n"
        + s.getvalue()
    )


def _profile_all(cases: List[BenchCase], case_name: str) -> str:
    """Profile all three setters for the named case."""
    matching = [c for c in cases if c.name == case_name]
    if not matching:
        raise ValueError(f"No case named {case_name!r}")
    out = []
    for setter_case in _build_setter_cases(matching):
        # Warm one call so numba compilation / caches don't pollute the profile.
        warm = setter_case.factory()
        setattr(warm, setter_case.setter_attr, setter_case.target)
        out.append(_profile_setter(setter_case))
    return "\n".join(out)


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
        help="Overwrite BASELINE_SETTERS.json with the current run.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Dump cProfiles of all three setters (skips the timing sweep).",
    )
    parser.add_argument(
        "--profile-case",
        default="medium",
        choices=["small", "medium", "large"],
        help="Which laminate case to profile (default: medium).",
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

    _install_brentq_probe()

    if args.profile:
        print(f"\n# cProfile of all setters ({args.profile_case} case):")
        print(_profile_all(cases, args.profile_case))
        return 0

    baseline = _load_baseline()
    print("\ncase,fn,mean_ms,p50_ms,p95_ms,min_ms,n_obj_calls,delta_vs_baseline_pct")

    all_results = _run_all(cases)
    for case_name, by_fn in all_results.items():
        for fn_name, summary in by_fn.items():
            base = baseline.get(case_name, {}).get(fn_name)
            if base is not None and base.get("mean_ms"):
                delta = (summary["mean_ms"] - base["mean_ms"]) / base["mean_ms"] * 100.0
                delta_str = f"{delta:+.1f}"
            else:
                delta_str = "n/a"
            print(
                f"{case_name},{fn_name},"
                f"{summary['mean_ms']:.1f},"
                f"{summary['p50_ms']:.1f},"
                f"{summary['p95_ms']:.1f},"
                f"{summary['min_ms']:.1f},"
                f"{summary.get('n_obj_calls', 0)},"
                f"{delta_str}"
            )

    if args.update_baseline:
        _save_baseline(all_results)
        print(f"\n# Wrote baseline to {BASELINE_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
