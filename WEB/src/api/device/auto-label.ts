import { defHttp } from '@/utils/http/axios';
import {
  exportAnnotationDataset,
  extractAnnotationFrames,
  importAnnotationLabelme,
  type DatasetAnnotationExportParams,
} from '@/api/device/dataset';

enum Api {
  /** AI 推理与自动标注任务（model-server） */
  AutoLabel = '/model/dataset',
  Model = '/model',
  /** @deprecated 旧版依赖部署推理服务，保留兼容 */
  AIService = '/model/deploy_service',
}

const commonApi = (
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  params = {},
  headers = {},
  isTransformResponse = true,
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method](
    {
      url,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        ...headers,
      },
      ...params,
    },
    {
      isTransformResponse: isTransformResponse,
    },
  );
};

// —— AI 自动标注（直连 model-server 模型推理，无需部署推理服务）——

export interface StartAutoLabelParams {
  model_id?: number;
  label_mode?: 'yolo' | 'sam';
  text_prompts?: string[];
  confidence_threshold?: number;
  annotation_type?: 'rectangle' | 'polygon';
  return_masks?: boolean;
  sample_selection?: string;
  /** @deprecated 请使用 model_id */
  model_service_id?: number;
}

export interface StartSamBootstrapParams {
  text_prompts: string[];
  bootstrap_limit?: number;
  bootstrap_selection?: 'unlabeled_first' | 'random' | 'all';
  confidence_threshold?: number;
  annotation_type?: 'rectangle' | 'polygon';
  return_masks?: boolean;
}

export const startAutoLabel = (datasetId: number, data: StartAutoLabelParams | Record<string, unknown>) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/start`, { data });
};

export interface AutoLabelStrategy {
  bootstrap_sam_limit?: number;
  yolo_iterate_every?: number;
  auto_train_yolo?: boolean;
  skip_sam_cold_start?: boolean;
  initial_model_id?: number | null;
  /** 自动训练微调基座（模型管理）；不填则首轮用 model_arch */
  pretrain_model_id?: number | null;
  /** 官方预训练：yolo26n / yolo11n / yolov8n（内置） */
  model_arch?: string;
  sam_supplement_enabled?: boolean;
  sam_supplement_until_labeled?: number;
  sam_supplement_stop_map?: number;
  sam_supplement_min_detections?: number;
  yolo_confidence?: number;
  sam_confidence?: number;
  /** SAM 冷启动最低识别率（0–1），低于此值建议改用手动/YOLO 自动标注 */
  sam_bootstrap_min_hit_rate?: number;
  /** 模型更新历史保留条数（不设则读服务端 AUTO_LABEL_MODEL_HISTORY_MAX） */
  model_history_max?: number | null;
}

export interface StartSamPipelineParams {
  text_prompts: string[];
  duration_hours?: number;
  capture_interval_sec?: number;
  confidence_threshold?: number;
  annotation_type?: 'rectangle' | 'polygon';
  return_masks?: boolean;
  auto_export?: boolean;
  keep_annotated_images_only?: boolean;
  train_ratio?: number;
  val_ratio?: number;
  test_ratio?: number;
  execution_mode?: 'local' | 'cluster';
  frame_task_ids?: number[];
  queue_priority?: number;
  strategy?: AutoLabelStrategy;
  model_id?: number;
}

/** 无人值守扩充：多路摄像头分布式自动打标，写入指定数据集 */
export const startSamPipeline = (datasetId: number, data: StartSamPipelineParams) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/pipeline/start`, { data });
};

export const getAutoLabelSubtasks = (datasetId: number, taskId: number) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/task/${taskId}/subtasks`);
};

export const getAutoLabelQueue = (datasetId: number, params: Record<string, unknown> = {}) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/queue`, { params });
};

export const pauseAutoLabelTask = (datasetId: number, taskId: number) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/task/${taskId}/pause`);
};

export const resumeAutoLabelTask = (datasetId: number, taskId: number) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/task/${taskId}/resume`);
};

export const cancelAutoLabelTask = (datasetId: number, taskId: number) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/task/${taskId}/cancel`);
};

export const startSamBootstrap = (datasetId: number, data: StartSamBootstrapParams) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/bootstrap/start`, { data });
};

