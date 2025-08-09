from dash import callback, Input, Output, ALL, State

from electrodes.cell_operations import get_electrode_from_cell
from electrodes.callback_helpers import create_electrode_callback

from general.enumerated_classes import ElectrodeType, MaterialType
from general.callback_helpers import create_material_callback
from cache_service import cache



@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_insulation_material_selector', 'value'),
        Output({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input('cathode_insulation_material_selector', 'value'),
        Input({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'insulation_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_cathode_insulation_material(
    cell_data,
    material_selector,
    input_values,
    slider_values,
):
    
    callback_function = create_material_callback(MaterialType.CATHODE_INSULATION)

    response = callback_function(
        cell_data,
        material_selector,
        input_values,
        slider_values
    )

    return response



@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output('warnings_store', 'data'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'action': 'flip_x'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'action': 'flip_y'}, 'n_clicks'),
    ],
    [
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode(cell_data, input_values, slider_values, flip_x, flip_y, existing_warnings):

    callback_function = create_electrode_callback(ElectrodeType.CATHODE)

    response = callback_function(
        cell_data,
        input_values,
        slider_values,
        flip_x,
        flip_y,
        existing_warnings
    )

    return response


@callback(
    [
        Output('cathode_top_down_plot', 'figure'),
        Output('cathode_cross_section_plot', 'figure'),
        Output('cathode_areal_capacity_plot', 'figure'),
        Output('cathode_capacity_plot', 'figure'),
    ],
    [
        Input('cell_store', 'data'),
        Input('continue_to_design', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_cathode_plots(cell_data, continue_to_design):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    cathode = get_electrode_from_cell(cell, ElectrodeType.CATHODE)

    # get the plots from the current collector
    plot_a = cathode.get_top_down_view(title='Top-Down Cathode View')
    plot_b = cathode.get_cross_section(title='Cross-Section Cathode View')
    plot_areal_capacity = cathode.plot_half_cell_curve(areal=True, title='Areal Capacity Plot')
    plot_capacity = cathode.plot_half_cell_curve(areal=False, title='Capacity Plot')

    return plot_a, plot_b, plot_areal_capacity, plot_capacity


