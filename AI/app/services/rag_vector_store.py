"""RAG Milvus 向量存储。PostgreSQL 保存元数据，Milvus 保存向量。"""
import os
import threading

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility


class RagVectorStore:
    def __init__(self):
        self.uri = os.getenv('MILVUS_URI', 'http://localhost:19530')
        self.collection_name = os.getenv('RAG_MILVUS_COLLECTION', 'rag_knowledge_chunks')
        self.dimensions = int(os.getenv('RAG_EMBEDDING_DIMENSIONS', '1024'))
        self.alias = 'rag'
        self._lock = threading.Lock()
        self._connected = False

    def _connect(self):
        if self._connected:
            return
        with self._lock:
            if self._connected:
                return
            host = self.uri.replace('http://', '').replace('https://', '').split(':')[0]
            port = self.uri.rsplit(':', 1)[-1] if ':' in self.uri else '19530'
            connections.connect(alias=self.alias, host=host, port=port)
            self._ensure_collection()
            self._connected = True

    def _ensure_collection(self):
        if utility.has_collection(self.collection_name, using=self.alias):
            collection = Collection(self.collection_name, using=self.alias)
            field = next((item for item in collection.schema.fields if item.name == 'embedding'), None)
            actual_dim = field.params.get('dim') if field else None
            if actual_dim and int(actual_dim) != self.dimensions:
                raise RuntimeError(f'Milvus 集合维度为 {actual_dim}，当前 Embedding 配置为 {self.dimensions}')
            return
        schema = CollectionSchema([
            FieldSchema('id', DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema('knowledge_base_id', DataType.INT64),
            FieldSchema('document_id', DataType.INT64),
            FieldSchema('chunk_id', DataType.INT64),
            FieldSchema('embedding', DataType.FLOAT_VECTOR, dim=self.dimensions),
        ], description='EasyAIoT RAG knowledge chunks')
        collection = Collection(self.collection_name, schema=schema, using=self.alias)
        collection.create_index('embedding', {
            'index_type': 'HNSW', 'metric_type': 'COSINE',
            'params': {'M': 16, 'efConstruction': 200},
        })

    def _collection(self):
        self._connect()
        collection = Collection(self.collection_name, using=self.alias)
        collection.load()
        return collection

    def insert(self, records: list[dict]) -> list[str]:
        if not records:
            return []
        result = self._collection().insert(records)
        self._collection().flush()
        return [str(value) for value in result.primary_keys]

    def search(self, knowledge_base_id: int, vector: list[float], limit: int) -> list[dict]:
        results = self._collection().search(
            data=[vector], anns_field='embedding',
            param={'metric_type': 'COSINE', 'params': {'ef': max(64, limit * 4)}},
            limit=limit, expr=f'knowledge_base_id == {int(knowledge_base_id)}',
            output_fields=['chunk_id', 'document_id'],
        )
        return [{
            'milvus_id': str(hit.id), 'chunk_id': int(hit.entity.get('chunk_id')),
            'document_id': int(hit.entity.get('document_id')), 'similarity': float(hit.distance),
        } for hit in results[0]]

    def search_segments(self, segment_ids: list[int], vector: list[float], limit: int) -> list[dict]:
        if not segment_ids:
            return []
        ids = ','.join(str(int(value)) for value in segment_ids)
        results = self._collection().search(
            data=[vector], anns_field='embedding',
            param={'metric_type': 'COSINE', 'params': {'ef': max(64, limit * 4)}},
            limit=limit, expr=f'chunk_id in [{ids}]', output_fields=['chunk_id', 'document_id'],
        )
        return [{'milvus_id': str(hit.id), 'chunk_id': int(hit.entity.get('chunk_id')),
                 'document_id': int(hit.entity.get('document_id')), 'similarity': float(hit.distance)}
                for hit in results[0]]

    def delete_segment(self, segment_id: int):
        collection = self._collection()
        collection.delete(expr=f'chunk_id == {int(segment_id)}')
        collection.flush()

    def drop_collection(self):
        self._connect()
        if utility.has_collection(self.collection_name, using=self.alias):
            utility.drop_collection(self.collection_name, using=self.alias)
        self._connected = False

    def delete_document(self, document_id: int):
        collection = self._collection()
        collection.delete(expr=f'document_id == {int(document_id)}')
        collection.flush()

    def delete_knowledge_base(self, knowledge_base_id: int):
        collection = self._collection()
        collection.delete(expr=f'knowledge_base_id == {int(knowledge_base_id)}')
        collection.flush()

    def health(self) -> dict:
        try:
            self._connect()
            return {'ok': True, 'uri': self.uri, 'collection': self.collection_name, 'dimensions': self.dimensions}
        except Exception as exc:
            return {'ok': False, 'uri': self.uri, 'collection': self.collection_name, 'error': str(exc)}


_store = None
_store_lock = threading.Lock()


def get_rag_vector_store() -> RagVectorStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = RagVectorStore()
    return _store
