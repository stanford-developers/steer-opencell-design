import dash as ds
<<<<<<< HEAD
from steer_core.Apps.Components.SliderComponents import SliderWithTextInput
=======
from steer_core.Apps.Components.SliderComponents import SliderWithTextInput, SliderWithTextInputAndCheckbox
>>>>>>> electrode_ui
from styles import BUTTON_STYLE
from database_service import INSULATION_MATERIALS


cathode_insulation_material_parameters = ds.html.Div(

    id = 'cathode_insulation_material_parameters',

    children=[

        ds.html.H5('Select insulation material', style={'font-weight': 'bold'}),

        ds.dcc.Dropdown(
            id='cathode_insulation_material_selector', 
            placeholder='Select Cathode Insulation Material',
            style={'width': 'calc(50%)'},
            options=[{'label': material, 'value': material} for material in INSULATION_MATERIALS]
        ),

        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'insulation_material'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'density',
            title = 'Density (kg/m³)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'insulation_material'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'specific_cost',
            title = 'Specific Cost (€/kg)'
        )(),

        ds.html.Br(), ds.html.Br(),

    ]

)


cathode_design_parameters = ds.html.Div(
    
    id='cathode_electrode_design_parameters',
    
    children=[

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Coating', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'mass_loading',
            title = 'Mass Loading (mg/cm²)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'coating_thickness',
            title = 'Coating Thickness (µm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'calender_density',
            title = 'Calender Density (g/cm³)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'porosity',
            title = 'Porosity (%)'
        )(),

    ]

)


cathode_plots = ds.html.Div([


    ds.dcc.Graph(
        id='cathode_top_down_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

    ds.dcc.Graph(
        id='cathode_cross_section_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

    ds.dcc.Graph(
        id='cathode_areal_capacity_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

    ds.dcc.Graph(
        id='cathode_capacity_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

], style={'display': 'flex', 'flex-direction': 'column'})



cathode_properties = ds.html.Div([
    
    ds.html.Br(),
    ds.html.H5('Cathode Properties', style={'font-weight': 'bold'}),
    ds.html.Br(),

    # Container div for the properties table
    ds.html.Div(
        id='cathode_properties_div',
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




cathode_electrode_layout = ds.html.Div([

    ds.html.Div([
        
        ds.html.Br(), ds.html.Br(), ds.html.Br(), 
        cathode_insulation_material_parameters,
        cathode_design_parameters,
        cathode_properties,
        ds.html.Div(style={'height': '200px'})

        ], style={'flex': '1', 'padding': '20px', 'width': 'calc(50%)'}),

    cathode_plots,
    
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '20px', 'width': 'calc(100%)'})

