from dash import callback, Input, Output, ALL, ctx, State
from materials.callback_helpers import create_material_callback
from general.enumerated_classes import MaterialType


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_current_collector_material_selector', 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input('cathode_current_collector_material_selector', 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'drag_value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'step'),
        State({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_material(
    cell_data,
    material_selector,
    drag_values,
    input_values,
    slider_values,
    slider_steps,
    input_steps
):

    callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR)

    response = callback_function(
        cell_data,
        material_selector,
        input_values,
        slider_values,
        drag_values,
        slider_steps,
        input_steps
    )

    response = response

    return response

