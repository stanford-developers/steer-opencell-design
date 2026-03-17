# Formulations

Electrode formulations blend active materials, binders, and conductive additives by weight percentage. The formulation computes a blended density, specific cost, and composite specific capacity curve from its constituents.

```python
cathode_formulation = ocd.CathodeFormulation(
    active_materials={cathode_active: 95},       # weight %
    binders={binder: 2},
    conductive_additives={conductive_additive: 3},
)
```

---

::: steer_opencell_design.Materials.Formulations
    options:
      members_order: source
      show_root_heading: true
