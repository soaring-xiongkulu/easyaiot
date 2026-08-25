/**
 * 人脸库管理接口
 */
import { defHttp } from '@/utils/http/axios';
import { resolveLibraryImageDisplayUrl } from '@/utils/alertMinioImage';

export { resolveLibraryImageDisplayUrl as resolveFaceImageDisplayUrl };

const FACE_PREFIX = '/video/face';

const FACE_API_SUCCESS_CODES = new Set([0, 200]);

/** 判断人脸库接口是否成功（兼容 transform 剥离外层后的实体对象） */
export function isFaceLibraryApiOk(response: unknown): boolean {
  if (response == null || typeof response !== 'object') return false;
  const r = response as Record<string, unknown>;
  if (typeof r.code === 'number') return FACE_API_SUCCESS_CODES.has(r.code);
  if (typeof r.id === 'number') return true;
  if (typeof r.success_count === 'number') return true;
  if (Array.isArray(r.entries)) return true;
  return false;
}

export function getFaceLibraryApiMsg(response: unknown, fallback = ''): string {
  if (response != null && typeof response === 'object') {
    const msg = (response as Record<string, unknown>).msg;
    if (typeof msg === 'string' && msg) return msg;
  }
  return fallback;
}

/** 从接口异常中解析业务提示（避免暴露 HTTP 状态码原文） */
/** 兼容 axios transform 后直接返回实体 与 未 transform 的 { data } 包裹 */
export function unwrapFaceApiEntity<T extends { id?: number }>(
  response: T | { data?: T | null } | null | undefined,
): T | null {
  if (response == null) return null;
  if (typeof response === 'object' && typeof (response as T).id === 'number') {
    return response as T;
  }
  const nested = (response as { data?: T | null }).data;
  return nested ?? null;
}

export function parseFaceApiError(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (error == null) return fallback;
  if (typeof error === 'string') {
    return /^Request failed with status code \d+$/i.test(error) ? fallback : error;
  }
  const e = error as {
    message?: string;
    response?: { data?: { msg?: string } };
  };
  const bodyMsg = e.response?.data?.msg;
  if (typeof bodyMsg === 'string' && bodyMsg.trim()) return bodyMsg.trim();
  const msg = e.message;
  if (typeof msg === 'string' && msg && !/^Request failed with status code \d+$/i.test(msg)) {
    return msg;
  }
  return fallback;
}

/** 是否为摄像头自动录入未配置类错误 */
export function isAutoEnrollConfigError(error: unknown): boolean {
  const msg = parseFaceApiError(error, '');
  return /请先完成|请先保存|请至少绑定|绑定.*摄像头|配置.*摄像头|device_ids|摄像头/i.test(msg);
}

async function faceMutationApi<T = unknown>(
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
    if (!FACE_API_SUCCESS_CODES.has(body?.code)) {
      throw new Error(body?.msg || '请求失败');
    }
    return body;
  } catch (error) {
    throw new Error(parseFaceApiError(error, '请求失败'));
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
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        ...options.headers,
      },
      ...(method === 'get' ? { params: options.params } : { data: options.data || options.params }),
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  ) as Promise<T>;
};

export interface FaceLibrary {
  id: number;
  name: string;
  /** 后台自动生成，创建时无需传入 */
  code: string;
  business_tags?: string[];
  description?: string;
  similarity_threshold: number;
  is_enabled: boolean;
  face_count: number;
  /** 归一化人员数量（每人可含多张照片） */
  person_count?: number;
  /** 摄像头自动录入是否运行中 */
  auto_enroll_running?: boolean;
  created_at?: string;
  updated_at?: string;
  entries?: FaceEntry[];
}

