// Regression tests for F-312: capToolResult hard-caps tool result blobs
// at write time so a single oversized capture_terminal / execute_command
// response can't blow up the conversation computed (F-301) on subsequent
// turns. 32 KB total, 8 KB head, 16 KB tail, with a clear Chinese
// truncation marker. Strings under the cap must pass through unchanged.

import { describe, expect, it } from 'vitest'

// Mirror of capToolResult in agent.ts. If the helper changes, this test
// must be updated; the agent module isn't loaded directly because it pulls
// in a heavy terminal/xterm graph that's awkward to mock in vitest.
const TOOL_RESULT_MAX_BYTES = 32 * 1024
const TOOL_RESULT_HEAD_BYTES = 8 * 1024
const TOOL_RESULT_TAIL_BYTES = 16 * 1024

function capToolResult(text: string): string {
  if (text.length <= TOOL_RESULT_MAX_BYTES) return text
  const head = text.slice(0, TOOL_RESULT_HEAD_BYTES)
  const tail = text.slice(text.length - TOOL_RESULT_TAIL_BYTES)
  const omitted = text.length - TOOL_RESULT_HEAD_BYTES - TOOL_RESULT_TAIL_BYTES
  return `${head}\n\n─────── [已截断: 工具结果共 ${text.length} 字节, 已省略 ${omitted} 字节] ────────\n调整工具参数（如 head_lines / tail_lines）或分段调用以查看被截断部分。\n\n${tail}`
}

describe('capToolResult (F-312 tool result blob cap)', () => {
  it('passes through unchanged when exactly at the cap', () => {
    const text = 'a'.repeat(TOOL_RESULT_MAX_BYTES)
    expect(capToolResult(text)).toBe(text)
  })

  it('passes through unchanged when below the cap', () => {
    const text = 'a'.repeat(TOOL_RESULT_MAX_BYTES - 1)
    expect(capToolResult(text)).toBe(text)
  })

  it('truncates with a clear marker when one byte over the cap', () => {
    const text = 'a'.repeat(TOOL_RESULT_MAX_BYTES + 1)
    const out = capToolResult(text)
    expect(out).toContain('已截断')
    expect(out).toContain(`${TOOL_RESULT_MAX_BYTES + 1} 字节`)
    // omitted = total - HEAD - TAIL, not just "1 byte over"
    const expectedOmitted = text.length - TOOL_RESULT_HEAD_BYTES - TOOL_RESULT_TAIL_BYTES
    expect(out).toContain(`已省略 ${expectedOmitted} 字节`)
    // Original head preserved
    expect(out.startsWith('a'.repeat(TOOL_RESULT_HEAD_BYTES))).toBe(true)
    // Original tail preserved
    expect(out.endsWith('a'.repeat(TOOL_RESULT_TAIL_BYTES))).toBe(true)
  })

  it('truncates a multi-megabyte blob to ~head + tail + marker', () => {
    const text = 'x'.repeat(1024 * 1024) // 1 MB
    const out = capToolResult(text)
    expect(out.length).toBeLessThan(text.length)
    expect(out.length).toBeLessThan(TOOL_RESULT_MAX_BYTES * 2)
    expect(out).toContain('已截断')
    expect(out).toContain(`${1024 * 1024} 字节`)
    expect(out).toContain('已省略')
    expect(out).toContain('调整工具参数')
    expect(out.startsWith('x'.repeat(TOOL_RESULT_HEAD_BYTES))).toBe(true)
    expect(out.endsWith('x'.repeat(TOOL_RESULT_TAIL_BYTES))).toBe(true)
  })

  it('marks the omitted byte count as total - head - tail', () => {
    const text = 'A'.repeat(TOOL_RESULT_MAX_BYTES * 4)
    const out = capToolResult(text)
    const expectedOmitted = text.length - TOOL_RESULT_HEAD_BYTES - TOOL_RESULT_TAIL_BYTES
    expect(out).toContain(`已省略 ${expectedOmitted} 字节`)
  })

  it('preserves head and tail content for distinguishable text', () => {
    // Head and tail are long enough to fill the head/tail slices on their
    // own; middle uses a separator pattern to make any leakage visible.
    const head = 'BEGIN_HEAD'.repeat(1024) // 10 KB > 8 KB head slice
    const tail = 'END_TAIL'.repeat(3072) // 24 KB > 16 KB tail slice
    const middle = 'X'.repeat(TOOL_RESULT_MAX_BYTES * 4)
    const text = head + middle + tail
    const out = capToolResult(text)
    // head preserved start
    expect(out.startsWith('BEGIN_HEAD')).toBe(true)
    // tail preserved end
    expect(out.endsWith('END_TAIL')).toBe(true)
    // middle is dropped (any X-run > 100 chars would indicate leakage)
    expect(out).not.toMatch(/X{100,}/)
    // marker is present
    expect(out).toContain('已截断')
  })

  it('handles empty string as a no-op', () => {
    expect(capToolResult('')).toBe('')
  })

  it('handles exactly TOOL_RESULT_MAX_BYTES + 1 (boundary)', () => {
    const text = 'b'.repeat(TOOL_RESULT_MAX_BYTES + 1)
    const out = capToolResult(text)
    expect(out).not.toBe(text)
    expect(out).toContain('已截断')
  })

  it('handles TOOL_RESULT_MAX_BYTES * 10 (deep over the cap)', () => {
    const text = 'c'.repeat(TOOL_RESULT_MAX_BYTES * 10)
    const out = capToolResult(text)
    expect(out).toContain('已截断')
    expect(out.length).toBeLessThan(text.length / 10) // drastically shorter
  })

  it('output length is bounded by head + tail + fixed marker overhead', () => {
    const text = 'd'.repeat(TOOL_RESULT_MAX_BYTES * 100)
    const out = capToolResult(text)
    // Approximate upper bound: head + tail + ~200 bytes of marker
    expect(out.length).toBeLessThanOrEqual(TOOL_RESULT_HEAD_BYTES + TOOL_RESULT_TAIL_BYTES + 400)
  })

  it('preserves newlines and unicode content inside preserved head/tail', () => {
    const head = '头部\n带换行\r\nWindows\n行尾'
    const tail = '尾部\n更多内容\n🎉✓'
    const middle = 'X'.repeat(TOOL_RESULT_MAX_BYTES * 2)
    const text = head + '\n' + middle + '\n' + tail
    const out = capToolResult(text)
    expect(out).toContain('带换行')
    expect(out).toContain('🎉✓')
  })
})
