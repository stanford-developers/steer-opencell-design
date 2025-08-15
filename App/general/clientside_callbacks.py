from dash import MATCH, clientside_callback, Input, Output

clientside_callback(
    """
    function(slider_value) {
        if (slider_value === null || slider_value === undefined) {
            return window.dash_clientside.no_update;
        }
        return slider_value;
    }
    """,
    Output({'electrode': MATCH, 'object': MATCH, 'property': MATCH, 'subtype': 'input'}, 'value'),
    Input({'electrode': MATCH, 'object': MATCH, 'property': MATCH, 'subtype': 'slider'}, 'drag_value'),
    Input('cell_store', 'modified_timestamp'),
    prevent_initial_call=True
)

# Clientside callback to sync rangeslider drag_value to input_start and input_end values
clientside_callback(
    """
    function(rangeslider_values) {
        if (!rangeslider_values || !Array.isArray(rangeslider_values) || rangeslider_values.length !== 2) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        
        // rangeslider_values is a tuple [start, end]
        const start_value = rangeslider_values[0];
        const end_value = rangeslider_values[1];
        
        return [start_value, end_value];
    }
    """,
    [
        Output({'electrode': MATCH, 'object': MATCH, 'property': MATCH, 'subtype': 'input_start'}, 'value'),
        Output({'electrode': MATCH, 'object': MATCH, 'property': MATCH, 'subtype': 'input_end'}, 'value')
    ],
    Input({'electrode': MATCH, 'object': MATCH, 'property': MATCH, 'subtype': 'rangeslider'}, 'drag_value'),
    Input('cell_store', 'modified_timestamp'),
    prevent_initial_call=True
)

