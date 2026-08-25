/**
 * 车牌库管理接口
 */
import { defHttp } from '@/utils/http/axios';
import { resolveLibraryImageDisplayUrl } from '@/utils/alertMinioImage';

export { resolveLibraryImageDisplayUrl as resolvePlateImageDisplayUrl };

const PLATE_PREFIX = '/video/plate';

const PLATE_API_SUCCESS_CODES = new Set([0, 200]);

export function isPlateLibraryApiOk(response: unknown): boolean {
  if (response == null || typeof response !== 'object') return false;
  const r = response as Record<string, unknown>;
  if (typeof r.code === 'number') return PLATE_API_SUCCESS_CODES.has(r.code);
  return typeof r.id === 'number';
}

export function parsePlateApiError(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (error == null) return fallback;
  if (typeof error === 'string') {
    return /^Request failed with status code \d+$/i.test(error) ? fallback : error;
  }
  const e = error as { message?: string; response?: { data?: { msg?: string } } };
  const bodyMsg = e.response?.data?.msg;
  if (typeof bodyMsg === 'string' && bodyMsg.trim()) return bodyMsg.trim();
  const msg = e.message;
  if (typeof msg === 'string' && msg && !/^Request failed with status code \d+$/i.test(msg)) {
    return msg;
  }
  return fallback;
}

export function isAutoEnrollConfigError(error: unknown): boolean {
  const msg = parsePlateApiError(error, '');
  return /请先完成|请先保存|请至少绑定|绑定.*摄像头|配置.*摄像头|device_ids|摄像头/i.test(msg);
}

