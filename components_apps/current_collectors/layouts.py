import dash as ds
from styles import *
from pathlib import Path

from general.custom_components import SliderWithTextInput

from SteerEnergyStorage.Materials.CurrentCollectors import *
from SteerEnergyStorage.Materials.RawMaterials import *

# get current collector materials from the database
from SteerEnergyStorage.DataManager import DataManager
CURRENT_DIR = Path(__file__).resolve().parent
DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
dm = DataManager(DATA_PATH)


CURRENT_COLLECTOR_MATERIALS = dm.get_current_collector_materials(most_recent=True)['name'].tolist()
CURRENT_COLLECTOR_DESIGNS = ['Punched','Notched','Tabless','Tabbed']


cathode_current_collector_material_parameters = ds.html.Div(

    id = 'cathode_current_collector_material_parameters',

    children=[

        ds.html.H5('Select material', style={'font-weight': 'bold'}),

        ds.dcc.Dropdown(
            id='cathode_material_selector', 
            placeholder='Select Cathode Current Collector Material',
            style={'width': 'calc(50%)'},
            options=[{'label': material, 'value': material} for material in CURRENT_COLLECTOR_MATERIALS]
        ),

        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'material'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'density',
            title = 'Density (kg/m³)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'material'},
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


cathode_current_collector_design_parameters = ds.html.Div([

    ds.html.H5('Select design', style={'font-weight': 'bold'}),
        ds.dcc.Dropdown(
            id='cathode_current_collector_design',
            placeholder='Select Cathode Current Collector Design',
            style={'width': 'calc(50%)'},
            options=[{'label': design, 'value': design.lower()} for design in CURRENT_COLLECTOR_DESIGNS]
        ),

    ds.html.Br(), ds.html.Br(),

])


cathode_punched_design_parameters = ds.html.Div(
    
    id='cathode_punched_design_parameters', 
    children=[

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Body', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'width',
            title = 'Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'height',
            title = 'Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'thickness',
            title = 'Thickness (\u03bcm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Tab', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_width',
            title = 'Tab Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_height',
            title = 'Tab Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_position',
            title = 'Tab Position (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Coating', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'coated_tab_height',
            title = 'Coated Tab Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'insulation_width',
            title = 'Insulation Width (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Derived', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.001,
            mark_interval = 2,
            property_name = 'cost',
            slider_disable = True,
            title = 'Cost ($)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.01,
            mark_interval = 2,
            property_name = 'mass',
            slider_disable = True,
            title = 'Mass (g)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'coated_area',
            slider_disable = True,
            title = 'Coated Area (both sides) (cm²)'
        )(),

    ]
)


cathode_notched_design_parameters = ds.html.Div(
    id='cathode_notched_design_parameters',
    children=[ds.html.P('Notched design parameters will be added here.', style={'font-style': 'italic'})]
)


cathode_tabless_design_parameters = ds.html.Div(
    id='cathode_tabless_design_parameters',
    children=[ds.html.P('Tabless design parameters will be added here.', style={'font-style': 'italic'})]
)


cathode_tabbed_design_parameters = ds.html.Div(
    id='cathode_tabbed_design_parameters',
    children=[ds.html.P('Tabbed design parameters will be added here.', style={'font-style': 'italic'})]
)


cathode_plots = ds.html.Div([


    ds.dcc.Graph(
        id='cathode_a_side_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True
    ),

    ds.dcc.Graph(
        id='cathode_b_side_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True
    ),

], style={'display': 'flex', 'flex-direction': 'column'})


cathode_current_collector_layout = ds.html.Div([

    ds.html.Div([
        
        ds.html.Br(), ds.html.Br(), ds.html.Br(), 

        cathode_current_collector_material_parameters,
        cathode_current_collector_design_parameters,
        cathode_punched_design_parameters,
        cathode_notched_design_parameters,
        cathode_tabless_design_parameters,
        cathode_tabbed_design_parameters,

        ds.html.Div(style={'height': '200px'})

        ], style={'flex': '1', 'padding': '20px', 'width': 'calc(50%)'}),

    cathode_plots,
    
], style={'display': 'flex', 'flex-direction': 'row', 'padding': '20px', 'width': 'calc(100%)'})


anode_current_collector_layout = ds.html.Div([
    ds.html.Br(), ds.html.Br(),
    ds.html.H3('Anode Current Collector'),
], style=DIV_STYLE)


