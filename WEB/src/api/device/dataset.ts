import {defHttp} from '@/utils/http/axios';

enum Api {
  Dataset = '/dataset',
  DatasetImage = '/dataset/image',
  DatasetTag = '/dataset/tag',
  DatasetTask = '/dataset/task',
  DatasetTaskResult = '/dataset/task-result',
  DatasetTaskUser = '/dataset/task-user',
  DatasetVideo = '/dataset/video',
  Warehouse = '/warehouse',
  WarehouseDataset = '/warehouse/dataset',
  DatasetFrameTask = '/dataset/frame-task',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});

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

// 新增类型定义
interface AutoLabelModelReqVO {
  modelId?: number;
  /** @deprecated 请使用 modelId */
  modelServiceId?: number;
}

interface DatasetSplitReqVO {
  trainRatio: number;
  valRatio: number;
  testRatio: number;
}

export interface DatasetSyncCheckResult {
  usageAllocated: boolean;
  annotationCompleted: boolean;
  syncReady: boolean;
  syncing: boolean;
  syncedToMinio: boolean;
  syncError: string | null;
  syncStatus: DatasetSyncStatus;
  syncStage: DatasetSyncStage | null;
  syncProgress: number;
  processedImages: number;
  syncSubmittedAt: string | null;
  syncStartedAt: string | null;
  syncFinishedAt: string | null;
  totalImages: number;
  unallocatedCount: number;
  unannotatedCount: number;
}

export type DatasetSyncStatus = 'IDLE' | 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';

export type DatasetSyncStage =
  | 'WAITING'
  | 'PREPARING'
  | 'EXPORTING'
  | 'PACKAGING'
  | 'UPLOADING'
  | 'FINALIZING'
  | 'COMPLETED'
  | 'FAILED';

export function parseDatasetSyncCheckResult(raw: unknown): DatasetSyncCheckResult {
  const data = (raw as { data?: DatasetSyncCheckResult })?.data ?? (raw as DatasetSyncCheckResult);
  const syncedToMinio = !!data?.syncedToMinio;
  const syncing = !!data?.syncing;
  const syncStatus = data?.syncStatus
    ?? (syncedToMinio ? 'SUCCEEDED' : syncing ? 'RUNNING' : data?.syncError ? 'FAILED' : 'IDLE');
  return {
    usageAllocated: !!data?.usageAllocated,
    annotationCompleted: !!data?.annotationCompleted,
    syncReady: !!data?.syncReady,
    syncing: syncing || syncStatus === 'QUEUED' || syncStatus === 'RUNNING',
    syncedToMinio,
    syncError: data?.syncError || null,
    syncStatus,
    syncStage: data?.syncStage ?? (syncedToMinio ? 'COMPLETED' : null),
    syncProgress: Math.max(0, Math.min(100, data?.syncProgress ?? (syncedToMinio ? 100 : 0))),
    processedImages: data?.processedImages ?? (syncedToMinio ? data?.totalImages ?? 0 : 0),
    syncSubmittedAt: data?.syncSubmittedAt ?? null,
    syncStartedAt: data?.syncStartedAt ?? null,
    syncFinishedAt: data?.syncFinishedAt ?? null,
    totalImages: data?.totalImages ?? 0,
    unallocatedCount: data?.unallocatedCount ?? 0,
    unannotatedCount: data?.unannotatedCount ?? 0,
  };
}

// 数据集
export const createDataset = (params) => {
  return commonApi('post', Api.Dataset + '/create', {params});
};

export const updateDataset = (params) => {
  return commonApi('put', Api.Dataset + '/update', {params});
};

export const deleteDataset = (id) => {
  return commonApi('delete', `${Api.Dataset}/delete?id=${id}`);
};

export const getDataset = (params) => {
  return commonApi('get', Api.Dataset + '/get', {params});
};

export const getDatasetPage = (params) => {
  return commonApi('get', Api.Dataset + '/page', {params}, {}, false);
};

export const exportDatasetExcel = (params) => {
  return commonApi('get', Api.Dataset + '/export-excel', {params});
};

// 修改后的接口实现
export const setAutoLabelModel = (datasetId, params: AutoLabelModelReqVO) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/set-auto-label-model`, {
    params: {...params}
  });
};

export const autoLabel = (datasetId) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/auto-label`);
};

