"""Wind a laminate turn on turn around a mandrel.

A wound strip packs onto itself: each turn's bottom face sits on the top face of
the turn beneath it, so the strip at a given angle is offset from the mandrel by
everything wound underneath at that angle. The old kernels instead pitched each
point by the thickness of the strip being laid (dr/dθ = t(s)/2π), which opened a
gap of Δt one turn after every thickness step up (where the electrodes start, where
a skip coat ends) and an overlap of Δt after every step down (where the electrodes
end, so the separator tail was drawn through the last electrode turn).

The winding here is a lagged recurrence on a *template*: P sample points per turn
that are the same every turn (a circle for a round mandrel, a racetrack for a
pressed flat one), each with its outward normal. Offset curves of a circle or a
racetrack share their normals, so the strip at sample ``i`` is exactly
``template[i % P] + a[i] * normal[i % P]``, and the material beneath it is sample
``i - P``. Then

* the first turn rests on the mandrel (``a = 0``);
* afterwards the support under sample ``m`` is ``a[m - P]`` plus the strip's
  thickness there;
* the strip bridges a step in its support with a short straight ramp (rise 1 over
  a run of :data:`RAMP_RUN_PER_RISE`), as a strip under winding tension does,
  leaving a small wedge void instead of a full-height gap;
* arc length advances along the strip's mid-plane, and the strip ends exactly at
  its length.

Thickness is a piecewise-constant function of arc length (:class:`StackProfile`),
averaged over each sample's arc, so every step lands where the layer actually
starts or stops. A tape, when present, is wound in the same pass as the strip's
outermost continuation, and the laminate's samples are identical with or without
it (the recurrence only ever looks one turn back).

Everything a jelly roll measures comes from the outer envelope (the last turn's
outer face), which both the full rebuild and the dimension setters' lightweight
objective read, so the two always agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from steer_core.Constants.Universal import PI, TWO_PI

from steer_opencell_design.Constructions.Layups.StackProfile import StackProfile

try:  # pragma: no cover - numba is a hard dependency; this only guards imports
    from numba import njit

    HAS_NUMBA = True
except ImportError:  # pragma: no cover
    HAS_NUMBA = False

    def njit(*args, **kwargs):  # type: ignore[misc]
        def decorator(func):
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator


_NJIT_KW = dict(cache=True, fastmath=True, error_model="numpy", boundscheck=False)

# Columns of a wound path array (shared with SpiralUtils).
THETA_COL = 0
X_UNWRAPPED_COL = 1
RADIUS_COL = 2
X_COORD_COL = 3
Z_COORD_COL = 4
TURNS_COL = 5
N_COLS = 6

# Horizontal run per unit rise of the ramp a strip makes over a step in the turn
# beneath it (a strip under tension bridges the step; it cannot fold into it).
RAMP_RUN_PER_RISE = 4.0

# Where across its thickness the strip's length is measured: 0 = bottom face,
# 0.5 = mid-plane. A bent strip's length is its neutral (mid) plane's.
ARC_REFERENCE = 0.5

# Default template resolution: samples per turn on a round mandrel, and samples
# per semicircle / target spacing on a racetrack's straights.
ROUND_POINTS_PER_TURN = 100
ROUND_POINTS_PER_TURN_HIRES = 360
RACETRACK_CURVE_POINTS = 48
RACETRACK_CURVE_POINTS_HIRES = 128
RACETRACK_STRAIGHT_SPACING = 2e-3
RACETRACK_STRAIGHT_SPACING_HIRES = 2e-4


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class WindingTemplate:
    """One turn of sample points on the mandrel surface, with outward normals.

    ``kind`` is ``"round"`` or ``"racetrack"``. ``radius`` is the mandrel (or
    pressed) radius and ``straight`` the racetrack's straight length (0 for round).
    The template is traversed in winding order; sample ``j`` of every turn lies on
    the same normal line.
    """

    kind: str
    x: np.ndarray
    z: np.ndarray
    nx: np.ndarray
    nz: np.ndarray
    radius: float
    straight: float = 0.0

    @property
    def points_per_turn(self) -> int:
        return int(self.x.shape[0])

    @property
    def perimeter(self) -> float:
        return TWO_PI * self.radius + 2.0 * self.straight


def round_template(radius: float, points_per_turn: int = ROUND_POINTS_PER_TURN) -> WindingTemplate:
    """A round mandrel's template: clockwise from the top (θ = π/2)."""
    p = max(int(points_per_turn), 8)
    theta = PI / 2 - TWO_PI * np.arange(p) / p
    nx, nz = np.cos(theta), np.sin(theta)
    return WindingTemplate("round", radius * nx, radius * nz, nx, nz, float(radius))


