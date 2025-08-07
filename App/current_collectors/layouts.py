import dash as ds
from styles import *

from general.custom_components import SliderWithTextInput, RangeSliderWithTextInput
from database_service import CURRENT_COLLECTOR_MATERIALS

from steer_opencell_design.Materials.CurrentCollectors import *
from steer_opencell_design.Materials.RawMaterials import *


CURRENT_COLLECTOR_DESIGNS = ['Punched','Notched','Tabless','Tabbed']


cathode_current_collector_material_parameters = ds.html.Div(

    id = 'cathode_current_collector_material_parameters',

    children=[

        ds.html.H5('Select current collector material', style={'font-weight': 'bold'}),

        ds.dcc.Dropdown(
            id='cathode_current_collector_material_selector', 
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


cathode_current_collector_design_parameters = ds.html.Div(

    id = 'cathode_current_collector_design_div',
    
    children=[

        ds.html.H5('Select design', style={'font-weight': 'bold'}),
            ds.dcc.Dropdown(
                id='cathode_current_collector_design',
                placeholder='Select Cathode Current Collector Design',
                style={'width': 'calc(50%)'},
                options=[{'label': design, 'value': design.lower()} for design in CURRENT_COLLECTOR_DESIGNS]
            ),

        ds.html.Br(), ds.html.Br(),

    ], 

    style={}
)


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

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'insulation_area',
            slider_disable = True,
            title = 'Insulation Area (both sides) (cm²)'
        )(),

        
        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Datums', style={'font-weight': 'bold'}),
        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_x',
            slider_disable = False,
            title = 'X (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_y',
            slider_disable = False,
            title = 'Y (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'punched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.01,
            mark_interval = 0.2,
            property_name = 'datum_z',
            slider_disable = False,
            title = 'Z (mm)'
        )(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_x'},
            children='Flip X',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

        ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_y'},
            children='Flip Y',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

    ]
)


cathode_notched_design_parameters = ds.html.Div(
    
    id='cathode_notched_design_parameters', 
    children=[

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Body', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'length',
            title = 'Length (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'width',
            title = 'Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
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
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_width',
            title = 'Tab Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_height',
            title = 'Tab Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_spacing',
            title = 'Tab Spacing (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_gap',
            title = 'Tab Gap (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Coating', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'coated_tab_height',
            title = 'Coated Tab Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'insulation_width',
            title = 'Insulation Width (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'a_side_coated_section',
            title = 'A Side Coated Section (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'b_side_coated_section',
            title = 'B Side Coated Section (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Derived', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.001,
            mark_interval = 2,
            property_name = 'cost',
            slider_disable = True,
            title = 'Cost ($)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.01,
            mark_interval = 2,
            property_name = 'mass',
            slider_disable = True,
            title = 'Mass (g)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'coated_area',
            slider_disable = True,
            title = 'Coated Area (both sides) (cm²)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'insulation_area',
            slider_disable = True,
            title = 'Insulation Area (both sides) (cm²)'
        )(),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Datums', style={'font-weight': 'bold'}),
        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_x',
            slider_disable = False,
            title = 'X (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_y',
            slider_disable = False,
            title = 'Y (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'notched_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.01,
            mark_interval = 0.2,
            property_name = 'datum_z',
            slider_disable = False,
            title = 'Z (mm)'
        )(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_x'},
            children='Flip X',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

        ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_y'},
            children='Flip Y',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

    ]
)


cathode_tabless_design_parameters = ds.html.Div(
    
    id='cathode_tabless_design_parameters',
    
    children=[

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Body', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'length',
            title = 'Length (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'width',
            title = 'Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'thickness',
            title = 'Thickness (\u03bcm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Coating', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'coated_width',
            title = 'Coated Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'tab_height',
            title = 'Tab Height (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 100,
            step = 0.1,
            mark_interval = 30,
            property_name = 'insulation_width',
            title = 'Insulation Width (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'a_side_coated_section',
            title = 'A Side Coated Section (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'b_side_coated_section',
            title = 'B Side Coated Section (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Derived', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.001,
            mark_interval = 2,
            property_name = 'cost',
            slider_disable = True,
            title = 'Cost ($)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.01,
            mark_interval = 2,
            property_name = 'mass',
            slider_disable = True,
            title = 'Mass (g)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'coated_area',
            slider_disable = True,
            title = 'Coated Area (both sides) (cm²)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'insulation_area',
            slider_disable = True,
            title = 'Insulation Area (both sides) (cm²)'
        )(),

        
        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Datums', style={'font-weight': 'bold'}),
        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_x',
            slider_disable = False,
            title = 'X (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_y',
            slider_disable = False,
            title = 'Y (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabless_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.01,
            mark_interval = 0.2,
            property_name = 'datum_z',
            slider_disable = False,
            title = 'Z (mm)'
        )(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_x'},
            children='Flip X',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

        ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_y'},
            children='Flip Y',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

    ]

)


