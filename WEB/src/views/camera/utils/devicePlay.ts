import type { DeviceInfo, MonitorTreeDeviceNode } from '@/api/device/camera';
import { getDeviceInfo } from '@/api/device/camera';
import { ensureDeviceStreamForwardTask } from '@/api/device/stream_forward';
import { playByDeviceAndChannel } from '@/api/device/gb28181';
import {
  formatCameraDeviceLabel,
  gb28181VirtualDeviceId,
  getGb28181PlayIds,
  isGb28181Device,
  shouldPlayViaGb28181,
} from './deviceLabel';
import { isProtectedStreamUrl, signStreamUrl } from './streamTicket';

export type DevicePlayModalOpener = (visible: boolean, data: Record<string, any>) => void;

function parseProviderJson(value: unknown): Record<string, any> | null {
  if (!value) return null;
  if (typeof value === 'object') return value as Record<string, any>;
  if (typeof value !== 'string') return null;
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

/** 从设备记录中提取火山 RTC（volc）播放地址 */
export function extractVolcLiveUrl(record: Record<string, any> | null | undefined): string | null {
  if (!record) return null;
  const provider =
    parseProviderJson(record.provider) ||
    parseProviderJson(record.live_provider) ||
    parseProviderJson(record.providerJson) ||
    parseProviderJson(record.provider_json);

  const providerType = String(
    provider?.url_type || provider?.type || record.providerType || record.urlType || '',
  ).toLowerCase();
  const providerUrl = String(provider?.url || '').trim();
  if (providerType === 'volc' && providerUrl) return providerUrl;

  for (const candidate of [record.source, record.url, record.directUrl]) {
    const value = String(candidate || '').trim();
    if (!value) continue;
    if (value.startsWith('volc://')) return decodeURIComponent(value.slice('volc://'.length));
  }
  return null;
}

export function isGb28181DeviceRecord(record: { source?: string | null; device_kind?: string }) {
  return isGb28181Device(record.source, record.device_kind);
}

export function hasDirectPlayStream(record: DeviceInfo, ai = false): boolean {
  if (isGb28181DeviceRecord(record)) return false;
  if ((record as { device_kind?: string }).device_kind === 'gb28181_sip') return false;
  if (!ai && extractVolcLiveUrl(record as Record<string, any>)) return true;
  if (ai) {
    return !!(record.ai_http_stream || record.ai_rtmp_stream);
  }
  return !!(record.http_stream || record.rtmp_stream);
}

/** 设备是否具备可播放流（原始流、AI 流或国标点播） */
export function hasPlayableStream(record: DeviceInfo): boolean {
  if (shouldPlayViaGb28181(record)) return true;
  return hasDirectPlayStream(record) || hasDirectPlayStream(record, true);
}

type DirectStreamFields = Pick<
  DeviceInfo,
  'http_stream' | 'rtmp_stream' | 'ai_http_stream' | 'ai_rtmp_stream'
>;

export interface DirectPlayUrlResult {
  url: string | null;
  /** 启用 AI 时，AI 地址不可播则回退原始流 */
  fallbackUrl?: string | null;
  /** 已探测到 AI 流在推流，播放器超时后再回退原始流 */
  preferAi?: boolean;
  /** 首帧先播原始流后，后台探测就绪可升级的 AI 地址 */
  pendingAiUrl?: string | null;
}

/** 探测 AI 流是否在 ZLM 上就绪（毫秒） */
export const AI_STREAM_PROBE_MS = 1200;
/** 多分屏探测宜更短，避免空 /ai 长时间占连接 */
export const AI_STREAM_PROBE_MULTI_VIEW_MS = 900;
/** 直连 AI 流起播超时后回退原始流（毫秒，仅 preferAi 时生效） */
export const AI_PLAY_FALLBACK_MS = 2500;
/** Jessibuca 播 /ai 且可回退时，加载/心跳超时（秒），尽快触发 stream-error */
export const AI_STREAM_LOAD_TIMEOUT_SEC = 3;
export const AI_STREAM_HEART_TIMEOUT_SEC = 8;

const LOCAL_STREAM_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0']);

/**
 * RFC1918 私网 + 169.254 链路本地地址。此类 host 通常是媒体节点自身探测到的内网 IP，
 * 公网/跨网页面浏览器无法直连，须改写为页面 host 交由 nginx 反代。
 */
function isPrivateLanHost(host: string): boolean {
  const m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.\d{1,3}$/.exec(host || '');
  if (!m) return false;
  const a = Number(m[1]);
  const b = Number(m[2]);
  if (a === 10) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  if (a === 169 && b === 254) return true;
  return false;
}

/** 流是否在远端集群 SRS/ZLM 节点（页面 nginx 无法代理，须保留原 host） */
function isRemoteClusterStreamHost(streamHost: string, pageHostname: string): boolean {
  if (!streamHost || !pageHostname) return false;
  if (LOCAL_STREAM_HOSTS.has(streamHost) || LOCAL_STREAM_HOSTS.has(pageHostname)) return false;
  // 私网/链路本地 IP 不是可直连的远端集群节点，改写为页面 host 经 nginx 代理
  if (isPrivateLanHost(streamHost)) return false;
  return streamHost !== pageHostname;
}

/** 将服务端生成的 127.0.0.1/localhost 流地址改写为当前页面主机名，便于浏览器拉流 */
export function rewriteStreamUrlForBrowser(url: string): string {
  const trimmed = url?.trim();
  if (!trimmed || typeof window === 'undefined') return trimmed;

  try {
    const parsed = new URL(trimmed);
    const pageHost = window.location.hostname;
    if (!pageHost || LOCAL_STREAM_HOSTS.has(pageHost)) return trimmed;
    if (!LOCAL_STREAM_HOSTS.has(parsed.hostname)) return trimmed;

    parsed.hostname = pageHost;
    return parsed.toString();
  } catch {
    return trimmed;
  }
}

/**
 * 将流地址的主机名+端口改写为当前页面的 host（hostname:port），便于浏览器拉流。
 * 例如页面在 http://localhost:8888 打开时，
 * http://33.150.1.104:8080/ai/xxx.flv -> http://localhost:8888/ai/xxx.flv
 * 仅替换 host，协议与路径保持不变。
 * forcePageProxy 用于明确知道当前页面 nginx 已代理媒体路径的入口，避免反向代理页面
 * 仍按服务端返回的远端 host:port 直连媒体服务。
 */
export function rewriteStreamHostToPageHost(
  url: string,
  options?: { forcePageProxy?: boolean },
): string {
  const trimmed = url?.trim();
  if (!trimmed || typeof window === 'undefined') return trimmed;

  try {
    const parsed = new URL(trimmed);
    const pageHostname = window.location.hostname;
    if (!pageHostname) return trimmed;

    // 集群模式：流在远端 SRS/ZLM 节点，nginx 仅代理本机 srs-host，不应改写为页面 host
    if (!options?.forcePageProxy && isRemoteClusterStreamHost(parsed.hostname, pageHostname)) {
      return trimmed;
    }

    // mini/单机：SRS(8080)/ZLM(6080) 等本机媒体流由页面 nginx 反代，改写为当前页面 host。
    // 用 hostname+port 分别赋值：页面在默认端口(443/80)时 window.location.port 为空，
    // 借此清掉流地址上的 8080/6080，避免浏览器直连（公网常关闭）的媒体端口。
    parsed.hostname = pageHostname;
    parsed.port = window.location.port;
    return parsed.toString();
  } catch {
    return trimmed;
  }
}

/**
 * 规范化 Jessibuca 播放地址。
 * SRS 的 /live、/ai 经页面 nginx 或 Vite 代理时须用 HTTP-FLV（GET 长连接）；
 * 改为 ws:// 时 Vite 开发环境常握手失败（Unexpected response code: 200）。
 * 国标 /rtp 仍保留 ws-flv（ZLM）。
 */
export function normalizeJessibucaPlayUrl(url: string): string {
  const trimmed = url?.trim();
  if (!trimmed || typeof window === 'undefined') return trimmed;

  try {
    const parsed = new URL(trimmed);
    if (/^\/(ai|live)\//i.test(parsed.pathname)) {
      if (parsed.protocol === 'ws:') parsed.protocol = 'http:';
      if (parsed.protocol === 'wss:') parsed.protocol = 'https:';
      // https 页面直连 http-flv 会被浏览器按 mixed-content 拦截。
      // 仅升级已改写成页面 host 的地址（单机经页面 nginx 反代，随页面出 https）；
      // 远端集群节点 host 未改写、其 8080 未必有 TLS，不能盲目升级。
      if (
        window.location.protocol === 'https:' &&
        parsed.protocol === 'http:' &&
        parsed.host === window.location.host
      ) {
        parsed.protocol = 'https:';
      }
      return parsed.toString();
    }
    return trimmed;
  } catch {
    return trimmed;
  }
}

/** @deprecated 仅 ZLM /rtp 等已确认支持 WS 代理的场景使用；SRS /live 请用 HTTP-FLV */
export function preferWsFlvForJessibuca(url: string): string {
  const trimmed = url?.trim();
  if (!trimmed || typeof window === 'undefined') return trimmed;

  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === 'ws:' || parsed.protocol === 'wss:') return trimmed;
    if (!/\.flv(\?|$)/i.test(parsed.pathname)) return trimmed;
    if (parsed.protocol === 'http:') {
      parsed.protocol = 'ws:';
      return parsed.toString();
    }
    if (parsed.protocol === 'https:') {
      parsed.protocol = 'wss:';
      return parsed.toString();
    }
    return trimmed;
  } catch {
    return trimmed;
  }
}

