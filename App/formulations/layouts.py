import dash as ds
from steer_core.Apps.Components.SliderComponents import SliderWithTextInput
from App.styles import ADD_REMOVE_BUTTON_STYLE, ADD_REMOVE_BUTTON_CONTAINER_STYLE



cathode_parameters = ds.html.Div(
    
    id='cathode_formulation_design_parameters',
    
    children=[

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'formulation'},
            min_val = 0,
            max_val = 5,
            step = 0.01,
            mark_interval = 1,
            property_name = 'voltage_cutoff',
            title = 'Voltage Cutoff (V)',
            div_width='60%'
        )(),

    ]

)


cathode_active_material_div = ds.html.Div(
    id = "cathode-active-material-div",
    children=[]
)


cathode_binder_div = ds.html.Div(
    id = "cathode-binder-div",
    children=[]    
)


cathode_conductive_additive_div = ds.html.Div(
    id = "cathode-conductive-additive-div",
    children=[]    
)


cathode_active_material_buttons_div = ds.html.Div([
    ds.html.Button(
        "+", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'active_material'},
        style={**ADD_REMOVE_BUTTON_STYLE, 'marginRight': '10px'}
    ),
    ds.html.Button(
        "-", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'active_material'},
        style=ADD_REMOVE_BUTTON_STYLE
    ),
])


cathode_binder_buttons_div = ds.html.Div([
    ds.html.Button(
        "+", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'binder'},
        style={**ADD_REMOVE_BUTTON_STYLE, 'marginRight': '10px'}
    ),
    ds.html.Button(
        "-", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'binder'},
        style=ADD_REMOVE_BUTTON_STYLE
    ),
], style=ADD_REMOVE_BUTTON_CONTAINER_STYLE)


cathode_conductive_additive_buttons_div = ds.html.Div([
    ds.html.Button(
        "+", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'conductive_additive'},
        style={**ADD_REMOVE_BUTTON_STYLE, 'marginRight': '10px'}
    ),
    ds.html.Button(
        "-", 
        id={'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'conductive_additive'},
        style=ADD_REMOVE_BUTTON_STYLE
    ),
], style=ADD_REMOVE_BUTTON_CONTAINER_STYLE)


cathode_formulation_plots = ds.html.Div([

    # First plot on top (full width)
    ds.html.Div([
        ds.html.H5("Half Cell Curve", style={'margin': '0 0 2px 0', 'textAlign': 'center'}),
        ds.dcc.Graph(
            id='cathode_formulation_specific_capacity_plot', 
            style={'width': '100%', 'height': '50vh'},
            responsive=True,
            config={'responsive': True}
        ),
    ]),

    # Line break between top and bottom plots
    ds.html.Br(),

    # Second and third plots side by side
    ds.html.Div([
        ds.html.Div([
            ds.html.H5("Specific Cost Breakdown", style={'margin': '0 0 2px 0', 'textAlign': 'center'}),
            ds.dcc.Graph(
                id='cathode_formulation_specific_cost_breakdown_plot', 
                style={'width': '100%', 'height': '40vh'},
                responsive=True,
                config={'responsive': True}
            ),
        ], style={'flex': '1', 'minWidth': '0'}),  # flex: 1 makes it take equal space, minWidth: 0 prevents overflow

        ds.html.Div([
            ds.html.H5("Density Breakdown", style={'margin': '0 0 2px 0', 'textAlign': 'center'}),
            ds.dcc.Graph(
                id='cathode_formulation_density_breakdown_plot', 
                style={'width': '100%', 'height': '40vh'},
                responsive=True,
                config={'responsive': True}
            ),
        ], style={'flex': '1', 'minWidth': '0'}),  # flex: 1 makes it take equal space, minWidth: 0 prevents overflow
    ], style={
        'display': 'flex', 
        'flex-direction': 'row',
        'gap': '30px',  # Small gap between the two plots
        'width': '100%'
    }),

], style={
    'display': 'flex', 
    'flex-direction': 'column', 
    'flex': '1',  # Takes all remaining space instead of fixed 30%
    'padding': '10px',  # Reduced padding from 20px to 10px
    'box-sizing': 'border-box',
    'min-height': '40vh',  # Ensures minimum height
    'overflow': 'hidden'  # Prevent overflow
})


cathode_properties = ds.html.Div([
    
    ds.html.Br(),
    ds.html.H5('Cathode Formulation Properties', style={'font-weight': 'bold'}),
    ds.html.Br(),

    # Container div for the properties table
    ds.html.Div(
        id='cathode_formulation_properties_div',
        children=[
            ds.html.P("Properties will be displayed here when calculated.", 
                     style={'font-style': 'italic', 'color': '#666'})
        ],
        style={
            'border': '1px solid #ddd',
            'border-radius': '4px',
            'padding': '15px',
            'margin': '10px 0',
            'background-color': '#f9f9f9',
            'min-height': '200px',
            'width': '80%'
        }
    ),

], style={'padding': '20px', 'width': '100%'})


cathode_formulation_layout = ds.html.Div([

    ds.html.Div([

        ds.html.Div([
            
            ds.html.Br(), ds.html.Br(),
            cathode_parameters,
            ds.html.Br(), ds.html.Br(),
            ds.html.H5("Active Materials"),
            cathode_active_material_div,
            cathode_active_material_buttons_div,
            ds.html.Br(), ds.html.Br(),
            ds.html.H5("Binders"),
            cathode_binder_div,
            cathode_binder_buttons_div,
            ds.html.Br(),
            ds.html.H5("Conductive Additives"),
            cathode_conductive_additive_div,
            cathode_conductive_additive_buttons_div,
            ds.html.Br(),
            cathode_properties,
            ds.html.Div(style={'height': '400px'})

            ], style={'flex': '0 0 55%', 'padding': '20px', 'box-sizing': 'border-box'}),

        cathode_formulation_plots,  # This will automatically take the remaining 30%
        
    ], style={'display': 'flex', 'flex-direction': 'row', 'width': '100%'})

], style={'padding': '20px', 'width': '100%'})


