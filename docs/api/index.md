# API Reference

All public classes are re-exported from the top-level namespace for convenience:

```python
import steer_opencell_design as ocd
cell = ocd.CylindricalCell(...)
```

The package is organized into three layers that mirror the battery cell modeling hierarchy:

---

## Materials

Raw material definitions and electrode formulations — the foundation of every cell.

| Page | Key Classes |
|---|---|
| [Active Materials](materials/active-materials.md) | `CathodeMaterial`, `AnodeMaterial` |
| [Binders](materials/binders.md) | `Binder` |
| [Conductive Additives](materials/conductive-additives.md) | `ConductiveAdditive` |
| [Electrolytes](materials/electrolytes.md) | `Electrolyte` |
| [Other Materials](materials/other.md) | `SeparatorMaterial`, `CurrentCollectorMaterial`, `TapeMaterial`, `InsulationMaterial`, `PrismaticContainerMaterial`, `LaminateMaterial`, `FlexFrameMaterial` |
| [Formulations](materials/formulations.md) | `CathodeFormulation`, `AnodeFormulation` |

## Components

Physical parts built from materials.

| Page | Key Classes |
|---|---|
| [Electrodes](components/electrodes.md) | `Cathode`, `Anode` |
| [Separators](components/separators.md) | `Separator` |
| [Current Collectors](components/current-collectors.md) | `NotchedCurrentCollector`, `TabWeldedCurrentCollector`, `PunchedCurrentCollector`, `TablessCurrentCollector` |
| [Containers](components/containers.md) | `CylindricalCanister`, `PrismaticCanister`, `PouchEncapsulation`, `FlexFrameEncapsulation`, ... |

## Constructions

Higher-level assemblies and complete cells.

| Page | Key Classes |
|---|---|
| [Layups](constructions/layups.md) | `Laminate`, `MonoLayer`, `ZFoldMonoLayer` |
| [Electrode Assemblies](constructions/electrode-assemblies.md) | `WoundJellyRoll`, `FlatWoundJellyRoll`, `PunchedStack`, `ZFoldStack` |
| [Cells](constructions/cells.md) | `CylindricalCell`, `PrismaticCell`, `PouchCell`, `FlexFrameCell` |

## Utilities

| Page | Contents |
|---|---|
| [Utilities](utils.md) | Decorators and helper functions |
