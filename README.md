# steer-opencell-design

A Python package for designing and modeling lithium-ion and sodium-ion battery cells. Part of the [STEER](https://github.com/stanford-developers) platform, `steer-opencell-design` provides a hierarchical, composable API for building virtual battery cells from raw materials up to complete cell assemblies, with built-in cost, mass, and electrochemical performance calculations.

## Features

- **Hierarchical cell modeling** — compose cells from materials → formulations → electrodes → assemblies → complete cells
- **Multiple cell formats** — cylindrical, prismatic, pouch, and flex-frame cell architectures
- **Multiple assembly types** — wound jelly rolls (round and flat), z-fold stacks, and punched stacks
- **Electrochemical curves** — half-cell voltage–capacity curves are combined into full-cell curves with N/P ratio control
- **Cost and mass breakdowns** — automatic roll-up of cost and mass from component level to cell level
- **Interactive visualization** — Plotly-based cross-sections, top-down views, capacity plots, and sunburst breakdowns
- **Serialization** — serialize and deserialize full cell configurations for storage and sharing
- **Database integration** — load reference materials and cell designs from the built-in database

## Installation

```bash
pip install steer-opencell-design
```

Requires Python >= 3.10. Dependencies (`steer-core`, `steer-materials`, `steer-opencell-data`) are installed automatically.

## Quickstart

The following example builds a complete cylindrical cell from scratch. The workflow follows the natural hierarchy: **Materials → Formulations → Electrodes → Layup → Assembly → Cell**.

```python
import steer_opencell_design as ocd

# ── 1. Materials ──────────────────────────────────────────────────

# Load active materials from the built-in database
cathode_active = ocd.CathodeMaterial.from_database("LFP")
cathode_active.specific_cost = 6      # $/kg
cathode_active.density = 3.6          # g/cm³

anode_active = ocd.AnodeMaterial.from_database("Synthetic Graphite")
anode_active.specific_cost = 4
anode_active.density = 2.2

# Create auxiliary materials
conductive_additive = ocd.ConductiveAdditive(
    name="Super P", specific_cost=15, density=2.0, color="#000000"
)
binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

# ── 2. Formulations ──────────────────────────────────────────────

cathode_formulation = ocd.CathodeFormulation(
    active_materials={cathode_active: 95},     # weight %
    binders={binder: 2},
    conductive_additives={conductive_additive: 3},
)

anode_formulation = ocd.AnodeFormulation(
    active_materials={anode_active: 90},
    binders={binder: 5},
    conductive_additives={conductive_additive: 5},
)

# ── 3. Current Collectors ────────────────────────────────────────

cc_material = ocd.CurrentCollectorMaterial(
    name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
)

cathode_cc = ocd.NotchedCurrentCollector(
    material=cc_material,
    length=4500,          # mm
    width=300,            # mm
    thickness=8,          # μm
    tab_width=60,         # mm
    tab_spacing=200,      # mm
    tab_height=18,        # mm
    insulation_width=6,   # mm
    coated_tab_height=2,  # mm
)

anode_cc = ocd.NotchedCurrentCollector(
    material=cc_material,
    length=4500, width=306, thickness=8,
    tab_width=60, tab_spacing=100, tab_height=18,
    insulation_width=6, coated_tab_height=2,
)

# ── 4. Electrodes ────────────────────────────────────────────────

insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

cathode = ocd.Cathode(
    formulation=cathode_formulation,
    mass_loading=12,              # mg/cm²
    current_collector=cathode_cc,
    calender_density=2.60,        # g/cm³
    insulation_material=insulation,
    insulation_thickness=10,      # μm
)

anode = ocd.Anode(
    formulation=anode_formulation,
    mass_loading=7.2,
    current_collector=anode_cc,
    calender_density=1.1,
    insulation_material=insulation,
    insulation_thickness=10,
)

# ── 5. Separator & Layup ─────────────────────────────────────────

separator_material = ocd.SeparatorMaterial(
    name="Polyethylene", specific_cost=2, density=0.94,
    color="#FDFDB7", porosity=45,   # %
)

top_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=5000)
bottom_separator = ocd.Separator(material=separator_material, thickness=25, width=310, length=7000)

layup = ocd.Laminate(
    anode=anode, cathode=cathode,
    top_separator=top_separator, bottom_separator=bottom_separator,
)

# ── 6. Electrode Assembly ────────────────────────────────────────

mandrel = ocd.RoundMandrel(diameter=5, length=350)

tape_material = ocd.TapeMaterial.from_database("Kapton")
tape_material.density = 1.42
tape_material.specific_cost = 70
tape = ocd.Tape(material=tape_material, thickness=30)

jellyroll = ocd.WoundJellyRoll(
    laminate=layup, mandrel=mandrel,
    tape=tape, additional_tape_wraps=5,
)

# ── 7. Encapsulation ─────────────────────────────────────────────

aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
copper = ocd.PrismaticContainerMaterial.from_database("Copper")

encapsulation = ocd.CylindricalEncapsulation(
    cathode_terminal_connector=ocd.CylindricalTerminalConnector(material=aluminum, thickness=2, fill_factor=0.8),
    anode_terminal_connector=ocd.CylindricalTerminalConnector(material=copper, thickness=3, fill_factor=0.7),
    lid_assembly=ocd.CylindricalLidAssembly(material=aluminum, thickness=4.0, fill_factor=0.9),
    canister=ocd.CylindricalCanister(material=aluminum, outer_radius=21.4, height=330, wall_thickness=0.5),
)

# ── 8. Electrolyte & Cell ────────────────────────────────────────

electrolyte = ocd.Electrolyte(
    name="1M LiPF6 in EC:DMC (1:1)",
    density=1.2, specific_cost=15.0, color="#00FF00",
)

cell = ocd.CylindricalCell(
    reference_electrode_assembly=jellyroll,
    encapsulation=encapsulation,
    electrolyte=electrolyte,
    electrolyte_overfill=20,  # %
)

# ── 9. Inspect Results ───────────────────────────────────────────

print(f"Energy:            {cell.energy} Wh")
print(f"Mass:              {cell.mass} g")
print(f"Specific energy:   {cell.specific_energy} Wh/kg")
print(f"Volumetric energy: {cell.volumetric_energy} Wh/L")
print(f"Cost per energy:   {cell.cost_per_energy} $/kWh")

# Visualize
cell.get_cross_section().show()
cell.get_capacity_plot().show()
cell.plot_mass_breakdown().show()
cell.plot_cost_breakdown().show()
```

## Package Overview

The package is organized into four layers that mirror the physical hierarchy of a battery cell:

```
Materials  →  Components  →  Constructions  →  Cells
```

### Materials (`steer_opencell_design.Materials`)

Raw materials and electrode formulations.

| Class | Description |
|---|---|
| `CathodeMaterial` / `AnodeMaterial` | Active materials with half-cell voltage–capacity curves |
| `Binder` | Electrode binder materials (e.g., PVDF, CMC) |
| `ConductiveAdditive` | Conductive additives (e.g., carbon black, Super P) |
| `CathodeFormulation` / `AnodeFormulation` | Blended electrode formulations with weight fractions |
| `Electrolyte` | Liquid electrolyte materials |
| `SeparatorMaterial` | Separator base material with porosity |
| `CurrentCollectorMaterial` | Metal foil material for current collectors |
| `TapeMaterial` | Adhesive tape material for winding termination |
| `InsulationMaterial` | Ceramic insulation coatings (e.g., Al₂O₃) |
| `PrismaticContainerMaterial` | Container housing materials (aluminum, steel) |
| `LaminateMaterial` | Laminate pouch film materials |
| `FlexFrameMaterial` | Flex-frame housing materials (e.g., PEEK) |

Most materials can be loaded from the built-in database:

```python
material = ocd.CathodeMaterial.from_database("NMC811")
binder = ocd.Binder.from_database("PVDF")
```

### Components (`steer_opencell_design.Components`)

Physical parts that make up a cell.

**Electrodes:**

| Class | Description |
|---|---|
| `Cathode` / `Anode` | Complete electrodes with formulation, current collector, and coating parameters |

**Current Collectors:**

| Class | Description |
|---|---|
| `NotchedCurrentCollector` | Notched foil for tabless wound cells |
| `TabWeldedCurrentCollector` | Foil with welded tab strips at specified positions |
| `TablessCurrentCollector` | Continuous foil with edge-based connections |
| `PunchedCurrentCollector` | Punched foil with integral tabs for stacked cells |

**Separators:**

| Class | Description |
|---|---|
| `Separator` | Porous separator membrane |

**Containers:**

| Class | Description |
|---|---|
| `CylindricalCanister`, `CylindricalLidAssembly`, `CylindricalTerminalConnector`, `CylindricalEncapsulation` | Cylindrical can components |
| `PrismaticCanister`, `PrismaticLidAssembly`, `PrismaticTerminalConnector`, `PrismaticEncapsulation` | Prismatic housing components |
| `PouchEncapsulation`, `LaminateSheet`, `PouchTerminal` | Pouch film components |
| `FlexFrame`, `FlexFrameEncapsulation` | Flex-frame housing components |

### Constructions (`steer_opencell_design.Constructions`)

Higher-level assemblies that combine components.

**Layups** — define how electrode layers are arranged:

| Class | Description |
|---|---|
| `Laminate` | Two-separator layup for wound cells (top + bottom separator sandwiching cathode and anode) |
| `MonoLayer` | Single-separator layup for stacked cells |
| `ZFoldMonoLayer` | Z-fold separator variant of MonoLayer |

**Electrode Assemblies** — define how layups are assembled:

| Class | Description |
|---|---|
| `WoundJellyRoll` | Cylindrical (round) wound jelly roll |
| `FlatWoundJellyRoll` | Flat (racetrack) wound jelly roll for prismatic cells |
| `ZFoldStack` | Z-fold stacked electrode assembly |
| `PunchedStack` | Punched/stacked electrode assembly |

**Cells** — complete battery cells:

| Class | Description |
|---|---|
| `CylindricalCell` | Cylindrical cell (e.g., 18650, 21700, 4680) |
| `PrismaticCell` | Prismatic hard-case cell |
| `PouchCell` | Pouch (soft-pack) cell |
| `FlexFrameCell` | Flex-frame cell for solid-state designs |

### Utilities

| Class/Function | Description |
|---|---|
| `NPRatioControlMode` | Enum controlling how N/P ratio adjustments propagate |
| `OverhangControlMode` | Enum controlling electrode overhang behavior |
| `RoundMandrel` / `FlatMandrel` | Winding mandrel geometry for jelly roll assembly |
| `Tape` | Termination tape for wound assemblies |

## Units Convention

| Quantity | Unit |
|---|---|
| Length, width, height | mm |
| Thickness (coatings, foils, separators, tapes) | μm |
| Mass loading | mg/cm² |
| Density | g/cm³ |
| Specific cost | $/kg |
| Porosity, weight fractions | % |
| Energy | Wh |
| Mass (cell-level) | g |
| Cost (cell-level) | $ |
| Specific energy | Wh/kg |
| Volumetric energy density | Wh/L |
| Cost per energy | $/kWh |

## Propagating Changes Through the Hierarchy

`steer-opencell-design` uses a hierarchical object model where child components are nested inside parent components:

```
Cell
└── ElectrodeAssembly (JellyRoll, Stack)
    └── Layup (Laminate, MonoLayer)
        ├── Cathode
        │   ├── Formulation
        │   │   └── ActiveMaterials, Binders, etc.
        │   └── CurrentCollector
        ├── Anode
        │   ├── Formulation
        │   └── CurrentCollector
        └── Separators
```

When you modify a property deep in the hierarchy (e.g., changing the cathode's mass loading), parent objects need to recalculate their derived properties. There are two methods to handle this:

### Method 1: `propagate_changes()` (Recommended)

The simplest approach is to modify the property and then call `propagate_changes()` on that object. This bubbles the recalculation up through all parent objects automatically:

```python
# Modify a property low in the hierarchy
cell.reference_electrode_assembly.layup.cathode.mass_loading = 15

# Propagate changes up to the cell level
cell.reference_electrode_assembly.layup.cathode.propagate_changes()

# Now the cell's energy, mass, cost, etc. are all updated
print(cell.energy)  # Reflects the new mass loading
```

You can call `propagate_changes()` from any level in the hierarchy:

```python
# Modify current collector thickness
cell.reference_electrode_assembly.layup.cathode.current_collector.thickness = 12

# Propagate from the current collector level - goes through:
# CurrentCollector → Cathode → Layup → JellyRoll → Cell
cell.reference_electrode_assembly.layup.cathode.current_collector.propagate_changes()
```

### Method 2: `update()` (Single Level)

If you only need to recalculate a single object without propagating to parents, use `update()`:

```python
# Recalculate just the cathode's properties
cathode.update()
```

This is useful when making multiple changes before triggering a full recalculation, or when working with standalone components not yet attached to a parent.

### Method 3: Re-assignment (Manual Propagation)

You can also trigger recalculation by re-assigning each component through its parent's setter:

```python
# Modify the active material
cell.reference_electrode_assembly.layup.cathode.formulation.active_material_1 = new_material

# Propagate changes up the hierarchy by re-assigning each level
cell.reference_electrode_assembly.layup.cathode.formulation = (
    cell.reference_electrode_assembly.layup.cathode.formulation
)
cell.reference_electrode_assembly.layup.cathode = (
    cell.reference_electrode_assembly.layup.cathode
)
cell.reference_electrode_assembly.layup = (
    cell.reference_electrode_assembly.layup
)
cell.reference_electrode_assembly = (
    cell.reference_electrode_assembly
)
```

This approach gives you explicit control but is more verbose. The `propagate_changes()` method is generally preferred.

### After Deserialization

When loading a cell from serialized data or a database, parent references may not be established automatically. The `propagate_changes()` method still works - it simply stops at the first level without a parent. To ensure full propagation after deserialization, changes will propagate correctly as you access and modify nested components.

```python
# Load from database
cell = ocd.CylindricalCell.from_database(table_name="cell_references", name="My Cell")

# Modify and propagate - works correctly
cell.reference_electrode_assembly.layup.cathode.mass_loading = 14
cell.reference_electrode_assembly.layup.cathode.propagate_changes()
```

## Serialization

Cells can be serialized and deserialized for storage:

```python
# Save
data = cell.serialize()

# Restore
restored_cell = ocd.CylindricalCell.deserialize(data)
```

## Loading from Database

Reference cells and materials can be loaded from the built-in database:

```python
cell = ocd.CylindricalCell.from_database(
    table_name="cell_references",
    name="LFP Cylindrical Tabless Cell"
)
```

## Testing

```bash
# Run all tests
pytest

# Run a specific test
pytest -k test_cells
```

## Development

```bash
# Format Python code
black .
isort .
```

## Citation

If you use this software in your research, please cite it using the metadata in `CITATION.cff`.

## License

MIT License. See [LICENCE.txt](LICENCE.txt) for details.
