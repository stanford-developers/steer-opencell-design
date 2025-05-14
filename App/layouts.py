import dash as ds
from styles import *
from custom_components import SliderWithTextInput, RangeSliderWithTextInput, CurrentCollectorSelector

from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial

BUTTON_DIV_STYLE = {'display': 'flex', 'gap': '10px', 'margin-left': '-10px'}

##########
current_collector_materials = [m for m in CurrentCollector.get_available_materials()]
active_materials_cathode = [m for m in CathodeMaterial.get_available_materials()]
active_materials_anode = [m for m in AnodeMaterial.get_available_materials()]
##########


data_stores = ds.html.Div([
    ds.dcc.Store(id='app-load-trigger', data={}),
    ds.dcc.Store(id={'type': 'store', 'object': 'currrent_collector', 'type': 'materials'}, data=current_collector_materials),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'cathode'}, data=active_materials_cathode),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'anode'}, data=active_materials_anode),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'cathode', 'object': 'formulation'}),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'anode', 'object': 'formulation'}),
    ds.dcc.Store(id={'type': 'store', 'component': 'separator'}),
    ds.dcc.Store(id={'type': 'store', 'component': 'electrolyte'}),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'cathode', 'object': 'current_collector'}),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'anode', 'object': 'current_collector'}),
    ds.dcc.Store(id={'type': 'store', 'object': 'encapsulation'}),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'cathode', 'object': 'electrode'}),
    ds.dcc.Store(id={'type': 'store', 'electrode': 'anode', 'object': 'electrode'}),
    ds.dcc.Store(id={'type': 'store', 'object': 'electrode_assembly'}),
    ds.dcc.Store(id={'type': 'store', 'object': 'cell'}),
])


cell_construction = ds.html.Div([

    ds.html.Br(), 

    ds.html.H3('Form Factor', style=HEADER_STYLE),
    ds.html.Br(), 

    ds.html.Div([
        ds.dcc.Dropdown(
            id='form_factor_dropdown',
            options=[
                {'label': 'Cylindrical', 'value': 'cylindrical'},
                {'label': 'Prismatic',   'value': 'prismatic'},
                {'label': 'Pouch',       'value': 'pouch'},
            ],
            placeholder='select cell form factor',
            style=DROPDOWN_STYLE
        )
    ]),

    ds.html.Br(), ds.html.Br(), 

    ds.html.Div([
        ds.dcc.Dropdown(
            id='internal_structure_dropdown',
            placeholder='select electrode assembly structure',
            style=DROPDOWN_STYLE | {'margin-top': '-30px'}
        )
    ]),
    
    ds.html.Br(), ds.html.Br(),

    ds.html.Div([
        ds.dcc.Dropdown(
            id='num_electrode_assemblies',
            placeholder='select number of electrode assemblies',
            style=DROPDOWN_STYLE | {'margin-top': '-30px'}
        )
    ]),

], style={'padding-left': '10px'})


cell_operation = ds.html.Div([
    
    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H3('Operating Window', style=HEADER_STYLE),
    ds.html.Br(),

    RangeSliderWithTextInput({'type': 'operation'}, 0, 6, [1.5, 4.2], 0.1, 1, 'voltage_range', "Voltage Range (V)").render(),
    ds.html.Br(), ds.html.Br(),
    RangeSliderWithTextInput({'type': 'operation'}, 0, 40, [2, 12], 0.1, 5, 'capacity_range', "Irreverisble and Reversible Capacity (Ah)").render(),

    ], style={'padding-left': '10px'})


