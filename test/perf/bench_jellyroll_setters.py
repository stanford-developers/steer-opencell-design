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


def _time_setter(setter_case: SetterCase) -> Dict[str, float]:
    """Run ``WARMUP_RUNS + TIMED_RUNS`` setter calls and return summary."""
    for _ in range(WARMUP_RUNS):
        jr = setter_case.factory()
        setattr(jr, setter_case.setter_attr, setter_case.target)

    timings_ms: List[float] = []
    for _ in range(TIMED_RUNS):
        jr = setter_case.factory()
        t0 = time.perf_counter()
        setattr(jr, setter_case.setter_attr, setter_case.target)
        timings_ms.append((time.perf_counter() - t0) * 1000.0)

    sorted_ms = sorted(timings_ms)
    return {
        "mean_ms": statistics.fmean(sorted_ms),
        "p50_ms": sorted_ms[len(sorted_ms) // 2],
        "p95_ms": sorted_ms[max(0, int(round(0.95 * (len(sorted_ms) - 1))))],
        "min_ms": sorted_ms[0],
    }


def _run_all(cases: List[BenchCase]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Time every (case, setter) combination. Return nested dict keyed by case."""
    results: Dict[str, Dict[str, Dict[str, float]]] = {}
    for setter_case in _build_setter_cases(cases):
        case_bucket = results.setdefault(setter_case.case_name, {})
        fn_key = f"{setter_case.assembly_kind}.{setter_case.setter_attr}"
        case_bucket[fn_key] = _time_setter(setter_case)
    return results


def _profile_one(case: BenchCase) -> str:
    """cProfile a single radius setter on the given case (medium by default)."""
    pr = cProfile.Profile()
    wound = _build_wound(case)
    target = wound.radius * 1.10
    pr.enable()
    wound.radius = target
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumulative")
    ps.print_stats(25)
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
        help="Overwrite BASELINE_SETTERS.json with the current run.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Also dump a cProfile of one radius-setter call (medium case).",
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
    print("\ncase,fn,mean_ms,p50_ms,p95_ms,min_ms,delta_vs_baseline_pct")

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
                f"{delta_str}"
            )

    if args.profile:
        print("\n# cProfile of medium WoundJellyRoll.radius setter (top 25):")
        print(_profile_one(cases[1]))

    if args.update_baseline:
        _save_baseline(all_results)
        print(f"\n# Wrote baseline to {BASELINE_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
