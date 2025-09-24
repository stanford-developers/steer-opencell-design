from enum import Enum

from App.general.enumerated_classes import TriggerType


class TriggerRouter:
    """Routes callback triggers to appropriate handlers using enums."""

    # Define string patterns for component selectors
    COMPONENT_SELECTOR_PATTERNS = [
        "_material_selector",
        "_design_selector",
        "_type_selector",
    ]

    @staticmethod
    def get_trigger_type(triggered_id, trigger_property=None) -> TriggerType:
        """Determine the type of trigger."""

        if triggered_id is None:
            return None

        # Check trigger property first
        if trigger_property == "style":
            return TriggerType.STYLE

        # Handle string triggers
        if isinstance(triggered_id, str):
            return TriggerRouter._handle_string_trigger(triggered_id)

        # Handle dict triggers
        elif isinstance(triggered_id, dict):
            return TriggerRouter._handle_dict_trigger(triggered_id)

        raise ValueError(f"Unknown trigger type: {triggered_id}")

    @staticmethod
    def _handle_string_trigger(triggered_id: str) -> TriggerType:
        """Handle string-based triggers."""

        # Check for exact enum matches first
        if triggered_id == TriggerType.CELL_STORE.value:
            return TriggerType.CELL_STORE

        # Check for button triggers
        if "button" in triggered_id:
            return TriggerType.BUTTON

        # Check for component selector patterns
        for pattern in TriggerRouter.COMPONENT_SELECTOR_PATTERNS:
            if triggered_id.endswith(pattern):
                return TriggerType.COMPONENT_SELECTOR

        raise ValueError(f"Unknown string trigger: {triggered_id}")

    @staticmethod
    def _handle_dict_trigger(triggered_id: dict) -> TriggerType:
        """Handle dictionary-based triggers."""

        if "property" in triggered_id:
            return TriggerType.PROPERTY

        elif "action" in triggered_id:
            return TriggerType.ACTION

        elif "index" in triggered_id and triggered_id.get("subtype") == "dropdown":
            return TriggerType.INDEXED_DROPDOWN

        elif triggered_id.get("subtype") == "weight_fraction":
            return TriggerType.WEIGHT_FRACTION

        raise ValueError(f"Unknown dict trigger: {triggered_id}")

    @staticmethod
    def is_component_selector(triggered_id: str) -> bool:
        """Check if trigger is a component selector."""
        return any(triggered_id.endswith(pattern) for pattern in TriggerRouter.COMPONENT_SELECTOR_PATTERNS)

    @staticmethod
    def get_component_type_from_selector(triggered_id: str) -> str:
        """Extract component type from selector ID."""
        for pattern in TriggerRouter.COMPONENT_SELECTOR_PATTERNS:
            if triggered_id.endswith(pattern):
                return triggered_id.replace(pattern, "")

        return triggered_id
