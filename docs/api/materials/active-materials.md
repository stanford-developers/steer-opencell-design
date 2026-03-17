# Active Materials

Active materials define the electrochemistry of a cell. Each material wraps one or more half-cell voltage–capacity curves and exposes properties like reversible specific capacity, density, and cost.

Most active materials can be loaded from the database:

```python
cathode = ocd.CathodeMaterial.from_database("NMC811")
anode   = ocd.AnodeMaterial.from_database("Synthetic Graphite")
```

---

::: steer_opencell_design.Materials.ActiveMaterials
    options:
      members_order: source
      show_root_heading: true

---

## Capacity Curve Utilities

Helper functions for manipulating and combining voltage–capacity curves.

::: steer_opencell_design.Materials.CapacityCurveUtils
    options:
      show_root_heading: true
