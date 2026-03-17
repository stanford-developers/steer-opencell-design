# Change Propagation

When you modify a property deep in the hierarchy (e.g., changing the cathode's mass loading), parent objects need to recalculate their derived properties. There are three approaches:

## Method 1: `propagate_changes()` (Recommended)

The simplest approach — modify the property and call `propagate_changes()` on that object:

```python
# Modify a property low in the hierarchy
cell.reference_electrode_assembly.layup.cathode.mass_loading = 15

# Propagate changes up to the cell level
cell.reference_electrode_assembly.layup.cathode.propagate_changes()

# Now the cell's energy, mass, cost, etc. are all updated
print(cell.energy)
```

## Method 2: `update()`

Recalculates a single object without propagating to parents. Useful when you're making multiple changes before recalculating:

```python
cathode = cell.reference_electrode_assembly.layup.cathode
cathode.mass_loading = 15
cathode.calender_density = 2.8

# Only recalculates the cathode
cathode.update()

# Must manually update each parent
cell.reference_electrode_assembly.layup.update()
cell.reference_electrode_assembly.update()
cell.update()
```

## Method 3: Re-assignment

Manually re-assign each level for explicit control:

```python
layup = cell.reference_electrode_assembly.layup
cathode = layup.cathode
cathode.mass_loading = 15

layup.cathode = cathode           # triggers layup recalc
assembly = cell.reference_electrode_assembly
assembly.layup = layup            # triggers assembly recalc
cell.reference_electrode_assembly = assembly  # triggers cell recalc
```

!!! tip "Use `propagate_changes()` for most cases"
    Unless you need fine-grained control over recalculation order, `propagate_changes()` is the recommended approach — it's a single call that handles the entire hierarchy.
