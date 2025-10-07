import dash as ds
from App.general.styles import *

# Import warnings from general layouts
from App.general.layouts import warnings

# Simple placeholder content for results tabs
mechanicals_tab_content = ds.html.Div(
    id="mechanicals_tab_content",
    children=[
        ds.html.P("Mechanicals content will be displayed here", style={"color": "#6c757d", "line-height": "1.5"}),
    ]
)

load_balancing_tab_content = ds.html.Div(
    id="load_balancing_tab_content",
    children=[
        ds.html.P("Load balancing content will be displayed here", style={"color": "#6c757d", "line-height": "1.5"}),
    ]
)

construction_tab_content = ds.html.Div(
    id="construction_tab_content",
    children=[
        ds.html.P("Construction content will be displayed here", style={"color": "#6c757d", "line-height": "1.5"}),
    ]
)

results_tab_content = ds.html.Div(
    id="results_tab_content",
    children=[
        ds.html.P("Results content will be displayed here", style={"color": "#6c757d", "line-height": "1.5"}),
    ]
)

warnings_tab_content = ds.html.Div(
    id="warnings_tab_content",
    children=[warnings]
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
