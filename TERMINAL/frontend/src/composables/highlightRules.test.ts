import { describe, it, expect } from 'vitest'
import { HIGHLIGHT_RULES, matchTextSpans, type HighlightCategory } from './highlightRules'

/** Match one line of plain text and flatten the spans to text+category. */
function spans(text: string): Array<{ text: string; category: HighlightCategory }> {
  return matchTextSpans(text, HIGHLIGHT_RULES)
    .spans
    .map((s) => ({ text: text.slice(s.start, s.end), category: s.category }))
}

/** The span (if any) whose text contains the given substring. */
function find(text: string, substr: string, category: HighlightCategory): boolean {
  return spans(text).some((s) => s.text.includes(substr) && s.category === category)
}

function noSpanOf(text: string, category: HighlightCategory): boolean {
  return !spans(text).some((s) => s.category === category)
}

describe('matchTextSpans — keyword rules', () => {
  it('highlights IP addresses as host', () => {
    expect(spans('ping 10.1.0.13\n')).toContainEqual({ text: '10.1.0.13', category: 'host' })
  })

  it('restricts the IP first octet to 1-254', () => {
    expect(noSpanOf('src 0.1.2.3\n', 'host')).toBe(true)
    expect(noSpanOf('src 255.1.2.3\n', 'host')).toBe(true)
    expect(find('src 254.1.2.3\n', '254.1.2.3', 'host')).toBe(true)
  })

  it('colors localhost, null and none as host', () => {
    expect(find('connecting to localhost\n', 'localhost', 'host')).toBe(true)
    expect(find('status: null\n', 'null', 'host')).toBe(true)
    expect(find('mode: none\n', 'none', 'host')).toBe(true)
  })

  it('colors IPv6 addresses as host (full and :: compressed forms)', () => {
    expect(find('addr 2001:db8:0:0:0:0:2:1 end\n', '2001:db8:0:0:0:0:2:1', 'host')).toBe(true)
    expect(find('inet6 fe80::1/64\n', 'fe80::1', 'host')).toBe(true)
    expect(find('listening on ::1\n', '::1', 'host')).toBe(true)
    expect(find('route 2001:db8::/32 via gw\n', '2001:db8::', 'host')).toBe(true)
  })

  it('does not highlight MAC addresses or :: scope tokens as IPv6', () => {
    expect(noSpanOf('mac aa:bb:cc:dd:ee:ff\n', 'host')).toBe(true)
    expect(noSpanOf('std::vector<int>\n', 'host')).toBe(true)
    expect(noSpanOf('at 12:34:56 sharp\n', 'host')).toBe(true)
  })

  it('colors error words as error', () => {
    expect(find('connect: connection refused\n', 'connection refused', 'error')).toBe(true)
    expect(find('ERROR: bad address\n', 'ERROR', 'error')).toBe(true)
    expect(find('ERROR: bad address\n', 'bad address', 'error')).toBe(true)
    expect(find('kernel panic: segmentation fault\n', 'segmentation fault', 'error')).toBe(true)
  })

  it('colors falsy output values (false/no/ko) as error when punctuation-guarded', () => {
    // NOTE: buffer rows never contain newlines (translateToString per row),
    // so the trailing-$ lookahead works on these inputs as it does live.
    expect(find('Result: no', 'no', 'error')).toBe(true)
    expect(find('=> false', 'false', 'error')).toBe(true)
    // prose must stay untouched
    expect(spans('nothing here')).toEqual([])
  })

  it('colors success words as success', () => {
    expect(find('session connected\n', 'connected', 'success')).toBe(true)
    expect(find('request accepted\n', 'accepted', 'success')).toBe(true)
    expect(find('deployed successfully\n', 'successfully', 'success')).toBe(true)
  })

  it('colors warning words as warning', () => {
    expect(find('WARNING: low disk\n', 'WARNING', 'warning')).toBe(true)
    expect(find('file not found\n', 'not found', 'warning')).toBe(true)
    expect(find('cannot open device\n', 'cannot', 'warning')).toBe(true)
  })

  it('colors info verbs as info', () => {
    expect(find('starting service…\n', 'starting', 'info')).toBe(true)
    expect(find('(ii) loading module\n', '(ii)', 'info')).toBe(true)
  })

  it('highlights URLs as url', () => {
    expect(find('see https://example.com/a?b=1 now\n', 'https://example.com', 'url')).toBe(true)
  })

  it('does not highlight arbitrary numbers', () => {
    expect(spans('port 8080 and 42\n')).toEqual([])
  })

  it('does not match keywords inside words', () => {
    expect(spans('terror attack\n')).toEqual([])
    expect(spans('warninglabel\n')).toEqual([])
    expect(spans('noteworthy\n')).toEqual([])
  })

  it('is case-insensitive', () => {
    expect(find('Connection Refused\n', 'Connection Refused', 'error')).toBe(true)
    expect(find('PING 10.0.0.1\n', '10.0.0.1', 'host')).toBe(true)
  })
})