/** fetch 探测流可用性须用 HTTP(S)，不能走 WS */
export function flvUrlForHttpProbe(url: string): string {
  const trimmed = url?.trim();
  if (!trimmed) return trimmed;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === 'ws:') parsed.protocol = 'http:';
    else if (parsed.protocol === 'wss:') parsed.protocol = 'https:';
    return parsed.toString();
  } catch {
    return trimmed;
  }
}

/** RTMP 转 HTTP-FLV（Jessibuca 浏览器端需 HTTP/WS 地址） */
export function convertRtmpToHttp(rtmpUrl: string): string | null {
  const trimmed = rtmpUrl?.trim();
  if (!trimmed || !trimmed.startsWith('rtmp://')) {
    return null;
  }
  try {
    const url = new URL(trimmed);
    const server = url.hostname;
    let path = url.pathname.replace(/^\//, '');
    if (!path) path = 'live';
    if (!path.endsWith('.flv')) path = `${path}.flv`;
    return rewriteStreamUrlForBrowser(`http://${server}:8080/${path}`);
  } catch {
    return null;
  }
}

function toBrowserPlayUrl(stream?: string | null): string | null {
  const trimmed = stream?.trim();
  if (!trimmed) return null;
  const httpUrl = trimmed.startsWith('rtmp://') ? convertRtmpToHttp(trimmed) : trimmed;
  if (!httpUrl) return null;
  // 所有播放地址统一走当前页面 host:port，便于不同环境下浏览器直接拉流（HTTP-FLV）
  return normalizeJessibucaPlayUrl(rewriteStreamHostToPageHost(httpUrl));
}

/**
 * 多分屏播放地址：
 * - 页面已是 HTTP/2/3：同 origin 多路复用，直接用页面 host（最终方案）
 * - 否则（Vite HTTP/1.1）：自动轮换 127.0.0.1..N 扩连接池（本机打开时）
 */
let multiViewOriginSeq = 0;

/** 回环 origin 池大小；可用 VITE_MULTIVIEW_LOOPBACK_POOL 覆盖（1~254） */
function multiViewLoopbackPoolSize(): number {
  const raw =
    typeof import.meta !== 'undefined'
      ? Number((import.meta as any).env?.VITE_MULTIVIEW_LOOPBACK_POOL)
      : NaN;
  if (Number.isFinite(raw) && raw >= 1) return Math.min(254, Math.floor(raw));
  return 64;
}

function isLocalDevPageHost(host: string): boolean {
  return host === 'localhost' || host.startsWith('127.') || host === '[::1]' || host === '::1';
}

/** 当前页面文档是否已经走 HTTP/2 或 HTTP/3（可多路复用，无需 127.x 池） */
export function pageUsesHttp2(): boolean {
  if (typeof performance === 'undefined') return false;
  try {
    const nav = performance.getEntriesByType('navigation')[0] as
      | PerformanceNavigationTiming
      | undefined;
    const proto = (nav?.nextHopProtocol || '').toLowerCase();
    return proto === 'h2' || proto === 'h2c' || proto.startsWith('h3');
  } catch {
    return false;
  }
}

function resolveMultiViewMediaPort(): string {
  if (typeof window === 'undefined') return '';
  return window.location.port || '';
}

/** 自动生成多分屏 hostname 列表 */
function collectMultiViewPageHosts(): string[] {
  const pageHost = (typeof window !== 'undefined' && window.location.hostname) || 'localhost';
  const hosts: string[] = [];
  const push = (h?: string | null) => {
    const host = (h || '').trim();
    if (!host || hosts.includes(host)) return;
    hosts.push(host);
  };

  // HTTP/2/3：一条连接多路复用，保持单一 origin
  if (pageUsesHttp2()) {
    return [pageHost];
  }

  if (isLocalDevPageHost(pageHost)) {
    const n = multiViewLoopbackPoolSize();
    for (let i = 1; i <= n; i += 1) {
      push(`127.0.0.${i}`);
    }
  } else {
    push(pageHost);
    const envHosts = String(
      (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_MULTIVIEW_EXTRA_HOSTS) || '',
    )
      .split(/[\s,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    for (const h of envHosts) push(h);
  }

  return hosts.length ? hosts : [pageHost];
}

export function toMultiViewPlayUrl(url?: string | null): string | null {
  const trimmed = url?.trim();
  if (!trimmed) return null;
  if (typeof window === 'undefined') return trimmed;
  try {
    const httpUrl = trimmed.startsWith('rtmp://') ? convertRtmpToHttp(trimmed) : trimmed;
    if (!httpUrl) return null;
    const pageUrl = rewriteStreamHostToPageHost(httpUrl);
    const parsed = new URL(pageUrl);
    const path = parsed.pathname || '';
    if (!/^\/(live|ai|rtp)\//i.test(path)) {
      return pageUrl;
    }
    const hosts = collectMultiViewPageHosts();
    const host = hosts[multiViewOriginSeq++ % hosts.length]!;
    const port = resolveMultiViewMediaPort();
    parsed.protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    parsed.hostname = host;
    if (port) parsed.port = port;
    else parsed.port = '';
    return parsed.toString();
  } catch {
    return trimmed;
  }
}

/** 是否为算法任务输出的 AI 流（检测框烧录在此路流上） */
export function isAiStreamPlayUrl(url?: string | null): boolean {
  if (!url) return false;
  return /\/ai\//i.test(url);
}

function pickVideoPlayUrl(device: DirectStreamFields): string | null {
  return toBrowserPlayUrl(device.http_stream) || toBrowserPlayUrl(device.rtmp_stream);
}

function pickAiPlayUrl(device: DirectStreamFields): string | null {
  return toBrowserPlayUrl(device.ai_http_stream) || toBrowserPlayUrl(device.ai_rtmp_stream);
}

/** 探测时判定"真有推流"所需的最小媒体字节数（FLV 头仅 13B，无推流方时只回头部就停） */
const PROBE_MIN_MEDIA_BYTES = 1024;

/**
 * 快速探测流是否可播（避免无算法任务时长时间等待空 AI 地址）。
 * 仅返回 200/FLV 头不足为据：SRS 对任何 FLV 请求都会临时创建空源并回头部，
 * 因此必须确认在超时窗口内确有媒体数据流过，才认定 AI 流已就绪。
 * 探测失败时返回 false，调用方应直接播原始流。
 */
export async function probeStreamPlayable(
  url: string,
  timeoutMs = AI_STREAM_PROBE_MS,
): Promise<boolean> {
  let target = url?.trim();
  if (!target || typeof window === 'undefined') return false;
  target = flvUrlForHttpProbe(target);
  // 探测时若落在页面 host，轮换到 127.0.0.1:同端口，避免与播放抢同一 origin 的 6 路连接
  try {
    const u = new URL(target);
    if (
      /^\/(live|ai)\//i.test(u.pathname) &&
      typeof window !== 'undefined' &&
      u.port === window.location.port
    ) {
      if (u.hostname === 'localhost') u.hostname = '127.0.0.1';
      else if (u.hostname === '127.0.0.1') u.hostname = 'localhost';
      target = u.toString();
    }
  } catch {
    /* keep target */
  }
  // 探测直连 fetch /ai 地址，受 secure_link 保护，需先签名（开启强制校验时未签名恒 403）。
  // 签发失败则降级探测未签名地址：强制校验关闭时仍能正常探测，开启时会 403 -> 探测返回 false -> 回退原始流。
  if (isProtectedStreamUrl(target)) {
    try {
      target = await signStreamUrl(target);
    } catch {
      /* 降级：保留未签名地址继续探测 */
    }
  }
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(target, {
      method: 'GET',
      signal: controller.signal,
      cache: 'no-store',
    });
    if (res.status === 404 || res.status === 403) return false;
    if (!res.ok && res.status !== 206) return false;
    if (!res.body) return false;

    const reader = res.body.getReader();
    let received = 0;
    try {
      while (received < PROBE_MIN_MEDIA_BYTES) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) received += value.length;
      }
    } finally {
      // 停止拉流，释放 SRS 上的临时消费连接
      try {
        await reader.cancel();
      } catch {
        /* ignore */
      }
    }
    return received >= PROBE_MIN_MEDIA_BYTES;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timer);
  }
}

