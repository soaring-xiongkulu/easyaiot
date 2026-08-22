/**
 * 告警/抓拍/录像/模型图片展示地址解析。
 * - MinIO：/api/v1/buckets/... 经 nginx 同源代理
 * - VIDEO API：/video/... 前缀 /dev-api
 * - mini 本地绝对路径：/data/... 经 VIDEO alert/image 代理
 */
export function isHostLocalMediaPath(path: string | null | undefined): boolean {
  if (!path) return false;
  const p = String(path).trim();
  if (!p.startsWith('/')) return false;
  if (p.startsWith('/api/') || p.startsWith('/video/')) return false;
  return (
    p.startsWith('/data/') ||
    p.startsWith('/mnt/') ||
    p.startsWith('/app/') ||
    p.startsWith('/tmp/')
  );
}

function resolveVideoApiPath(path: string): string {
  const apiPrefix = (import.meta.env.VITE_GLOB_API_URL || '').replace(/\/$/, '');
  return `${apiPrefix}${path}`;
}

function normalizeMinioDownloadPath(path: string): string {
  const qIndex = path.indexOf('?');
  if (qIndex < 0) return path;
  const base = path.slice(0, qIndex);
  const params = new URLSearchParams(path.slice(qIndex + 1));
  const prefix = params.get('prefix');
  if (prefix) {
    params.set('prefix', prefix);
    return `${base}?${params.toString()}`;
  }
  return path;
}

export function resolveAlertImageDisplayUrl(imageUrl: string | null | undefined): string {
  if (imageUrl == null || String(imageUrl).trim() === '') return '';
  const u = String(imageUrl).trim();
  if (u.startsWith('http://') || u.startsWith('https://')) return u;
  if (u.startsWith('/api/v1/buckets/')) {
    return `${window.location.origin}${normalizeMinioDownloadPath(u)}`;
  }
  if (u.startsWith('/video/')) {
    return resolveVideoApiPath(u);
  }
  if (isHostLocalMediaPath(u)) {
    return resolveVideoApiPath(`/video/alert/image?path=${encodeURIComponent(u)}`);
  }
  if (u.startsWith('/')) {
    return `${window.location.origin}${u}`;
  }
  return u;
}

/**
 * 训练结果图：历史数据写在 model-train 桶，对象 key 与 models 桶中一致，统一走 models 桶访问。
 */
export function resolveTrainResultsDisplayUrl(imageUrl: string | null | undefined): string {
  if (imageUrl == null || String(imageUrl).trim() === '') return '';
  let u = String(imageUrl).trim();
  if (u.includes('/api/v1/buckets/model-train/')) {
    u = u.replace('/api/v1/buckets/model-train/', '/api/v1/buckets/models/');
  }
  return resolveAlertImageDisplayUrl(u);
}

/** 模型管理封面图 */
export function resolveModelImageDisplayUrl(imageUrl: string | null | undefined): string {
  return resolveAlertImageDisplayUrl(imageUrl);
}

function isLocalMinioHost(hostname: string): boolean {
  const h = hostname.toLowerCase();
  return h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0';
}

/** 将 MinIO 直链 http(s)://host/bucket/key 转为 nginx 同源代理路径 */
function convertDirectMinioUrlToDownloadPath(url: string): string {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname.replace(/^\/+/, '');
    const slashIdx = path.indexOf('/');
    if (slashIdx <= 0) return url;
    const bucket = path.slice(0, slashIdx);
    const objectName = path.slice(slashIdx + 1);
    if (!objectName) return url;
    return `/api/v1/buckets/${bucket}/objects/download?prefix=${encodeURIComponent(objectName)}`;
  } catch {
    return url;
  }
}

/**
 * 人脸库 / 车牌库图片展示地址。
 * 兼容历史数据中的 http://localhost:9000/{bucket}/{key} 直链。
 */
export function resolveLibraryImageDisplayUrl(imageUrl: string | null | undefined): string {
  if (imageUrl == null || String(imageUrl).trim() === '') return '';
  const u = String(imageUrl).trim();
  if (u.startsWith('http://') || u.startsWith('https://')) {
    try {
      const parsed = new URL(u);
      if (isLocalMinioHost(parsed.hostname)) {
        return resolveAlertImageDisplayUrl(convertDirectMinioUrlToDownloadPath(u));
      }
    } catch {
      return u;
    }
    return u;
  }
  return resolveAlertImageDisplayUrl(u);
}
