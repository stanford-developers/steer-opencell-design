from typing import Type, List
from enum import Enum
from dataclasses import dataclass
from steer_opencell_design.Formulations.ElectrodeFormulations import (
    CathodeFormulation,
    AnodeFormulation,
)


class FormulationType(Enum):
    CATHODE = "cathode_formulation"
    ANODE = "anode_formulation"


@dataclass
class FormulationConfig:
    """Configuration for different formulation types."""
    formulation_type: Type
    cell_path: List[str]
    parameter_list: List[str]


# Define configurations
FORMULATION_CONFIGS = {
    FormulationType.CATHODE: FormulationConfig(
        formulation_type=CathodeFormulation,
        cell_path=["cathode", "formulation"],
        parameter_list=[
            "voltage_cutoff",
        ],
    ),
    FormulationType.ANODE: FormulationConfig(
        formulation_type=AnodeFormulation,
        cell_path=["anode", "formulation"],
        parameter_list=[
            "voltage_cutoff",
        ],
    ),
}
