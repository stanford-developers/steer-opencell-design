import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Theme and Color Constants
BOOTSTRAP_THEME = dbc.themes.LUX
RIGHT_PANEL_COLOR = "#e3e5e6"

#############################
# General Component Styles  #
#############################

# Headers and Text
HEADER_STYLE = {"textAlign": "left"}
DASHBOARD_HEADER_STYLE = {"color": "#333", "margin-bottom": "20px"}
SECTION_HEADER_STYLE = {"font-weight": "bold"}
DESCRIPTION_TEXT_STYLE = {"margin-bottom": "10px", "color": "#666"}
PLACEHOLDER_TEXT_STYLE = {"color": "#6c757d", "line-height": "1.5"}

# Dropdowns and Inputs
DROPDOWN_STYLE = {"width": "50%"}
DROPDOWN_WIDTH_HALF = {"width": "calc(50%)"}
DROPDOWN_WIDTH = "80%"
INPUT_STYLE = {"width": "16%", "margin-left": "10px"}
TEXT_INPUT_STYLE = {"width": "100%", "margin-left": "10px", "margin-bottom": "15px"}

# Buttons
BUTTON_STYLE = {
    "margin-left": "10px",
    "background-color": "white",
    "border": "1px solid #ccc",
    "padding": "5px 10px",
    "cursor": "pointer",
}

ADD_REMOVE_BUTTON_STYLE = {
    "backgroundColor": "#f8f9fa",
    "color": "black",
    "border": "none",
    "borderRadius": "50%",
    "width": "30px",
    "height": "30px",
    "fontSize": "16px",
    "cursor": "pointer",
}

ADD_REMOVE_BUTTON_CONTAINER_STYLE = {"marginTop": "10px", "marginBottom": "20px"}

# Containers and Divs
DIV_STYLE = {"margin-left": "20px", "margin-right": "20px", "width": "calc(100)"}
BUTTON_DIV_STYLE = {"display": "flex", "gap": "10px", "margin-left": "-10px"}

# Layout containers
FULL_WIDTH_CONTAINER = {"width": "100%"}
FULL_WIDTH_WITH_PADDING = {"width": "100%", "padding": "10px"}
FULL_WIDTH_WITH_MARGIN = {"width": "100%", "margin-bottom": "20px"}

#############################
# Cell Type Panel Styles    #
#############################

CELL_TYPE_PANEL_STYLE = {
    "display": "flex",
    "flex-direction": "row",
    "padding": "100px",
    "width": "90%",
}

CELL_TYPE_FORM_STYLE = {
    "flex": "0 0 35%",
    "padding": "20px",
    "justify-content": "center",
    "align-items": "center",
    "padding-top": "-400px",
}

CELL_SCHEMATIC_IMAGE_STYLE = {
    "width": "50%",
    "height": "auto",
    "display": "block",
    "margin": "20px auto",
}

CELL_SCHEMATIC_BUTTON_STYLE = {
    "border": "none",
    "background": "none",
    "padding": "20px",
    "cursor": "pointer",
    "width": "100%",
    "height": "auto",
    "border-radius": "8px",
    "transition": "transform 0.2s ease, box-shadow 0.2s ease",
    "text-align": "center",
}

def get_cell_schematic_grid_style(grid_columns):
    return {
        "display": "grid",
        "gridTemplateColumns": f"repeat({grid_columns}, 1fr)",
        "gap": "10px",
        "margin-top": "-20px",
        "margin-left": "100px",
    }

CELL_SCHEMATIC_PANEL_STYLE = {
    "flex": "1",
    "padding": "20px",
    "justify-content": "center",
    "align-items": "left",
    "width": "10%",
    "margin-top": "-100px",
}

#############################
# Main Layout Styles        #
#############################

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

TAB_CONTENT_VISIBLE_STYLE = {"display": "block", "padding": "20px 0"}
TAB_CONTENT_HIDDEN_STYLE = {"display": "none", "padding": "20px 0"}

RESULTS_SIDEBAR_CONTENT_STYLE = {
    "padding": "20px",
    "backgroundColor": "#ffffff",
    "border-radius": "4px"
}

#############################
# Results Tab Styles        #
#############################

# Figure containers
FIGURE_CONTAINER_STYLE = {
    "width": "48%", 
    "display": "inline-block", 
    "margin": "1%",
    "border": "1px solid #ddd",
    "border-radius": "4px",
    "padding": "10px",
    "height": "600px"
}

FIGURE_GRAPH_STYLE = {
    "height": "570px"
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

# Construction tab styles
CONSTRUCTION_OPACITY_LABEL_STYLE = {"margin-right": "10px", "font-weight": "bold", "min-width": "80px"}
CONSTRUCTION_SLIDER_CONTAINER_STYLE = {"flex": "1", "margin-right": "20px"}
CONSTRUCTION_OPACITY_CONTAINER_STYLE = {
    "display": "flex",
    "align-items": "center",
    "margin-bottom": "20px",
    "padding": "15px",
    "background-color": "#f8f9fa",
    "border-radius": "5px",
    "border": "1px solid #dee2e6"
}

CONSTRUCTION_FIGURE_CONTAINER_STYLE = {
    "width": "100%",
    "display": "flex",
    "flex-direction": "column",
    "gap": "20px"
}

#############################
# Electrode Layout Styles   #
#############################

ELECTRODE_LAYOUT_CONTAINER = {"padding": "20px", "width": "100%"}
ELECTRODE_SPACING_DIV = {"height": "200px"}

# Control mode styles
CONTROL_MODE_CONTAINER = {"margin": "10px 0"}
CONTROL_MODE_INPUT_STYLE = {"margin-right": "8px", "transform": "scale(1.2)"}
CONTROL_MODE_LABEL_STYLE = {
    "display": "flex",
    "align-items": "center",
    "margin-bottom": "8px",
    "font-weight": "bold",
}

#############################
# Inline Utility Styles     #
#############################

# Common inline styles that appear frequently
HEADER_WITH_PADDING_STYLE = {"width": "20%", "height": "auto", "padding-left": "15px"}

# Plotly Figure
EMPTY_FIG = go.Figure()
EMPTY_FIG.update_layout(paper_bgcolor=RIGHT_PANEL_COLOR, plot_bgcolor=RIGHT_PANEL_COLOR)
