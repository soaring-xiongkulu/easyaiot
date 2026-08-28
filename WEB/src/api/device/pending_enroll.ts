/**
 * 待入库工作台接口（未匹配人脸/车牌目标的暂存、标注修正与确认入库）
 *
 * 人脸线与车牌线为两条独立业务线，接口同构：
 *  - face  → /video/face/pending-enroll/...（特征向量入库）
 *  - plate → /video/plate/pending-enroll/...（车牌号入库）
 */
import { defHttp } from '@/utils/http/axios';
import { parseFaceApiError } from '@/api/device/face_library';

export type PendingEnrollKind = 'face' | 'plate';

export type PendingEnrollStatus = 'pending' | 'enrolled' | 'discarded';

const PREFIX_MAP: Record<PendingEnrollKind, string> = {
  face: '/video/face/pending-enroll',
  plate: '/video/plate/pending-enroll',
};

const SUCCESS_CODES = new Set([0, 200]);

/** AI 检测框（整帧像素坐标） */
export interface PendingEnrollBbox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface PendingEnrollStats {
  pending: number;
  enrolled: number;
  discarded: number;
}

export interface PendingEnrollRecord {
  id: number;
  task_id?: number;
  task_name?: string;
  device_id: string;
  device_name?: string;
  /** 人脸线：OCR/匹配信息 */
  plate_no?: string;
  plate_color?: string;
  detect_conf?: number;
  similarity?: number;
  matched?: boolean;
  matched_person_name?: string;
  enroll_status: PendingEnrollStatus;
  /** AI 标注框 [x1, y1, x2, y2]（整帧像素坐标） */
  bbox?: [number, number, number, number] | null;
  frame_image_path?: string | null;
  frame_image_url?: string | null;
  /** 整帧是否仍可用（过期后只能基于裁剪图入库，无法修正标注框） */
  frame_available: boolean;
  frame_width?: number;
  frame_height?: number;
  crop_image_path?: string | null;
  crop_image_url?: string | null;
  enroll_target_library_id?: number | null;
  enroll_person_id?: number | null;
  enroll_entry_id?: number | null;
  enroll_time?: string | null;
  created_at?: string;
}

export interface PendingEnrollListResult {
  code: number;
  msg: string;
  list: PendingEnrollRecord[];
  total: number;
  page: number;
  page_size: number;
  stats: PendingEnrollStats;
}

export interface PendingEnrollListParams {
  status?: PendingEnrollStatus | 'all';
  page?: number;
  pageSize?: number;
  search?: string;
  device_id?: string;
  task_id?: number;
}

function prefixOf(kind: PendingEnrollKind) {
  return PREFIX_MAP[kind];
}

async function mutationApi<T = unknown>(
  kind: PendingEnrollKind,
  url: string,
  data?: unknown,
): Promise<{ code: number; msg: string; data?: T }> {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  try {
    const res = await defHttp.post(
      {
        url: `${prefixOf(kind)}${url}`,
        data,
        headers: {
          // @ts-ignore
          ignoreCancelToken: true,
        },
      },
      { isTransformResponse: false, errorMessageMode: 'none' },
    );
    const body = ((res as { data?: { code: number; msg: string; data?: T } })?.data ?? res) as {
      code: number;
      msg: string;
      data?: T;
    };
    if (!SUCCESS_CODES.has(body?.code)) {
      throw new Error(body?.msg || '请求失败');
    }
    return body;
  } catch (error) {
    throw new Error(parseFaceApiError(error, '请求失败'));
  }
}

export const listPendingRecords = async (
  kind: PendingEnrollKind,
  params?: PendingEnrollListParams,
): Promise<PendingEnrollListResult> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const res = await defHttp.get<PendingEnrollListResult>(
    {
      url: `${prefixOf(kind)}/records`,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: false, errorMessageMode: 'none' },
  );
  // isTransformResponse:false 时 defHttp 返回完整 AxiosResponse，业务体在其 data 字段
  return (((res as { data?: PendingEnrollListResult })?.data ?? res) as PendingEnrollListResult);
};

