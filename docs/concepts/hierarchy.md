# Modeling Hierarchy

The package is organized into four layers that mirror the physical structure of a battery cell:

```
Materials  →  Components  →  Constructions  →  Cells
```

## Layer Breakdown

### Materials

Raw materials and electrode formulations — the foundation of every cell.

| Class | Description |
|---|---|
| `CathodeMaterial` / `AnodeMaterial` | Active materials with half-cell voltage–capacity curves |
| `Binder` | Electrode binder materials (e.g., PVDF, CMC) |
| `ConductiveAdditive` | Conductive additives (e.g., carbon black, Super P) |
| `CathodeFormulation` / `AnodeFormulation` | Blended electrode formulations with weight fractions |
| `Electrolyte` | Liquid electrolyte materials |
| `SeparatorMaterial` | Separator base material with porosity |
| `CurrentCollectorMaterial` | Metal foil material for current collectors |
| `TapeMaterial` | Adhesive tape for winding termination |
| `InsulationMaterial` | Ceramic insulation coatings (e.g., Al₂O₃) |
| `PrismaticContainerMaterial` | Container housing materials |
| `LaminateMaterial` | Laminate pouch film materials |
| `FlexFrameMaterial` | Flex-frame housing materials |

### Components

Physical parts built from materials.

| Class | Description |
|---|---|
| `Cathode` / `Anode` | Electrodes combining a formulation, current collector, and coating parameters |
| `Separator` | Porous separator membrane |
| `NotchedCurrentCollector` | Notched foil for tabless wound cells |
| `TabWeldedCurrentCollector` | Foil with welded tab strips |
| `TablessCurrentCollector` | Continuous foil with edge connections |
| `PunchedCurrentCollector` | Punched foil with integral tabs for stacked cells |

### Constructions

Higher-level assemblies that combine components.

**Layups** define how electrode layers are arranged:

| Class | Description |
|---|---|
| `Laminate` | Two-separator layup for wound cells |
| `MonoLayer` | Single-separator layup for stacked cells |
| `ZFoldMonoLayer` | Z-fold separator variant |

**Electrode Assemblies** define how layups are formed into 3D structures:

| Class | Description |
|---|---|
| `WoundJellyRoll` | Cylindrical wound jelly roll |
| `FlatWoundJellyRoll` | Flat (racetrack) wound jelly roll |
| `ZFoldStack` | Z-fold stacked assembly |
| `PunchedStack` | Punched-and-stacked assembly |

### Cells

Complete battery cells that combine assemblies with encapsulation and electrolyte:

| Class | Cell Format |
|---|---|
| `CylindricalCell` | Cylindrical (e.g., 18650, 21700, 4680) |
| `PrismaticCell` | Prismatic hard-case |
| `PouchCell` | Pouch soft-pack |
| `FlexFrameCell` | Flex-frame (solid-state) |

## Object Tree

When fully assembled, a cell's internal object tree looks like this:

```
Cell
└── Electrode Assembly (JellyRoll or Stack)
    └── Layup (Laminate or MonoLayer)
        ├── Cathode
        │   ├── CathodeFormulation
        │   │   ├── CathodeMaterial(s)
        │   │   ├── Binder(s)
        │   │   └── ConductiveAdditive(s)
        │   └── CurrentCollector
        ├── Anode
        │   ├── AnodeFormulation
        │   │   ├── AnodeMaterial(s)
        │   │   ├── Binder(s)
        │   │   └── ConductiveAdditive(s)
        │   └── CurrentCollector
        └── Separator(s)
```

Every node in this tree exposes **settable properties** (e.g., mass loading, calender density, N/P ratio) and **computed read-only properties** (energy, mass, cost, breakdowns). See [Change Propagation](propagation.md) for how modifications flow through the hierarchy.