async function plateMutationApi<T = unknown>(
  method: 'post' | 'put' | 'delete',
  url: string,
  data?: unknown,
): Promise<{ code: number; msg: string; data?: T }> {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  try {
    const res = await defHttp[method](
      {
        url,
        ...(method === 'delete' ? {} : { data }),
        headers: { // @ts-ignore
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
    if (!PLATE_API_SUCCESS_CODES.has(body?.code)) {
      throw new Error(body?.msg || '请求失败');
    }
    return body;
  } catch (error) {
    throw new Error(parsePlateApiError(error, '请求失败'));
  }
}

const commonApi = <T = any>(
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  options: { params?: any; data?: any; headers?: Record<string, string> } = {},
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp[method](
    {
      url,
      headers: { // @ts-ignore
        ignoreCancelToken: true,
        ...options.headers,
      },
      ...(method === 'get' ? { params: options.params } : { data: options.data || options.params }),
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  ) as Promise<T>;
};

export interface PlateLibrary {
  id: number;
  name: string;
  code: string;
  business_tags?: string[];
  description?: string;
  is_enabled: boolean;
  plate_count: number;
  auto_enroll_running?: boolean;
  created_at?: string;
  updated_at?: string;
  entries?: PlateEntry[];
}

export interface PlateEntry {
  id: number;
  library_id: number;
  plate_no: string;
  plate_color?: string;
  owner_name?: string;
  owner_phone?: string;
  image_path?: string;
  image_url?: string;
  remark?: string;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PlateModelStatus {
  exists: boolean;
  detect_model?: string;
  rec_model?: string;
  downloading: boolean;
  stage?: string;
  progress: number;
  error?: string | null;
}

export interface PlateAutoEnrollTask {
  id?: number;
  library_id: number;
  device_ids: string[];
  device_names?: string[];
  duration_minutes: number;
  capture_interval_sec: number;
  is_running: boolean;
  started_at?: string;
  expires_at?: string;
  enrolled_count?: number;
  skipped_count?: number;
}

export interface PlateMatchRecord {
  id: number;
  task_id?: number;
  task_name?: string;
  device_id: string;
  device_name?: string;
  library_id?: number;
  library_name?: string;
  plate_no?: string;
  plate_color?: string;
  plate_image_path?: string;
  matched: boolean;
  matched_owner_name?: string;
  detect_conf?: number;
  status?: string;
  created_at?: string;
}

export const listPlateLibraries = (params?: { search?: string; is_enabled?: boolean }) =>
  commonApi<{ code: number; msg: string; data: PlateLibrary[]; total: number }>(
    'get',
    `${PLATE_PREFIX}/libraries`,
    { params },
  );

export const getPlateLibrary = (libraryId: number, includeEntries = false) =>
  commonApi<{ code: number; msg: string; data: PlateLibrary }>(
    'get',
    `${PLATE_PREFIX}/libraries/${libraryId}`,
    { params: { include_entries: includeEntries } },
  );

export const createPlateLibrary = (data: Partial<PlateLibrary>) =>
  plateMutationApi<PlateLibrary>('post', `${PLATE_PREFIX}/libraries`, data);

export const updatePlateLibrary = (libraryId: number, data: Partial<PlateLibrary>) =>
  plateMutationApi<PlateLibrary>('put', `${PLATE_PREFIX}/libraries/${libraryId}`, data);

export const deletePlateLibrary = (libraryId: number) =>
  plateMutationApi('delete', `${PLATE_PREFIX}/libraries/${libraryId}`);

/**
 * 车牌条目列表。
 * 后端返回 { code, msg, list, total }（列表字段为 list，无 data 包装），
 * 与全局分页转换（只认 data 字段）不一致，故关闭 transform 直接读取原始响应体。
 */
export const listPlateEntries = (
  libraryId: number,
  params?: { search?: string; page?: number; page_size?: number },
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp
    .get(
      {
        url: `${PLATE_PREFIX}/libraries/${libraryId}/entries`,
        params,
        headers: { // @ts-ignore
          ignoreCancelToken: true,
        },
      },
      { isTransformResponse: false, errorMessageMode: 'none' },
    )
    .then((res) => {
      const body = ((res as { data?: { code: number; msg: string; list: PlateEntry[]; total: number } })?.data ??
        res) as { code: number; msg: string; list: PlateEntry[]; total: number };
      if (!PLATE_API_SUCCESS_CODES.has(body?.code)) {
        throw new Error(body?.msg || '请求失败');
      }
      return body;
    });
};

export const addPlateEntry = (libraryId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${PLATE_PREFIX}/libraries/${libraryId}/entries`,
      data: formData,
      headers: { // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  );
};

export const updatePlateEntry = (entryId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.put(
    {
      url: `${PLATE_PREFIX}/entries/${entryId}`,
      data: formData,
      headers: { // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  );
};

export const deletePlateEntry = (entryId: number) =>
  commonApi('delete', `${PLATE_PREFIX}/entries/${entryId}`);

export const batchDeletePlateEntries = (entryIds: number[]) =>
  plateMutationApi<{ deleted: number }>('post', `${PLATE_PREFIX}/entries/batch-delete`, {
    entry_ids: entryIds,
  });

export interface PlateNormalizeEntry {
  entry_id: number;
  plate_no: string;
  plate_color?: string;
  owner_name?: string;
  owner_phone?: string;
  image_url?: string;
  image_path?: string;
  remark?: string;
  is_enabled: boolean;
  created_at?: string;
}

export interface PlateNormalizeGroup {
  group_id: number;
  plate_no: string;
  count: number;
  entry_count?: number;
  suggested_target_entry_id: number;
  entries: PlateNormalizeEntry[];
}

export interface PlateNormalizeMergeAllResult {
  merged_groups: number;
  merged_entries: number;
  plate_count: number;
}

export const previewPlateNormalizeGroups = (libraryId: number, threshold = 1) =>
  commonApi<{ code: number; msg: string; data: PlateNormalizeGroup[]; total: number }>(
    'get',
    `${PLATE_PREFIX}/libraries/${libraryId}/normalize/preview`,
    { params: { threshold } },
  );

export const mergePlateNormalizeEntries = (
  libraryId: number,
  targetEntryId: number,
  sourceEntryIds: number[],
) =>
  plateMutationApi('post', `${PLATE_PREFIX}/libraries/${libraryId}/normalize/merge`, {
    target_entry_id: targetEntryId,
    source_entry_ids: sourceEntryIds,
  });

export const mergeAllPlateNormalizeGroups = (libraryId: number, threshold = 1) =>
  plateMutationApi<PlateNormalizeMergeAllResult>(
    'post',
    `${PLATE_PREFIX}/libraries/${libraryId}/normalize/merge-all`,
    { threshold },
  );

export const getPlateModelStatus = () => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp
    .get(
      {
        url: `${PLATE_PREFIX}/model/status`,
        headers: { // @ts-ignore
          ignoreCancelToken: true,
        },
      },
      { isTransformResponse: false, errorMessageMode: 'none' },
    )
    .then((res) => {
      const body = ((res as { data?: { code: number; msg: string; data: PlateModelStatus } })?.data ??
        res) as { code: number; msg: string; data: PlateModelStatus };
      if (!PLATE_API_SUCCESS_CODES.has(body?.code)) {
        throw new Error(body?.msg || '查询失败');
      }
      return body;
    });
};

export const downloadPlateModel = () =>
  plateMutationApi<{ started: boolean; message?: string } & PlateModelStatus>(
    'post',
    `${PLATE_PREFIX}/model/download`,
  );

export const getPlateAutoEnrollTask = (libraryId: number) =>
  commonApi<{ code: number; msg: string; data: PlateAutoEnrollTask | null }>(
    'get',
    `${PLATE_PREFIX}/libraries/${libraryId}/auto-enroll`,
  );

export const savePlateAutoEnrollConfig = (libraryId: number, data: Partial<PlateAutoEnrollTask>) =>
  plateMutationApi<PlateAutoEnrollTask>('put', `${PLATE_PREFIX}/libraries/${libraryId}/auto-enroll`, data);

export const startPlateAutoEnroll = (libraryId: number) =>
  plateMutationApi<PlateAutoEnrollTask>('post', `${PLATE_PREFIX}/libraries/${libraryId}/auto-enroll/start`);

export const stopPlateAutoEnroll = (libraryId: number) =>
  plateMutationApi<PlateAutoEnrollTask>('post', `${PLATE_PREFIX}/libraries/${libraryId}/auto-enroll/stop`);

export const listPlateMatchRecords = (params?: {
  page?: number;
  page_size?: number;
  library_id?: number;
  device_id?: string;
  matched?: boolean;
}) =>
  commonApi<{ code: number; msg: string; list: PlateMatchRecord[]; total: number }>(
    'get',
    `${PLATE_PREFIX}/matching/records`,
    { params },
  );

/** 车牌出现轨迹点（某车牌在某天被各摄像头识别命中的地图坐标时间线） */
export interface PlateTrajectoryPoint {
  match_record_id: number;
  time: string;
  device_id: string;
  device_name: string;
  address?: string | null;
  longitude: number;
  latitude: number;
  plate_no?: string | null;
  plate_color?: string | null;
  matched_owner_name?: string | null;
  detect_conf?: number | null;
  library_name?: string | null;
  task_name?: string | null;
  alert_id?: number | null;
  plate_image_path?: string | null;
  plate_image_url?: string | null;
}

export const getPlateTrajectory = (params: {
  plate_no: string;
  date: string;
  device_id?: string;
  limit?: number;
}) => {
  return commonApi<{
    code: number;
    msg: string;
    data: { plate_no: string; date: string; points: PlateTrajectoryPoint[]; total: number };
  }>('get', `${PLATE_PREFIX}/matching/trajectory`, { params });
};

export const recognizePlateImage = (formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${PLATE_PREFIX}/recognize/image`,
      data: formData,
      headers: { // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  );
};
