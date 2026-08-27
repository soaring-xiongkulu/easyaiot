import { queryAlertRecord } from '@/api/device/calculate';
import { isHostLocalMediaPath, resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';

/** 是否为 MinIO 录像下载地址（与后端 on_dvr 写入的 record_path / playback.file_path 一致） */
export function isMinioRecordDownloadPath(path: string | null | undefined): boolean {
  if (!path) return false;
  const p = path.trim();
  if (p.startsWith('/api/v1/buckets/') && p.includes('/objects/download')) {
    return true;
  }
  if (p.startsWith('http://') || p.startsWith('https://')) {
    return p.includes('/api/v1/buckets/') || p.includes('/objects/download');
  }
  return false;
}

/** 宿主机 SRS 本地路径，上传 MinIO 后不可用于浏览器直连播放 */
function isHostLocalRecordPath(path: string): boolean {
  const p = path.trim();
  return (
    p.startsWith('/data/playbacks') ||
    p.startsWith('/data/') ||
    p.startsWith('/app/') ||
    /\.flv$/i.test(p) && p.startsWith('/')
  );
}

/** 是否为点播/录像文件 URL（非实时流） */
export function isVodPlaybackUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  const u = String(url).trim();
  return (
    u.includes('/video/alert/record') ||
    u.includes('/video/record/space/') ||
    /\/video\/media\/assets\/[^/?#]+\/content(?:[?#]|$)/.test(u) ||
    (u.includes('/api/v1/buckets/') && u.includes('/objects/download'))
  );
}

function toAbsolutePlayUrl(url: string): string {
  if (!url || url.startsWith('http://') || url.startsWith('https://')) {
    return url || '';
  }
  if (typeof window === 'undefined') return url;
  const path = url.startsWith('/') ? url : `/${url}`;
  return `${window.location.origin}${path}`;
}

/** 将 MinIO/相对路径转为可播放的完整 URL */
export function resolveAlertVideoUrl(videoUrl: string): string {
  if (!videoUrl) return '';
  if (videoUrl.startsWith('http://') || videoUrl.startsWith('https://')) {
    return videoUrl;
  }
  if (videoUrl.startsWith('/api/v1/buckets')) {
    return toAbsolutePlayUrl(videoUrl);
  }
  if (videoUrl.startsWith('/video/')) {
    return toAbsolutePlayUrl(resolveAlertImageDisplayUrl(videoUrl));
  }
  if (isHostLocalMediaPath(videoUrl)) {
    const apiPrefix = (import.meta.env.VITE_GLOB_API_URL || '').replace(/\/$/, '');
    return toAbsolutePlayUrl(`${apiPrefix}/video/alert/record?path=${encodeURIComponent(videoUrl)}`);
  }
  if (videoUrl.startsWith('/')) {
    return toAbsolutePlayUrl(`${import.meta.env.VITE_GLOB_API_URL || ''}${videoUrl}`);
  }
  return videoUrl;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export type AlertRecordLike = {
  id?: number | string;
  device_id?: string;
  time?: string;
  record_path?: string | null;
};

/**
 * 解析告警录像播放地址：优先 record_path（MinIO），否则按设备+时间查 Playback。
 * on_dvr 上传后可能有几秒延迟，失败时会自动重试一次。
 */
export async function resolveAlertRecordVideoUrl(
  record: AlertRecordLike,
  options?: { timeRange?: number; retryDelayMs?: number },
): Promise<string | null> {
  const timeRange = options?.timeRange ?? 300;
  const retryDelayMs = options?.retryDelayMs ?? 2500;

  const directPath = record.record_path?.trim();
  if (directPath) {
    if (isMinioRecordDownloadPath(directPath)) {
      return resolveAlertVideoUrl(directPath);
    }
    if (isHostLocalMediaPath(directPath)) {
      return resolveAlertVideoUrl(directPath);
    }
    if (directPath.startsWith('/video/')) {
      return resolveAlertVideoUrl(directPath);
    }
    if (isHostLocalRecordPath(directPath)) {
      console.warn(
        '[alertRecord] record_path 为宿主机本地路径，已忽略并改查 playback/MinIO:',
        directPath,
      );
    } else {
      console.warn('[alertRecord] record_path 非 MinIO 下载地址，改查 playback:', directPath);
    }
  }

  if (!record.device_id || !record.time) {
    return null;
  }

  const params = {
    device_id: String(record.device_id),
    alert_time: record.time,
    time_range: timeRange,
    ...(record.id != null ? { alert_id: record.id } : {}),
  };

  const tryQuery = async () => {
    const result = await queryAlertRecord(params);
    const url = result?.video_url || result?.file_path;
    return url ? resolveAlertVideoUrl(url) : null;
  };

  let url = await tryQuery();
  if (!url && retryDelayMs > 0) {
    await sleep(retryDelayMs);
    url = await tryQuery();
  }
  return url;
}
