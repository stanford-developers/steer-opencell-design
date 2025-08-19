from dash import callback, Input, Output, ALL, State, ctx

from general.callback_helpers import create_properties_table

from electrodes.callback_helpers import create_electrode_callback
from electrodes.configs import ELECTRODE_CONFIGS

from current_collectors.configs import COLLECTOR_CONFIGS

from general.enumerated_classes import ElectrodeType, MaterialType, CollectorType
from general.cell_operations import get_object_from_cell

from cache_service import cache

from steer_opencell_design.Components.Electrodes import ElectrodeControlMode


@callback(
    Output('cathode_insulation_material_parameters', 'style'),
    Input('cell_store', 'data'),
    State('cathode_insulation_material_parameters', 'style'),
    prevent_initial_call=True
)
def toggle_cathode_insulation_parameters(cell_data, current_style):

    # Get the configuration for cathode
    config = COLLECTOR_CONFIGS[CollectorType.GENERIC]

    # Get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # Get the current collector object
    current_collector = get_object_from_cell(cell, config)
    
    # Ensure current_style is a dict
    if current_style is None:
        current_style = {}

    # Show if insulation_area > 0, else hide
    if hasattr(current_collector, 'insulation_area') and current_collector.insulation_area > 0:
        # Remove 'display' if present, or set to 'block'
        style = dict(current_style)
        style.pop('display', None)
        return style
    else:
        # Set 'display' to 'none'
        style = dict(current_style)
        style['display'] = 'none'
        return style



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



@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_control_mode_selector', 'value'),
    ],
    [
        Input('cathode_control_mode_selector', 'value'),
        Input('cell_store', 'data'),
    ],
    [
        State('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_control_mode(selected_mode, cell_data_input, cell_data_state):
    """
    Update the cathode control mode based on the radio button selection,
    and update the radio button to reflect the current control mode.
    """
    from dash import ctx
    
    # Use the most recent cell_data
    cell_data = cell_data_input or cell_data_state
    
    if not cell_data:
        return cell_data, 'MAINTAIN_CALENDER_DENSITY'
    
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.CATHODE]
    
    # Get the cell from the cache
    cell = cache.get(cell_data['cache_key'])
    
    if not cell:
        return cell_data, 'MAINTAIN_CALENDER_DENSITY'
    
    # Get the cathode from the cell
    cathode = get_object_from_cell(cell, config)
    
    # Check which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    if 'cathode_control_mode_selector' in str(triggered_id):
        # Radio button was changed - update the electrode
        mode_mapping = {
            'MAINTAIN_MASS_LOADING': ElectrodeControlMode.MAINTAIN_MASS_LOADING,
            'MAINTAIN_CALENDER_DENSITY': ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY,
            'MAINTAIN_COATING_THICKNESS': ElectrodeControlMode.MAINTAIN_COATING_THICKNESS
        }
        
        # Set the control mode if valid
        if selected_mode in mode_mapping:
            cathode.control_mode = mode_mapping[selected_mode]

            # Update the cache with the modified cell
            cache.set(cell_data['cache_key'], cell)
        
        return cell_data, selected_mode
    
    else:
        # Cell data was updated - sync the radio button with electrode state
        current_mode = cathode.control_mode
        
        # Map the enum value back to the UI string
        mode_reverse_mapping = {
            ElectrodeControlMode.MAINTAIN_MASS_LOADING: 'MAINTAIN_MASS_LOADING',
            ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: 'MAINTAIN_CALENDER_DENSITY',
            ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: 'MAINTAIN_COATING_THICKNESS'
        }
        
        ui_mode = mode_reverse_mapping.get(current_mode, 'MAINTAIN_CALENDER_DENSITY')
        
        return cell_data, ui_mode