export const splitDataset = (datasetId, params: DatasetSplitReqVO) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/split`, {
    params: {...params}
  });
};

export const resetDataset = (datasetId) => {
  return commonApi('post', `${Api.Dataset}/${datasetId}/reset`);
};

// 图片数据集
export const createDatasetImage = (params) => {
  return commonApi('post', Api.DatasetImage + '/create', {params});
};

export const updateDatasetImage = (params) => {
  return commonApi('put', Api.DatasetImage + '/update', {params});
};

export const deleteDatasetImage = (id) => {
  return commonApi('delete', `${Api.DatasetImage}/delete/${id}`);
};

export const deleteDatasetImages = (ids) => {
  return commonApi('delete', `${Api.DatasetImage}/batchDelete/${ids}`);
};

export const getDatasetImage = (params) => {
  return commonApi('get', Api.DatasetImage + '/get', {params});
};

export const getDatasetImagePage = (params) => {
  return commonApi('get', Api.DatasetImage + '/page', {params});
};

export const exportDatasetImageExcel = (params) => {
  return commonApi('get', Api.DatasetImage + '/export-excel', {params});
};

export const checkSyncCondition = (datasetId) => {
  return commonApi('get', `${Api.DatasetImage}/${datasetId}/check-sync-condition`);
};

export const syncToMinio = (datasetId) => {
  return commonApi('post', `${Api.DatasetImage}/${datasetId}/sync-to-minio`, {
    timeout: 30 * 1000,
  });
};

interface DatasetSyncPollOptions {
  intervalMs?: number;
  timeoutMs?: number;
  signal?: AbortSignal;
  onStatus?: (status: DatasetSyncCheckResult) => void;
  onPollError?: (error: Error, retryCount: number) => void;
}

export async function waitForDatasetMinioSync(
  datasetId,
  options: DatasetSyncPollOptions = {},
): Promise<DatasetSyncCheckResult> {
  const intervalMs = options.intervalMs ?? 2000;
  const timeoutMs = options.timeoutMs ?? 30 * 60 * 1000;
  const deadline = Date.now() + timeoutMs;
  let consecutivePollErrors = 0;

  while (true) {
    if (options.signal?.aborted) {
      throw abortError();
    }
    let status: DatasetSyncCheckResult;
    try {
      status = parseDatasetSyncCheckResult(await checkSyncCondition(datasetId));
      consecutivePollErrors = 0;
    } catch (error) {
      if (options.signal?.aborted) {
        throw abortError();
      }
      consecutivePollErrors++;
      const pollError = error instanceof Error ? error : new Error('同步状态查询失败');
      options.onPollError?.(pollError, consecutivePollErrors);
      if (Date.now() >= deadline) {
        throw new Error('暂时无法获取同步状态，请稍后刷新页面重试');
      }
      await waitForPoll(Math.min(intervalMs * consecutivePollErrors, 10_000), options.signal);
      continue;
    }
    options.onStatus?.(status);
    if (status.syncStatus === 'SUCCEEDED' || status.syncedToMinio) {
      return status;
    }
    if (status.syncStatus === 'FAILED') {
      throw new Error(status.syncError || '同步失败，请重新提交');
    }
    if (status.syncStatus !== 'QUEUED' && status.syncStatus !== 'RUNNING' && !status.syncing) {
      throw new Error(status.syncError || '同步任务未启动或已停止');
    }
    if (Date.now() >= deadline) {
      throw new Error('同步任务仍在后台运行，请稍后刷新查看');
    }
    await waitForPoll(intervalMs, options.signal);
  }
}

function waitForPoll(delayMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, delayMs);
    const onAbort = () => {
      window.clearTimeout(timer);
      reject(abortError());
    };
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

function abortError(): Error {
  const error = new Error('同步状态轮询已取消');
  error.name = 'AbortError';
  return error;
}

// 数据集标签
export const createDatasetTag = (params) => {
  return commonApi('post', Api.DatasetTag + '/create', {params});
};

export const updateDatasetTag = (params) => {
  return commonApi('put', Api.DatasetTag + '/update', {params});
};

export const deleteDatasetTag = (id) => {
  return commonApi('delete', `${Api.DatasetTag}/delete?id=${id}`);
};

export const getDatasetTag = (params) => {
  return commonApi('get', Api.DatasetTag + '/get', {params});
};

export const getDatasetTagPage = (params) => {
  return commonApi('get', Api.DatasetTag + '/page', {params});
};

export const exportDatasetTagExcel = (params) => {
  return commonApi('get', Api.DatasetTag + '/export-excel', {params});
};

// 图片/压缩包上传（解压与入库可能较慢，延长超时）
export interface DatasetImageUploadResult {
  successCount?: number;
  failedCount?: number;
  skippedCount?: number;
  overwrittenCount?: number;
  failedFiles?: string[];
  importTaskId?: string;
  importStatus?: 'processing' | 'completed';
}

export interface DatasetImageImportTaskResult {
  taskId: string;
  status: 'processing' | 'completed' | 'failed' | 'cancelled';
  processedCount?: number;
  totalCount?: number;
  result?: DatasetImageUploadResult;
  annotationResult?: DatasetAnnotationImportResult;
  errorMessage?: string;
}

export interface DatasetYoloPreflightClass {
  classId: number;
  detectedName?: string;
  suggestedName?: string;
  manualNameRequired: boolean;
  existingTag: boolean;
}

export interface DatasetYoloPreflightSplit {
  split: 'train' | 'validation' | 'test' | 'unassigned';
  imageCount: number;
  matchedLabelCount: number;
}

export interface DatasetYoloPreflightResult {
  rootPath: string;
  importable: boolean;
  imageCount: number;
  matchedLabelCount: number;
  missingLabelCount: number;
  invalidLabelCount: number;
  duplicateImageNameCount: number;
  splits: DatasetYoloPreflightSplit[];
  classes: DatasetYoloPreflightClass[];
  existingTags: string[];
  warnings: string[];
}

export interface DatasetYoloImportParams {
  path: string;
  classMapping: Record<number, string>;
  classMappingConfirmed: boolean;
  importMode: 'annotations_only' | 'overwrite';
  allowMissingLabels: boolean;
  preserveSplits: boolean;
}

export const getDatasetImageImportTask = (taskId: string): Promise<DatasetImageImportTaskResult> => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});
  return defHttp.get(
    { url: `${Api.DatasetImage}/import-task/${taskId}`, timeout: 30 * 1000 },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

export const cancelDatasetImageImportTask = (taskId: string): Promise<boolean> => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});
  return defHttp.delete(
    { url: `${Api.DatasetImage}/import-task/${taskId}`, timeout: 30 * 1000 },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

function sleepMs(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function waitForDatasetImportTask(
  taskId: string,
  options?: { onProgress?: (processed: number, total?: number) => void; signal?: AbortSignal },
): Promise<DatasetImageImportTaskResult> {
  const pollIntervalMs = 2000;
  let cancelRequested = false;
  const requestCancel = () => {
    if (cancelRequested) return;
    cancelRequested = true;
    void cancelDatasetImageImportTask(taskId).catch(() => {});
  };
  options?.signal?.addEventListener('abort', requestCancel, { once: true });
  try {
    while (true) {
      if (options?.signal?.aborted) {
        requestCancel();
        throw new Error('上传已取消');
      }
      const task = await getDatasetImageImportTask(taskId);
      if (task.status === 'cancelled') {
        throw new Error('上传已取消');
      }
      if (task.status === 'completed') {
        return task;
      }
      if (task.status === 'failed') {
        throw new Error(task.errorMessage || '导入失败');
      }
      if (task.processedCount != null && task.processedCount > 0) {
        options?.onProgress?.(task.processedCount, task.totalCount);
      } else if (task.totalCount != null && task.totalCount > 0) {
        options?.onProgress?.(0, task.totalCount);
      }
      await sleepMs(pollIntervalMs);
    }
  } finally {
    options?.signal?.removeEventListener('abort', requestCancel);
  }
}

interface DatasetImportTaskSubmitResult {
  taskId: string;
  status: string;
}

async function submitAnnotationPathImport(
  url: string,
  data: object,
  signal?: AbortSignal,
  onProgress?: (processed: number, total?: number) => void,
): Promise<DatasetAnnotationImportResult> {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const submit = await defHttp.post<DatasetImportTaskSubmitResult>(
    { url, data, timeout: 60 * 1000, signal },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
  const taskId = submit?.taskId;
  if (!taskId) {
    throw new Error('导入任务创建失败');
  }
  const task = await waitForDatasetImportTask(taskId, { signal, onProgress });
  if (!task.annotationResult) {
    throw new Error('导入结果为空');
  }
  return task.annotationResult;
}

export const uploadDatasetImage = (formData: FormData): Promise<DatasetImageUploadResult> => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});
  return defHttp.post(
    {
      url: `${Api.DatasetImage}/upload`,
      data: formData,
      timeout: 30 * 60 * 1000,
    },
    {
      successMessageMode: 'none',
      errorMessageMode: 'none',
    },
  );
};

// —— 分片上传（断点续传，最大 200GB）——

export interface DatasetChunkUploadInitParams {
  datasetId: number;
  fileName: string;
  fileSize: number;
  isZip: boolean;
  totalChunks: number;
  chunkSize: number;
  fileKey?: string;
}

export interface DatasetChunkUploadInitResult {
  uploadId: string;
  uploadedChunks?: number[];
  resumed?: boolean;
}

export interface DatasetChunkUploadStatusResult {
  uploadId: string;
  totalChunks: number;
  uploadedChunks: number[];
}

const chunkUploadHeaders = () => ({
  'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
});

export const initDatasetChunkUpload = (data: DatasetChunkUploadInitParams): Promise<DatasetChunkUploadInitResult> => {
  defHttp.setHeader(chunkUploadHeaders());
  return defHttp.post(
    { url: `${Api.DatasetImage}/upload/chunk/init`, data, timeout: 60 * 1000 },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

export const uploadDatasetChunk = (uploadId: string, chunkIndex: number, chunk: Blob): Promise<boolean> => {
  defHttp.setHeader(chunkUploadHeaders());
  const formData = new FormData();
  formData.append('uploadId', uploadId);
  formData.append('chunkIndex', String(chunkIndex));
  formData.append('chunk', chunk, `chunk-${chunkIndex}`);
  return defHttp.post(
    {
      url: `${Api.DatasetImage}/upload/chunk`,
      data: formData,
      timeout: 10 * 60 * 1000,
    },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

export const getDatasetChunkUploadStatus = (uploadId: string): Promise<DatasetChunkUploadStatusResult> => {
  defHttp.setHeader(chunkUploadHeaders());
  return defHttp.get(
    { url: `${Api.DatasetImage}/upload/chunk/status`, params: { uploadId }, timeout: 30 * 1000 },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

export const completeDatasetChunkUpload = (uploadId: string): Promise<DatasetImageUploadResult> => {
  defHttp.setHeader(chunkUploadHeaders());
  const formData = new FormData();
  formData.append('uploadId', uploadId);
  return defHttp.post(
    {
      url: `${Api.DatasetImage}/upload/chunk/complete`,
      data: formData,
      timeout: 10 * 60 * 1000,
    },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

export const abortDatasetChunkUpload = (uploadId: string): Promise<boolean> => {
  defHttp.setHeader(chunkUploadHeaders());
  return defHttp.delete(
    { url: `${Api.DatasetImage}/upload/chunk`, params: { uploadId }, timeout: 30 * 1000 },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

// —— 标注工具：导入/导出（对齐 auto-labeling V9.13.0）——

export interface DatasetAnnotationImportResult {
  imagesCopied?: number;
  labelmeImages?: number;
  cocoImages?: number;
  yoloImages?: number;
  hint?: string;
  cloudDatasetId?: number;
  updatedImages?: number;
  createdImages?: number;
  /** 导入时创建的类别/标签名 */
  classes?: string[];
  tagsCreated?: number;
}

export interface DatasetAnnotationExportParams {
  trainRatio?: number;
  valRatio?: number;
  testRatio?: number;
  sampleSelection?: 'all' | 'annotated' | 'unannotated';
  selectedClasses: string[];
  exportPrefix?: string;
}

const annotationPost = (url: string, data?: Record<string, unknown>, options: Record<string, unknown> = {}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    { url, data, timeout: 60 * 60 * 1000, ...options },
    { isTransformResponse: true, errorMessageMode: 'message' },
  );
};

/** 导出 YOLO ZIP */
export const exportAnnotationDataset = (datasetId: number, data: DatasetAnnotationExportParams) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.Dataset}/${datasetId}/annotation/export`,
      data,
      responseType: 'blob',
      timeout: 30 * 60 * 1000,
    },
    { isTransformResponse: false },
  );
};