cathode_mechanicals = ds.html.Div([

    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H5('Current Collector Material', style=HEADER_STYLE),
    ds.html.Br(),
    CurrentCollectorSelector({'electrode': 'cathode', 'object': 'current_collector'}, [], density_default=2.7, specific_cost_default=2.64).render(),
    ds.html.Br(), ds.html.Br(),
    ds.html.H5('Design', style=HEADER_STYLE),
    ds.html.Br(),
    ds.dcc.Dropdown(
        id={'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'cathode', 'feature': 'design'}, 
        placeholder='select electrode assembly structure to see options',
        style={'width': '200px'}
        ),
    ds.html.Div(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'div', 'electrode': 'cathode'}),
    ds.html.Div(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'message', 'electrode': 'cathode'}),
    ds.dcc.Graph(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'graph', 'electrode': 'cathode'}, style={'height': '400px', 'width': '1400px'}),

    ds.html.Div(style={'height': '1000px'})

], style={'padding-left': '20px', 'width': '100%'})


anode_mechanicals = ds.html.Div([

    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H5('Current Collector Material', style=HEADER_STYLE),
    ds.html.Br(),
    CurrentCollectorSelector({'electrode': 'anode', 'object': 'current_collector'}, [], density_default=2.7, specific_cost_default=2.64).render(),
    ds.html.Br(), ds.html.Br(),
    ds.html.H5('Design', style=HEADER_STYLE),
    ds.html.Br(),
    ds.dcc.Dropdown(
        id={'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'anode', 'feature': 'design'}, 
        placeholder='select electrode assembly structure to see options',
        style={'width': '200px'}
        ),
    ds.html.Div(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'div', 'electrode': 'anode'}),
    ds.html.Div(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'message', 'electrode': 'anode'}),
    ds.dcc.Graph(id={'tab': 'mechanicals', 'object': 'current_collector', 'object': 'graph', 'electrode': 'anode'}, style={'height': '400px', 'width': '1400px'}),


    ds.html.Div(style={'height': '1000px'})

], style={'padding-left': '20px', 'width': '100%'})


positive_terminal_inputs = ds.html.Div([
    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Positive Terminal"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'cathode'}, 0, 10, 2, 0.01, 1, 'mass', 'Mass (g)', div_width='1000px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'cathode'}, 0, 1000, 100, 0.1, 100, 'specific_cost', 'Specific Cost ($/kg)', div_width='600px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'cathode'}, 0, 20, 5, 0.1, 10, 'thickness', 'Thickness (mm)', div_width='600px').render(), ds.html.Br(),
    ds.html.Div(id={'tab': 'encapsulation', 'object': 'terminal', 'object': 'message', 'electrode': 'cathode'}), 
])


negative_terminal_inputs = ds.html.Div([
    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Negative Terminal"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'anode'}, 0, 10, 2, 0.01, 1, 'mass', 'Mass (g)', div_width='1000px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'anode'}, 0, 1000, 100, 0.1, 100, 'specific_cost', 'Specific Cost ($/kg)', div_width='600px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'anode'}, 0, 20, 5, 0.1, 10, 'thickness', 'Thickness (mm)', div_width='600px').render(), ds.html.Br(), 
    ds.html.Div(id={'tab': 'encapsulation', 'object': 'terminal', 'object': 'message', 'electrode': 'anode'}), 
])


cylindrical_encapsulation = ds.html.Div([

    positive_terminal_inputs,
    negative_terminal_inputs,

    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Cylindrical Shell"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1, 0.2, 0.01, 1, 'cost', 'Cost ($)', div_width='500px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1000, 50, 0.1, 100, 'mass', 'Mass (g)', div_width='1400px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 100, 17, 0.1, 10, 'internal_radius', 'Internal Radius (mm)', div_width='700px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1, 0.3, 0.01, 1, 'wall_thickness', 'Wall thickness (mm)', div_width='500px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 500, 100, 0.1, 100, 'length', 'Length (mm)', div_width='500px').render(), ds.html.Br(), 

])


