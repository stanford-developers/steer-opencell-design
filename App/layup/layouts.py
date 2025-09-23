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
    
    # The plot
    ds.dcc.Graph(
        id='layup_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
    ),

    # Opacity control slider - moved above plot for better layout
    ds.html.Div([
        ds.html.Label("Plot Opacity:", style={'margin-right': '10px', 'font-weight': 'bold'}),
        ds.html.Div([
            ds.dcc.Slider(
                id='layup_opacity_slider',
                min=0,
                max=1,
                step=0.01,
                value=0.2,  # Default opacity
                marks={
                    0.0: '0%',
                    0.2: '20%',
                    0.4: '40%',
                    0.6: '60%',
                    0.8: '80%',
                    1.0: '100%'
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'width': '80%', 'margin-left': '10px'}),  # Fixed width for slider
    ], style={
        'display': 'flex', 
        'align-items': 'center', 
        'margin-bottom': '15px',
        'padding': '10px',
    }),

    # Areal capacity design plot
    ds.dcc.Graph(
        id='areal_capacity_design_plot', 
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


