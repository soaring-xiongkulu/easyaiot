// Internal editor save (FileEditorDialog) must base64-encode UTF-8 content;
// a plain btoa() throws InvalidCharacterError for any char above Latin1.
import { describe, it, expect } from 'vitest'
import { utf8ToBase64 } from './base64'

function decodeUtf8Base64(b64: string): string {
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return new TextDecoder().decode(bytes)
}

describe('utf8ToBase64', () => {
  it('encodes an empty string', () => {
    expect(utf8ToBase64('')).toBe('')
  })

  it('round-trips ASCII text', () => {
    const text = 'hello, world!\n'
    expect(decodeUtf8Base64(utf8ToBase64(text))).toBe(text)
  })

  it('round-trips Chinese characters without throwing', () => {
    const text = '你好，世界 — 中文注释 🎉'
    expect(() => utf8ToBase64(text)).not.toThrow()
    expect(decodeUtf8Base64(utf8ToBase64(text))).toBe(text)
  })

  it('matches the chunked reference across the 8K boundary', () => {
    // Same expectation as components/toBase64.test.ts: byte-identical to a
    // per-byte TextEncoder reference, chunk boundary included.
    const text = '中'.repeat(0x2000) + 'A'.repeat(0x2000)
    const bytes = new TextEncoder().encode(text)
    let ref = ''
    for (let i = 0; i < bytes.length; i++) ref += String.fromCharCode(bytes[i])
    expect(utf8ToBase64(text)).toBe(btoa(ref))
  })
})
