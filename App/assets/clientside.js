window.dash_clientside = Object.assign({}, window.dash_clientside, {
    slider_sync: {
        // Optimized for single value (MATCH pattern)
        sync_drag_to_input: function(drag_value) {
            // Early return for undefined/null
            if (drag_value === undefined || drag_value === null) {
                return window.dash_clientside.no_update;
            }
            return drag_value;
        },
        
        // For arrays (ALL pattern) - but use MATCH instead for better performance
        sync_drag_to_input_array: function(drag_values) {
            if (!drag_values || !Array.isArray(drag_values)) {
                return window.dash_clientside.no_update;
            }
            // Only return values that actually changed
            return drag_values;
        },
        
        // Optimized range slider functions
        sync_range_start: function(drag_value) {
            if (!drag_value || !Array.isArray(drag_value) || drag_value.length < 2) {
                return window.dash_clientside.no_update;
            }
            return drag_value[0];
        },
        
        sync_range_end: function(drag_value) {
            if (!drag_value || !Array.isArray(drag_value) || drag_value.length < 2) {
                return window.dash_clientside.no_update;
            }
            return drag_value[1];
        }
    }
});