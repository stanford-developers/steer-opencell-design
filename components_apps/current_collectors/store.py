# import dash as ds
# from uuid import uuid4

# from cache_service import cache

# from styles import *
# from SteerEnergyStorage.Materials.CurrentCollectors import *
# from SteerEnergyStorage.Materials.RawMaterials import *
# from pathlib import Path
# from SteerEnergyStorage.DataManager import DataManager

# # get current collector materials from the database
# CURRENT_DIR = Path(__file__).resolve().parent
# DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
# dm = DataManager(DATA_PATH)

# # Get default cathode cc material
# cathode_current_collector_material = CurrentCollectorMaterial.from_database('Aluminum')

# # store default material in cache
# cache_key = str(uuid4())
# cache.set(cache_key, cathode_current_collector_material)
# cathode_current_collector_material_store = ds.dcc.Store(
#     data={'cache_key': cache_key}, 
#     id='cathode_current_collector_material_store'
# )

# # get default anode cc material
# anode_current_collector_material = CurrentCollectorMaterial.from_database('Copper')

# # store default material in cache
# cache_key = str(uuid4())
# cache.set(cache_key, anode_current_collector_material)
# anode_current_collector_material_store = ds.dcc.Store(
#     data={'cache_key': cache_key},
#     id='anode_current_collector_material_store'
# )


# # get default cathode cc
# default_cathode_current_collector = PunchedCurrentCollector(
#     material=cathode_current_collector_material,
#     width=280,
#     height=220,
#     thickness=12,
#     tab_width=30,
#     tab_height=20,
#     tab_position=50,
#     coated_tab_height=3,
#     insulation_width=8
# )

# # store cc in cache
# cache_key = str(uuid4())
# cache.set(cache_key, default_cathode_current_collector)

# # store the key in dcc.Store component
# cathode_current_collector_store = ds.dcc.Store(
#     data={'cache_key': cache_key}, 
#     id='cathode_current_collector_store'
# )


# # get default anode cc
# default_anode_current_collector = PunchedCurrentCollector(
#     material=anode_current_collector_material,
#     width=284,
#     height=224,
#     thickness=8,
#     tab_width=30,
#     tab_height=20,
#     tab_position=174,
#     coated_tab_height=3,
#     insulation_width=8
# )

# # store cc in cache
# cache_key = str(uuid4())
# cache.set(cache_key, default_anode_current_collector)

# anode_current_collector_store = ds.dcc.Store(
#     data={'cache_key': cache_key},
#     id='anode_current_collector_store'
# )
