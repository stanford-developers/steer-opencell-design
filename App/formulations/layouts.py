import dash as ds
from steer_core.Apps.Components.SliderComponents import SliderWithTextInput
from steer_core.Apps.Components.MaterialSelectors import (
    MaterialSelector,
    ActiveMaterialSelector,
)
from App.general.styles import ADD_REMOVE_BUTTON_STYLE, ADD_REMOVE_BUTTON_CONTAINER_STYLE


#############################
######## CATHODE ############
#############################

cathode_message = ds.html.Div(id="cathode_formulation_message", children=[])

cathode_parameters = ds.html.Div(
    id="cathode_formulation_design_parameters",
    children=[
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "formulation"},
            min_val=0,
            max_val=5,
            step=0.01,
            mark_interval=1,
            property_name="voltage_cutoff",
            title="Voltage Cutoff (V)",
            div_width="60%",
        )(),
    ],
)

cathode_active_material_div = ds.html.Div(
    id="cathode-active-material-div",
    children=[
        ActiveMaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "active_material",
                "index": 0,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "active_material",
                "index": 1,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "active_material",
                "index": 2,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "active_material",
                "index": 3,
            },
            hidden=True,
        )(),
    ],
)

cathode_binder_div = ds.html.Div(
    id="cathode-binder-div",
    children=[
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "binder",
                "index": 0,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "binder",
                "index": 1,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "binder",
                "index": 2,
            },
            hidden=True,
        )(),
    ],
)

cathode_conductive_additive_div = ds.html.Div(
    id="cathode-conductive-additive-div",
    children=[
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 0,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 1,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "cathode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 2,
            },
            hidden=True,
        )(),
    ],
)

cathode_active_material_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "add",
                "material": "active_material",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "remove",
                "material": "active_material",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ]
)

cathode_binder_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "add",
                "material": "binder",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "remove",
                "material": "binder",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ],
    style=ADD_REMOVE_BUTTON_CONTAINER_STYLE,
)

cathode_conductive_additive_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "add",
                "material": "conductive_additive",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "cathode",
                "object": "formulation",
                "action": "remove",
                "material": "conductive_additive",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ],
    style=ADD_REMOVE_BUTTON_CONTAINER_STYLE,
)



cathode_formulation_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        cathode_message,
        ds.html.Br(),
        ds.html.Br(),
        cathode_parameters,
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Active Materials"),
        cathode_active_material_div,
        cathode_active_material_buttons_div,
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Binders"),
        cathode_binder_div,
        cathode_binder_buttons_div,
        ds.html.Br(),
        ds.html.H5("Conductive Additives"),
        cathode_conductive_additive_div,
        cathode_conductive_additive_buttons_div,
        ds.html.Br(),
        ds.html.Div(style={"height": "400px"}),
    ],
    style={"padding": "20px", "width": "100%"},
)


#############################
######### ANODE #############
#############################

anode_message = ds.html.Div(id="anode_formulation_message", children=[])

anode_parameters = ds.html.Div(
    id="anode_formulation_design_parameters",
    children=[
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "formulation"},
            min_val=0,
            max_val=5,
            step=0.01,
            mark_interval=1,
            property_name="voltage_cutoff",
            title="Voltage Cutoff (V)",
            div_width="60%",
        )(),
    ],
)

anode_active_material_div = ds.html.Div(
    id="anode-active-material-div",
    children=[
        ActiveMaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "active_material",
                "index": 0,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "active_material",
                "index": 1,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "active_material",
                "index": 2,
            },
            hidden=True,
        )(),
        ActiveMaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "active_material",
                "index": 3,
            },
            hidden=True,
        )(),
    ],
)

anode_binder_div = ds.html.Div(
    id="anode-binder-div",
    children=[
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "binder",
                "index": 0,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "binder",
                "index": 1,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "binder",
                "index": 2,
            },
            hidden=True,
        )(),
    ],
)

anode_conductive_additive_div = ds.html.Div(
    id="anode-conductive-additive-div",
    children=[
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 0,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 1,
            },
            hidden=True,
        )(),
        MaterialSelector(
            id_base={
                "electrode": "anode",
                "object": "formulation",
                "material": "conductive_additive",
                "index": 2,
            },
            hidden=True,
        )(),
    ],
)

anode_active_material_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "add",
                "material": "active_material",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "remove",
                "material": "active_material",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ]
)

anode_binder_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "add",
                "material": "binder",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "remove",
                "material": "binder",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ],
    style=ADD_REMOVE_BUTTON_CONTAINER_STYLE,
)

anode_conductive_additive_buttons_div = ds.html.Div(
    [
        ds.html.Button(
            "+",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "add",
                "material": "conductive_additive",
            },
            style={**ADD_REMOVE_BUTTON_STYLE, "marginRight": "10px"},
        ),
        ds.html.Button(
            "-",
            id={
                "electrode": "anode",
                "object": "formulation",
                "action": "remove",
                "material": "conductive_additive",
            },
            style=ADD_REMOVE_BUTTON_STYLE,
        ),
    ],
    style=ADD_REMOVE_BUTTON_CONTAINER_STYLE,
)



anode_formulation_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        anode_message,
        ds.html.Br(),
        ds.html.Br(),
        anode_parameters,
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Active Materials"),
        anode_active_material_div,
        anode_active_material_buttons_div,
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Binders"),
        anode_binder_div,
        anode_binder_buttons_div,
        ds.html.Br(),
        ds.html.H5("Conductive Additives"),
        anode_conductive_additive_div,
        anode_conductive_additive_buttons_div,
        ds.html.Br(),
        ds.html.Div(style={"height": "400px"}),
    ],
    style={"padding": "20px", "width": "100%"},
)
