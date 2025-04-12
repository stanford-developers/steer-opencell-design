import dash as ds

HEADER_STYLE = {'textAlign': 'left', 'padding-left': '0px'}
DIV_STYLE = {'padding-left': '20px', 'width': '50%'}
DROPDOWN_STYLE = {'width': '70%'}

cell_construction = ds.html.Div([

    ds.html.Br(), ds.html.Br(), 
    
    ds.html.Div([
        ds.html.H3('Form Factor', style=HEADER_STYLE),
        ds.dcc.Dropdown(
            id='form_factor_dropdown',
            options=[
                {'label': 'Cylindrical Cell', 'value': 'cylindrical'},
                {'label': 'Prismatic Cell',   'value': 'prismatic'},
                {'label': 'Pouch Cell',       'value': 'pouch'},
            ],
            placeholder='Select a form factor',
            style=DROPDOWN_STYLE
        )
    ], style=DIV_STYLE),

    ds.html.Br(), ds.html.Br(), 

    ds.html.Div([
        ds.html.H3('Electrode Assembly Type', style=HEADER_STYLE),
        ds.dcc.Dropdown(
            id='internal_structure_dropdown',
            placeholder='Select an internal structure',
            style=DROPDOWN_STYLE
        )
    ], style=DIV_STYLE),
    
    ds.html.Br(), ds.html.Br(),

    ds.html.Div(id='num_electrode_assemblies', style=DIV_STYLE),

])


cathode_design = ds.html.Div([

    ds.dcc.Store(id='cathode_active_materials_list'),

    ds.html.Br(), ds.html.Br(),
    ds.html.H3('Active Materials'),
    ds.html.Br(), 
    ds.html.Div(id='active_materials_list', children=[]),
    ds.html.Button("+", id='add_active_materials', n_clicks=0, style={'margin-left': '10px'}),
    ds.html.Br(), ds.html.Br(),

    ds.html.H3('Binders'),
    ds.html.P("This tab will contain the electrode formulation layout."),
    ds.html.Br(), ds.html.Br(),

    ds.html.H3('Conductive Additives'),
    ds.html.P("This tab will contain the electrode formulation layout.")

    # Add your electrode formulation layout components here
], style=DIV_STYLE)


anode_design = ds.html.Div([

    ds.dcc.Store(id='anode_active_materials_list'),
    
    ds.html.Br(),
    ds.html.H2('Electrode Design'),
    ds.html.P("This tab will contain the electrode design layout."),
    # Add your electrode design layout components here
])


encapsulation = ds.html.Div([
    ds.html.Br(),
    ds.html.H2('Encapsulation'),
    ds.html.P("This tab will contain the encapsulation layout."),
    # Add your encapsulation layout components here
])


cell_analysis = ds.html.Div([
    ds.html.Br(),
    ds.html.H2('Cell Analysis'),
    ds.html.P("This tab will contain the cell analysis layout."),
    # Add your cell analysis layout components here
])