cathode_tabbed_design_parameters = ds.html.Div(
    
    id='cathode_tabbed_design_parameters',
    
    children=[

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Body', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'length',
            title = 'Length (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 500,
            step = 0.1,
            mark_interval = 30,
            property_name = 'width',
            title = 'Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'thickness',
            title = 'Thickness (\u03bcm)'
        )(),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Tab Parameters', style={'font-weight': 'bold'}),
        ds.html.Br(),

        ds.dcc.Dropdown(
            id='cathode_current_collector_tab_material_selector', 
            placeholder='Select Cathode Current Collector Material',
            style={'width': 'calc(50%)'},
            options=[{'label': material, 'value': material} for material in CURRENT_COLLECTOR_MATERIALS]
        ),

        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tab_material'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'density',
            title = 'Tab Material Density (kg/m³)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tab_material'},
            min_val = 0,
            max_val = 500,
            step = 0.01,
            mark_interval = 30,
            property_name = 'specific_cost',
            title = 'Tab Material Specific Cost (€/kg)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'tab_width',
            title = 'Tab Width (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'tab_length',
            title = 'Tab Length (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.1,
            mark_interval = 10,
            property_name = 'tab_overhang',
            title = 'Tab Overhang (mm)'
        )(),

        ds.html.Br(),
        ds.html.P('Tab Weld Side'),
        ds.dcc.RadioItems(
            id={'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'tab_weld_side', 'subtype': 'radioitem'},
            options=[
                {'label': 'A Side', 'value': 'a'},
                {'label': 'B Side', 'value': 'b'}
            ],
            value='a'
        ),
        ds.html.Br(),

        ds.html.Br(),
        ds.html.P('Tab Positions Relative to Start of Tape (mm). Enter positions as a comma-separated list (e.g., "0, 100, 200")'),
        ds.dcc.Input(
            id={'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'weld_tab_positions', 'subtype': 'text_input'},
            type='text',
            style={'width': '60%', 'marginBottom': '10px'},
            debounce=True  
        ),
        ds.html.Br(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Coating', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 200,
            step = 0.1,
            mark_interval = 10,
            property_name = 'skip_coat_width',
            title = 'Width of Tab Skip Coats (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'a_side_coated_section',
            title = 'A Side Coated Section (mm)'
        )(),

        RangeSliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 5000,
            step = 0.1,
            mark_interval = 500,
            property_name = 'b_side_coated_section',
            title = 'B Side Coated Section (mm)'
        )(),

        ds.html.Br(), ds.html.Br(), 
        ds.html.H5('Derived', style={'font-weight': 'bold'}),
        ds.html.Br(), 

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.001,
            mark_interval = 2,
            property_name = 'cost',
            slider_disable = True,
            title = 'Cost ($)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 20,
            step = 0.01,
            mark_interval = 2,
            property_name = 'mass',
            slider_disable = True,
            title = 'Mass (g)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 10000,
            step = 0.1,
            mark_interval = 200,
            property_name = 'coated_area',
            slider_disable = True,
            title = 'Coated Area (both sides) (cm²)'
        )(),

        ds.html.Br(), ds.html.Br(),
        ds.html.H5('Datums', style={'font-weight': 'bold'}),
        ds.html.Br(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_x',
            slider_disable = False,
            title = 'X (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.001,
            mark_interval = 0.2,
            property_name = 'datum_y',
            slider_disable = False,
            title = 'Y (mm)'
        )(),

        SliderWithTextInput(
            id_base = {'electrode': 'cathode', 'object': 'tabbed_current_collector'},
            min_val = 0,
            max_val = 1,
            step = 0.01,
            mark_interval = 0.2,
            property_name = 'datum_z',
            slider_disable = False,
            title = 'Z (mm)'
        )(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_x'},
            children='Flip X',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

        ds.html.Br(), ds.html.Br(),

        ds.html.Button(
            id={'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_y'},
            children='Flip Y',
            style=BUTTON_STYLE | {'width': 'calc(30%)'}
        ),

    ]

)


cathode_plots = ds.html.Div([


    ds.dcc.Graph(
        id='cathode_current_collector_a_side_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

    ds.dcc.Graph(
        id='cathode_current_collector_b_side_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
    ),

    ds.dcc.Graph(
        id='cathode_current_collector_top_down_plot', 
        style={'width': '50vw', 'height': '40vw'},
        responsive=True,
        config={
            'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d']
        }
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






