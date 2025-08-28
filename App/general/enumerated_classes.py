from enum import Enum, auto



# =============================================================================
# Component and UI Related Enums
# =============================================================================

class SubType(Enum):
    SLIDER = 'slider'
    INPUT = 'input'
    RANGESLIDER = 'rangeslider'
    INPUT_START = 'input_start'
    INPUT_END = 'input_end'
    RADIOITEM = 'radioitem'
    TEXT_INPUT = 'text_input'


class TriggerType(Enum):
    CELL_STORE = 'cell_store'
    PROPERTY = 'property'
    ACTION = 'action'
    RADIOITEM = 'radioitem'
    COMPONENT_SELECTOR = 'component_selector'
    BUTTON = 'button'
    INDEXED_DROPDOWN = 'indexed_dropdown'


class ActionType(Enum):
    FLIP_X = 'flip_x'
    FLIP_Y = 'flip_y'
    ROTATE = 'rotate'

class TabWeldSide(Enum):
    A_SIDE = 'a'
    B_SIDE = 'b'


class CategoricalProperty(Enum):
    """Categorical properties that don't have ranges."""
    TAB_WELD_SIDE = 'tab_weld_side'


class PropertyCategory(Enum):
    """Categories of properties."""
    NUMERICAL = auto()
    CATEGORICAL = auto()
    RANGE = auto()




# =============================================================================
# Physical Component Enums
# =============================================================================

class CollectorType(Enum):
    PUNCHED = 'punched'
    NOTCHED = 'notched'
    TABLESS = 'tabless'
    TABBED = 'tabbed'
    GENERIC = 'generic'

class ElectrodeType(Enum):
    CATHODE = 'cathode'
    ANODE = 'anode'
    GENERIC = 'generic'

class MaterialType(Enum):
    CATHODE_CURRENT_COLLECTOR = 'cathode_current_collector'
    CATHODE_CURRENT_COLLECTOR_TAB = 'cathode_current_collector_tab'
    CATHODE_INSULATION = 'cathode_insulation'
    ANODE_CURRENT_COLLECTOR = 'anode_current_collector'
    ANODE_CURRENT_COLLECTOR_TAB = 'anode_current_collector_tab'
    ANODE_INSULATION = 'anode_insulation'
    BINDER = 'binder'
    CONDUCTIVE_ADDITIVE = 'conductive_additive'
    ACTIVE_MATERIAL = 'active_material'

class FormulationType(Enum):
    CATHODE = 'cathode_formulation'
    ANODE = 'anode_formulation'

