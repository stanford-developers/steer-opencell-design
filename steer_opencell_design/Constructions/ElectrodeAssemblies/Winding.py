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
* afterwards the support under sample ``m`` is ``a[m - P]`` plus the height of
  the stack's top there;
* the strip is held under tension and has no bending stiffness, so it lies on the
  *taut chain* over its support: the local convex hull, in the x-z plane. Where
  the support steps up or down, the strip leaves the step's top corner in a
  straight line and touches down where that line is tangent to the surface
  beneath, at the step's horizon: arccos(rho / (rho + step)) round a surface of
  radius rho, so the span is short and steep near the core and long and shallow
  further out. On a racetrack's straight the horizon is the straight's end, so
  the span reaches the next curve. The void under the span is all the gap there
  is;
* within the strip, every layer drapes over the layers beneath it the same way
  (:func:`_drape_window`): where a layer starts or stops underneath, the layers
  above bend over the step instead of jumping, and only the top of the stack can
  still step (where a top layer itself ends), for the next turn to span;
* arc length advances along the strip's mid-plane, and the strip ends exactly at
  its length.

Layer heights come from the exact layer stack (:class:`StackProfile`): every step
lands where the layer actually starts or stops, with the step's corner placed on
the mandrel's exact shape between samples. A tape, when present, is wound in the
same pass as the strip's outermost continuation, and the laminate's samples are
identical with or without it (the recurrence only ever looks one turn back).

Known limit: all layers share the strip's one arc length.

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
    n_curve: int = 0  # racetrack samples per semicircle
    n_straight: int = 0  # racetrack samples per straight

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
        n_c,
        n_s,
    )


# --------------------------------------------------------------------------- #
# Kernel
# --------------------------------------------------------------------------- #
# A chain that turns inward by more than this angle (rad) at a vertex is concave
# there, and the taut strip bridges it. Collinear points (straights) are kept.
_CONCAVE_TOL = 1e-9
# A step in the stack's top surface smaller than this (m) is not a corner.
_CORNER_TOL = 1e-12


@njit(inline="always", **_NJIT_KW)
def _tpl_at(f, is_round, radius, half, straight, n_c, n_s, p):
    """Template point and outward normal at fractional template index ``f``.

    Exact on the mandrel's own shape (not the chord between samples): a circle,
    or a racetrack's semicircles and straights. Integer ``f`` gives the samples.
    """
    f = f % p
    if is_round:
        th = PI / 2 - TWO_PI * f / p
        nx = np.cos(th)
        nz = np.sin(th)
        return radius * nx, radius * nz, nx, nz
    u = f + 0.5
    if u >= p:
        u -= p
    if u < n_c:  # right semicircle
        phi = PI / 2 - PI * u / n_c
        nx = np.cos(phi)
        nz = np.sin(phi)
        return half + radius * nx, radius * nz, nx, nz
    u -= n_c
    if u < n_s:  # bottom straight, right to left
        return half - straight * u / n_s, -radius, 0.0, -1.0
    u -= n_s
    if u < n_c:  # left semicircle
        phi = -PI / 2 - PI * u / n_c
        nx = np.cos(phi)
        nz = np.sin(phi)
        return -half + radius * nx, radius * nz, nx, nz
    u -= n_c  # top straight, left to right
    return -half + straight * u / n_s, radius, 0.0, 1.0


@njit(inline="always", **_NJIT_KW)
def _hull_push(cf, cx, cz, n, f, x, z, mask, floor):
    """Push a point onto a clockwise chain, first popping every vertex the new
    point makes concave (the strip spans straight over it). Returns the length.

    The chain is stored at ``index & mask`` (a ring buffer; ``mask = -1`` for a
    plain array) and is never popped below ``floor`` entries.
    """
    while n >= 2 and n > floor:
        b = (n - 1) & mask
        c = (n - 2) & mask
        e1x = cx[b] - cx[c]
        e1z = cz[b] - cz[c]
        e2x = x - cx[b]
        e2z = z - cz[b]
        cr = e1x * e2z - e1z * e2x
        if cr > 0 and cr * cr > (_CONCAVE_TOL * _CONCAVE_TOL) * (
            (e1x * e1x + e1z * e1z) * (e2x * e2x + e2z * e2z)
        ):
            n -= 1
        else:
            break
    k = n & mask
    cf[k] = f
    cx[k] = x
    cz[k] = z
    return n + 1


