/**
 * 轻量 Markdown → 安全 HTML 渲染器（平台智能助手专用，零依赖）
 *
 * 支持：标题（# ~ ####）、粗体/斜体、行内代码、围栏代码块、有序/无序列表、
 * 引用、链接、分割线、基础表格。所有输入先 HTML escape，输出可安全用于 v-html。
 * 生成的节点带 `md-` 前缀类名，供组件样式定制。
 */

const INLINE_CODE_RE = /`([^`\n]+)`/g
const BOLD_RE = /\*\*([^*]+)\*\*/g
const ITALIC_RE = /\*([^*\n]+)\*/g
const LINK_RE = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g
const FENCE_RE = /^```/
const HEADING_RE = /^(#{1,4})\s+(.+)$/
const HR_RE = /^([-*_])\1{2,}\s*$/
const QUOTE_RE = /^>\s?/
const UL_ITEM_RE = /^\s*[-*+]\s+(.+)$/
const OL_ITEM_RE = /^\s*(\d+)[.)]\s+(.+)$/
const TABLE_SEP_RE = /^\s*\|?[\s:|-]*\|[\s:|-]*\|?\s*$/

export function escapeHtml(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/** 行内元素：行内代码 → 粗体 → 斜体 → 链接 */
function renderInline(text: string): string {
  return escapeHtml(text)
    .replace(INLINE_CODE_RE, (_m, code: string) => `<code class="md-code-inline">${code}</code>`)
    .replace(BOLD_RE, '<strong>$1</strong>')
    .replace(ITALIC_RE, '<em>$1</em>')
    .replace(LINK_RE, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
}

/** 围栏代码块（含语言标注，代码内容原样转义） */
function renderFence(lang: string, lines: string[]): string {
  const label = escapeHtml(lang.trim()) || 'code'
  const body = escapeHtml(lines.join('\n'))
  return (
    `<div class="md-code"><div class="md-code__bar"><span class="md-code__lang">${label}</span>` +
    `<button class="md-code__copy" type="button">复制</button></div>` +
    `<pre class="md-code__pre"><code>${body}</code></pre></div>`
  )
}

/** 流式过程中代码围栏未闭合时退化为纯文本，避免整段被当作代码块渲染 */
export function isUnbalancedFence(text: string): boolean {
  let count = 0
  for (const line of text.split('\n')) if (FENCE_RE.test(line)) count++
  return count % 2 === 1
}

export function renderMarkdown(md: string): string {
  if (!md) return ''
  const lines = md.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let i = 0

  const isParagraphBreak = (line: string) => {
    if (!line.trim()) return true
    return (
      FENCE_RE.test(line) ||
      HEADING_RE.test(line) ||
      HR_RE.test(line) ||
      QUOTE_RE.test(line) ||
      UL_ITEM_RE.test(line) ||
      OL_ITEM_RE.test(line) ||
      line.includes('|') ||
      TABLE_SEP_RE.test(line)
    )
  }

  while (i < lines.length) {
    const line = lines[i]

    // 围栏代码块
    if (FENCE_RE.test(line)) {
      const lang = line.slice(3)
      const buf: string[] = []
      i++
      while (i < lines.length && !FENCE_RE.test(lines[i])) {
        buf.push(lines[i])
        i++
      }
      i++ // 跳过结束围栏
      html.push(renderFence(lang, buf))
      continue
    }

    const trimmed = line.trim()
    if (!trimmed) {
      i++
      continue
    }

    // 标题
    const heading = HEADING_RE.exec(trimmed)
    if (heading) {
      const level = heading[1].length
      html.push(`<h${level} class="md-h md-h${level}">${renderInline(heading[2])}</h${level}>`)
      i++
      continue
    }

    // 分割线
    if (HR_RE.test(trimmed)) {
      html.push('<hr class="md-hr">')
      i++
      continue
    }

    // 引用
    if (QUOTE_RE.test(trimmed)) {
      const buf: string[] = []
      while (i < lines.length && QUOTE_RE.test(lines[i].trim())) {
        buf.push(lines[i].trim().replace(QUOTE_RE, ''))
        i++
      }
      html.push(`<blockquote class="md-quote">${buf.map(renderInline).join('<br>')}</blockquote>`)
      continue
    }

    // 表格：当前行含 |，且下一行为分隔行
    if (trimmed.includes('|') && i + 1 < lines.length && lines[i + 1].includes('-') && TABLE_SEP_RE.test(lines[i + 1])) {
      const header = trimmed.split('|').map((s) => s.trim()).filter(Boolean)
      i += 2
      const rows: string[][] = []
      while (i < lines.length && lines[i].includes('|')) {
        rows.push(lines[i].split('|').map((s) => s.trim()).filter(Boolean))
        i++
      }
      const renderCells = (row: string[]) => row.map((c) => `<td>${renderInline(c)}</td>`).join('')
      html.push(
        `<div class="md-table-wrap"><table class="md-table"><thead><tr>` +
        `${header.map((c) => `<th>${renderInline(c)}</th>`).join('')}</tr></thead>` +
        `<tbody>${rows.map((r) => `<tr>${renderCells(r)}</tr>`).join('')}</tbody></table></div>`,
      )
      continue
    }

    // 无序列表
    const ulItem = UL_ITEM_RE.exec(line)
    if (ulItem) {
      const items: string[] = [renderInline(ulItem[1])]
      i++
      while (i < lines.length) {
        const m = UL_ITEM_RE.exec(lines[i])
        if (!m) break
        items.push(renderInline(m[1]))
        i++
      }
      html.push(`<ul class="md-list">${items.map((x) => `<li>${x}</li>`).join('')}</ul>`)
      continue
    }

    // 有序列表
    const olItem = OL_ITEM_RE.exec(line)
    if (olItem) {
      const items: string[] = [renderInline(olItem[2])]
      i++
      while (i < lines.length) {
        const m = OL_ITEM_RE.exec(lines[i])
        if (!m) break
        items.push(renderInline(m[2]))
        i++
      }
      html.push(`<ol class="md-list">${items.map((x) => `<li>${x}</li>`).join('')}</ol>`)
      continue
    }

    // 普通段落（合并连续非空行）
    const buf: string[] = [renderInline(trimmed)]
    i++
    while (i < lines.length && !isParagraphBreak(lines[i])) {
      buf.push(renderInline(lines[i].trim()))
      i++
    }
    html.push(`<p class="md-p">${buf.join('<br>')}</p>`)
  }

  return html.join('\n')
}
