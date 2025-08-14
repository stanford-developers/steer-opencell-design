from dash import callback, Input, Output, ALL, State

from App.general.callback_helpers import create_properties_table
from electrodes.callback_helpers import create_electrode_callback
from electrodes.configs import ELECTRODE_CONFIGS

from general.enumerated_classes import ElectrodeType, MaterialType
from general.cell_operations import get_object_from_cell

from materials.callback_helpers import create_material_callback
from cache_service import cache



@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings
):

    callback_function = create_electrode_callback(ElectrodeType.CATHODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return response



@callback(
    [
        Output('cathode_top_down_plot', 'figure'),
        Output('cathode_cross_section_plot', 'figure'),
        Output('cathode_areal_capacity_plot', 'figure'),
        Output('cathode_capacity_plot', 'figure'),
        Output('cathode_properties_div', 'children'),
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
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.CATHODE]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    cathode = get_object_from_cell(cell, config)

    # get the plots from the current collector
    plot_a = cathode.get_top_down_view(title='Top-Down Cathode View')
    plot_b = cathode.get_cross_section(title='Cross-Section Cathode View')
    plot_areal_capacity = cathode.plot_half_cell_curve(areal=True, title='Areal Capacity Plot')
    plot_capacity = cathode.plot_half_cell_curve(areal=False, title='Capacity Plot')

    # Get the properties
    properties = cathode.properties

    # Create properties table using utility function
    properties_table = create_properties_table(properties, table_id='cathode_properties_table', decimal_places=2)

    return plot_a, plot_b, plot_areal_capacity, plot_capacity, properties_table


