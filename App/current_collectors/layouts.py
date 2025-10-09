import dash as ds
from App.general.styles import *

from steer_core.Apps.Components.SliderComponents import SliderWithTextInput
from steer_core.Apps.Components.RangeSliderComponents import RangeSliderWithTextInput
from App.general.database_service import CURRENT_COLLECTOR_MATERIALS
from App.formulations.layouts import cathode_formulation_layout, anode_formulation_layout
from App.electrodes.layouts import cathode_electrode_layout, anode_electrode_layout

CURRENT_COLLECTOR_DESIGNS = ["Punched", "Notched", "Tabless", "Tabbed"]


#############################
# CATHODE CURRENT COLLECTOR #
#############################

cathode_current_collector_material_parameters = ds.html.Div(
    id="cathode_current_collector_material_parameters",
    children=[
        ds.html.H5("Select current collector material", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="cathode_current_collector_material_selector",
            placeholder="Select Cathode Current Collector Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in CURRENT_COLLECTOR_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "material"},
            property_name="density",
            title="Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "material"},
            property_name="specific_cost",
            title="Specific Cost (€/kg)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
    ],
)

cathode_current_collector_design_parameters = ds.html.Div(
    id="cathode_current_collector_design_div",
    children=[
        ds.html.H5("Select design", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id={'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'dropdown'},
            placeholder="Select Cathode Current Collector Design",
            style={"width": "calc(50%)"},
            options=[{"label": design, "value": design.lower()} for design in CURRENT_COLLECTOR_DESIGNS],
        ),
        ds.html.Br(),
        ds.html.Br(),
    ],
    style={},
)

cathode_punched_design_parameters = ds.html.Div(
    id="cathode_punched_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="width",
            title="Width (mm)",
            message="will influence the possible tab positions and widths",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="height",
            title="Height (mm)",
            message="will influence the allowed insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
            message="will influence the allowed tab positions",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
            message="will influence the allowed coated tab height values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="tab_position",
            title="Tab Position (mm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="coated_tab_height",
            title="Coated Tab Height (mm)",
            message="will influence the allowed tab height values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "punched_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
    ],
)

cathode_notched_design_parameters = ds.html.Div(
    id="cathode_notched_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="width",
            title="Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="tab_spacing",
            title="Tab Spacing (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="tab_gap",
            title="Tab Gap (mm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="coated_tab_height",
            title="Coated Tab Height (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "notched_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

cathode_tabless_design_parameters = ds.html.Div(
    id="cathode_tabless_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="width",
            title="Width (mm)",
            message="will influence allowed coated width, tab height and insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="coated_width",
            title="Coated Width (mm)",
            message="will influence the tab height (keeping tape width constant) and the allowed insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
            message="will influence the coated width (keeping tab width constant)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabless_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

cathode_tabbed_design_parameters = ds.html.Div(
    id="cathode_tabbed_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="width",
            title="Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab Parameters", style={"font-weight": "bold"}),
        ds.html.Br(),
        ds.dcc.Dropdown(
            id="cathode_current_collector_tab_material_selector",
            placeholder="Select Cathode Current Collector Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in CURRENT_COLLECTOR_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tab_material"},
            property_name="density",
            title="Tab Material Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tab_material"},
            property_name="specific_cost",
            title="Tab Material Specific Cost (€/kg)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="tab_length",
            title="Tab Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="tab_overhang",
            title="Tab Overhang (mm)",
        )(),
        ds.html.Br(),
        ds.html.P("Tab Weld Side"),
        ds.dcc.RadioItems(
            id={
                "electrode": "cathode",
                "object": "tabbed_current_collector",
                "property": "tab_weld_side",
                "subtype": "radioitem",
            },
            options=[
                {"label": "A Side", "value": "a"},
                {"label": "B Side", "value": "b"},
            ],
            value="a",
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.P('Tab Positions Relative to Start of Tape (mm). Enter positions as a comma-separated list (e.g., "0, 100, 200")'),
        ds.dcc.Input(
            id={
                "electrode": "cathode",
                "object": "tabbed_current_collector",
                "property": "tab_positions_text",
                "subtype": "text_input",
            },
            type="text",
            style={"width": "60%", "marginBottom": "10px"},
            debounce=True,
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            property_name="skip_coat_width",
            title="Width of Tab Skip Coats (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "cathode", "object": "tabbed_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

cathode_current_collector_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        cathode_current_collector_material_parameters,
        cathode_current_collector_design_parameters,
        cathode_punched_design_parameters,
        cathode_notched_design_parameters,
        cathode_tabless_design_parameters,
        cathode_tabbed_design_parameters,
        ds.html.Div(style={"height": "200px"}),
    ],
    style={
        "padding": "20px",
        "width": "calc(100%)",
    },
)


#############################
# ANODE CURRENT COLLECTOR #
#############################

anode_current_collector_material_parameters = ds.html.Div(
    id="anode_current_collector_material_parameters",
    children=[
        ds.html.H5("Select current collector material", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id="anode_current_collector_material_selector",
            placeholder="Select Anode Current Collector Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in CURRENT_COLLECTOR_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "material"},
            property_name="density",
            title="Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "material"},
            property_name="specific_cost",
            title="Specific Cost (€/kg)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
    ],
)

anode_current_collector_design_parameters = ds.html.Div(
    id="anode_current_collector_design_div",
    children=[
        ds.html.H5("Select design", style={"font-weight": "bold"}),
        ds.dcc.Dropdown(
            id={'electrode': 'anode', 'object': 'current_collector', 'subtype': 'dropdown'},
            placeholder="Select Anode Current Collector Design",
            style={"width": "calc(50%)"},
            options=[{"label": design, "value": design.lower()} for design in CURRENT_COLLECTOR_DESIGNS],
        ),
        ds.html.Br(),
        ds.html.Br(),
    ],
    style={},
)

anode_punched_design_parameters = ds.html.Div(
    id="anode_punched_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="width",
            title="Width (mm)",
            message="will influence the possible tab positions and widths",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="height",
            title="Height (mm)",
            message="will influence the allowed insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
            message="will influence the allowed tab positions",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
            message="will influence the allowed coated tab height values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="tab_position",
            title="Tab Position (mm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="coated_tab_height",
            title="Coated Tab Height (mm)",
            message="will influence the allowed tab height values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "punched_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
    ],
)

anode_notched_design_parameters = ds.html.Div(
    id="anode_notched_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="width",
            title="Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="tab_spacing",
            title="Tab Spacing (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="tab_gap",
            title="Tab Gap (mm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="coated_tab_height",
            title="Coated Tab Height (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "notched_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

anode_tabless_design_parameters = ds.html.Div(
    id="anode_tabless_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="width",
            title="Width (mm)",
            message="will influence allowed coated width, tab height and insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="coated_width",
            title="Coated Width (mm)",
            message="will influence the tab height (keeping tape width constant) and the allowed insulation width values",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="tab_height",
            title="Tab Height (mm)",
            message="will influence the coated width (keeping tab width constant)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            property_name="insulation_width",
            title="Insulation Width (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabless_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

anode_tabbed_design_parameters = ds.html.Div(
    id="anode_tabbed_design_parameters",
    children=[
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Body", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="length",
            title="Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="width",
            title="Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="thickness",
            title="Thickness (\u03bcm)",
        )(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Tab Parameters", style={"font-weight": "bold"}),
        ds.html.Br(),
        ds.dcc.Dropdown(
            id="anode_current_collector_tab_material_selector",
            placeholder="Select Anode Current Collector Material",
            style={"width": "calc(50%)"},
            options=[{"label": material, "value": material} for material in CURRENT_COLLECTOR_MATERIALS],
        ),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tab_material"},
            property_name="density",
            title="Tab Material Density (kg/m³)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tab_material"},
            property_name="specific_cost",
            title="Tab Material Specific Cost (€/kg)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="tab_width",
            title="Tab Width (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="tab_length",
            title="Tab Length (mm)",
        )(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="tab_overhang",
            title="Tab Overhang (mm)",
        )(),
        ds.html.Br(),
        ds.html.P("Tab Weld Side"),
        ds.dcc.RadioItems(
            id={
                "electrode": "anode",
                "object": "tabbed_current_collector",
                "property": "tab_weld_side",
                "subtype": "radioitem",
            },
            options=[
                {"label": "A Side", "value": "a"},
                {"label": "B Side", "value": "b"},
            ],
            value="a",
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.P('Tab Positions Relative to Start of Tape (mm). Enter positions as a comma-separated list (e.g., "0, 100, 200")'),
        ds.dcc.Input(
            id={
                "electrode": "anode",
                "object": "tabbed_current_collector",
                "property": "tab_positions_text",
                "subtype": "text_input",
            },
            type="text",
            style={"width": "60%", "marginBottom": "10px"},
            debounce=True,
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        ds.html.H5("Coating", style={"font-weight": "bold"}),
        ds.html.Br(),
        SliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            property_name="skip_coat_width",
            title="Width of Tab Skip Coats (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="a_side_coated_section",
            title="A Side Coated Section (mm)",
        )(),
        RangeSliderWithTextInput(
            id_base={"electrode": "anode", "object": "tabbed_current_collector"},
            min_val=0,
            max_val=5000,
            step=0.1,
            mark_interval=500,
            property_name="b_side_coated_section",
            title="B Side Coated Section (mm)",
        )(),
    ],
)

anode_current_collector_layout = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Br(),
        ds.html.Br(),
        anode_current_collector_material_parameters,
        anode_current_collector_design_parameters,
        anode_punched_design_parameters,
        anode_notched_design_parameters,
        anode_tabless_design_parameters,
        anode_tabbed_design_parameters,
        ds.html.Div(style={"height": "200px"}),
    ],
    style={
        "padding": "20px",
        "width": "calc(100%)",
    },
)


