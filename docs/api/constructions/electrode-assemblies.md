# Electrode Assemblies

Electrode assemblies combine layups into a three-dimensional structure. Two families are supported:

| Type | Description | Cell Format |
|---|---|---|
| `WoundJellyRoll` | Round wound jelly roll | Cylindrical |
| `FlatWoundJellyRoll` | Flat (racetrack) wound jelly roll | Prismatic |
| `PunchedStack` | Punched and stacked electrodes | Prismatic, Pouch, Flex-frame |
| `ZFoldStack` | Z-fold separator with stacked electrodes | Prismatic, Pouch |

---

## Jelly Rolls

Wound electrode assemblies for cylindrical and flat-wound prismatic cells.

::: steer_opencell_design.Constructions.ElectrodeAssemblies.JellyRolls
    options:
      members_order: source
      show_root_heading: true

---

## Stacks

Stacked electrode assemblies for prismatic, pouch, and flex-frame cells.

::: steer_opencell_design.Constructions.ElectrodeAssemblies.Stacks
    options:
      members_order: source
      show_root_heading: true

---

## Tape

Termination tape used to secure wound assemblies.

::: steer_opencell_design.Constructions.ElectrodeAssemblies.Tape
    options:
      members_order: source
      show_root_heading: true

---

## Winding Equipment

Mandrel geometry for jelly roll winding.

::: steer_opencell_design.Constructions.ElectrodeAssemblies.WindingEquipment
    options:
      members_order: source
      show_root_heading: true

---

## Spiral Utilities

Low-level functions for spiral geometry calculations.

::: steer_opencell_design.Constructions.ElectrodeAssemblies.SpiralUtils
    options:
      members_order: source
      show_root_heading: true
