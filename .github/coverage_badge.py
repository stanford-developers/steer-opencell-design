"""Render a shields.io endpoint file describing the current test coverage.

Codecov and Coveralls both require a GitHub App to be installed on the
owning organisation, which we cannot arrange for `stanford-developers`.
Instead the docs workflow runs the suite, hands the resulting `coverage.xml`
to this script, and publishes the output alongside the documentation on
GitHub Pages. The README then points shields.io at that public URL, so the
badge stays live without any third-party service holding credentials.

This lives in `.github/` rather than the conventional `scripts/` because
`.gitignore` excludes any directory named `scripts`, at any depth.

Usage:
    python .github/coverage_badge.py coverage.xml docs/coverage.json
"""

from __future__ import annotations

import json
import pathlib
import sys
import xml.etree.ElementTree as ET

# Thresholds mirror the `--cov-fail-under=80` floor set in pyproject.toml:
# anything the CI would reject reads as red, and the band just above the
# floor stays visually distinct from comfortably-covered code.
_BANDS = (
    (90, "brightgreen"),
    (80, "green"),
    (70, "yellow"),
    (0, "red"),
)


def _colour(percent: float) -> str:
    for floor, name in _BANDS:
        if percent >= floor:
            return name
    return "red"


def _read_percent(report: pathlib.Path) -> float | None:
    """Return coverage as a percentage, or None if the report is unusable.

    A failed or interrupted test run can leave no report at all, or one
    without the `line-rate` attribute. That should degrade the badge to
    'unknown' rather than fail the docs deploy.
    """
    if not report.is_file():
        return None
    try:
        line_rate = ET.parse(report).getroot().get("line-rate")
    except ET.ParseError:
        return None
    if line_rate is None:
        return None
    try:
        return float(line_rate) * 100
    except ValueError:
        return None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    report, destination = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    percent = _read_percent(report)

    if percent is None:
        payload = {"schemaVersion": 1, "label": "coverage", "message": "unknown", "color": "lightgrey"}
    else:
        payload = {
            "schemaVersion": 1,
            "label": "coverage",
            "message": f"{percent:.0f}%",
            "color": _colour(percent),
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload) + "\n")
    print(f"{destination}: {payload['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
