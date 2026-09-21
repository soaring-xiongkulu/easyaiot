// UTF-8-safe base64 encoder. Plain btoa() throws InvalidCharacterError for any
// code point above Latin1 (e.g. Chinese text in the internal file editor), so
// encode to UTF-8 bytes first. Chunked to stay under the V8 argument-count cap
// on String.fromCharCode.apply for large files — same pattern as
// components/toBase64.test.ts (F-028).
export function utf8ToBase64(str: string): string {
  const bytes = new TextEncoder().encode(str)
  let binary = ''
  const CHUNK = 0x2000
  for (let i = 0; i < bytes.length; i += CHUNK) {
    const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length))
    binary += String.fromCharCode.apply(null, slice as unknown as number[])
  }
  return btoa(binary)
}
