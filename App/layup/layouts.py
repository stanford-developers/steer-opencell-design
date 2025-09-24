import dash as ds
from App.styles import *

from App.layup.lists import LAYUP_DESIGNS

from App.database_service import SEPARATOR_MATERIALS

from steer_core.Apps.Components.SliderComponents import SliderWithTextInput


layup_design = ds.html.Div(
    id="layup_design_div",
    children=[
        ds.html.H5("Select design", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="layup_design",
            placeholder="Select Layup Design",
            style={"width": "calc(50%)"},
            options=[
                {"label": design, "value": design.lower()} for design in LAYUP_DESIGNS
            ],
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
    ],
    style={},
)


layup_control_modes = ds.html.Div(
    id="layup_control_modes",
    children=[
        ds.html.Br(),
        ds.html.H5("Control Mode", style={"font-weight": "bold"}),
        ds.html.Br(),
        ds.html.P(
            """Select the control mode for layup overhangs.  Fixed component mode will keep component geometries constant and move the object to satisfy the requested overhang. 
            Fixed overhang mode will change only the overhang requested, and manipulate the component geometries as needed to satisfy the overhang.
            """,
            style={"margin-bottom": "10px", "color": "#666"},
        ),
        ds.dcc.RadioItems(
            id="layup_control_mode_selector",
            options=[
                {
                    "label": "Fixed Component Geometries", 
                    "value": "FIXED_COMPONENT"
                },
                {
                    "label": "Fixed Overhangs",
                    "value": "FIXED_OVERHANGS",
                },
            ],
            value="FIXED_COMPONENT",
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


separator_material_parameters = ds.html.Div(
    id="separator_material_parameters",
    children=[
        ds.html.H5("Select separator material", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="separator_material_selector",
            placeholder="Select Separator Material",
            style={"width": "calc(50%)"},
            options=[
                {"label": material, "value": material}
                for material in SEPARATOR_MATERIALS
            ],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={
                "object": "separator_material",
            },
            property_name="density",
            title="Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={
                "object": "separator_material",
            },
            property_name="specific_cost",
            title="Specific Cost (€/kg)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
    ],
)


zfold_design_parameters = ds.html.Div(
    id="zfold_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Anode", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="anode_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="anode_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="anode_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="anode_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Separator", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="separator_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "zfoldmonolayer"},
            property_name="separator_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
    ],
)


laminate_design_parameters = ds.html.Div(
    id="laminate_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Anode", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="anode_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="anode_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="anode_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="anode_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Top Separator", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="top_separator_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="top_separator_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="top_separator_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="top_separator_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Bottom Separator", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="bottom_separator_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="bottom_separator_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="bottom_separator_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "laminate"},
            property_name="bottom_separator_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
    ],
)


stacked_design_parameters = ds.html.Div(
    id="stacked_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Anode", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="anode_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="anode_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="anode_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="anode_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Top Separator", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="top_separator_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="top_separator_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="top_separator_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="top_separator_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Bottom Separator", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="bottom_separator_overhang_left",
            title="Left Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="bottom_separator_overhang_right",
            title="Right Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="bottom_separator_overhang_top",
            title="Top Overhang (mm)"
        )(),
        SliderWithTextInput(
            id_base={"object": "stacked"},
            property_name="bottom_separator_overhang_bottom",
            title="Bottom Overhang (mm)"
        )(),
    ],
)


layup_plots = ds.html.Div(
    [
        # The plot
        ds.dcc.Graph(
            id="layup_plot",
            style={"width": "50vw", "height": "40vw"},
            responsive=True,
        ),
        # Opacity control slider - moved above plot for better layout
        ds.html.Div(
            [
                ds.html.Label(
                    "Plot Opacity:",
                    style={"margin-right": "10px", "font-weight": "bold"},
                ),
                ds.html.Div(
                    [
                        ds.dcc.Slider(
                            id="layup_opacity_slider",
                            min=0,
                            max=1,
                            step=0.01,
                            value=0.2,  # Default opacity
                            marks={
                                0.0: "0%",
                                0.2: "20%",
                                0.4: "40%",
                                0.6: "60%",
                                0.8: "80%",
                                1.0: "100%",
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    style={"width": "80%", "margin-left": "10px"},
                ),  # Fixed width for slider
            ],
            style={
                "display": "flex",
                "align-items": "center",
                "margin-bottom": "15px",
                "padding": "10px",
            },
        ),
        # Areal capacity design plot
        ds.dcc.Graph(
            id="areal_capacity_design_plot",
            style={"width": "50vw", "height": "40vw"},
            responsive=True,
        ),
    ],
    style={"display": "flex", "flex-direction": "column"},
)


layup_layout = ds.html.Div(
    [
        ds.html.Div(
            [
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Br(),
                layup_design,
                separator_material_parameters,
                layup_control_modes,
                zfold_design_parameters,
                laminate_design_parameters,
                stacked_design_parameters,
                ds.html.Div(style={"height": "200px"}),
            ],
            style={"flex": "1", "padding": "20px", "width": "calc(50%)"},
        ),
        layup_plots,
    ],
    style={
        "display": "flex",
        "flex-direction": "row",
        "padding": "20px",
        "width": "calc(100%)",
    },
)


