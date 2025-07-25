from OpenCell.DataManager import DataManager
from pathlib import Path

# get current collector materials from the database
CURRENT_DIR = Path(__file__).resolve().parent
DATA_PATH = CURRENT_DIR / '..' / 'Data' / 'database.db'
dm = DataManager(DATA_PATH)

FORM_FACTOR_OPTIONS = dm.get_data('cells')['form_factor'].unique().tolist()
CURRENT_COLLECTOR_MATERIALS = dm.get_current_collector_materials(most_recent=True)['name'].tolist()