export interface FaceEntry {
  id: number;
  library_id: number;
  person_id?: number;
  person_name: string;
  person_code?: string;
  image_path?: string;
  image_url?: string;
  remark?: string;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FacePerson {
  id: number;
  library_id: number;
  person_name: string;
  person_code?: string;
  cover_entry_id?: number;
  cover_image_url?: string;
  is_enabled: boolean;
  face_count: number;
  created_at?: string;
  updated_at?: string;
  entries?: FaceEntry[];
}

/** 人脸特征提取模型 face_rec.onnx 状态 */
export interface FaceRecModelStatus {
  exists: boolean;
  filename: string;
  path?: string;
  size_bytes: number;
  downloading: boolean;
  /** 存在未完成的 zip 下载，可断点续传 */
  resumable?: boolean;
  /** idle | downloading | extracting | done | error */
  stage?: string;
  progress: number;
  downloaded_bytes?: number;
  total_bytes?: number;
  error?: string | null;
}

export interface FaceAutoEnrollTask {
  id?: number;
  library_id: number;
  device_ids: string[];
  device_names?: string[];
  duration_minutes: number;
  capture_interval_sec: number;
  person_name_prefix?: string;
  is_running: boolean;
  started_at?: string;
  expires_at?: string;
  enrolled_count?: number;
  skipped_count?: number;
}

export interface FaceNormalizeEntry {
  entry_id: number;
  person_id?: number;
  person_name: string;
  person_code?: string;
  image_url?: string;
  image_path?: string;
  created_at?: string;
}

export interface FaceNormalizePerson {
  person_id: number;
  person_name: string;
  person_code?: string;
  face_count: number;
  entries: FaceNormalizeEntry[];
}

export interface FaceNormalizeGroup {
  group_id: number;
  /** 该组内人脸照片总数 */
  count: number;
  entry_count?: number;
  /** 该组内涉及的不同人员数 */
  person_count?: number;
  suggested_target_person_id?: number;
  /** 兼容旧版按条目合并 */
  suggested_target_entry_id?: number;
  persons: FaceNormalizePerson[];
  entries?: FaceNormalizeEntry[];
}

export interface FaceNormalizeMergeAllResult {
  merged_groups: number;
  merged_persons: number;
  face_count: number;
  person_count: number;
}

export interface FaceMatchRecord {
  id: number;
  task_id?: number;
  task_name?: string;
  device_id: string;
  device_name?: string;
  library_id?: number;
  library_name?: string;
  face_image_path?: string;
  matched: boolean;
  matched_person_name?: string;
  matched_person_code?: string;
  similarity?: number;
  threshold?: number;
  status?: string;
  created_at?: string;
}

export const listFaceLibraries = (params?: { search?: string; is_enabled?: boolean }) => {
  return commonApi<{ code: number; msg: string; data: FaceLibrary[]; total: number }>(
    'get',
    `${FACE_PREFIX}/libraries`,
    { params },
  );
};

export const getFaceLibrary = (libraryId: number, includeEntries = false) => {
  return commonApi<{ code: number; msg: string; data: FaceLibrary }>(
    'get',
    `${FACE_PREFIX}/libraries/${libraryId}`,
    { params: { include_entries: includeEntries } },
  );
};

export const createFaceLibrary = (data: Partial<FaceLibrary>) => {
  return faceMutationApi<FaceLibrary>('post', `${FACE_PREFIX}/libraries`, data);
};

export const updateFaceLibrary = (libraryId: number, data: Partial<FaceLibrary>) => {
  return faceMutationApi<FaceLibrary>('put', `${FACE_PREFIX}/libraries/${libraryId}`, data);
};

export const deleteFaceLibrary = (libraryId: number) => {
  return faceMutationApi('delete', `${FACE_PREFIX}/libraries/${libraryId}`);
};

export const listFaceEntries = (libraryId: number, params?: { search?: string }) => {
  return commonApi<{ code: number; msg: string; data: FaceEntry[]; total: number }>(
    'get',
    `${FACE_PREFIX}/libraries/${libraryId}/entries`,
    { params },
  );
};

export const listFacePersons = (
  libraryId: number,
  params?: { search?: string; page?: number; pageSize?: number; pageNo?: number },
) => {
  return commonApi<{ code: number; msg: string; data: FacePerson[]; total: number }>(
    'get',
    `${FACE_PREFIX}/libraries/${libraryId}/persons`,
    { params },
  );
};

export const getFacePerson = (personId: number, includeEntries = true) => {
  return commonApi<{ code: number; msg: string; data: FacePerson }>(
    'get',
    `${FACE_PREFIX}/persons/${personId}`,
    { params: { include_entries: includeEntries } },
  );
};

export const setFacePersonCover = (personId: number, entryId: number) => {
  return faceMutationApi<FacePerson>('put', `${FACE_PREFIX}/persons/${personId}/cover`, {
    entry_id: entryId,
  });
};

export const deleteFacePerson = (personId: number) => {
  return faceMutationApi('delete', `${FACE_PREFIX}/persons/${personId}`);
};

export const batchDeleteFacePersons = (personIds: number[]) => {
  return faceMutationApi<{ deleted: number }>('post', `${FACE_PREFIX}/persons/batch-delete`, {
    person_ids: personIds,
  });
};

export const addFaceEntry = (libraryId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${FACE_PREFIX}/libraries/${libraryId}/entries`,
      data: formData,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  );
};

export interface FaceBatchEntryResult {
  person_id?: number;
  entries: FaceEntry[];
  success_count: number;
  failed_count: number;
  errors?: Array<{ index: number; msg: string }>;
}

export const addFaceEntriesBatch = (libraryId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${FACE_PREFIX}/libraries/${libraryId}/entries/batch`,
      data: formData,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  ) as Promise<{ code: number; msg: string; data: FaceBatchEntryResult }>;
};

