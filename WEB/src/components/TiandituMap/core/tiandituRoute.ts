import { getTiandituKey } from '../constants';

export type RoadTrackMode = 'face' | 'plate';
export type LonLat = [number, number];

const DRIVE_API = 'https://api.tianditu.gov.cn/drive';
/** 天地图浏览器端 Key 有 QPS 限制：逐段请求留出间隔，被限流时退避后重试一次 */
export const SEGMENT_INTERVAL_MS = 220;
const RATE_LIMIT_RETRY_DELAY_MS = 900;

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timer);
        const error = new Error('aborted');
        error.name = 'AbortError';
        reject(error);
      },
      { once: true },
    );
  });
}

/** 限流等业务错误以 HTTP 200 + JSON 返回（如 {"code":302010,"msg":"该tk已限流"}） */
function parseRateLimitCode(text: string): number | null {
  if (!text.trim().startsWith('{')) return null;
  try {
    const data = JSON.parse(text);
    return typeof data?.code === 'number' ? data.code : null;
  } catch {
    return null;
  }
}

function parseRoadResponse(text: string): LonLat[] {
  const xml = new DOMParser().parseFromString(text, 'text/xml');
  if (xml.querySelector('parsererror')) throw new Error('道路规划结果无法解析');

  const points: LonLat[] = [];
  const pushPoints = (raw: string) => {
    raw.split(';').filter(Boolean).forEach((pair) => {
      const [lng, lat] = pair.split(',').map(Number);
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) return;
      const previous = points[points.length - 1];
      if (!previous || previous[0] !== lng || previous[1] !== lat) points.push([lng, lat]);
    });
  };

  xml.querySelectorAll('simple > item streetLatLon').forEach((node) => pushPoints(String(node.textContent || '')));
  // 短路线（约 300 米内）天地图不返回分街道数据，完整折线改在 routelatlon 节点给出
  if (points.length < 2) pushPoints(xml.querySelector('routelatlon')?.textContent?.trim() || '');

  if (points.length < 2) {
    const message = xml.querySelector('msg, message')?.textContent?.trim();
    throw new Error(message || '未找到可通行道路');
  }
  return points;
}

/**
 * 将两个抓拍点匹配到实际道路。车辆使用驾车策略，人脸使用步行策略。
 * signal 用于在用户切换日期/目标时取消已经过期的规划请求。
 */
export async function planRoadSegment(
  start: LonLat,
  end: LonLat,
  mode: RoadTrackMode,
  signal?: AbortSignal,
): Promise<LonLat[]> {
  const key = import.meta.env.VITE_TIANDITU_ROUTE_KEY || getTiandituKey();
  if (!key) throw new Error('未配置天地图道路规划 Key');
  const postStr = JSON.stringify({
    orig: `${start[0]},${start[1]}`,
    dest: `${end[0]},${end[1]}`,
    mid: '',
    style: mode === 'plate' ? '0' : '3',
  });
  const url = `${DRIVE_API}?postStr=${encodeURIComponent(postStr)}&type=search&tk=${encodeURIComponent(key)}`;
  for (let attempt = 0; ; attempt++) {
    const response = await fetch(url, { signal });
    const text = await response.text();
    const rateLimitCode = parseRateLimitCode(text);
    if (rateLimitCode != null && attempt < 1) {
      await sleep(RATE_LIMIT_RETRY_DELAY_MS, signal);
      continue;
    }
    if (!response.ok) throw new Error(`道路规划请求失败（${response.status}）`);
    if (rateLimitCode != null) throw new Error(`道路规划服务限流（${rateLimitCode}），请稍后重试`);
    return parseRoadResponse(text);
  }
}
