import dash as ds
from styles import *

app = ds.Dash(__name__, external_stylesheets=[BOOTSTRAP_THEME])
app.config.suppress_callback_exceptions = True
app.title = 'SteerCellDesignTool'

def create_app():

    app.layout = ds.html.Div([

        ds.html.Br(),
        ds.html.Img(src='assets/header_image.png', style={'width': '20%', 'height': 'auto', 'padding-left': '15px'}),
        ds.html.Br(), ds.html.Br(), 

        ds.html.H3('Cell Design Tool', style=HEADER_STYLE | {'padding-left': '20px'}),
        
        ds.html.P(["Please reach out to Dr. Nicholas Siemons at nsiemons@stanford.edu for help or feedback."], style={'padding-left': '20px'}),

    ])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    

def run():
    app.run_server(debug=True)



