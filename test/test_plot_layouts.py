# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Layout invariants for the plot_* APIs surfaced to the Dash apps.

These guard the contract the OpenCell app relies on: layout kwargs never
crash, zoom state survives via uirevision, side views are labelled with the
Y/Z axes they actually show, hover units match the axes, and the spiral
figure stays lean (WebGL lines, no per-point customdata on fills).
"""

import unittest

import plotly.graph_objects as go

from test_cells import _build_tesla_like_nmc_cell


class TestPlotLayoutInvariants(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cell = _build_tesla_like_nmc_cell()
        cls.jellyroll = cls.cell._reference_electrode_assembly
        cls.layup = cls.jellyroll._layup
        cls.cathode = cls.layup._cathode
        cls.anode = cls.layup._anode
        cls.separator = cls.layup._top_separator

    # ── Layout kwargs are collision-safe ─────────────────────────────

    def test_layout_kwargs_do_not_crash(self):
        """Overriding defaulted layout keys used to raise TypeError."""
        plot_calls = [
            self.cell.plot_capacity_curve,
            self.cell.plot_top_down_view,
            self.cell.plot_cross_section,
            self.jellyroll.plot_spiral,
            self.jellyroll.plot_top_down_view,
            self.jellyroll.plot_side_view,
            self.layup.plot_top_down_view,
            self.layup.plot_areal_capacity_curve,
            self.cathode.plot_cross_section,
            self.cathode.plot_top_down_view,
            self.cathode.plot_right_left_view,
            self.separator.plot_top_down_view,
            self.separator.plot_right_left_view,
            self.cathode.current_collector.plot_top_down_view,
        ]
        for plot_call in plot_calls:
            with self.subTest(plot=plot_call.__name__):
                fig = plot_call(paper_bgcolor="black", title="Custom Title")
                self.assertEqual(fig.layout.paper_bgcolor, "black")
                self.assertEqual(fig.layout.title.text, "Custom Title")

    def test_uirevision_set_for_dash_state_preservation(self):
        for fig in (
            self.cell.plot_capacity_curve(),
            self.jellyroll.plot_spiral(),
            self.layup.plot_areal_capacity_curve(),
        ):
            self.assertTrue(fig.layout.uirevision)

    # ── Axis labelling ────────────────────────────────────────────────

    def test_side_views_use_yz_axes(self):
        for fig in (
            self.cathode.plot_right_left_view(),
            self.separator.plot_right_left_view(),
            self.cathode.current_collector.plot_right_left_view(),
        ):
            self.assertEqual(fig.layout.xaxis.title.text, "Y (mm)")
            self.assertEqual(fig.layout.yaxis.title.text, "Z (mm)")

    def test_spiral_has_no_circular_scaleanchor(self):
        fig = self.jellyroll.plot_spiral()
        # Z anchors to X; X must not simultaneously anchor back to Y.
        self.assertEqual(fig.layout.yaxis.scaleanchor, "x")
        self.assertIsNone(fig.layout.xaxis.scaleanchor)

    # ── Titles and units ──────────────────────────────────────────────

    def test_areal_capacity_title_has_formatted_np_ratio(self):
        fig = self.layup.plot_areal_capacity_curve()
        self.assertRegex(
            fig.layout.title.text, r"Areal Capacity Curves \(N/P: \d+\.\d{3}\)"
        )

    def test_capacity_curve_has_title(self):
        fig = self.cell.plot_capacity_curve()
        self.assertIn("Capacity Curves", fig.layout.title.text)

    def test_integrated_capacity_hover_uses_ah(self):
        trace = self.cell.integrated_capacity_area_trace
        self.assertIn("Ah", trace.hovertemplate)
        self.assertNotIn("mAh", trace.hovertemplate)

    def test_analytic_colors_come_from_package_constants(self):
        from steer_opencell_design.Utils.Constants import (
            COLOR_FULL_CELL,
            COLOR_FULL_CELL_FILL,
        )

        self.assertEqual(self.cell.capacity_curve_trace.line.color, COLOR_FULL_CELL)
        self.assertEqual(
            self.cell.integrated_capacity_area_trace.fillcolor, COLOR_FULL_CELL_FILL
        )

    def test_cost_breakdown_unit_is_dollars(self):
        fig = self.cell._encapsulation.plot_cost_breakdown()
        hover_texts = list(fig.data[0].customdata)
        self.assertTrue(any("$" in text for text in hover_texts))
        self.assertFalse(any("currency units" in text for text in hover_texts))

    # ── Spiral figure stays lean ──────────────────────────────────────

    def test_spiral_line_traces_use_webgl(self):
        fig = self.jellyroll.plot_spiral()
        line_traces = [t for t in fig.data if t.fill is None or t.fill == "none"]
        self.assertTrue(line_traces)
        for trace in line_traces:
            self.assertIsInstance(trace, go.Scattergl)

    def test_spiral_fill_traces_skip_hover_and_customdata(self):
        fig = self.jellyroll.plot_spiral()
        fill_traces = [t for t in fig.data if t.fill == "toself"]
        self.assertTrue(fill_traces)
        for trace in fill_traces:
            self.assertEqual(trace.hoverinfo, "skip")
            self.assertIsNone(trace.customdata)

    # ── Flip-based views restore object state ─────────────────────────

    def test_flip_views_restore_state(self):
        datum_before = self.cathode.current_collector.datum
        self.cathode.plot_a_side_view()
        self.cathode.plot_b_side_view()
        self.layup.plot_down_top_view()
        self.assertEqual(self.cathode.current_collector.datum, datum_before)


if __name__ == "__main__":
    unittest.main()
