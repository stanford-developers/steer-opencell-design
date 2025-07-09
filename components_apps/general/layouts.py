import dash as ds
from styles import *

from current_collectors.layouts import *
from current_collectors.store import *

stores = ds.html.Div([
    cathode_current_collector_material_store,
    anode_current_collector_material_store,
    cathode_current_collector_store,
    anode_current_collector_store
])

thumbnail = ds.html.Div([
    ds.html.Br(),
    ds.html.Img(src='assets/header_image.png', style={'width': '20%', 'height': 'auto', 'padding-left': '15px'}),
    ds.html.Br(), ds.html.Br(), 
])

header = ds.html.Div([
    ds.html.H1('OpenCell Design Tool', style=HEADER_STYLE | {'padding-left': '20px'}),
    ds.html.P(["Please reach out to Dr. Nicholas Siemons at nsiemons@stanford.edu for help or feedback."], style={'padding-left': '20px'}),
    ds.html.Br(), ds.html.Br(), 
])

warnings = ds.html.Div([
    ds.html.Br(), ds.html.Br(),
    ds.html.H3('Warnings'),
    ds.html.P('This is a placeholder for warnings.'),
], style=DIV_STYLE)

tabs = ds.html.Div([

    ds.html.Div([
    ds.html.Br(), 
    ]),

    ds.dcc.Tabs(
        id='tabs-container',
        children=[
            ds.dcc.Tab(label='Cathode Current Collector', value='cathode_cc', className='tab-style', selected_className='tab-selected-style'),
            ds.dcc.Tab(label='Anode Current Collector', value='anode_cc', className='tab-style', selected_className='tab-selected-style'),
            ds.dcc.Tab(label='Warnings', value='warnings', className='tab-style', selected_className='tab-selected-style')
        ],
        value='cathode_cc',
    ),

    ds.html.Div(id='cathode_cc', children=[cathode_current_collector_layout], style={'display': 'block'}),
    ds.html.Div(id='anode_cc', children=[anode_current_collector_layout], style={'display': 'none'}),
    ds.html.Div(id='warnings', children=[warnings], style={'display': 'none'}),

], style=DIV_STYLE)

