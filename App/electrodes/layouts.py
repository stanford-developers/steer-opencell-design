import dash as ds
from steer_core.Apps.Components.SliderComponents import SliderWithTextInput
from App.general.database_service import INSULATION_MATERIALS


#############################
######## CATHODE ############
#############################

cathode_insulation_material_parameters = ds.html.Div(
    id="cathode_insulation_material_parameters",
    children=[
        ds.html.H5("Select insulation material", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="cathode_insulation_material_selector",
            placeholder="Select Cathode Insulation Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in INSULATION_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "insulation_material"},
            property_name="density",
            title="Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "insulation_material"},
            property_name="specific_cost",
            title="Specific Cost (€/kg)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "electrode"},
            property_name="insulation_thickness",
            title="Insulation Thickness (µm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
    ],
)

cathode_control_modes = ds.html.Div(
    id="cathode_control_modes",
    children=[
        ds.html.Br(),
        ds.html.H5("Control Mode", style={"font-weight": "bold"}),
        ds.html.Br(),
        ds.html.P(
            "Select which property to maintain constant when other parameters change:",
            style={"margin-bottom": "10px", "color": "#666"},
        ),
        ds.dcc.RadioItems(
            id={"electrode": "cathode", "object": "electrode", "property": "control_mode", "subtype": "radioitem"},
            options=[
                {
                    "label": " Maintain Mass Loading", 
                    "value": "maintain_mass_loading"},
                {
                    "label": " Maintain Calender Density",
                    "value": "maintain_calender_density",
                },
                {
                    "label": " Maintain Coating Thickness",
                    "value": "maintain_coating_thickness",
                },
            ],
            value="maintain_calender_density",  # Default to current behavior (single value, not list)
            style={"margin": "10px 0"},
            inputStyle={"margin-right": "8px", "transform": "scale(1.2)"},
            labelStyle={
                "display": "flex",
                "align-items": "center",
                "margin-bottom": "8px",
                "font-weight": "bold",
            },
        ),
        ds.html.Br(),
    ],
)

cathode_design_parameters = ds.html.Div(
    id="cathode_electrode_design_parameters",
    children=[
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "electrode"},
            property_name="mass_loading",
            title="Mass Loading (mg/cm²)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "electrode"},
            property_name="coating_thickness",
            title="Coating Thickness (µm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "electrode"},
            property_name="calender_density",
            title="Calender Density (g/cm³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "electrode"},
            property_name="porosity",
            title="Porosity (%)",
        )(),
    ],
)

cathode_electrode_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        cathode_insulation_material_parameters,
        cathode_control_modes,
        cathode_design_parameters,
        ds.html.Div(style={"height": "200px"}),
    ],
    style={"padding": "20px", "width": "100%"},
)


#############################
######### ANODE #############
#############################


anode_insulation_material_parameters = ds.html.Div(
    id="anode_insulation_material_parameters",
    children=[
        ds.html.H5("Select insulation material", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="anode_insulation_material_selector",
            placeholder="Select Anode Insulation Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in INSULATION_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "insulation_material"},
            property_name="density",
            title="Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "insulation_material"},
            property_name="specific_cost",
            title="Specific Cost (€/kg)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "electrode"},
            property_name="insulation_thickness",
            title="Insulation Thickness (µm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
    ],
)

anode_control_modes = ds.html.Div(
    id="anode_control_modes",
    children=[
        ds.html.Br(),
        ds.html.H5("Control Mode", style={"font-weight": "bold"}),
        ds.html.Br(),
        ds.html.P(
            "Select which property to maintain constant when other parameters change:",
            style={"margin-bottom": "10px", "color": "#666"},
        ),
        ds.dcc.RadioItems(
            id={"electrode": "anode", "object": "electrode", "property": "control_mode", "subtype": "radioitem"},
            options=[
                {
                    "label": " Maintain Mass Loading",
                    "value": "maintain_mass_loading"
                },
                {
                    "label": " Maintain Calender Density",
                    "value": "maintain_calender_density",
                },
                {
                    "label": " Maintain Coating Thickness",
                    "value": "maintain_coating_thickness",
                },
            ],
            value="maintain_calender_density",
            style={"margin": "10px 0"},
            inputStyle={"margin-right": "8px", "transform": "scale(1.2)"},
            labelStyle={
                "display": "flex",
                "align-items": "center",
                "margin-bottom": "8px",
                "font-weight": "bold",
            },
        ),
        ds.html.Br(),
    ],
)

anode_design_parameters = ds.html.Div(
    id="anode_electrode_design_parameters",
    children=[
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "electrode"},
            property_name="mass_loading",
            title="Mass Loading (mg/cm²)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "electrode"},
            property_name="coating_thickness",
            title="Coating Thickness (µm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "electrode"},
            property_name="calender_density",
            title="Calender Density (g/cm³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "electrode"},
            property_name="porosity",
            title="Porosity (%)",
        )(),
    ],
)

anode_electrode_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        anode_insulation_material_parameters,
        anode_control_modes,
        anode_design_parameters,
        ds.html.Div(style={"height": "200px"}),
    ],
    style={"padding": "20px", "width": "100%"},
)
