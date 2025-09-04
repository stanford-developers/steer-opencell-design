from time import time
from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL, dash_table, clientside_callback

from App.cache_service import cache

from App.formulations.callback_helpers import create_generic_formulation_callback, create_generic_formulation_div_callback
from App.formulations.configs import FORMULATION_CONFIGS

from App.general.enumerated_classes import FormulationType
from App.general.cell_operations import get_object_from_cell
from App.general.callback_helpers import create_properties_table, create_success_message, create_error_message, create_no_update_response

from App.materials.configs import MaterialType, MATERIAL_CONFIGS, MaterialConfig


@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'formulation', 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_formulation_main(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings
):

    callback_function = create_generic_formulation_callback(
        FormulationType.CATHODE
    )

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return response


@callback(
    [   
        Output('cathode_formulation_message', 'children'),
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),

        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL}, 'style'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'subtype': 'dropdown'}, 'options'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'subtype': 'dropdown'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'subtype': 'weight_fraction'}, 'value'),

        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': ALL, 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'step'),

    ],
    [
        Input('cell_store', 'data'),


        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'active_material'}, 'n_clicks'),
        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'active_material'}, 'n_clicks'),
        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'binder'}, 'n_clicks'),
        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'binder'}, 'n_clicks'),
        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'conductive_additive'}, 'n_clicks'),
        # Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'conductive_additive'}, 'n_clicks'),
    ],
    [
        State('warnings_store', 'data'),

        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL}, 'style'),
        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL}, 'style'),
        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL}, 'style'),

        State('cathode_active_material_store', 'data'),
        State('anode_active_material_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_formulation_div(
    cell_data,
    # add_active_clicks,
    # remove_active_clicks,
    # add_binder_clicks,
    # remove_binder_clicks,
    # add_conductive_clicks,
    # remove_conductive_clicks,
    existing_warnings,
    active_div_styles,
    binder_div_styles,
    conductive_div_styles,
    cathode_material_options,
    anode_material_options
):

    try:

        callback_function = create_generic_formulation_div_callback(FormulationType.CATHODE)

        response = callback_function(
            existing_warnings,
            cell_data,
            active_div_styles,
            binder_div_styles,
            conductive_div_styles,
            cathode_material_options,
            anode_material_options
        )

        message_div = create_success_message('Cathode formulation updated successfully')

    except Exception as e:
        
        print(f"Exception in update_cathode_formulation_div: {e}")
        import traceback
        traceback.print_exc()

        div_style_response = (
            [no_update for _ in active_div_styles] +
            [no_update for _ in binder_div_styles] +
            [no_update for _ in conductive_div_styles]
        )

        dropdown_options_response = (
            [no_update for _ in active_div_styles] +
            [no_update for _ in binder_div_styles] +
            [no_update for _ in conductive_div_styles]
        )

        dropdown_value_response = (
            [no_update for _ in active_div_styles] +
            [no_update for _ in binder_div_styles] +
            [no_update for _ in conductive_div_styles]
        )

        weight_fraction_response = (
            [no_update for _ in active_div_styles] +
            [no_update for _ in binder_div_styles] +
            [no_update for _ in conductive_div_styles]
        )

        response = (
            no_update, 
            no_update,
            div_style_response,
            dropdown_options_response,
            dropdown_value_response,
            weight_fraction_response,
            [no_update for _ in range(0, 28)],
            [no_update for _ in range(0, 28)],
            [no_update for _ in range(0, 28)],
            [no_update for _ in range(0, 28)],
            [no_update for _ in range(0, 28)],
            [no_update for _ in range(0, 28)],
        ) 

        # Convert exception to string for JSON serialization
        message_div = create_error_message(f"Error updating cathode formulation: {str(e)}")

    return (message_div, ) + response



@callback(
    [
        Output('cathode_formulation_specific_capacity_plot', 'figure'),
        Output('cathode_formulation_specific_cost_breakdown_plot', 'figure'),
        Output('cathode_formulation_density_breakdown_plot', 'figure'),
        Output('cathode_formulation_properties_div', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input('continue_to_design', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_cathode_formulation_plots(cell_data, continue_to_design):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    # Get the configuration
    config = FORMULATION_CONFIGS[FormulationType.CATHODE]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    formulation = get_object_from_cell(cell, config)

    # get the plots from the current collector
    plot_a = formulation.plot_half_cell_curve(add_materials=True)
    plot_b = formulation.plot_specific_cost_breakdown()
    plot_c = formulation.plot_density_breakdown()

    # Get the properties
    properties = formulation.properties

    # Create properties table using utility function
    properties_table = create_properties_table(properties, table_id='cathode_properties_table', decimal_places=2)

    return plot_a, plot_b, plot_c, properties_table