/** 直连设备播放地址：启用 AI 时优先 AI 流，无 AI 地址则回退原始流；未启用时仅原始流 */
export async function pickDirectPlayUrl(
  device: DirectStreamFields,
  enableAi = false,
): Promise<string | null> {
  return (await pickDirectPlayUrls(device, enableAi)).url;
}

export async function pickDirectPlayUrls(
  device: DirectStreamFields,
  enableAi = false,
): Promise<DirectPlayUrlResult> {
  const videoUrl = pickVideoPlayUrl(device);
  if (!enableAi) {
    return { url: videoUrl };
  }

  const aiUrl = pickAiPlayUrl(device);
  if (!aiUrl) {
    return { url: videoUrl };
  }
  if (aiUrl === videoUrl) {
    return { url: aiUrl };
  }
  if (!videoUrl) {
    return { url: aiUrl, preferAi: true };
  }

  // 启用 AI：优先直接播 /ai（算法任务只推 app=ai）；失败再由播放器回退 /live。
  // 若先播空 /live，SRS 会挂起无响应，多分屏会一直「视频加载中」。
  return { url: aiUrl, fallbackUrl: videoUrl, preferAi: true };
}

/** 全局串行 AI 探测，避免多分屏同时 fetch 空 /ai 占满浏览器连接池 */
const AI_UPGRADE_PROBE_LIMIT = 1;
let aiUpgradeProbeActive = 0;
const aiUpgradeProbeWaiters: Array<() => void> = [];

