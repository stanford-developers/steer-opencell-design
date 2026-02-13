"""Decorators for automatic property recalculation."""

from functools import wraps


def calculate_electrochemical_properties(func):
    """
    Decorator to conditionally recalculate electrochemical properties after a method call.

    After the decorated method executes, if ``self._update_properties`` is truthy,
    ``self._calculate_electrochemical_properties()`` is called to recompute derived
    electrochemical values. The decorated object must have both ``_update_properties``
    (attribute) and ``_calculate_electrochemical_properties()`` (method).

    This is typically applied to property setters that modify parameters affecting
    electrochemical behavior (e.g., voltage cutoffs, capacity scaling).
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_electrochemical_properties()
        return result
    return wrapper

