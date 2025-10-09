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

# Load balancing specific styles
LOAD_BALANCING_CONTAINER_BASE = {
    "border": "1px solid #ddd",
    "border-radius": "4px",
    "padding": "10px",
}

LOAD_BALANCING_LEFT_CONTAINER = {
    **LOAD_BALANCING_CONTAINER_BASE,
    "width": "100%",
    "margin-bottom": "20px",
    "height": "650px"
}

LOAD_BALANCING_LEFT_CONTAINER_BOTTOM = {
    **LOAD_BALANCING_CONTAINER_BASE,
    "width": "100%",
    "height": "650px"
}

LOAD_BALANCING_RIGHT_CONTAINER = {
    **LOAD_BALANCING_CONTAINER_BASE,
    "width": "64%",
    "display": "inline-block",
    "vertical-align": "top",
    "height": "1320px"
}

LOAD_BALANCING_LEFT_COLUMN_STYLE = {
    "width": "32%",
    "display": "inline-block",
    "vertical-align": "top",
    "margin-right": "2%"
}

LOAD_BALANCING_SMALL_GRAPH_STYLE = {
    "height": "630px"
}

LOAD_BALANCING_LARGE_GRAPH_STYLE = {
    "height": "1270px"
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
        ds.html.Div(
            children=[
                # Left column - two figures stacked vertically (1/3 width)
                ds.html.Div(
                    children=[
                        # Top left - Cathode Cross Section
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="cathode_cross_section",
                                    config={'displayModeBar': False},
                                    style=LOAD_BALANCING_SMALL_GRAPH_STYLE
                                )
                            ],
                            style=LOAD_BALANCING_LEFT_CONTAINER
                        ),
                        # Bottom left - Anode Cross Section
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="anode_cross_section",
                                    config={'displayModeBar': False},
                                    style=LOAD_BALANCING_SMALL_GRAPH_STYLE
                                )
                            ],
                            style=LOAD_BALANCING_LEFT_CONTAINER_BOTTOM
                        ),
                    ],
                    style=LOAD_BALANCING_LEFT_COLUMN_STYLE
                ),
                # Right column - large figure (2/3 width)
                ds.html.Div(
                    children=[
                        ds.dcc.Graph(
                            id="areal_capacity_plot",
                            config={'displayModeBar': False},
                            style=LOAD_BALANCING_LARGE_GRAPH_STYLE
                        )
                    ],
                    style=LOAD_BALANCING_RIGHT_CONTAINER
                ),
            ],
            style={"width": "100%", "padding": "10px"}
        )
    ]
)

construction_tab_content = ds.html.Div(
    id="construction_tab_content",
    children=[
        ds.html.Div(
            children=[
                # Top row - full width figure with opacity slider
                ds.html.Div(
                    children=[
                        ds.html.Div(
                            children=[
                                ds.html.Label("Opacity:", style={"margin-right": "10px", "font-weight": "bold", "min-width": "80px"}),
                                ds.html.Div(
                                    children=[
                                        ds.dcc.Slider(
                                            id="layup_design_opacity_slider",
                                            min=0,
                                            max=1,
                                            step=0.1,
                                            value=1.0,
                                            marks={i/10: f"{i/10:.1f}" for i in range(0, 11, 2)},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        )
                                    ],
                                    style={"flex": "1", "margin-right": "20px"}
                                )
                            ],
                            style={
                                "display": "flex",
                                "align-items": "center",
                                "margin-bottom": "10px",
                                "padding": "0 10px"
                            }
                        ),
                        ds.dcc.Graph(
                            id="layup_design_figure",
                            style=FIGURE_GRAPH_STYLE
                        )
                    ],
                    style={
                        "width": "100%",
                        "border": "1px solid #ddd",
                        "border-radius": "4px",
                        "padding": "10px",
                        "margin-bottom": "20px",
                        "height": "650px"  # Increased height to accommodate slider
                    }
                ),
                # Bottom row - two half-width figures
                ds.html.Div(
                    children=[
                        # Bottom left
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="electrode_assembly_top_down",
                                    config={'displayModeBar': False},
                                    style=FIGURE_GRAPH_STYLE
                                )
                            ],
                            style=FIGURE_CONTAINER_STYLE
                        ),
                        # Bottom right
                        ds.html.Div(
                            children=[
                                ds.dcc.Graph(
                                    id="electrode_assembly_right_left",
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
