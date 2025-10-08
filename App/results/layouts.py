import dash as ds
from App.general.styles import *


# Define common styles as constants
FIGURE_CONTAINER_STYLE = {
    "width": "48%", 
    "display": "inline-block", 
    "margin": "1%",
    "border": "1px solid #ddd",
    "border-radius": "4px",
    "padding": "10px",
    "height": "600px"  # Much taller for proper square appearance
}

FIGURE_GRAPH_STYLE = {
    "height": "570px"  # Much taller to make figures truly square
}

mechanicals_tab_content = ds.html.Div(
    id="mechanicals_tab_content",
    children=[
        # 2x2 grid layout for the four figures
        ds.html.Div(
            children=[
                # Top row
                ds.html.Div(
                    children=[
                        # Top left - Cathode A Side
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="cathode_a_side",
                                    config={'displayModeBar': False},
                                    style=FIGURE_GRAPH_STYLE
                                )
                            ],
                            style=FIGURE_CONTAINER_STYLE
                        ),
                        # Top right - Anode A Side
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="anode_a_side",
                                    config={'displayModeBar': False},
                                    style=FIGURE_GRAPH_STYLE
                                )
                            ],
                            style=FIGURE_CONTAINER_STYLE
                        ),
                    ],
                    style={"width": "100%", "margin-bottom": "20px"}
                ),
                # Bottom row
                ds.html.Div(
                    children=[
                        # Bottom left - Cathode B Side
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="cathode_b_side",
                                    config={'displayModeBar': False},
                                    style=FIGURE_GRAPH_STYLE
                                )
                            ],
                            style=FIGURE_CONTAINER_STYLE
                        ),
                        # Bottom right - Anode B Side
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="anode_b_side",
                                    config={'displayModeBar': False},
                                    style=FIGURE_GRAPH_STYLE
                                )
                            ],
                            style=FIGURE_CONTAINER_STYLE
                        ),
                    ],
                    style={"width": "100%"}
                ),
            ],
            style={"width": "100%", "padding": "10px"}
        )
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

warnings = ds.html.Div(
    id="warnings",
    children=[
        ds.html.P("No warnings to display.", style={"color": "#6c757d", "line-height": "1.5"}),
    ]
)

warnings_tab_content = ds.html.Div(
    id="warnings_tab_content",
    children=[warnings]
)
