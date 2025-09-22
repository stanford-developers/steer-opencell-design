import dash as ds
from App.styles import *

from App.layup.lists import LAYUP_DESIGNS

from App.database_service import SEPARATOR_MATERIALS

from steer_core.Apps.Components.SliderComponents import SliderWithTextInput


layup_design = ds.html.Div(

    id = 'layup_design_div',
    
    children=[

        ds.html.H5('Select design', style={'font-weight': 'bold'}),
            ds.dcc.Dropdown(
                id='layup_design',
                placeholder='Select Layup Design',
                style={'width': 'calc(50%)'},
                options=[{'label': design, 'value': design.lower()} for design in LAYUP_DESIGNS]
            ),

        ds.html.Br(), ds.html.Br(),

    ], 

    style={}
)


separator_material_parameters = ds.html.Div(

    id = 'separator_material_parameters',

    children=[

        ds.html.H5('Select separator material', style={'font-weight': 'bold'}),

        ds.dcc.Dropdown(
            id='separator_material_selector', 
            placeholder='Select Separator Material',
            style={'width': 'calc(50%)'},
            options=[{'label': material, 'value': material} for material in SEPARATOR_MATERIALS]
        ),

        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'object': 'separator_material', },
            property_name = 'density',
            title = 'Density (kg/m³)'
        )(),

        SliderWithTextInput(
            id_base = {'object': 'separator_material', },
            property_name = 'specific_cost',
            title = 'Specific Cost (€/kg)'
        )(),

        ds.html.Br(), ds.html.Br(),

    ]

)


layup_plots = ds.html.Div([


    ds.dcc.Graph(
        id='layup_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
    ),


], style={'display': 'flex', 'flex-direction': 'column'})


layup_layout = ds.html.Div([

    ds.html.Div([
        
        ds.html.Br(), ds.html.Br(), ds.html.Br(), 

        layup_design,
        separator_material_parameters,

        ds.html.Div(style={'height': '200px'})

        ], style={'flex': '1', 'padding': '20px', 'width': 'calc(50%)'}),

    layup_plots,
    
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '20px', 'width': 'calc(100%)'})

