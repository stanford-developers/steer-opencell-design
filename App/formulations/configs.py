from typing import Type, List
from dataclasses import dataclass
from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)
from App.general.enumerated_classes import FormulationType

from App.formulations.lists import (
    FORMULATION_PARAMETER_LIST,
    FORMULATION_SETTABLE_PARAMETERS,
)


@dataclass
class FormulationConfig:
    """Configuration for different current collector types."""

    formulation_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]


# Define configurations
FORMULATION_CONFIGS = {
    FormulationType.CATHODE: FormulationConfig(
        formulation_type=CathodeFormulation,
        parameter_list=FORMULATION_PARAMETER_LIST,
        settable_parameters=FORMULATION_SETTABLE_PARAMETERS,
        cell_path=["cathode", "formulation"],
    ),
    FormulationType.ANODE: FormulationConfig(
        formulation_type=AnodeFormulation,
        parameter_list=FORMULATION_PARAMETER_LIST,
        settable_parameters=FORMULATION_SETTABLE_PARAMETERS,
        cell_path=["anode", "formulation"],
    ),
}
