# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The simple 3D outline of a cell: geometry helper and the cell API (1.4.0)."""

import itertools
import unittest

import numpy as np
import plotly.graph_objects as go

from steer_opencell_design.Constructions.Cells.Base import _Cell
from steer_opencell_design.Utils.Outline import outline_mesh, signed_volume

ORIENTATIONS = ["".join(p) for p in itertools.permutations("xyz")]


def _faces_point_outward(x, y, z, i, j, k, centre) -> bool:
    v = np.stack([x, y, z], axis=1)
    normals = np.cross(v[j] - v[i], v[k] - v[i])
    centroids = (v[i] + v[j] + v[k]) / 3.0 - np.asarray(centre, dtype=float)
    return bool((np.einsum("ij,ij->i", normals, centroids) > 0).all())


class TestOutlineMesh(unittest.TestCase):
    def test_box_counts_and_vertex_order(self):
        x, y, z, i, j, k = outline_mesh("box", (10.0, 20.0, 30.0))
        self.assertEqual(len(x), 8)
        self.assertEqual(len(i), 12)
        # index = bw + 2*bh + 4*bt, with b = 0 at the min side
        for idx in range(8):
            bw, bh, bt = idx & 1, (idx >> 1) & 1, (idx >> 2) & 1
            self.assertEqual(x[idx], 5.0 if bw else -5.0)
            self.assertEqual(y[idx], 10.0 if bh else -10.0)
            self.assertEqual(z[idx], 15.0 if bt else -15.0)

    def test_cylinder_counts_and_vertex_order(self):
        n = 12
        x, y, z, i, j, k = outline_mesh("cylinder", (40.0, 100.0, 40.0), n_sides=n)
        self.assertEqual(len(x), 2 * n + 2)
        self.assertEqual(len(i), 4 * n)
        np.testing.assert_allclose(y[:n], -50.0)
        np.testing.assert_allclose(y[n : 2 * n], 50.0)
        np.testing.assert_allclose([y[2 * n], y[2 * n + 1]], [-50.0, 50.0])
        np.testing.assert_allclose(np.hypot(x[:n], z[:n]), 20.0)
        # ring vertex 0 sits on local +width
        self.assertAlmostEqual(x[0], 20.0)
        self.assertAlmostEqual(z[0], 0.0)

    def test_normals_face_outward_in_every_orientation(self):
        datum = (1.0, -2.0, 3.0)
        for shape, orientation in itertools.product(("box", "cylinder"), ORIENTATIONS):
            with self.subTest(shape=shape, orientation=orientation):
                mesh = outline_mesh(shape, (10.0, 20.0, 30.0 if shape == "box" else 10.0),
                                    datum, orientation, 8)
                self.assertTrue(_faces_point_outward(*mesh, datum))
                self.assertGreater(signed_volume(*mesh), 0.0)

    def test_box_volume_is_exact(self):
        self.assertAlmostEqual(signed_volume(*outline_mesh("box", (10.0, 20.0, 30.0))), 6000.0)

    def test_cylinder_volume_is_the_polygon_prism(self):
        n, r, h = 12, 5.0, 20.0
        polygon_area = 0.5 * n * r * r * np.sin(2 * np.pi / n)
        mesh = outline_mesh("cylinder", (2 * r, h, 2 * r), n_sides=n)
        self.assertAlmostEqual(signed_volume(*mesh), polygon_area * h, places=6)

    def test_orientation_maps_local_axes_onto_world_axes(self):
        x, y, z, *_ = outline_mesh("box", (10.0, 20.0, 30.0), (100.0, 0.0, 0.0), "xzy")
        # width along x, height along z, thickness along y
        self.assertAlmostEqual(np.ptp(x), 10.0)
        self.assertAlmostEqual(np.ptp(z), 20.0)
        self.assertAlmostEqual(np.ptp(y), 30.0)
        self.assertAlmostEqual(float(np.mean(x)), 100.0)

    def test_dtypes(self):
        x, y, z, i, j, k = outline_mesh("cylinder", (1.0, 2.0, 1.0))
        for arr in (x, y, z):
            self.assertEqual(arr.dtype, np.float64)
        for arr in (i, j, k):
            self.assertEqual(arr.dtype, np.int64)

    def test_invalid_arguments(self):
        bad = [
            dict(shape="sphere", dimensions=(1, 1, 1)),
            dict(shape="box", dimensions=(1, 1)),
            dict(shape="box", dimensions=(1, 0, 1)),
            dict(shape="box", dimensions=(1, float("nan"), 1)),
            dict(shape="box", dimensions=(1, 1, 1), orientation="xxy"),
            dict(shape="box", dimensions=(1, 1, 1), orientation="ab"),
            dict(shape="box", dimensions=(1, 1, 1), datum=(0, 0)),
            dict(shape="cylinder", dimensions=(1, 1, 1), n_sides=2),
            dict(shape="cylinder", dimensions=(1, 1, 1), n_sides=4.5),
        ]
        for kwargs in bad:
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                with self.assertRaises(ValueError):
                    outline_mesh(**kwargs)


