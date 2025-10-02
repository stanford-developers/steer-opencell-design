import dash as ds

LANDING_PAGE_IMAGE_URLS = {
    "Pouch": "assets/Pouch.png",
    "Prismatic": "assets/Prismatic.png",
    "Cylindrical": "assets/Cylindrical.png",
    "Stacked": "assets/Stacked.png",
    "Wound": "assets/Wound.png",
    "Flat Wound": "assets/Flat Wound.png",
    "Na/Na+": "assets/NaNa+.png",
    "Li/Li+": "assets/LiLi+.png",
    "Zn/Zn2+": "assets/ZnZn2+.png",
}

cell_store = ds.dcc.Store(id="cell_store", data={"cache_key": None})
old_cell_store = ds.dcc.Store(id="old_cell_store", data={"cache_key": None})

warnings_store = ds.dcc.Store(id="warnings_store", data=[])

cathode_active_material_store = ds.dcc.Store(id="cathode_active_material_store", data=[])

anode_active_material_store = ds.dcc.Store(id="anode_active_material_store", data=[])
