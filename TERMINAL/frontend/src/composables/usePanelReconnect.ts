// Reconnect orchestration for file-transfer panels (sftp/scp/ftp/smb/webdav/
// s3/wsl-file — every panel whose tab content is the protocol-agnostic file
// browser). Extracted from App.vue's reconnectSftpPanel so the tab right-click
// 「重连」 and the refresh-triggered auto-reconnect share one implementation:
// close the old session, create a fresh one from the panel's stored config,
// rebind the panel, and wait for the new session to report connected.
import { CreateSession, CloseSession, ListSessions } from '../../bindings/easyaiot/terminal/app'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { fileTransferProto } from '../utils/fileTransferUtils'

// One in-flight reconnect per panel: concurrent triggers (refresh spam, a
// burst of failed listings) share the same attempt instead of stacking
// close/create cycles. Keyed by panel id; removed on completion.
const inflight = new Map<string, Promise<string | null>>()

// How long to wait for the fresh session to report connected. Matches the
// SSH dial timeout on the backend (30s); polling covers both synchronously
// connecting types (SFTP/S3, already up when CreateSession returns) and
// async ones (FTP) that flip to connected a moment later.
const CONNECT_TIMEOUT_MS = 30_000
const CONNECT_POLL_MS = 300

export function isPanelReconnecting(panelId: string): boolean {
  return inflight.has(panelId)
}

// Reconnect a file-transfer panel. Resolves with the NEW session id once the
// session is connected; resolves null when the fresh session fails to come up
// (the session:status 'error' path already toasts the backend's connect error)
// or rejects with the underlying error when the reconnect itself could not run.
// Returns via the shared in-flight promise when a reconnect for this panel is
// already running.
export function reconnectFileTransferPanel(panelId: string): Promise<string | null> {
  const existing = inflight.get(panelId)
  if (existing) return existing
  const attempt = doReconnect(panelId).finally(() => inflight.delete(panelId))
  inflight.set(panelId, attempt)
  return attempt
}

async function doReconnect(panelId: string): Promise<string | null> {
  const panelStore = usePanelStore()
  const sessionStore = useSessionStore()
  const panel = panelStore.getPanel(panelId)
  const cfg = panel?.config
  if (!cfg || !cfg.type) return null

  const oldId = panel.sessionId
  if (oldId) {
    try { await CloseSession(oldId) } catch (_) {}
  }
  // SSH-based file panels carry the protocol preference on the config; the
  // file-transfer types (ftp/smb/...) already match their session type.
  const proto = fileTransferProto(cfg)
  const sessionType = cfg.type === 'ssh' ? proto : cfg.type
  const info = await CreateSession(sessionType, cfg)
  panelStore.bindSession(panelId, info.id)
  sessionStore.initSession(info.id)
  const ok = await waitUntilConnected(info.id)
  return ok ? info.id : null
}

async function waitUntilConnected(sid: string): Promise<boolean> {
  const deadline = Date.now() + CONNECT_TIMEOUT_MS
  while (Date.now() < deadline) {
    try {
      const sessions = await ListSessions()
      // ListSessions comes from the untyped Wails bindings (same as callers
      // like FileTabContent's probe), so the shape is annotated locally.
      const status = (sessions as Array<{ id: string; status: string }>)
        .find(s => s.id === sid)?.status
      if (status === 'connected') return true
      if (status === 'error' || status === 'disconnected') return false
    } catch { /* transient IPC failure — keep polling until the deadline */ }
    await new Promise(r => setTimeout(r, CONNECT_POLL_MS))
  }
  return false
}