export const updateFaceEntry = (entryId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.put(
    {
      url: `${FACE_PREFIX}/entries/${entryId}`,
      data: formData,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  ) as Promise<{ code: number; msg: string; data: FaceEntry }>;
};

export const deleteFaceEntry = (entryId: number) => {
  return faceMutationApi('delete', `${FACE_PREFIX}/entries/${entryId}`);
};

export const listFaceMatchRecords = (params?: {
  page?: number;
  pageSize?: number;
  library_id?: number;
  device_id?: string;
  matched?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; list: FaceMatchRecord[]; total: number }>(
    'get',
    `${FACE_PREFIX}/matching/records`,
    { params },
  );
};

/** 人物出现轨迹点（某人在某天被各摄像头识别命中的地图坐标时间线） */
export interface FaceTrajectoryPoint {
  match_record_id: number;
  time: string;
  device_id: string;
  device_name: string;
  address?: string | null;
  longitude: number;
  latitude: number;
  similarity?: number | null;
  threshold?: number | null;
  library_name?: string | null;
  task_name?: string | null;
  alert_id?: number | null;
  face_image_path?: string | null;
  face_image_url?: string | null;
}

export const getFaceTrajectory = (params: {
  person_name: string;
  date: string;
  device_id?: string;
  limit?: number;
}) => {
  return commonApi<{
    code: number;
    msg: string;
    data: { person_name: string; date: string; points: FaceTrajectoryPoint[]; total: number };
  }>('get', `${FACE_PREFIX}/matching/trajectory`, { params });
};

export const getFaceAutoEnrollTask = (libraryId: number) => {
  return commonApi<{ code: number; msg: string; data: FaceAutoEnrollTask | null }>(
    'get',
    `${FACE_PREFIX}/libraries/${libraryId}/auto-enroll`,
  );
};

export const saveFaceAutoEnrollConfig = (
  libraryId: number,
  data: Partial<FaceAutoEnrollTask>,
) => {
  return faceMutationApi<FaceAutoEnrollTask>(
    'put',
    `${FACE_PREFIX}/libraries/${libraryId}/auto-enroll`,
    data,
  );
};

export const startFaceAutoEnroll = (libraryId: number) => {
  return faceMutationApi<FaceAutoEnrollTask>(
    'post',
    `${FACE_PREFIX}/libraries/${libraryId}/auto-enroll/start`,
  );
};

export const stopFaceAutoEnroll = (libraryId: number) => {
  return faceMutationApi<FaceAutoEnrollTask>(
    'post',
    `${FACE_PREFIX}/libraries/${libraryId}/auto-enroll/stop`,
  );
};

export const previewFaceNormalizeGroups = (libraryId: number, threshold = 0.75) => {
  return commonApi<{ code: number; msg: string; data: FaceNormalizeGroup[]; total: number }>(
    'get',
    `${FACE_PREFIX}/libraries/${libraryId}/normalize/preview`,
    { params: { threshold } },
  );
};

/** 归一化合并：将其他人员的全部照片归入目标人员 */
export const mergeFaceNormalizePersons = (
  libraryId: number,
  targetPersonId: number,
  sourcePersonIds: number[],
) => {
  return faceMutationApi('post', `${FACE_PREFIX}/libraries/${libraryId}/normalize/merge`, {
    target_person_id: targetPersonId,
    source_person_ids: sourcePersonIds,
  });
};

/** @deprecated 请使用 mergeFaceNormalizePersons */
export const mergeFaceNormalizeEntries = (
  libraryId: number,
  targetEntryId: number,
  sourceEntryIds: number[],
) => {
  return faceMutationApi('post', `${FACE_PREFIX}/libraries/${libraryId}/normalize/merge`, {
    target_entry_id: targetEntryId,
    source_entry_ids: sourceEntryIds,
  });
};

export const mergeAllFaceNormalizeGroups = (libraryId: number, threshold = 0.75) => {
  return faceMutationApi<FaceNormalizeMergeAllResult>(
    'post',
    `${FACE_PREFIX}/libraries/${libraryId}/normalize/merge-all`,
    { threshold },
  );
};

/** 查询人脸特征提取模型是否已下载 */
export const getFaceRecModelStatus = () => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp
    .get(
      {
        url: `${FACE_PREFIX}/model/status`,
        headers: {
          // @ts-ignore
          ignoreCancelToken: true,
        },
      },
      { isTransformResponse: false, errorMessageMode: 'none' },
    )
    .then((res) => {
      const body = ((res as { data?: { code: number; msg: string; data: FaceRecModelStatus } })?.data ??
        res) as { code: number; msg: string; data: FaceRecModelStatus };
      if (!FACE_API_SUCCESS_CODES.has(body?.code)) {
        throw new Error(body?.msg || '查询失败');
      }
      return body;
    });
};

/** 触发服务端下载人脸特征提取模型 */
export const downloadFaceRecModel = () => {
  return faceMutationApi<{ started: boolean; message?: string } & FaceRecModelStatus>(
    'post',
    `${FACE_PREFIX}/model/download`,
  );
};
