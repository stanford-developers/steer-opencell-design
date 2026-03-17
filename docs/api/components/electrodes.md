# Electrodes

Electrodes combine a formulation with a current collector and coating parameters (mass loading, calender density, insulation). Key settable properties include `mass_loading`, `calender_density`, `coating_thickness`, and `porosity`—changing one automatically recalculates the others based on the active `control_mode`.

```python
cathode = ocd.Cathode(
    formulation=cathode_formulation,
    mass_loading=12,               # mg/cm²
    current_collector=cathode_cc,
    calender_density=2.60,         # g/cm³
    insulation_material=insulation,
    insulation_thickness=10,       # μm
)
```

---

::: steer_opencell_design.Components.Electrodes
    options:
      members_order: source
      show_root_heading: true
