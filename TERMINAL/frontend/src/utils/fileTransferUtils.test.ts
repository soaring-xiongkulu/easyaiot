import { describe, it, expect } from 'vitest'
import { supportsRemoteSymlink } from './fileTransferUtils'

// "New link" must appear wherever the backend can create symbolic links. The
// WSL dual-pane file window carries config type 'wsl-file' (the companion
// sidebar uses 'wsl'), and both are served by the WSL file session.
describe('supportsRemoteSymlink', () => {
  it('accepts every backend with link semantics', () => {
    for (const type of ['ssh', 'sftp', 'scp', 'wsl', 'wsl-file']) {
      expect(supportsRemoteSymlink({ type })).toBe(true)
    }
  })

  it('rejects protocols without link semantics', () => {
    for (const type of ['ftp', 'smb', 'webdav', 's3', 'local', 'serial']) {
      expect(supportsRemoteSymlink({ type })).toBe(false)
    }
    expect(supportsRemoteSymlink(null)).toBe(false)
    expect(supportsRemoteSymlink(undefined)).toBe(false)
  })
})
