import dash as ds
import dash_bootstrap_components as dbc
from callbacks import *
import layouts

BOOTSTRAP_THEME = dbc.themes.LUX
HEADER_STYLE = {'textAlign': 'left', 'padding-left': '15px'}

app = ds.Dash(__name__, external_stylesheets=[BOOTSTRAP_THEME])
app.config.suppress_callback_exceptions = True
app.title = 'SteerCellDesignTool'

def create_app():
    app.layout = ds.html.Div([

        ds.html.Br(),
        ds.html.Img(src='assets/header_image.png', style={'width': '30%', 'height': 'auto'}),
        ds.html.Br(), ds.html.Br(),

        ds.html.H1('Cell Design Tool', style=HEADER_STYLE),
        ds.html.Br(), ds.html.Br(),

        ds.dcc.Tabs(
            children=[
                ds.dcc.Tab(label='Cell Construction', value='cell_construction', children=[layouts.cell_construction]),
                ds.dcc.Tab(label='Cathode Design', value='cathode_design', children=[layouts.cathode_design]),
                ds.dcc.Tab(label='Anode Design', value='anode_design', children=[layouts.anode_design]),
                ds.dcc.Tab(label='Encapsulation', value='encapsulation', children=[layouts.encapsulation]),
                ds.dcc.Tab(label='Cell Analysis', value='cell_analysis', children=[layouts.cell_analysis])
            ], 
            value='cell_construction')
    ])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

def run():
    app.run_server(debug=True)



