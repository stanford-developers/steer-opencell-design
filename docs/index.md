# STEER OpenCell Design

**A Python package for designing and modeling lithium-ion and sodium-ion battery cells.**

Part of the [STEER](https://github.com/stanford-developers) platform, OpenCell Design provides a hierarchical, composable API for building virtual battery cells from raw materials up to complete cell assemblies—with built-in cost, mass, and electrochemical performance calculations.

<div class="grid cards" markdown>

- :material-layers-outline: **Hierarchical Modeling**

    Compose cells from materials → formulations → electrodes → assemblies → complete cells

- :material-battery-charging: **Four Cell Formats**

    Cylindrical, prismatic, pouch, and flex-frame architectures

- :material-chart-line: **Electrochemical Curves**

    Half-cell voltage–capacity curves combined into full-cell curves with N/P ratio control

- :material-scale-balance: **Cost & Mass Breakdowns**

    Automatic roll-up from component level to cell level

- :material-chart-donut: **Interactive Visualization**

    Plotly-based cross-sections, top-down views, capacity plots, and sunburst breakdowns

- :material-database: **Database Integration**

    Load reference materials and pre-configured cell designs from the STEER database

</div>

## Quick Example

```python
import steer_opencell_design as ocd

# Load materials from the database
cathode_active = ocd.CathodeMaterial.from_database("NMC811")
anode_active   = ocd.AnodeMaterial.from_database("Synthetic Graphite")

# Build up the hierarchy: formulations → electrodes → layup → assembly → cell
# ... (see Getting Started for the full walkthrough)

# Inspect results
print(f"Energy:          {cell.energy:.1f} Wh")
print(f"Specific energy: {cell.specific_energy:.1f} Wh/kg")
print(f"Cost per energy: {cell.cost_per_energy:.1f} $/kWh")

# Interactive visualization
cell.get_cross_section().show()
cell.plot_mass_breakdown().show()
```

## Installation

```bash
pip install steer-opencell-design
```

Requires **Python ≥ 3.10**. Dependencies (`steer-core`, `steer-materials`, `numba`) are installed automatically.

## Modeling Hierarchy

The package mirrors the physical hierarchy of a battery cell:

```
Cell
└── Electrode Assembly (jelly roll or stack)
    └── Layup (laminate or mono-layer)
        ├── Cathode
        │   ├── Formulation (active materials + binder + additive)
        │   └── Current Collector
        ├── Anode
        │   ├── Formulation
        │   └── Current Collector
        └── Separator(s)
```

Every level exposes settable properties (mass loading, calender density, N/P ratio, etc.) and computed read-only properties (energy, mass, cost, breakdowns). Changes at any level propagate automatically through the hierarchy.

## Next Steps

- [Getting Started](getting-started.md) — full walkthrough building a cylindrical cell from scratch
- [Concepts](concepts/hierarchy.md) — understand the modeling hierarchy, change propagation, and units
- [API Reference](api/index.md) — detailed class and method documentation
