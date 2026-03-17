# Cells

Complete battery cell models. Each cell type wraps one or more electrode assemblies inside an encapsulation, fills with electrolyte, and computes energy, mass, cost, and volumetric properties.

All cell types provide:

- **Settable properties**: `operating_voltage_window`, `reversible_capacity`, `n_electrode_assembly`, `electrolyte_overfill`
- **Computed properties**: `energy`, `mass`, `cost`, `volume`, `specific_energy`, `volumetric_energy`, `cost_per_energy`
- **Visualization**: `get_cross_section()`, `get_top_down_view()`, `get_capacity_plot()`, `plot_mass_breakdown()`, `plot_cost_breakdown()`

---

## Cylindrical Cell

For round wound jelly rolls (e.g., 18650, 21700, 4680).

::: steer_opencell_design.Constructions.Cells.CylindricalCell
    options:
      members_order: source
      show_root_heading: true

---

## Prismatic Cell

For flat-wound or stacked assemblies in hard-case housings.

::: steer_opencell_design.Constructions.Cells.PrismaticCell
    options:
      members_order: source
      show_root_heading: true

---

## Pouch Cell

For stacked assemblies in soft-pack laminate pouches.

::: steer_opencell_design.Constructions.Cells.PouchCell
    options:
      members_order: source
      show_root_heading: true

---

## Flex-Frame Cell

For solid-state cell designs with a flex-frame housing.

::: steer_opencell_design.Constructions.Cells.FlexFrameCell
    options:
      members_order: source
      show_root_heading: true
