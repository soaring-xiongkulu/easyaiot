import { incrementPatchVersion } from '../../utils/modelVersionUtils';

export const ACTIVE_TRAIN_STATUSES = ['preparing', 'Train', 'train', 'running', 'stopping'];

export const RETRAINABLE_STATUSES = ['stopped', 'completed', 'error', 'failed'];

const TIMEZONE_SUFFIX_RE = /(?:Z|[+-]\d{2}:?\d{2})$/i;

export function formatTrainTaskTime(value?: string): string {
  if (!value) return '--';
  const trimmed = value.trim();
  const timestamp = TIMEZONE_SUFFIX_RE.test(trimmed) ? trimmed : `${trimmed}Z`;
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function isTrainTaskActive(status?: string): boolean {
  return ACTIVE_TRAIN_STATUSES.includes(String(status || ''));
}

export function canRetrainTrainTask(status?: string): boolean {
  return RETRAINABLE_STATUSES.includes(String(status || ''));
}

export function canPublishTrainTask(record?: {
  status?: string;
  minio_model_path?: string;
}): boolean {
  return String(record?.status || '') === 'completed' && !!(record?.minio_model_path || '').trim();
}

export function getPublishedModelId(record?: {
  published_model_id?: number | string | null;
  hyperparameters?: unknown;
}): number | null {
  if (record?.published_model_id != null) {
    const id = Number(record.published_model_id);
    return Number.isNaN(id) ? null : id;
  }
  const hp = parseTrainHyperparameters(record?.hyperparameters);
  if (hp.published_model_id != null) {
    const id = Number(hp.published_model_id);
    return Number.isNaN(id) ? null : id;
  }
  return null;
}

export function getSuggestedPublishVersion(record?: {
  suggested_publish_version?: string | null;
  published_version?: string | null;
  hyperparameters?: unknown;
}): string {
  if (record?.suggested_publish_version) {
    return String(record.suggested_publish_version);
  }
  const hp = parseTrainHyperparameters(record?.hyperparameters);
  if (hp.published_version) {
    return incrementPatchVersion(String(hp.published_version));
  }
  if (record?.published_version) {
    return incrementPatchVersion(String(record.published_version));
  }
  return '1.0.0';
}

export function canResumeTrainTask(record?: {
  status?: string;
  can_resume?: boolean;
  checkpoint_dir?: string;
}): boolean {
  if (!['stopped', 'error', 'failed'].includes(String(record?.status || ''))) return false;
  if (record?.can_resume !== undefined) return record.can_resume === true;
  return !!(record?.checkpoint_dir || '').trim();
}

export function getCompletedEpochs(record?: {
  completed_epochs?: number;
  hyperparameters?: unknown;
}): number {
  if (record?.completed_epochs != null) {
    return Number(record.completed_epochs) || 0;
  }
  const hp = parseTrainHyperparameters(record?.hyperparameters);
  return Number(hp.completed_epochs) || 0;
}

export function formatTrainProgressDetail(record?: {
  status?: string;
  current_epoch?: number;
  total_epochs?: number;
  current_batch?: number;
  total_batches?: number;
  progress_phase?: string;
  completed_epochs?: number;
  hyperparameters?: unknown;
}): string {
  const hp = parseTrainHyperparameters(record?.hyperparameters);
  const totalEpochs = Number(record?.total_epochs ?? hp.epochs) || 0;
  const completedEpochs = getCompletedEpochs(record);
  const currentEpoch = Number(record?.current_epoch ?? hp.current_epoch) || completedEpochs;
  const currentBatch = Number(record?.current_batch ?? hp.current_batch) || 0;
  const totalBatches = Number(record?.total_batches ?? hp.total_batches) || 0;
  const phase = String(record?.progress_phase ?? hp.progress_phase ?? '');

  if (currentEpoch > 0 && totalEpochs > 0) {
    const parts = [`第 ${Math.min(currentEpoch, totalEpochs)}/${totalEpochs} 轮`];
    if (totalBatches > 0) {
      parts.push(`${phase === 'validation' ? '验证' : '批次'} ${Math.min(currentBatch, totalBatches)}/${totalBatches}`);
    }
    return parts.join(' · ');
  }
  if (completedEpochs > 0 && totalEpochs > 0) {
    return `已完成 ${completedEpochs}/${totalEpochs} 轮`;
  }
  return '';
}

export function isCloudDatasetPath(path?: string): boolean {
  if (!path) return false;
  if (path.startsWith('/api/v1/buckets/')) return true;
  return path.includes('://') && !path.startsWith('file://');
}

export function parseTrainHyperparameters(raw: unknown) {
  try {
    const hp = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!hp || typeof hp !== 'object') return {};
    return {
      epochs: hp.epochs ?? 100,
      batch_size: hp.batch_size ?? 16,
      imgsz: hp.img_size ?? hp.imgsz ?? 640,
      modelPath: hp.model_arch ?? 'yolov8n.pt',
      use_gpu: hp.use_gpu !== false,
      gpu_ids: hp.gpu_ids,
      taskName: hp.task_base_name ?? '',
      datasetSource: hp.dataset_source ?? 'local',
      completed_epochs: hp.completed_epochs ?? 0,
      current_epoch: hp.current_epoch ?? 0,
      current_batch: hp.current_batch ?? 0,
      total_batches: hp.total_batches ?? 0,
      progress_phase: hp.progress_phase ?? '',
      progress_updated_at: hp.progress_updated_at ?? null,
      published_model_id: hp.published_model_id ?? null,
      published_version: hp.published_version ?? null,
    };
  } catch {
    return {};
  }
}

