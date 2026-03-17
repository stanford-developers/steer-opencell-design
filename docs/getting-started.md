# Getting Started

## Installation

=== "From PyPI"

    ```bash
    pip install steer-opencell-design
    ```

=== "From Source"

    ```bash
    git clone https://github.com/stanford-developers/steer-opencell-design.git
    cd steer-opencell-design
    pip install -e .
    ```

### Database Connection

To load reference materials with `from_database()`, set the `API_URL` environment variable:

```bash
export API_URL=https://59xitvvsf2.execute-api.us-east-2.amazonaws.com/production
```

Or set it in your script before importing:

```python
import os
os.environ["API_URL"] = "https://59xitvvsf2.execute-api.us-east-2.amazonaws.com/production"
```

---

## Building a Cylindrical Cell

This walkthrough builds a complete cylindrical cell from scratch, following the natural hierarchy: **Materials → Formulations → Electrodes → Layup → Assembly → Cell**.

### 1. Materials

Load active materials from the built-in database and create auxiliary materials:

```python
import steer_opencell_design as ocd

# Active materials (from database)
cathode_active = ocd.CathodeMaterial.from_database("LFP")
cathode_active.specific_cost = 6      # $/kg
cathode_active.density = 3.6          # g/cm³

anode_active = ocd.AnodeMaterial.from_database("Synthetic Graphite")
anode_active.specific_cost = 4
anode_active.density = 2.2

# Auxiliary materials
conductive_additive = ocd.ConductiveAdditive(
    name="Super P", specific_cost=15, density=2.0, color="#000000"
)
binder = ocd.Binder(name="CMC", specific_cost=10, density=1.5, color="#FFFFFF")
```

### 2. Formulations

Combine active materials, binders, and conductive additives into electrode formulations with weight percentages:

```python
cathode_formulation = ocd.CathodeFormulation(
    active_materials={cathode_active: 95},       # weight %
    binders={binder: 2},
    conductive_additives={conductive_additive: 3},
)

anode_formulation = ocd.AnodeFormulation(
    active_materials={anode_active: 90},
    binders={binder: 5},
    conductive_additives={conductive_additive: 5},
)
```

### 3. Current Collectors

Define current collectors with tab geometry:

```python
cc_material = ocd.CurrentCollectorMaterial(
    name="Aluminum", specific_cost=5, density=2.7, color="#AAAAAA"
)

cathode_cc = ocd.NotchedCurrentCollector(
    material=cc_material,
    length=4500, width=300, thickness=8,       # mm, mm, μm
    tab_width=60, tab_spacing=200, tab_height=18,
    insulation_width=6, coated_tab_height=2,
)

anode_cc = ocd.NotchedCurrentCollector(
    material=cc_material,
    length=4500, width=306, thickness=8,
    tab_width=60, tab_spacing=100, tab_height=18,
    insulation_width=6, coated_tab_height=2,
)
```

### 4. Electrodes

Create electrodes by combining formulations with current collectors and coating parameters:

```python
insulation = ocd.InsulationMaterial.from_database("Aluminium Oxide, 99.5%")

cathode = ocd.Cathode(
    formulation=cathode_formulation,
    mass_loading=12,               # mg/cm²
    current_collector=cathode_cc,
    calender_density=2.60,         # g/cm³
    insulation_material=insulation,
    insulation_thickness=10,       # μm
)

anode = ocd.Anode(
    formulation=anode_formulation,
    mass_loading=7.2,
    current_collector=anode_cc,
    calender_density=1.1,
    insulation_material=insulation,
    insulation_thickness=10,
)
```

### 5. Separator & Layup

Define separators and combine everything into a layup:

```python
separator_material = ocd.SeparatorMaterial(
    name="Polyethylene", specific_cost=2, density=0.94,
    color="#FDFDB7", porosity=45,   # %
)

top_separator = ocd.Separator(
    material=separator_material, thickness=25, width=310, length=5000
)
bottom_separator = ocd.Separator(
    material=separator_material, thickness=25, width=310, length=7000
)

layup = ocd.Laminate(
    anode=anode, cathode=cathode,
    top_separator=top_separator, bottom_separator=bottom_separator,
)
```

!!! tip "Laminate vs MonoLayer"
    Use `Laminate` (two separators) for wound cells and `MonoLayer` (single separator) for stacked cells.

### 6. Electrode Assembly

Wind the layup onto a mandrel and secure with tape:

```python
mandrel = ocd.RoundMandrel(diameter=5, length=350)

tape_material = ocd.TapeMaterial.from_database("Kapton")
tape_material.density = 1.42
tape_material.specific_cost = 70
tape = ocd.Tape(material=tape_material, thickness=30)

jellyroll = ocd.WoundJellyRoll(
    laminate=layup, mandrel=mandrel,
    tape=tape, additional_tape_wraps=5,
)
```

### 7. Encapsulation

Define the container components:

```python
aluminum = ocd.PrismaticContainerMaterial.from_database("Aluminum")
copper = ocd.PrismaticContainerMaterial.from_database("Copper")

encapsulation = ocd.CylindricalEncapsulation(
    cathode_terminal_connector=ocd.CylindricalTerminalConnector(
        material=aluminum, thickness=2, fill_factor=0.8
    ),
    anode_terminal_connector=ocd.CylindricalTerminalConnector(
        material=copper, thickness=3, fill_factor=0.7
    ),
    lid_assembly=ocd.CylindricalLidAssembly(
        material=aluminum, thickness=4.0, fill_factor=0.9
    ),
    canister=ocd.CylindricalCanister(
        material=aluminum, outer_radius=21.4,
        height=330, wall_thickness=0.5,
    ),
)
```

### 8. Electrolyte & Cell

Bring it all together:

```python
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
```

### 9. Inspect Results

```python
print(f"Energy:            {cell.energy:.1f} Wh")
print(f"Mass:              {cell.mass:.1f} g")
print(f"Specific energy:   {cell.specific_energy:.1f} Wh/kg")
print(f"Volumetric energy: {cell.volumetric_energy:.1f} Wh/L")
print(f"Cost per energy:   {cell.cost_per_energy:.1f} $/kWh")

# Interactive Plotly visualizations
cell.get_cross_section().show()
cell.get_capacity_plot().show()
cell.plot_mass_breakdown().show()
cell.plot_cost_breakdown().show()
```

---

## Database Materials Catalog

Reference materials can be loaded with `from_database()`:

| Material Type | Available Names |
|---|---|
| **Cathode Active** | `"LFP"`, `"NMC811"`, `"NMC622"`, `"NFM111 (Vendor B)"`, `"NFM111 (Vendor C)"`, `"NFPP"`, `"NaNiMn P2-O3 Composite"` |
| **Anode Active** | `"Synthetic Graphite"`, `"Hard Carbon (Vendor A)"`, `"Hard Carbon (Vendor B)"` |
| **Binder** | `"PVDF"`, `"CMC"`, `"SBR"` |
| **Conductive Additive** | `"Super P"`, `"Graphite"`, `"Carbon Nanotubes"` |
| **Insulation** | `"Aluminium Oxide, 99.5%"`, `"Aluminium Oxide, 95%"` |
| **Tape** | `"Kapton"`, `"Polyester"` |
| **Container** | `"Aluminum"`, `"Copper"`, `"Steel"` |

Pre-configured reference cells can also be loaded:

```python
cell = ocd.CylindricalCell.from_database(
    table_name="cell_references",
    name="LFP Cylindrical Tabless Cell",
)
```
