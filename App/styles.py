import dash_bootstrap_components as dbc
import plotly.graph_objects as go

BOOTSTRAP_THEME = dbc.themes.LUX
HEADER_STYLE = {'textAlign': 'left'}
DROPDOWN_STYLE = {'width': '50%'}
BUTTON_STYLE = {'margin-left': '10px', 'background-color': 'white', 'border': '1px solid #ccc', 'padding': '5px 10px', 'cursor': 'pointer'}
INPUT_STYLE = {'width': '16%', 'margin-left': '10px'}
TEXT_INPUT_STYLE = {'width': '100%', 'margin-left': '10px', 'margin-bottom': '15px'}

SEPARATOR_COLOR = "#585600"
CATHODE_COLOR = '#FF8C00'
ANODE_COLOR = "#0048FF"
CURRENT_COLLECTOR_COLOR = '#C0C0C0'
LID_COLOR = "#8D8D8D"

RIGHT_PANEL_COLOR = '#e3e5e6'

EMPTY_FIG = go.Figure()
EMPTY_FIG.update_layout(paper_bgcolor=RIGHT_PANEL_COLOR, plot_bgcolor=RIGHT_PANEL_COLOR)