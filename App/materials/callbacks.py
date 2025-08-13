from dash import callback, clientside_callback, Input, Output, ALL, ctx, State, MATCH
from materials.callback_helpers import create_material_callback
from general.enumerated_classes import MaterialType, ElectrodeType


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'step'),
        Output('cathode_current_collector_material_selector', 'value'),
    ],
    [
        Input('cell_store', 'data'),
        Input('cathode_current_collector_material_selector', 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_material(
    cell_data,
    material_selector,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
):

    callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR)

    response = callback_function(
        cell_data,
        material_selector,
        input_values,
        slider_values,
    )

    response = response

    return response

