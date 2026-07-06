# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Small shared mixins for container components.

The cylindrical and prismatic container families independently grew near-identical
helpers for (a) extruding a 2-D footprint into a 3-D coordinate array,
(b) converting a geometric volume into bulk material/mass/cost via the
component's ``_material``, and (c) wiring a single trace onto a Plotly figure
with the project's standard axis styling.

These mixins centralise that logic so each concrete container class only
owns the *geometry-specific* parts (footprint shape, dimension validation,
tab layout, etc.).

All three mixins are intentionally dependency-light: they only touch public
or well-established semi-private attributes (`_datum`, `_thickness`,
`_material`, `SCHEMATIC_*_AXIS` class attributes, and the
``extrude_footprint`` / ``rotate_coordinates`` helpers from
``steer_core.Mixins.Coordinates``).
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import plotly.graph_objects as go

from steer_core.Constants.Units import KG_TO_G
from steer_core.Mixins.Plotter import PlotterMixin


class ExtrudedFootprintMixin:
    """Provides ``_extrude_footprint`` for components with a 2-D footprint.

    Previously duplicated verbatim in ``Cylindrical.py`` and ``Prismatic.py``.
    Assumes the consumer class mixes in ``steer_core.Mixins.Coordinates``
    (for ``extrude_footprint``) and defines ``_datum`` and ``_thickness``.
    """

    def _extrude_footprint(self, footprint: np.ndarray) -> np.ndarray:
        """Extrude a 2-D ``(N, 2)`` footprint into a 3-D ``(M, 3)`` array.

        The ``z``-axis is taken as the extrusion direction and the component
        ``_thickness`` is used for the extrusion length, with ``_datum`` as
        the in-plane origin.
        """
        x, y, z, _ = self.extrude_footprint(
            footprint[:, 0],
            footprint[:, 1],
            self._datum,
            self._thickness,
        )
        return np.column_stack((x, y, z))


class BulkFromVolumeMixin:
    """Compute bulk mass/volume/cost from a geometric volume.

    Previously duplicated as the tail of ``_calculate_bulk_properties`` in
    ``Cylindrical.py`` and ``Prismatic.py``. The consumer class must own a
    ``_material`` with ``_density``, ``_mass``, ``_volume`` and ``_cost``
    properties (i.e. anything extending ``_VolumedMaterialMixin``).
    """

    def _apply_bulk_from_volume(self, volume: float) -> None:
        """Set ``_mass``, ``_volume`` and ``_cost`` from a geometric volume [m³].

        Internally pushes the mass to ``self._material`` so downstream
        references to the material's properties stay consistent, then reads
        the resulting bulk values back onto ``self``.
        """
        _mass = volume * self._material._density
        mass_g = _mass * KG_TO_G
        self._material.mass = mass_g

        self._mass = self._material._mass
        self._volume = self._material._volume
        self._cost = self._material._cost


class SchematicPlotMixin:
    """Provides ``_layout_schematic`` for view-specific plot helpers.

    Previously duplicated across three view functions per container file.
    The consumer class must define ``SCHEMATIC_X_AXIS``, ``SCHEMATIC_Y_AXIS``
    and ``SCHEMATIC_Z_AXIS`` class attributes (as every container base
    already does).
    """

    def _layout_schematic(
        self,
        trace: Optional[go.Scatter],
        *,
        xaxis: dict,
        yaxis: dict,
        **layout_kwargs: Any,
    ) -> go.Figure:
        """Wrap a single trace in a Plotly figure with the project's layout.

        Parameters
        ----------
        trace
            Plotly trace (e.g. ``self.top_down_trace``). If ``None`` — for
            example when the component has no coordinates yet — an empty
            figure is returned so the UI can render a placeholder.
        xaxis, yaxis
            Axis layout dicts (typically ``self.SCHEMATIC_*_AXIS``).
        **layout_kwargs
            Extra keyword arguments forwarded to ``figure.update_layout``.
            Standard defaults for ``paper_bgcolor`` / ``plot_bgcolor`` are
            applied when not supplied.
        """
        figure = go.Figure()
        if trace is not None:
            figure.add_trace(trace)

        # Called as a static helper so this mixin stays usable without
        # PlotterMixin in the consumer's MRO.
        return PlotterMixin.apply_plot_layout(
            figure,
            defaults={
                "xaxis": xaxis,
                "yaxis": yaxis,
                "paper_bgcolor": "white",
                "plot_bgcolor": "white",
            },
            overrides=layout_kwargs,
        )


def rectangular_footprint_at_datum(
    width: float,
    length: float,
    datum: tuple,
) -> np.ndarray:
    """Return a closed rectangular footprint centred on ``datum``.

    The path is traced clockwise starting at the bottom-left and closes with
    a copy of the starting point (shape ``(5, 2)``). Used by prismatic
    terminal connectors and lid assemblies, which previously inlined this
    identical geometry.

    Parameters
    ----------
    width, length
        Rectangle dimensions in metres (the ``x`` and ``y`` extents).
    datum
        ``(x, y, ...)`` origin; only the first two components are used.
    """
    half_width = width / 2
    half_length = length / 2

    x0, y0 = datum[0], datum[1]

    x_coords = np.array([
        x0 - half_width,
        x0 + half_width,
        x0 + half_width,
        x0 - half_width,
        x0 - half_width,
    ])

    y_coords = np.array([
        y0 - half_length,
        y0 - half_length,
        y0 + half_length,
        y0 + half_length,
        y0 - half_length,
    ])

    return np.column_stack((x_coords, y_coords))