@njit(inline="always", **_NJIT_KW)
def _ray_hit(tx, tz, nx, nz, ux, uz, vx, vz):
    """Distance along the ray ``(tx, tz) + t (nx, nz)`` to the line through u, v."""
    dx = vx - ux
    dz = vz - uz
    den = nx * dz - nz * dx
    if den == 0.0:
        return np.nan
    return ((ux - tx) * dz - (uz - tz) * dx) / den


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
def _drape_run(
    c, t_c, n_run, run_e, run_y, n_ch, ch_f, ch_x, ch_z,
    el_f, el_q, el_k, el_tx, el_tz, el_nx, el_nz, el_a,
    off, edge_bot, low_l, low_r, present, n_strip,
):
    """Read one run of layer ``c`` off its chain: its bottom at every element,
    raising the surface the layers above it rest on."""
    kk = 0
    for r in range(n_run):
        er = run_e[r]
        f = el_f[er]
        while kk + 1 < n_ch - 1 and ch_f[kk + 1] <= f:
            kk += 1
        hgt = run_y[r]
        if n_ch >= 2:
            hit = _ray_hit(
                el_tx[er], el_tz[er], el_nx[er], el_nz[er],
                ch_x[kk], ch_z[kk], ch_x[kk + 1], ch_z[kk + 1],
            )
            if hit - el_a[er] > hgt:
                hgt = hit - el_a[er]
        top = hgt + t_c
        if el_q[er] >= 0:
            off[c, el_q[er]] = hgt
            if top > low_l[er]:
                low_l[er] = top
        else:
            ke = el_k[er]
            edge_bot[c, ke] = hgt
            if ke - 1 >= 0 and ke - 1 < n_strip and present[c, ke - 1] and top > low_l[er]:
                low_l[er] = top
            if ke < n_strip and present[c, ke] and top > low_r[er]:
                low_r[er] = top


