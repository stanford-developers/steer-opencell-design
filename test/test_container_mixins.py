# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Direct tests for the small shared container mixins.

The mixins centralise logic that used to be duplicated across
``Cylindrical.py``, ``Prismatic.py``, and ``Pouch.py``. We exercise them
through tiny test doubles so a regression here surfaces in this file
rather than in (much larger) integration tests.
"""

import unittest

import numpy as np
import plotly.graph_objects as go
from steer_core.Mixins.Coordinates import CoordinateMixin

from steer_opencell_design.Components.Containers._mixins import (
    BulkFromVolumeMixin,
    ExtrudedFootprintMixin,
    SchematicPlotMixin,
    rectangular_footprint_at_datum,
)


class _FakeMaterial:
    """Minimal stand-in for ``_VolumedMaterialMixin``.

    ``BulkFromVolumeMixin._apply_bulk_from_volume`` writes the converted mass
    via ``self._material.mass = mass_g`` and reads back ``_mass``,
    ``_volume`` and ``_cost`` — those are the only contract points.
    """

    def __init__(self, density_kg_per_m3: float, specific_cost_per_kg: float):
        self._density = density_kg_per_m3
        self._specific_cost = specific_cost_per_kg
        self._mass = 0.0
        self._volume = 0.0
        self._cost = 0.0

    @property
    def mass(self) -> float:
        return self._mass

    @mass.setter
    def mass(self, mass_g: float) -> None:
        # Mirror ``_VolumedMaterialMixin``: input is in grams, internal SI is kg.
        self._mass = mass_g / 1000.0
        self._volume = self._mass / self._density
        self._cost = self._mass * self._specific_cost


class _ExtrudedComponent(ExtrudedFootprintMixin, CoordinateMixin):
    def __init__(self, datum: np.ndarray, thickness: float):
        self._datum = datum
        self._thickness = thickness


class _BulkComponent(BulkFromVolumeMixin):
    def __init__(self, material: _FakeMaterial):
        self._material = material


class _PlotComponent(SchematicPlotMixin):
    pass


class TestExtrudedFootprintMixin(unittest.TestCase):
    def test_extrudes_unit_square_to_two_z_levels(self):
        component = _ExtrudedComponent(
            datum=np.array([0.0, 0.0, 0.0]),
            thickness=1.0,
        )
        footprint = np.array(
            [
                [-0.5, -0.5],
                [+0.5, -0.5],
                [+0.5, +0.5],
                [-0.5, +0.5],
                [-0.5, -0.5],
            ]
        )

        coords = component._extrude_footprint(footprint)

        self.assertIsInstance(coords, np.ndarray)
        self.assertEqual(coords.shape[1], 3)

        finite_z = coords[~np.isnan(coords[:, 2]), 2]
        unique_z = np.unique(np.round(finite_z, 6))
        self.assertEqual(unique_z.size, 2, msg=f"expected 2 z-levels, got {unique_z}")
        self.assertAlmostEqual(unique_z.max() - unique_z.min(), 1.0, places=6)

    def test_extrusion_thickness_scales_z_span(self):
        for thickness in (0.5, 2.0, 10.0):
            component = _ExtrudedComponent(
                datum=np.array([0.0, 0.0, 0.0]),
                thickness=thickness,
            )
            footprint = np.array(
                [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]], dtype=float
            )
            coords = component._extrude_footprint(footprint)
            finite_z = coords[~np.isnan(coords[:, 2]), 2]
            self.assertAlmostEqual(
                finite_z.max() - finite_z.min(),
                thickness,
                places=6,
                msg=f"z-span did not match thickness={thickness}",
            )


class TestBulkFromVolumeMixin(unittest.TestCase):
    def test_writes_mass_volume_cost_consistently(self):
        material = _FakeMaterial(density_kg_per_m3=2700.0, specific_cost_per_kg=5.0)
        component = _BulkComponent(material)

        volume = 1e-3  # 1 L = 1e-3 m^3
        component._apply_bulk_from_volume(volume)

        expected_mass_kg = volume * material._density  # 2.7 kg
        self.assertAlmostEqual(component._mass, expected_mass_kg, places=9)
        self.assertAlmostEqual(component._volume, volume, places=12)
        self.assertAlmostEqual(
            component._cost, expected_mass_kg * material._specific_cost, places=9
        )

    def test_zero_volume_zeros_everything(self):
        material = _FakeMaterial(density_kg_per_m3=1000.0, specific_cost_per_kg=10.0)
        component = _BulkComponent(material)

        component._apply_bulk_from_volume(0.0)

        self.assertEqual(component._mass, 0.0)
        self.assertEqual(component._volume, 0.0)
        self.assertEqual(component._cost, 0.0)


class TestSchematicPlotMixin(unittest.TestCase):
    def test_returns_figure_with_trace_when_provided(self):
        component = _PlotComponent()
        trace = go.Scatter(x=[0, 1], y=[0, 1], name="probe")

        figure = component._layout_schematic(
            trace,
            xaxis={"title": "x"},
            yaxis={"title": "y"},
        )

        self.assertIsInstance(figure, go.Figure)
        self.assertEqual(len(figure.data), 1)
        self.assertEqual(figure.data[0].name, "probe")
        self.assertEqual(figure.layout.xaxis.title.text, "x")
        self.assertEqual(figure.layout.yaxis.title.text, "y")

    def test_returns_empty_figure_when_trace_is_none(self):
        """The Pouch.LaminateSheet path passes ``None`` when no coordinates exist yet."""
        component = _PlotComponent()
        figure = component._layout_schematic(
            None,
            xaxis={"title": "x"},
            yaxis={"title": "y"},
        )
        self.assertIsInstance(figure, go.Figure)
        self.assertEqual(len(figure.data), 0)

    def test_layout_kwargs_default_to_white_background(self):
        component = _PlotComponent()
        figure = component._layout_schematic(
            None,
            xaxis={},
            yaxis={},
        )
        self.assertEqual(figure.layout.paper_bgcolor, "white")
        self.assertEqual(figure.layout.plot_bgcolor, "white")

    def test_caller_can_override_background(self):
        component = _PlotComponent()
        figure = component._layout_schematic(
            None,
            xaxis={},
            yaxis={},
            paper_bgcolor="black",
        )
        self.assertEqual(figure.layout.paper_bgcolor, "black")


class TestRectangularFootprintAtDatum(unittest.TestCase):
    def test_returns_closed_5_point_loop_centred_on_datum(self):
        coords = rectangular_footprint_at_datum(
            width=2.0, length=4.0, datum=(10.0, 20.0, 0.0)
        )

        self.assertEqual(coords.shape, (5, 2))
        np.testing.assert_array_almost_equal(coords[0], coords[-1])

    def test_corners_match_expected_geometry(self):
        coords = rectangular_footprint_at_datum(
            width=2.0, length=4.0, datum=(0.0, 0.0)
        )
        expected = np.array(
            [
                [-1.0, -2.0],
                [+1.0, -2.0],
                [+1.0, +2.0],
                [-1.0, +2.0],
                [-1.0, -2.0],
            ]
        )
        np.testing.assert_array_almost_equal(coords, expected)

    def test_datum_translates_the_rectangle(self):
        base = rectangular_footprint_at_datum(
            width=3.0, length=5.0, datum=(0.0, 0.0)
        )
        shifted = rectangular_footprint_at_datum(
            width=3.0, length=5.0, datum=(7.0, -3.0)
        )
        # Each row of the shifted rectangle must be (base + datum_offset).
        offset = np.array([7.0, -3.0])
        np.testing.assert_array_almost_equal(
            shifted - base, np.tile(offset, (base.shape[0], 1))
        )


if __name__ == "__main__":
    unittest.main()
