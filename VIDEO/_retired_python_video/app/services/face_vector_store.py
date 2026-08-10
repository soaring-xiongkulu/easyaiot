"""Milvus 人脸向量存储"""
import logging
import os
import threading
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
    _PYMILVUS_IMPORT_ERROR: Optional[Exception] = None
except Exception as exc:  # pragma: no cover
    Collection = None
    CollectionSchema = None
    DataType = None
    FieldSchema = None
    connections = None
    utility = None
    _PYMILVUS_IMPORT_ERROR = exc


class FaceVectorStore:
    def __init__(self):
        self.milvus_uri = os.getenv('MILVUS_URI', 'http://localhost:19530')
        self.collection_name = os.getenv('FACE_MILVUS_COLLECTION', 'face_embeddings')
        self._dim = 512
        self._connected = False
        self._lock = threading.Lock()

    def _ensure_connected(self):
        if _PYMILVUS_IMPORT_ERROR is not None or connections is None:
            raise RuntimeError(f'pymilvus 未安装或加载失败: {_PYMILVUS_IMPORT_ERROR}')
        if self._connected:
            return
        with self._lock:
            if self._connected:
                return
            alias = 'default'
            if alias not in connections.list_connections() or not connections.has_connection(alias):
                host = self.milvus_uri.replace('http://', '').replace('https://', '').split(':')[0]
                port = self.milvus_uri.split(':')[-1] if ':' in self.milvus_uri else '19530'
                connections.connect(alias=alias, host=host, port=port)
            self._ensure_collection()
            self._connected = True

    def _ensure_collection(self):
        if utility.has_collection(self.collection_name):
            return
        fields = [
            FieldSchema(name='id', dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name='library_id', dtype=DataType.INT64),
            FieldSchema(name='face_entry_id', dtype=DataType.INT64),
            FieldSchema(name='label', dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name='person_name', dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name='person_code', dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, dim=self._dim),
        ]
        schema = CollectionSchema(fields=fields, description='face embeddings')
        Collection(name=self.collection_name, schema=schema)
        col = Collection(self.collection_name)
        col.create_index(
            field_name='embedding',
            index_params={'index_type': 'IVF_FLAT', 'metric_type': 'IP', 'params': {'nlist': 128}},
        )

    def _collection(self) -> Collection:
        self._ensure_connected()
        col = Collection(self.collection_name)
        col.load()
        return col

    def insert_embedding(
        self,
        embedding: np.ndarray,
        label: str,
        library_id: int,
        face_entry_id: int = 0,
        person_name: str = '',
        person_code: str = '',
    ) -> Dict[str, Any]:
        col = self._collection()
        vec = embedding.astype(np.float32).tolist()
        result = col.insert([{
            'library_id': int(library_id),
            'face_entry_id': int(face_entry_id),
            'label': label or person_name or '',
            'person_name': person_name or label or '',
            'person_code': person_code or '',
            'embedding': vec,
        }])
        col.flush()
        ids = result.primary_keys
        return {'insert_result': result, 'milvus_id': str(ids[0]) if ids else None}

    def update_face_entry_id(self, milvus_id, face_entry_id: int) -> None:
        logger.warning('update_face_entry_id: milvus 暂不支持原地更新 milvus_id=%s entry=%s', milvus_id, face_entry_id)

    def delete_by_milvus_id(self, milvus_id) -> None:
        col = self._collection()
        col.delete(expr=f'id == {int(milvus_id)}')
        col.flush()

    def delete_by_face_entry_id(self, face_entry_id: int) -> None:
        col = self._collection()
        col.delete(expr=f'face_entry_id == {int(face_entry_id)}')
        col.flush()

    def delete_face(self, label: str) -> int:
        col = self._collection()
        col.delete(expr=f'label == "{label}"')
        col.flush()
        return 0

    def search_embedding(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        library_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        col = self._collection()
        vec = embedding.astype(np.float32).tolist()
        expr = f'library_id == {int(library_id)}' if library_id is not None else None
        results = col.search(
            data=[vec],
            anns_field='embedding',
            param={'metric_type': 'IP', 'params': {'nprobe': 16}},
            limit=top_k,
            expr=expr,
            output_fields=['library_id', 'face_entry_id', 'label', 'person_name', 'person_code'],
        )
        items: List[Dict[str, Any]] = []
        for hit in results[0]:
            entity = hit.entity
            items.append({
                'milvus_id': str(hit.id),
                'similarity': float(hit.distance),
                'library_id': entity.get('library_id'),
                'face_entry_id': entity.get('face_entry_id'),
                'label': entity.get('label'),
                'person_name': entity.get('person_name'),
                'person_code': entity.get('person_code'),
            })
        return items

    def list_faces(self, label: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        col = self._collection()
        expr = f'label == "{label}"' if label else 'id >= 0'
        return col.query(
            expr=expr,
            output_fields=['id', 'label', 'library_id', 'face_entry_id', 'person_name'],
            limit=limit,
        )

    def list_library_embeddings(self, library_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
        col = self._collection()
        return col.query(
            expr=f'library_id == {int(library_id)}',
            output_fields=['id', 'face_entry_id', 'person_name', 'person_code', 'embedding'],
            limit=limit,
        )

    def ping(self) -> Dict[str, Any]:
        try:
            self._ensure_connected()
            ok = utility.has_collection(self.collection_name)
            return {
                'milvus_uri': self.milvus_uri,
                'collection_name': self.collection_name,
                'collection_exists': ok,
            }
        except Exception as exc:
            return {
                'milvus_uri': self.milvus_uri,
                'collection_name': self.collection_name,
                'collection_exists': False,
                'error': str(exc),
            }


_STORE_LOCK = threading.Lock()
_STORE_INSTANCE: Optional[FaceVectorStore] = None


def get_face_vector_store() -> FaceVectorStore:
    global _STORE_INSTANCE
    if _STORE_INSTANCE is not None:
        return _STORE_INSTANCE
    with _STORE_LOCK:
        if _STORE_INSTANCE is None:
            _STORE_INSTANCE = FaceVectorStore()
    return _STORE_INSTANCE
