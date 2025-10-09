import dash as ds
from App.general.styles import *

from App.current_collectors.layouts import cathode_current_collector_layout, anode_current_collector_layout
from App.formulations.layouts import cathode_formulation_layout, anode_formulation_layout
from App.electrodes.layouts import cathode_electrode_layout, anode_electrode_layout

from App.current_collectors.orchestra import current_collector_trigger_stores
from App.electrodes.orchestra import electrode_trigger_stores
from App.layup.orchestra import layup_trigger_stores
from App.formulations.orchestra import formulation_trigger_stores
from App.results.orchestra import results_trigger_stores
from App.general.orchestra import last_triggered

from App.layup.layouts import layup_mechanicals_layout, layup_areal_layout

from App.electrode_assembly.layouts import electrode_assembly_layout

from App.general.store import (
    cell_store,
    old_cell_store,
    warnings_store,
    cathode_active_material_store,
    anode_active_material_store,
    LANDING_PAGE_IMAGE_URLS,
)

from App.results.layouts import (
    mechanicals_tab_content,
    load_balancing_tab_content,
    construction_tab_content,
    results_tab_content,
    warnings_tab_content
)

from App.general.database_service import FORM_FACTOR_OPTIONS


stores = ds.html.Div([
        cell_store,
        old_cell_store,
        warnings_store,
        cathode_active_material_store,
        anode_active_material_store,
        last_triggered,
        current_collector_trigger_stores,
        electrode_trigger_stores,
        formulation_trigger_stores,
        layup_trigger_stores,
        results_trigger_stores
])


thumbnail = ds.html.Div(
    [
        ds.html.Br(),
        ds.html.Img(
            src="assets/header_image.png",
            style={"width": "20%", "height": "auto", "padding-left": "15px"},
        ),
        ds.html.Br(),
        ds.html.Br(),
    ]
)


header = ds.html.Div(
    [
        ds.html.H1("OpenCell Design Tool", style=HEADER_STYLE | {"padding-left": "20px"}),
        # ds.html.P(["Please reach out to Dr. Nicholas Siemons at nsiemons@stanford.edu for help or feedback."], style={'padding-left': '20px'}),
        ds.html.Br(),
        ds.html.Br(),
    ]
)


cell_type_button_panel = ds.html.Div(
    ds.html.Div(
        id="cell_schematic",
        children=[
            ds.html.Button(
                children=[
                    ds.html.Img(
                        id={"type": "cell_schematic_image", "key": j},
                        src=i,
                        style={
                            "width": "50%",
                            "height": "auto",
                            "display": "block",
                            "margin": "20px auto",  # Centers horizontally and adds vertical margin
                        },
                    )
                ],
                id={"type": "cell_schematic_button", "key": j},
                style={
                    "border": "none",
                    "background": "none",
                    "padding": "20px",
                    "cursor": "pointer",
                    "width": "100%",
                    "height": "auto",
                    "border-radius": "8px",
                    "transition": "transform 0.2s ease, box-shadow 0.2s ease",
                    "text-align": "center",  # Centers inline/block content
                },
                className="cell-schematic-button",  # For CSS hover effects
            )
            for (j, i) in LANDING_PAGE_IMAGE_URLS.items()
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(3, 1fr)",
            "gap": "10px",
            "margin-top": "-20px",
            "margin-left": "100px",
        },
    ),
    style={
        "flex": "1",
        "padding": "20px",
        "justify-content": "center",
        "align-items": "left",
        "width": "10%",
        "margin-top": "-100px",
    },
)


