---
title: 'OpenCell Design: An Open-Source Python Library for Construction, Energetic and Technoeconomic Modeling of Battery Cell Designs'
tags:
  - Python
  - battery
  - cell design
  - technoeconomic modeling
  - energy storage
authors:
  - name: Nicholas Siemons
    orcid: 0000-0002-0755-3981
    corresponding: true
    affiliation: 1
  - name: Adrian Yao
    orcid: 0000-0001-9515-3226
    affiliation: 1
  - name: William C. Chueh
    orcid: 0000-0002-7066-3470
    affiliation: 1
affiliations:
  - name: Department of Materials Science and Engineering, Stanford University, Stanford, CA 94305, USA
    index: 1
date: 3 July 2026
bibliography: paper.bib
---

# Summary

OpenCell Design is an open-source Python library that provides a hierarchical, composable API for building virtual battery cells from individual components and materials. The software implements a modeling hierarchy that mirrors the physical construction of a cell — spanning materials, formulations, electrodes, layups, electrode assemblies, encapsulations, and complete cells. Users can construct cylindrical, prismatic, and pouch cell architectures using wound jelly rolls, stacked assemblies, or z-fold stacked assemblies.

OpenCell Design calculates mass and cost at every level of the hierarchy, enabling direct assessment of economic viability alongside electrochemical performance. A propagation system automatically updates all dependent calculations when any parameter changes, eliminating the need to manually rebuild cell models. Interactive browser-based visualizations built on Plotly [@plotly2015] provide immediate feedback through cross-section views, voltage–capacity curves, and hierarchical cost and mass breakdowns.


# Statement of Need

The global transition to electrified transportation and grid-scale energy storage has placed increasing demands on battery technology [@chu2012opportunities; @dunn2011electrical]. Metal-ion batteries are the dominant technology for applications from portable electronics to electric vehicles [@goodenough2013li; @blomgren2017development], and both thermodynamic performance and technoeconomic metrics are critical to their continued development [@nykvist2015rapidly; @ziegler2021re]. Understanding the design and material drivers behind cell performance and cost requires modeling at multiple scales — a single cell comprises dozens of interacting parameters across materials, formulations, current collectors, separators, electrodes, and encapsulations.

OpenCell Design is aimed at battery researchers, cell designers, and technoeconomic analysts who need to connect design and material choices to both electrochemical performance and manufacturing cost within a single, scriptable framework. It provides an open-source, programmatic tool that combines hierarchical cell construction with integrated cost and performance calculations in an extensible, composable framework.

# State of the field

Several tools address aspects of this challenge. PyBaMM [@sulzer2021pybamm] provides physics-based electrochemical simulation but does not model the geometric construction of cells or calculate mass and cost breakdowns. BatPaC [@nelson2019batpac] and CAMS [@cams2024] estimate manufacturing cost and performance but are implemented as Excel workbooks, limiting extensibility and programmatic integration. Both are also unidirectional models — outputs depend on a fixed set of inputs, and bidirectional parameter setting is not possible. Other tools such as electrode formulation calculators address isolated aspects of cell design rather than the complete hierarchy from materials to cells.

Rather than reimplementing electrochemical simulation, OpenCell Design occupies a complementary niche: it focuses on the geometric construction, mass, and cost of a cell across the full materials-to-cell hierarchy, complementing physics-based simulators such as PyBaMM rather than replacing them. This build-versus-contribute trade-off — building a new, open, programmatic construction-and-cost framework where the existing alternatives are closed Excel workbooks or single-scale calculators — is the core scholarly contribution of the software.

# Software design

The software is distributed as three complementary Python packages, each with its own repository, test suite, and documentation:

