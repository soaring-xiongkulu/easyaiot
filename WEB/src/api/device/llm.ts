import { defHttp } from '@/utils/http/axios';

enum Api {
  LLM_LIST = '/admin-api/video/llm/list',
  LLM_DETAIL = '/admin-api/video/llm/detail',
  LLM_CREATE = '/admin-api/video/llm/create',
  LLM_UPDATE = '/admin-api/video/llm/update',
  LLM_DELETE = '/admin-api/video/llm/delete',
  LLM_ACTIVATE = '/admin-api/video/llm/activate',
  LLM_TEST = '/admin-api/video/llm/test',
  LLM_VISION_ANALYZE = '/admin-api/video/llm/vision/analyze',
  LLM_VISION_INFERENCE = '/admin-api/video/llm/vision/inference',
  LLM_VISION_UNDERSTANDING = '/admin-api/video/llm/vision/understanding',
  LLM_VISION_DEEP_THINKING = '/admin-api/video/llm/vision/deep-thinking',
  LLM_VIDEO_INFERENCE = '/admin-api/video/llm/video/inference',
  LLM_VIDEO_UNDERSTANDING = '/admin-api/video/llm/video/understanding',
}

export interface LLMModel {
  id?: number;
  name: string;
  service_type?: string; // 服务类型: online(线上) | local(本地)
  vendor: string;
  model_type: string;
  model_name: string;
  base_url: string;
  api_key?: string; // 线上服务必填，本地服务可选
  api_version?: string;
  temperature?: number;
  max_tokens?: number;
  timeout?: number;
  is_active?: boolean;
  status?: string;
  last_test_time?: string;
  last_test_result?: string;
  description?: string;
  icon_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LLMListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  service_type?: string;
  vendor?: string;
  model_type?: string;
}

export interface LLMListResponse {
  code: number;
  msg: string;
  data: {
    list: LLMModel[];
    total: number;
  };
}

export interface LLMDetailResponse {
  code: number;
  msg: string;
  data: LLMModel;
}

export interface LLMTestResponse {
  code: number;
  msg: string;
  data: {
    success: boolean;
    message: string;
    response?: string;
    error?: string;
  };
}

export interface VisionAnalyzeResponse {
  code: number;
  msg: string;
  data: {
    response: string;
    raw_result?: any;
  };
}

// 获取大模型列表
export const getLLMList = (params?: LLMListParams) => {
  return defHttp.get<LLMListResponse>({ url: Api.LLM_LIST, params });
};

// 获取大模型详情
export const getLLMDetail = (modelId: number) => {
  return defHttp.get<LLMDetailResponse>({ url: `${Api.LLM_DETAIL}/${modelId}` });
};

// 创建大模型配置
export const createLLM = (data: LLMModel) => {
  return defHttp.post<LLMDetailResponse>({ url: Api.LLM_CREATE, data });
};

// 更新大模型配置
export const updateLLM = (modelId: number, data: Partial<LLMModel>) => {
  return defHttp.put<LLMDetailResponse>({ url: `${Api.LLM_UPDATE}/${modelId}`, data });
};

// 删除大模型配置
export const deleteLLM = (modelId: number) => {
  return defHttp.delete({ url: `${Api.LLM_DELETE}/${modelId}` });
};

// 激活大模型
export const activateLLM = (modelId: number) => {
  return defHttp.post<LLMDetailResponse>({ url: `${Api.LLM_ACTIVATE}/${modelId}` });
};

// 测试大模型连接
export const testLLM = (modelId: number) => {
  return defHttp.post<LLMTestResponse>({ url: `${Api.LLM_TEST}/${modelId}` });
};

// 视觉分析
export const visionAnalyze = (imageFile: File, prompt?: string) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VISION_ANALYZE,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 视觉推理
export const visionInference = (imageFile: File, prompt?: string) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VISION_INFERENCE,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 视觉理解
export const visionUnderstanding = (imageFile: File, prompt?: string) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VISION_UNDERSTANDING,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 深度思考
export const visionDeepThinking = (imageFile: File, prompt?: string) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VISION_DEEP_THINKING,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 视频推理
export const videoInference = (videoFile?: File, videoUrl?: string, prompt?: string) => {
  const formData = new FormData();
  if (videoFile) {
    formData.append('video', videoFile);
  }
  if (videoUrl) {
    formData.append('video_url', videoUrl);
  }
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VIDEO_INFERENCE,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 视频理解
export const videoUnderstanding = (videoFile?: File, videoUrl?: string, prompt?: string) => {
  const formData = new FormData();
  if (videoFile) {
    formData.append('video', videoFile);
  }
  if (videoUrl) {
    formData.append('video_url', videoUrl);
  }
  if (prompt) {
    formData.append('prompt', prompt);
  }
  return defHttp.post<VisionAnalyzeResponse>({
    url: Api.LLM_VIDEO_UNDERSTANDING,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};
