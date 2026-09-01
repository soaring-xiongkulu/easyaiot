import { http } from '@/http/http'

export interface AlertRecord {
  id?: number | string
  device_id?: string
  device_name?: string
  time?: string
  task_name?: string
  event?: string
  task_type?: string
  object?: string
  matched_person_name?: string
  source_event?: string
  business_tags?: string[]
  region?: string | null
  image_url?: string
  record_path?: string
  information?: unknown
  /** 大模型（LLM）研判状态：not_sampled/pending/confirmed/rejected/error/rate_limited/skipped */
  llm_judge_status?: string | null
  llm_judge_detail?: Record<string, unknown> | null
}

export interface AlertListResult {
  alert_list?: AlertRecord[]
  total?: number
}

export interface AlertListParams {
  pageNo?: number
  pageSize?: number
  task_name?: string
  device_id?: string
  event?: string
  business_tags?: string
  begin_datetime?: string
  end_datetime?: string
}

/** 分页查询告警事件 */
export function queryAlarmList(params: AlertListParams) {
  return http.get<AlertListResult>('/video/alert/page', params)
}

/** 清空全部告警 */
export function clearAllAlarms() {
  return http.delete<boolean>('/video/alert/clear/all')
}

/** 删除单条告警 */
export function deleteAlarm(id: number | string) {
  return http.delete<boolean>(`/video/alert/delete/${id}`)
}

/** 告警统计数量 */
export function getAlertCount(params?: { device_id?: string }) {
  return http.get<{ count?: number }>('/video/alert/count', params)
}

export interface AlertRecordQueryResult {
  video_url?: string
  file_path?: string
  url?: string
}

/** 根据设备 ID 与告警时间查询录像 */
export function queryAlertRecord(params: {
  device_id: string
  alert_time: string
  time_range?: number
  alert_id?: number | string
}) {
  return http.get<AlertRecordQueryResult>('/video/alert/record/query', params)
}