def racetrack_template(
    radius: float,
    straight: float,
    curve_points: int = RACETRACK_CURVE_POINTS,
    straight_spacing: float = RACETRACK_STRAIGHT_SPACING,
) -> WindingTemplate:
    """A racetrack's template: clockwise from the top of the right semicircle.

    Right semicircle (centre ``(+S/2, 0)``), bottom straight right to left, left
    semicircle, top straight left to right. Curves are sampled at fixed angles and
    straights at fixed x, so every turn's samples sit on the same normals.
    """
    n_c = max(int(curve_points), 4)
    half = straight / 2.0
    n_s = max(int(np.ceil(straight / straight_spacing)), 2) if straight > 0 else 0
    parts_x, parts_z, parts_nx, parts_nz = [], [], [], []

    phi = PI / 2 - PI * (np.arange(n_c) + 0.5) / n_c  # right curve, π/2 -> -π/2
    parts_x.append(half + radius * np.cos(phi))
    parts_z.append(radius * np.sin(phi))
    parts_nx.append(np.cos(phi))
    parts_nz.append(np.sin(phi))
    if n_s:
        xs = half - straight * (np.arange(n_s) + 0.5) / n_s  # bottom, right -> left
        parts_x.append(xs)
        parts_z.append(np.full(n_s, -radius))
        parts_nx.append(np.zeros(n_s))
        parts_nz.append(np.full(n_s, -1.0))
    phi = -PI / 2 - PI * (np.arange(n_c) + 0.5) / n_c  # left curve, -π/2 -> -3π/2
    parts_x.append(-half + radius * np.cos(phi))
    parts_z.append(radius * np.sin(phi))
    parts_nx.append(np.cos(phi))
    parts_nz.append(np.sin(phi))
    if n_s:
        xs = -half + straight * (np.arange(n_s) + 0.5) / n_s  # top, left -> right
        parts_x.append(xs)
        parts_z.append(np.full(n_s, radius))
        parts_nx.append(np.zeros(n_s))
        parts_nz.append(np.ones(n_s))
    return WindingTemplate(
        "racetrack",
        np.concatenate(parts_x),
        np.concatenate(parts_z),
        np.concatenate(parts_nx),
        np.concatenate(parts_nz),
        float(radius),
        float(straight),
    )


# --------------------------------------------------------------------------- #
# Kernel
# --------------------------------------------------------------------------- #
@njit(**_NJIT_KW)
def _cum_area_at(s, edges, thick, cum, j):
    """Cumulative thickness-length integral at ``s`` (pointer ``j`` only advances)."""
    m = thick.shape[0]
    if s <= edges[0]:
        return 0.0, 0
    while j < m - 1 and s >= edges[j + 1]:
        j += 1
    if s >= edges[m]:
        return cum[m], j
    return cum[j] + thick[j] * (s - edges[j]), j


# A support rising or falling faster than a ramp by more than this (m per sample)
# is a step the ramp search must see; anything gentler can never beat the support.
_STEP_TOLERANCE = 1e-13


