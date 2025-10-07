import dash as ds
from App.general.styles import *

# Results tabs content
mechanicals_tab_content = ds.html.Div(
    id="mechanicals_tab_content",
    children=[
        ds.html.H5("Mechanical Properties", style={"color": "#333", "margin-bottom": "15px"}),
        ds.html.P("• Cell dimensions and weight", style={"color": "#666"}),
        ds.html.P("• Structural integrity analysis", style={"color": "#666"}),
        ds.html.P("• Thermal management", style={"color": "#666"}),
        ds.html.P("• Safety factors", style={"color": "#666"}),
    ]
)

load_balancing_tab_content = ds.html.Div(
    id="load_balancing_tab_content",
    children=[
        ds.html.H5("Load Balancing Analysis", style={"color": "#333", "margin-bottom": "15px"}),
        ds.html.P("• Current distribution", style={"color": "#666"}),
        ds.html.P("• Voltage uniformity", style={"color": "#666"}),
        ds.html.P("• Heat generation mapping", style={"color": "#666"}),
        ds.html.P("• Efficiency optimization", style={"color": "#666"}),
    ]
)

construction_tab_content = ds.html.Div(
    id="construction_tab_content",
    children=[
        ds.html.H5("Construction Details", style={"color": "#333", "margin-bottom": "15px"}),
        ds.html.P("• Assembly specifications", style={"color": "#666"}),
        ds.html.P("• Material breakdown", style={"color": "#666"}),
        ds.html.P("• Manufacturing considerations", style={"color": "#666"}),
        ds.html.P("• Quality control metrics", style={"color": "#666"}),
    ]
)

results_tab_content = ds.html.Div(
    id="results_tab_content",
    children=[
        ds.html.H5("Performance Results", style={"color": "#333", "margin-bottom": "15px"}),
        ds.html.P("• Energy density", style={"color": "#666"}),
        ds.html.P("• Power density", style={"color": "#666"}),
        ds.html.P("• Cost analysis", style={"color": "#666"}),
        ds.html.P("• Performance plots", style={"color": "#666"}),
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
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Load Balancing",
                    value="load_balancing",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Construction",
                    value="construction",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
                ds.dcc.Tab(
                    label="Results",
                    value="results",
                    className="tab-style",
                    selected_className="tab-selected-style",
                ),
            ],
            value="mechanicals",
        ),
        ds.html.Div(id="mechanicals_tab", children=[mechanicals_tab_content], style={"display": "block", "padding-top": "20px"}),
        ds.html.Div(id="load_balancing_tab", children=[load_balancing_tab_content], style={"display": "none", "padding-top": "20px"}),
        ds.html.Div(id="construction_tab", children=[construction_tab_content], style={"display": "none", "padding-top": "20px"}),
        ds.html.Div(id="results_tab", children=[results_tab_content], style={"display": "none", "padding-top": "20px"}),
    ],
    style={
        "height": "100%",
        "overflowY": "auto"
    }
)
