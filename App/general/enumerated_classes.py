from enum import Enum, auto


# =============================================================================
# Component and UI Related Enums
# =============================================================================


class SubType(Enum):
    SLIDER = "slider"
    INPUT = "input"
    RANGESLIDER = "rangeslider"
    INPUT_START = "input_start"
    INPUT_END = "input_end"
    RADIOITEM = "radioitem"
    TEXT_INPUT = "text_input"


class TriggerType(Enum):
    CELL_STORE = "cell_store"
    STYLE = "style"
    PROPERTY = "property"
    ACTION = "action"
    RADIOITEM = "radioitem"
    COMPONENT_SELECTOR = "component_selector"
    BUTTON = "button"
    INDEXED_DROPDOWN = "indexed_dropdown"
    WEIGHT_FRACTION = "weight_fraction"
    DROPDOWN = "dropdown"


class ActionType(Enum):
    FLIP_X = "flip_x"
    FLIP_Y = "flip_y"
    ROTATE = "rotate"


class TabWeldSide(Enum):
    A_SIDE = "a"
    B_SIDE = "b"


class CategoricalProperty(Enum):
    """Categorical properties that don't have ranges."""

    TAB_WELD_SIDE = "tab_weld_side"


class PropertyCategory(Enum):
    """Categories of properties."""

    NUMERICAL = auto()
    CATEGORICAL = auto()
    RANGE = auto()
