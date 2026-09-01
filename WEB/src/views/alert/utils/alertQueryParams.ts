import type { AlertMapQuery } from '@/components/TiandituMap';
import { normalizeAlertBusinessTagsParam } from '@/views/alert/alertDisplay';

const TIME_RANGE_KEY = '[begin_datetime, end_datetime]';

/** 将表单/表格原始参数规范化为告警 API 查询参数 */
export function normalizeAlertQueryParams(
  raw: Record<string, unknown>,
  routeTaskName?: string,
): Record<string, unknown> {
  const p = { ...raw };

  if (p[TIME_RANGE_KEY] && Array.isArray(p[TIME_RANGE_KEY])) {
    const [begin, end] = p[TIME_RANGE_KEY] as unknown[];
    if (begin && typeof (begin as { format?: (f: string) => string }).format === 'function') {
      p.begin_datetime = (begin as { format: (f: string) => string }).format('YYYY-MM-DD HH:mm:ss');
    } else if (begin) {
      p.begin_datetime = begin;
    }
    if (end && typeof (end as { format?: (f: string) => string }).format === 'function') {
      p.end_datetime = (end as { format: (f: string) => string }).format('YYYY-MM-DD HH:mm:ss');
    } else if (end) {
      p.end_datetime = end;
    }
    delete p[TIME_RANGE_KEY];
  }

  if (p.begin_datetime && typeof p.begin_datetime === 'object' && typeof (p.begin_datetime as { format?: (f: string) => string }).format === 'function') {
    p.begin_datetime = (p.begin_datetime as { format: (f: string) => string }).format('YYYY-MM-DD HH:mm:ss');
  }
  if (p.end_datetime && typeof p.end_datetime === 'object' && typeof (p.end_datetime as { format?: (f: string) => string }).format === 'function') {
    p.end_datetime = (p.end_datetime as { format: (f: string) => string }).format('YYYY-MM-DD HH:mm:ss');
  }

  if (p.task_name) {
    p.task_name = String(p.task_name).trim();
    if (!p.task_name) delete p.task_name;
  }

  const businessTags = normalizeAlertBusinessTagsParam(p.business_tags);
  if (businessTags) {
    p.business_tags = businessTags;
  } else {
    delete p.business_tags;
  }

  if (routeTaskName && !p.task_name) {
    p.task_name = String(routeTaskName).trim();
  }

  if (p.device_id !== undefined && p.device_id !== null && String(p.device_id).trim() === '') {
    delete p.device_id;
  }

  if (p.begin_datetime === null || p.begin_datetime === undefined || p.begin_datetime === '') {
    delete p.begin_datetime;
  }
  if (p.end_datetime === null || p.end_datetime === undefined || p.end_datetime === '') {
    delete p.end_datetime;
  }
  if (p.llm_judge_status === null || p.llm_judge_status === undefined || p.llm_judge_status === '') {
    delete p.llm_judge_status;
  }

  return p;
}

/** 提取不含分页的筛选快照，供翻页/地图模式复用 */
export function snapshotAlertFilters(processed: Record<string, unknown>): Record<string, unknown> {
  const filterParams: Record<string, unknown> = {};
  if (processed.begin_datetime) filterParams.begin_datetime = processed.begin_datetime;
  if (processed.end_datetime) filterParams.end_datetime = processed.end_datetime;
  if (processed.task_name) filterParams.task_name = processed.task_name;
  if (processed.device_id !== undefined && processed.device_id !== '' && processed.device_id !== null) {
    filterParams.device_id = processed.device_id;
  }
  if (processed.event !== undefined && processed.event !== null && processed.event !== '') {
    filterParams.event = processed.event;
  }
  if (processed.business_tags) {
    filterParams.business_tags = processed.business_tags;
  }
  if (processed.llm_judge_status !== undefined && processed.llm_judge_status !== null && processed.llm_judge_status !== '') {
    filterParams.llm_judge_status = processed.llm_judge_status;
  }
  return filterParams;
}

export function hasAlertFilterParams(p: Record<string, unknown>): boolean {
  return !!(
    p.begin_datetime ||
    p.end_datetime ||
    p.task_name ||
    p.device_id ||
    p.event ||
    (p.business_tags && String(p.business_tags).trim()) ||
    (p.llm_judge_status && String(p.llm_judge_status).trim())
  );
}

/** 合并翻页参数与持久化筛选 */
export function mergeAlertFetchParams(
  p: Record<string, unknown>,
  lastFilters: Record<string, unknown>,
): Record<string, unknown> {
  const normalized = normalizeAlertQueryParams(p);
  if (!hasAlertFilterParams(normalized) && Object.keys(lastFilters).length > 0) {
    return { ...normalized, ...lastFilters };
  }
  return normalized;
}

/** 转为地图组件 query（较大 pageSize） */
export function toAlertMapQuery(filters: Record<string, unknown>, pageSize = 500): AlertMapQuery & Record<string, unknown> {
  return {
    pageNo: 1,
    pageSize,
    device_id: filters.device_id as string | undefined,
    begin_datetime: filters.begin_datetime as string | undefined,
    end_datetime: filters.end_datetime as string | undefined,
    event: filters.event as string | undefined,
    task_name: filters.task_name as string | undefined,
    business_tags: filters.business_tags as string | undefined,
  };
}
