# Electrode Assemblies — Design Notes

This document describes the internal architecture and key algorithms of the
`ElectrodeAssemblies` module, intended for developers working on or extending
the jelly roll and stack assembly code.

## Module Overview

```
ElectrodeAssemblies/
├── Base.py             # _ElectrodeAssembly — abstract base class
├── JellyRolls.py       # WoundJellyRoll, FlatWoundJellyRoll (~4000 lines)
├── SpiralUtils.py      # SpiralCalculator — static geometry methods
├── Stacks.py           # ZFoldStack, PunchedStack
├── Tape.py             # Termination tape
└── WindingEquipment.py  # RoundMandrel, FlatMandrel
```

### Class Hierarchy

```
_ElectrodeAssembly (ABC)
├── _JellyRoll (ABC)
│   ├── WoundJellyRoll      — round spiral winding
│   └── FlatWoundJellyRoll   — racetrack (flat) winding
└── _Stack (ABC)
    ├── ZFoldStack           — z-fold separator stacking
    └── PunchedStack         — punched electrode stacking
```

## Jelly Roll Geometry

### Spiral Calculation

The core geometric algorithm is in `SpiralCalculator.calculate_variable_thickness_spiral()`.
It integrates a **variable-thickness Archimedean-like spiral** using adaptive 4th-order
Runge–Kutta (RK4) integration.

**Governing equations** (parametrized by θ, clockwise):

```
dr/dθ     = t(x) / (2π)
ds/dθ     = √(r² + (dr/dθ)²)       — local arc-length rate
dx/dθ     = ds/dθ                    — unwrapped length as accumulated arc
```

where `t(x)` is the spatially varying laminate thickness at unwrapped position `x`,
provided by `laminate.get_thickness_at_x(x)`. This accounts for the fact that the
electrode stack has different thicknesses at different positions (e.g., bare foil
regions are thinner than double-coated regions).

**Key features:**
- Adaptive step sizing via Richardson error estimation
- Automatic fallback to analytic uniform-thickness when variation is negligible
- Gradient-aware minimum step to capture rapid thickness changes
- Early termination with endpoint interpolation for exact length landing

### Spiral Data Format

All spirals are stored as NumPy arrays with 6 columns:

| Column Index | Constant      | Meaning                          |
|-------------|---------------|----------------------------------|
| 0           | `THETA_COL`   | Angular position (radians)       |
| 1           | `X_UNWRAPPED_COL` | Unwrapped arc length (m)    |
| 2           | `RADIUS_COL`  | Radial position (m)              |
| 3           | `X_COORD_COL` | Cartesian x coordinate (m)       |
| 4           | `Z_COORD_COL` | Cartesian z coordinate (m)       |
| 5           | `TURNS_COL`   | Cumulative turn count            |

### Round vs Flat Winding

- **`WoundJellyRoll`** uses `calculate_variable_thickness_spiral()` and `build_component_spirals()` for purely circular winding around a `RoundMandrel`.

- **`FlatWoundJellyRoll`** uses `calculate_variable_thickness_racetrack()` and `build_component_racetracks()` for racetrack (oval) winding around a `FlatMandrel`. The racetrack geometry has straight sections connected by semicircular ends, with the mandrel's width determining the length of the straight sections.

### Component Spiral Building

After the base spiral is computed, `build_component_spirals()` splits it into
per-component segments (cathode, anode, top separator, bottom separator,
cathode current collector, anode current collector) by mapping the unwrapped
position to the laminate's layer boundaries.

`build_extruded_component_spirals()` then extrudes each component spiral
radially by its thickness, producing inner/outer boundary curves used for
cross-section visualization.

### Tape Handling

Termination tape wraps are added after the electrode winding:

- **`TapeDriver.JELLY_ROLL_DRIVEN`**: User specifies `additional_tape_wraps`; tape length is calculated.
- **`TapeDriver.TAPE_DRIVEN`**: User specifies `tape.length`; additional wraps are back-calculated.

The tape spiral is built on top of the outermost electrode layer and contributes
to the overall jelly roll radius and mass.

### Tab Crumple Factor

For tabbed current collectors (`TabWeldedCurrentCollector`), the `collector_tab_crumple_factor`
(0–100%) controls how much the welded tabs compress radially when wound. At 100%,
tabs add no thickness; at 0%, tabs add their full height to the winding radius.

## Stack Assembly

Stacks are simpler than jelly rolls — they layer `MonoLayer` or `ZFoldMonoLayer`
units vertically:

- **`PunchedStack`**: Each layer is a discrete punched monolayer stacked on top of the previous one.
- **`ZFoldStack`**: A continuous separator is z-folded between electrode pairs, with configurable `additional_separator_wraps`.

The stack's `n_layers` property controls how many repeat units are stacked,
and `thickness` is computed from the sum of individual layer thicknesses.

## Property Recalculation Pattern

All assemblies use a decorator-driven recalculation pattern:

1. **`@calculate_all_properties`** — triggers full recalculation of geometry, spirals, and derived values
2. **`@calculate_bulk_properties`** — recalculates only mass, cost, and volume (skips geometry)
3. **`@calculate_tape_properties`** — recalculates tape-related geometry (jelly rolls only)
4. **`@calculate_coordinates`** — rebuilds visualization coordinates

Recalculation is gated by `self._update_properties`. When constructing objects
with `_update_properties=False`, you can batch multiple parameter changes before
triggering a single recalculation.

## Internal Unit Conventions

All internal calculations use SI units (meters, kilograms, etc.). User-facing
properties convert to conventional units:

| Internal (SI)  | User-facing           |
|---------------|-----------------------|
| m             | mm (lengths)          |
| m             | μm (thicknesses)      |
| m²            | cm² (areas)           |
| m³            | cm³ (volumes)         |
| kg            | g (masses)            |
| $/kg          | $/kg (costs)          |

## Visualization

Both jelly rolls and stacks provide Plotly-based views:

- **`get_top_down_view()`** — plan view showing spiral windings or stacked layers
- **`get_cross_section()`** / **`get_side_view()`** — cross-section showing layer geometry
- **`get_capacity_plot()`** — voltage–capacity curves (inherited from `_ElectrodeAssembly`)
- **`plot_mass_breakdown()`** / **`plot_cost_breakdown()`** — sunburst charts

Spiral visualization uses extruded component spirals to render filled polygons
in Plotly, color-coded by component type.
