import dash as ds

from App.general.styles import *
from App.general.store import (
    cell_store,
    old_cell_store,
    warnings_store,
    cathode_active_material_store,
    anode_active_material_store,
    LANDING_PAGE_IMAGE_URLS,
)
from App.general.database_service import FORM_FACTOR_OPTIONS
from App.general.orchestra import last_triggered

from App.current_collectors.layouts import cathode_tabs_div, anode_tabs_div
from App.current_collectors.orchestra import current_collector_trigger_stores

from App.electrodes.orchestra import electrode_trigger_stores

from App.formulations.orchestra import formulation_trigger_stores

from App.layup.layouts import layup_tabs_div
from App.layup.orchestra import layup_trigger_stores

from App.electrode_assembly.layouts import electrode_assembly_layout

from App.results.layouts import (
    mechanicals_tab_content,
    load_balancing_tab_content,
    construction_tab_content,
    results_tab_content,
    warnings_tab_content
)
from App.results.orchestra import results_trigger_stores

#############################
# Configuration Constants   #
#############################

# Main tab configuration
MAIN_TAB_CONFIG = [
    {"label": "Cathode", "value": "cathode"},
    {"label": "Anode", "value": "anode"},
    {"label": "Layup", "value": "layup"},
    {"label": "Electrode Assembly", "value": "electrode_assembly"},
]

# Results tab configuration
RESULTS_TAB_CONFIG = [
    {"label": "Mechanicals", "value": "mechanicals"},
    {"label": "Load Balancing", "value": "load_balancing"},
    {"label": "Construction", "value": "construction"},
    {"label": "Results", "value": "results"},
    {"label": "Warnings", "value": "warnings"},
]

# Layout constants
GOLDEN_RATIO = 1.618
GRID_COLUMNS = 3

# Main layout styles
MAIN_LAYOUT_STYLE = {
    "display": "flex",
    "flexDirection": "row",
    "width": "100%",
    "gap": "0px"
}

MAIN_CONTENT_STYLE = {
    "flex": "1",
    "paddingRight": "15px"
}

TAB_CONTENT_MAIN_STYLE = {
    "flex": "1",
    "paddingRight": "15px"
}

TAB_CONTENT_RESULTS_STYLE = {
    "flex": "1.618",
    "backgroundColor": "#f8f9fa", 
    "border": "1px solid #dee2e6",
    "borderRadius": "8px",
    "padding": "20px",
    "marginLeft": "10px",
    "minHeight": "calc(100vh - 300px)"
}

# Tab content styles
TAB_CONTENT_VISIBLE_STYLE = {"display": "block", "padding": "20px 0"}
TAB_CONTENT_HIDDEN_STYLE = {"display": "none", "padding": "20px 0"}

# Results sidebar content style
RESULTS_SIDEBAR_CONTENT_STYLE = {
    "height": "100%",
    "overflowY": "auto"
}

# Dashboard header style
DASHBOARD_HEADER_STYLE = {"color": "#333", "margin-bottom": "20px"}


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
            style=HEADER_WITH_PADDING_STYLE,
        ),
        ds.html.Br(),
        ds.html.Br(),
    ]
)


header = ds.html.Div(
    [
        ds.html.H1("OpenCell Design Tool", style=HEADER_STYLE | {"padding-left": "20px"}),
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
                        style=CELL_SCHEMATIC_IMAGE_STYLE,
                    )
                ],
                id={"type": "cell_schematic_button", "key": j},
                style=CELL_SCHEMATIC_BUTTON_STYLE,
                className="cell-schematic-button",  # For CSS hover effects
            )
            for (j, i) in LANDING_PAGE_IMAGE_URLS.items()
        ],
        style=get_cell_schematic_grid_style(GRID_COLUMNS),
    ),
    style=CELL_SCHEMATIC_PANEL_STYLE,
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
                    style={"width": DROPDOWN_WIDTH},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Internal Construction"),
                ds.dcc.Dropdown(
                    id="internal_construction_dropdown",
                    options=[],
                    style={"width": DROPDOWN_WIDTH},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Electrochemical Reference"),
                ds.dcc.Dropdown(
                    id="electrochemical_reference_dropdown",
                    options=[],
                    style={"width": DROPDOWN_WIDTH},
                ),
                ds.html.Br(),
                ds.html.Br(),
                ds.html.H5("Cell Name"),
                ds.dcc.Dropdown(
                    id="cell_name_dropdown",
                    options=[],
                    style={"width": DROPDOWN_WIDTH},
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
        ds.html.Div(id="cathode_tab", children=[cathode_tabs_div], style=TAB_CONTENT_VISIBLE_STYLE),
        ds.html.Div(id="anode_tab", children=[anode_tabs_div], style=TAB_CONTENT_HIDDEN_STYLE),
        ds.html.Div(id="layup_tab", children=[layup_tabs_div], style=TAB_CONTENT_HIDDEN_STYLE),
        ds.html.Div(id="electrode_assembly_tab",children=[electrode_assembly_layout],style=TAB_CONTENT_HIDDEN_STYLE,),
    ]
)



# Results sidebar with tabs
results_sidebar = ds.html.Div(
    id="results_sidebar",
    children=[
        ds.html.H4("Analysis Dashboard", style=DASHBOARD_HEADER_STYLE),
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
            style=MAIN_LAYOUT_STYLE,
            children=[
                # Main content area (golden ratio smaller portion)
                ds.html.Div(
                    children=[main_tabs_content],
                    style=TAB_CONTENT_MAIN_STYLE
                ),
                # Results area (golden ratio larger portion)
                ds.html.Div(
                    children=[results_sidebar],  # Will be populated by callback
                    style=TAB_CONTENT_RESULTS_STYLE
                )
            ]
        )
    ],
    style=DIV_STYLE | {"display": "none"},
)