#############################
#       TABS DIVS           #
#############################

cathode_tabs_div = ds.html.Div(
    id="cathode_tabs_panel",
    children=[
        ds.dcc.Tabs(
            id="cathode-tabs-container",
            children=[
                ds.dcc.Tab(
                    label="Current Collector",
                    value="cathode_current_collector",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Formulation",
                    value="cathode_formulation",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Electrode",
                    value="cathode_electrode",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
            ],
            value="cathode_current_collector",
        ),
        ds.html.Div(
            id="cathode_current_collector_tab",
            children=[cathode_current_collector_layout],
            style={"display": "block", "padding": "20px 0"},
        ),
        ds.html.Div(
            id="cathode_formulation_tab",
            children=[cathode_formulation_layout],
            style={"display": "none", "padding": "20px 0"},
        ),
        ds.html.Div(
            id="cathode_electrode_tab",
            children=[cathode_electrode_layout],
            style={"display": "none", "padding": "20px 0"},
        ),
    ],
    style={"margin-left": "20px", "margin-right": "20px", "display": "block"},
)


anode_tabs_div = ds.html.Div(
    id="anode_tabs_panel",
    children=[
        ds.dcc.Tabs(
            id="anode-tabs-container",
            children=[
                ds.dcc.Tab(
                    label="Current Collector",
                    value="anode_current_collector",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Formulation",
                    value="anode_formulation",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Electrode",
                    value="anode_electrode",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
            ],
            value="anode_current_collector",
        ),
        ds.html.Div(
            id="anode_current_collector_tab",
            children=[anode_current_collector_layout],
            style={"display": "block", "padding": "20px 0"},
        ),
        ds.html.Div(
            id="anode_formulation_tab",
            children=[anode_formulation_layout],
            style={"display": "none", "padding": "20px 0"},
        ),
        ds.html.Div(
            id="anode_electrode_tab",
            children=[anode_electrode_layout],
            style={"display": "none", "padding": "20px 0"},
        ),
    ],
    style={"margin-left": "20px", "margin-right": "20px", "display": "block"},
)

