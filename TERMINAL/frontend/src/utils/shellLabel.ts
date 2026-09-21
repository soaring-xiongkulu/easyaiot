// Shared local-shell label helper. The same path may appear in the start-page
// shell dropdown, the connection form, the settings default-shell selector and
// terminal tab titles, so every surface must label it identically.
//
// bash.exe needs path-based disambiguation: Git for Windows, Cygwin and MSYS2
// all ship a bash.exe and the basename alone cannot tell them apart.

function shellBasename(path: string): string {
  const base = path.replace(/\\/g, '/').split('/').pop() || path
  return base.replace(/\.exe$/i, '')
}

export function getShellLabel(path: string, emptyFallback = ''): string {
  if (!path) return emptyFallback
  const lower = path.toLowerCase()
  if (lower.startsWith('admin://')) {
    const inner = getShellLabel(path.slice(8), emptyFallback)
    return inner.endsWith(' (Admin)') ? inner : `${inner} (Admin)`
  }
  if (lower.startsWith('clink://')) {
    return 'Command Prompt (Clink)'
  }
  if (lower.startsWith('wsl://')) {
    const distro = path.slice(6)
    return distro ? `WSL - ${distro}` : 'WSL'
  }
  if (lower.includes('pwsh')) return 'PowerShell'
  if (lower.includes('powershell')) return 'Windows PowerShell'
  if (lower.includes('bash')) {
    // Git for Windows lives under a `git` path segment (Program Files, scoop,
    // chocolatey), Cygwin under `cygwin*`, MSYS2 under `msys*`.
    if (/[\\/]git[\\/]/i.test(path)) return 'Git Bash'
    // The chocolatey shim directory carries no `git` segment, but its
    // bash.exe comes from the git package.
    if (lower.includes('chocolatey')) return 'Git Bash'
    if (lower.includes('cygwin')) return 'Cygwin'
    if (lower.includes('msys')) return 'MSYS2'
    return shellBasename(path)
  }
  if (lower.includes('cmd')) return 'Command Prompt'
  if (shellBasename(path).toLowerCase() === 'nu') return 'Nushell'
  return shellBasename(path)
}

/** Parses the distro name from a `wsl://<distro>` shell path, else null. */
export function parseWslFromShell(shellPath?: string): string | null {
  if (shellPath && shellPath.toLowerCase().startsWith('wsl://')) {
    const distro = shellPath.slice(6)
    return distro || null
  }
  return null
}
