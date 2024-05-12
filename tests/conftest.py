from tests.units import fixtures
from tests.units.fixtures._load_fixtures import get_sub_modules

# Load fixtures dynamically
pytest_plugins = [*get_sub_modules(fixtures)]
