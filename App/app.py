import dash as ds
from App.cache_service import cache

from styles import *

# Initialize the dash app
app = ds.Dash(
    __name__, 
    external_stylesheets=[BOOTSTRAP_THEME],
    prevent_initial_callbacks="initial_duplicate"
)

# Initialize the cache
cache.init_app(app.server)

# Suppress callback exceptions for easier debugging
app.config.suppress_callback_exceptions = True
app.title = 'SteerCellDesignTool'

# Import components
from general.callbacks import *
from current_collectors.callbacks import *
from general.layouts import *

# Set high level layout
def create_app():

    app.layout = ds.html.Div([
        stores,
        thumbnail,
        header,
        cell_type,
        tabs
    ])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    

def run():
    app.run_server(debug=True)