function enqueueAiUpgradeProbe<T>(job: () => Promise<T>): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const run = () => {
      aiUpgradeProbeActive += 1;
      job()
        .then(resolve, reject)
        .finally(() => {
          aiUpgradeProbeActive -= 1;
          const next = aiUpgradeProbeWaiters.shift();
          if (next) next();
        });
    };
    if (aiUpgradeProbeActive < AI_UPGRADE_PROBE_LIMIT) run();
    else aiUpgradeProbeWaiters.push(run);
  });
}

export type PendingAiUpgradeOptions = {
  /** 探测超时，默认 AI_STREAM_PROBE_MS */
  probeMs?: number;
  /** 起播后再延迟探测，避免与首屏 /live 抢连接 */
  delayMs?: number;
  /** 是否走全局串行探测（默认 true） */
  serialize?: boolean;
};

/**
 * 首帧已播原始流后，后台探测 AI 就绪再升级（分屏/大屏/弹窗共用）。
 * 多分屏务必 serialize + delay，否则空 /ai 会把连接池打满导致全屏卡死。
 */
export function schedulePendingAiStreamUpgrade(
  aiUrl: string,
  fallbackUrl: string,
  shouldUpgrade: () => boolean,
  onUpgrade: () => void,
  options?: PendingAiUpgradeOptions,
): void {
  const ai = aiUrl?.trim();
  const fb = fallbackUrl?.trim();
  if (!ai || !fb || ai === fb) return;

  const probeMs = options?.probeMs ?? AI_STREAM_PROBE_MS;
  const delayMs = Math.max(0, options?.delayMs ?? 0);
  const serialize = options?.serialize !== false;

  const run = async () => {
    if (delayMs > 0) {
      await new Promise<void>((r) => window.setTimeout(r, delayMs));
    }
    if (!shouldUpgrade()) return;
    const ready = await probeStreamPlayable(ai, probeMs);
    if (!ready || !shouldUpgrade()) return;
    onUpgrade();
  };

  if (serialize) {
    void enqueueAiUpgradeProbe(run);
  } else {
    void run();
  }
}

