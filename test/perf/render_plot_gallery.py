# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Render every user-facing plot_* figure to HTML for visual QA.

Builds the regression cylindrical cell used by the test suite and writes one
HTML file per figure into ``plot_gallery/`` (gitignored), plus an ``index.html``
linking them all. Run from the repository root:

    python test/perf/render_plot_gallery.py

Requires the local development database (same requirement as the test suite).
"""

import os
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "test"))
os.environ.setdefault("OPENCELL_ENV", "development")

OUTPUT_DIR = REPO_ROOT / "plot_gallery"


def build_figures():
    """Return an ordered {slug: figure factory} mapping covering the plot APIs."""
    from test_cells import _build_tesla_like_nmc_cell

    cell = _build_tesla_like_nmc_cell()
    jellyroll = cell._reference_electrode_assembly
    layup = jellyroll._layup
    cathode = layup._cathode
    anode = layup._anode
    separator = layup._top_separator
    collector = cathode.current_collector
    encapsulation = cell._encapsulation

    return {
        # Cell level
        "cell_capacity_curve": cell.plot_capacity_curve,
        "cell_mass_breakdown": cell.plot_mass_breakdown,
        "cell_cost_breakdown": cell.plot_cost_breakdown,
        "cell_top_down_view": cell.plot_top_down_view,
        "cell_cross_section": cell.plot_cross_section,
        # Jelly roll
        "jellyroll_spiral": jellyroll.plot_spiral,
        "jellyroll_top_down_view": jellyroll.plot_top_down_view,
        "jellyroll_side_view": jellyroll.plot_side_view,
        "jellyroll_capacity_curve": jellyroll.plot_capacity_curve,
        # Layup
        "layup_top_down_view": layup.plot_top_down_view,
        "layup_down_top_view": layup.plot_down_top_view,
        "layup_areal_capacity_curve": layup.plot_areal_capacity_curve,
        # Electrodes
        "cathode_cross_section": cathode.plot_cross_section,
        "cathode_top_down_view": cathode.plot_top_down_view,
        "cathode_a_side_view": cathode.plot_a_side_view,
        "cathode_b_side_view": cathode.plot_b_side_view,
        "cathode_right_left_view": cathode.plot_right_left_view,
        "cathode_areal_capacity_curve": cathode.plot_areal_capacity_curve,
        "cathode_mass_breakdown": cathode.plot_mass_breakdown,
        "anode_cross_section": anode.plot_cross_section,
        # Formulation / material curves
        "cathode_formulation_curve": lambda: cathode.formulation.plot_specific_capacity_curve(
            add_materials=True
        ),
        # Current collector
        "collector_top_down_view": collector.plot_top_down_view,
        "collector_right_left_view": collector.plot_right_left_view,
        # Separator
        "separator_top_down_view": separator.plot_top_down_view,
        "separator_right_left_view": separator.plot_right_left_view,
        "separator_bottom_up_view": separator.plot_bottom_up_view,
        # Encapsulation
        "encapsulation_side_view": encapsulation.plot_side_view,
        "encapsulation_mass_breakdown": encapsulation.plot_mass_breakdown,
        "encapsulation_cost_breakdown": encapsulation.plot_cost_breakdown,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    figures = build_figures()

    rendered, failed = [], []
    for slug, factory in figures.items():
        try:
            fig = factory()
            if fig is None:
                raise ValueError("plot method returned None")
            fig.write_html(
                OUTPUT_DIR / f"{slug}.html",
                include_plotlyjs="cdn",
                full_html=True,
            )
            rendered.append(slug)
            print(f"  ok      {slug}")
        except Exception:
            failed.append(slug)
            print(f"  FAILED  {slug}")
            traceback.print_exc()

    links = "\n".join(
        f'<li><a href="{slug}.html" target="_blank">{slug}</a></li>'
        for slug in rendered
    )
    (OUTPUT_DIR / "index.html").write_text(
        "<html><body><h1>steer-opencell-design plot gallery</h1>"
        f"<ul>{links}</ul></body></html>"
    )

    print(f"\nRendered {len(rendered)} figures to {OUTPUT_DIR}/ "
          f"({len(failed)} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
