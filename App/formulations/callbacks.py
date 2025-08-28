from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL, dash_table, clientside_callback

from App.cache_service import cache

from App.formulations.callback_helpers import create_generic_formulation_callback
from App.formulations.configs import FORMULATION_CONFIGS

from App.general.enumerated_classes import FormulationType
from App.general.cell_operations import get_object_from_cell
from App.general.callback_helpers import create_properties_table
from App.general.trigger_router import TriggerRouter, TriggerType


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
def update_cathode_formulation(
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
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode-active-material-div', 'children'),
        Output('cathode-binder-div', 'children'),
        Output('cathode-conductive-additive-div', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input('add-cathode-binder-button', 'n_clicks'),
        Input('remove-cathode-binder-button', 'n_clicks'),
        Input('add-cathode-conductive-additive-button', 'n_clicks'),
        Input('remove-cathode-conductive-additive-button', 'n_clicks'),
    ],
    [
        State('warnings_store', 'data'),
        State('cathode-binder-div', 'children'),
        State('cathode-conductive-additive-div', 'children'),
        State('cathode_active_material_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_formulation(
    cell_data,
    add_binder_clicks,
    remove_binder_clicks,
    add_conductive_clicks,
    remove_conductive_clicks,
    existing_warnings,
    binder_children,
    conductive_children,
    active_materials
):
    
    # Get the triggered ID
    triggered_id = ctx.triggered_id

    # get the configuration
    config = FORMULATION_CONFIGS[FormulationType.CATHODE]

    # get the cell from the cell store
    cell = cache.get(cell_data['cache_key'])

    # get the formulation
    formulation = get_object_from_cell(cell, config)

    # Create trigger router and process the trigger
    trigger_type = TriggerRouter.get_trigger_type(triggered_id)

    if trigger_type == TriggerType.CELL_STORE:
        from App.formulations.handlers import handle_cell_store_update_material_children
        return handle_cell_store_update_material_children(formulation, config, active_materials)


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

