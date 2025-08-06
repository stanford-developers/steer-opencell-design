import dash as ds
from general.custom_components import SliderWithTextInput, RangeSliderWithTextInput
from styles import BUTTON_STYLE


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
            max_val = 20,
            step = 0.1,
            mark_interval = 2,
            property_name = 'thickness',
            title = 'Thickness (µm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 2,
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

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Derived Parameters', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 20,
            step = 0.001,
            mark_interval = 2,
            property_name = 'cost',
            slider_disable = True,
            title = 'Cost ($)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 20,
            step = 0.01,
            mark_interval = 2,
            property_name = 'mass',
            slider_disable = True,
            title = 'Mass (g)'
        )(),


        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Datums', style={'font-weight': 'bold'}),
        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_x',
            slider_disable = False,
            title = 'X (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_y',
            slider_disable = False,
            title = 'Y (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'electrode'},
            min_val = 0,
            max_val = 1,
            step = 0.01,
            mark_interval = 0.2,
            property_name = 'datum_z',
            slider_disable = False,
            title = 'Z (mm)'
        )(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'electrode', 'action': 'flip_x'},
            children='Flip X',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

        ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'electrode', 'action': 'flip_y'},
            children='Flip Y',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

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


cathode_electrode_layout = ds.html.Div([

    ds.html.Div([
        
        ds.html.Br(), ds.html.Br(), ds.html.Br(), 

        cathode_design_parameters,

        ds.html.Div(style={'height': '200px'})

        ], style={'flex': '1', 'padding': '20px', 'width': 'calc(50%)'}),

    cathode_plots,
    
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '20px', 'width': 'calc(100%)'})

