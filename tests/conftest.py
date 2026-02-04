import sys
import os
import pytest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.config_service import Config

# Add the clients directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clients')))

# Add the services directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))

# Add the handlers directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'handlers')))

# Configure asyncio mode for pytest-asyncio
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def test_data_dir(project_root):
    """Return the test data directory path"""
    return os.path.join(project_root, 'tests', 'data')

def mock_config():
    @pytest.fixture(scope="session", autouse=True)
    def config(self):
        """Create a test configuration"""
        return Config({
            'bot': {
                'whitelist': [12345, 67890],
                'admin_id': 12345,
                'welcome': 'Welcome to AVBot!'
            },
            'ycloud': {
                'folder_id': 'test_folder_id',
                'api_key': 'test_token'
            },
            'yandex': {
                'folder_id': 'test_folder_id',
                'oauth_token': 'test_token'
            }
        })
    import services.config_service
    services.config_service.config = config
    yield config

# Configure asyncio mode
@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == "win32" else asyncio.DefaultEventLoopPolicy()