/** 上传图片文件夹 */
export const importAnnotationImageFolder = (datasetId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post({
    url: `${Api.Dataset}/${datasetId}/annotation/import-folder`,
    data: formData,
    timeout: 30 * 60 * 1000,
  });
};

/** 导入 LabelMe 文件夹 */
export const importAnnotationLabelme = (datasetId: number, formData: FormData) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post({
    url: `${Api.Dataset}/${datasetId}/annotation/import-labelme`,
    data: formData,
    timeout: 30 * 60 * 1000,
  });
};

/** ImageFolder 路径导入（异步任务，支持取消） */
export const importAnnotationImageFolderPath = (
  datasetId: number,
  path: string,
  signal?: AbortSignal,
  onProgress?: (processed: number, total?: number) => void,
) => submitAnnotationPathImport(`${Api.Dataset}/${datasetId}/annotation/import-path`, { path }, signal, onProgress);

/** YOLO 路径导入（异步任务，支持取消） */
export const importAnnotationYoloPath = (
  datasetId: number,
  data: DatasetYoloImportParams,
  signal?: AbortSignal,
  onProgress?: (processed: number, total?: number) => void,
) => submitAnnotationPathImport(`${Api.Dataset}/${datasetId}/annotation/import-yolo-path`, data, signal, onProgress);