@njit(inline="always", **_NJIT_KW)
def _ramped_support(i, sup, w, n_sup, reach, run_per_rise):
    """The strip's offset at sample ``i``: its support, or a ramp off a higher
    support within ``reach`` ahead (rising before a step up, a wedge void) or
    behind (draping after a step down)."""
    best = sup[i]
    k = 1
    while i + k < n_sup:
        d = w[i + k] - w[i]
        if d > reach:
            break
        v = sup[i + k] - d / run_per_rise
        if v > best:
            best = v
        k += 1
    k = 1
    while i - k >= 0:
        d = w[i] - w[i - k]
        if d > reach:
            break
        v = sup[i - k] - d / run_per_rise
        if v > best:
            best = v
        k += 1
    return best


@njit(**_NJIT_KW)
def _wind_lagged(
    tpl_x, tpl_z, tpl_nx, tpl_nz,
    edges, thick, cum,
    s_strip, s_stop, n_after_strip,
    run_per_rise, arc_reference, reach, max_n,
):
    """Wind the strip turn on turn; see the module docstring.

    Returns ``(a, s, tc, i_strip, n, overflow)``: per sample the offset from the
    mandrel surface ``a`` (m), arc length ``s`` (m) and mean thickness ``tc`` of
    the arc just laid, the first sample at or past ``s_strip``, the samples used,
    and whether ``max_n`` was too small.
    """
    p = tpl_x.shape[0]
    a = np.empty(max_n)
    s = np.empty(max_n)
    tc = np.empty(max_n)
    sup = np.empty(max_n)  # support offset under each sample
    w = np.empty(max_n)    # arc distance along the support, for the ramp
    w[0] = 0.0
    n_sup = 0
    steps = np.empty(max_n, dtype=np.int64)  # samples where the support steps
    n_steps = 0
    next_step = 0
    j_cum = 0
    c_prev = 0.0
    i_strip = -1
    t0 = thick[0] if thick.shape[0] > 0 else 0.0
    j_sup = 0  # n_sup % p, kept as a counter (integer modulo is slow)
    j_i = 0    # i % p

    for i in range(max_n):
        # Supports are needed up to the ramp's reach ahead; they only read
        # samples at least one turn back, all of which are already wound.
        target = min(i + p - 2, max_n - 1)
        while n_sup <= target:
            m = n_sup
            jm = j_sup
            jp = jm - 1 if jm > 0 else p - 1
            j_sup = jm + 1 if jm + 1 < p else 0
            if m < p:
                sup[m] = 0.0
            else:
                sup[m] = a[m - p] + 0.5 * (tc[m - p] + tc[m - p + 1])
            if m > 0:
                off = sup[m - 1]
                dx = (tpl_x[jm] + off * tpl_nx[jm]) - (tpl_x[jp] + off * tpl_nx[jp])
                dz = (tpl_z[jm] + off * tpl_nz[jm]) - (tpl_z[jp] + off * tpl_nz[jp])
                w[m] = w[m - 1] + np.sqrt(dx * dx + dz * dz)
                if abs(sup[m] - sup[m - 1]) > (w[m] - w[m - 1]) / run_per_rise + _STEP_TOLERANCE:
                    steps[n_steps] = m
                    n_steps += 1
            n_sup += 1

        # A ramp can beat the support only near a step steeper than the ramp
        # itself (a layer starting or stopping one turn down); earlier ramps
        # carried outward are gentler, so the ramp search runs only within reach
        # of a recorded step. Skip steps already out of reach behind.
        while next_step < n_steps and w[steps[next_step]] < w[i] - reach - (
            w[steps[next_step]] - w[steps[next_step] - 1]
        ):
            next_step += 1
        if next_step >= n_steps or w[steps[next_step]] > w[i] + reach:
            a[i] = sup[i]
        else:
            a[i] = _ramped_support(i, sup, w, n_sup, reach, run_per_rise)

        if i == 0:
            s[0] = 0.0
            tc[0] = t0
        else:
            jm = j_i
            jp = jm - 1 if jm > 0 else p - 1
            mid = arc_reference * tc[i - 1]
            dx = (tpl_x[jm] + (a[i] + mid) * tpl_nx[jm]) - (tpl_x[jp] + (a[i - 1] + mid) * tpl_nx[jp])
            dz = (tpl_z[jm] + (a[i] + mid) * tpl_nz[jm]) - (tpl_z[jp] + (a[i - 1] + mid) * tpl_nz[jp])
            ds = np.sqrt(dx * dx + dz * dz)
            if ds < 1e-15:
                ds = 1e-15
            s[i] = s[i - 1] + ds
            j_prev = j_cum
            c_now, j_cum = _cum_area_at(s[i], edges, thick, cum, j_cum)
            if j_cum == j_prev and edges[j_cum] < s[i - 1] and s[i] < edges[j_cum + 1]:
                tc[i] = thick[j_cum]  # the whole arc lies on one interval
            else:
                tc[i] = (c_now - c_prev) / ds
            c_prev = c_now
        j_i = j_i + 1 if j_i + 1 < p else 0

        if i_strip < 0 and s[i] >= s_strip:
            i_strip = i
        if i_strip >= 0:
            if n_after_strip >= 0:
                if i - i_strip >= n_after_strip:
                    return a[: i + 1], s[: i + 1], tc[: i + 1], i_strip, i + 1, False
            elif s[i] >= s_stop:
                return a[: i + 1], s[: i + 1], tc[: i + 1], i_strip, i + 1, False

    return a, s, tc, i_strip, max_n, True


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #
@njit(**_NJIT_KW)
def _gather_rows(
    tpl_x, tpl_z, tpl_nx, tpl_nz, a, s, lo, hi, extra, x_origin, is_round, radius
):
    """Path rows and unit normals at samples ``lo..hi-1``, ``extra[k]`` above the
    strip's bottom face (the same arithmetic as :meth:`WindingResult._rows`)."""
    p = tpl_x.shape[0]
    n = hi - lo
    rows = np.empty((n, 6))
    normals = np.empty((n, 2))
    for k in range(n):
        i = lo + k
        j = i % p
        nx = tpl_nx[j]
        nz = tpl_nz[j]
        x = (tpl_x[j] + a[i] * nx) + extra[k] * nx
        z = (tpl_z[j] + a[i] * nz) + extra[k] * nz
        phase = TWO_PI * i / p
        if is_round:
            rows[k, 0] = PI / 2 - phase
            rows[k, 2] = radius + a[i] + extra[k]
        else:
            rows[k, 0] = phase
            rows[k, 2] = np.hypot(x, z)
        rows[k, 1] = s[i] + x_origin
        rows[k, 3] = x
        rows[k, 4] = z
        rows[k, 5] = i / p
        norm = np.hypot(nx, nz)
        if not norm > 0:
            norm = 1.0
        normals[k, 0] = nx / norm
        normals[k, 1] = nz / norm
    return rows, normals


