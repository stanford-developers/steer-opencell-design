from typing import Type, List, Optional
from dataclasses import dataclass
from enum import Enum, auto

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector,
    _CurrentCollector,
)

# define CollectorType enum
class CollectorType(Enum):
    CATHODE_PUNCHED = "cathode_punched"
    CATHODE_NOTCHED = "cathode_notched"
    CATHODE_TABLESS = "cathode_tabless"
    CATHODE_TABBED = "cathode_tabbed"
    CATHODE_GENERIC = "cathode_generic"
    ANODE_PUNCHED = "anode_punched"
    ANODE_NOTCHED = "anode_notched"
    ANODE_TABLESS = "anode_tabless"
    ANODE_TABBED = "anode_tabbed"
    ANODE_GENERIC = "anode_generic"

# define a dataclass for current collector configurations
@dataclass
class CurrentCollectorConfig:
    """Configuration for different current collector types."""
    collector_type: Type
    cell_path: List[str]
    parameter_list: List[str]
    range_slider_parameters: Optional[List[str]] = None
    radioitem_parameters: Optional[List[str]] = None
    text_parameters: Optional[List[str]] = None


# Define configurations
COLLECTOR_CONFIGS = {
    CollectorType.CATHODE_PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        cell_path=["cathode", "current_collector"],
        parameter_list=[
            "width",
            "height",
            "thickness",
            "tab_width",
            "tab_height",
            "tab_position",
            "coated_tab_height",
            "insulation_width",
        ],
    ),
    CollectorType.CATHODE_NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        cell_path=["cathode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "tab_width",
            "tab_height",
            "tab_spacing",
            "tab_gap",
            "coated_tab_height",
            "insulation_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
    ),
    CollectorType.CATHODE_TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        cell_path=["cathode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "coated_width",
            "tab_height",
            "insulation_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
    ),
    CollectorType.CATHODE_TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        cell_path=["cathode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "tab_width",
            "tab_length",
            "tab_overhang",
            "skip_coat_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
        radioitem_parameters=[
            "tab_weld_side",
        ],
        text_parameters=[
            "tab_positions_text",
        ],
    ),
    CollectorType.CATHODE_GENERIC: CurrentCollectorConfig(
        collector_type=_CurrentCollector,
        cell_path=["cathode", "current_collector"],
        parameter_list=[],
    ),
    CollectorType.ANODE_PUNCHED: CurrentCollectorConfig(
        collector_type=PunchedCurrentCollector,
        cell_path=["anode", "current_collector"],
        parameter_list=[
            "width",
            "height",
            "thickness",
            "tab_width",
            "tab_height",
            "tab_position",
            "coated_tab_height",
            "insulation_width",
        ],
    ),
    CollectorType.ANODE_NOTCHED: CurrentCollectorConfig(
        collector_type=NotchedCurrentCollector,
        cell_path=["anode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "tab_width",
            "tab_height",
            "tab_spacing",
            "tab_gap",
            "coated_tab_height",
            "insulation_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
    ),
    CollectorType.ANODE_TABLESS: CurrentCollectorConfig(
        collector_type=TablessCurrentCollector,
        cell_path=["anode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "coated_width",
            "tab_height",
            "insulation_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
    ),
    CollectorType.ANODE_TABBED: CurrentCollectorConfig(
        collector_type=TabWeldedCurrentCollector,
        cell_path=["anode", "current_collector"],
        parameter_list=[
            "length",
            "width",
            "thickness",
            "tab_width",
            "tab_length",
            "tab_overhang",
            "skip_coat_width",
        ],
        range_slider_parameters=[
            "a_side_coated_section",
            "b_side_coated_section",
        ],
        radioitem_parameters=[
            "tab_weld_side",
        ],
        text_parameters=[
            "tab_positions_text",
        ],
    ),
    CollectorType.ANODE_GENERIC: CurrentCollectorConfig(
        collector_type=_CurrentCollector,
        cell_path=["anode", "current_collector"],
        parameter_list=[],
    ),
}

