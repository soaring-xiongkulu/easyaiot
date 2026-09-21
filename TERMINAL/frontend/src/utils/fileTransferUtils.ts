// Shared utilities for file-transfer features (companion panels, standalone
// SFTP/SCP connections, transfer menus). Protocol-related helpers that are
// used across components/stores live here.

// Effective file-transfer protocol of a connection. Only SSH connections carry
// the choice; anything else (and legacy configs without the field) is SFTP.
export function fileTransferProto(config?: { type?: string; fileTransferProto?: 'sftp' | 'scp' } | null): 'sftp' | 'scp' {
  return config?.type === 'ssh' && config?.fileTransferProto === 'scp' ? 'scp' : 'sftp'
}

// i18n key for the "connect SFTP / connect SCP" context-menu item of an SSH
// connection, matching its configured file-transfer protocol.
export function connectFileMenuKey(config?: { type?: string; fileTransferProto?: 'sftp' | 'scp' } | null): string {
  return fileTransferProto(config) === 'scp' ? 'sidebar.connectScp' : 'sidebar.connectSftp'
}

// True when the connection's remote filesystem can create symbolic links
// (SSH = SFTP/SCP companion or standalone, and WSL — 'wsl' for the companion
// sidebar's terminal config, 'wsl-file' for the dual-pane file window). FTP,
// SMB, WebDAV and S3 have no link semantics, so their file panels hide the
// "new link" entry.
export function supportsRemoteSymlink(config?: { type?: string } | null): boolean {
  if (!config) return false
  return config.type === 'ssh' || config.type === 'sftp' || config.type === 'scp' || config.type === 'wsl' || config.type === 'wsl-file'
}

// True when an operation failed because the transport died rather than because
// the remote side rejected the request. Covers pkg/sftp's "connection lost"
// (SFTP/SCP), crypto/ssh and net package wording, and the HTTP transport
// errors surfaced by WebDAV/S3. A matching error means retrying on a fresh
// connection may succeed — anything else (e.g. "no such directory") would
// fail again, so callers can skip the reconnect.
export function isConnectionLostError(err?: string | null): boolean {
  if (!err) return false
  return /connection lost|not connected|use of closed network connection|broken pipe|connection reset|connection refused|unexpected eof|\beof\b|already closed|ssh: disconnected/i.test(err)
}
