import { signStreamTicket, type StreamTicketResp } from '@/api/device/camera';

/**
 * 受保护流地址的 secure_link 签名工具。
 *
 * 后端（VIDEO）为 /ai /live /rtp 这三类流路径签发短期票据 {e, st}，nginx 用 secure_link 校验。
 * 由于 secure_link 的哈希只覆盖「路径」（不含 host/port），所以：
 *  - 票据按 pathname 缓存即可，host 改写不影响；
 *  - ws-flv 自带的 ?originTypeStr=... 查询不影响签名，追加 &e=&st= 即可。
 */

/** 仅这三类路径需要签名；其余（MinIO/录像/mp4 等）原样放行 */
const PROTECTED_PATH_RE = /^\/(ai|live|rtp)\//i;
/** 服务端票据 TTL（秒），与调用保持一致 */
const DEFAULT_TTL = 90;
/** 本地缓存有效期，略短于服务端 TTL，避免边界过期 */
const TICKET_CACHE_TTL_MS = 60_000;

interface CacheEntry {
  ticket: StreamTicketResp;
  mintedAt: number;
  inflight?: Promise<StreamTicketResp>;
}

const cache = new Map<string, CacheEntry>();

function parseUrl(url: string): URL | null {
  if (!url) return null;
  try {
    return new URL(url, typeof window !== 'undefined' ? window.location.href : undefined);
  } catch {
    return null;
  }
}

/** 该地址是否为需要签名的受保护流地址 */
export function isProtectedStreamUrl(url: string): boolean {
  const u = parseUrl(url);
  return !!u && PROTECTED_PATH_RE.test(u.pathname);
}

async function getTicket(path: string, forceRefresh: boolean): Promise<StreamTicketResp> {
  const cached = cache.get(path);
  if (
    !forceRefresh &&
    cached &&
    !cached.inflight &&
    Date.now() - cached.mintedAt < TICKET_CACHE_TTL_MS
  ) {
    return cached.ticket;
  }
  if (!forceRefresh && cached?.inflight) {
    return cached.inflight;
  }

  const inflight = signStreamTicket(path, DEFAULT_TTL)
    .then((resp) => {
      const ticket: StreamTicketResp = { e: Number(resp.e), st: String(resp.st) };
      cache.set(path, { ticket, mintedAt: Date.now() });
      return ticket;
    })
    .catch((err) => {
      // 失败不缓存（含 401），下次重新签发；调用方会降级使用未签名地址。
      cache.delete(path);
      throw err;
    });

  cache.set(path, {
    ticket: cached?.ticket ?? { e: 0, st: '' },
    mintedAt: cached?.mintedAt ?? 0,
    inflight,
  });
  return inflight;
}

/** 让某地址对应路径的票据失效，下次 signStreamUrl 会强制重新签发 */
export function clearTicketForUrl(url: string): void {
  const u = parseUrl(url);
  if (u) cache.delete(u.pathname);
}

/**
 * 给受保护流地址追加 secure_link 票据参数。
 * 非受保护地址原样返回。签发失败会抛出（交由调用方/拦截器处理）。
 */
export async function signStreamUrl(
  url: string,
  opts?: { forceRefresh?: boolean },
): Promise<string> {
  const u = parseUrl(url);
  if (!u || !PROTECTED_PATH_RE.test(u.pathname)) return url;

  const ticket = await getTicket(u.pathname, !!opts?.forceRefresh);
  // 幂等：先清掉可能已有的 e/st，再写入新值（base64url 字符 -_ 不会被编码）
  u.searchParams.delete('e');
  u.searchParams.delete('st');
  u.searchParams.set('e', String(ticket.e));
  u.searchParams.set('st', ticket.st);
  return u.toString();
}
