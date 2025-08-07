from typing import Type, List, Optional
from dataclasses import dataclass

from steer_opencell_design.Materials.CurrentCollectors import (
    PunchedCurrentCollector, 
    NotchedCurrentCollector, 
    TablessCurrentCollector, 
    TabWeldedCurrentCollector
)

from general.enumerated_classes import (
    CollectorType
)

from current_collectors.parameter_lists import (
    PUNCHED_PARAMETER_LIST,
    PUNCHED_SETTABLE_PARAMETERS,
    NOTCHED_PARAMETER_LIST,
    NOTCHED_SETTABLE_PARAMETERS,
    TABLESS_PARAMETER_LIST,
    TABLESS_SETTABLE_PARAMETERS,
    TABBED_PARAMETER_LIST,
    TABBED_SETTABLE_PARAMETERS,
    TAPE_RANGE_SLIDER_PARAMETERS
)


@dataclass
class CurrentCollectorConfig:
    """Configuration for different current collector types."""
    collector_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    range_slider_parameters: Optional[List[str]] = None


# Define configurations
COLLECTOR_CONFIGS = {
    CollectorType.PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        parameter_list=PUNCHED_PARAMETER_LIST,
        settable_parameters=PUNCHED_SETTABLE_PARAMETERS
    ),
    CollectorType.NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        parameter_list=NOTCHED_PARAMETER_LIST,
        settable_parameters=NOTCHED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    ),
    CollectorType.TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        parameter_list=TABLESS_PARAMETER_LIST,
        settable_parameters=TABLESS_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    ),
    CollectorType.TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        parameter_list=TABBED_PARAMETER_LIST,
        settable_parameters=TABBED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS
    )
}


