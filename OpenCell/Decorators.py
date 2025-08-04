from functools import wraps

def calculate_coordinates(func):
    """
    Decorator to recalculate spatial properties after a method call.
    This is useful for methods that modify the geometry of a component.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_coordinates()
        return result
    return wrapper


def calculate_half_cell_curve(func):
    """
    Decorator to recalculate half-cell curve properties after a method call.
    This is useful for methods that modify the half-cell curve data.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_half_cell_curve()
        return result
    return wrapper


def calculate_bulk_properties(func):
    """
    Decorator to recalculate bulk properties after a method call.
    This is useful for methods that modify the material properties.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_bulk_properties()
        return result
    return wrapper


def calculate_all_properties(func):
    """
    Decorator to recalculate both spatial and bulk properties after a method call.
    This is useful for methods that modify both geometry and material properties.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_all_properties()
        return result
    return wrapper


def calculate_areas(func):
    """
    Decorator to recalculate areas after a method call.
    This is useful for methods that modify the geometry of a component.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_coordinates()
            self._calculate_areas()
        return result
    return wrapper


def calculate_weld_tab_properties(func):
    """
    Decorator to recalculate weld tab properties after a method call.
    This is useful for methods that modify the weld tab geometry or material.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_weld_tab_properties()
        return result
    return wrapper


def calculate_half_cell_curves_properties(func):
    """
    Decorator to recalculate half-cell curves properties after a method call.
    This is useful for methods that modify the half-cell curves data.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_update_properties') and self._update_properties:
            self._calculate_half_cell_curves_properties()
        return result
    return wrapper
