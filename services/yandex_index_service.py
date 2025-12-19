import os
import logging
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    HybridSearchIndexType,
    StaticIndexChunkingStrategy,
    VectorSearchIndexType,
    ReciprocalRankFusionIndexCombinationStrategy
)

logger = logging.getLogger(__name__)

class YandexIndexService:
    def __init__(self, sdk: YCloudML, folder_id: str):
        self.sdk = sdk
        self.folder_id = folder_id

    def _get_or_create_index(self, index_name: str, files) -> str:
        """
        Возвращает index_id, создаёт индекс при отсутствии
        """
        
        index_id = self._get_index_id_by_name(index_name)

        if index_id: 
            return index_id
        
        # Если индекс не найден, создаём новый
        logger.info(f"Search index '{index_name}' not found. Creating new one...")
        
        # Prepare parameters for index creation
        create_params = {
            "name": index_name,
            "index_type": HybridSearchIndexType(
                chunking_strategy=StaticIndexChunkingStrategy(
                    max_chunk_size_tokens=700,
                    chunk_overlap_tokens=300
                ),
                vector_search_index=VectorSearchIndexType(
                    doc_embedder_uri=f"emb://{self.folder_id}/text-search-doc/latest",
                    query_embedder_uri=f"emb://{self.folder_id}/text-search-query/latest"
                ),
                normalization_strategy="L2",
                combination_strategy=ReciprocalRankFusionIndexCombinationStrategy(
                    k=60
                )
            ),
            "files": files
        }

        operation = self.sdk.search_indexes.create_deferred(**create_params)
        
        # Дожидаемся создания
        result = operation.wait()
        index_id = result.id
        
        logger.info(f"Created search index: {index_id}")
        
        return index_id

    def _add_files_to_index(self, index, files):
        """
        Добавляет файлы в существующий индекс
        """
        try:
            logger.info(f"Adding {len(files)} files to existing index {index.id}")

            operation = index.add_files_deferred(files=files)
            operation.wait()

            logger.info(f"Successfully added {len(files)} files to index {index.id}")

        except Exception as e:
            logger.error(f"Error adding files to index: {e}")
            raise

    def upload_file_to_index(self, file_path: str, file_name: str, index_name: str = None):
        """
        Загружает файл и добавляет в индекс
        """

        # First upload the file
        logger.info(f"Uploading file to Yandex Cloud: {file_path}")
        yc_file = self.sdk.files.upload(file_path, name=file_name)
        logger.info(f"Uploaded file to Yandex Cloud: {yc_file!r}")
        
        # Check if index exists
        index = self.get_index_by_name(index_name)

        if index:
            # If index exists, add file to existing index
            logger.info(f"Adding file to existing index: {index.name}")
            self._add_files_to_index(index, [yc_file])
            # Return the existing index ID
            return index.id
        else:
            # If index doesn't exist, create new index with the file
            logger.info(f"Creating new index with file: {file_name}")
            index_id = self._get_or_create_index(index_name, files=[yc_file])
        
        return index_id
    def get_index_by_name(self, index_name: str) :
        """
        Get or create index ID for a specific user
        """
        # Проверяем, существует ли индекс с таким именем
        try:
            # Получаем список индексов
            indexes = self.sdk.search_indexes.list()

            # Ищем индекс с заданным именем
            for index in indexes:
                if index.name == index_name:
                    logger.info(f"Found existing search index: {index.id}")
                    return index
        except Exception as e:
            logger.warning(f"Error while listing indexes: {e}")        

        return None
    
    def _get_index_id_by_name(self, index_name: str) -> int:
        index = self.get_index_by_name(index_name)
        if index:
            return index.id
        return None
    
    def get_index_name(self, user_id: int, topic_name: str) -> str:
        return f"avbot_index_{user_id}_{topic_name}"

    def get_index_id_for_topic(self, user_id: int, topic_name: str) -> str:
        """
        Get or create index ID for a specific topic
        """
        index_name = self.get_index_name(user_id, topic_name)
        index = self.get_index_by_name(index_name)

        if index: 
            return index.id
        
        return None

