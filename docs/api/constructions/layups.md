# Layups

A layup defines how electrodes and separators are arranged into a repeating unit. Layups handle N/P ratio control, electrode overhang, and areal capacity curve computation.

| Type | Description | Typical Use |
|---|---|---|
| `Laminate` | Two separators sandwiching cathode and anode | Wound cells |
| `MonoLayer` | Single separator between cathode and anode | Stacked cells |
| `ZFoldMonoLayer` | Z-fold separator variant | Z-fold stacks |

---

## Control Modes & Enums

::: steer_opencell_design.Constructions.Layups.Base
    options:
      members_order: source
      show_root_heading: true

---

## Overhang Utilities

::: steer_opencell_design.Constructions.Layups.OverhangUtils
    options:
      members_order: source
      show_root_heading: true

---

## Laminate

Two-separator layup for wound cells.

::: steer_opencell_design.Constructions.Layups.Laminate
    options:
      members_order: source
      show_root_heading: true

---

## Mono Layers

Single-separator layups for stacked cells.

::: steer_opencell_design.Constructions.Layups.MonoLayers
    options:
      members_order: source
      show_root_heading: true

---

## Areal Capacity Curve Utilities

::: steer_opencell_design.Constructions.Layups.ArealCapacityCurveUtils
    options:
      members_order: source
      show_root_heading: true
