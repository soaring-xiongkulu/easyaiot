"""RAG 切片、Embedding 与 Milvus/关键词混合检索。"""
import math
import os
import re
import hashlib
from collections import Counter

import requests

from db_models import RagKnowledgeDocument, RagKnowledgeSegment
from app.services.rag_vector_store import get_rag_vector_store


def split_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    clean = re.sub(r'\r\n?', '\n', text or '')
    clean = re.sub(r'\n{3,}', '\n\n', clean).strip()
    if not clean:
        return []
    paragraphs = [part.strip() for part in re.split(r'\n\s*\n', clean) if part.strip()]
    chunks, buffer = [], ''
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 1 <= chunk_size:
            buffer = f'{buffer}\n{paragraph}'.strip()
            continue
        if buffer:
            chunks.append(buffer)
        while len(paragraph) > chunk_size:
            chunks.append(paragraph[:chunk_size])
            paragraph = paragraph[chunk_size - overlap:]
        buffer = paragraph
    if buffer:
        chunks.append(buffer)
    return chunks


def terms(text: str) -> list[str]:
    lowered = (text or '').lower()
    words = re.findall(r'[a-z0-9][a-z0-9_.:/-]{1,}|[\u4e00-\u9fff]{2,}', lowered)
    result = []
    for word in words:
        if re.fullmatch(r'[\u4e00-\u9fff]+', word):
            result.extend(word[i:i + 2] for i in range(max(1, len(word) - 1)))
            result.append(word)
        else:
            result.append(word)
    return result


def _embedding_config() -> tuple[str, str, str]:
    base_url = os.getenv('RAG_EMBEDDING_BASE_URL', '').strip().rstrip('/')
    api_key = os.getenv('RAG_EMBEDDING_API_KEY', '').strip()
    model = os.getenv('RAG_EMBEDDING_MODEL', '').strip()
    if not base_url or not model:
        raise RuntimeError('RAG Embedding 未配置，请设置 RAG_EMBEDDING_BASE_URL 和 RAG_EMBEDDING_MODEL')
    return base_url, api_key, model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 OpenAI 兼容 /embeddings；平台统一要求输出 1024 维。"""
    if not texts:
        return []
    provider = os.getenv('RAG_EMBEDDING_PROVIDER', 'auto').strip().lower()
    if provider == 'auto':
        provider = 'openai-compatible' if os.getenv('RAG_EMBEDDING_BASE_URL') and os.getenv('RAG_EMBEDDING_MODEL') else 'local-hash'
    if provider == 'local-hash':
        # 无外部 Key 的离线演示/降级模式：特征哈希会真实写入 Milvus，便于验证完整链路。
        # 生产环境应使用语义 Embedding 服务，切换后上层知识库与智能体接口保持不变。
        dimensions = 1024
        vectors = []
        for text in texts:
            vector = [0.0] * dimensions
            values = terms(text)
            for value in values:
                digest = hashlib.sha256(value.encode('utf-8')).digest()
                index = int.from_bytes(digest[:4], 'big') % dimensions
                vector[index] += 1.0 if digest[4] & 1 else -1.0
            norm = math.sqrt(sum(item * item for item in vector)) or 1.0
            vectors.append([item / norm for item in vector])
        return vectors
    base_url, api_key, model = _embedding_config()
    url = base_url if base_url.endswith('/embeddings') else f'{base_url}/embeddings'
    response = requests.post(
        url,
        headers={'Content-Type': 'application/json', **({'Authorization': f'Bearer {api_key}'} if api_key else {})},
        json={'model': model, 'input': texts, 'dimensions': 1024},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json().get('data') or []
    vectors = [item.get('embedding') for item in sorted(data, key=lambda item: item.get('index', 0))]
    if len(vectors) != len(texts) or any(not vector or len(vector) != 1024 for vector in vectors):
        raise RuntimeError('Embedding 服务返回数量或维度异常，平台要求 1024 维')
    return vectors


def index_document(document: RagKnowledgeDocument, text: str) -> int:
    chunks = split_text(text)
    vectors = []
    for start in range(0, len(chunks), 16):
        vectors.extend(embed_texts(chunks[start:start + 16]))
    for index, (content, embedding) in enumerate(zip(chunks, vectors)):
        chunk = RagKnowledgeSegment(
            segment_index=index,
            title=f'片段 {index + 1}',
            content=content,
            search_terms=' '.join(terms(content)),
        )
        chunk._rag_embedding = embedding
        document.segments.append(chunk)
    return len(chunks)


def persist_document_vectors(document: RagKnowledgeDocument) -> None:
    records = [{
        'knowledge_base_id': int(document.id),
        'document_id': int(document.id), 'chunk_id': int(chunk.id),
        'embedding': chunk._rag_embedding,
    } for chunk in document.segments]
    ids = get_rag_vector_store().insert(records)
    if len(ids) != len(document.segments):
        raise RuntimeError('Milvus 写入数量与知识片段数量不一致')
    for chunk, milvus_id in zip(document.segments, ids):
        chunk.milvus_id = milvus_id
        if hasattr(chunk, '_rag_embedding'):
            delattr(chunk, '_rag_embedding')


def retrieve_segments(segment_ids: list[int], query: str, limit: int = 5) -> list[dict]:
    query_terms = terms(query)
    if not query_terms:
        return []
    query_vector = embed_texts([query])[0]
    candidate_limit = max(20, min(limit * 8, 80))
    vector_hits = get_rag_vector_store().search_segments(segment_ids, query_vector, candidate_limit)
    hit_by_chunk = {item['chunk_id']: item for item in vector_hits}
    chunk_ids = list(hit_by_chunk)
    chunks = RagKnowledgeSegment.query.filter(RagKnowledgeSegment.id.in_(chunk_ids), RagKnowledgeSegment.is_enabled.is_(True)).all() if chunk_ids else []
    chunks.sort(key=lambda item: vector_hits.index(hit_by_chunk[item.id]))
    if not chunks:
        return []
    query_count = Counter(query_terms)
    document_frequency = Counter()
    chunk_terms = []
    for chunk in chunks:
        values = (chunk.search_terms or '').split()
        chunk_terms.append(values)
        document_frequency.update(set(values))
    scored = []
    total = len(chunks)
    for rank, (chunk, values) in enumerate(zip(chunks, chunk_terms)):
        counts = Counter(values)
        score = 0.0
        for term, qtf in query_count.items():
            if counts[term]:
                idf = math.log(1 + total / (1 + document_frequency[term]))
                score += (1 + math.log(counts[term])) * idf * qtf
        if query.lower() in chunk.content.lower():
            score += 4.0
        # Reciprocal-rank 融合：向量召回始终参与，词项命中负责提升精确术语。
        vector_score = hit_by_chunk[chunk.id]['similarity']
        scored.append((vector_score * 0.75 + min(score, 4.0) * 0.0625, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{
        'segment_id': chunk.id,
        'document_id': chunk.document_id,
        'document_name': chunk.document.name,
        'content': chunk.content,
        'score': round(score, 4),
    } for score, chunk in scored[:max(1, min(limit, 10))]]
