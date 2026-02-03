import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.yandex_index_service import YandexIndexService
from yandex_cloud_ml_sdk import YCloudML


class TestYandexIndexService:
    """Test suite for YandexIndexService class"""

    @pytest.fixture
    def mock_sdk(self):
        """Create a mock Yandex Cloud SDK"""
        mock = Mock(spec=YCloudML)
        mock.search_indexes = Mock()
        mock.files = Mock()
        return mock
        return Mock(spec=YCloudML)

    @pytest.fixture
    def index_service(self, mock_sdk):
        """Create an instance of YandexIndexService with mock SDK"""
        return YandexIndexService(mock_sdk, "test_folder_id")

    def test_init(self, mock_sdk):
        """Test initialization of YandexIndexService"""
        service = YandexIndexService(mock_sdk, "test_folder_id")
        assert service.sdk == mock_sdk
        assert service.folder_id == "test_folder_id"

    def test_get_index_name(self, index_service):
        """Test get_index_name method"""
        user_id = 12345
        topic_name = "test_topic"
        expected_name = "avbot_index_12345_test_topic"
        assert index_service.get_index_name(user_id, topic_name) == expected_name

    @patch('services.yandex_index_service.logger')
    def test_get_index_by_name_found(self, mock_logger, index_service):
        """Test get_index_by_name when index is found"""
        # Create mock index
        mock_index = Mock()
        mock_index.name = "test_index"
        mock_index.id = "test_index_id"
        
        # Mock the list method to return our mock index
        index_service.sdk.search_indexes.list.return_value = [mock_index]
        
        result = index_service.get_index_by_name("test_index")
        assert result == mock_index
        mock_logger.info.assert_called_with("Found existing search index: test_index_id")

    @patch('services.yandex_index_service.logger')
    def test_get_index_by_name_not_found(self, mock_logger, index_service):
        """Test get_index_by_name when index is not found"""
        # Mock the list method to return an empty list
        index_service.sdk.search_indexes.list.return_value = []
        
        result = index_service.get_index_by_name("nonexistent_index")
        assert result is None

    @patch('services.yandex_index_service.logger')
    def test_get_index_by_name_exception(self, mock_logger, index_service):
        """Test get_index_by_name when an exception occurs"""
        # Mock the list method to raise an exception
        index_service.sdk.search_indexes.list.side_effect = Exception("API Error")
        
        result = index_service.get_index_by_name("test_index")
        assert result is None
        mock_logger.warning.assert_called_with("Error while listing indexes: API Error")

    @patch('services.yandex_index_service.logger')
    def test__get_index_id_by_name(self, mock_logger, index_service):
        """Test _get_index_id_by_name method"""
        # Create mock index
        mock_index = Mock()
        mock_index.name = "test_index"
        mock_index.id = "test_index_id"
        
        # Mock the get_index_by_name method
        index_service.get_index_by_name = Mock(return_value=mock_index)
        
        result = index_service._get_index_id_by_name("test_index")
        assert result == "test_index_id"

    def test__get_index_id_by_name_not_found(self, index_service):
        """Test _get_index_id_by_name when index is not found"""
        # Mock the get_index_by_name method to return None
        index_service.get_index_by_name = Mock(return_value=None)
        
        result = index_service._get_index_id_by_name("nonexistent_index")
        assert result is None

    @patch('services.yandex_index_service.logger')
    def test__add_files_to_index_success(self, mock_logger, index_service):
        """Test _add_files_to_index method success case"""
        # Create mock index and files
        mock_index = Mock()
        mock_index.id = "test_index_id"
        mock_files = [Mock()]
        
        # Mock the add_files_deferred method
        mock_operation = Mock()
        mock_index.add_files_deferred.return_value = mock_operation
        mock_operation.wait.return_value = None
        
        index_service._add_files_to_index(mock_index, mock_files)
        
        # Verify the methods were called
        mock_index.add_files_deferred.assert_called_with(files=mock_files)
        mock_operation.wait.assert_called_once()
        mock_logger.info.assert_any_call("Adding 1 files to existing index test_index_id")
        mock_logger.info.assert_any_call("Successfully added 1 files to index test_index_id")

    @patch('services.yandex_index_service.logger')
    def test__add_files_to_index_exception(self, mock_logger, index_service):
        """Test _add_files_to_index method when an exception occurs"""
        # Create mock index and files
        mock_index = Mock()
        mock_index.id = "test_index_id"
        mock_files = [Mock()]
        
        # Mock the add_files_deferred method to raise an exception
        mock_index.add_files_deferred.side_effect = Exception("Add files error")
        
        with pytest.raises(Exception, match="Add files error"):
            index_service._add_files_to_index(mock_index, mock_files)
        
        mock_logger.error.assert_called_with("Error adding files to index: Add files error")

    @patch('services.yandex_index_service.logger')
    def test_upload_file_to_index_existing_index(self, mock_logger, index_service):
        """Test upload_file_to_index when index exists"""
        # Create mock file and index
        mock_yc_file = Mock()
        mock_index = Mock()
        mock_index.id = "existing_index_id"
        mock_index.name = "existing_index"
        
        # Mock the SDK files upload method
        index_service.sdk.files.upload.return_value = mock_yc_file
        
        # Mock the get_index_by_name method
        index_service.get_index_by_name = Mock(return_value=mock_index)
        
        # Mock the _add_files_to_index method
        index_service._add_files_to_index = Mock()
        
        result = index_service.upload_file_to_index("test_path.txt", "test_file.txt", "existing_index")
        
        # Verify the methods were called correctly
        index_service.sdk.files.upload.assert_called_with("test_path.txt", name="test_file.txt")
        index_service.get_index_by_name.assert_called_with("existing_index")
        index_service._add_files_to_index.assert_called_with(mock_index, [mock_yc_file])
        assert result == "existing_index_id"

    @patch('services.yandex_index_service.logger')
    def test_upload_file_to_index_new_index(self, mock_logger, index_service):
        """Test upload_file_to_index when index doesn't exist"""
        # Create mock file
        mock_yc_file = Mock()
        
        # Mock the SDK files upload method
        index_service.sdk.files.upload.return_value = mock_yc_file
        
        # Mock the get_index_by_name method to return None (index doesn't exist)
        index_service.get_index_by_name = Mock(return_value=None)
        
        # Mock the _get_or_create_index method
        index_service._get_or_create_index = Mock(return_value="new_index_id")
        
        result = index_service.upload_file_to_index("test_path.txt", "test_file.txt", "new_index")
        
        # Verify the methods were called correctly
        index_service.sdk.files.upload.assert_called_with("test_path.txt", name="test_file.txt")
        index_service.get_index_by_name.assert_called_with("new_index")
        index_service._get_or_create_index.assert_called_with("new_index", files=[mock_yc_file])
        assert result == "new_index_id"

    @patch('services.yandex_index_service.logger')
    def test__get_or_create_index_existing(self, mock_logger, index_service):
        """Test _get_or_create_index when index exists"""
        # Mock the _get_index_id_by_name method to return an existing ID
        index_service._get_index_id_by_name = Mock(return_value="existing_index_id")
        
        result = index_service._get_or_create_index("existing_index", [])
        
        assert result == "existing_index_id"
        index_service._get_index_id_by_name.assert_called_with("existing_index")

    @patch('services.yandex_index_service.logger')
    def test__get_or_create_index_new(self, mock_logger, index_service):
        """Test _get_or_create_index when index doesn't exist"""
        # Mock the _get_index_id_by_name method to return None (index doesn't exist)
        index_service._get_index_id_by_name = Mock(return_value=None)
        
        # Mock the SDK search_indexes.create_deferred method
        mock_operation = Mock()
        mock_operation.wait.return_value = Mock(id="new_index_id")
        index_service.sdk.search_indexes.create_deferred.return_value = mock_operation
        
        result = index_service._get_or_create_index("new_index", [])
        
        assert result == "new_index_id"
        index_service._get_index_id_by_name.assert_called_with("new_index")
        index_service.sdk.search_indexes.create_deferred.assert_called_once()
        mock_operation.wait.assert_called_once()
        mock_logger.info.assert_any_call("Search index 'new_index' not found. Creating new one...")
        mock_logger.info.assert_any_call("Created search index: new_index_id")

    @patch('services.yandex_index_service.logger')
    def test_get_index_id_for_topic_existing(self, mock_logger, index_service):
        """Test get_index_id_for_topic when index exists"""
        # Create mock index
        mock_index = Mock()
        mock_index.id = "topic_index_id"
        
        # Mock the get_index_by_name method
        index_service.get_index_by_name = Mock(return_value=mock_index)
        
        # Mock the set_topic_index function from dialog_service
        with patch('services.yandex_index_service.set_topic_index') as mock_set_topic_index:
            result = index_service.get_index_id_for_topic(12345, "test_topic")
            
            assert result == "topic_index_id"
            index_service.get_index_by_name.assert_called_with("avbot_index_12345_test_topic")
            mock_set_topic_index.assert_called_with(12345, "test_topic", "topic_index_id")

    def test_get_index_id_for_topic_not_found(self, index_service):
        """Test get_index_id_for_topic when index doesn't exist"""
        # Mock the get_index_by_name method to return None
        index_service.get_index_by_name = Mock(return_value=None)
        
        result = index_service.get_index_id_for_topic(12345, "nonexistent_topic")
        
        assert result is None
        index_service.get_index_by_name.assert_called_with("avbot_index_12345_nonexistent_topic")