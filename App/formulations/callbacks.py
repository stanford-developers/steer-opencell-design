from time import time
from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL, dash_table, clientside_callback

from App.cache_service import cache

from App.formulations.callback_helpers import create_generic_formulation_callback, create_generic_formulation_div_callback, create_generic_formulation_material_callback
from App.formulations.configs import FORMULATION_CONFIGS

from App.general.enumerated_classes import FormulationType
from App.general.cell_operations import get_object_from_cell
from App.general.callback_helpers import create_properties_table, create_no_update_response
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
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode-active-material-div', 'children'),
        Output('cathode-binder-div', 'children'),
        Output('cathode-conductive-additive-div', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'active_material'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'active_material'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'binder'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'binder'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'add', 'material': 'conductive_additive'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'action': 'remove', 'material': 'conductive_additive'}, 'n_clicks'),
    ],
    [
        State('warnings_store', 'data'),
        State('cathode-active-material-div', 'children'),
        State('cathode-binder-div', 'children'),
        State('cathode-conductive-additive-div', 'children')
    ],
    prevent_initial_call=True
)
def update_cathode_formulation_div(
    cell_data,
    add_active_clicks,
    remove_active_clicks,
    add_binder_clicks,
    remove_binder_clicks,
    add_conductive_clicks,
    remove_conductive_clicks,
    existing_warnings,
    active_children,
    binder_children,
    conductive_children
):

    callback_function = create_generic_formulation_div_callback(FormulationType.CATHODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        active_children,
        binder_children,
        conductive_children,
    )

    return response


@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),

        # active material outputs
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'step'),

        # binder outputs
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'step'),

        # conductive additive outputs
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        # active material inputs
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'subtype': 'dropdown'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'subtype': 'weight_fraction'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),

        # binder inputs
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'subtype': 'dropdown'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'subtype': 'weight_fraction'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),

        # conductive additive inputs
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'subtype': 'dropdown'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'subtype': 'weight_fraction'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State('cell_store', 'data'),
        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'active_material', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'binder', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'cathode', 'object': 'formulation', 'material': 'conductive_additive', 'index': ALL, 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_formulation_material_values(
    
    active_dropdown_values,
    active_weight_fractions,
    active_input_n_sub,
    active_input_n_blur,
    active_slider_values,

    binder_dropdown_values,
    binder_weight_fractions,
    binder_input_n_sub,
    binder_input_n_blur,
    binder_slider_values,

    conductive_dropdown_values,
    conductive_weight_fractions,
    conductive_input_n_sub,
    conductive_input_n_blur,
    conductive_slider_values,
    
    cell_data,
    active_input_values,
    binder_input_values,
    conductive_input_values,
    existing_warnings
):

    print("=========================================")
    print(f"DEBUG: triggered id {ctx.triggered_id}")
    
    print(f"DEBUG: active material dropdown values {active_dropdown_values}")
    print(f"DEBUG: active material weight fractions {active_weight_fractions}")
    print(f"DEBUG: active material slider values {active_slider_values}")
    print(f"DEBUG: active material input values {active_input_values}")

    print(f"DEBUG: binder material dropdown values {binder_dropdown_values}")
    print(f"DEBUG: binder material weight fractions {binder_weight_fractions}")
    print(f"DEBUG: binder material slider values {binder_slider_values}")
    print(f"DEBUG: binder material input values {binder_input_values}")

    print(f"DEBUG: conductive material dropdown values {conductive_dropdown_values}")
    print(f"DEBUG: conductive material weight fractions {conductive_weight_fractions}")
    print(f"DEBUG: conductive material slider values {conductive_slider_values}")
    print(f"DEBUG: conductive material input values {conductive_input_values}")
    print("=========================================")

    callback_function = create_generic_formulation_material_callback(FormulationType.CATHODE)

    response = callback_function(
        existing_warnings=existing_warnings,
        cell_data=cell_data,

        active_dropdown_values=active_dropdown_values,
        active_weight_fractions=active_weight_fractions,
        active_slider_values=active_slider_values,
        active_input_values=active_input_values,
        
        binder_dropdown_values=binder_dropdown_values,
        binder_weight_fractions=binder_weight_fractions,
        binder_slider_values=binder_slider_values,
        binder_input_values=binder_input_values,
        
        conductive_dropdown_values=conductive_dropdown_values,
        conductive_weight_fractions=conductive_weight_fractions,
        conductive_slider_values=conductive_slider_values,
        conductive_input_values=conductive_input_values
    )

    return response


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

