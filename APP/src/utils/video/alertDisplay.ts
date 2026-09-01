/** 告警列表展示与筛选共用常量（对齐 WEB alertDisplay.ts） */

export const ALERT_EVENT_OPTIONS = [
  { value: '', label: '全部' },
  { value: '行人检测', label: '行人检测' },
  { value: 'face_library_match', label: '人脸库匹配' },
  { value: 'plate_library_match', label: '车牌库匹配' },
] as const

const ALERT_EVENT_LABEL_MAP: Record<string, string> = {
  face_library_match: '人脸库匹配',
  plate_library_match: '车牌库匹配',
  行人检测: '行人检测',
}

export function formatAlertEvent(event?: string | null): string {
  if (!event)
    return '-'
  return ALERT_EVENT_LABEL_MAP[event] || event
}

export function getAlertEventTagType(event?: string | null): 'primary' | 'success' | 'warning' | 'danger' | 'default' {
  if (event === 'face_library_match')
    return 'primary'
  if (event === 'plate_library_match')
    return 'success'
  if (event === '行人检测')
    return 'warning'
  return 'default'
}

type AlertPersonRecord = {
  event?: string | null
  matched_person_name?: string | null
  source_event?: string | null
}

export function formatAlertListTitle(record: AlertPersonRecord): string {
  const personName = record.matched_person_name ? String(record.matched_person_name) : ''
  const sourceEvent = record.source_event ? String(record.source_event) : ''
  if (personName && sourceEvent)
    return `${personName} · ${formatAlertEvent(sourceEvent)}`
  if (personName)
    return `${formatAlertEvent(record.event)} · ${personName}`
  return formatAlertEvent(record.event)
}

export function getTaskTypeText(taskType?: string | null): string {
  if (taskType === 'realtime')
    return '实时'
  if (taskType === 'snap' || taskType === 'snapshot')
    return '抓拍'
  if (taskType === 'patrol')
    return '巡检'
  return taskType || '-'
}

/** 是否为抓拍类任务（无关联告警录像） */
export function isSnapAlertTask(record: {
  task_type?: string | null
  information?: unknown
}): boolean {
  let taskType = record.task_type
  if (!taskType && record.information) {
    if (typeof record.information === 'object' && record.information !== null) {
      taskType = (record.information as { task_type?: string }).task_type
    }
    else if (typeof record.information === 'string') {
      try {
        const info = JSON.parse(record.information)
        taskType = info?.task_type
      }
      catch {
        // ignore
      }
    }
  }
  return taskType === 'snap' || taskType === 'snapshot'
}

export function getTaskTypeTagType(taskType?: string | null): 'primary' | 'success' | 'warning' | 'danger' | 'default' {
  if (taskType === 'realtime')
    return 'primary'
  if (taskType === 'snap' || taskType === 'snapshot')
    return 'success'
  if (taskType === 'patrol')
    return 'warning'
  return 'default'
}

/** 大模型（LLM）研判状态映射（与 iot-sink 回写枚举一致） */
const LLM_JUDGE_LABEL_MAP: Record<string, string> = {
  not_sampled: '未抽检',
  pending: '研判中',
  confirmed: '确认成立',
  rejected: '误报',
  error: '研判失败',
  rate_limited: '限流跳过',
  skipped: '已跳过',
}

/** 已进入大模型研判队列的状态（被抽检，含排队中与失败） */
const LLM_SAMPLED_STATUSES = ['confirmed', 'rejected', 'pending', 'error']

/** 告警是否已被 AI 抽检（决定标签显示） */
export function isLlmSampled(status?: string | null): boolean {
  return !!status && LLM_SAMPLED_STATUSES.includes(String(status))
}

export function formatLlmJudgeStatus(status?: string | null): string {
  if (!status)
    return ''
  return LLM_JUDGE_LABEL_MAP[status] || status
}

export function getLlmJudgeTagType(status?: string | null): 'primary' | 'success' | 'warning' | 'danger' | 'default' {
  if (status === 'confirmed')
    return 'success'
  if (status === 'rejected' || status === 'rate_limited' || status === 'skipped')
    return 'warning'
  if (status === 'error')
    return 'danger'
  if (status === 'pending')
    return 'primary'
  return 'default'
}

/** 研判结论文本（来自 llm_judge_detail 快照，兼容字符串与对象） */
export function formatLlmJudgeConclusion(detail?: unknown): string {
  if (!detail)
    return ''
  if (typeof detail === 'string') {
    try {
      const parsed = JSON.parse(detail)
      return formatLlmJudgeConclusion(parsed)
    }
    catch {
      return detail
    }
  }
  if (typeof detail !== 'object')
    return String(detail)
  const d = detail as Record<string, unknown>
  const parts: string[] = []
  if (typeof d.confidence === 'number')
    parts.push(`置信度 ${Math.round(d.confidence * 100)}%`)
  if (d.reason)
    parts.push(String(d.reason))
  return parts.join(' · ')
}
