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

INDEX_NAME = "telegram-documents-index"

class YandexIndexService:
    def __init__(self, sdk: YCloudML, folder_id: str):
        self.sdk = sdk
        self.folder_id = folder_id

    def get_or_create_index(self) -> str:
        """
        Возвращает index_id, создаёт индекс при отсутствии
        """

        # 1. Проверяем сохранённый ID
        index_id = os.getenv("YC_SEARCH_INDEX_ID")
        if index_id:
            logger.info(f"Using existing search index: {index_id}")
            return index_id

        # 2. Иначе создаём новый индекс
        logger.info("Search index not found. Creating new one...")

        operation = self.sdk.search_indexes.create_deferred(
            name=INDEX_NAME,
            index_type=HybridSearchIndexType(
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
            )
        )

        # 3. Дожидаемся создания
        result = operation.wait()
        index_id = result.id

        logger.info(f"Created search index: {index_id}")

        # 4. Сохраняем (пример через env)
        os.environ["YC_SEARCH_INDEX_ID"] = index_id

        return index_id

    def upload_file_to_index(self, file_path: str):
        """
        Загружает файл и добавляет в индекс
        """

        index_id = self.get_or_create_index()

        logger.info(f"Uploading file to Yandex Cloud: {file_path}")
        yc_file = self.sdk.files.upload(file_path)

        logger.info(f"Adding file to index {index_id}")
        self.sdk.search_indexes.add_files(
            index_id=index_id,
            files=[yc_file]
        )