@njit(**_NJIT_KW)
def _drape_window(
    q_a, q_b, k_lo, k_hi,
    a, s, iv, H, off, inwin, edge_bot, edge_f, corner_f, corner_h, n_corner,
    tpl_x, tpl_z, tpl_nx, tpl_nz, is_round, radius, half, straight, n_c, n_s,
    edges, thick, present, layer_t, n_strip,
):
    """Drape every layer over the layers beneath it, samples ``q_a..q_b``.

    Each layer's bottom face is the taut chain (local convex hull, in x-z) of the
    top of the layers below it, on its own segments. The support steps exactly at
    the profile edges ``k_lo..k_hi``, which enter as corner points. Writes each
    layer's bottom height above the strip's bottom face (``off``, NaN where it is
    absent), its height at each edge (``edge_bot``), the stack top ``H``, the
    edges' fractional sample positions (``edge_f``), and a corner wherever the
    stack top still steps (a layer ending on top), for the next turn to bridge.
    """
    p = tpl_x.shape[0]
    n_layers = layer_t.shape[0]
    n_w = q_b - q_a + 1
    n_k = k_hi - k_lo + 1 if k_hi >= k_lo else 0
    n_el = n_w + n_k
    el_f = np.empty(n_el)
    el_q = np.empty(n_el, np.int64)
    el_k = np.empty(n_el, np.int64)
    el_tx = np.empty(n_el)
    el_tz = np.empty(n_el)
    el_nx = np.empty(n_el)
    el_nz = np.empty(n_el)
    el_a = np.empty(n_el)

    # samples and edges in order along the strip (an edge before a sample at it)
    q = q_a
    k = k_lo
    q0 = q_a
    for e in range(n_el):
        if k <= k_hi and (q > q_b or edges[k] <= s[q]):
            ek = edges[k]
            while q0 < q_b and s[q0 + 1] <= ek:
                q0 += 1
            if q0 < q_b and ek > s[q0]:
                fr = (ek - s[q0]) / (s[q0 + 1] - s[q0])
                f = q0 + fr
                av = a[q0] + fr * (a[q0 + 1] - a[q0])
            else:
                f = float(q0)
                av = a[q0]
            tx, tz, nx, nz = _tpl_at(f, is_round, radius, half, straight, n_c, n_s, p)
            el_f[e] = f
            el_q[e] = -1
            el_k[e] = k
            el_tx[e] = tx
            el_tz[e] = tz
            el_nx[e] = nx
            el_nz[e] = nz
            el_a[e] = av
            edge_f[k] = f
            k += 1
        else:
            j = q % p
            el_f[e] = float(q)
            el_q[e] = q
            el_k[e] = -1
            el_tx[e] = tpl_x[j]
            el_tz[e] = tpl_z[j]
            el_nx[e] = tpl_nx[j]
            el_nz[e] = tpl_nz[j]
            el_a[e] = a[q]
            q += 1

    low_l = np.zeros(n_el)  # top of the layers below: at a sample, or left of an edge
    low_r = np.zeros(n_el)  # right of an edge
    ch_f = np.empty(n_el)
    ch_x = np.empty(n_el)
    ch_z = np.empty(n_el)
    run_e = np.empty(n_el, np.int64)
    run_y = np.empty(n_el)

    for c in range(n_layers):
        t_c = layer_t[c]
        for qq in range(q_a, q_b + 1):
            off[c, qq] = np.nan
        n_run = 0
        n_ch = 0
        for e in range(n_el + 1):
            add = False
            flush_before = False
            flush_after = False
            y = 0.0
            if e == n_el:
                flush_before = True
            elif el_q[e] >= 0:
                jv = iv[el_q[e]]
                if jv < n_strip and present[c, jv]:
                    add = True
                    y = low_l[e]
                else:
                    flush_before = True
            else:
                ke = el_k[e]
                pl = ke - 1 >= 0 and ke - 1 < n_strip and present[c, ke - 1]
                pr = ke < n_strip and present[c, ke]
                if pl and pr:  # the layer runs on over a step beneath it
                    add = True
                    y = max(low_l[e], low_r[e])
                elif pl:  # the layer ends here
                    add = True
                    y = low_l[e]
                    flush_after = True
                elif pr:  # the layer starts here
                    flush_before = True
                    add = True
                    y = low_r[e]
                else:
                    flush_before = True
            if flush_before and n_run > 0:
                _drape_run(
                    c, t_c, n_run, run_e, run_y, n_ch, ch_f, ch_x, ch_z,
                    el_f, el_q, el_k, el_tx, el_tz, el_nx, el_nz, el_a,
                    off, edge_bot, low_l, low_r, present, n_strip,
                )
                n_run = 0
                n_ch = 0
            if add:
                h = el_a[e] + y
                n_ch = _hull_push(
                    ch_f, ch_x, ch_z, n_ch, el_f[e],
                    el_tx[e] + h * el_nx[e], el_tz[e] + h * el_nz[e], -1, 0,
                )
                run_e[n_run] = e
                run_y[n_run] = y
                n_run += 1
            if flush_after and n_run > 0:
                _drape_run(
                    c, t_c, n_run, run_e, run_y, n_ch, ch_f, ch_x, ch_z,
                    el_f, el_q, el_k, el_tx, el_tz, el_nx, el_nz, el_a,
                    off, edge_bot, low_l, low_r, present, n_strip,
                )
                n_run = 0
                n_ch = 0

    for e in range(n_el):
        if el_q[e] >= 0:
            qq = el_q[e]
            inwin[qq] = 1
            if iv[qq] < n_strip:
                H[qq] = low_l[e]
        else:
            ke = el_k[e]
            h_l = low_l[e] if ke - 1 >= 0 and ke - 1 < n_strip else 0.0
            if ke < n_strip:
                h_r = low_r[e]
            elif ke < thick.shape[0]:
                h_r = thick[ke]  # the tape, past the strip's end
            else:
                h_r = 0.0
            if abs(h_l - h_r) > _CORNER_TOL and n_corner < corner_f.shape[0]:
                corner_f[n_corner] = el_f[e]
                corner_h[n_corner] = max(h_l, h_r)
                n_corner += 1
    return n_corner


