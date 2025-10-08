import dash as ds
from App.general.cache_service import cache
from App.general.styles import *

# Set high level layout
def create_app():
    
    # Initialize the dash app
    app = ds.Dash(
        __name__,
        external_stylesheets=[BOOTSTRAP_THEME],
        prevent_initial_callbacks="initial_duplicate",
    )

    # Suppress callback exceptions for easier debugging
    app.config.suppress_callback_exceptions = True
    app.title = "OpenCell"

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
        "App.general.clientside_callbacks",
        "App.general.callbacks",

        "App.current_collectors.callbacks",
        "App.current_collectors.orchestra",

        "App.electrodes.callbacks",
        "App.electrodes.orchestra",

        "App.materials.callbacks",
        # "App.formulations.callbacks",
        # "App.layup.callbacks",
        
        "App.results.callbacks",
        "App.results.orchestra",
    ]

    for module_name in callback_modules:
        importlib.import_module(module_name)


def register_layouts(app):

    from App.general.layouts import stores, thumbnail, header, cell_type, main_tabs

    app.layout = ds.html.Div([
        stores, 
        thumbnail, 
        header, 
        cell_type,  
        main_tabs
    ])


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(debug=True)

