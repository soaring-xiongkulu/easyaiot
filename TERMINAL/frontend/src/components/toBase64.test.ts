// F-028 behavior-parity: chunked base64 must produce byte-identical output to
// the per-byte reference implementation, including for inputs that cross the
// 8K chunk boundary and very large inputs (where the old per-byte loop would
// starve the V8 argument-count cap on String.fromCharCode.apply).
import { describe, it, expect } from 'vitest'

// The chunked implementation, copied verbatim from BaseTerminal.vue so this
// test exercises the exact production code path.
function toBase64(str: string): string {
  const bytes = new TextEncoder().encode(str)
  let binary = ''
  const CHUNK = 0x2000
  for (let i = 0; i < bytes.length; i += CHUNK) {
    const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length))
    binary += String.fromCharCode.apply(null, slice as unknown as number[])
  }
  return btoa(binary)
}

// Reference implementation: per-byte String.fromCharCode concat. Safe under
// the vitest arg cap because each call has a single argument.
function toBase64Ref(str: string): string {
  const bytes = new TextEncoder().encode(str)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

describe('toBase64 (F-028 chunked)', () => {
  it('round-trips an empty string', () => {
    expect(toBase64('')).toBe('')
  })

  it('matches the per-byte reference for ASCII text', () => {
    const text = 'hello, world!\n'
    expect(toBase64(text)).toBe(toBase64Ref(text))
    expect(atob(toBase64(text))).toBe(text)
  })

  it('matches the reference across the 8K chunk boundary', () => {
    const text = 'A'.repeat(0x2000 - 1) + 'B' + 'C'.repeat(0x2000)
    expect(toBase64(text)).toBe(toBase64Ref(text))
  })

  it('matches the reference for multibyte UTF-8', () => {
    const text = '你好，世界 — emoji 🎉 and box drawing ──'
    expect(toBase64(text)).toBe(toBase64Ref(text))
  })

  it('matches the reference for a 100 KB string (well past the chunk size)', () => {
    const text = 'X'.repeat(100 * 1024)
    expect(toBase64(text)).toBe(toBase64Ref(text))
  })
})