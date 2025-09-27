"""Qdrant vector database service with clean interface"""
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import numpy as np


class VectorDatabaseInterface(ABC):
    """Abstract interface for vector database operations"""

    @abstractmethod
    def ensure_collection(self, collection_name: str, vector_size: int) -> bool:
        """Ensure collection exists with given vector size"""
        pass

    @abstractmethod
    def upsert_vectors(self, collection_name: str, points: List[PointStruct]) -> bool:
        """Upsert vector points to collection"""
        pass

    @abstractmethod
    def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of collections with metadata"""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection"""
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        pass


class QdrantService(VectorDatabaseInterface):
    """Qdrant vector database service implementation"""

    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self._client: Optional[QdrantClient] = None

    def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port, api_key=self.api_key)
        return self._client

    def ensure_collection(self, collection_name: str, vector_size: int) -> bool:
        """Ensure collection exists with given vector size"""
        try:
            client = self._get_client()
            existing_collections = [c.name for c in client.get_collections().collections]

            if collection_name not in existing_collections:
                client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                return True  # Created new collection

            return False  # Collection already exists
        except Exception as e:
            raise VectorDatabaseError(f"Failed to ensure collection: {e}")

    def upsert_vectors(self, collection_name: str, points: List[PointStruct]) -> bool:
        """Upsert vector points to collection"""
        try:
            client = self._get_client()
            client.upsert(collection_name=collection_name, points=points)
            return True
        except Exception as e:
            raise VectorDatabaseError(f"Failed to upsert vectors: {e}")

    def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of collections with metadata"""
        try:
            client = self._get_client()
            collections_info = client.get_collections()

            collections = []
            for coll in collections_info.collections:
                try:
                    coll_info = client.get_collection(coll.name)
                    count = client.count(coll.name)
                    collections.append({
                        "name": coll.name,
                        "vector_size": coll_info.config.params.vectors.size,
                        "distance": coll_info.config.params.vectors.distance.value,
                        "count": count.count if count else 0,
                        "status": coll_info.status.value
                    })
                except Exception:
                    collections.append({
                        "name": coll.name,
                        "vector_size": "N/A",
                        "distance": "N/A",
                        "count": "N/A",
                        "status": "Error"
                    })

            return collections
        except Exception as e:
            raise VectorDatabaseError(f"Failed to get collections: {e}")

    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection"""
        try:
            client = self._get_client()
            client.delete_collection(collection_name)
            return True
        except Exception as e:
            raise VectorDatabaseError(f"Failed to delete collection: {e}")

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        try:
            client = self._get_client()
            collections = [c.name for c in client.get_collections().collections]

            if collection_name in collections:
                coll_info = client.get_collection(collection_name)
                count = client.count(collection_name)
                return {
                    "name": collection_name,
                    "vector_size": coll_info.config.params.vectors.size,
                    "distance": coll_info.config.params.vectors.distance.value,
                    "count": count.count if count else 0,
                    "status": coll_info.status.value
                }
            return None
        except Exception:
            return None

    def test_connection(self) -> bool:
        """Test Qdrant connection"""
        try:
            client = self._get_client()
            client.get_collections()
            return True
        except Exception:
            return False


class VectorProcessor:
    """Vector processing utilities"""

    @staticmethod
    def create_point_id(pk_value: Any, chunk_index: int) -> int:
        """Create deterministic point ID from PK and chunk index"""
        pk_str = str(pk_value)
        id_string = f"{pk_str}::{chunk_index}"
        hash_bytes = hashlib.sha256(id_string.encode("utf-8")).digest()
        return int.from_bytes(hash_bytes[:8], "big") & ((1 << 64) - 1)

    @staticmethod
    def create_point_struct(
        pk_value: Any,
        chunk_index: int,
        row_index: int,
        text: str,
        vector: np.ndarray,
        source_row: Dict[str, Any]
    ) -> PointStruct:
        """Create PointStruct for Qdrant"""
        point_id = VectorProcessor.create_point_id(pk_value, chunk_index)

        return PointStruct(
            id=point_id,
            vector=vector.tolist(),
            payload={
                "text": text,
                "pk": pk_value,
                "chunk_index": chunk_index,
                "row_index": row_index,
                "source_row": source_row
            }
        )


class BatchProcessor:
    """Batch processing for large datasets"""

    def __init__(self, qdrant_service: QdrantService, batch_size: int = 64):
        self.qdrant_service = qdrant_service
        self.batch_size = batch_size

    def process_batches(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        embeddings: np.ndarray,
        progress_callback: Optional[callable] = None
    ) -> Tuple[int, float]:
        """Process documents in batches and return (total_processed, elapsed_time)"""
        total = len(documents)
        processed = 0
        start_time = time.time()

        for i in range(0, total, self.batch_size):
            batch_docs = documents[i:i + self.batch_size]
            batch_embeddings = embeddings[i:i + self.batch_size]

            # Create points for this batch
            points = []
            for doc, embedding in zip(batch_docs, batch_embeddings):
                point = VectorProcessor.create_point_struct(
                    pk_value=doc["pk"],
                    chunk_index=doc["chunk_index"],
                    row_index=doc["row_index"],
                    text=doc["text"],
                    vector=embedding,
                    source_row=doc.get("source_row", {})
                )
                points.append(point)

            # Upsert batch
            self.qdrant_service.upsert_vectors(collection_name, points)
            processed += len(batch_docs)

            # Call progress callback if provided
            if progress_callback:
                progress_callback(processed, total, time.time() - start_time)

        elapsed_time = time.time() - start_time
        print(f"[DEBUG] BatchProcessor - start_time: {start_time}, end_time: {time.time()}, elapsed: {elapsed_time}")
        return processed, elapsed_time


class VectorDatabaseError(Exception):
    """Vector database operation error"""
    pass


class QdrantServiceFactory:
    """Factory for creating Qdrant services"""

    @staticmethod
    def create_service(host: str, port: int, api_key: Optional[str] = None) -> VectorDatabaseInterface:
        """Create Qdrant service instance"""
        return QdrantService(host, port, api_key)