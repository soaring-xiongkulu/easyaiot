import logging
import os

import requests
from flask import Blueprint, jsonify, request

from db_models import LLMModel, RagExpert, RagKnowledgeDocument, RagKnowledgeSegment, RagKnowledgeSet, db
from app.services.llm_gateway_client import invoke_chat
from app.services.rag_service import embed_texts, index_document, persist_document_vectors, retrieve_segments, terms
from app.services.rag_vector_store import get_rag_vector_store

rag_bp = Blueprint('rag', __name__)
logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {'.txt', '.md', '.markdown', '.csv', '.json', '.log'}


def ok(data=None, msg='success'):
    return jsonify({'code': 0, 'msg': msg, 'data': data})


def ids_from(data, field):
    return list(dict.fromkeys(int(value) for value in (data.get(field) or [])))


def replace_segment_vector(segment):
    store = get_rag_vector_store()
    store.delete_segment(segment.id)
    vector = embed_texts([segment.content])[0]
    ids = store.insert([{'knowledge_base_id': segment.document_id, 'document_id': segment.document_id,
                         'chunk_id': segment.id, 'embedding': vector}])
    segment.milvus_id = ids[0]


@rag_bp.route('/documents', methods=['GET', 'POST'])
def documents():
    if request.method == 'GET':
        items = RagKnowledgeDocument.query.order_by(RagKnowledgeDocument.updated_at.desc()).all()
        return ok([item.to_dict() for item in items])
    upload = request.files.get('file')
    if not upload or not upload.filename:
        return jsonify({'code': 400, 'msg': '请选择知识文档'}), 400
    extension = os.path.splitext(upload.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({'code': 400, 'msg': '仅支持 TXT、Markdown、CSV、JSON、LOG'}), 400
    raw = upload.read()
    if len(raw) > 10 * 1024 * 1024:
        return jsonify({'code': 400, 'msg': '单个文件不能超过 10MB'}), 400
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return jsonify({'code': 400, 'msg': '文件必须使用 UTF-8 编码'}), 400
    item = RagKnowledgeDocument(name=upload.filename, content_type=upload.mimetype,
                                char_count=len(text), status='parsed')
    count = index_document(item, text)
    if not count:
        return jsonify({'code': 400, 'msg': '文档没有可解析文本'}), 400
    try:
        db.session.add(item)
        db.session.flush()
        persist_document_vectors(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if item.id:
            get_rag_vector_store().delete_document(item.id)
        raise
    return ok(item.to_dict(), f'文档已解析，生成 {count} 个待维护知识片段')


@rag_bp.route('/documents/<int:item_id>', methods=['DELETE'])
def delete_document(item_id):
    item = RagKnowledgeDocument.query.get_or_404(item_id)
    get_rag_vector_store().delete_document(item.id)
    db.session.delete(item)
    db.session.commit()
    return ok(msg='知识文档及其片段已删除')


@rag_bp.route('/documents/<int:item_id>/segments', methods=['GET', 'POST'])
def document_segments(item_id):
    document = RagKnowledgeDocument.query.get_or_404(item_id)
    if request.method == 'GET':
        return ok([item.to_dict() for item in sorted(document.segments, key=lambda value: value.segment_index)])
    data = request.get_json(silent=True) or {}
    content = str(data.get('content') or '').strip()
    if not content:
        return jsonify({'code': 400, 'msg': '片段内容不能为空'}), 400
    item = RagKnowledgeSegment(document_id=document.id, segment_index=len(document.segments),
                               title=str(data.get('title') or '').strip(), content=content,
                               tags=data.get('tags') or [], search_terms=' '.join(terms(content)))
    db.session.add(item)
    db.session.flush()
    replace_segment_vector(item)
    db.session.commit()
    return ok(item.to_dict(), '知识片段已创建')


@rag_bp.route('/segments', methods=['GET'])
def segments():
    query = RagKnowledgeSegment.query
    document_id = request.args.get('document_id', type=int)
    if document_id:
        query = query.filter_by(document_id=document_id)
    items = query.order_by(RagKnowledgeSegment.updated_at.desc()).all()
    return ok([item.to_dict() for item in items])


@rag_bp.route('/segments/<int:item_id>', methods=['PUT', 'DELETE'])
def segment_item(item_id):
    item = RagKnowledgeSegment.query.get_or_404(item_id)
    if request.method == 'DELETE':
        get_rag_vector_store().delete_segment(item.id)
        db.session.delete(item)
        db.session.commit()
        return ok(msg='知识片段已删除')
    data = request.get_json(silent=True) or {}
    content = str(data.get('content') or '').strip()
    if not content:
        return jsonify({'code': 400, 'msg': '片段内容不能为空'}), 400
    content_changed = content != item.content
    item.title, item.content = str(data.get('title') or '').strip(), content
    item.tags, item.is_enabled = data.get('tags') or [], bool(data.get('is_enabled', True))
    item.search_terms = ' '.join(terms(content))
    if content_changed:
        replace_segment_vector(item)
    db.session.commit()
    return ok(item.to_dict(), '知识片段已更新')


@rag_bp.route('/knowledge-sets', methods=['GET', 'POST'])
def knowledge_sets():
    if request.method == 'GET':
        return ok([item.to_dict() for item in RagKnowledgeSet.query.order_by(RagKnowledgeSet.updated_at.desc()).all()])
    return save_knowledge_set()


def save_knowledge_set(item=None):
    data = request.get_json(silent=True) or {}
    name, category = str(data.get('name') or '').strip(), str(data.get('category') or '').strip()
    segment_ids = ids_from(data, 'segment_ids')
    segments = RagKnowledgeSegment.query.filter(RagKnowledgeSegment.id.in_(segment_ids)).all() if segment_ids else []
    if not name or not category or not segments:
        return jsonify({'code': 400, 'msg': '名称、分类和知识片段不能为空'}), 400
    if len(segments) != len(segment_ids):
        return jsonify({'code': 404, 'msg': '部分知识片段不存在'}), 404
    item = item or RagKnowledgeSet()
    item.name, item.category, item.description, item.segments = name, category, data.get('description'), segments
    db.session.add(item)
    db.session.commit()
    return ok(item.to_dict(), '知识集已保存')


@rag_bp.route('/knowledge-sets/<int:item_id>', methods=['PUT', 'DELETE'])
def knowledge_set_item(item_id):
    item = RagKnowledgeSet.query.get_or_404(item_id)
    if request.method == 'PUT':
        return save_knowledge_set(item)
    if item.experts:
        return jsonify({'code': 400, 'msg': '知识集正在被 RAG 专家使用，请先解除关联'}), 400
    db.session.delete(item)
    db.session.commit()
    return ok(msg='知识集已删除，原文档和片段已保留')


@rag_bp.route('/knowledge-sets/<int:item_id>/search', methods=['POST'])
def search_knowledge_set(item_id):
    item = RagKnowledgeSet.query.get_or_404(item_id)
    data = request.get_json(silent=True) or {}
    query = str(data.get('query') or '').strip()
    if not query:
        return jsonify({'code': 400, 'msg': '请输入检索内容'}), 400
    return ok(retrieve_segments([value.id for value in item.segments if value.is_enabled], query,
                                limit=int(data.get('top_k') or 8)))


@rag_bp.route('/experts', methods=['GET', 'POST'])
def experts():
    if request.method == 'GET':
        return ok([item.to_dict() for item in RagExpert.query.order_by(RagExpert.updated_at.desc()).all()])
    return save_expert()


def save_expert(item=None):
    data = request.get_json(silent=True) or {}
    name, category = str(data.get('name') or '').strip(), str(data.get('category') or '').strip()
    set_ids = ids_from(data, 'knowledge_set_ids')
    sets = RagKnowledgeSet.query.filter(RagKnowledgeSet.id.in_(set_ids)).all() if set_ids else []
    prompt = str(data.get('system_prompt') or '').strip()
    if not name or not category or not sets or not prompt:
        return jsonify({'code': 400, 'msg': '名称、分类、知识集和专家指令不能为空'}), 400
    if len(sets) != len(set_ids):
        return jsonify({'code': 404, 'msg': '部分知识集不存在'}), 404
    item = item or RagExpert()
    item.name, item.category, item.knowledge_sets = name, category, sets
    item.system_prompt, item.welcome_message = prompt, data.get('welcome_message')
    db.session.add(item)
    db.session.commit()
    return ok(item.to_dict(), 'RAG 专家已保存')


@rag_bp.route('/experts/<int:item_id>', methods=['PUT', 'DELETE'])
def expert_item(item_id):
    item = RagExpert.query.get_or_404(item_id)
    if request.method == 'PUT':
        return save_expert(item)
    db.session.delete(item)
    db.session.commit()
    return ok(msg='RAG 专家已删除')


@rag_bp.route('/experts/<int:item_id>/chat', methods=['POST'])
def expert_chat(item_id):
    expert = RagExpert.query.get_or_404(item_id)
    data = request.get_json(silent=True) or {}
    question = str(data.get('question') or '').strip()
    if not question:
        return jsonify({'code': 400, 'msg': '问题不能为空'}), 400
    segment_ids = list({segment.id for knowledge_set in expert.knowledge_sets for segment in knowledge_set.segments if segment.is_enabled})
    sources = retrieve_segments(segment_ids, question, limit=int(data.get('top_k') or 5))
    context = '\n\n'.join(f'【资料 {index}｜{item["document_name"]}】\n{item["content"]}'
                            for index, item in enumerate(sources, 1)) or '未检索到相关知识。'
    model = LLMModel.query.filter_by(is_active=True).order_by(LLMModel.id).first()
    if not model:
        response = f'【检索结果】\n\n{sources[0]["content"]}' if sources else '知识集中没有检索到相关依据。'
        return ok({'response': response, 'model': None, 'mode': 'retrieval', 'sources': sources})
    messages = [{'role': 'system', 'content': f'{expert.system_prompt}\n必须依据资料回答，资料不足时明确说明，不得编造。引用使用【资料 1】格式。\n\n{context}'},
                {'role': 'user', 'content': question}]
    try:
        result = invoke_chat(model, messages, stream=False, timeout=model.timeout)
        return ok({'response': result['response'], 'model': model.model_name, 'sources': sources})
    except requests.exceptions.RequestException as exc:
        logger.warning('RAG 专家调用模型失败，降级为检索回答', exc_info=True)
        response = f'【模型暂不可用，已返回检索结果】\n\n{sources[0]["content"]}' if sources else '模型暂不可用，知识集中也没有检索到依据。'
        return ok({'response': response, 'model': None, 'degraded': True, 'warning': str(exc), 'sources': sources})


@rag_bp.route('/health', methods=['GET'])
def health():
    return ok(get_rag_vector_store().health())
