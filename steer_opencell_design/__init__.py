# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
STEER OpenCell Design — A Python package for designing and modeling battery cells.

This package provides a hierarchical, composable API for building virtual battery
cells from raw materials up to complete cell assemblies. The modeling hierarchy is::

    Materials → Formulations → Electrodes → Layups → Assemblies → Cells

Supported cell formats:
    - Cylindrical (e.g., 18650, 21700, 4680)
    - Prismatic (hard-case)
    - Pouch (soft-pack)
    - Flex-frame (solid-state)

All public classes are re-exported from this top-level namespace for convenience::

    import steer_opencell_design as ocd
    cell = ocd.CylindricalCell(...)

Unit and curve contract
-----------------------
Values are stored internally in SI base units and converted to more
convenient industry units at the public API boundary.

**Internal SI storage:**

- Charge: ampere-seconds (A·s).
- Mass: kilograms (kg).
- Length, area, volume: metres (m, m², m³).
- Voltage: volts (V, referenced to Li/Li+ for half-cell curves).
- Specific cost: $/kg.

**Public-API units:**

- Capacity properties (e.g. ``cell.irreversible_capacity``) return
  ampere-hours (Ah); DataFrame columns are labelled ``"Capacity (Ah)"``.
- Densities / loadings in the Dash UI are exposed in g/cm³, mg/cm², etc.

**Curve ndarray layout** (applies to ``_specific_capacity_curve`` and
``_areal_capacity_curve`` on active materials, formulations, electrodes,
layups, assemblies and cells):

- Column 0: charge (A·s/kg for specific, A·s/m² for areal, A·s for full-cell).
- Column 1: voltage (V vs Li/Li+ for half-cell curves; full-cell OCV for cells).
- Column 2: direction flag, ``+1`` for charge and ``-1`` for discharge.

**N/P ratio (``layup.np_ratio``):** ratio of the maximum areal capacity of
the anode to the maximum areal capacity of the cathode (i.e. ratio of the
max x-axis values on the paired areal-capacity curves; see
``steer_core.CurveComposition``). This is *not* a textbook
reversible-capacity N/P unless the two Q_max points correspond to the same
SOC window.

**Full-cell OCV construction:** the full-cell capacity curve is
``V_full = V_cathode − V_anode`` at matched areal capacity; the full-cell
capacity axis is the intersection of the two electrode areal-capacity
ranges.

**Anode-free convention:** anode-free designs use
``Anode(formulation=None, ...)`` with a ``V = 0`` voltage proxy and
``layup.np_ratio = inf``.
"""

__version__ = "1.0.41"

# Register OpenCell domain tables with the base DataManager so
# that URL routing (materials/ vs cells/) works for any DataManager instance.
from steer_opencell_design.Data.OpenCellDataManager import register_opencell_tables as _register_tables  # noqa: E402
_register_tables()

# import materials
from .Materials.ActiveMaterials import CathodeMaterial, AnodeMaterial
from .Materials.Binders import Binder
from .Materials.ConductiveAdditives import ConductiveAdditive
from .Materials.Electrolytes import Electrolyte
from .Materials.Other import TapeMaterial, SeparatorMaterial, CurrentCollectorMaterial, PrismaticContainerMaterial, LaminateMaterial, InsulationMaterial, FlexFrameMaterial

# import formulations
from .Materials.Formulations import AnodeFormulation, CathodeFormulation

# import current collectors
from .Components.CurrentCollectors.Notched import NotchedCurrentCollector
from .Components.CurrentCollectors.Tabbed import TabWeldedCurrentCollector, WeldTab
from .Components.CurrentCollectors.Punched import PunchedCurrentCollector
from .Components.CurrentCollectors.Tabless import TablessCurrentCollector

# import electrodes
from .Components.Electrodes import Cathode, Anode
from .Components.Separators import Separator

# import layups
from .Constructions.Layups.Base import NPRatioControlMode
from .Constructions.Layups.OverhangUtils import OverhangControlMode
from .Constructions.Layups.Laminate import Laminate
from .Constructions.Layups.MonoLayers import ZFoldMonoLayer, MonoLayer

# import electrode assemblies
from .Constructions.ElectrodeAssemblies.Tape import Tape
from .Constructions.ElectrodeAssemblies.JellyRolls import WoundJellyRoll, FlatWoundJellyRoll
from .Constructions.ElectrodeAssemblies.Stacks import ZFoldStack, PunchedStack
from .Constructions.ElectrodeAssemblies.WindingEquipment import RoundMandrel, FlatMandrel

# import containers
from .Components.Containers.Cylindrical import CylindricalCanister, CylindricalEncapsulation, CylindricalLidAssembly, CylindricalTerminalConnector
from .Components.Containers.Pouch import PouchEncapsulation, LaminateSheet, PouchTerminal
from .Components.Containers.Prismatic import PrismaticCanister, PrismaticEncapsulation, PrismaticLidAssembly, PrismaticTerminalConnector
from .Components.Containers.Flexframe import FlexFrame, FlexFrameEncapsulation

# import cells
from .Constructions.Cells.CylindricalCell import CylindricalCell
from .Constructions.Cells.PrismaticCell import PrismaticCell
from .Constructions.Cells.PouchCell import PouchCell
from .Constructions.Cells.FlexFrameCell import FlexFrameCell

# import simulation helpers
from .Simulation import (
    DFNRunner,
    MissingPyBaMMDependencyError,
    MissingPyBaMMParametersError,
    PyBaMMGeometry,
    PyBaMMIntegrationError,
    RateCapabilityResult,
    RateCurveResult,
    UnsupportedCellForPyBaMMError,
    build_pybamm_parameter_values,
    extract_pybamm_geometry,
    simulate_rate_capability,
    validate_pybamm_parameter_values,
)







