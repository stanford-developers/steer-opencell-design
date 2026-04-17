"""Geometry extraction helpers for mapping OpenCell designs into PyBaMM inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import UnsupportedCellForPyBaMMError

LITERS_TO_CUBIC_METERS = 1e-3
MILLIMETERS_TO_METERS = 1e-3


@dataclass(frozen=True)
class PyBaMMGeometry:
    """Subset of OpenCell geometry that maps directly into PyBaMM parameters."""

    reference_interfacial_area_m2: float
    electrode_width_m: float
    electrode_height_m: float
    negative_electrode_thickness_m: float
    separator_thickness_m: float
    positive_electrode_thickness_m: float
    negative_current_collector_thickness_m: float
    positive_current_collector_thickness_m: float
    negative_electrode_porosity: float
    separator_porosity: float
    positive_electrode_porosity: float
    negative_electrode_active_material_volume_fraction: float
    positive_electrode_active_material_volume_fraction: float
    nominal_cell_capacity_ah: float
    lower_voltage_cutoff_v: float
    upper_voltage_cutoff_v: float
    cell_volume_m3: float
    electrodes_in_parallel: int

    def to_parameter_values(self) -> dict[str, float]:
        """Return PyBaMM parameter updates derived from the design geometry."""

        nominal_current = self.nominal_cell_capacity_ah
        return {
            "Electrode width [m]": self.electrode_width_m,
            "Electrode height [m]": self.electrode_height_m,
            "Negative electrode thickness [m]": self.negative_electrode_thickness_m,
            "Separator thickness [m]": self.separator_thickness_m,
            "Positive electrode thickness [m]": self.positive_electrode_thickness_m,
            "Negative current collector thickness [m]": self.negative_current_collector_thickness_m,
            "Positive current collector thickness [m]": self.positive_current_collector_thickness_m,
            "Negative electrode porosity": self.negative_electrode_porosity,
            "Separator porosity": self.separator_porosity,
            "Positive electrode porosity": self.positive_electrode_porosity,
            "Negative electrode active material volume fraction": self.negative_electrode_active_material_volume_fraction,
            "Positive electrode active material volume fraction": self.positive_electrode_active_material_volume_fraction,
            "Nominal cell capacity [A.h]": self.nominal_cell_capacity_ah,
            "Lower voltage cut-off [V]": self.lower_voltage_cutoff_v,
            "Upper voltage cut-off [V]": self.upper_voltage_cutoff_v,
            "Cell volume [m3]": self.cell_volume_m3,
            "Number of electrodes connected in parallel to make a cell": float(self.electrodes_in_parallel),
            "Number of cells connected in series to make a battery": 1.0,
            # The rate-capability workflow overrides current via the experiment,
            # but a reasonable nominal 1C value keeps the parameter set coherent.
            "Current function [A]": nominal_current,
            "Typical current [A]": nominal_current,
        }


def extract_pybamm_geometry(cell: Any) -> PyBaMMGeometry:
    """Extract the OpenCell quantities that can be mapped into a DFN parameter set."""

    _validate_supported_cell(cell)

    assembly = cell._reference_electrode_assembly
    layup = assembly._layup
    anode = layup._anode
    cathode = layup._cathode

    if anode._is_anode_free:
        raise UnsupportedCellForPyBaMMError(
            "Phase-1 PyBaMM support requires a paired anode/cathode design; anode-free cells are not supported yet."
        )

    electrode_width_m = min(
        float(anode._current_collector._y_foil_length),
        float(cathode._current_collector._y_foil_length),
    )
    if electrode_width_m <= 0:
        raise UnsupportedCellForPyBaMMError("Unable to derive a positive electrode width for the PyBaMM mapping.")

    reference_interfacial_area_m2 = float(assembly._interfacial_area)
    if reference_interfacial_area_m2 <= 0:
        raise UnsupportedCellForPyBaMMError("Unable to derive a positive interfacial area for the PyBaMM mapping.")

    electrode_height_m = reference_interfacial_area_m2 / electrode_width_m
    nominal_cell_capacity_ah = float(cell.reversible_capacity)
    if nominal_cell_capacity_ah <= 0:
        raise UnsupportedCellForPyBaMMError("The cell must have a positive reversible capacity for DFN simulations.")

    return PyBaMMGeometry(
        reference_interfacial_area_m2=reference_interfacial_area_m2,
        electrode_width_m=electrode_width_m,
        electrode_height_m=electrode_height_m,
        negative_electrode_thickness_m=float(anode._coating_thickness),
        separator_thickness_m=_average(
            float(layup._top_separator._thickness),
            float(layup._bottom_separator._thickness),
        ),
        positive_electrode_thickness_m=float(cathode._coating_thickness),
        negative_current_collector_thickness_m=float(anode._current_collector._thickness),
        positive_current_collector_thickness_m=float(cathode._current_collector._thickness),
        negative_electrode_porosity=float(anode._porosity),
        separator_porosity=_average(
            float(layup._top_separator._material._porosity),
            float(layup._bottom_separator._material._porosity),
        ),
        positive_electrode_porosity=float(cathode._porosity),
        negative_electrode_active_material_volume_fraction=_active_material_volume_fraction(anode._formulation, anode._porosity),
        positive_electrode_active_material_volume_fraction=_active_material_volume_fraction(cathode._formulation, cathode._porosity),
        nominal_cell_capacity_ah=nominal_cell_capacity_ah,
        lower_voltage_cutoff_v=float(cell.minimum_operating_voltage),
        upper_voltage_cutoff_v=float(cell.maximum_operating_voltage),
        cell_volume_m3=_resolve_cell_volume_m3(cell),
        electrodes_in_parallel=int(cell.n_electrode_assembly),
    )


def _validate_supported_cell(cell: Any) -> None:
    """Gate the phase-1 workflow to liquid-electrolyte OpenCell formats."""

    cell_type = cell.__class__.__name__
    if cell_type == "FlexFrameCell":
        raise UnsupportedCellForPyBaMMError(
            "FlexFrameCell is intentionally out of scope for the phase-1 DFN integration."
        )
    if cell_type not in {"CylindricalCell", "PouchCell", "PrismaticCell"}:
        raise UnsupportedCellForPyBaMMError(
            f"{cell_type} is not supported by the phase-1 PyBaMM integration."
        )


def _active_material_volume_fraction(formulation: Any, porosity: float) -> float:
    """Estimate the active-material volume fraction in the porous composite electrode."""

    active_specific_volume = sum(
        float(weight_fraction) / float(material._density)
        for material, weight_fraction in formulation._active_materials.items()
    )
    total_specific_volume = float(formulation._specific_volume)
    if total_specific_volume <= 0:
        raise UnsupportedCellForPyBaMMError(
            f"Formulation `{formulation.name}` has an invalid specific volume for PyBaMM mapping."
        )

    active_fraction_in_solids = active_specific_volume / total_specific_volume
    active_fraction_in_electrode = (1.0 - float(porosity)) * active_fraction_in_solids
    return max(0.0, min(1.0, active_fraction_in_electrode))


def _resolve_cell_volume_m3(cell: Any) -> float:
    """Prefer the existing cell volume calculation, then fall back to external geometry."""

    cell_volume_l = cell.volume
    if cell_volume_l is not None:
        return float(cell_volume_l) * LITERS_TO_CUBIC_METERS

    if hasattr(cell, "diameter") and hasattr(cell, "height"):
        radius_m = (float(cell.diameter) * MILLIMETERS_TO_METERS) / 2.0
        height_m = float(cell.height) * MILLIMETERS_TO_METERS
        return 3.141592653589793 * radius_m**2 * height_m

    if hasattr(cell, "width") and hasattr(cell, "height") and hasattr(cell, "thickness"):
        width_m = float(cell.width) * MILLIMETERS_TO_METERS
        height_m = float(cell.height) * MILLIMETERS_TO_METERS
        thickness_m = float(cell.thickness) * MILLIMETERS_TO_METERS
        return width_m * height_m * thickness_m

    raise UnsupportedCellForPyBaMMError("Unable to determine cell volume for the PyBaMM mapping.")


def _average(lhs: float, rhs: float) -> float:
    """Return the mean of two scalar values."""

    return (float(lhs) + float(rhs)) / 2.0
