/** Session-scoped SQL query history (localStorage). */
import type { HistoryEntry } from '../types/database'

const MAX = 50

function key(sessionId: string) {
  return `terminal.db.sqlHistory.${sessionId}`
}

export function loadSqlHistory(sessionId: string): HistoryEntry[] {
  if (!sessionId) return []
  try {
    const raw = localStorage.getItem(key(sessionId))
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function pushSqlHistory(sessionId: string, entry: Omit<HistoryEntry, 'id'>): HistoryEntry[] {
  if (!sessionId || !entry.sql.trim()) return loadSqlHistory(sessionId)
  const list = loadSqlHistory(sessionId)
  const item: HistoryEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    ...entry,
  }
  const next = [item, ...list.filter(e => e.sql !== entry.sql)].slice(0, MAX)
  try {
    localStorage.setItem(key(sessionId), JSON.stringify(next))
  } catch { /* ignore quota */ }
  return next
}