export function supportsRtspForward(record: DeviceInfo): boolean {
  return !isGb28181DeviceRecord(record);
}

/** 从 WVP 点播结果中选取浏览器可播地址（HTTPS 页优先 wss/https，并做 localhost 改写） */
export function pickWvpPlayUrl(streamContent: Record<string, any> | null | undefined): string | null {
  if (!streamContent) return null;
  const isHttps =
    typeof window !== 'undefined' && window.location.protocol === 'https:';
  const candidates = isHttps
    ? [
        streamContent.wss_flv,
        streamContent.https_flv,
        streamContent.wss_fmp4,
        streamContent.https_fmp4,
        streamContent.ws_flv,
        streamContent.flv,
        streamContent.fmp4,
      ]
    : [
        streamContent.ws_flv,
        streamContent.flv,
        streamContent.ws_fmp4,
        streamContent.fmp4,
        streamContent.https_flv,
        streamContent.wss_flv,
      ];
  for (const raw of candidates) {
    const url = toBrowserPlayUrl(raw);
    if (url) return url;
  }
  return toBrowserPlayUrl(streamContent.rtmp);
}

export async function resolveGb28181StreamUrl(
  sipDeviceId: string,
  channelId: string,
): Promise<string | null> {
  const res = await playByDeviceAndChannel(sipDeviceId, channelId);
  const streamContent = (res as any)?.data?.data ?? (res as any)?.data;
  return pickWvpPlayUrl(streamContent);
}