@njit(**_NJIT_KW)
def _wind_taut(
    tpl_x, tpl_z, tpl_nx, tpl_nz, is_round, radius, half, straight, n_c, n_s,
    edges, thick, cum, present, layer_t, n_strip,
    s_strip, s_stop, n_after_strip, arc_reference, max_n,
):
    """Wind the strip turn on turn; see the module docstring.

    Each turn's bottom face is the taut chain over the turn beneath it; within
    the strip each layer drapes over the layers below it (:func:`_drape_window`,
    run on windows around the profile's edges). Returns per sample the offset of
    the strip's bottom face from the mandrel ``a``, the arc length ``s``, the mean
    raw thickness ``tc`` of the arc just laid (for the mid-plane arc), the stack
    top ``H``, the profile interval ``iv`` and the drape results, plus the first
    sample at or past ``s_strip``, the samples used, and whether ``max_n`` was too
    small.
    """
    p = tpl_x.shape[0]
    n_layers = layer_t.shape[0]
    n_edge = edges.shape[0]
    a = np.empty(max_n)
    s = np.empty(max_n)
    tc = np.empty(max_n)
    H = np.empty(max_n)
    iv = np.empty(max_n, np.int64)
    inwin = np.zeros(max_n, np.int8)
    off = np.empty((n_layers, max_n))
    # the support under the samples about to be laid, and the turn-to-turn chain
    # (support index, x, z), are only read within a turn or so of the strip:
    # ring buffers that stay in cache
    ring = 8
    while ring < 4 * p + 8:
        ring *= 2
    mask = ring - 1
    sup = np.empty(ring)
    edge_bot = np.full((n_layers, n_edge), np.nan)
    edge_f = np.full(n_edge, np.nan)
    corner_f = np.empty(n_edge + 2)
    corner_h = np.empty(n_edge + 2)
    n_corner = 0
    cf = np.empty(ring)
    cx = np.empty(ring)
    cz = np.empty(ring)
    n_ch = 0
    j_sup = 0  # n_sup % p, and i % p, kept as counters
    j_i = 0
    kk = 0
    n_sup = 0
    next_corner = 0
    n_final = 0  # samples whose stack top is final (drape done)
    pend = False
    q_a = 0
    k_first = 1
    k_last = 0
    next_k = 1
    win_end = 0.0
    max_pend = p - 3
    j_cum = 0
    c_prev = 0.0
    i_strip = -1
    t0 = thick[0] if thick.shape[0] > 0 else 0.0
    done = False
    n_out = max_n

    for i in range(max_n):
        # a long pending drape window would starve the next turn of supports
        if pend and i - q_a >= max_pend:
            k_hi = k_last
            while k_hi >= k_first and edges[k_hi] > s[i - 1]:
                k_hi -= 1
            n_corner = _drape_window(
                q_a, i - 1, k_first, k_hi,
                a, s, iv, H, off, inwin, edge_bot, edge_f, corner_f, corner_h, n_corner,
                tpl_x, tpl_z, tpl_nx, tpl_nz, is_round, radius, half, straight, n_c, n_s,
                edges, thick, present, layer_t, n_strip,
            )
            next_k = k_hi + 1
            pend = False
            n_final = i

        # supports up to one turn ahead, over samples whose stack top is final
        target = min(i + p - 2, n_final + p - 1, max_n - 1)
        while n_sup <= target:
            m = n_sup
            while next_corner < n_corner and corner_f[next_corner] + p < m:
                fc = corner_f[next_corner]
                c0 = int(fc)
                fr = fc - c0
                ac = a[c0] + fr * (a[c0 + 1] - a[c0]) if fr > 0 else a[c0]
                x, z, nx, nz = _tpl_at(fc, is_round, radius, half, straight, n_c, n_s, p)
                h = ac + corner_h[next_corner]
                n_ch = _hull_push(
                    cf, cx, cz, n_ch, fc + p, x + h * nx, z + h * nz, mask, n_ch - ring + 4
                )
                next_corner += 1
            jm = j_sup
            j_sup = jm + 1 if jm + 1 < p else 0
            sm = 0.0 if m < p else a[m - p] + H[m - p]
            sup[m & mask] = sm
            n_ch = _hull_push(
                cf, cx, cz, n_ch, float(m),
                tpl_x[jm] + sm * tpl_nx[jm], tpl_z[jm] + sm * tpl_nz[jm], mask, n_ch - ring + 4,
            )
            n_sup += 1

        # the strip at i: where its normal meets the chain over its support
        if kk > n_ch - 2:
            kk = n_ch - 2 if n_ch >= 2 else 0
        if kk < n_ch - ring + 4:
            kk = n_ch - ring + 4
        while kk > 0 and cf[kk & mask] > i:
            kk -= 1
        while kk + 1 < n_ch - 1 and cf[(kk + 1) & mask] <= i:
            kk += 1
        ji = j_i
        ai = sup[i & mask]
        k0 = kk & mask
        k1 = (kk + 1) & mask
        if n_ch >= 2 and cf[k0] != i and cf[k1] > i:  # i is not itself a vertex
            hit = _ray_hit(
                tpl_x[ji], tpl_z[ji], tpl_nx[ji], tpl_nz[ji], cx[k0], cz[k0], cx[k1], cz[k1]
            )
            if hit > ai:
                ai = hit
        a[i] = ai

        if i == 0:
            s[0] = 0.0
            tc[0] = t0
            j_cum = 0
        else:
            jp = ji - 1 if ji > 0 else p - 1
            mid = arc_reference * tc[i - 1]
            dx = (tpl_x[ji] + (a[i] + mid) * tpl_nx[ji]) - (tpl_x[jp] + (a[i - 1] + mid) * tpl_nx[jp])
            dz = (tpl_z[ji] + (a[i] + mid) * tpl_nz[ji]) - (tpl_z[jp] + (a[i - 1] + mid) * tpl_nz[jp])
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
        iv[i] = j_cum
        H[i] = thick[j_cum] if s[i] < edges[n_edge - 1] else 0.0

        if i_strip < 0 and s[i] >= s_strip:
            i_strip = i
        if i_strip >= 0:
            if n_after_strip >= 0:
                done = i - i_strip >= n_after_strip
            else:
                done = s[i] >= s_stop

        # drape windows: around each profile edge, merged when they overlap
        ri = radius + a[i] + H[i]
        if is_round:
            l_half = TWO_PI * ri / 8.0
        else:
            l_half = straight + PI * ri / 4.0
        if not pend:
            if next_k <= n_strip and s[i] >= edges[next_k] - l_half:
                pend = True
                q_a = i
                k_first = next_k
                k_last = next_k
                next_k += 1
                win_end = edges[k_last] + l_half
            else:
                n_final = i + 1
        if pend:
            while next_k <= n_strip and edges[next_k] - l_half <= win_end:
                k_last = next_k
                next_k += 1
                win_end = edges[k_last] + l_half
            if s[i] >= win_end or done:
                k_hi = k_last
                while k_hi >= k_first and edges[k_hi] > s[i]:
                    k_hi -= 1
                n_corner = _drape_window(
                    q_a, i, k_first, k_hi,
                    a, s, iv, H, off, inwin, edge_bot, edge_f, corner_f, corner_h,
                    n_corner,
                    tpl_x, tpl_z, tpl_nx, tpl_nz, is_round, radius, half, straight,
                    n_c, n_s, edges, thick, present, layer_t, n_strip,
                )
                next_k = k_hi + 1
                pend = False
                n_final = i + 1

        j_i = ji + 1 if ji + 1 < p else 0
        if done:
            n_out = i + 1
            break

    overflow = not done
    return (
        a[:n_out], s[:n_out], tc[:n_out], H[:n_out], iv[:n_out], inwin[:n_out],
        off[:, :n_out], edge_bot, edge_f, corner_f[:n_corner], corner_h[:n_corner],
        i_strip, n_out, overflow,
    )


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #
@njit(**_NJIT_KW)
def _gather_rows(
    tpl_x, tpl_z, tpl_nx, tpl_nz, a, s, lo, hi, extra, x_origin, is_round, radius
):
    """Path rows and unit normals at samples ``lo..hi-1``, ``extra[k]`` above the
    strip's bottom face (the same arithmetic as :meth:`WindingResult._frac_rows`)."""
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


