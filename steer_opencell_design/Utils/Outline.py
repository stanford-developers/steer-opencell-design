# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Simple 3D outlines of cells: a box or a low-poly cylinder as one triangle mesh.

These are for drawing many cells at pack or container scale, where the detailed
layer-by-layer views are far too heavy. A cell's outline is described in its own
frame by ``(width, height, thickness)`` in mm (local axes 0, 1, 2), and placed in the
world by a ``datum`` (the centre of its bounding box) and an ``orientation``.

``orientation`` is a permutation of ``"xyz"``: its k-th letter is the world axis that
local axis k points along. ``"xyz"`` is OpenCell's own frame (height along y);
``"xzy"`` stands the cell upright in a z-up world with its thickness along y.

The returned arrays are ``(x, y, z, i, j, k)``: vertex coordinates (float64, mm) and
0-based triangle vertex indices (int64), the arguments of a plotly ``Mesh3d``. Every
triangle winds counter-clockwise seen from outside, so normals point outward.

Vertex order (pinned by tests, so callers can merge many copies by offsetting
indices):

- box: 8 vertices, index ``bw + 2*bh + 4*bt`` with ``b`` 0 at the min and 1 at the
  max along each local axis; 12 triangles.
- cylinder (axis along local height): vertices ``0..n-1`` are the bottom ring,
  ``n..2n-1`` the top ring, ``2n`` and ``2n+1`` the bottom and top cap centres; ring
  vertex ``m`` sits at angle ``2*pi*m/n`` from local +width. ``4n`` triangles.
"""

from typing import Sequence, Tuple

import numpy as np

MeshArrays = Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]

OUTLINE_SHAPES = ("box", "cylinder")

# Box faces as (local axis, side) quads, each listed counter-clockwise seen from
# outside, then split into two triangles.
_BOX_QUADS = (
    (0, 4, 6, 2),  # width min (-w face)
    (1, 3, 7, 5),  # width max (+w face)
    (0, 1, 5, 4),  # height min
    (2, 6, 7, 3),  # height max
    (0, 2, 3, 1),  # thickness min
    (4, 5, 7, 6),  # thickness max
)


def _axis_permutation(orientation: str) -> Tuple[int, int, int]:
    """World axis index for each local axis, from an ``"xyz"`` permutation."""
    if not isinstance(orientation, str) or sorted(orientation.lower()) != ["x", "y", "z"]:
        raise ValueError(
            f"orientation must be a permutation of 'xyz' (e.g. 'xyz', 'xzy'), "
            f"got {orientation!r}"
        )
    return tuple("xyz".index(c) for c in orientation.lower())


def _flip_if_reflected(perm: Tuple[int, int, int], faces: np.ndarray) -> np.ndarray:
    """Re-wind triangles when the axis permutation is a reflection.

    An odd permutation of the axes mirrors the mesh, which turns counter-clockwise
    windings clockwise; swapping two vertices of every triangle restores outward
    normals.
    """
    inversions = sum(
        1 for a in range(3) for b in range(a + 1, 3) if perm[a] > perm[b]
    )
    if inversions % 2:
        return faces[:, [0, 2, 1]]
    return faces


def _place(local: np.ndarray, perm, datum) -> np.ndarray:
    world = np.empty_like(local)
    for axis_local, axis_world in enumerate(perm):
        world[:, axis_world] = local[:, axis_local]
    return world + np.asarray(datum, dtype=float)


def _box_local(dimensions: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
    half = np.asarray(dimensions, dtype=float) / 2.0
    idx = np.arange(8)
    bits = np.stack([(idx >> 0) & 1, (idx >> 1) & 1, (idx >> 2) & 1], axis=1)
    vertices = (bits * 2 - 1) * half
    faces = []
    for a, b, c, d in _BOX_QUADS:
        faces.append((a, b, c))
        faces.append((a, c, d))
    return vertices, np.asarray(faces, dtype=np.int64)


def _cylinder_local(dimensions: Sequence[float], n_sides: int) -> Tuple[np.ndarray, np.ndarray]:
    diameter, height, depth = (float(d) for d in dimensions)
    angles = 2.0 * np.pi * np.arange(n_sides) / n_sides
    ring_w = 0.5 * diameter * np.cos(angles)
    ring_t = 0.5 * depth * np.sin(angles)
    half_h = height / 2.0
    bottom = np.stack([ring_w, np.full(n_sides, -half_h), ring_t], axis=1)
    top = np.stack([ring_w, np.full(n_sides, half_h), ring_t], axis=1)
    centres = np.array([[0.0, -half_h, 0.0], [0.0, half_h, 0.0]])
    vertices = np.vstack([bottom, top, centres])

    m = np.arange(n_sides)
    nxt = (m + 1) % n_sides
    bc, tc = 2 * n_sides, 2 * n_sides + 1
    # Wound to face outward in the identity orientation; _flip_if_reflected keeps them
    # outward under mirroring permutations.
    sides_a = np.stack([m, n_sides + m, nxt], axis=1)
    sides_b = np.stack([nxt, n_sides + m, n_sides + nxt], axis=1)
    cap_bottom = np.stack([np.full(n_sides, bc), m, nxt], axis=1)
    cap_top = np.stack([np.full(n_sides, tc), n_sides + nxt, n_sides + m], axis=1)
    faces = np.vstack([sides_a, sides_b, cap_bottom, cap_top]).astype(np.int64)
    return vertices, faces


def outline_mesh(
    shape: str,
    dimensions: Sequence[float],
    datum: Sequence[float] = (0.0, 0.0, 0.0),
    orientation: str = "xyz",
    n_sides: int = 12,
) -> MeshArrays:
    """Build the outline mesh of a cell (see the module docstring for conventions).

    Args:
        shape: ``"box"`` or ``"cylinder"``.
        dimensions: ``(width, height, thickness)`` in mm, in the cell's frame. For a
            cylinder, width and thickness are both its diameter.
        datum: World position of the outline's bounding-box centre, mm.
        orientation: Permutation of ``"xyz"`` mapping local axes to world axes.
        n_sides: Polygon sides of a cylinder (ignored for a box), at least 3.

    Returns:
        ``(x, y, z, i, j, k)`` arrays for a plotly ``Mesh3d``.
    """
    if shape not in OUTLINE_SHAPES:
        raise ValueError(f"shape must be one of {OUTLINE_SHAPES}, got {shape!r}")
    dims = [float(d) for d in dimensions]
    if len(dims) != 3 or any(not np.isfinite(d) or d <= 0 for d in dims):
        raise ValueError(f"dimensions must be three positive numbers (mm), got {dimensions!r}")
    if len(tuple(datum)) != 3:
        raise ValueError(f"datum must be an (x, y, z) triple in mm, got {datum!r}")
    perm = _axis_permutation(orientation)

    if shape == "box":
        local, faces = _box_local(dims)
    else:
        if not isinstance(n_sides, (int, np.integer)) or isinstance(n_sides, bool) or n_sides < 3:
            raise ValueError(f"n_sides must be an integer of at least 3, got {n_sides!r}")
        local, faces = _cylinder_local(dims, int(n_sides))

    world = _place(local, perm, datum)
    faces = _flip_if_reflected(perm, faces)
    return world[:, 0], world[:, 1], world[:, 2], faces[:, 0], faces[:, 1], faces[:, 2]


def signed_volume(x, y, z, i, j, k) -> float:
    """Signed volume of a closed triangle mesh (positive when normals face outward)."""
    v = np.stack([x, y, z], axis=1)
    a, b, c = v[i], v[j], v[k]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
