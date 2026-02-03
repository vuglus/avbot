import sys
import os
import pytest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    return {
        'bot': {
            'whitelist': [12345, 67890],
            'admin_id': 12345,
            'welcome': 'Welcome to AVBot!'
        },
        'yandex': {
            'folder_id': 'test_folder_id',
            'oauth_token': 'test_token'
        },
        'speech': {
            'folder_id': 'test_folder_id',
            'oauth_token': 'test_token'
        }
    }


# Configure asyncio mode
@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == "win32" else asyncio.DefaultEventLoopPolicy()