import dash as ds
from App.styles import *

from App.current_collectors.layouts import cathode_current_collector_layout
from App.formulations.layouts import cathode_formulation_layout
from App.electrodes.layouts import cathode_electrode_layout

from App.current_collectors.layouts import anode_current_collector_layout
from App.formulations.layouts import anode_formulation_layout
from App.electrodes.layouts import anode_electrode_layout

from App.electrode_assembly.layouts import electrode_assembly_layout

from App.general.store import (
    cell_store, 
    warnings_store, 
    cathode_active_material_store,
    anode_active_material_store,
    LANDING_PAGE_IMAGE_URLS
)

from App.database_service import FORM_FACTOR_OPTIONS


stores = ds.html.Div([
    cell_store,
    warnings_store,
    cathode_active_material_store,
    anode_active_material_store,
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
], style=DIV_STYLE)


cell_type_button_panel = ds.html.Div(
    
        ds.html.Div(
            id='cell_schematic', 
            children = [
                ds.html.Button(
                    children=[
                        ds.html.Img(
                            id={'type': 'cell_schematic_image', 'key': j},
                            src=i, 
                            style={
                                'width': '50%', 
                                'height': 'auto',
                                'display': 'block',
                                'margin': '20px auto'  # Centers horizontally and adds vertical margin
                            }
                        )
                    ],
                    id={'type': 'cell_schematic_button', 'key': j},
                    style={
                        'border': 'none',
                        'background': 'none',
                        'padding': '20px',
                        'cursor': 'pointer',
                        'width': '100%',
                        'height': 'auto',
                        'border-radius': '8px',
                        'transition': 'transform 0.2s ease, box-shadow 0.2s ease',
                        'text-align': 'center'  # Centers inline/block content
                    },
                    className='cell-schematic-button'  # For CSS hover effects
                ) 
                for (j, i) in LANDING_PAGE_IMAGE_URLS.items()
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, 1fr)",
                "gap": "10px",
                'margin-top': '-20px',
                'margin-left': '100px',
            }
        ),
        style={'flex': '1', 'padding': '20px', 'justify-content': 'center', 'align-items': 'left', 'width': '10%', 'margin-top': '-100px'}
)


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

        ds.html.Br(), ds.html.Br(), ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id='continue_to_design',
            children='Continue to Design \t \u2192 ',
            style=BUTTON_STYLE | {'width': '30%', 'border': 'none'},
        ),

        ds.html.Div(style={'height': '100px'})
        ], style={'flex': '0 0 35%', 'padding': '20px', 'justify-content': 'center', 'align-items': 'center', 'padding-top': '-400px'}
    ),

    cell_type_button_panel,
        
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '100px', 'width': '90%'})


cathode_tabs_div = ds.html.Div(

    id='cathode_tabs_panel',

    children=[
        ds.dcc.Tabs(
            id='cathode-tabs-container',
            children=[
                ds.dcc.Tab(label='Current Collector', value='cathode_current_collector', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Formulation', value='cathode_formulation', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Electrode', value='cathode_electrode', className='tab-style', selected_className='tab-selected-style')
            ],
            value='cathode_current_collector',
        ),

        ds.html.Div(id='cathode_current_collector_tab', children=[cathode_current_collector_layout], style={'display': 'block'}),
        ds.html.Div(id='cathode_formulation_tab', children=[cathode_formulation_layout], style={'display': 'none'}),
        ds.html.Div(id='cathode_electrode_tab', children=[cathode_electrode_layout], style={'display': 'none'}),

    ], style = DIV_STYLE | {'display': 'block'}

)


anode_tabs_div = ds.html.Div(

    id='anode_tabs_panel',

    children=[
        ds.dcc.Tabs(
            id='anode-tabs-container',
            children=[
                ds.dcc.Tab(label='Current Collector', value='anode_current_collector', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Formulation', value='anode_formulation', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Electrode', value='anode_electrode', className='tab-style', selected_className='tab-selected-style')
            ],
            value='anode_current_collector',
        ),

        ds.html.Div(id='anode_current_collector_tab', children=[anode_current_collector_layout], style={'display': 'block'}),
        ds.html.Div(id='anode_formulation_tab', children=[anode_formulation_layout], style={'display': 'none'}),
        ds.html.Div(id='anode_electrode_tab', children=[anode_electrode_layout], style={'display': 'none'}),

    ], style = DIV_STYLE | {'display': 'block'}

)


main_tabs = ds.html.Div(
    
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
            id='main-tabs-container',
            children=[
                ds.dcc.Tab(label='Cathode', value='cathode', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Anode', value='anode', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Electrode Assembly', value='electrode_assembly', className='tab-style', selected_className='tab-selected-style'),
                ds.dcc.Tab(label='Warnings', value='warnings', className='tab-style', selected_className='tab-selected-style')
            ],
            value='cathode',
        ),

        ds.html.Div(id='cathode_tab', children=[cathode_tabs_div], style={'display': 'block'}),
        ds.html.Div(id='anode_tab', children=[anode_tabs_div], style={'display': 'none'}),
        ds.html.Div(id='electrode_assembly_tab', children=[electrode_assembly_layout], style={'display': 'none'}),
        ds.html.Div(id='warnings_tab', children=[warnings], style={'display': 'none'}),

    ], style = DIV_STYLE | {'display': 'none'}
)




