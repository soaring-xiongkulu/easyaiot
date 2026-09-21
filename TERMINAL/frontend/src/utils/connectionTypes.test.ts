// Regression tests for the connection-type registry lookups: every entry
// resolves an icon, and the string-based lookup used by TabItem stays
// type-correct (a bare string must not be treated as a {type} object).
import { describe, it, expect } from 'vitest'
import { CONNECTION_TYPES, connectionTypeInfo, connectionTypeIcon, connectionTypeIconOfKind, connectionTypeLabel } from './connectionTypes'

describe('connectionTypes registry', () => {
  it('gives every entry an icon and label', () => {
    for (const info of CONNECTION_TYPES) {
      expect(info.icon, info.type).toBeTruthy()
      expect(info.label, info.type).toBeTruthy()
      expect(connectionTypeInfo(info.type), info.type).toBeTruthy()
      expect(connectionTypeIconOfKind(info.type), info.type).toBeTruthy()
    }
  })

  it('resolves icons from config objects and bare type strings', () => {
    expect(connectionTypeIcon({ type: 'ssh' })).toBeTruthy()
    expect(connectionTypeIcon(null)).toBeUndefined()
    // the object helper must not silently resolve for a bare string
    expect(connectionTypeIcon('ssh' as never)).toBeUndefined()
  })

  it('labels filter keys for discriminated subtypes', () => {
    expect(connectionTypeLabel('database:mysql')).toBe('MySQL')
    expect(connectionTypeLabel('container:docker')).toBe('Docker')
    expect(connectionTypeLabel('redis')).toBe('Redis')
  })
})
