from typing import Type, List, Optional
from dataclasses import dataclass

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector, 
    NotchedCurrentCollector, 
    TablessCurrentCollector, 
    TabWeldedCurrentCollector,
    _CurrentCollector
)

from App.general.enumerated_classes import (
    CollectorType
)

from App.current_collectors.lists import (
    PUNCHED_PARAMETER_LIST,
    PUNCHED_SETTABLE_PARAMETERS,
    NOTCHED_PARAMETER_LIST,
    NOTCHED_SETTABLE_PARAMETERS,
    TABLESS_PARAMETER_LIST,
    TABLESS_SETTABLE_PARAMETERS,
    TABBED_PARAMETER_LIST,
    TABBED_SETTABLE_PARAMETERS,
    TABBED_RADIOITEM_PARAMETERS,
    TABBED_TEXT_PARAMETERS,
    TAPE_RANGE_SLIDER_PARAMETERS
)


@dataclass
class CurrentCollectorConfig:
    """Configuration for different current collector types."""
    collector_type: Type
    parameter_list: List[str]
    settable_parameters: List[str]
    cell_path: List[str]
    range_slider_parameters: Optional[List[str]] = None
    radioitem_parameters: Optional[List[str]] = None
    text_parameters: Optional[List[str]] = None


# Define configurations
COLLECTOR_CONFIGS = {

    CollectorType.CATHODE_PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        parameter_list=PUNCHED_PARAMETER_LIST,
        settable_parameters=PUNCHED_SETTABLE_PARAMETERS,
        cell_path=['cathode', 'current_collector'],
    ),
    CollectorType.CATHODE_NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        parameter_list=NOTCHED_PARAMETER_LIST,
        settable_parameters=NOTCHED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['cathode', 'current_collector'],
    ),
    CollectorType.CATHODE_TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        parameter_list=TABLESS_PARAMETER_LIST,
        settable_parameters=TABLESS_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['cathode', 'current_collector'],
    ),
    CollectorType.CATHODE_TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        parameter_list=TABBED_PARAMETER_LIST,
        settable_parameters=TABBED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['cathode', 'current_collector'],
        radioitem_parameters=TABBED_RADIOITEM_PARAMETERS,
        text_parameters=TABBED_TEXT_PARAMETERS
    ),
    CollectorType.CATHODE_GENERIC: CurrentCollectorConfig(
        collector_type=_CurrentCollector,
        parameter_list=[],
        settable_parameters=[],
        cell_path=['cathode', 'current_collector']
    ),

    CollectorType.ANODE_PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        parameter_list=PUNCHED_PARAMETER_LIST,
        settable_parameters=PUNCHED_SETTABLE_PARAMETERS,
        cell_path=['anode', 'current_collector'],
    ),
    CollectorType.ANODE_NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        parameter_list=NOTCHED_PARAMETER_LIST,
        settable_parameters=NOTCHED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['anode', 'current_collector'],
    ),
    CollectorType.ANODE_TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        parameter_list=TABLESS_PARAMETER_LIST,
        settable_parameters=TABLESS_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['anode', 'current_collector'],
    ),
    CollectorType.ANODE_TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        parameter_list=TABBED_PARAMETER_LIST,
        settable_parameters=TABBED_SETTABLE_PARAMETERS,
        range_slider_parameters=TAPE_RANGE_SLIDER_PARAMETERS,
        cell_path=['anode', 'current_collector'],
        radioitem_parameters=TABBED_RADIOITEM_PARAMETERS,
        text_parameters=TABBED_TEXT_PARAMETERS
    ),
    CollectorType.ANODE_GENERIC: CurrentCollectorConfig(
        collector_type=_CurrentCollector,
        parameter_list=[],
        settable_parameters=[],
        cell_path=['anode', 'current_collector']
    ),

}


