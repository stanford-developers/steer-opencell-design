from dash import callback, Input, Output, ALL, State, ctx, no_update

from App.general.callback_helpers import create_properties_table

from App.electrodes.callback_helpers import create_electrode_callback
from App.electrodes.configs import ELECTRODE_CONFIGS

from App.current_collectors.configs import COLLECTOR_CONFIGS

from App.general.enumerated_classes import ElectrodeType, MaterialType, CollectorType
from App.general.cell_operations import get_object_from_cell, set_object_to_cell, set_cell_to_cache

from App.cache_service import cache

from steer_opencell_design.Components.Electrodes import ElectrodeControlMode


@callback(
    Output('cathode_insulation_material_parameters', 'style'),
    Input('cell_store', 'data'),
    State('cathode_insulation_material_parameters', 'style'),
    prevent_initial_call=True
)
def toggle_cathode_insulation_parameters(cell_data, current_style):

    # Get the configuration for cathode
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

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
    Output('anode_insulation_material_parameters', 'style'),
    Input('cell_store', 'data'),
    State('anode_insulation_material_parameters', 'style'),
    prevent_initial_call=True
)
def toggle_anode_insulation_parameters(cell_data, current_style):

    # Get the configuration for anode
    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

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
        Input('cathode_electrode_tab', 'style'),
        Input('cathode_tab', 'style'),
        Input('tabs_panel', 'style'),

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
    cc_tab_style,
    tab_style,
    tabs_panel_style,

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
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style]
    )
    
    return response