@dataclass
class TapeSpec:
    """A tape wound after the strip: by turns (``wraps``) or by ``length`` (m)."""

    thickness: float
    wraps: Optional[float] = None
    length: Optional[float] = None


@dataclass
class WindingResult:
    """One winding: per-sample arrays plus helpers to read the strip and tape."""

    template: WindingTemplate
    profile: StackProfile
    a: np.ndarray        # offset of the strip's bottom face from the mandrel (m)
    s: np.ndarray        # arc length (m), 0 at the strip's start
    tc: np.ndarray       # mean thickness of the arc ending at each sample (m)
    strip_length: float  # where the laminate ends (m)
    total_length: float  # where the tape ends, or the strip if no tape (m)
    tape_thickness: float = 0.0

    # ---- per-sample geometry ------------------------------------------------
    @property
    def points_per_turn(self) -> int:
        return self.template.points_per_turn

    def _index(self) -> np.ndarray:
        return np.arange(self.a.shape[0])

    def _template_columns(self, index: np.ndarray):
        j = index % self.points_per_turn
        t = self.template
        return t.x[j], t.z[j], t.nx[j], t.nz[j]

    def theta(self, index_f: np.ndarray) -> np.ndarray:
        """The THETA column for (fractional) sample indices."""
        phase = TWO_PI * index_f / self.points_per_turn
        if self.template.kind == "round":
            return PI / 2 - phase
        return phase

    def _rows(self, columns, extra_offset):
        """Rows from per-sample ``columns`` (already gathered/interpolated)."""
        px, pz, nx, nz, theta, turns, a, s = columns
        x = px + extra_offset * nx
        z = pz + extra_offset * nz
        rows = np.empty((x.shape[0], N_COLS))
        rows[:, THETA_COL] = theta
        rows[:, X_UNWRAPPED_COL] = s + self.profile.x_origin
        if self.template.kind == "round":
            rows[:, RADIUS_COL] = self.template.radius + a + extra_offset
        else:
            rows[:, RADIUS_COL] = np.hypot(x, z)
        rows[:, X_COORD_COL] = x
        rows[:, Z_COORD_COL] = z
        rows[:, TURNS_COL] = turns
        norm = np.hypot(nx, nz)
        norm = np.where(norm > 0, norm, 1.0)
        return rows, np.column_stack((nx / norm, nz / norm))

    def _sample_rows(self, lo: int, hi: int, extra: np.ndarray):
        """Rows and normals at samples ``lo..hi-1`` (no interpolation needed)."""
        t = self.template
        return _gather_rows(
            t.x, t.z, t.nx, t.nz, self.a, self.s, lo, hi,
            np.ascontiguousarray(extra, dtype=float), self.profile.x_origin,
            t.kind == "round", float(t.radius),
        )

    def _at_lengths(self, s_query: np.ndarray):
        """Columns linearly interpolated at arc lengths ``s_query``."""
        n = self.a.shape[0]
        s_query = np.asarray(s_query, dtype=float)
        i0 = np.clip(np.searchsorted(self.s, s_query, side="right") - 1, 0, max(n - 2, 0))
        i1 = np.minimum(i0 + 1, n - 1)
        span = self.s[i1] - self.s[i0]
        f = np.where(span > 0, (s_query - self.s[i0]) / np.where(span > 0, span, 1.0), 0.0)
        f = np.clip(f, 0.0, 1.0)
        index_f = i0 + f
        x0, z0, nx0, nz0 = self._template_columns(i0)
        x1, z1, nx1, nz1 = self._template_columns(i1)
        a0, a1 = self.a[i0], self.a[i1]
        px0, pz0 = x0 + a0 * nx0, z0 + a0 * nz0
        px1, pz1 = x1 + a1 * nx1, z1 + a1 * nz1

        def lerp(c0, c1):
            return c0 + f * (c1 - c0)

        return (lerp(px0, px1), lerp(pz0, pz1), lerp(nx0, nx1), lerp(nz0, nz1),
                self.theta(index_f), index_f / self.points_per_turn, lerp(a0, a1), s_query)

    def sample(self, s_query: np.ndarray, extra_offset: np.ndarray) -> np.ndarray:
        """Wound-path rows at arc lengths ``s_query``, ``extra_offset`` above the
        strip's bottom face. Columns as :data:`THETA_COL` ... :data:`TURNS_COL`
        (turns from the strip's start; ``x_unwrapped`` in laminate x)."""
        s_query = np.asarray(s_query, dtype=float)
        rows, _ = self._rows(self._at_lengths(s_query), np.asarray(extra_offset, float))
        return rows

    def normals(self, s_query: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Unit outward normals at arc lengths ``s_query`` (interpolated)."""
        _, normals = self._rows(self._at_lengths(np.asarray(s_query, float)), 0.0)
        return normals[:, 0], normals[:, 1]

    # ---- the strip's base path ---------------------------------------------
    def base_path(self) -> np.ndarray:
        """The laminate's bottom-face path, ending exactly at the strip's end."""
        n_in = int(np.searchsorted(self.s, self.strip_length, side="left"))
        body, _ = self._sample_rows(0, n_in, np.zeros(n_in))
        end, _ = self._rows(self._at_lengths(np.array([self.strip_length])), 0.0)
        return np.vstack((body, end))

    # ---- components ----------------------------------------------------------
    def _segment_path(self, s0: float, s1: float, offset_of, inner: np.ndarray):
        """Rows and normals for one segment ``[s0, s1]``.

        Samples strictly inside are gathered directly; the ends and each internal
        profile edge are interpolated, an edge twice (left then right of it) so
        the path steps there. ``offset_of(s, side)`` gives the extra offset.
        """
        lo = int(np.searchsorted(self.s, s0, side="right"))
        hi = int(np.searchsorted(self.s, s1, side="left"))
        hi = max(hi, lo)
        body_rows, body_n = self._sample_rows(lo, hi, offset_of(self.s[lo:hi], "right"))

        special_s = np.concatenate(([s0], np.repeat(inner, 2), [s1]))
        sides = ["right"] + ["left", "right"] * inner.shape[0] + ["left"]
        side_right = np.array([side == "right" for side in sides])
        offsets = np.where(
            side_right, offset_of(special_s, "right"), offset_of(special_s, "left")
        )
        sp_rows, sp_n = self._rows(self._at_lengths(special_s), offsets)

        # interleave: s0 first, each edge pair before the first sample past it, s1 last
        where = np.searchsorted(self.s[lo:hi], special_s[1:-1], side="left")
        rows = np.insert(body_rows, where, sp_rows[1:-1], axis=0)
        normals = np.insert(body_n, where, sp_n[1:-1], axis=0)
        rows = np.vstack((sp_rows[:1], rows, sp_rows[-1:]))
        normals = np.vstack((sp_n[:1], normals, sp_n[-1:]))
        return rows, normals

    def layer_path(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        """A layer's centre-line path and its outward normals.

        One NaN row separates the layer's segments. Every segment ends exactly at
        the layer's end, and where a layer beneath it starts or stops inside a
        segment the path steps (two rows at the same arc length).
        """
        profile = self.profile
        c = profile.names.index(name)
        half = profile.layer_thickness[c] / 2

        def offset_of(s_vals, side):
            off = profile.offset[c, profile.interval_at(s_vals, side=side)]
            return np.where(np.isnan(off), half, off)

        rows, normals = [], []
        nan_row = np.full((1, N_COLS), np.nan)
        nan_n = np.full((1, 2), np.nan)
        for s0, s1 in profile.segments[name]:
            inner = profile.edges[(profile.edges > s0) & (profile.edges < s1)]
            seg_rows, seg_n = self._segment_path(s0, s1, offset_of, inner)
            rows += [seg_rows, nan_row]
            normals += [seg_n, nan_n]
        if not rows:
            return np.empty((0, N_COLS)), np.empty((0, 2))
        path = np.vstack(rows[:-1])
        path[:, TURNS_COL] -= path[0, TURNS_COL]
        return path, np.vstack(normals[:-1])

    def tape_path(self) -> Tuple[np.ndarray, np.ndarray]:
        """The tape's centre-line path and normals (empty when there is no tape)."""
        if self.total_length <= self.strip_length or self.tape_thickness <= 0:
            return np.empty((0, N_COLS)), np.empty((0, 2))
        half = self.tape_thickness / 2
        path, normals = self._segment_path(
            self.strip_length,
            self.total_length,
            lambda s_vals, side: np.full(np.shape(s_vals), half),
            np.empty(0),
        )
        path[:, TURNS_COL] -= path[0, TURNS_COL]
        return path, normals

    # ---- measurement ---------------------------------------------------------
    def envelope(self) -> np.ndarray:
        """(N, 2) points on the roll's outer face: the last turn, tape included.

        At each template angle the outermost material is the last turn passing
        it (every turn sits on the one beneath), so the last P samples' outer
        faces (plus the strip's exact end corner) bound the whole roll.
        """
        p = self.points_per_turn
        n = self.a.shape[0]
        end_s = min(self.total_length, float(self.s[-1]))
        lo = max(0, n - p)
        idx = np.arange(lo, n)
        x, z, nx, nz = self._template_columns(idx)
        tc_next = np.concatenate((self.tc[1:], self.tc[-1:]))
        top = self.a[idx] + 0.5 * (self.tc[idx] + tc_next[idx])
        pts = [np.column_stack((x + top * nx, z + top * nz))]
        end_t = self._thickness_at_s(np.array([end_s - 1e-12]))
        end_row = self.sample(np.array([end_s]), end_t)
        pts.append(end_row[:, [X_COORD_COL, Z_COORD_COL]])
        if n < p:  # less than one turn: the bare mandrel bounds the rest
            pts.append(np.column_stack((self.template.x, self.template.z)))
        return np.vstack(pts)

    def _thickness_at_s(self, s_query: np.ndarray) -> np.ndarray:
        t = self.profile.thickness_at(np.minimum(s_query, self.strip_length))
        if self.tape_thickness > 0:
            t = np.where(s_query > self.strip_length, self.tape_thickness, t)
        return t


def _max_samples(template: WindingTemplate, edges: np.ndarray, thick: np.ndarray, extra: int) -> int:
    """An upper bound on samples to wind ``edges``/``thick`` (plus ``extra``).

    Turn ``k`` lies at least ``k`` thinnest layers off the mandrel, so it is at
    least ``perimeter + 2*pi*k*t_min`` long; arc over a zero-thickness gap adds
    length without lifting the next turn, so it can take at most
    ``gap / perimeter`` extra turns.
    """
    perimeter = max(template.perimeter, 1e-9)
    lengths = np.diff(edges)
    solid = thick > 0
    gap_length = float(lengths[~solid].sum())
    solid_length = float(lengths[solid].sum())
    turns = gap_length / perimeter
    if solid_length > 0:
        t_min = float(thick[solid].min())
        # smallest n with perimeter*n + pi*t_min*n^2 >= solid_length
        turns += (-perimeter + np.sqrt(perimeter**2 + 4 * PI * t_min * solid_length)) / (
            2 * PI * t_min
        )
    return int(np.ceil((turns + 3.0) * template.points_per_turn)) + extra + 8


def wind(
    profile: StackProfile,
    template: WindingTemplate,
    tape: Optional[TapeSpec] = None,
) -> WindingResult:
    """Wind ``profile`` (and an optional ``tape``) onto ``template``."""
    strip_length = float(profile.length)
    edges = profile.edges.astype(np.float64)
    thick = profile.thickness.astype(np.float64)
    tape_t = 0.0
    n_after = -1
    s_stop = strip_length
    if tape is not None and tape.thickness > 0:
        tape_t = float(tape.thickness)
        if tape.wraps is not None and tape.wraps > 0:
            n_after = int(np.ceil(tape.wraps * template.points_per_turn)) + 1
            tape_end = strip_length + 1e6  # long enough; the count stops it
        elif tape.length is not None and tape.length > 0:
            tape_end = strip_length + float(tape.length)
            s_stop = tape_end
        else:
            tape_t = 0.0
        if tape_t > 0:
            edges = np.concatenate((edges, [tape_end]))
            thick = np.concatenate((thick, [tape_t]))
    if thick.size == 0:
        edges = np.array([0.0, max(strip_length, 1e-9)])
        thick = np.zeros(1)
    cum = np.concatenate(([0.0], np.cumsum(thick * np.diff(edges))))
    t_max = max(float(thick.max()), 1e-9)
    reach = 2.0 * RAMP_RUN_PER_RISE * t_max

    if n_after >= 0:  # wraps: the strip, then a counted number of samples
        max_n = _max_samples(template, edges[:-1], thick[:-1], n_after)
    else:
        max_n = _max_samples(template, edges, thick, 0)
    for _ in range(6):
        a, s, tc, i_strip, n, overflow = _wind_lagged(
            template.x, template.z, template.nx, template.nz,
            edges, thick, cum,
            strip_length, s_stop, n_after,
            RAMP_RUN_PER_RISE, ARC_REFERENCE, reach, max_n,
        )
        if not overflow:
            break
        max_n *= 2
    else:  # pragma: no cover - the bound above is generous
        raise RuntimeError("winding did not reach the end of the strip")

    if n_after >= 0:
        # count the wraps from the strip's exact end, not the next sample
        index = np.arange(s.shape[0], dtype=float)
        start = float(np.interp(strip_length, s, index))
        end = min(start + float(tape.wraps) * template.points_per_turn, index[-1])
        total = float(np.interp(end, index, s))
    else:
        total = float(s_stop) if tape_t > 0 else strip_length
    return WindingResult(
        template=template,
        profile=profile,
        a=a.copy(),
        s=s.copy(),
        tc=tc.copy(),
        strip_length=strip_length,
        total_length=total,
        tape_thickness=tape_t,
    )


# --------------------------------------------------------------------------- #
# Extrusion
# --------------------------------------------------------------------------- #
def extrude_path(path: np.ndarray, normals: np.ndarray, thickness: float, kind: str) -> np.ndarray:
    """A closed outline of a centre-line path thickened by ``thickness``.

    Per NaN-separated segment: the outer edge, two padding rows, then the inner
    edge reversed; NaN rows between segments (the layout plots expect).
    """
    if path.size == 0:
        return path.copy()
    half = thickness / 2.0
    nan_row = np.full((1, path.shape[1]), np.nan)
    valid = ~np.isnan(path[:, X_UNWRAPPED_COL])
    bounds = np.flatnonzero(np.diff(np.concatenate(([False], valid, [False])).astype(np.int8)))
    out = []
    for start, end in zip(bounds[0::2], bounds[1::2]):
        seg, nrm = path[start:end], normals[start:end]
        outer, inner = seg.copy(), seg.copy()
        outer[:, X_COORD_COL] = seg[:, X_COORD_COL] + half * nrm[:, 0]
        outer[:, Z_COORD_COL] = seg[:, Z_COORD_COL] + half * nrm[:, 1]
        inner[:, X_COORD_COL] = seg[:, X_COORD_COL] - half * nrm[:, 0]
        inner[:, Z_COORD_COL] = seg[:, Z_COORD_COL] - half * nrm[:, 1]
        if kind == "round":
            outer[:, RADIUS_COL] = seg[:, RADIUS_COL] + half
            inner[:, RADIUS_COL] = seg[:, RADIUS_COL] - half
        else:
            outer[:, RADIUS_COL] = np.hypot(outer[:, X_COORD_COL], outer[:, Z_COORD_COL])
            inner[:, RADIUS_COL] = np.hypot(inner[:, X_COORD_COL], inner[:, Z_COORD_COL])
        inner = inner[::-1]
        out.append(
            np.vstack((outer, np.tile(outer[-1], (2, 1)), np.tile(inner[0], (2, 1)), inner))
        )
        out.append(nan_row)
    return np.vstack(out[:-1])


def component_paths(
    result: WindingResult, thicknesses: Dict[str, float]
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """Every layer's (and the tape's) centre-line path and extruded outline."""
    paths: Dict[str, np.ndarray] = {}
    outlines: Dict[str, np.ndarray] = {}
    kind = result.template.kind
    for c, name in enumerate(result.profile.names):
        path, normals = result.layer_path(name)
        paths[name] = path
        outlines[name] = extrude_path(
            path, normals, thicknesses.get(name, float(result.profile.layer_thickness[c])), kind
        )
    tape, tape_normals = result.tape_path()
    if tape.size:
        paths["tape"] = tape
        outlines["tape"] = extrude_path(tape, tape_normals, result.tape_thickness, kind)
    return paths, outlines