export const getSamBootstrapStatus = (datasetId: number) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/bootstrap/status`);
};

export const completeSamBootstrapReview = (
  datasetId: number,
  data: { review_passed: boolean; reviewer_note?: string },
) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/bootstrap/complete-review`, { data });
};

export interface SamBootstrapStatus {
  has_task?: boolean;
  task_id?: number;
  status?: string;
  phase?: string;
  processed_images?: number;
  total_images?: number;
  success_count?: number;
  bootstrap_limit?: number;
  bootstrap_done?: boolean;
  review_passed?: boolean;
  ready_for_train?: boolean;
  awaiting_sam_review?: boolean;
  sam_hit_count?: number;
  sam_empty_count?: number;
  recognition_rate?: number;
  recognition_rate_pct?: number;
  min_hit_rate?: number;
  min_hit_rate_pct?: number;
  sam_quality_passed?: boolean;
  review_recommended?: boolean;
}

export const resetSamBootstrapAnnotations = (datasetId: number) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/bootstrap/reset`);
};

export interface AutoLabelModelHistoryItem {
  id: number;
  dataset_id: number;
  model_id?: number;
  train_task_id?: number;
  source_model_id?: number;
  version_no: number;
  annotated_count: number;
  class_names?: string[];
  map50?: number;
  status: 'PENDING' | 'TRAINING' | 'COMPLETED' | 'FAILED';
  trigger_source?: string;
  error_message?: string;
  created_at?: string;
  completed_at?: string;
}

export interface AutoLabelModelHistoryResult {
  current_model_id?: number;
  current_model?: { id: number; name: string; version?: string };
  history: AutoLabelModelHistoryItem[];
  max_history: number;
}

export const getAutoLabelModelHistory = (datasetId: number) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/model/history`);
};

export interface UpdateAutoLabelModelParams {
  base_model_id?: number;
  model_id?: number;
  train_epochs?: number;
  model_history_max?: number;
  strategy?: Partial<AutoLabelStrategy>;
}

export const updateAutoLabelModel = (datasetId: number, data: UpdateAutoLabelModelParams = {}) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/model/update`, { data });
};

export const getAutoLabelTask = (datasetId: number, taskId: number) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/task/${taskId}`);
};

export const listAutoLabelTasks = (datasetId: number, params: any) => {
  return commonApi('get', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/tasks`, { params });
};

export const getAutoLabelModelList = (params = {}) => {
  return commonApi('get', `${Api.Model}/list`, { params });
};

/** @deprecated 自动标注已改为直连模型，请使用 getAutoLabelModelList */
export const getAIServiceList = (params = {}) => {
  return commonApi('get', `${Api.AIService}/list`, { params }, {}, false);
};

export const labelSingleImage = (datasetId: number, imageId: number, data: Record<string, unknown>) => {
  return commonApi('post', `${Api.AutoLabel}/dataset/${datasetId}/auto-label/image/${imageId}`, { data });
};

// —— 以下导入/导出已迁移至 iot-dataset（/dataset/{id}/annotation/*），保留别名兼容旧调用 ——

/** @deprecated 请使用 `exportAnnotationDataset`（@/api/device/dataset） */
export const exportLabeledDataset = (datasetId: number, params: Record<string, unknown>) => {
  const body: DatasetAnnotationExportParams = {
    trainRatio: Number(params.train_ratio ?? 0.7),
    valRatio: Number(params.val_ratio ?? 0.2),
    testRatio: Number(params.test_ratio ?? 0.1),
    sampleSelection: (params.sample_selection ?? params.sample_type ?? 'all') as DatasetAnnotationExportParams['sampleSelection'],
    selectedClasses: (params.selected_classes as string[]) ?? [],
    exportPrefix: String(params.export_prefix ?? params.file_prefix ?? ''),
  };
  return exportAnnotationDataset(datasetId, body);
};

/** @deprecated 请使用 `extractAnnotationFrames`（@/api/device/dataset） */
export const extractFramesFromVideo = extractAnnotationFrames;

/** @deprecated 请使用 `importAnnotationLabelme`（@/api/device/dataset） */
export const importLabelmeDataset = importAnnotationLabelme;
