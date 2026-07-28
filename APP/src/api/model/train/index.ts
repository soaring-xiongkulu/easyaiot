import { useTokenStore, useUserStore } from '@/store'
import { getEnvBaseUrl } from '@/utils'
import { http } from '@/http/http'

export interface TrainTask {
  id: number
  name?: string
  task_name?: string
  dataset_name?: string
  dataset_version?: string
  start_time?: string
  progress?: number
  completed_epochs?: number
  total_epochs?: number
  current_epoch?: number
  current_batch?: number
  total_batches?: number
  progress_phase?: 'train' | 'validation' | 'completed' | string
  progress_updated_at?: number
  progress_message?: string
  status?: string
  schedule_policy?: string
  service_server_ip?: string
  minio_model_path?: string
  can_resume?: boolean
  published_model_id?: number | null
  hyperparameters?: unknown
}

export interface TrainTaskListResult {
  data?: TrainTask[]
  list?: TrainTask[]
  total?: number
}

export interface TrainTaskListParams {
  pageNo?: number
  pageSize?: number
  task_name?: string
  progress_filter?: string
}

/** 训练任务分页列表 */
export function getTrainTaskPage(params?: TrainTaskListParams) {
  return http.get<TrainTaskListResult>('/model/train_task/list', params)
}

/** 获取训练任务详情 */
export function getTrainTaskDetail(taskId: number) {
  return http.get<TrainTask>(`/model/train_task/${taskId}`)
}

/** 停止训练任务 */
export function stopTrain(taskId: number) {
  return http.post(`/model/train_task/${taskId}/stop`)
}

/** 获取训练日志 */
export function getTrainLogs(taskId: number) {
  return http.get<string | { logs?: string }>(`/model/train_task/${taskId}/logs`)
}

/** 获取训练状态 */
export function getTrainStatus(taskId: number) {
  return http.get<TrainTask>(`/model/train_task/${taskId}/status`)
}

/** 删除训练任务 */
export function deleteTrainTask(taskId: number) {
  return http.delete(`/model/train_task/delete/${taskId}`)
}

export type TrainSchedulePolicy = 'local' | 'auto' | 'node'

export interface TrainStartConfig {
  epochs: number
  batch_size: number
  imgsz: number
  taskName?: string
  modelPath: string
  datasetSource?: 'local' | 'cloud'
  datasetPath: string
  datasetName?: string
  datasetVersion?: string
  use_gpu?: boolean
  gpu_ids?: number[]
  schedulePolicy?: TrainSchedulePolicy
  schedule_policy?: TrainSchedulePolicy
  targetNodeId?: number | null
  target_node_id?: number | null
  taskId?: number
  resume?: boolean
}

/** 启动 / 续训 / 重训 */
export function startTrain(config: TrainStartConfig) {
  return http.post('/model/train_task/start', config)
}

export interface GpuDeviceInfo {
  index: number
  name: string
  total_memory_gb: number
  free_memory_gb?: number
  used_memory_gb?: number
}

export interface GpuStatusData {
  cuda_available: boolean
  visible_gpu_ids: number[]
  multi_gpu: boolean
  devices: GpuDeviceInfo[]
}

/** GPU 状态探测 */
export function getTrainGpuStatus() {
  return http.get<GpuStatusData>('/model/train_task/gpu/status')
}

/** 发布训练权重到模型管理 */
export function publishTrainTask(
  taskId: number,
  params?: { name?: string, version?: string, description?: string, auto_increment?: boolean },
) {
  return http.post(`/model/train_task/${taskId}/publish`, params || {})
}

function resolveUploadUrl(path: string): string {
  // #ifdef H5
  if (JSON.parse(import.meta.env.VITE_APP_PROXY_ENABLE)) {
    return import.meta.env.VITE_APP_PROXY_PREFIX + path
  }
  // #endif
  return getEnvBaseUrl() + path
}

/** 上传本地 YOLO 数据集 ZIP（最大 5GB，超时 1h） */
export function uploadTrainDataset(filePath: string, fileName?: string): Promise<{ path: string, fileName?: string }> {
  return new Promise((resolve, reject) => {
    const tokenStore = useTokenStore()
    const token = tokenStore.updateNowTime().validToken
    const url = resolveUploadUrl('/model/train_task/dataset/upload')
    const header: Record<string, string> = {
      Authorization: token ? `Bearer ${token}` : '',
    }
    if (import.meta.env.VITE_APP_TENANT_ENABLE === 'true') {
      const tenantId = useUserStore().tenantId
      if (tenantId)
        header['tenant-id'] = String(tenantId)
    }

    uni.uploadFile({
      url,
      filePath,
      name: 'file',
      header,
      timeout: 3600000,
      success: (res) => {
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          if (data.code === 0 || data.code === 200) {
            const payload = data.data ?? data
            resolve({ path: payload.path, fileName: payload.fileName })
          }
          else {
            reject(new Error(data.msg || data.message || '上传失败'))
          }
        }
        catch (e) {
          reject(e)
        }
      },
      fail: reject,
    })
  })
}