export interface GbChannelPlayUrlResult {
  url: string | null;
  fallbackUrl?: string | null;
  preferAi?: boolean;
  pendingAiUrl?: string | null;
}

/** 加载国标通道对应的 device 表记录（含 ai_http_stream） */
export async function loadGbChannelSyncedDevice(
  sipDeviceId: string,
  channelId: string,
  synced?: MonitorTreeDeviceNode | null,
): Promise<MonitorTreeDeviceNode | null> {
  if (synced?.ai_http_stream?.trim() || synced?.ai_rtmp_stream?.trim()) {
    return synced;
  }
  // 目录树已有同步设备但无 AI 地址时，跳过详情请求，直接走 WVP 点播
  if (synced?.id) {
    return synced;
  }
  try {
    const res = await getDeviceInfo(gb28181VirtualDeviceId(sipDeviceId, channelId));
    const device = (res as any)?.data ?? res;
    return device?.id ? (device as MonitorTreeDeviceNode) : synced ?? null;
  } catch {
    return synced ?? null;
  }
}

/**
 * 国标通道播放地址：启用 AI 时优先 ai_http_stream（算法烧录检测框），否则 WVP 点播原始流。
 */
export async function resolveGbChannelPlayUrls(
  sipDeviceId: string,
  channelId: string,
  options?: {
    enableAi?: boolean;
    synced?: MonitorTreeDeviceNode | null;
    wvpUrl?: string | null;
  },
): Promise<GbChannelPlayUrlResult> {
  const enableAi = options?.enableAi ?? false;
  const wvpPromise =
    options?.wvpUrl != null
      ? Promise.resolve(options.wvpUrl)
      : resolveGb28181StreamUrl(sipDeviceId, channelId);

  if (!enableAi) {
    return { url: await wvpPromise };
  }

  const [wvpUrl, synced] = await Promise.all([
    wvpPromise,
    loadGbChannelSyncedDevice(sipDeviceId, channelId, options?.synced ?? null),
  ]);

  if (synced) {
    const { url, fallbackUrl, preferAi, pendingAiUrl } = await pickDirectPlayUrls(
      synced as DirectStreamFields,
      true,
    );
    if (url) {
      return {
        url,
        fallbackUrl: fallbackUrl ?? wvpUrl,
        preferAi,
        pendingAiUrl,
      };
    }
  }

  return { url: wvpUrl };
}