# One reference cell per form factor (flex-frame has no reference cell).
CELLS = (
    ("LFP Stacked Prismatic Cell", "box"),
    ("NMC811 Stacked Pouch Cell", "box"),
    ("LFP Cylindrical Tabless Cell", "cylinder"),
)


class TestCellOutline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = {
            name: _Cell.from_database(name, table_name="cell_references") for name, _ in CELLS
        }

    def test_outline_dimensions_match_the_form_factor(self):
        prismatic = self.cells["LFP Stacked Prismatic Cell"]
        self.assertEqual(
            prismatic.outline_dimensions, (prismatic.width, prismatic.height, prismatic.length)
        )
        pouch = self.cells["NMC811 Stacked Pouch Cell"]
        self.assertEqual(pouch.outline_dimensions, (pouch.width, pouch.height, pouch.thickness))
        cylinder = self.cells["LFP Cylindrical Tabless Cell"]
        self.assertEqual(
            cylinder.outline_dimensions, (cylinder.diameter, cylinder.height, cylinder.diameter)
        )

    def test_mesh_bounds_equal_the_outline(self):
        for name, shape in CELLS:
            with self.subTest(name=name):
                cell = self.cells[name]
                w, h, t = cell.outline_dimensions
                x, y, z, *_ = cell.get_outline_mesh((0.0, 0.0, 0.0), "xzy", 64)
                self.assertAlmostEqual(np.ptp(x), w, places=6)
                self.assertAlmostEqual(np.ptp(z), h, places=6)
                if shape == "box":
                    self.assertAlmostEqual(np.ptp(y), t, places=6)
                else:  # a 64-gon spans its full diameter on x, nearly on y
                    self.assertAlmostEqual(np.ptp(y), t, delta=t * 0.01)

    def test_prismatic_outline_volume_is_the_cell_volume(self):
        cell = self.cells["LFP Stacked Prismatic Cell"]
        volume_l = signed_volume(*cell.get_outline_mesh()) * 1e-6
        self.assertAlmostEqual(volume_l, cell.volume, places=3)

    def test_mesh_follows_a_dimension_change(self):
        cell = self.cells["LFP Stacked Prismatic Cell"]
        before = np.ptp(cell.get_outline_mesh()[1])
        target = cell.height + 10.0
        low, high = cell.height_range
        if not low <= target <= high:
            self.skipTest("height range too narrow for the check")
        cell.height = target
        self.assertAlmostEqual(np.ptp(cell.get_outline_mesh()[1]), cell.height, places=6)
        self.assertNotAlmostEqual(before, cell.height)

    def test_simple_3d_trace_and_plot(self):
        for name, _ in CELLS:
            with self.subTest(name=name):
                cell = self.cells[name]
                self.assertIsInstance(cell.simple_3d_trace, go.Mesh3d)
                fig = cell.plot_3d_view(title="custom")
                self.assertEqual([t.type for t in fig.data], ["mesh3d"])
                self.assertEqual(fig.layout.scene.aspectmode, "data")
                self.assertEqual(fig.layout.title.text, "custom")

    def test_equality_still_holds(self):
        # DunderMixin compares every property: outline_dimensions is cheap and the
        # *_trace property is excluded, so equality is unchanged.
        from copy import deepcopy

        cell = self.cells["NMC811 Stacked Pouch Cell"]
        self.assertEqual(cell, deepcopy(cell))


if __name__ == "__main__":
    unittest.main()
