import { http } from '@/http/http'

export interface AlgorithmTask {
  id: number
  task_name: string
  task_code?: string
  task_type: 'realtime' | 'snap' | 'patrol'
  executor?: 'python' | 'cpp' | string
  runtime_bin_path?: string
  runtime_control_port?: number
  device_ids?: string[]
  device_names?: string[]
  model_ids?: number[]
  model_names?: string
  is_enabled: boolean
  status?: number
  exception_reason?: string
  total_frames?: number
  total_detections?: number
  total_captures?: number
  last_process_time?: string
  extract_interval?: number
  motion_gate_enabled?: boolean
  motion_gate_config?: { preset?: string }
  cron_expression?: string
  alert_event_enabled?: boolean
  schedule_policy?: 'local' | 'auto' | 'node'
  prefer_gpu?: boolean
  target_node_id?: number | null
}

export interface AlgorithmTaskListResult {
  data?: AlgorithmTask[]
  total?: number
}

export interface AlgorithmTaskListParams {
  pageNo?: number
  pageSize?: number
  search?: string
  device_id?: string
  task_type?: 'realtime' | 'snap' | 'patrol'
  is_enabled?: boolean
}

/** 算法任务分页列表 */
export function listAlgorithmTasks(params?: AlgorithmTaskListParams) {
  return http.get<AlgorithmTaskListResult>('/video/algorithm/task/list', params)
}

/** 获取算法任务详情 */
export function getAlgorithmTask(taskId: number) {
  return http.get<AlgorithmTask>(`/video/algorithm/task/${taskId}`)
}

/** 启动算法任务 */
export function startAlgorithmTask(taskId: number) {
  return http.post<AlgorithmTask>(`/video/algorithm/task/${taskId}/start`, {})
}

/** 停止算法任务 */
export function stopAlgorithmTask(taskId: number) {
  return http.post<AlgorithmTask>(`/video/algorithm/task/${taskId}/stop`, {})
}

/** 重启算法任务 */
export function restartAlgorithmTask(taskId: number) {
  return http.post<AlgorithmTask>(`/video/algorithm/task/${taskId}/restart`, {})
}

export interface AlgorithmTaskPayload {
  task_name: string
  task_type?: 'realtime' | 'snap' | 'patrol'
  device_ids?: string[]
  model_ids?: number[]
  schedule_policy?: 'local' | 'auto' | 'node'
  prefer_gpu?: boolean
  target_node_id?: number | null
  extract_interval?: number
  motion_gate_enabled?: boolean
  motion_gate_config?: { preset?: string }
  cron_expression?: string
  patrol_interval_sec?: number
  alert_event_enabled?: boolean
  is_enabled?: boolean
}

/** 创建算法任务 */
export function createAlgorithmTask(data: AlgorithmTaskPayload) {
  return http.post<AlgorithmTask>('/video/algorithm/task', data, undefined, undefined, { hideErrorToast: true })
}

/** 更新算法任务 */
export function updateAlgorithmTask(taskId: number, data: Partial<AlgorithmTaskPayload>) {
  return http.put<AlgorithmTask>(`/video/algorithm/task/${taskId}`, data, undefined, undefined, { hideErrorToast: true })
}

/** 删除算法任务 */
export function deleteAlgorithmTask(taskId: number) {
  return http.delete(`/video/algorithm/task/${taskId}`)
}

export function getAlgorithmTaskTypeText(type?: string, executor?: string): string {
  let base = '-'
  if (type === 'realtime')
    base = '实时'
  else if (type === 'snap')
    base = '抓拍'
  else if (type === 'patrol')
    base = '巡检'
  else if (type)
    base = type
  const ex = String(executor || 'python').toLowerCase()
  if (base !== '-' && (ex === 'cpp' || ex === 'c++' || ex === 'runtime' || ex === 'cxx'))
    return `${base}(高性能)`
  return base
}
