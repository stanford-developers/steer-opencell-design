import dash_bootstrap_components as dbc
import plotly.graph_objects as go

BOOTSTRAP_THEME = dbc.themes.LUX
HEADER_STYLE = {'textAlign': 'left'}
DROPDOWN_STYLE = {'width': '50%'}
BUTTON_STYLE = {'margin-left': '10px', 'background-color': 'white', 'border': '1px solid #ccc', 'padding': '5px 10px', 'cursor': 'pointer'}
ADD_REMOVE_BUTTON_STYLE = {
    'backgroundColor': '#f8f9fa',
    'color': 'black',
    'border': 'none',
    'borderRadius': '50%',
    'width': '30px',
    'height': '30px',
    'fontSize': '16px',
    'cursor': 'pointer'
}
ADD_REMOVE_BUTTON_CONTAINER_STYLE = {'marginTop': '10px', 'marginBottom': '20px'}
INPUT_STYLE = {'width': '16%', 'margin-left': '10px'}
TEXT_INPUT_STYLE = {'width': '100%', 'margin-left': '10px', 'margin-bottom': '15px'}
DIV_STYLE = {'margin-left': '20px', 'margin-right': '20px', 'width': 'calc(100)'}
BUTTON_DIV_STYLE = {'display': 'flex', 'gap': '10px', 'margin-left': '-10px'}

RIGHT_PANEL_COLOR = '#e3e5e6'

EMPTY_FIG = go.Figure()
EMPTY_FIG.update_layout(paper_bgcolor=RIGHT_PANEL_COLOR, plot_bgcolor=RIGHT_PANEL_COLOR)