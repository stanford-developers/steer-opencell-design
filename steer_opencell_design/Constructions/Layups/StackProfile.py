"""The exact layer stack of a laminate along its length.

A wound laminate is a stack of layers (coatings, foils, separators) that each start
and stop at their own position along the strip. Its thickness is piecewise constant
between those positions, and each layer's height within the stack is the sum of the
layers present beneath it (layers drop onto whatever lies below, so the stack never
holds a void).

:func:`build_stack_profile` reads each layer's exact segments, not a sampled grid, so
a coating that starts 189.0 mm along the strip starts there in the winding too.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np

# Two segment ends closer than this (m) are the same breakpoint.
_EDGE_MERGE_TOLERANCE = 1e-12


@dataclass(frozen=True)
class StackProfile:
    """A laminate's stack as piecewise-constant functions of strip position ``s``.

    ``s`` runs from 0 at the first layer's start (``x = x_origin``) to ``length``.
    Interval ``k`` is ``[edges[k], edges[k + 1])``.

    Attributes
    ----------
    edges : (M + 1,) array
        Breakpoints in s (m): every layer segment's start and end.
    thickness : (M,) array
        Total stack thickness (m) on each interval.
    cum_area : (M + 1,) array
        Cumulative thickness-length integral at each edge (m^2), for cell averages.
    names : tuple of str
        Layer names, bottom to top (layers that exist anywhere in the laminate).
    layer_thickness : (C,) array
        Each layer's thickness (m).
    present : (C, M) bool array
        Whether a layer exists on an interval.
    offset : (C, M) array
        Height (m) of a layer's centre above the stack's bottom on each interval;
        NaN where the layer is absent.
    segments : dict
        Layer name -> (k, 2) array of its ``[s_start, s_end]`` segments.
    x_origin : float
        Laminate x (m) at ``s = 0``.
    length : float
        Strip length (m), the last layer's end in s.
    """

    edges: np.ndarray
    thickness: np.ndarray
    cum_area: np.ndarray
    names: Tuple[str, ...]
    layer_thickness: np.ndarray
    present: np.ndarray
    offset: np.ndarray
    segments: Dict[str, np.ndarray] = field(default_factory=dict)
    x_origin: float = 0.0
    length: float = 0.0

    @property
    def max_thickness(self) -> float:
        return float(self.thickness.max()) if self.thickness.size else 0.0

    def interval_at(self, s: np.ndarray, side: str = "right") -> np.ndarray:
        """Interval index containing each ``s`` (clipped to the profile)."""
        index = np.searchsorted(self.edges, s, side=side) - 1
        return np.clip(index, 0, len(self.thickness) - 1)

    def thickness_at(self, s: np.ndarray) -> np.ndarray:
        """Stack thickness (m) at each ``s``; 0 outside the strip."""
        s = np.asarray(s, dtype=float)
        values = self.thickness[self.interval_at(s)]
        outside = (s < self.edges[0]) | (s > self.edges[-1])
        return np.where(outside, 0.0, values)


def _segments_from_center_line(coords: np.ndarray) -> List[Tuple[float, float]]:
    """``[x_start, x_end]`` pairs of a centre line whose segments are NaN-separated."""
    coords = np.asarray(coords, dtype=float)
    if coords.size == 0:
        return []
    xs = coords[:, 0]
    valid = ~np.isnan(xs)
    bounds = np.flatnonzero(np.diff(np.concatenate(([False], valid, [False])).astype(np.int8)))
    if bounds.size == 0:
        return []
    starts = bounds[0::2]
    lows = np.minimum.reduceat(np.where(valid, xs, np.inf), starts)
    highs = np.maximum.reduceat(np.where(valid, xs, -np.inf), starts)
    return [(float(x0), float(x1)) for x0, x1 in zip(lows, highs) if x1 > x0]


def build_stack_profile(
    layer_specs: Sequence[Tuple[str, np.ndarray, float]],
) -> StackProfile:
    """Build a :class:`StackProfile` from ``(name, centre_line, thickness)`` layers.

    ``layer_specs`` lists the layers bottom to top. Each centre line holds the
    layer's segment end points (NaN rows between segments), as the components'
    ``get_*_center_line()`` methods return them.
    """
    names: List[str] = []
    thicknesses: List[float] = []
    raw_segments: List[List[Tuple[float, float]]] = []
    for name, coords, thickness in layer_specs:
        segments = _segments_from_center_line(coords)
        if not segments or thickness is None or thickness <= 0:
            continue
        names.append(name)
        thicknesses.append(float(thickness))
        raw_segments.append(segments)

    if not names:
        empty = np.zeros(0)
        return StackProfile(
            edges=np.zeros(1),
            thickness=empty,
            cum_area=np.zeros(1),
            names=(),
            layer_thickness=empty,
            present=np.zeros((0, 0), dtype=bool),
            offset=np.zeros((0, 0)),
        )

    x_origin = min(x0 for segments in raw_segments for x0, _ in segments)
    ends = np.array(
        sorted(
            {x - x_origin for segments in raw_segments for pair in segments for x in pair}
        )
    )
    keep = np.concatenate(([True], np.diff(ends) > _EDGE_MERGE_TOLERANCE))
    edges = ends[keep]

    mids = 0.5 * (edges[:-1] + edges[1:])
    layer_t = np.array(thicknesses)
    present = np.zeros((len(names), len(mids)), dtype=bool)
    segments_s: Dict[str, np.ndarray] = {}
    for c, segments in enumerate(raw_segments):
        pairs = np.array([(x0 - x_origin, x1 - x_origin) for x0, x1 in segments])
        segments_s[names[c]] = pairs
        for s0, s1 in pairs:
            present[c] |= (mids > s0) & (mids < s1)

    contribution = layer_t[:, None] * present
    below = np.cumsum(contribution, axis=0) - contribution
    offset = np.where(present, below + layer_t[:, None] / 2, np.nan)
    thickness = contribution.sum(axis=0)
    cum_area = np.concatenate(([0.0], np.cumsum(thickness * np.diff(edges))))

    return StackProfile(
        edges=edges,
        thickness=thickness,
        cum_area=cum_area,
        names=tuple(names),
        layer_thickness=layer_t,
        present=present,
        offset=offset,
        segments=segments_s,
        x_origin=float(x_origin),
        length=float(edges[-1]),
    )