pouch_encapsulation = ds.html.Div([

    positive_terminal_inputs,
    negative_terminal_inputs,

    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Pouch"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 200, 100, 0.1, 20, 'laminate_thickness', 'Laminate thickness (μm)', div_width='800px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 30, 15, 0.01, 5, 'laminate_areal_mass', 'Laminate areal mass (mg/cm²)', div_width='800px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 10, 4, 0.01, 2, 'laminate_areal_cost', 'Laminate areal cost ($/cm²)', div_width='800px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 10, 1, 0.01, 2, 'tape_mass', 'Mass of sealing tape (g)', div_width='400px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 50, 4, 0.01, 5, 'side_heat_seal', 'Width of side heat seals (mm)', div_width='600px').render(), ds.html.Br(), 
    SliderWithTextInput({'object': 'encapsulation', 'type': 'pouch'}, 0, 50, 4, 0.01, 5, 'top_heat_seal', 'Width of top heat seal (mm)', div_width='600px').render(), ds.html.Br(), 

])


prismatic_encapsulation = ds.html.Div([

    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Prismatic Lid"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_lid'}, 0, 200, 20, 0.1, 20, 'mass', 'Mass (g)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_lid'}, 0, 5, 0.5, 0.01, 1, 'cost', 'Cost ($)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_lid'}, 0, 100, 20, 0.1, 10, 'external_width', 'External Width (mm)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_lid'}, 0, 100, 20, 0.1, 10, 'internal_width', 'Internal Width (mm)', div_width='1000px').render(), ds.html.Br(),

    ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H4("Prismatic Case"),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 200, 20, 0.1, 20, 'mass', 'Mass (g)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 5, 0.5, 0.01, 1, 'cost', 'Cost ($)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 200, 100, 0.1, 40, 'internal_length', 'Internal Length (mm)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 200, 50, 0.1, 40, 'internal_width', 'Internal Width (mm)', div_width='1000px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 500, 100, 0.1, 50, 'internal_height', 'Internal Height (mm)', div_width='1400px').render(), ds.html.Br(),
    SliderWithTextInput({'object': 'encapsulation', 'type': 'prismatic_case'}, 0, 4, 0.5, 0.01, 1, 'wall_thickness', 'Wall Thickness (mm)', div_width='700px').render(), ds.html.Br(),

])


