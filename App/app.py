import dash as ds
from callbacks import *
import layouts
from styles import *

app = ds.Dash(__name__, external_stylesheets=[BOOTSTRAP_THEME])
app.config.suppress_callback_exceptions = True
app.title = 'SteerCellDesignTool'

def create_app():

    app.layout = ds.html.Div([

        ds.html.Br(),
        ds.html.Img(src='assets/header_image.png', style={'width': '20%', 'height': 'auto', 'padding-left': '7px'}),
        ds.html.Br(), ds.html.Br(), 

        layouts.data_stores,

        ds.html.H1('Cell Design Tool', style=HEADER_STYLE | {'padding-left': '10px'}),
        ds.html.Br(), ds.html.Br(), 

        layouts.cell_construction,
        layouts.cell_operation,
        layouts.tab_container,
        layouts.cell_analysis

    ])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    

def run():
    app.run_server(debug=True)



