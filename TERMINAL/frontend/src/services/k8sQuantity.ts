// K8s quantity parse/format for metrics columns.

export function parseCpu(q: string): number {
  if (!q) return 0
  const s = String(q).trim()
  if (s.endsWith('n')) return Math.round(parseFloat(s) / 1e6)
  if (s.endsWith('u')) return Math.round(parseFloat(s) / 1e3)
  if (s.endsWith('m')) return Math.round(parseFloat(s))
  return Math.round(parseFloat(s) * 1000)
}

const MEM_UNITS: Record<string, number> = {
  Ki: 1024, Mi: 1024 ** 2, Gi: 1024 ** 3, Ti: 1024 ** 4, Pi: 1024 ** 5,
  k: 1e3, M: 1e6, G: 1e9, T: 1e12, P: 1e15,
}
export function parseMemory(q: string): number {
  if (!q) return 0
  const m = String(q).trim().match(/^(\d+(?:\.\d+)?)([A-Za-z]+)?$/)
  if (!m) return 0
  const n = parseFloat(m[1])
  return m[2] ? Math.round(n * (MEM_UNITS[m[2]] || 1)) : Math.round(n)
}

export function formatCpu(millicores: number): string {
  if (millicores < 1000) return `${Math.round(millicores)}m`
  const cores = millicores / 1000
  return Number.isInteger(cores) ? String(cores) : cores.toFixed(1)
}

export function formatMemory(bytes: number): string {
  const units: [string, number][] = [['Gi', 1024 ** 3], ['Mi', 1024 ** 2], ['Ki', 1024]]
  for (const [suffix, size] of units) {
    if (bytes >= size) {
      const v = bytes / size
      return `${Number.isInteger(v) ? v : v.toFixed(1)}${suffix}`
    }
  }
  return `${bytes}`
}

export function percent(used: number, total: number): string {
  if (!total || total <= 0) return '—'
  return `${Math.round((used / total) * 100)}%`
}