@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('anode_electrode_tab', 'style'),
        Input('anode_tab', 'style'),
        Input('tabs_panel', 'style'),

        Input('cell_store', 'data'),

        Input({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'anode', 'object': 'electrode', 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode(
    cc_tab_style,
    tab_style,
    tabs_panel_style,

    cell_data,
    
    input_n_sub,
    input_n_blur,
    slider_values,

    input_values,
    existing_warnings
):

    callback_function = create_electrode_callback(ElectrodeType.ANODE)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        viewing_styles=[cc_tab_style, tab_style, tabs_panel_style]
    )

    return response



@callback(
    [
        Output('cathode_top_down_plot', 'figure'),
        Output('cathode_cross_section_plot', 'figure'),
        Output('cathode_cost_breakdown_plot', 'figure'),
        Output('cathode_mass_breakdown_plot', 'figure'),
        Output('cathode_properties_div', 'children'),
    ],
    [
        Input('cathode_electrode_tab', 'style'),
        Input('cathode_current_collector_tab', 'style'),
        Input('cathode_tab', 'style'),
        Input('tabs_panel', 'style'),

        Input('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_plots(
    
    electrode_tab_style,
    cc_tab_style,
    tab_style,
    tabs_panel_style,

    cell_data, 
    ):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    # If all display is none for any of the viewing styles, return no update
    if any(d.get('display') == 'none' for d in [tab_style, tabs_panel_style]):
        return no_update, no_update, no_update, no_update, no_update
    
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.CATHODE]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    cathode = get_object_from_cell(cell, config)

    # Get the properties
    properties = cathode.properties

    # Only update if the electrode tab is visible
    if electrode_tab_style.get('display') == 'block':
        plot_b = cathode.get_cross_section(title='Cross-Section Cathode View')
        plot_cost_breakdown = cathode.plot_cost_breakdown(title='Cost Breakdown Plot')
        plot_mass_breakdown = cathode.plot_mass_breakdown(title='Mass Breakdown Plot')
        properties_table = create_properties_table(properties, table_id='cathode_properties_table', decimal_places=2)
        return no_update, plot_b, plot_cost_breakdown, plot_mass_breakdown, properties_table

    elif cc_tab_style.get('display') == 'block':
        plot_a = cathode.get_top_down_view(title='Top-Down Cathode View')
        return plot_a, no_update, no_update, no_update, no_update
    
    else:
        return no_update, no_update, no_update, no_update, no_update

@callback(
    [
        Output('anode_top_down_plot', 'figure'),
        Output('anode_cross_section_plot', 'figure'),
        Output('anode_cost_breakdown_plot', 'figure'),
        Output('anode_mass_breakdown_plot', 'figure'),
        Output('anode_properties_div', 'children'),
    ],
    [
        Input('anode_electrode_tab', 'style'),
        Input('anode_current_collector_tab', 'style'),
        Input('anode_tab', 'style'),
        Input('tabs_panel', 'style'),

        Input('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_plots(
    
    electrode_tab_style,
    cc_tab_style,
    tab_style,
    tabs_panel_style,

    cell_data, 
    ):
    """
    Update the anode current collector plots based on the current collector store data.
    """
    # If all display is none for any of the viewing styles, return no update
    if any(d.get('display') == 'none' for d in [tab_style, tabs_panel_style]):
        return no_update, no_update, no_update, no_update, no_update
    
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.ANODE]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    anode = get_object_from_cell(cell, config)

    # Get the properties
    properties = anode.properties

    # Only update if the electrode tab is visible
    if electrode_tab_style.get('display') == 'block':
        plot_b = anode.get_cross_section(title='Cross-Section Anode View')
        plot_cost_breakdown = anode.plot_cost_breakdown(title='Cost Breakdown Plot')
        plot_mass_breakdown = anode.plot_mass_breakdown(title='Mass Breakdown Plot')
        properties_table = create_properties_table(properties, table_id='anode_properties_table', decimal_places=2)
        return no_update, plot_b, plot_cost_breakdown, plot_mass_breakdown, properties_table

    elif cc_tab_style.get('display') == 'block':
        plot_a = anode.get_top_down_view(title='Top-Down Anode View')
        return plot_a, no_update, no_update, no_update, no_update
    
    else:
        return no_update, no_update, no_update, no_update, no_update



@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_control_mode_selector', 'value'),
    ],
    [
        Input('cathode_control_mode_selector', 'value'),
        Input('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_control_mode(selected_mode, cell_data):
    """
    Update the cathode control mode based on the radio button selection,
    and update the radio button to reflect the current control mode.
    """
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.CATHODE]

    # Get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # Get the cathode from the cell
    cathode = get_object_from_cell(cell, config)

    # get the mode map
    mode_mapping = {
        'MAINTAIN_MASS_LOADING': ElectrodeControlMode.MAINTAIN_MASS_LOADING,
        'MAINTAIN_CALENDER_DENSITY': ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY,
        'MAINTAIN_COATING_THICKNESS': ElectrodeControlMode.MAINTAIN_COATING_THICKNESS
    }

    # map the control mode to the UI string
    mode_reverse_mapping = {
        ElectrodeControlMode.MAINTAIN_MASS_LOADING: 'MAINTAIN_MASS_LOADING',
        ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: 'MAINTAIN_CALENDER_DENSITY',
        ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: 'MAINTAIN_COATING_THICKNESS'
    }

    if ctx.triggered_id == 'cell_store':
        return no_update, mode_reverse_mapping.get(cathode.control_mode, 'MAINTAIN_CALENDER_DENSITY')

    elif ctx.triggered_id == 'cathode_control_mode_selector':

        # get the control mode from the value
        mode = mode_mapping.get(selected_mode, ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY)

        # set the control mode to the cathode
        cathode.control_mode = mode

        # set the cathode to the cell
        new_cell = set_object_to_cell(cell, cathode, config)

        # set the new cell to the cache
        new_key = set_cell_to_cache(new_cell)

        return {'cache_key': new_key}, no_update

@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('anode_control_mode_selector', 'value'),
    ],
    [
        Input('anode_control_mode_selector', 'value'),
        Input('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_control_mode(selected_mode, cell_data):
    """
    Update the anode control mode based on the radio button selection,
    and update the radio button to reflect the current control mode.
    """
    # Get the configuration
    config = ELECTRODE_CONFIGS[ElectrodeType.ANODE]

    # Get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # Get the anode from the cell
    anode = get_object_from_cell(cell, config)

    # get the mode map
    mode_mapping = {
        'MAINTAIN_MASS_LOADING': ElectrodeControlMode.MAINTAIN_MASS_LOADING,
        'MAINTAIN_CALENDER_DENSITY': ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY,
        'MAINTAIN_COATING_THICKNESS': ElectrodeControlMode.MAINTAIN_COATING_THICKNESS
    }

    # map the control mode to the UI string
    mode_reverse_mapping = {
        ElectrodeControlMode.MAINTAIN_MASS_LOADING: 'MAINTAIN_MASS_LOADING',
        ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY: 'MAINTAIN_CALENDER_DENSITY',
        ElectrodeControlMode.MAINTAIN_COATING_THICKNESS: 'MAINTAIN_COATING_THICKNESS'
    }

    if ctx.triggered_id == 'cell_store':
        return no_update, mode_reverse_mapping.get(anode.control_mode, 'MAINTAIN_CALENDER_DENSITY')

    elif ctx.triggered_id == 'anode_control_mode_selector':

        # get the control mode from the value
        mode = mode_mapping.get(selected_mode, ElectrodeControlMode.MAINTAIN_CALENDER_DENSITY)

        # set the control mode to the anode
        anode.control_mode = mode

        # set the anode to the cell
        new_cell = set_object_to_cell(cell, anode, config)

        # set the new cell to the cache
        new_key = set_cell_to_cache(new_cell)

        return {'cache_key': new_key}, no_update