export const getPendingStats = async (
  kind: PendingEnrollKind,
): Promise<{ code: number; msg: string; data: PendingEnrollStats }> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const res = await defHttp.get<{ code: number; msg: string; data: PendingEnrollStats }>(
    {
      url: `${prefixOf(kind)}/stats`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: false, errorMessageMode: 'none' },
  );
  return (((res as { data?: { code: number; msg: string; data: PendingEnrollStats } })?.data ??
    res) as { code: number; msg: string; data: PendingEnrollStats });
};

export const getPendingRecordDetail = async (
  kind: PendingEnrollKind,
  recordId: number,
): Promise<{ code: number; msg: string; data: PendingEnrollRecord }> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const res = await defHttp.get<{ code: number; msg: string; data: PendingEnrollRecord }>(
    {
      url: `${prefixOf(kind)}/records/${recordId}`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: false, errorMessageMode: 'none' },
  );
  return (((res as { data?: { code: number; msg: string; data: PendingEnrollRecord } })?.data ??
    res) as { code: number; msg: string; data: PendingEnrollRecord });
};

export const batchDiscardPendingRecords = (kind: PendingEnrollKind, ids: number[]) =>
  mutationApi<{ changed: number }>(kind, '/records/batch-discard', { ids });

export const batchRestorePendingRecords = (kind: PendingEnrollKind, ids: number[]) =>
  mutationApi<{ changed: number }>(kind, '/records/batch-restore', { ids });

export const batchDeletePendingRecords = (kind: PendingEnrollKind, ids: number[]) =>
  mutationApi<{ deleted: number }>(kind, '/records/batch-delete', { ids });

/**
 * 按修正后的标注框请求提取区域 JPEG 预览，返回对象 URL（调用方负责 revoke）。
 */
export const fetchExtractPreviewUrl = async (
  kind: PendingEnrollKind,
  recordId: number,
  bbox?: [number, number, number, number] | null,
): Promise<string> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const [x1, y1, x2, y2] = bbox ?? [];
  const blob = (await defHttp.post(
    {
      url: `${prefixOf(kind)}/records/${recordId}/extract-preview`,
      data: bbox?.length === 4 ? { bbox: [x1, y1, x2, y2] } : {},
      responseType: 'blob',
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: false, errorMessageMode: 'none' },
  )) as unknown as Blob;
  if (!(blob instanceof Blob)) {
    throw new Error('提取预览失败');
  }
  return URL.createObjectURL(blob);
};

/** 单条确认入库入参 */
export interface PendingEnrollPayload {
  record_id: number;
  /** 目标库 ID */
  library_id: number;
  /** 标注框（整帧像素坐标），不传则使用 AI 原始框 */
  bbox?: [number, number, number, number] | null;
  // 人脸线字段
  person_id?: number;
  person_name?: string;
  person_code?: string;
  // 车牌线字段
  plate_no?: string;
  plate_color?: string;
  owner_name?: string;
  owner_phone?: string;
  remark?: string;
}

export const enrollPendingRecord = (kind: PendingEnrollKind, payload: PendingEnrollPayload) => {
  const { record_id, ...rest } = payload;
  return mutationApi(kind, `/records/${record_id}/enroll`, rest);
};

export const batchEnrollPendingRecords = (
  kind: PendingEnrollKind,
  items: PendingEnrollPayload[],
) =>
  mutationApi<{
    success_count: number;
    failed_count: number;
    success: Array<{ record_id: number; entry: Record<string, unknown> }>;
    failed: Array<{ record_id?: number; msg: string }>;
  }>(kind, '/records/batch-enroll', { items });

/** AI 框 [x1,y1,x2,y2] → 编辑器矩形 {x,y,w,h} */
export function bboxToRect(
  bbox?: [number, number, number, number] | null,
): PendingEnrollBbox | null {
  if (!bbox || bbox.length < 4) return null;
  const [x1, y1, x2, y2] = bbox;
  const rect = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1) };
  if (rect.w <= 0 || rect.h <= 0) return null;
  return rect;
}

/** 编辑器矩形 → [x1,y1,x2,y2] */
export function rectToBbox(rect: PendingEnrollBbox): [number, number, number, number] {
  return [
    Math.round(rect.x),
    Math.round(rect.y),
    Math.round(rect.x + rect.w),
    Math.round(rect.y + rect.h),
  ];
}
