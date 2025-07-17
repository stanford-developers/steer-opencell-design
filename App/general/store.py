import dash as ds

cell_store = ds.dcc.Store(
    id = 'cell_store',
    data = {'cache_key': None}
)

cathode_current_collector_material_store = ds.dcc.Store(
    id='cathode_current_collector_material_store',
    data={'cache_key': None}
)

cathode_current_collector_store = ds.dcc.Store(
    data={'cache_key': None}, 
    id='cathode_current_collector_store'
)