export function resolveTaskBaseNameFromRecord(record: Record<string, unknown>): string {
  const hp = parseTrainHyperparameters(record.hyperparameters);
  if (hp.taskName) return hp.taskName;

  let base = String(record.name || record.task_name || '').trim();
  const taskId = record.id as number | undefined;
  if (taskId != null && base.endsWith(`_${taskId}`)) {
    base = base.slice(0, -(`_${taskId}`).length);
  }
  const dsName = String(record.dataset_name || '').trim();
  const dsVersion = String(record.dataset_version || '').trim();
  for (const part of [dsVersion, dsName]) {
    if (part && base.endsWith(`_${part}`)) {
      base = base.slice(0, -(part.length + 1));
    }
  }
  if (isLegacyBadTaskBaseName(base)) {
    return 'train';
  }
  return base || 'train';
}

const LEGACY_TIMESTAMP_BASE_RE = /^train_task_\d{8}_\d{6}$/;
const LEGACY_BAD_TASK_BASE_RE = /^(train_)?download\?prefix=/i;

export function isLegacyBadTaskBaseName(name?: string): boolean {
  const text = (name || '').trim();
  if (!text) return true;
  if (LEGACY_BAD_TASK_BASE_RE.test(text)) return true;
  if (isLegacyBadDatasetName(text)) return true;
  if (LEGACY_TIMESTAMP_BASE_RE.test(text)) return true;
  return text.startsWith('train_task_');
}

/** 训练任务展示名：仅保留用户任务名与任务 ID，数据集信息走独立字段。 */
export function buildTrainTaskDisplayName(
  baseName: string,
  _datasetName?: string,
  _datasetVersion?: string,
  taskId?: number,
): string {
  let base = (baseName || '').trim();
  if (isLegacyBadTaskBaseName(base)) {
    base = 'train';
  }
  if (!base) base = 'train';

  const parts = [base];
  if (taskId != null) parts.push(String(taskId));
  return parts.join('_');
}

const UPLOAD_STORAGE_STEM_RE = /^[0-9a-f]{32}$/i;
const LEGACY_BAD_NAME_RE = /^download\?prefix=/i;

export function isUploadStorageStem(name: string): boolean {
  return UPLOAD_STORAGE_STEM_RE.test((name || '').trim());
}

export function isLegacyBadDatasetName(name?: string): boolean {
  const text = (name || '').trim().replace(/\.zip$/i, '');
  if (!text) return true;
  if (isUploadStorageStem(text)) return true;
  return LEGACY_BAD_NAME_RE.test(text);
}

/** 本地上传数据集展示名：优先可读 dataset_name，避免使用 UUID 存储文件名。 */
export function resolveLocalDatasetDisplayName(
  datasetPath: string,
  datasetName?: string,
): string {
  const stored = (datasetName || '').trim().replace(/\.zip$/i, '');
  if (stored && !isLegacyBadDatasetName(stored)) {
    return stored;
  }
  const pathBase = (datasetPath.split('/').pop() || '').replace(/\.zip$/i, '');
  if (pathBase && !isLegacyBadDatasetName(pathBase)) {
    return pathBase;
  }
  return stored && isLegacyBadDatasetName(stored) ? '本地数据集' : stored || pathBase || '本地数据集';
}
