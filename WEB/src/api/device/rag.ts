import { defHttp } from '@/utils/http/axios'

const BASE = '/model/rag'

export interface KnowledgeDocument {
  id: number;
  name: string;
  content_type?: string;
  char_count: number;
  status: string;
  source_type: string;
  segment_count: number;
  enabled_segment_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface KnowledgeSegment {
  id: number;
  document_id: number;
  document_name: string;
  index: number;
  title: string;
  content: string;
  tags: string[];
  is_enabled: boolean;
  knowledge_set_count: number;
  updated_at?: string;
}

export interface KnowledgeSet {
  id: number;
  name: string;
  category: string;
  description?: string;
  segment_ids: number[];
  segment_count: number;
  document_count: number;
  expert_count: number;
  updated_at?: string;
}

export interface RagExpert {
  id: number;
  name: string;
  category: string;
  knowledge_set_ids: number[];
  knowledge_set_names: string[];
  system_prompt: string;
  welcome_message?: string;
  is_enabled: boolean;
  updated_at?: string;
}

export interface RagSource {
  segment_id: number;
  document_id: number;
  document_name: string;
  content: string;
  score: number;
}

/** 向量库健康状态（Milvus 连接与集合信息）；embedding_mode=local-hash 表示词频降级检索 */
export interface RagHealth {
  ok: boolean;
  uri: string;
  collection: string;
  dimensions?: number;
  error?: string;
  embedding_mode?: 'openai-compatible' | 'local-hash';
}

/** 多轮对话历史消息 */
export interface RagChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface RagChatResult {
  response: string;
  model?: string | null;
  mode?: string;
  degraded?: boolean;
  warning?: string;
  sources: RagSource[];
}

// ==================== 知识文档 ====================

export const listKnowledgeDocuments = () => defHttp.get<KnowledgeDocument[]>({ url: `${BASE}/documents` })

export const uploadKnowledgeDocument = (file: File) => {
  const data = new FormData();
  data.append('file', file);
  return defHttp.post<KnowledgeDocument>({ url: `${BASE}/documents`, data });
}

export const deleteKnowledgeDocument = (id: number) => defHttp.delete({ url: `${BASE}/documents/${id}` })

// ==================== 知识片段 ====================

export const listKnowledgeSegments = (documentId?: number) =>
  defHttp.get<KnowledgeSegment[]>({ url: `${BASE}/segments`, params: documentId ? { document_id: documentId } : {} })

export const createKnowledgeSegment = (documentId: number, data: Partial<KnowledgeSegment>) =>
  defHttp.post<KnowledgeSegment>({ url: `${BASE}/documents/${documentId}/segments`, data })

export const updateKnowledgeSegment = (id: number, data: Partial<KnowledgeSegment>) =>
  defHttp.put<KnowledgeSegment>({ url: `${BASE}/segments/${id}`, data })

export const deleteKnowledgeSegment = (id: number) => defHttp.delete({ url: `${BASE}/segments/${id}` })

/** AI 批量补全片段标题与业务标签（内容不变，不重新向量化），单次最多 20 条 */
export const autoMetaSegments = (ids: number[]) =>
  defHttp.post<{ updated: number; failed: string[] }>({ url: `${BASE}/segments/auto-meta`, data: { ids } })

/** 合并同一文档的多个片段：内容拼接、标签并集，知识集引用自动改挂新片段 */
export const mergeSegments = (ids: number[], title?: string) =>
  defHttp.post<KnowledgeSegment>({ url: `${BASE}/segments/merge`, data: { ids, title } })

// ==================== 知识集 ====================

export const listKnowledgeSets = () => defHttp.get<KnowledgeSet[]>({ url: `${BASE}/knowledge-sets` })

export const createKnowledgeSet = (data: Partial<KnowledgeSet>) =>
  defHttp.post<KnowledgeSet>({ url: `${BASE}/knowledge-sets`, data })

export const updateKnowledgeSet = (id: number, data: Partial<KnowledgeSet>) =>
  defHttp.put<KnowledgeSet>({ url: `${BASE}/knowledge-sets/${id}`, data })

export const deleteKnowledgeSet = (id: number) => defHttp.delete({ url: `${BASE}/knowledge-sets/${id}` })

export const searchKnowledgeSet = (id: number, query: string, topK = 8) =>
  defHttp.post<RagSource[]>({ url: `${BASE}/knowledge-sets/${id}/search`, data: { query, top_k: topK } })

// ==================== RAG 专家 ====================

export const listRagExperts = () => defHttp.get<RagExpert[]>({ url: `${BASE}/experts` })

export const createRagExpert = (data: Partial<RagExpert>) => defHttp.post<RagExpert>({ url: `${BASE}/experts`, data })

export const updateRagExpert = (id: number, data: Partial<RagExpert>) =>
  defHttp.put<RagExpert>({ url: `${BASE}/experts/${id}`, data })

export const deleteRagExpert = (id: number) => defHttp.delete({ url: `${BASE}/experts/${id}` })

/**
 * 专家问答。history 传入此前对话（不含本次问题），后端拼接为多轮上下文；
 * top_k 控制召回资料条数。
 */
export const chatWithRagExpert = (id: number, question: string, options?: { history?: RagChatMessage[]; topK?: number }) =>
  defHttp.post<RagChatResult>({
    url: `${BASE}/experts/${id}/chat`,
    data: { question, top_k: options?.topK ?? 5, history: options?.history ?? [] },
  })

export const getRagHealth = () => defHttp.get<RagHealth>({ url: `${BASE}/health` })