@njit(**_NJIT_KW)
def _template_at_many(f, is_round, radius, half, straight, n_c, n_s, p):
    n = f.shape[0]
    out = np.empty((n, 4))
    for k in range(n):
        x, z, nx, nz = _tpl_at(f[k], is_round, radius, half, straight, n_c, n_s, p)
        out[k, 0] = x
        out[k, 1] = z
        out[k, 2] = nx
        out[k, 3] = nz
    return out


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
    tc: np.ndarray       # mean raw thickness of the arc ending at each sample (m)
    H: np.ndarray        # height of the stack's top above its bottom face (m)
    iv: np.ndarray       # kernel interval (profile, then tape) at each sample
    inwin: np.ndarray    # 1 where a drape window set the layer heights
    off: np.ndarray      # (C, n) layer bottoms above the strip's bottom face (m)
    edges: np.ndarray    # kernel interval edges in s (profile edges, then tape end)
    edge_bot: np.ndarray  # (C, M + 1) layer bottoms at each edge (m; NaN if unset)
    edge_f: np.ndarray   # fractional sample position of each edge
    corner_f: np.ndarray  # stack-top steps: fractional sample position ...
    corner_h: np.ndarray  # ... and the higher side's stack-top height (m)
    strip_length: float  # where the laminate ends (m)
    total_length: float  # where the tape ends, or the strip if no tape (m)
    tape_thickness: float = 0.0

    # ---- per-sample geometry ------------------------------------------------
    @property
    def points_per_turn(self) -> int:
        return self.template.points_per_turn

    def _template_columns(self, index: np.ndarray):
        j = index % self.points_per_turn
        t = self.template
        return t.x[j], t.z[j], t.nx[j], t.nz[j]

    def _template_at(self, f: np.ndarray):
        """Exact template points and normals at fractional sample positions."""
        t = self.template
        out = _template_at_many(
            np.ascontiguousarray(f, dtype=float), t.kind == "round", float(t.radius),
            float(t.straight) / 2.0, float(t.straight), int(t.n_curve),
            int(t.n_straight), t.points_per_turn,
        )
        return out[:, 0], out[:, 1], out[:, 2], out[:, 3]

    def theta(self, index_f: np.ndarray) -> np.ndarray:
        """The THETA column for (fractional) sample indices."""
        phase = TWO_PI * index_f / self.points_per_turn
        if self.template.kind == "round":
            return PI / 2 - phase
        return phase

    def _interp(self, values: np.ndarray, f: np.ndarray) -> np.ndarray:
        """Per-sample ``values`` linearly interpolated at fractional positions."""
        n = values.shape[0]
        i0 = np.clip(np.floor(f).astype(np.int64), 0, max(n - 2, 0))
        i1 = np.minimum(i0 + 1, n - 1)
        fr = np.clip(f - i0, 0.0, 1.0)
        return values[i0] + fr * (values[i1] - values[i0])

    def _index_at(self, s_query: np.ndarray) -> np.ndarray:
        """Fractional sample positions of arc lengths ``s_query``."""
        n = self.s.shape[0]
        s_query = np.asarray(s_query, dtype=float)
        i0 = np.clip(np.searchsorted(self.s, s_query, side="right") - 1, 0, max(n - 2, 0))
        i1 = np.minimum(i0 + 1, n - 1)
        span = self.s[i1] - self.s[i0]
        fr = np.where(span > 0, (s_query - self.s[i0]) / np.where(span > 0, span, 1.0), 0.0)
        return i0 + np.clip(fr, 0.0, 1.0)

    def _frac_rows(self, f: np.ndarray, s_vals: np.ndarray, offset: np.ndarray):
        """Rows and unit normals at fractional positions ``f``, ``offset`` (m) out
        from the mandrel along its normal (on the mandrel's exact shape)."""
        f = np.asarray(f, dtype=float)
        x0, z0, nx, nz = self._template_at(f)
        offset = np.broadcast_to(np.asarray(offset, dtype=float), f.shape)
        x = x0 + offset * nx
        z = z0 + offset * nz
        rows = np.empty((f.shape[0], N_COLS))
        rows[:, THETA_COL] = self.theta(f)
        rows[:, X_UNWRAPPED_COL] = np.asarray(s_vals, dtype=float) + self.profile.x_origin
        if self.template.kind == "round":
            rows[:, RADIUS_COL] = self.template.radius + offset
        else:
            rows[:, RADIUS_COL] = np.hypot(x, z)
        rows[:, X_COORD_COL] = x
        rows[:, Z_COORD_COL] = z
        rows[:, TURNS_COL] = f / self.points_per_turn
        return rows, np.column_stack((nx, nz))

    def _sample_rows(self, lo: int, hi: int, extra: np.ndarray):
        """Rows and normals at samples ``lo..hi-1`` (no interpolation needed)."""
        t = self.template
        return _gather_rows(
            t.x, t.z, t.nx, t.nz, self.a, self.s, lo, hi,
            np.ascontiguousarray(extra, dtype=float), self.profile.x_origin,
            t.kind == "round", float(t.radius),
        )

    def sample(self, s_query: np.ndarray, extra_offset: np.ndarray) -> np.ndarray:
        """Wound-path rows at arc lengths ``s_query``, ``extra_offset`` above the
        strip's bottom face. Columns as :data:`THETA_COL` ... :data:`TURNS_COL`
        (turns from the strip's start; ``x_unwrapped`` in laminate x)."""
        s_query = np.asarray(s_query, dtype=float)
        f = self._index_at(s_query)
        rows, _ = self._frac_rows(f, s_query, self._interp(self.a, f) + extra_offset)
        return rows

    # ---- corners the strip bends over --------------------------------------
    def _bends(self, lo: float, hi: float):
        """Where a turn bends over a step in the turn beneath (a stack-top corner
        it rests on), within fractional positions ``(lo, hi)``: the positions and
        the strip's bottom-face offset there."""
        if self.corner_f.size == 0:
            return np.empty(0), np.empty(0)
        p = self.points_per_turn
        f_up = self.corner_f + p
        keep = (f_up > lo) & (f_up < hi) & (f_up < self.a.shape[0] - 1)
        if not np.any(keep):
            return np.empty(0), np.empty(0)
        f_up = f_up[keep]
        a_corner = self._interp(self.a, self.corner_f[keep]) + self.corner_h[keep]
        touching = a_corner > self._interp(self.a, f_up) + _CORNER_TOL
        return f_up[touching], a_corner[touching]

    @staticmethod
    def _merge(body, extras):
        """Sample rows ``body = (f, rows, normals)`` with a few ``extras`` parts
        inserted in order of position (an extra goes before a sample at its
        position; extras keep their order among themselves)."""
        f_b, rows, normals = body
        extras = [part for part in extras if part[0].shape[0]]
        if not extras:
            return rows, normals
        f_x = np.concatenate([part[0] for part in extras])
        order = np.argsort(f_x, kind="stable")
        at = np.searchsorted(f_b, f_x[order], side="left")
        x_rows = np.vstack([part[1] for part in extras])[order]
        x_normals = None if normals is None else np.vstack([part[2] for part in extras])[order]
        cuts = np.concatenate(([0], at, [f_b.shape[0]]))
        rows_out, normals_out = [], []
        for k in range(at.shape[0] + 1):
            rows_out.append(rows[cuts[k] : cuts[k + 1]])
            if normals is not None:
                normals_out.append(normals[cuts[k] : cuts[k + 1]])
            if k < at.shape[0]:
                rows_out.append(x_rows[k : k + 1])
                if normals is not None:
                    normals_out.append(x_normals[k : k + 1])
        return (
            np.concatenate(rows_out),
            None if normals is None else np.concatenate(normals_out),
        )

    # ---- the strip's base path ---------------------------------------------
    def base_path(self) -> np.ndarray:
        """The laminate's bottom-face path, ending exactly at the strip's end."""
        n_in = int(np.searchsorted(self.s, self.strip_length, side="left"))
        body, body_n = self._sample_rows(0, n_in, np.zeros(n_in))
        f_end = np.array([self._edge_position(self.profile.thickness.shape[0])])
        end, end_n = self._frac_rows(
            f_end, np.array([self.strip_length]), self._interp(self.a, f_end)
        )
        f_b, a_b = self._bends(0.0, float(f_end[0]))
        if f_b.size:
            bend, bend_n = self._frac_rows(f_b, self._interp(self.s, f_b), a_b)
            rows, _ = self._merge((np.arange(n_in, dtype=float), body, None), [(f_b, bend, bend_n)])
        else:
            rows = body
        return np.vstack((rows, end))

    # ---- components ----------------------------------------------------------
    def _edge_position(self, k: int) -> float:
        f = self.edge_f[k] if k < self.edge_f.shape[0] else np.nan
        if np.isnan(f):
            f = float(self._index_at(np.array([self.edges[k]]))[0])
        return float(f)

    def layer_bottom(self, c: int) -> np.ndarray:
        """Layer ``c``'s bottom face above the strip's bottom face at each sample
        (m; NaN where the layer is absent)."""
        profile = self.profile
        m = profile.thickness.shape[0]
        out = np.full(self.a.shape[0], np.nan)
        inside = self.iv < m
        out[inside] = profile.offset[c, self.iv[inside]] - profile.layer_thickness[c] / 2
        win = self.inwin.astype(bool)
        out[win] = self.off[c, win]
        return out

    def _edge_bottom(self, c: int, k: int) -> float:
        value = self.edge_bot[c, k] if k < self.edge_bot.shape[1] else np.nan
        if np.isnan(value):
            profile = self.profile
            m = profile.thickness.shape[0]
            for j in (k, k - 1):  # the side the layer is on
                if 0 <= j < m and profile.present[c, j]:
                    return float(profile.offset[c, j] - profile.layer_thickness[c] / 2)
            return 0.0
        return float(value)

    def layer_path(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        """A layer's centre-line path and its outward normals.

        One NaN row separates the layer's segments. Every segment ends exactly at
        the layer's end; where a layer beneath it starts or stops the path bends
        over the step (one row at the edge) instead of jumping.
        """
        profile = self.profile
        c = profile.names.index(name)
        half = profile.layer_thickness[c] / 2
        bottom = self.layer_bottom(c)
        rows, normals = [], []
        nan_row = np.full((1, N_COLS), np.nan)
        nan_n = np.full((1, 2), np.nan)
        for s0, s1 in profile.segments[name]:
            k0 = int(np.argmin(np.abs(profile.edges - s0)))
            k1 = int(np.argmin(np.abs(profile.edges - s1)))
            lo = int(np.searchsorted(self.s, s0, side="right"))
            hi = max(int(np.searchsorted(self.s, s1, side="left")), lo)
            body_extra = bottom[lo:hi] + half
            body_extra = np.where(np.isnan(body_extra), half, body_extra)
            body, body_n = self._sample_rows(lo, hi, body_extra)

            ks = np.arange(k0, k1 + 1)
            f_e = np.array([self._edge_position(k) for k in ks])
            b_e = np.array([self._edge_bottom(c, k) for k in ks])
            edge, edge_n = self._frac_rows(
                f_e, profile.edges[ks], self._interp(self.a, f_e) + b_e + half
            )

            f_b, a_b = self._bends(float(f_e[0]), float(f_e[-1]))
            b_b = self._interp(np.where(np.isnan(bottom), 0.0, bottom), f_b)
            bend, bend_n = self._frac_rows(f_b, self._interp(self.s, f_b), a_b + b_b + half)

            seg, seg_n = self._merge(
                (np.arange(lo, hi, dtype=float), body, body_n),
                [(f_e, edge, edge_n), (f_b, bend, bend_n)],
            )
            rows += [seg, nan_row]
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
        f0 = self._edge_position(self.profile.thickness.shape[0])
        f1 = float(self._index_at(np.array([self.total_length]))[0])
        lo = int(np.searchsorted(self.s, self.strip_length, side="right"))
        hi = max(int(np.searchsorted(self.s, self.total_length, side="left")), lo)
        body, body_n = self._sample_rows(lo, hi, np.full(hi - lo, half))
        f_ends = np.array([f0, f1])
        ends, ends_n = self._frac_rows(
            f_ends, np.array([self.strip_length, self.total_length]),
            self._interp(self.a, f_ends) + half,
        )
        f_b, a_b = self._bends(f0, f1)
        bend, bend_n = self._frac_rows(f_b, self._interp(self.s, f_b), a_b + half)
        path, normals = self._merge(
            (np.arange(lo, hi, dtype=float), body, body_n),
            [(f_ends[:1], ends[:1], ends_n[:1]), (f_b, bend, bend_n)],
        )
        path = np.vstack((path, ends[1:]))
        normals = np.vstack((normals, ends_n[1:]))
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
        top = self.a[idx] + self.H[idx]
        pts = [np.column_stack((x + top * nx, z + top * nz))]
        f_end = self._index_at(np.array([end_s]))
        end_row, _ = self._frac_rows(
            f_end, np.array([end_s]), self._interp(self.a, f_end) + self._end_height()
        )
        pts.append(end_row[:, [X_COORD_COL, Z_COORD_COL]])
        if n < p:  # less than one turn: the bare mandrel bounds the rest
            pts.append(np.column_stack((self.template.x, self.template.z)))
        return np.vstack(pts)

    def _end_height(self) -> float:
        """The stack-top height just before the wound material's end."""
        if self.tape_thickness > 0 and self.total_length > self.strip_length:
            return float(self.tape_thickness)
        profile = self.profile
        m = profile.thickness.shape[0]
        if m == 0:
            return 0.0
        tops = [
            self._edge_bottom(c, m) + profile.layer_thickness[c]
            for c in range(len(profile.names))
            if profile.present[c, m - 1]
        ]
        return float(max(tops)) if tops else float(profile.thickness[m - 1])


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
    n_strip = int(thick.shape[0])
    present = np.ascontiguousarray(profile.present, dtype=np.bool_)
    layer_t = np.ascontiguousarray(profile.layer_thickness, dtype=np.float64)
    if present.shape[0] != layer_t.shape[0] or present.ndim != 2:
        present = np.zeros((0, max(n_strip, 1)), dtype=np.bool_)
        layer_t = np.zeros(0)
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
        n_strip = 0
    cum = np.concatenate(([0.0], np.cumsum(thick * np.diff(edges))))

    if n_after >= 0:  # wraps: the strip, then a counted number of samples
        max_n = _max_samples(template, edges[:-1], thick[:-1], n_after)
    else:
        max_n = _max_samples(template, edges, thick, 0)
    is_round = template.kind == "round"
    for _ in range(6):
        out = _wind_taut(
            template.x, template.z, template.nx, template.nz,
            is_round, float(template.radius), float(template.straight) / 2.0,
            float(template.straight), int(template.n_curve), int(template.n_straight),
            edges, thick, cum, present, layer_t, n_strip,
            strip_length, s_stop, n_after, ARC_REFERENCE, max_n,
        )
        (a, s, tc, H, iv, inwin, off, edge_bot, edge_f, corner_f, corner_h,
         i_strip, n, overflow) = out
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
        H=H.copy(),
        iv=iv.copy(),
        inwin=inwin.copy(),
        off=off,
        edges=edges,
        edge_bot=edge_bot,
        edge_f=edge_f,
        corner_f=corner_f.copy(),
        corner_h=corner_h.copy(),
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
