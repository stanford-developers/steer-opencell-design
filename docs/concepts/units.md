# Units Convention

All classes in `steer-opencell-design` follow a consistent set of units.

## Standard Units

| Quantity | Unit | Notes |
|---|---|---|
| Length, width, height | mm | Macro dimensions |
| Thickness | μm | Coatings, foils, separators, tapes |
| Mass loading | mg/cm² | Electrode coating loading |
| Density | g/cm³ | Material and formulation densities |
| Specific cost | $/kg | Material cost |
| Porosity | % | Separator and electrode porosity |
| Weight fractions | % | Formulation component fractions |

## Cell-Level Outputs

| Quantity | Unit |
|---|---|
| Energy | Wh |
| Mass | g |
| Cost | $ |
| Volume | L |
| Specific energy | Wh/kg |
| Volumetric energy density | Wh/L |
| Cost per energy | $/kWh |
| Capacity | Ah |

## Electrochemical Quantities

| Quantity | Unit |
|---|---|
| Voltage | V |
| Specific capacity | mAh/g |
| Areal capacity | mAh/cm² |

!!! note
    Thickness parameters (coatings, foils, separators, tapes) use **μm**, while macro dimensions (length, width, height) use **mm**. Pay attention to this distinction when setting properties.