cell_type = ds.html.Div(
    id="cell_type_panel",
    children=[
        ds.html.Div(
            [
                ds.html.H3("Select Cell from Database"),
                ds.html.Br(),
                ds.html.H5("Form Factor"),
                ds.dcc.Dropdown(
                    id="form_factor_dropdown",
                    options=[{"label": i.replace("_", " ").title(), "value": i} for i in FORM_FACTOR_OPTIONS],
                    style={"width": "80%"},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Internal Construction"),
                ds.dcc.Dropdown(
                    id="internal_construction_dropdown",
                    options=[],
                    style={"width": "80%"},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Electrochemical Reference"),
                ds.dcc.Dropdown(
                    id="electrochemical_reference_dropdown",
                    options=[],
                    style={"width": "80%"},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Cell Name"),
                ds.dcc.Dropdown(
                    id="cell_name_dropdown",
                    options=[],
                    style={"width": "80%"},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H3("... Or Upload Custom Cell"),
                ds.html.Br(),
                ds.html.Div(
                    [
                        ds.dcc.Upload(
                            id="upload_cell",
                            children=[ds.html.A("Select .pkl file for upload", style=BUTTON_STYLE)],
                        ),
                    ],
                    style={"width": "80%"},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.Button(
                    id="continue_to_design",
                    children="Continue to Design \t \u2192 ",
                    style=BUTTON_STYLE | {"width": "30%", "border": "none"},
                ),
                ds.html.Div(style={"height": "100px"}),
            ],
            style={
                "flex": "0 0 35%",
                "padding": "20px",
                "justify-content": "center",
                "align-items": "center",
                "padding-top": "-400px",
            },
        ),
        cell_type_button_panel,
    ],
    style={
        "display": "flex",
        "flex-direction": "row",
        "padding": "100px",
        "width": "90%",
    },
)


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


layup_tabs_div = ds.html.Div(
    id="layup_tabs_panel",
    children=[
        ds.dcc.Tabs(
            id="layup-tabs-container",
            children=[
                ds.dcc.Tab(
                    label="Mechanicals",
                    value="layup_mechanicals_layout",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Areal Designer",
                    value="layup_areal_layout",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
            ],
            value="layup_mechanicals_layout",
        ),
        ds.html.Div(
            id="layup_mechanicals_layout",
            children=[layup_mechanicals_layout],
            style={"display": "block", "padding": "20px 0"},
        ),
        ds.html.Div(
            id="layup_areal_layout",
            children=[layup_areal_layout],
            style={"display": "none", "padding": "20px 0"},
        ),
    ],
    style={"margin-left": "20px", "margin-right": "20px", "display": "block"},
)


# Main tabs content (will be placed in left column)
main_tabs_content = ds.html.Div(
    id="main_tabs_content",
    children=[
        ds.html.Br(),
        ds.html.Button(
            id="back_to_cell_type",
            children="\u2190 Back to Cell Type",
            style=BUTTON_STYLE | {"width": "15%", "border": "none"},
        ),
        ds.html.Br(),
        ds.html.Br(),
        ds.dcc.Tabs(
            id="main-tabs-container",
            children=[
                ds.dcc.Tab(
                    label="Cathode",
                    value="cathode",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Anode",
                    value="anode",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Layup",
                    value="layup",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Electrode Assembly",
                    value="electrode_assembly",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
            ],
            value="cathode",
        ),
        ds.html.Div(id="cathode_tab", children=[cathode_tabs_div], style={"display": "block", "padding": "20px 0"}),
        ds.html.Div(id="anode_tab", children=[anode_tabs_div], style={"display": "none", "padding": "20px 0"}),
        ds.html.Div(id="layup_tab", children=[layup_tabs_div], style={"display": "none", "padding": "20px 0"}),
        ds.html.Div(id="electrode_assembly_tab",children=[electrode_assembly_layout],style={"display": "none", "padding": "20px 0"},),
    ]
)



# Results sidebar with tabs
results_sidebar = ds.html.Div(
    id="results_sidebar",
    children=[
        ds.html.H4("Analysis Dashboard", style={"color": "#333", "margin-bottom": "20px"}),
        ds.dcc.Tabs(
            id="results-tabs-container",
            children=[
                ds.dcc.Tab(
                    label="Mechanicals",
                    value="mechanicals",
                    className="results-tab-style",
                    selected_className="results-tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Load Balancing",
                    value="load_balancing",
                    className="results-tab-style",
                    selected_className="results-tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Construction",
                    value="construction",
                    className="results-tab-style",
                    selected_className="results-tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Results",
                    value="results",
                    className="results-tab-style",
                    selected_className="results-tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Warnings",
                    value="warnings",
                    className="results-tab-style",
                    selected_className="results-tab-selected-style",
                ),
            ],
            value="mechanicals",
        ),
        ds.html.Div(
            id="mechanicals_tab", 
            children=[mechanicals_tab_content], 
            style={"display": "block", "padding": "20px 0"}
        ),
        ds.html.Div(
            id="load_balancing_tab", 
            children=[load_balancing_tab_content], 
            style={"display": "none", "padding": "20px 0"}
        ),
        ds.html.Div(
            id="construction_tab", 
            children=[construction_tab_content], 
            style={"display": "none", "padding": "20px 0"}
        ),
        ds.html.Div(
            id="results_tab", 
            children=[results_tab_content], 
            style={"display": "none", "padding": "20px 0"}
        ),
        ds.html.Div(
            id="warnings_tab", 
            children=[warnings_tab_content], 
            style={"display": "none", "padding": "20px 0"}
        ),
    ],
    style={
        "height": "100%",
        "overflowY": "auto"
    }
)



# Split layout with main tabs (2/3) and results sidebar (1/3)
main_tabs = ds.html.Div(
    id="tabs_panel",
    children=[
        ds.html.Div(
            style={
                "display": "flex",
                "flexDirection": "row",
                "width": "100%",
                "gap": "0px"
            },
            children=[
                # Main content area (golden ratio smaller portion)
                ds.html.Div(
                    children=[main_tabs_content],
                    style={
                        "flex": "1",
                        "paddingRight": "15px"
                    }
                ),
                # Results area (golden ratio larger portion)
                ds.html.Div(
                    children=[results_sidebar],  # Will be populated by callback
                    style={
                        "flex": "1.618",
                        "backgroundColor": "#f8f9fa",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "8px",
                        "padding": "20px",
                        "marginLeft": "10px",
                        "minHeight": "calc(100vh - 300px)"
                    }
                )
            ]
        )
    ],
    style=DIV_STYLE | {"display": "none"},
)


