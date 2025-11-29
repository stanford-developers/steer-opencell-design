from functools import wraps


def calculate_electrochemical_properties(func):
    """
    Decorator to recalculate electrochemical properties after a method call.
    This is useful for methods that modify properties affecting electrochemical behavior.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_electrochemical_properties()
        return result
    return wrapper

