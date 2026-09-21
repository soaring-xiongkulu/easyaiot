import { describe, it, expect } from 'vitest'
import { getShellLabel } from './shellLabel'

describe('getShellLabel', () => {
  it('returns the empty fallback for an empty path', () => {
    expect(getShellLabel('', 'Local')).toBe('Local')
    expect(getShellLabel('', '')).toBe('')
  })

  it('labels admin:// shells with an (Admin) suffix', () => {
    expect(getShellLabel('admin://C:\\Windows\\System32\\cmd.exe')).toBe('Command Prompt (Admin)')
    expect(getShellLabel('admin://powershell.exe')).toBe('Windows PowerShell (Admin)')
    // no double suffix when the inner label already ends with (Admin)
    expect(getShellLabel('admin://wsl://Ubuntu')).toBe('WSL - Ubuntu (Admin)')
  })

  it('labels wsl:// shells with the distro name', () => {
    expect(getShellLabel('wsl://Ubuntu-22.04')).toBe('WSL - Ubuntu-22.04')
    expect(getShellLabel('wsl://')).toBe('WSL')
  })

  it('labels PowerShell variants', () => {
    expect(getShellLabel('C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe')).toBe('Windows PowerShell')
    expect(getShellLabel('C:\\Program Files\\PowerShell\\7\\pwsh.exe')).toBe('PowerShell')
  })

  it('labels Git Bash by its install path', () => {
    expect(getShellLabel('C:\\Program Files\\Git\\bin\\bash.exe')).toBe('Git Bash')
    expect(getShellLabel('C:\\Users\\me\\scoop\\apps\\git\\current\\bin\\bash.exe')).toBe('Git Bash')
  })

  it('labels the chocolatey bash shim as Git Bash', () => {
    // The chocolatey shim directory carries no `git` path segment, but the
    // bash.exe there comes from the git package.
    expect(getShellLabel('C:\\ProgramData\\chocolatey\\bin\\bash.exe')).toBe('Git Bash')
  })

  it('labels Cygwin bash by its install path', () => {
    expect(getShellLabel('C:\\cygwin64\\bin\\bash.exe')).toBe('Cygwin')
    expect(getShellLabel('D:\\tools\\cygwin\\bin\\bash.exe')).toBe('Cygwin')
  })

  it('labels MSYS2 bash by its install path', () => {
    expect(getShellLabel('C:\\msys64\\usr\\bin\\bash.exe')).toBe('MSYS2')
    expect(getShellLabel('C:\\tools\\msys32\\usr\\bin\\bash.exe')).toBe('MSYS2')
  })

  it('falls back to the basename for unknown bash paths instead of mislabeling Git Bash', () => {
    expect(getShellLabel('E:\\custom\\bash.exe')).toBe('bash')
  })

  it('labels Command Prompt', () => {
    expect(getShellLabel('C:\\Windows\\System32\\cmd.exe')).toBe('Command Prompt')
  })

  it('labels Nushell', () => {
    expect(getShellLabel('C:\\Users\\me\\scoop\\shims\\nu.exe')).toBe('Nushell')
  })

  it('falls back to the basename for unrecognized shells', () => {
    expect(getShellLabel('C:\\tools\\fish.exe')).toBe('fish')
  })
})
