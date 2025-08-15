window.dash_clientside = Object.assign({}, window.dash_clientside, {
    slider_sync: {
        sync_drag_to_input: function(drag_value) {
            // Only update input visually during drag, don't trigger server callbacks
            if (drag_value === undefined || drag_value === null) {
                return window.dash_clientside.no_update;
            }
            return drag_value;
        }
    }
});
