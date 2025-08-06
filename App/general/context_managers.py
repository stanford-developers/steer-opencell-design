import warnings
import time
from contextlib import contextmanager
from typing import List, Dict

@contextmanager
def capture_warnings(existing_warnings: List[Dict] = None, source: str = None, clear_source_warnings: bool = True):
    """
    Context manager to capture warnings and format them for Dash.
    
    Parameters
    ----------
    existing_warnings : List[Dict], optional
        Existing warnings to append to
    source : str, optional
        Source identifier for the warnings
    clear_source_warnings : bool, optional
        Whether to clear existing warnings from the same source before adding new ones
        
    Yields
    ------
    List[Dict]
        The combined list of warnings (existing + new)
    """
    if existing_warnings is None:
        existing_warnings = []
    
    # Clear existing warnings from the same source if requested
    if clear_source_warnings and source:
        existing_warnings = [w for w in existing_warnings if w.get('source') != source]
    
    with warnings.catch_warnings(record=True) as warnings_list:
        warnings.simplefilter("always")
        
        # Yield the cleaned warnings list
        yield existing_warnings
        
        # Process any new warnings after the operation
        new_warnings = []
        for w in warnings_list:
            new_warnings.append({
                'message': str(w.message),
                'category': w.category.__name__,
                'filename': w.filename,
                'lineno': w.lineno,
                'timestamp': time.time(),
                'source': source or 'unknown',
                'id': f"{source}_{int(time.time())}" if source else f"warning_{int(time.time())}"
            })
        
        # Add new warnings
        existing_warnings.extend(new_warnings)

