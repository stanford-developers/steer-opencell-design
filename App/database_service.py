import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from steer_core.DataManager import DataManager

dm = DataManager()

FORM_FACTOR_OPTIONS = dm.get_data('cells')['form_factor'].unique().tolist()
CURRENT_COLLECTOR_MATERIALS = dm.get_current_collector_materials(most_recent=True)['name'].tolist()
INSULATION_MATERIALS = dm.get_insulation_materials(most_recent=True)['name'].tolist()
BINDER_MATERIALS = dm.get_binder_materials(most_recent=True)['name'].tolist()
CONDUCTIVE_ADDITIVE_MATERIALS = dm.get_conductive_additive_materials(most_recent=True)['name'].tolist()
SEPARATOR_MATERIALS = dm.get_separator_materials(most_recent=True)['name'].tolist()