encapsulation = ds.html.Div([

    ds.html.Div(id={'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'div'}),
    ds.html.Div(id={'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'message'}),

    ds.html.Br(), ds.html.Br(),
            ds.html.Div([
                ds.dcc.Graph(id={'type': 'encapsulation', 'object': 'graph', 'view': 'top'}, style={'width': '700px', 'height': '700px'}),
                ds.dcc.Graph(id={'type': 'encapsulation', 'object': 'graph', 'view': 'side'}, style={'width': '700px', 'height': '700px'}),
                ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'align-items': 'flex-start'}),

    ds.html.Div(style={'height': '1000px'})

], style={'padding-left': '20px', 'width': '100%'})


cathode_formulation = ds.html.Div([

    ds.html.Br(), ds.html.Br(),
    ds.html.H4('Active Materials'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'cathode', 'material': 'active_material'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'cathode', 'material': 'active_material'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'cathode', 'material': 'active_material'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Binders'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'cathode', 'material': 'binder'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'cathode', 'material': 'binder'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'cathode', 'material': 'binder'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Conductive Additives'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'cathode', 'material': 'conductive_additive'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'cathode', 'material': 'conductive_additive'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'cathode', 'material': 'conductive_additive'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H5('Formulation Properties'),
    ds.html.Div(id={'type': 'formulation_properties_text', 'electrode': 'cathode'}, children=['-'], style={'width': '150%'}),

    ds.html.Div(style={'height': '1000px'})

    # Add your electrode formulation layout components here
], style={'padding-left': '20px', 'width': '60%'})


anode_formulation = ds.html.Div([

    ds.html.Br(), ds.html.Br(),
    ds.html.H4('Active Materials'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'anode', 'material': 'active_material'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'anode', 'material': 'active_material'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'anode', 'material': 'active_material'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Binders'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'anode', 'material': 'binder'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'anode', 'material': 'binder'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'anode', 'material': 'binder'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Conductive Additives'),
    ds.html.Div(id={'type': 'materials_selector', 'electrode': 'anode', 'material': 'conductive_additive'}, children=[], style={'width': '100%'}),
    ds.html.Div([
        ds.html.Button("+", id={'type': 'button', 'action': 'add', 'electrode': 'anode', 'material': 'conductive_additive'}, n_clicks=0, style=BUTTON_STYLE),
        ds.html.Button("-", id={'type': 'button', 'action': 'remove', 'electrode': 'anode', 'material': 'conductive_additive'}, n_clicks=0, style=BUTTON_STYLE)
    ], style=BUTTON_DIV_STYLE),
    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H5('Formulation Properties'),
    ds.html.Div(id={'type': 'formulation_properties_text', 'electrode': 'anode'}, style={'width': '150%'}),

    ds.html.Div(style={'height': '1000px'})

], style={'padding-left': '20px', 'width': '60%'})


electrodes = ds.html.Div([

    ds.html.Br(), ds.html.Br(), ds.html.Br(),
 
    ds.html.H4('Cathode'),
    ds.html.Br(),
    SliderWithTextInput({'type': 'electrodes', 'electrode': 'cathode', 'object': 'electrode'}, 0, 60, 30, 0.1, 5, 'mass_loading', "Cathode Mass Loading (mg/cm³)", True, '1000px').render(),
    ds.html.Br(),
    SliderWithTextInput({'type': 'electrodes', 'electrode': 'cathode', 'object': 'electrode'}, 0, 5, 2, 0.01, 1, 'calender_density', "Calender Density (g/cm³)", True, '1000px').render(),
    ds.html.Br(),
    ds.html.Div(id={'tab': 'electrodes', 'object': 'message', 'electrode': 'cathode'}),

    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Anode'),
    ds.html.Br(),
    SliderWithTextInput({'type': 'electrodes', 'electrode': 'anode', 'object': 'electrode'}, 0, 60, 15, 0.1, 5, 'mass_loading', "Cathode Mass Loading (mg/cm³)", True, '1000px').render(),
    ds.html.Br(),
    SliderWithTextInput({'type': 'electrodes', 'electrode': 'anode', 'object': 'electrode'}, 0, 5, 1, 0.01, 1, 'calender_density', "Calender Density (g/cm³)", True, '1000px').render(),
    ds.html.Br(),
    ds.html.Div(id={'tab': 'electrodes', 'object': 'message', 'electrode': 'anode'}),

    ds.html.Br(), ds.html.Br(), ds.html.Br(),

    ds.html.H4('Assembly'),
    ds.html.Div(id={'type': 'div', 'object': 'electrode_assembly'}),
    ds.html.Div(id={'tab': 'electrodes', 'object': 'message', 'type': 'electrode_assembly'}),
    ds.dcc.Graph(id={'tab': 'electrodes', 'object': 'graph', 'type': 'electrode_assembly'}, config={'toImageButtonOptions': {'scale': 8}}),

    ds.html.Div(style={'height': '1000px'})
], style={'padding-left': '20px', 'width': '100%'})


separator_electrolyte = ds.html.Div([

    ds.html.Br(), ds.html.Br(),

    ds.html.Div(
        id={'tab': 'mechanicals', 'type': 'separator', 'object': 'div'}, 
        children=[
            ds.html.H4('Separator', style=HEADER_STYLE),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 60, 20, 1, 10, 'separator_thickness', title="Thickness (μm)", div_width='30%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 3, 0.2, 0.01, 1, 'separator_areal_cost', title="Areal Cost ($/m²)", div_width='40%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 3, 1, 0.01, 1, 'separator_density', title="Density (g/cm³)", div_width='40%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 300, 120, 0.1, 50, 'separator_width', title="Width (mm)", div_width='60%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 100, 45, 0.1, 5, 'separator_porosity', title="Porosity (%)", div_width='80%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 5000, 1200, 1, 200, 'separator_fold_length', title="Fold Length (mm)", div_width='110%').render(),
            ds.html.Br(),
            ds.html.Div(id={'type': 'separator_message_text'}, children=[' '], style={'width': '150%'}),
            ],
        style={'padding-left': '20px', 'width': '80%'}),

    ds.html.Br(),

    ds.html.Div(
        id={'tab': 'mechanicals', 'type': 'electrolyte', 'object': 'div'}, 
        children=[
            ds.html.H4('Electrolyte', style=HEADER_STYLE),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 20, 5, 0.01, 1, 'electrolyte_specific_cost', title="Specific Cost ($/kg)", div_width='80%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 2, 1, 0.01, 1, 'electrolyte_density', title="Density (g/cm³)", div_width='40%').render(),
            ds.html.Br(),
            SliderWithTextInput({'type': 'mechanicals'}, 0, 100, 10, 0.1, 10, 'electrolyte_overfill', title="Overfill (%)", div_width='70%').render(),
            ds.html.Br(),
            ds.html.Div(id={'type': 'electrolyte_message_text'}, children=[' '], style={'width': '150%'}),
            ],
        style={'padding-left': '20px', 'width': '80%'}),

    ds.html.Div(style={'height': '1000px'})

])


cell_analysis = ds.html.Div([
    
    ds.html.Br(),

    ds.html.H3('Cell Properties', style=HEADER_STYLE | {'padding-left': '20px'}),
    ds.html.Div(id={'type': 'cell_properties_text'}, style={'padding-left': '20px'}),

    ds.html.Br(), 

    ds.html.Div(id={'type': 'theoretical_curve_placeholder'}),

    ds.html.Br(), 
    ds.html.Div(id={'type': 'cost_mass_placeholder'}),

    ], style={
        'position': 'fixed',
        'top': '0',
        'right': '0',
        'width': '40%',
        'height': 'calc(200vw)',
        'background-color': '#e3e5e6',
        'padding': '10px',
        'overflow': 'auto',
        }
)


tab_container = ds.html.Div([

    ds.html.Div([
    ds.html.Br(), ds.html.Br(), ds.html.Br(), ds.html.Br(),
    ds.html.H3('Design', style=HEADER_STYLE),
    ]),

    ds.dcc.Tabs(
        id='tabs-container',
        children=[
            ds.dcc.Tab(label='Cathode Mechanicals', value='cathode_mechanicals'),
            ds.dcc.Tab(label='Anode Mechanicals', value='anode_mechanicals'),
            ds.dcc.Tab(label='Encapsulation', value='encapsulation'),
            ds.dcc.Tab(label='Cathode Formulation', value='cathode_design'),
            ds.dcc.Tab(label='Anode Formulation', value='anode_design'),
            ds.dcc.Tab(label='Separator and Electrolyte', value='separator_electrolyte_design'),
            ds.dcc.Tab(label='Electrode Specifications', value='electrodes'),
        ],
        value='cathode_mechanicals',
    ),

    ds.html.Div(id='cathode_mechanicals', children=[cathode_mechanicals], style={'display': 'block'}),
    ds.html.Div(id='anode_mechanicals', children=[anode_mechanicals], style={'display': 'none'}),
    ds.html.Div(id='encapsulation', children=[encapsulation], style={'display': 'none'}),
    ds.html.Div(id='cathode_design', children=[cathode_formulation], style={'display': 'none'}),
    ds.html.Div(id='anode_design', children=[anode_formulation], style={'display': 'none'}),
    ds.html.Div(id='separator_electrolyte_design', children=[separator_electrolyte], style={'display': 'none'}),
    ds.html.Div(id='electrodes', children=[electrodes], style={'display': 'none'}),

], style={'margin-left': '10px', 'margin-right': '10px', 'width': 'calc(58.5vw)'})