/** YOLO 路径导入预检 */
export const preflightAnnotationYoloPath = (
  datasetId: number,
  path: string,
  signal?: AbortSignal,
): Promise<DatasetYoloPreflightResult> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.Dataset}/${datasetId}/annotation/import-yolo-path/preflight`,
      data: { path },
      timeout: 10 * 60 * 1000,
      signal,
    },
    { successMessageMode: 'none', errorMessageMode: 'none' },
  );
};

/** COCO 路径导入（异步任务，支持取消） */
export const importAnnotationCocoPath = (
  datasetId: number,
  body: { cocoJson: string; imagesRoot?: string },
  signal?: AbortSignal,
  onProgress?: (processed: number, total?: number) => void,
) => submitAnnotationPathImport(`${Api.Dataset}/${datasetId}/annotation/import-coco-path`, body, signal, onProgress);

/** 云平台数据集列表 */
export const listAnnotationCloudDatasets = () =>
  commonApi('get', `${Api.Dataset}/annotation/cloud-datasets`, {}, {}, false);

/** 从云平台导入 */
export const importAnnotationFromCloud = (datasetId: number, sourceDatasetId: number, signal?: AbortSignal) =>
  annotationPost(`${Api.Dataset}/${datasetId}/annotation/cloud-import`, { sourceDatasetId }, { signal });

/** 导出到云平台 */
export const exportAnnotationToCloud = (datasetId: number, body: { name: string; version: string }) =>
  annotationPost(`${Api.Dataset}/${datasetId}/annotation/cloud-export`, body);

/** 视频抽帧 */
export const extractAnnotationFrames = (datasetId: number, formData: FormData, signal?: AbortSignal) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post({
    url: `${Api.Dataset}/${datasetId}/annotation/extract-frames`,
    data: formData,
    timeout: 30 * 60 * 1000,
    signal,
  });
};

// 标注任务
export const createDatasetTask = (params) => {
  return commonApi('post', Api.DatasetTask + '/create', {params});
};

export const updateDatasetTask = (params) => {
  return commonApi('put', Api.DatasetTask + '/update', {params});
};

export const deleteDatasetTask = (id) => {
  return commonApi('delete', `${Api.DatasetTask}/delete?id=${id}`);
};

export const getDatasetTask = (params) => {
  return commonApi('get', Api.DatasetTask + '/get', {params});
};

export const getDatasetTaskPage = (params) => {
  return commonApi('get', Api.DatasetTask + '/page', {params});
};

export const exportDatasetTaskExcel = (params) => {
  return commonApi('get', Api.DatasetTask + '/export-excel', {params});
};

// 标注任务结果
export const createDatasetTaskResult = (params) => {
  return commonApi('post', Api.DatasetTaskResult + '/create', {params});
};

export const updateDatasetTaskResult = (params) => {
  return commonApi('put', Api.DatasetTaskResult + '/update', {params});
};

export const deleteDatasetTaskResult = (id) => {
  return commonApi('delete', `${Api.DatasetTaskResult}/delete?id=${id}`);
};

export const getDatasetTaskResult = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/get', {params});
};

export const getDatasetTaskResultPage = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/page', {params});
};

export const exportDatasetTaskResultExcel = (params) => {
  return commonApi('get', Api.DatasetTaskResult + '/export-excel', {params});
};

// 标注任务用户
export const createDatasetTaskUser = (params) => {
  return commonApi('post', Api.DatasetTaskUser + '/create', {params});
};

export const updateDatasetTaskUser = (params) => {
  return commonApi('put', Api.DatasetTaskUser + '/update', {params});
};

export const deleteDatasetTaskUser = (id) => {
  return commonApi('delete', `${Api.DatasetTaskUser}/delete?id=${id}`);
};

export const getDatasetTaskUser = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/get', {params});
};

export const getDatasetTaskUserPage = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/page', {params});
};

export const exportDatasetTaskUserExcel = (params) => {
  return commonApi('get', Api.DatasetTaskUser + '/export-excel', {params});
};

// 视频数据集
export const createDatasetVideo = (params) => {
  return commonApi('post', Api.DatasetVideo + '/create', {params});
};

export const updateDatasetVideo = (params) => {
  return commonApi('put', Api.DatasetVideo + '/update', {params});
};

export const deleteDatasetVideo = (id) => {
  return commonApi('delete', `${Api.DatasetVideo}/delete?id=${id}`);
};

export const getDatasetVideo = (params) => {
  return commonApi('get', Api.DatasetVideo + '/get', {params});
};

export const getDatasetVideoPage = (params) => {
  return commonApi('get', Api.DatasetVideo + '/page', {params});
};

export const exportDatasetVideoExcel = (params) => {
  return commonApi('get', Api.DatasetVideo + '/export-excel', {params});
};

// 数据仓
export const createWarehouse = (params) => {
  return commonApi('post', Api.Warehouse + '/create', {params});
};

export const updateWarehouse = (params) => {
  return commonApi('put', Api.Warehouse + '/update', {params});
};

export const deleteWarehouse = (id) => {
  return commonApi('delete', `${Api.Warehouse}/delete?id=${id}`);
};

export const getWarehouse = (params) => {
  return commonApi('get', Api.Warehouse + '/get', {params});
};

export const getWarehousePage = (params) => {
  return commonApi('get', Api.Warehouse + '/page', {params});
};

export const exportWarehouseExcel = (params) => {
  return commonApi('get', Api.Warehouse + '/export-excel', {params});
};

// 数据仓数据集关联
export const createWarehouseDataset = (params) => {
  return commonApi('post', Api.WarehouseDataset + '/create', {params});
};

export const updateWarehouseDataset = (params) => {
  return commonApi('put', Api.WarehouseDataset + '/update', {params});
};

export const deleteWarehouseDataset = (id) => {
  return commonApi('delete', `${Api.WarehouseDataset}/delete?id=${id}`);
};

export const getWarehouseDataset = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/get', {params});
};

export const getWarehouseDatasetPage = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/page', {params});
};

export const exportWarehouseDatasetExcel = (params) => {
  return commonApi('get', Api.WarehouseDataset + '/export-excel', {params});
};

// 视频流帧捕获
export const createDatasetFrameTask = (params) => {
  return commonApi('post', Api.DatasetFrameTask + '/create', {params});
};

export const updateDatasetFrameTask = (params) => {
  return commonApi('put', Api.DatasetFrameTask + '/update', {params});
};

export const deleteDatasetFrameTask = (id) => {
  return commonApi('delete', `${Api.DatasetFrameTask}/delete?id=${id}`);
};

export const getDatasetFrameTask = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/get', {params});
};

export const getDatasetFrameTaskPage = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/page', {params});
};

export const exportDatasetFrameTaskExcel = (params) => {
  return commonApi('get', Api.DatasetFrameTask + '/export-excel', {params});
};
