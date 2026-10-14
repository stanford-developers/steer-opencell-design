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
    a = np.zeros(max_n)
    s = np.zeros(max_n)
    tc = np.zeros(max_n)
    sup = np.zeros(max_n)  # support offset under each sample
    w = np.zeros(max_n)    # arc distance along the support, for the ramp
    n_sup = 0
    j_cum = 0
    c_prev = 0.0
    i_strip = -1
    t0 = thick[0] if thick.shape[0] > 0 else 0.0

    for i in range(max_n):
        # Supports are needed up to the ramp's reach ahead; they only read
        # samples at least one turn back, all of which are already wound.
        target = min(i + p - 2, max_n - 1)
        while n_sup <= target:
            m = n_sup
            jm = m % p
            if m < p:
                sup[m] = 0.0
            else:
                sup[m] = a[m - p] + 0.5 * (tc[m - p] + tc[m - p + 1])
            if m > 0:
                jp = (m - 1) % p
                off = sup[m - 1]
                dx = (tpl_x[jm] + off * tpl_nx[jm]) - (tpl_x[jp] + off * tpl_nx[jp])
                dz = (tpl_z[jm] + off * tpl_nz[jm]) - (tpl_z[jp] + off * tpl_nz[jp])
                w[m] = w[m - 1] + np.sqrt(dx * dx + dz * dz)
            n_sup += 1

        best = sup[i]
        k = 1
        while i + k < n_sup:  # ahead: rise early towards a step up (wedge void)
            d = w[i + k] - w[i]
            if d > reach:
                break
            v = sup[i + k] - d / run_per_rise
            if v > best:
                best = v
            k += 1
        k = 1
        while i - k >= 0:  # behind: drape down after a step down
            d = w[i] - w[i - k]
            if d > reach:
                break
            v = sup[i - k] - d / run_per_rise
            if v > best:
                best = v
            k += 1
        a[i] = best

        if i == 0:
            s[0] = 0.0
            tc[0] = t0
        else:
            jm = i % p
            jp = (i - 1) % p
            mid = arc_reference * tc[i - 1]
            dx = (tpl_x[jm] + (a[i] + mid) * tpl_nx[jm]) - (tpl_x[jp] + (a[i - 1] + mid) * tpl_nx[jp])
            dz = (tpl_z[jm] + (a[i] + mid) * tpl_nz[jm]) - (tpl_z[jp] + (a[i - 1] + mid) * tpl_nz[jp])
            ds = np.sqrt(dx * dx + dz * dz)
            if ds < 1e-15:
                ds = 1e-15
            s[i] = s[i - 1] + ds
            c_now, j_cum = _cum_area_at(s[i], edges, thick, cum, j_cum)
            tc[i] = (c_now - c_prev) / ds
            c_prev = c_now

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

    def sample(self, s_query: np.ndarray, extra_offset: np.ndarray) -> np.ndarray:
        """Wound-path rows at arc lengths ``s_query``, ``extra_offset`` above the
        strip's bottom face. Columns as :data:`THETA_COL` ... :data:`TURNS_COL`
        (turns from the strip's start; ``x_unwrapped`` in laminate x)."""
        s_query = np.asarray(s_query, dtype=float)
        n = self.a.shape[0]
        index_f = np.interp(s_query, self.s, np.arange(n, dtype=float))
        i0 = np.clip(np.floor(index_f).astype(np.int64), 0, n - 1)
        i1 = np.minimum(i0 + 1, n - 1)
        f = index_f - i0
        x0, z0, nx0, nz0 = self._template_columns(i0)
        x1, z1, nx1, nz1 = self._template_columns(i1)
        off = np.interp(s_query, self.s, self.a) + extra_offset
        px0 = x0 + (self.a[i0] + extra_offset) * nx0
        pz0 = z0 + (self.a[i0] + extra_offset) * nz0
        px1 = x1 + (self.a[i1] + extra_offset) * nx1
        pz1 = z1 + (self.a[i1] + extra_offset) * nz1
        x = px0 + f * (px1 - px0)
        z = pz0 + f * (pz1 - pz0)
        rows = np.empty((s_query.shape[0], N_COLS))
        rows[:, THETA_COL] = self.theta(index_f)
        rows[:, X_UNWRAPPED_COL] = s_query + self.profile.x_origin
        if self.template.kind == "round":
            rows[:, RADIUS_COL] = self.template.radius + off
        else:
            rows[:, RADIUS_COL] = np.hypot(x, z)
        rows[:, X_COORD_COL] = x
        rows[:, Z_COORD_COL] = z
        rows[:, TURNS_COL] = index_f / self.points_per_turn
        return rows

    def normals(self, s_query: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Unit outward normals at arc lengths ``s_query`` (interpolated)."""
        n = self.a.shape[0]
        index_f = np.interp(np.asarray(s_query, float), self.s, np.arange(n, dtype=float))
        i0 = np.clip(np.floor(index_f).astype(np.int64), 0, n - 1)
        i1 = np.minimum(i0 + 1, n - 1)
        f = index_f - i0
        _, _, nx0, nz0 = self._template_columns(i0)
        _, _, nx1, nz1 = self._template_columns(i1)
        nx = nx0 + f * (nx1 - nx0)
        nz = nz0 + f * (nz1 - nz0)
        norm = np.hypot(nx, nz)
        norm = np.where(norm > 0, norm, 1.0)
        return nx / norm, nz / norm

    # ---- the strip's base path ---------------------------------------------
    def base_path(self) -> np.ndarray:
        """The laminate's bottom-face path, ending exactly at the strip's end."""
        inside = self.s < self.strip_length
        s_rows = np.concatenate((self.s[inside], [self.strip_length]))
        return self.sample(s_rows, np.zeros_like(s_rows))

    # ---- components ----------------------------------------------------------
    def layer_path(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        """A layer's centre-line path and its outward normals.

        One NaN row separates the layer's segments. Every segment ends exactly at
        the layer's end, and where a layer beneath it starts or stops inside a
        segment the path steps (two rows at the same arc length).
        """
        profile = self.profile
        c = profile.names.index(name)
        rows, normal_x, normal_z = [], [], []
        first_turn = None
        for s0, s1 in profile.segments[name]:
            inner = profile.edges[(profile.edges > s0) & (profile.edges < s1)]
            body = self.s[(self.s > s0) & (self.s < s1)]
            s_pts = np.concatenate(([s0], body, inner, inner, [s1]))
            # interval each point belongs to: start -> right side, end -> left,
            # internal edges once on each side
            side_right = np.concatenate(
                (
                    [True],
                    np.ones(body.shape[0], dtype=bool),
                    np.zeros(inner.shape[0], dtype=bool),
                    np.ones(inner.shape[0], dtype=bool),
                    [False],
                )
            )
            order = np.lexsort((side_right, s_pts))
            s_pts, side_right = s_pts[order], side_right[order]
            k = np.where(
                side_right,
                profile.interval_at(s_pts, side="right"),
                profile.interval_at(s_pts, side="left"),
            )
            offset = profile.offset[c, k]
            offset = np.where(np.isnan(offset), profile.layer_thickness[c] / 2, offset)
            path = self.sample(s_pts, offset)
            nx, nz = self.normals(s_pts)
            if first_turn is None:
                first_turn = path[0, TURNS_COL]
            path[:, TURNS_COL] -= first_turn
            if self.template.kind == "racetrack":
                # theta increases with the winding; keep it relative-free like round
                pass
            rows.append(path)
            normal_x.append(nx)
            normal_z.append(nz)
            rows.append(np.full((1, N_COLS), np.nan))
            normal_x.append(np.array([np.nan]))
            normal_z.append(np.array([np.nan]))
        if not rows:
            return np.empty((0, N_COLS)), np.empty((0, 2))
        rows, normal_x, normal_z = rows[:-1], normal_x[:-1], normal_z[:-1]
        return np.vstack(rows), np.column_stack((np.concatenate(normal_x), np.concatenate(normal_z)))

    def tape_path(self) -> Tuple[np.ndarray, np.ndarray]:
        """The tape's centre-line path and normals (empty when there is no tape)."""
        if self.total_length <= self.strip_length or self.tape_thickness <= 0:
            return np.empty((0, N_COLS)), np.empty((0, 2))
        body = self.s[(self.s > self.strip_length) & (self.s < self.total_length)]
        s_pts = np.concatenate(([self.strip_length], body, [self.total_length]))
        path = self.sample(s_pts, np.full_like(s_pts, self.tape_thickness / 2))
        path[:, TURNS_COL] -= path[0, TURNS_COL]
        nx, nz = self.normals(s_pts)
        return path, np.column_stack((nx, nz))

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


def _max_samples(template: WindingTemplate, total_length: float, extra_turns: float) -> int:
    """An upper bound on samples: turns can't be shorter than the mandrel's perimeter."""
    turns = total_length / max(template.perimeter, 1e-9) + extra_turns + 3.0
    return int(np.ceil(turns * template.points_per_turn)) + 8


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
    extra_turns = 0.0
    if tape is not None and tape.thickness > 0:
        tape_t = float(tape.thickness)
        if tape.wraps is not None and tape.wraps > 0:
            n_after = int(round(tape.wraps * template.points_per_turn))
            extra_turns = float(tape.wraps)
            tape_end = strip_length + 1e6  # long enough; the count stops it
        elif tape.length is not None and tape.length > 0:
            tape_end = strip_length + float(tape.length)
            s_stop = tape_end
            extra_turns = float(tape.length) / max(template.perimeter, 1e-9)
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

    max_n = _max_samples(template, strip_length, extra_turns)
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
        total = float(s[-1])
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
