import dash as ds
from styles import *

from App.current_collectors.layouts import *
from App.general.store import *
from App.database_service import *


stores = ds.html.Div([
    cell_store,
    cathode_current_collector_material_store,
    cathode_current_collector_store
])


thumbnail = ds.html.Div([
    ds.html.Br(),
    ds.html.Img(src='assets/header_image.png', style={'width': '20%', 'height': 'auto', 'padding-left': '15px'}),
    ds.html.Br(), ds.html.Br(), 
])


header = ds.html.Div([
    ds.html.H1('OpenCell Design Tool', style=HEADER_STYLE | {'padding-left': '20px'}),
    #ds.html.P(["Please reach out to Dr. Nicholas Siemons at nsiemons@stanford.edu for help or feedback."], style={'padding-left': '20px'}),
    ds.html.Br(), ds.html.Br(), 
])


warnings = ds.html.Div([
    ds.html.Br(), ds.html.Br(),
    ds.html.H3('Warnings'),
    ds.html.P('This is a placeholder for warnings.'),
], style=DIV_STYLE)


cell_type = ds.html.Div(
    
    id='cell_type_panel',

    children=[

    ds.html.Div([
        
        ds.html.H3('Select Cell from Database'), ds.html.Br(),
        ds.html.H5('Form Factor'),

        ds.dcc.Dropdown(
            id='form_factor_dropdown',
            options=[{'label': i.replace('_', ' ').title(), 'value': i} for i in FORM_FACTOR_OPTIONS],
            style={'width': '80%'},
        ),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Internal Construction'),

        ds.dcc.Dropdown(
            id='internal_construction_dropdown',
            options=[],
            style={'width': '80%'},
        ),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Electrochemical Reference'),
        
        ds.dcc.Dropdown(
            id='electrochemical_reference_dropdown',
            options=[],
            style={'width': '80%'},
        ),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Cell Name'),
        
        ds.dcc.Dropdown(
            id='cell_name_dropdown',
            options=[],
            style={'width': '80%'},
        ),

        ds.html.Br(), ds.html.Br(), ds.html.Br(), ds.html.Br(),
        ds.html.H3('... Or Upload Custom Cell'),
        ds.html.Br(),

        ds.html.Div([
            ds.dcc.Upload(
                id='upload_cell', 
                children=[ds.html.A('Select .pkl file for upload', style=BUTTON_STYLE)]
            ),
        ], style={'width': '80%'},),


        # ds.html.Br(), ds.html.Br(), ds.html.Br(), ds.html.Br(),
        # ds.html.H3('... Or Initiate Blank Cell'),
        # ds.html.Br(),

        # ds.html.Div([
        #     ds.html.Button('Initiate Blank Cell', id='initiate_blank_cell', style=BUTTON_STYLE),
        # ], style={'width': '80%'}),

        ds.html.Br(), ds.html.Br(), ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id='continue_to_design',
            children='Continue to Design \t \u2192 ',
            style=BUTTON_STYLE | {'width': '30%', 'border': 'none'},
        ),

        ds.html.Div(style={'height': '200px'})
        ], style={'flex': '0 0 35%', 'padding': '20px', 'justify-content': 'center', 'align-items': 'center'}),

    ds.html.Div(id='cell_schematic', style={'flex': '1', 'padding': '20px', 'justify-content': 'center', 'align-items': 'center'}),
    
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '100px', 'width': '100%'})


tabs = ds.html.Div(
    
    id='tabs_panel',

    children=[

    ds.html.Br(), 

    ds.html.Button(
            id='back_to_cell_type',
            children='\u2190 Back to Cell Type',
            style=BUTTON_STYLE | {'width': '10%', 'border': 'none'},
    ),

    ds.html.Br(), ds.html.Br(), 

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

], style = DIV_STYLE | {'display': 'none'})



