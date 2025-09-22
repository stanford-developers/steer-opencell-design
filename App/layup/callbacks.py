from dash import no_update, Input, Output, State, callback, ALL

from App.cache_service import cache

from App.general.enumerated_classes import LayupType
from App.general.cell_operations import get_object_from_cell
from App.layup.configs import LAYUP_CONFIGS


@callback(
    [
        Output('layup_plot', 'figure'),
    ],
    [
        Input('layup_tab', 'style'),
        Input('tabs_panel', 'style'),

        Input('cell_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_layup_plots(
    
    tab_style,
    tabs_panel_style,

    cell_data, 
    ):
    """
    Update the cathode current collector plots based on the current collector store data.
    """

    # If all display is none for any of the viewing styles, return no update
    if any(d.get('display') == 'none' for d in [tab_style, tabs_panel_style]):
        return no_update
    
    # Get the configuration
    config = LAYUP_CONFIGS[LayupType.GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    layup = get_object_from_cell(cell, config)

    # get the figure
    fig = layup.get_top_down_view()
    
    return (fig, )