export interface DialogPlayerOpenOptions {
  /** 启用 AI 时优先 AI 流，无则回退原始流；默认 true */
  enableAi?: boolean;
}

export async function openDeviceInDialogPlayer(
  openModal: DevicePlayModalOpener,
  record: DeviceInfo,
  options?: DialogPlayerOpenOptions,
): Promise<boolean> {
  const enableAi = options?.enableAi ?? true;
  const name = formatCameraDeviceLabel(record);

  const gbIds = getGb28181PlayIds(record as Record<string, any>);
  if (gbIds || shouldPlayViaGb28181(record)) {
    const sipDeviceId =
      gbIds?.sipDeviceId ?? String(record.deviceIdentification || record.sip_device_id || '').trim();
    const channelId =
      gbIds?.channelId ??
      String(record.channelId || record.presetPos || record.channel_id || '').trim();
    if (!sipDeviceId || !channelId) return false;

    const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolveGbChannelPlayUrls(sipDeviceId, channelId, {
      enableAi,
      synced: record,
    });
    if (!url) return false;

    openModal(true, {
      ...record,
      name,
      deviceIdentification: sipDeviceId,
      channelId,
      http_stream: url,
      _fallbackUrl: fallbackUrl ?? null,
      _preferAi: preferAi ?? false,
      _pendingAiUrl: pendingAiUrl ?? null,
      _enableAi: enableAi,
    });
    return true;
  }

  if (!hasPlayableStream(record)) return false;

  await ensureDirectRtspPlayReady(record.id);

  const { url, fallbackUrl, preferAi, pendingAiUrl } = await pickDirectPlayUrls(record, enableAi);
  if (!url) return false;

  openModal(true, {
    ...record,
    name,
    http_stream: url,
    _fallbackUrl: fallbackUrl ?? null,
    _preferAi: preferAi ?? false,
    _pendingAiUrl: pendingAiUrl ?? null,
    _enableAi: enableAi,
  });
  return true;
}

export async function resolveMonitorPlayUrl(
  device: DeviceInfo,
  streamType: 'video' | 'ai' = 'video',
): Promise<string | null> {
  if (streamType === 'ai') {
    return pickAiPlayUrl(device);
  }

  const gbIds = getGb28181PlayIds(device as Record<string, any>);
  if (gbIds) {
    return resolveGb28181StreamUrl(gbIds.sipDeviceId, gbIds.channelId);
  }

  return pickVideoPlayUrl(device);
}

/**
 * 点播前确保推流转发任务在调度节点上运行（NVR 多路走集群任务，不在控制面起 ffmpeg）。
 */
export async function ensureDirectRtspPlayReady(deviceId?: string | null): Promise<void> {
  const id = String(deviceId || '').trim();
  if (!id) return;
  try {
    await ensureDeviceStreamForwardTask(id);
  } catch {
    /* 已在推或瞬时失败时仍尝试打开播放器，由播放超时提示 */
  }
}
