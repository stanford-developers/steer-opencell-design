from enum import Enum, auto

class CollectorType(Enum):
    PUNCHED = 'punched'
    NOTCHED = 'notched'
    TABLESS = 'tabless'
    TABBED = 'tabbed'

class ElectrodeType(Enum):
    CATHODE = 'cathode'
    ANODE = 'anode'

class MaterialType(Enum):
    CATHODE_CURRENT_COLLECTOR = 'cathode_current_collector'
    CATHODE_CURRENT_COLLECTOR_TAB = 'cathode_current_collector_tab'
    ANODE_CURRENT_COLLECTOR = 'anode_current_collector'
    ANODE_CURRENT_COLLECTOR_TAB = 'anode_current_collector_tab'

class TriggerType(Enum):
    CELL_STORE = 'cell_store'
    PROPERTY = 'property'
    ACTION = 'action'
    RADIOITEM = 'radioitem'

class SubType(Enum):
    SLIDER = 'slider'
    INPUT = 'input'
    RANGESLIDER = 'rangeslider'
    INPUT_START = 'input_start'
    INPUT_END = 'input_end'
    RADIOITEM = 'radioitem'
    TEXT_INPUT = 'text_input'

class ActionType(Enum):
    FLIP_X = 'flip_x'
    FLIP_Y = 'flip_y'

class TabWeldSide(Enum):
    A_SIDE = 'a'
    B_SIDE = 'b'

class PropertyCategory(Enum):
    """Categories of properties."""
    NUMERICAL = auto()
    CATEGORICAL = auto()
    RANGE = auto()

class CategoricalProperty(Enum):
    """Categorical properties that don't have ranges."""
    TAB_WELD_SIDE = 'tab_weld_side'