describe('matchTextSpans — retained rules', () => {
  it('highlights a path containing the + special char', () => {
    const input = 'compiler /usr/local/gcc-11.5.0/bin/g++ -std=c++17\n'
    // The path anchor consumes the preceding whitespace (`(^|\s)` guard
    // group), so the space itself is NOT part of the span.
    expect(find(input, '/usr/local/gcc-11.5.0/bin/g++', 'path')).toBe(true)
    expect(spans(input).some((s) => s.text.startsWith(' '))).toBe(false)
  })

  it('highlights a path containing @ and ~', () => {
    const input = 'load /tmp/cache@1.tgz and ~/proj-2/app.exe now\n'
    expect(find(input, '/tmp/cache@1.tgz', 'path')).toBe(true)
    expect(find(input, '~/proj-2/app.exe', 'path')).toBe(true)
  })

  it('does not treat a bare an+b expression as a path', () => {
    expect(noSpanOf('compute an+b + c then d+e\n', 'path')).toBe(true)
  })

  it('highlights timestamps as datetime', () => {
    expect(find('at 12:34:56 done\n', '12:34:56', 'datetime')).toBe(true)
  })

  it('highlights quoted strings as string', () => {
    expect(find('msg "hello world" end\n', '"hello world"', 'string')).toBe(true)
  })

  it('highlights braces as brace', () => {
    expect(spans('hello {world}').some((s) => s.category === 'brace')).toBe(true)
  })
})

describe('matchTextSpans — span mechanics', () => {
  it('matches a run of consecutive identical brace symbols once', () => {
    const runs = spans('a **** b ===== c >>> d')
      .filter((s) => s.category === 'brace')
    expect(runs).toEqual([
      { text: '****', category: 'brace' },
      { text: '=====', category: 'brace' },
      { text: '>>>', category: 'brace' },
    ])
  })

  it('never overlaps spans: the first matching rule wins', () => {
    // The URL rule consumes the whole link; path/host/brace must not
    // double-cover parts of it.
    const input = 'see https://example.com/a?b=1 now'
    const raw = matchTextSpans(input, HIGHLIGHT_RULES).spans
    for (let i = 0; i < raw.length; i++) {
      for (let j = i + 1; j < raw.length; j++) {
        expect(raw[j].start >= raw[i].end || raw[i].start >= raw[j].end).toBe(true)
      }
    }
  })

  it('returns spans sorted by position regardless of rule order', () => {
    // path matches at a later column than datetime; datetime's rule runs
    // after path's, so unsorted output would interleave.
    const input = '2026-09-16 20:50:36,266 p=156 u=root | included: /opt/extra/init-base/roles/network-bond.yml\n'
    const raw = matchTextSpans(input, HIGHLIGHT_RULES).spans
    for (let i = 1; i < raw.length; i++) {
      expect(raw[i].start).toBeGreaterThanOrEqual(raw[i - 1].end)
    }
    // The timestamp (first columns) and the `=` signs must all be matched.
    expect(find(input, '2026-09-16 20:50:36,266', 'datetime')).toBe(true)
    expect(spans(input).some((s) => s.text === '=' && s.category === 'brace')).toBe(true)
    expect(find(input, '/opt/extra/init-base/roles/network-bond.yml', 'path')).toBe(true)
  })

  it('is stable when given an empty string', () => {
    expect(matchTextSpans('').spans).toEqual([])
  })

  it('respects the maxMatches cap and reports incompleteness', () => {
    const input = '{a} {b} {c} {d} {e} {f} {g} {h}'
    const result = matchTextSpans(input, HIGHLIGHT_RULES, { maxMatches: 3 })
    expect(result.spans.length).toBe(3)
    expect(result.complete).toBe(false)
  })
})
