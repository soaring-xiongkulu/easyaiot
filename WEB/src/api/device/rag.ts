import { defHttp } from '@/utils/http/axios'
const BASE='/model/rag'
export interface KnowledgeDocument{id:number;name:string;content_type?:string;char_count:number;status:string;source_type:string;segment_count:number;enabled_segment_count:number;created_at?:string;updated_at?:string}
export interface KnowledgeSegment{id:number;document_id:number;document_name:string;index:number;title:string;content:string;tags:string[];is_enabled:boolean;knowledge_set_count:number;updated_at?:string}
export interface KnowledgeSet{id:number;name:string;category:string;description?:string;segment_ids:number[];segment_count:number;document_count:number;expert_count:number;updated_at?:string}
export interface RagExpert{id:number;name:string;category:string;knowledge_set_ids:number[];knowledge_set_names:string[];system_prompt:string;welcome_message?:string;is_enabled:boolean;updated_at?:string}
export interface RagSource{segment_id:number;document_id:number;document_name:string;content:string;score:number}
export const listKnowledgeDocuments=()=>defHttp.get<KnowledgeDocument[]>({url:`${BASE}/documents`})
export const uploadKnowledgeDocument=(file:File)=>{const data=new FormData();data.append('file',file);return defHttp.post<KnowledgeDocument>({url:`${BASE}/documents`,data})}
export const deleteKnowledgeDocument=(id:number)=>defHttp.delete({url:`${BASE}/documents/${id}`})
export const listKnowledgeSegments=(documentId?:number)=>defHttp.get<KnowledgeSegment[]>({url:`${BASE}/segments`,params:documentId?{document_id:documentId}:{}})
export const createKnowledgeSegment=(documentId:number,data:Partial<KnowledgeSegment>)=>defHttp.post<KnowledgeSegment>({url:`${BASE}/documents/${documentId}/segments`,data})
export const updateKnowledgeSegment=(id:number,data:Partial<KnowledgeSegment>)=>defHttp.put<KnowledgeSegment>({url:`${BASE}/segments/${id}`,data})
export const deleteKnowledgeSegment=(id:number)=>defHttp.delete({url:`${BASE}/segments/${id}`})
export const listKnowledgeSets=()=>defHttp.get<KnowledgeSet[]>({url:`${BASE}/knowledge-sets`})
export const createKnowledgeSet=(data:Partial<KnowledgeSet>)=>defHttp.post<KnowledgeSet>({url:`${BASE}/knowledge-sets`,data})
export const updateKnowledgeSet=(id:number,data:Partial<KnowledgeSet>)=>defHttp.put<KnowledgeSet>({url:`${BASE}/knowledge-sets/${id}`,data})
export const deleteKnowledgeSet=(id:number)=>defHttp.delete({url:`${BASE}/knowledge-sets/${id}`})
export const searchKnowledgeSet=(id:number,query:string)=>defHttp.post<RagSource[]>({url:`${BASE}/knowledge-sets/${id}/search`,data:{query,top_k:8}})
export const listRagExperts=()=>defHttp.get<RagExpert[]>({url:`${BASE}/experts`})
export const createRagExpert=(data:Partial<RagExpert>)=>defHttp.post<RagExpert>({url:`${BASE}/experts`,data})
export const updateRagExpert=(id:number,data:Partial<RagExpert>)=>defHttp.put<RagExpert>({url:`${BASE}/experts/${id}`,data})
export const deleteRagExpert=(id:number)=>defHttp.delete({url:`${BASE}/experts/${id}`})
export const chatWithRagExpert=(id:number,question:string)=>defHttp.post({url:`${BASE}/experts/${id}/chat`,data:{question,top_k:5}})