- **steer-core** ([github.com/stanford-developers/steer-core](https://github.com/stanford-developers/steer-core)) provides foundational utilities shared across the platform, including validation, serialization with LZ4 compression, bidirectional property propagation, type checking, and interactive Plotly-based plotting mixins.
- **steer-materials** ([github.com/stanford-developers/steer-materials](https://github.com/stanford-developers/steer-materials)) defines the material layer — metals, solvents, and volumed material mixins that track density, cost, mass, and volume with automatic unit conversion and range validation.
- **steer-opencell-design** ([github.com/stanford-developers/steer-opencell-design](https://github.com/stanford-developers/steer-opencell-design)) is the primary package described in this paper. It builds on the previous two to implement the full cell-modeling hierarchy from active materials through to complete cells.

This separation of concerns allows each package to be developed, tested, and versioned independently while ensuring that common behaviors — such as serialization, validation, and change propagation — are defined once in `steer-core` and inherited throughout the stack.

Beyond package structure, the central architectural decision is bidirectional property propagation (detailed under *Key Features*): maintaining a parent reference on every component and re-running setters when a parameter changes adds internal bookkeeping, but in exchange users can express design studies — such as comparisons at constant volume or constant N/P ratio — without manually rebuilding a cell after each change.

![The OpenCell Design modeling hierarchy. Components at each level compose into the next, from materials through to complete cells.](hierarchy_tree.png){width=80%}

# Key Features

**Hierarchical modeling architecture.** Components are realized as Python classes organized into a hierarchy that mirrors the physical construction of a cell. Materials are composed into formulations, formulations are coated onto current collectors to form electrodes, electrodes are arranged into layups, layups are wound or stacked into electrode assemblies, and assemblies are encapsulated into complete cells. Properties are calculated at the lowest possible level — specific capacity in the active material, areal capacity in the electrode, total capacity in the cell.

**Bidirectional parameter propagation.** Each object maintains a reference to its parent. When a user modifies a parameter and calls `propagate_changes()`, the system re-assigns the modified object to its parent's setter, triggering recalculation at each level up to the cell. A finer-grained `update()` method propagates changes by a single level, enabling complex studies such as comparing designs at constant volume or constant N/P ratio.

**Extensible object-oriented design.** Base classes implemented as abstract base classes define the interface for each component type. New materials, current collector geometries, and entirely new cell formats can be added by subclassing. To demonstrate this, OpenCell Design includes a flex-frame cell class — a novel solid-state cell architecture — defined in approximately 1,000 lines of code by inheriting the existing base classes and composing existing components.

**Serialization and visualization.** A compact binary serialization format allows cell designs to be saved, shared, and version-controlled. Interactive Plotly-based visualizations provide cross-section views, top-down views, voltage–capacity plots, and sunburst cost/mass breakdowns at any level of the hierarchy.

**Numerical methods.** The library uses NumPy [@harris2020numpy] and SciPy [@virtanen2020scipy] for calculations, including closed-form and adaptive Runge–Kutta integration of thickness-dependent jelly roll spirals accelerated with Numba [@lam2015numba], and Brent's root-finding algorithm [@brent1971algorithm] for constraint satisfaction.

# Quality Control

OpenCell Design includes a comprehensive test suite comprising 21 test modules with over 900 individual test cases, organized to mirror the package structure. Tests cover materials, formulations, electrodes, current collectors, separators, layups, electrode assemblies, containers, and complete cells.

# Research impact statement

OpenCell Design is the computational engine behind the STEER OpenCell platform ([steer.stanford.edu/open-cell](https://steer.stanford.edu/open-cell/)), a publicly available web application for battery cell design and technoeconomic analysis. The platform currently serves more than 580 active users, including practitioners at over 40 battery developer firms, original equipment manufacturers (OEMs), and system integrators — demonstrating adoption well beyond the original development team.

The library has also supported strategic research: it was used to assess the energy-density and cost characteristics of solid-state batteries as part of solid-state battery roadmapping efforts conducted by STEER and the U.S. Department of Energy. The resulting analyses underpin STEER's public solid-state battery tracker ([dash.steerproject.org/steer-ssb-roadmapping](https://dash.steerproject.org/steer-ssb-roadmapping/)).

These deployments are enabled by the software's extensible, object-oriented design — demonstrated, for example, by a novel flex-frame solid-state cell format implemented in roughly 1,000 lines of code by subclassing existing base classes — and are supported by distribution on PyPI and a test suite of 21 modules and over 900 cases that promotes reproducible, verifiable results.

# AI usage disclosure

Generative AI tools were used during the development of OpenCell Design. Specifically, GitHub Copilot was used as a coding assistant to help write portions of the software, its documentation, and this paper. All AI-assisted output was verified for correctness and quality through the project's automated test suite (21 test modules with over 900 test cases) together with thorough manual inspection and review by the authors, who take full responsibility for the correctness of the software and the content of this paper.

# Acknowledgements

We thank the members of the STEER group at Stanford University for their feedback during the development of this software.

# References
