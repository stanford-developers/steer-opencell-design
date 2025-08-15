import dash as ds
from cache_service import cache
from styles import *

import sys
import os
# Ensure the App directory is in sys.path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)


# Import components
from general.callbacks import *
from current_collectors.callbacks import *
from electrodes.callbacks import *

# Set high level layout
def create_app():

    # Initialize the dash app
    app = ds.Dash(
        __name__, 
        external_stylesheets=[BOOTSTRAP_THEME],
        prevent_initial_callbacks="initial_duplicate"
    )

    # Suppress callback exceptions for easier debugging
    app.config.suppress_callback_exceptions = True
    app.title = 'OpenCell'

    # Initialize the cache
    cache.init_app(app.server)

    # Lazy load callbacks only when needed
    register_callbacks(app)
    register_layouts(app)

    return app


def register_callbacks(app):
    """Register callbacks using importlib to avoid import * in function."""
    import importlib
    
    # Import callback modules dynamically
    callback_modules = [
        'general.callbacks',
        'current_collectors.callbacks', 
        'electrodes.callbacks',
        'materials.callbacks',
        'general.clientside_callbacks'
    ]
    
    for module_name in callback_modules:
        importlib.import_module(module_name)


def register_layouts(app):

    from general.layouts import stores, thumbnail, header, cell_type, main_tabs
    
    app.layout = ds.html.Div([
        stores,
        thumbnail,
        header,
        cell_type,
        main_tabs
    ])


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    

def run():
    app.run_server(debug=True)


