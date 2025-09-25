from dash import MATCH, clientside_callback, Input, Output

clientside_callback(
    """
    function(slider_value) {
        return slider_value;
    }
    """,
    Output(
        {"electrode": MATCH, "object": MATCH, "property": MATCH, "subtype": "input"},
        "value",
    ),
    Input(
        {"electrode": MATCH, "object": MATCH, "property": MATCH, "subtype": "slider"},
        "value",
    ),
    prevent_initial_call=True,
)



clientside_callback(
    """
    function(slider_value) {
        return slider_value;
    }
    """,
    Output({"object": MATCH, "property": MATCH, "subtype": "input"}, "value"),
    Input({"object": MATCH, "property": MATCH, "subtype": "slider"}, "value"),
    prevent_initial_call=True,
)

clientside_callback(
    """
    function(slider_value) {
        return slider_value;
    }
    """,
    Output(
        {
            "electrode": MATCH,
            "object": MATCH,
            "material": MATCH,
            "property": MATCH,
            "index": MATCH,
            "subtype": "input",
        },
        "value",
    ),
    Input(
        {
            "electrode": MATCH,
            "object": MATCH,
            "property": MATCH,
            "index": MATCH,
            "material": MATCH,
            "subtype": "slider",
        },
        "value",
    ),
    prevent_initial_call=True,
)

# Rangeslider callback
clientside_callback(
    """
    function(rangeslider_values) {
        if (!rangeslider_values || !Array.isArray(rangeslider_values) || rangeslider_values.length !== 2) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        return [rangeslider_values[0], rangeslider_values[1]];
    }
    """,
    [
        Output(
            {
                "electrode": MATCH,
                "object": MATCH,
                "property": MATCH,
                "subtype": "input_start",
            },
            "value",
        ),
        Output(
            {
                "electrode": MATCH,
                "object": MATCH,
                "property": MATCH,
                "subtype": "input_end",
            },
            "value",
        ),
    ],
    Input(
        {
            "electrode": MATCH,
            "object": MATCH,
            "property": MATCH,
            "subtype": "rangeslider",
        },
        "value",
    ),
    prevent_initial_call=True,
)
