/**
 * 算法任务、抽帧器、排序器管理接口
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
import { commonApi } from '../index';

const ALGORITHM_PREFIX = '/video/algorithm';

// ====================== 算法任务管理接口 ======================
export interface AlgorithmTask {
  id: number;
  task_name: string;
  task_code: string;
  device_ids?: string[];
  device_names?: string[];
  extractor_id?: number;
  extractor_name?: string;
  sorter_id?: number;
  sorter_name?: string;
  status: number; // 0:正常, 1:异常
  is_enabled: boolean;
  run_status: string; // running:运行中, stopped:已停止, restarting:重启中
  exception_reason?: string;
  total_frames: number;
  total_detections: number;
  last_process_time?: string;
  last_success_time?: string;
  description?: string;
  algorithm_services?: AlgorithmModelService[];
  created_at?: string;
  updated_at?: string;
}

export interface AlgorithmTaskListResponse {
  code: number;
  msg: string;
  data: AlgorithmTask[];
  total: number;
}

export const listAlgorithmTasks = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  device_id?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<AlgorithmTaskListResponse>('get', `${ALGORITHM_PREFIX}/task/list`, { params });
};

export const getAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}`
  );
};

export const createAlgorithmTask = (data: {
  task_name: string;
  extractor_id?: number;
  sorter_id?: number;
  device_ids?: string[];
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task`,
    { data }
  );
};

export const updateAlgorithmTask = (task_id: number, data: Partial<AlgorithmTask>) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'put',
    `${ALGORITHM_PREFIX}/task/${task_id}`,
    { data }
  );
};

export const deleteAlgorithmTask = (task_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/task/${task_id}`);
};

export const startAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/start`
  );
};

export const stopAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/stop`
  );
};

export const restartAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/restart`
  );
};

// ====================== 抽帧器管理接口 ======================
export interface FrameExtractor {
  id: number;
  extractor_name: string;
  extractor_code: string;
  extractor_type: string; // interval:按间隔, time:按时间
  interval: number;
  description?: string;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FrameExtractorListResponse {
  code: number;
  msg: string;
  data: FrameExtractor[];
  total: number;
}

export const listFrameExtractors = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi<FrameExtractorListResponse>('get', `${ALGORITHM_PREFIX}/extractor/list`, { params });
};

export const getFrameExtractor = (extractor_id: number) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'get',
    `${ALGORITHM_PREFIX}/extractor/${extractor_id}`
  );
};

export const createFrameExtractor = (data: {
  extractor_name: string;
  extractor_type?: string;
  interval?: number;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'post',
    `${ALGORITHM_PREFIX}/extractor`,
    { data }
  );
};

export const updateFrameExtractor = (extractor_id: number, data: Partial<FrameExtractor>) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'put',
    `${ALGORITHM_PREFIX}/extractor/${extractor_id}`,
    { data }
  );
};

export const deleteFrameExtractor = (extractor_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/extractor/${extractor_id}`);
};

// ====================== 排序器管理接口 ======================
export interface Sorter {
  id: number;
  sorter_name: string;
  sorter_code: string;
  sorter_type: string; // confidence:置信度, time:时间, score:分数
  sort_order: string; // asc:升序, desc:降序
  description?: string;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SorterListResponse {
  code: number;
  msg: string;
  data: Sorter[];
  total: number;
}

export const listSorters = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi<SorterListResponse>('get', `${ALGORITHM_PREFIX}/sorter/list`, { params });
};

export const getSorter = (sorter_id: number) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'get',
    `${ALGORITHM_PREFIX}/sorter/${sorter_id}`
  );
};

export const createSorter = (data: {
  sorter_name: string;
  sorter_type?: string;
  sort_order?: string;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'post',
    `${ALGORITHM_PREFIX}/sorter`,
    { data }
  );
};

export const updateSorter = (sorter_id: number, data: Partial<Sorter>) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'put',
    `${ALGORITHM_PREFIX}/sorter/${sorter_id}`,
    { data }
  );
};

export const deleteSorter = (sorter_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/sorter/${sorter_id}`);
};

// ====================== 算法任务的服务管理接口 ======================
export interface AlgorithmModelService {
  id: number;
  task_id: number;
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method: string;
  request_headers?: any;
  request_body_template?: any;
  timeout: number;
  is_enabled: boolean;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export const listTaskServices = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService[] }>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/services`
  );
};

export const createTaskService = (task_id: number, data: {
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: any;
  request_body_template?: any;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/service`,
    { data }
  );
};

export const updateTaskService = (service_id: number, data: Partial<AlgorithmModelService>) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService }>(
    'put',
    `${ALGORITHM_PREFIX}/task/service/${service_id}`,
    { data }
  );
};

export const deleteTaskService = (service_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/task/service/${service_id}`);
};

