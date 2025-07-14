import dash as ds


@ds.callback(
    [ds.Output('cathode_cc', 'style'),
     ds.Output('anode_cc', 'style'),
     ds.Output('warnings', 'style')],
     ds.Input('tabs-container', 'value'),
    prevent_initial_call=True
)
def show_tab_content(active_tab):

    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    return [
        active_style if active_tab == 'cathode_cc' else styles,
        active_style if active_tab == 'anode_cc' else styles,
        active_style if active_tab == 'warnings' else styles,
    ]


