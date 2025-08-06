import dash as ds
from styles import *

electrode_assembly_layout = ds.html.Div(
    id='electrode_assembly_layout',
    children=[
        ds.html.P("This is the electrode assembly layout."),
    ],
    style=DIV_STYLE | {'display': 'block'}
)