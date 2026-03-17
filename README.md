# steer-opencell-design

[![PyPI version](https://img.shields.io/pypi/v/steer-opencell-design)](https://pypi.org/project/steer-opencell-design/)
[![Python](https://img.shields.io/pypi/pyversions/steer-opencell-design)](https://pypi.org/project/steer-opencell-design/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A Python package for designing and modeling lithium-ion and sodium-ion battery cells. Part of the [STEER](https://github.com/stanford-developers) platform, `steer-opencell-design` provides a hierarchical, composable API for building virtual battery cells from raw materials up to complete cell assemblies, with built-in cost, mass, and electrochemical performance calculations.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [More Examples](#more-examples)
  - [Prismatic Cell](#prismatic-cell-stacked)
  - [Pouch Cell](#pouch-cell-stacked)
  - [Flex-Frame Cell (Solid-State)](#flex-frame-cell-solid-state)
- [Package Overview](#package-overview)
  - [Materials](#materials-steer_opencell_designmaterials)
  - [Components](#components-steer_opencell_designcomponents)
  - [Constructions](#constructions-steer_opencell_designconstructions)
  - [Utilities](#utilities)
- [API Reference](#api-reference)
  - [Cell Properties](#cell-properties)
  - [Electrode Assembly Properties](#electrode-assembly-properties)
  - [Layup Properties](#layup-properties)
  - [Electrode Properties](#electrode-properties)
  - [Formulation Properties](#formulation-properties)
  - [Active Material Properties](#active-material-properties)
  - [Current Collector Properties](#current-collector-properties)
  - [Separator Properties](#separator-properties)
  - [Mandrel Properties](#mandrel-properties)
  - [Tape Properties](#tape-properties)
  - [Visualization Methods](#visualization-methods)
  - [Enums & Control Modes](#enums--control-modes)
- [Database Materials Catalog](#database-materials-catalog)
- [Units Convention](#units-convention)
- [Propagating Changes Through the Hierarchy](#propagating-changes-through-the-hierarchy)
- [Serialization](#serialization)
- [Loading from Database](#loading-from-database)
- [STEER Ecosystem](#steer-ecosystem)
- [Testing](#testing)
- [Development](#development)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

---

## Features

- **Hierarchical cell modeling** — compose cells from materials → formulations → electrodes → assemblies → complete cells
- **Multiple cell formats** — cylindrical, prismatic, pouch, and flex-frame cell architectures
- **Multiple assembly types** — wound jelly rolls (round and flat), z-fold stacks, and punched stacks
- **Electrochemical curves** — half-cell voltage–capacity curves are combined into full-cell curves with N/P ratio control
- **Cost and mass breakdowns** — automatic roll-up of cost and mass from component level to cell level
- **Interactive visualization** — Plotly-based cross-sections, top-down views, capacity plots, and sunburst breakdowns
- **Serialization** — serialize and deserialize full cell configurations for storage and sharing
- **Database integration** — load reference materials and cell designs from the STEER database
- **Change propagation** — modify any parameter and automatically recalculate all dependent properties up the hierarchy

---

## Installation

### From PyPI

```bash
pip install steer-opencell-design
```

Requires **Python >= 3.10**. Dependencies (`steer-core`, `steer-materials`, `numba`) are installed automatically.

### From Source

```bash
git clone https://github.com/stanford-developers/steer-opencell-design.git
cd steer-opencell-design
pip install -e .
```

### Database Connection

To use `from_database()` for loading reference materials and cell designs, set the `API_URL` environment variable to point to the STEER database:

```bash
export API_URL=https://api.opencell.example.com/production
```

You can add this to your shell profile (e.g., `~/.bashrc`, `~/.zshrc`) or set it in your Python script before importing:

```python
import os
os.environ["API_URL"] = "https://api.opencell.example.com/production"

import steer_opencell_design as ocd
```

---

## Quickstart

The following example builds a complete **cylindrical cell** from scratch. The workflow follows the natural hierarchy: **Materials → Formulations → Electrodes → Layup → Assembly → Cell**.

```python
import os
os.environ["API_URL"] = "https://api.opencell.example.com/production"

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

---

## More Examples

### Prismatic Cell (Stacked)

<details>
<summary>Build a prismatic cell with punched stacked electrodes</summary>

```python
import os
os.environ["API_URL"] = "https://api.opencell.example.com/production"

import steer_opencell_design as ocd

# ── Materials ─────────────────────────────────────────────────────

cathode_active = ocd.CathodeMaterial.from_database("LFP")
cathode_active.specific_cost = 6
cathode_active.density = 3.6

anode_active = ocd.AnodeMaterial.from_database("Synthetic Graphite")
anode_active.specific_cost = 4
anode_active.density = 2.2

conductive_additive = ocd.ConductiveAdditive(name="Super P", specific_cost=15, density=2.0, color="#000000")
binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")

# ── Formulations ──────────────────────────────────────────────────

cathode_form = ocd.CathodeFormulation(
    active_materials={cathode_active: 95},
    binders={binder: 2},
    conductive_additives={conductive_additive: 3},
)
anode_form = ocd.AnodeFormulation(
    active_materials={anode_active: 90},
    binders={binder: 5},
    conductive_additives={conductive_additive: 5},
)

# ── Current Collectors (Punched for stacking) ────────────────────

al_cc = ocd.CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")
cu_cc = ocd.CurrentCollectorMaterial(name="Copper", specific_cost=10, density=8.96, color="#B87333")

cathode_cc = ocd.PunchedCurrentCollector(
    material=al_cc, length=200, width=100, thickness=12,
    tab_width=40, tab_height=20,
)
anode_cc = ocd.PunchedCurrentCollector(
    material=cu_cc, length=204, width=104, thickness=8,
    tab_width=40, tab_height=20,
)

# ── Electrodes ────────────────────────────────────────────────────

insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

cathode = ocd.Cathode(
    formulation=cathode_form, mass_loading=20,
    current_collector=cathode_cc, calender_density=2.60,
    insulation_material=insulation, insulation_thickness=10,
)
anode = ocd.Anode(
    formulation=anode_form, mass_loading=12,
    current_collector=anode_cc, calender_density=1.1,
    insulation_material=insulation, insulation_thickness=10,
)

# ── Separator & Layup ────────────────────────────────────────────

sep_mat = ocd.SeparatorMaterial(name="Polyethylene", specific_cost=2, density=0.94, color="#FDFDB7", porosity=45)
separator = ocd.Separator(material=sep_mat, thickness=20, width=210, length=110)

layup = ocd.MonoLayer(anode=anode, cathode=cathode, separator=separator)

# ── Assembly (Punched Stack) ─────────────────────────────────────

tape_material = ocd.TapeMaterial.from_database("Kapton")
tape_material.density = 1.42
tape_material.specific_cost = 70
tape = ocd.Tape(material=tape_material, thickness=30)

stack = ocd.PunchedStack(mono_layer=layup, n_layers=20, tape=tape)

# ── Encapsulation ─────────────────────────────────────────────────

steel = ocd.PrismaticContainerMaterial.from_database("Steel")
aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
copper = ocd.PrismaticContainerMaterial.from_database("Copper")

encapsulation = ocd.PrismaticEncapsulation(
    cathode_terminal_connector=ocd.PrismaticTerminalConnector(material=aluminum, thickness=2, fill_factor=0.5),
    anode_terminal_connector=ocd.PrismaticTerminalConnector(material=copper, thickness=2, fill_factor=0.5),
    lid_assembly=ocd.PrismaticLidAssembly(material=steel, thickness=2, fill_factor=0.9),
    canister=ocd.PrismaticCanister(
        material=steel, height=120, width=110, depth=220,
        wall_thickness=0.5, base_thickness=0.5,
    ),
)

# ── Electrolyte & Cell ───────────────────────────────────────────

electrolyte = ocd.Electrolyte(name="1M LiPF6 in EC:DMC", density=1.2, specific_cost=15, color="#00FF00")

cell = ocd.PrismaticCell(
    reference_electrode_assembly=stack,
    encapsulation=encapsulation,
    electrolyte=electrolyte,
    n_electrode_assembly=6,
    electrolyte_overfill=20,
    clipped_tab_length=7,
)

print(f"Energy: {cell.energy:.2f} Wh | Mass: {cell.mass:.2f} g | Specific energy: {cell.specific_energy:.2f} Wh/kg")
```

</details>

### Pouch Cell (Stacked)

<details>
<summary>Build a pouch cell with punched stacked electrodes</summary>

```python
import os
os.environ["API_URL"] = "https://api.opencell.example.com/production"

import steer_opencell_design as ocd

# ── Materials & Formulations (same as prismatic example above) ───
# ... (create cathode_form, anode_form, cathode, anode as before)

# ── Separator & Layup ────────────────────────────────────────────

sep_mat = ocd.SeparatorMaterial(name="Polyethylene", specific_cost=2, density=0.94, color="#FDFDB7", porosity=45)
separator = ocd.Separator(material=sep_mat, thickness=20, width=210, length=110)
layup = ocd.MonoLayer(anode=anode, cathode=cathode, separator=separator)

# ── Assembly ──────────────────────────────────────────────────────

tape_material = ocd.TapeMaterial.from_database("Kapton")
tape_material.density = 1.42
tape_material.specific_cost = 70
tape = ocd.Tape(material=tape_material, thickness=30)

stack = ocd.PunchedStack(mono_layer=layup, n_layers=20, tape=tape)

# ── Pouch Encapsulation ──────────────────────────────────────────

laminate_mat = ocd.LaminateMaterial(name="Al Laminate", specific_cost=5, density=1.5, color="#C0C0C0")
al_mat = ocd.PrismaticContainerMaterial.from_database("Aluminum")
cu_mat = ocd.PrismaticContainerMaterial.from_database("Copper")

encapsulation = ocd.PouchEncapsulation(
    cathode_terminal=ocd.PouchTerminal(material=al_mat, width=40, thickness=200, length=20),
    anode_terminal=ocd.PouchTerminal(material=cu_mat, width=40, thickness=200, length=20),
    top_laminate_sheet=ocd.LaminateSheet(material=laminate_mat, thickness=113, draw_depth=5),
    bottom_laminate_sheet=ocd.LaminateSheet(material=laminate_mat, thickness=113, draw_depth=5),
    seal_width=8,
)

# ── Electrolyte & Cell ───────────────────────────────────────────

electrolyte = ocd.Electrolyte(name="1M LiPF6 in EC:DMC", density=1.2, specific_cost=15, color="#00FF00")

cell = ocd.PouchCell(
    reference_electrode_assembly=stack,
    encapsulation=encapsulation,
    electrolyte=electrolyte,
    n_electrode_assembly=2,
    electrolyte_overfill=20,
    clipped_tab_length=10,
)

print(f"Energy: {cell.energy:.2f} Wh | Mass: {cell.mass:.2f} g")
cell.get_top_down_view().show()
```

</details>

### Flex-Frame Cell (Solid-State)

<details>
<summary>Build a solid-state flex-frame cell with lithium metal anode</summary>

```python
import os
os.environ["API_URL"] = "https://api.opencell.example.com/production"

import steer_opencell_design as ocd
import pandas as pd

# ── Materials ─────────────────────────────────────────────────────

cathode_active = ocd.CathodeMaterial.from_database("NMC811")
cathode_active.specific_cost = 30
cathode_active.density = 4.87

# Lithium metal anode (custom half-cell curve)
anode_active = ocd.AnodeMaterial(
    name="Lithium Metal",
    half_cell_curve=pd.DataFrame({
        "voltage": [0.0, 0.01, 5.0],
        "capacity": [0.0, 3861, 3862],
    }),
    specific_cost=100,
    density=0.534,
    color="#C0C0C0",
)

conductive_additive = ocd.ConductiveAdditive(name="Super P", specific_cost=15, density=2.0, color="#000000")
binder = ocd.Binder(name="PVDF", specific_cost=10, density=1.78, color="#FFFFFF")

# ── Formulations ──────────────────────────────────────────────────

cathode_form = ocd.CathodeFormulation(
    active_materials={cathode_active: 90},
    binders={binder: 5},
    conductive_additives={conductive_additive: 5},
)
anode_form = ocd.AnodeFormulation(
    active_materials={anode_active: 100},
    binders={},
    conductive_additives={},
)

# ── Current Collectors & Electrodes ──────────────────────────────

al_cc = ocd.CurrentCollectorMaterial(name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA")
cu_cc = ocd.CurrentCollectorMaterial(name="Copper", specific_cost=10, density=8.96, color="#B87333")
insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

cathode = ocd.Cathode(
    formulation=cathode_form, mass_loading=30,
    current_collector=ocd.PunchedCurrentCollector(
        material=al_cc, length=80, width=55, thickness=12, tab_width=25, tab_height=15,
    ),
    calender_density=3.1, insulation_material=insulation, insulation_thickness=10,
)
anode = ocd.Anode(
    formulation=anode_form, mass_loading=2.1,
    current_collector=ocd.PunchedCurrentCollector(
        material=cu_cc, length=82, width=57, thickness=8, tab_width=25, tab_height=15,
    ),
    calender_density=0.534, insulation_material=insulation, insulation_thickness=10,
)

# ── Solid Electrolyte Separator ───────────────────────────────────

sep_mat = ocd.SeparatorMaterial(
    name="LLZO", specific_cost=200, density=5.1,
    color="#E0E0FF", porosity=0,     # solid electrolyte — zero porosity
)
separator = ocd.Separator(material=sep_mat, thickness=30, width=86, length=60)

# ── Layup → Stack ────────────────────────────────────────────────

layup = ocd.MonoLayer(anode=anode, cathode=cathode, separator=separator)

tape_mat = ocd.TapeMaterial.from_database("Kapton")
tape_mat.density = 1.42
tape_mat.specific_cost = 70

stack = ocd.PunchedStack(
    mono_layer=layup, n_layers=1,
    tape=ocd.Tape(material=tape_mat, thickness=30),
)

# ── Flex-Frame Encapsulation ─────────────────────────────────────

frame_mat = ocd.FlexFrameMaterial(name="PEEK", specific_cost=100, density=1.3, color="#D2B48C")
laminate_mat = ocd.LaminateMaterial(name="Al Laminate", specific_cost=5, density=1.5, color="#C0C0C0")
al_mat = ocd.PrismaticContainerMaterial.from_database("Aluminum")
cu_mat = ocd.PrismaticContainerMaterial.from_database("Copper")

encapsulation = ocd.FlexFrameEncapsulation(
    frame=ocd.FlexFrame(material=frame_mat, thickness=200, rim_width=5),
    cathode_terminal=ocd.PouchTerminal(material=al_mat, width=25, thickness=200, length=15),
    anode_terminal=ocd.PouchTerminal(material=cu_mat, width=25, thickness=200, length=15),
    top_laminate_sheet=ocd.LaminateSheet(material=laminate_mat, thickness=113, draw_depth=2),
    bottom_laminate_sheet=ocd.LaminateSheet(material=laminate_mat, thickness=113, draw_depth=2),
)

# ── Catholyte & Cell ─────────────────────────────────────────────

catholyte = ocd.Electrolyte(name="Gel Catholyte", density=1.3, specific_cost=50, color="#90EE90")

cell = ocd.FlexFrameCell(
    reference_electrode_assembly=stack,
    encapsulation=encapsulation,
    catholyte=catholyte,           # FlexFrameCell uses 'catholyte' instead of 'electrolyte'
    clipped_tab_length=8,
)

print(f"Energy: {cell.energy:.2f} Wh | Mass: {cell.mass:.2f} g | Cost: ${cell.cost:.2f}")
```

</details>

---

## Package Overview

The package is organized into four layers that mirror the physical hierarchy of a battery cell:

```
Materials  →  Components  →  Constructions  →  Cells
```

All classes inherit from a rich set of mixins provided by `steer-core` (validation, serialization, coordinate systems, change propagation, plotting, and database access), giving every object a consistent interface.

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
| `ElectrodeControlMode` | Enum controlling how electrode properties respond to changes |
| `RoundMandrel` / `FlatMandrel` | Winding mandrel geometry for jelly roll assembly |
| `Tape` | Termination tape for wound assemblies |

---

## API Reference

Properties marked **settable** can be assigned to directly and will trigger recalculation of dependent values. **Read-only** properties are computed automatically. Every settable property also has a corresponding `*_range` (soft) and often a `*_hard_range` (absolute) read-only property that defines the valid bounds for that parameter (omitted from tables below for brevity).

### Cell Properties

All cell types (`CylindricalCell`, `PrismaticCell`, `PouchCell`, `FlexFrameCell`).

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `reference_electrode_assembly` | — | Reference electrode assembly object |
| `encapsulation` | — | Container/encapsulation object |
| `electrolyte` | — | Electrolyte object |
| `n_electrode_assembly` | — | Number of electrode assemblies in the cell |
| `electrolyte_overfill` | % | Electrolyte overfill percentage |
| `operating_voltage_window` | (V, V) | (min, max) operating voltages |
| `maximum_operating_voltage` | V | Upper voltage limit |
| `minimum_operating_voltage` | V | Lower voltage limit |
| `reversible_capacity` | Ah | Usable discharge capacity (solves for min voltage) |
| `irreversible_capacity` | Ah | Maximum capacity at full charge (solves for max voltage) |
| `name` | — | Cell name |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `energy` | Wh | Total cell energy |
| `mass` | g | Total cell mass |
| `cost` | $ | Total cell cost |
| `volume` | L | Cell volume |
| `specific_energy` | Wh/kg | Gravimetric energy density |
| `volumetric_energy` | Wh/L | Volumetric energy density |
| `cost_per_energy` | $/kWh | Normalized cost per energy |
| `capacity_loss` | Ah | Capacity remaining at minimum voltage |
| `capacity_curve` | DataFrame | Full-cell voltage vs. capacity data |
| `cathode_capacity_curve` | DataFrame | Cathode half-cell curve |
| `anode_capacity_curve` | DataFrame | Anode half-cell curve |
| `mass_breakdown` | dict | Nested mass breakdown by component (g) |
| `cost_breakdown` | dict | Nested cost breakdown by component ($) |
| `form_factor` | str | Human-readable form factor (e.g., "Cylindrical") |
| `internal_construction` | str | Assembly type (e.g., "Wound Jelly Roll") |
| `reference_chemistry` | str | Chemistry reference string |
| `electrode_assemblies` | list | All electrode assembly instances in the cell |

### Electrode Assembly Properties

Shared by all assemblies (`WoundJellyRoll`, `FlatWoundJellyRoll`, `PunchedStack`, `ZFoldStack`).

**Settable (all assemblies):**

| Property | Unit | Description |
|---|---|---|
| `layup` | — | Layup object (Laminate, MonoLayer, etc.) |
| `name` | — | Assembly name |

**Read-only (all assemblies):**

| Property | Unit | Description |
|---|---|---|
| `pore_volume` | cm³ | Total pore volume (used for electrolyte fill) |
| `interfacial_area` | cm² | Active interfacial area |
| `capacity_curve` | DataFrame | Full-cell capacity curve (Ah vs. V) |
| `anode_capacity_curve` | DataFrame | Anode half-cell curve |
| `cathode_capacity_curve` | DataFrame | Cathode half-cell curve |
| `cost` | $ | Total assembly cost |
| `cost_breakdown` | dict | Nested cost breakdown |
| `mass` | g | Total assembly mass |
| `mass_breakdown` | dict | Nested mass breakdown |

**`WoundJellyRoll` — additional settable:**

| Property | Unit | Description |
|---|---|---|
| `mandrel` | — | Mandrel object |
| `tape` | — | Tape object |
| `additional_tape_wraps` | — | Number of extra tape wraps |
| `tape_length_driver` | — | `TapeDriver` enum (`JELLY_ROLL_DRIVEN` / `TAPE_DRIVEN`) |
| `collector_tab_crumple_factor` | % | Tab crumple factor |
| `height` | mm | Overall assembly height |
| `diameter` | mm | Outer diameter (WoundJellyRoll only) |
| `radius` | mm | Outer radius (WoundJellyRoll only) |

**`WoundJellyRoll` — additional read-only:**

| Property | Unit | Description |
|---|---|---|
| `roll_properties` | DataFrame | Turn counts per component |
| `spiral` | DataFrame | Spiral coordinates |
| `total_layup_length` | mm | Total unwrapped layup length |
| `total_height` | mm | Total wound height |

**`FlatWoundJellyRoll` — additional settable:**

| Property | Unit | Description |
|---|---|---|
| `thickness` | mm | Overall jelly roll thickness |
| `width` | mm | Overall jelly roll width |

**`FlatWoundJellyRoll` — additional read-only:**

| Property | Unit | Description |
|---|---|---|
| `pressed_radius` | mm | Pressed mandrel radius |
| `pressed_straight_length` | mm | Pressed mandrel straight length |

**`PunchedStack` / `ZFoldStack` — additional settable:**

| Property | Unit | Description |
|---|---|---|
| `n_layers` | — | Number of electrode layers |
| `thickness` | mm | Total stack thickness (adjusts `n_layers`) |

**`ZFoldStack` — additional settable:**

| Property | Unit | Description |
|---|---|---|
| `additional_separator_wraps` | — | Extra separator wraps around the stack |

### Layup Properties

Shared by `Laminate`, `MonoLayer`, `ZFoldMonoLayer`.

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `cathode` | — | Cathode electrode object |
| `anode` | — | Anode electrode object |
| `np_ratio` | — | N/P ratio (anode capacity / cathode capacity) |
| `np_ratio_control_mode` | — | `NPRatioControlMode` enum |
| `operating_voltage_window` | (V, V) | (min, max) voltage window |
| `minimum_operating_voltage` | V | Minimum operating voltage |
| `maximum_operating_voltage` | V | Maximum operating voltage |
| `operating_reversible_areal_capacity` | mAh/cm² | Operating reversible areal capacity |
| `electrode_orientation` | — | Electrode orientation enum |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `areal_capacity_curve` | DataFrame | Full-cell areal capacity curve (mAh/cm² vs. V) |

### Electrode Properties

`Cathode` and `Anode`.

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `formulation` | — | Electrode formulation object |
| `current_collector` | — | Current collector object |
| `mass_loading` | mg/cm² | Coating mass loading |
| `calender_density` | g/cm³ | Calendered coating density |
| `coating_thickness` | µm | Single-side coating thickness |
| `thickness` | µm | Total electrode thickness (CC + 2× coating) |
| `porosity` | % | Electrode coating porosity |
| `insulation_material` | — | Insulation material object |
| `insulation_thickness` | µm | Insulation coating thickness |
| `voltage_cutoff` | V | Half-cell voltage cutoff |
| `control_mode` | — | `ElectrodeControlMode` enum |
| `name` | — | Electrode name |

**`Anode`-only settable:**

| Property | Unit | Description |
|---|---|---|
| `top_overhang` | mm | Top overhang in layup context |
| `bottom_overhang` | mm | Bottom overhang in layup context |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `mass` | g | Total electrode mass |
| `cost` | $ | Total electrode cost |
| `mass_breakdown` | dict | Nested mass breakdown (g) |
| `cost_breakdown` | dict | Nested cost breakdown ($) |
| `areal_capacity_curve` | DataFrame | Areal capacity vs. voltage |
| `top_side` | str | Which side ('a'/'b') faces up |
| `properties` | dict | Summary dict (cost, mass, thickness) |

### Formulation Properties

`CathodeFormulation` and `AnodeFormulation`.

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `active_materials` | — | Dict of `{ActiveMaterial: weight%}` |
| `binders` | — | Dict of `{Binder: weight%}` |
| `conductive_additives` | — | Dict of `{ConductiveAdditive: weight%}` |
| `active_material_1` / `_2` / `_3` | — | Individual active material objects |
| `active_material_1_weight` / `_2_weight` / `_3_weight` | % | Individual weight percentages |
| `binder_1` / `_2` | — | Individual binder objects |
| `binder_1_weight` / `_2_weight` | % | Individual weight percentages |
| `conductive_additive_1` / `_2` | — | Individual conductive additive objects |
| `conductive_additive_1_weight` / `_2_weight` | % | Individual weight percentages |
| `voltage_cutoff` | V | Half-cell voltage cutoff |
| `mass` | g | Formulation mass |
| `volume` | cm³ | Formulation volume |
| `name` | — | Formulation name |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `density` | g/cm³ | Blended formulation density |
| `specific_cost` | $/g | Blended specific cost |
| `cost` | $ | Total formulation cost |
| `cost_breakdown` | dict | Nested cost breakdown |
| `mass_breakdown` | dict | Nested mass breakdown |
| `specific_capacity_curve` | DataFrame | Specific capacity curve (mAh/g vs. V) |
| `capacity_curve` | DataFrame | Capacity curve (mAh vs. V) |
| `voltage_operation_window` | (V, V) | Valid voltage range |
| `color` | str | Hex color string |

### Active Material Properties

`CathodeMaterial` and `AnodeMaterial`.

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `reversible_specific_capacity` | mAh/g | Reversible specific capacity |
| `irreversible_specific_capacity` | mAh/g | Irreversible specific capacity |
| `reversible_specific_capacity_scaling_percentage` | % | Scaling adjustment for reversible capacity |
| `irreversible_specific_capacity_scaling_percentage` | % | Scaling adjustment for irreversible capacity |
| `voltage_cutoff` | V | Voltage cutoff for half-cell curves |
| `specific_capacity_curves` | list | List of DataFrames (raw curve data) |
| `extrapolation_window` | V | Extrapolation window |
| `reference` | — | Reference electrode string (e.g., "Li/Li+") |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `specific_capacity_curve` | DataFrame | Specific capacity curve (mAh/g vs. V) |
| `minimum_extrapolated_voltage` | V | Minimum extrapolated voltage (`CathodeMaterial` only) |

### Current Collector Properties

Shared by all current collector types.

**Settable (all types):**

| Property | Unit | Description |
|---|---|---|
| `material` | — | Current collector material object |
| `thickness` | µm | Foil thickness |
| `insulation_width` | mm | Edge insulation width |
| `name` | — | Name string |

**Tape-style CCs** (`NotchedCurrentCollector`, `TablessCurrentCollector`) — **additional settable:**

| Property | Unit | Description |
|---|---|---|
| `length` | mm | Foil length |
| `width` | mm | Foil width |
| `bare_lengths_a_side` | (mm, mm) | (start, end) bare region on A-side |
| `bare_lengths_b_side` | (mm, mm) | (start, end) bare region on B-side |
| `a_side_coated_section` | (mm, mm) | (start, end) of A-side coating |
| `b_side_coated_section` | (mm, mm) | (start, end) of B-side coating |

**Tabbed CCs** (`NotchedCurrentCollector`, `TabWeldedCurrentCollector`, `PunchedCurrentCollector`) — **additional settable:**

| Property | Unit | Description |
|---|---|---|
| `tab_width` | mm | Tab width |
| `tab_height` | mm | Tab height |
| `coated_tab_height` | mm | Coated portion of tab height |

**Read-only (all types):**

| Property | Unit | Description |
|---|---|---|
| `mass` | g | Total mass |
| `cost` | $ | Total cost |
| `foil_area` | cm² | Single-sided foil area |
| `coated_area` | cm² | Total coated area |
| `a_side_coated_area` | cm² | A-side coated area |
| `b_side_coated_area` | cm² | B-side coated area |
| `insulation_area` | cm² | Total insulation area |
| `top_side` | str | Which side ('a'/'b') faces up |
| `total_height` | mm | Total height including tab (tabbed types) |

### Separator Properties

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `material` | — | Separator material object |
| `length` | mm | Separator length |
| `width` | mm | Separator width |
| `thickness` | µm | Separator thickness |
| `areal_cost` | $/m² | Areal cost (adjusts material specific cost) |
| `name` | — | Separator name |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `mass` | g | Total separator mass |
| `cost` | $ | Total separator cost |
| `area` | cm² | Separator area |
| `pore_volume` | mm³ | Pore volume (based on porosity) |

### Mandrel Properties

`RoundMandrel` and `FlatMandrel`.

**Settable (both):**

| Property | Unit | Description |
|---|---|---|
| `length` | mm | Mandrel length |
| `name` | — | Mandrel name |

**`RoundMandrel` — settable:**

| Property | Unit | Description |
|---|---|---|
| `radius` | mm | Mandrel radius |
| `diameter` | mm | Mandrel diameter |

**`FlatMandrel` — settable:**

| Property | Unit | Description |
|---|---|---|
| `width` | mm | Mandrel width |
| `height` | mm | Mandrel height |
| `radius` | mm | Half of height |

**`FlatMandrel` — read-only:**

| Property | Unit | Description |
|---|---|---|
| `straight_length` | mm | Flat segment length |

### Tape Properties

**Settable:**

| Property | Unit | Description |
|---|---|---|
| `material` | — | Tape material object |
| `length` | mm | Tape length |
| `width` | mm | Tape width |
| `thickness` | µm | Tape thickness |
| `areal_cost` | $/m² | Areal cost |
| `name` | — | Tape name |

**Read-only:**

| Property | Unit | Description |
|---|---|---|
| `mass` | g | Total tape mass |
| `cost` | $ | Total tape cost |
| `area` | cm² | Total tape area |

### Visualization Methods

All visualization methods return [Plotly](https://plotly.com/python/) `go.Figure` objects that can be displayed interactively with `.show()` or exported to HTML/PNG/SVG.

**Cell-level:**

| Method | Availability | Description |
|---|---|---|
| `get_cross_section()` | `CylindricalCell` | Spiral cross-section of the wound jelly roll |
| `get_top_down_view()` | All cell types | Top-down 2D view of the cell |
| `get_side_view()` | `PrismaticCell`, `PouchCell`, `FlexFrameCell` | Side view of the cell |
| `get_capacity_plot()` | All cell types | Full-cell + half-cell voltage–capacity curves |
| `plot_mass_breakdown()` | All cell types | Sunburst chart of mass by component |
| `plot_cost_breakdown()` | All cell types | Sunburst chart of cost by component |

**Electrode Assembly-level:**

| Method | Availability | Description |
|---|---|---|
| `get_spiral_plot()` | `WoundJellyRoll`, `FlatWoundJellyRoll` | Spiral winding path visualization |
| `get_top_down_view()` | All assemblies | Top-down view of the assembly |
| `get_side_view()` | All assemblies | Side view of the assembly |
| `get_capacity_plot()` | All assemblies | Assembly-level capacity curves |
| `plot_mass_breakdown()` | All assemblies | Assembly mass breakdown |
| `plot_cost_breakdown()` | All assemblies | Assembly cost breakdown |

**Electrode-level:**

| Method | Description |
|---|---|
| `get_cross_section()` | Electrode cross-section (coating + CC + insulation) |
| `get_top_down_view()` | Top-down electrode view |
| `get_a_side_view()` / `get_b_side_view()` | Individual coating side views |
| `plot_areal_capacity_curve()` | Areal capacity vs. voltage plot |
| `plot_mass_breakdown()` / `plot_cost_breakdown()` | Electrode-level breakdowns |

**Layup-level:**

| Method | Description |
|---|---|
| `get_top_down_view()` | Top-down layup view |
| `get_down_top_view()` | Bottom-up layup view |
| `get_areal_capacity_plot()` | Layup areal capacity curves |

### Enums & Control Modes

#### `ElectrodeControlMode`

Controls how interdependent electrode properties (`mass_loading`, `calender_density`, `coating_thickness`) respond when one is changed.

| Value | Behavior |
|---|---|
| `MAINTAIN_CALENDER_DENSITY` | Default. Keeps calender density constant; adjusts coating thickness. |
| `MAINTAIN_MASS_LOADING` | Keeps mass loading constant; adjusts coating thickness. |
| `MAINTAIN_COATING_THICKNESS` | Keeps coating thickness constant; adjusts mass loading or calender density. |

#### `NPRatioControlMode`

Controls how N/P ratio adjustments propagate through the layup.

| Value | Behavior |
|---|---|
| `FIXED_ANODE` | Anode stays fixed; cathode loading adjusts to achieve target N/P ratio. |
| `FIXED_CATHODE` | Cathode stays fixed; anode loading adjusts. |
| `FIXED_THICKNESS` | Thickness stays fixed; mass loading and calender density adjust. |

#### `OverhangControlMode`

Controls how electrode overhang is maintained.

| Value | Behavior |
|---|---|
| `FIXED_COMPONENT` | Overhang values shift component positions (dimensions are fixed). |
| `FIXED_OVERHANGS` | Overhang values change component dimensions (positions stay centered). |

---

## Database Materials Catalog

The STEER database includes reference materials that can be loaded with `from_database()`. Known entries include:

| Material Type | Available Names |
|---|---|
| **Cathode Active** | `"LFP"`, `"NMC811"`, `"NMC622"`, `"NFM111 (Vendor B)"`, `"NFM111 (Vendor C)"`, `"NFPP"`, `"NaNiMn P2-O3 Composite"` |
| **Anode Active** | `"Synthetic Graphite"`, `"Hard Carbon (Vendor A)"`, `"Hard Carbon (Vendor B)"` |
| **Binder** | `"PVDF"`, `"CMC"`, `"SBR"` |
| **Conductive Additive** | `"Super P"`, `"Graphite"`, `"Carbon Nanotubes"` |
| **Insulation** | `"Aluminium Oxide, 99.5%"`, `"Aluminium Oxide, 95%"` |
| **Separator** | `"Polyethylene"`, `"Nafion"` |
| **Tape** | `"Kapton"`, `"Polyester"` |
| **Current Collector** | `"Aluminum"`, `"Copper"` |
| **Container** | `"Aluminum"`, `"Copper"`, `"Steel"` |

Pre-configured reference cells can also be loaded:

```python
cell = ocd.CylindricalCell.from_database(
    table_name="cell_references",
    name="LFP Cylindrical Tabless Cell",
)
```

---

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

---

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

When you modify a property deep in the hierarchy (e.g., changing the cathode's mass loading), parent objects need to recalculate their derived properties. There are three methods to handle this:

- **`propagate_changes()`** — Recommended. Bubbles recalculation up through all parents automatically.
- **`update()`** — Recalculates a single object without propagating to parents.
- **Re-assignment** — Manually re-assign each level for explicit control.

### Method 1: `propagate_changes()` (Recommended)

The simplest approach — modify the property and then call `propagate_changes()` on that object:

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

# Propagate from the current collector level — goes through:
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

When loading a cell from serialized data or a database, parent references may not be established automatically. The `propagate_changes()` method still works — it simply stops at the first level without a parent.

```python
# Load from database
cell = ocd.CylindricalCell.from_database(table_name="cell_references", name="My Cell")

# Modify and propagate — works correctly
cell.reference_electrode_assembly.layup.cathode.mass_loading = 14
cell.reference_electrode_assembly.layup.cathode.propagate_changes()
```

---

## Serialization

All cells and components can be serialized and deserialized for storage and sharing:

```python
# Save
data = cell.serialize()

# Restore
restored_cell = ocd.CylindricalCell.deserialize(data)
```

The serialized output is a plain Python dict that can be converted to JSON for file storage or API transport.

---

## Loading from Database

Reference cells and materials can be loaded from the STEER database. Make sure the `API_URL` environment variable is set (see [Installation](#database-connection)).

```python
# Load a pre-configured cell
cell = ocd.CylindricalCell.from_database(
    table_name="cell_references",
    name="LFP Cylindrical Tabless Cell",
)

# Load individual materials
cathode_active = ocd.CathodeMaterial.from_database("NMC811")
separator_mat = ocd.SeparatorMaterial.from_database("Polyethylene")
```

---

## STEER Ecosystem

`steer-opencell-design` is part of the STEER platform. The ecosystem is composed of several packages that work together:

| Package | Role |
|---|---|
| [`steer-core`](https://pypi.org/project/steer-core/) | Provides the mixin framework shared by all STEER packages — validation, serialization, coordinate systems, change propagation, Plotly-based plotting, and database access. |
| [`steer-materials`](https://pypi.org/project/steer-materials/) | Base material classes with `from_database()` support, volumetric tracking, and metal subclasses. |
| **`steer-opencell-design`** | **This package.** The cell design API that composes materials and components into complete virtual battery cells with cost, mass, and electrochemical calculations. |

All dependencies are installed automatically when you `pip install steer-opencell-design`.

---

## Testing

The test suite uses Python's `unittest` framework via `pytest`:

```bash
# Run all tests
pytest

# Run a specific test file
pytest -k test_cells

# Run with verbose output
pytest -v

# Run a single test class or method
pytest -k "TestCylindricalCell"
```

The test environment is configured with `OPENCELL_ENV = "development"` (set automatically by `pyproject.toml`).

---

## Development

### Project Structure

```
steer-opencell-design/
├── steer_opencell_design/          # Main package
│   ├── Materials/                  # Raw materials & formulations
│   ├── Components/                 # Electrodes, separators, current collectors, containers
│   │   ├── CurrentCollectors/      # Notched, Tabbed, Tabless, Punched
│   │   └── Containers/             # Cylindrical, Prismatic, Pouch, FlexFrame
│   ├── Constructions/              # Assembly-level objects
│   │   ├── Layups/                 # Laminate, MonoLayer, ZFoldMonoLayer
│   │   ├── ElectrodeAssemblies/    # JellyRolls, Stacks, Tape, Mandrels
│   │   └── Cells/                  # CylindricalCell, PrismaticCell, PouchCell, FlexFrameCell
│   └── Utils/                      # Decorators and helper functions
├── test/                           # Unit tests (unittest via pytest)
├── pyproject.toml                  # Build config & dependencies
├── pyrightconfig.json              # Type checking config
├── CITATION.cff                    # Citation metadata
└── LICENCE.txt                     # AGPL-3.0 (dual licensed)
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

---

## Citation

If you use this software in your research, please cite it using the metadata in [`CITATION.cff`](CITATION.cff).

---

## License

OpenCell Design is dual-licensed:

- **Open-source license:** [AGPL-3.0](LICENCE.txt) — free for open-source projects. If you use OpenCell Design in your software, you must release your software's source code under AGPL-3.0.

- **Commercial license:** For proprietary/commercial use without the AGPL copyleft requirement, contact nsiemons@stanford.edu for a commercial license.

See [LICENCE.txt](LICENCE.txt) for the full AGPL-3.0 license text.
