import { defHttp } from '@/utils/http/axios';

enum Api {
  LLM_LIST = '/model/llm/list',
  LLM_DETAIL = '/model/llm/detail',
  LLM_CREATE = '/model/llm/create',
  LLM_UPDATE = '/model/llm/update',
  LLM_DELETE = '/model/llm/delete',
  LLM_ACTIVATE = '/model/llm/activate',
  LLM_DEACTIVATE = '/model/llm/deactivate',
  LLM_TEST = '/model/llm/test',
  LLM_TEMPLATES = '/model/llm/templates',
  LLM_CHAT = '/model/llm/chat',
  LLM_VISION_ANALYZE = '/model/llm/vision/analyze',
  LLM_VISION_INFERENCE = '/model/llm/vision/inference',
  LLM_VISION_UNDERSTANDING = '/model/llm/vision/understanding',
  LLM_VISION_DEEP_THINKING = '/model/llm/vision/deep-thinking',
  LLM_VIDEO_INFERENCE = '/model/llm/video/inference',
  LLM_VIDEO_UNDERSTANDING = '/model/llm/video/understanding',
}

export interface LLMModel {
  id?: number;
  name: string;
  service_type?: string; // 服务类型: online(线上) | local(本地)
  vendor: string; // 存储模板 key（存量数据为旧厂商标识，后端按别名解析）
  template?: string; // 详情接口返回：按别名解析后的模板 key
  template_label?: string; // 详情接口返回：模板显示名
  model_type: string;
  model_name: string;
  base_url: string;
  api_key?: string; // 线上服务必填，本地服务可选
  api_version?: string;
  temperature?: number;
  max_tokens?: number;
  timeout?: number;
  is_active?: boolean;
  is_preset?: boolean; // 预置模板数据（占位密钥 sk-placeholder-*），填入真实密钥后自动消失
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
  is_active?: string; // 过滤激活状态: 'true' | 'false' | '' (空字符串表示不过滤)
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

// 大模型接入模板（OpenAI 兼容协议 + 预置端点）
export interface LLMTemplate {
  key: string;
  label: string;
  base_url: string;
  doc_url?: string;
  builtin_models?: string[];
}

export interface LLMTemplatesResponse {
  code: number;
  msg: string;
  data: {
    templates: LLMTemplate[];
  };
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

// 获取大模型接入模板列表
export const getLLMTemplates = () => {
  return defHttp.get<LLMTemplatesResponse>({ url: Api.LLM_TEMPLATES });
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

// 禁用大模型
export const deactivateLLM = (modelId: number) => {
  return defHttp.post<LLMDetailResponse>({ url: `${Api.LLM_DEACTIVATE}/${modelId}` });
};

// 测试大模型连接
export const testLLM = (modelId: number) => {
  return defHttp.post<LLMTestResponse>({ url: `${Api.LLM_TEST}/${modelId}` });
};

// ========== HARNESS LLM 统一网关（收口通道，见 HARNESS/docs/llm-unified-gateway-design.md）==========
// VITE_LLM_GATEWAY_MODE = harness（默认，网关优先 + 失败自动回退直连）| direct（始终直连 AI 模块）
// VITE_LLM_GATEWAY_URL  = 网关基址（含 /api/llm，如 http://<host>:3082/api/llm；留空则直连）
// VITE_LLM_GATEWAY_TOKEN = 网关令牌（与 harness.env 的 LLM_GATEWAY_TOKEN 一致）
const LLM_GATEWAY_MODE = String(import.meta.env.VITE_LLM_GATEWAY_MODE ?? 'harness').trim().toLowerCase();
const LLM_GATEWAY_URL = String(import.meta.env.VITE_LLM_GATEWAY_URL ?? '')
  .trim()
  .replace(/\/+$/, '');
const LLM_GATEWAY_TOKEN = String(import.meta.env.VITE_LLM_GATEWAY_TOKEN ?? '').trim();

// 网关通道是否生效（未配置网关地址时自动退化为直连，等同 direct）
export function isLLMGatewayEnabled(): boolean {
  return LLM_GATEWAY_MODE !== 'direct' && !!LLM_GATEWAY_URL;
}

export interface LLMGatewayHealth {
  ok: boolean;
  model: string | null;
  model_name?: string | null;
  fetched_at?: string | null;
  stale?: boolean;
  last_error?: string | null;
}

// 网关健康探测（无需令牌）
export async function gatewayHealth(): Promise<LLMGatewayHealth> {
  const res = await fetch(`${LLM_GATEWAY_URL}/health`, { method: 'GET' });
  return (await res.json()) as LLMGatewayHealth;
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error ?? new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
}

// 经网关 /api/llm/chat 调用当前启用模型；返回与直连一致的 {code,msg,data:{response}} 信封
async function callGatewayChat(params: {
  prompt: string;
  mode?: string;
  file?: File;
  mediaUrl?: string;
  mediaType: 'image' | 'video';
  timeoutMs: number;
}): Promise<VisionAnalyzeResponse> {
  if (!LLM_GATEWAY_URL) {
    throw new Error('LLM网关地址未配置');
  }
  const url = params.mediaUrl ?? (params.file ? await fileToDataUrl(params.file) : '');
  if (!url) {
    throw new Error('缺少图片/视频输入');
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), params.timeoutMs);
  try {
    const res = await fetch(`${LLM_GATEWAY_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(LLM_GATEWAY_TOKEN ? { Authorization: `Bearer ${LLM_GATEWAY_TOKEN}` } : {}),
      },
      body: JSON.stringify({
        prompt: params.prompt,
        mode: params.mode,
        files: [{ type: params.mediaType, url }],
      }),
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`LLM网关响应 ${res.status}: ${text.slice(0, 200)}`);
    }
    return (await res.json()) as VisionAnalyzeResponse;
  } finally {
    clearTimeout(timer);
  }
}

// 网关优先 + 直连回退（网关禁用时即纯直连）
async function withLLMGateway<T>(direct: () => Promise<T>, viaGateway: () => Promise<T>): Promise<T> {
  if (!isLLMGatewayEnabled()) {
    return direct();
  }
  try {
    return await viaGateway();
  } catch (err) {
    console.warn('[llm] HARNESS网关调用失败，回退直连AI模块:', err);
    return direct();
  }
}

// 网关路径的空提示词兜底（网关要求 prompt 非空；直连路径由后端兜底）
const DEFAULT_IMAGE_PROMPT = '请描述这张图片的内容';
const DEFAULT_VIDEO_PROMPT = '请描述这个视频的内容';

// ========== 业务调用（签名保持不变；网关开启时优先走 HARNESS 网关）==========

// 视觉分析
export const visionAnalyze = (imageFile: File, prompt?: string) => {
  const direct = () => {
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
      timeout: 120000, // 120秒超时，大模型推理需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_IMAGE_PROMPT,
      file: imageFile,
      mediaType: 'image',
      timeoutMs: 120000,
    }),
  );
};

// 视觉推理
export const visionInference = (imageFile: File, prompt?: string) => {
  const direct = () => {
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
      timeout: 120000, // 120秒超时，大模型推理需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_IMAGE_PROMPT,
      mode: 'inference',
      file: imageFile,
      mediaType: 'image',
      timeoutMs: 120000,
    }),
  );
};

// 视觉理解
export const visionUnderstanding = (imageFile: File, prompt?: string) => {
  const direct = () => {
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
      timeout: 120000, // 120秒超时，大模型推理需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_IMAGE_PROMPT,
      mode: 'understanding',
      file: imageFile,
      mediaType: 'image',
      timeoutMs: 120000,
    }),
  );
};

// 深度思考
export const visionDeepThinking = (imageFile: File, prompt?: string) => {
  const direct = () => {
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
      timeout: 180000, // 180秒超时，深度思考模式需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_IMAGE_PROMPT,
      mode: 'deep-thinking',
      file: imageFile,
      mediaType: 'image',
      timeoutMs: 180000,
    }),
  );
};

// 视频推理
export const videoInference = (videoFile?: File, videoUrl?: string, prompt?: string) => {
  const direct = () => {
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
      timeout: 300000, // 300秒超时，视频推理需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_VIDEO_PROMPT,
      mode: 'inference',
      file: videoFile,
      mediaUrl: videoUrl,
      mediaType: 'video',
      timeoutMs: 300000,
    }),
  );
};

// 视频理解
export const videoUnderstanding = (videoFile?: File, videoUrl?: string, prompt?: string) => {
  const direct = () => {
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
      timeout: 300000, // 300秒超时，视频理解需要更长时间
    });
  };
  return withLLMGateway(direct, () =>
    callGatewayChat({
      prompt: prompt || DEFAULT_VIDEO_PROMPT,
      mode: 'understanding',
      file: videoFile,
      mediaUrl: videoUrl,
      mediaType: 'video',
      timeoutMs: 300000,
    }),
  );
};
