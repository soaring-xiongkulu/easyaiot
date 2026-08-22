import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';

export interface SnapshotQualityResult {
  valid: boolean;
  isGrey: boolean;
  loadable: boolean;
}

export interface SnapshotCapturePolicy {
  maxRetries: number;
  retryGapMs: number;
  preCaptureWaitMs: number;
  postCaptureWaitMs: number;
}

const DEFAULT_POLICY: SnapshotCapturePolicy = {
  maxRetries: 3,
  retryGapMs: 1500,
  preCaptureWaitMs: 0,
  postCaptureWaitMs: 400,
};

const GB28181_POLICY: SnapshotCapturePolicy = {
  maxRetries: 3,
  retryGapMs: 2000,
  preCaptureWaitMs: 5000,
  postCaptureWaitMs: 600,
};

/** 判断是否为 GB28181 类设备（点播出图较慢） */
export function isGb28181Device(device?: {
  id?: string;
  name?: string;
  source?: string | null;
  device_kind?: string | null;
} | null): boolean {
  if (!device) return false;
  const kind = String(device.device_kind || '').toLowerCase();
  if (kind === 'gb28181' || kind === 'gb28181_sip') return true;
  const source = String(device.source || '').toLowerCase();
  if (source.includes('gb28181')) return true;
  const id = String(device.id || '').toLowerCase();
  if (id.startsWith('gb28181_')) return true;
  const name = String(device.name || '');
  if (name.includes('GB28181') || name.includes('[GB28181]')) return true;
  return false;
}

export function getSnapshotCapturePolicy(device?: Parameters<typeof isGb28181Device>[0]): SnapshotCapturePolicy {
  return isGb28181Device(device) ? { ...GB28181_POLICY } : { ...DEFAULT_POLICY };
}

function analyzeImageData(data: Uint8ClampedArray, pixelCount: number): SnapshotQualityResult {
  if (pixelCount <= 0) {
    return { valid: false, isGrey: false, loadable: true };
  }

  let sumR = 0;
  let sumG = 0;
  let sumB = 0;
  const luminances: number[] = [];

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    sumR += r;
    sumG += g;
    sumB += b;
    luminances.push(0.299 * r + 0.587 * g + 0.114 * b);
  }

  const mean = luminances.reduce((acc, v) => acc + v, 0) / pixelCount;
  const variance = luminances.reduce((acc, v) => acc + (v - mean) ** 2, 0) / pixelCount;
  const stdDev = Math.sqrt(variance);

  const avgR = sumR / pixelCount;
  const avgG = sumG / pixelCount;
  const avgB = sumB / pixelCount;
  const chroma = Math.max(Math.abs(avgR - avgG), Math.abs(avgG - avgB), Math.abs(avgR - avgB));

  // 低方差 + 低色度 ≈ 灰屏/黑屏/未出图
  const isGrey =
    stdDev < 10 ||
    (stdDev < 18 && chroma < 14) ||
    (mean < 18 && stdDev < 22) ||
    (mean > 210 && stdDev < 18);

  return {
    valid: !isGrey,
    isGrey,
    loadable: true,
  };
}

function loadImageElement(url: string, useCors: boolean): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    if (useCors) {
      img.crossOrigin = 'anonymous';
    }
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

function sampleImageQuality(img: HTMLImageElement): SnapshotQualityResult {
  const sampleW = Math.min(160, img.naturalWidth);
  const sampleH = Math.min(160, img.naturalHeight);
  const canvas = document.createElement('canvas');
  canvas.width = sampleW;
  canvas.height = sampleH;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) {
    return { valid: true, isGrey: false, loadable: true };
  }

  try {
    ctx.drawImage(img, 0, 0, sampleW, sampleH);
    const { data } = ctx.getImageData(0, 0, sampleW, sampleH);
    return analyzeImageData(data, sampleW * sampleH);
  } catch {
    // 跨域无法读像素时，仅校验尺寸
    return { valid: true, isGrey: false, loadable: true };
  }
}

/** 校验抓图是否可加载且非灰屏 */
export async function verifySnapshotQuality(
  rawPath: string,
  options?: { bustCache?: boolean },
): Promise<SnapshotQualityResult> {
  const baseUrl = resolveAlertImageDisplayUrl(rawPath);
  if (!baseUrl) {
    return { valid: false, isGrey: false, loadable: false };
  }

  const url = options?.bustCache
    ? `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}_t=${Date.now()}`
    : baseUrl;

  let img = await loadImageElement(url, true);
  if (!img) {
    img = await loadImageElement(url, false);
  }
  if (!img || !img.naturalWidth || !img.naturalHeight) {
    return { valid: false, isGrey: false, loadable: false };
  }

  return sampleImageQuality(img);
}

export function sleep(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });
}
