(function () {
  const cfg = window.__EASYAIOT_HARNESS_BRAND__ || {}
  const name = cfg.name || 'EasyAIoT'
  const logo = cfg.logo || ''
  const heroHeadline = cfg.heroHeadline || ''
  const heroPreview = cfg.heroPreview

  let scanTimer = 0
  let dropHint = null

  function logoImg(cls) {
    return `<img class="${cls || 'easyaiot-replaced-logo'}" src="${logo}" alt="${name}" />`
  }

  function renderSidebar(btn) {
    // 禁止 innerHTML：侧栏由 React 托管，改 DOM 会在重渲时 NotFoundError(removeChild)
    if (!btn || btn.dataset.easyaiotBrand === '1')
      return
    btn.dataset.easyaiotBrand = '1'
    btn.setAttribute('aria-label', name)
    btn.title = name
  }

  /** DeepSeek FishLogo 特征 viewBox；侧栏 rail / 欢迎区都会用到 */
  function isFishLogoSvg(svg) {
    if (!svg || svg.tagName !== 'svg')
      return false
    if (svg.dataset.easyaiotLogo === '1')
      return false
    const vb = (svg.getAttribute('viewBox') || '').replace(/\s+/g, ' ').trim()
    if (vb === '0 0 23.16 17.04' || vb.startsWith('0 0 23.16'))
      return true
    const cls = svg.getAttribute('class') || ''
    if (/railFish|\bfish\b|FishLogo|wordmark/i.test(cls))
      return true
    if (svg.querySelector('clipPath[id*="whale"], [clip-path*="whale"]'))
      return true
    return false
  }

  function replaceFishSvg(svg) {
    // 禁止 replaceWith：会拆掉 React 侧栏 fiber，拖拽/重渲即 slot crashed
    if (!isFishLogoSvg(svg))
      return
    svg.dataset.easyaiotLogo = '1'
    svg.setAttribute('aria-hidden', 'true')
    svg.style.opacity = '0'
  }

  function replaceAllFishLogos(root) {
    if (!logo)
      return
    const scope = root || document
    // 只改属性/透明度，绝不替换或清空 React 节点
    scope.querySelectorAll('svg').forEach(replaceFishSvg)
    scope.querySelectorAll('img').forEach((img) => {
      if (img.dataset.easyaiotLogo === '1' || img.classList.contains('easyaiot-replaced-logo'))
        return
      const src = img.getAttribute('src') || ''
      if (/deepseek|dsh-.*logo|whale|fish/i.test(src) && !/easyaiot-brand-logo/i.test(src)) {
        img.src = logo
        img.classList.add('easyaiot-replaced-logo')
        img.dataset.easyaiotLogo = '1'
      }
    })
  }

  function isSloganHeadline(el) {
    const cls = String(el?.className || '')
    // 只要标语行（如 pXSMma_headline）；勿匹配 composerHero / EmptyHero / headlineText
    if (/composerHero|EmptyHero|emptyHero|heroGlow|HeroGlow|HeroShell/i.test(cls))
      return false
    if (/headlineText|HeadlineText/i.test(cls))
      return false
    return /headline/i.test(cls)
  }

  function restoreIfMistakenHero(el) {
    if (!el || el.dataset.easyaiotHero !== '1')
      return
    if (isSloganHeadline(el))
      return
    el.style.display = ''
    el.removeAttribute('hidden')
    delete el.dataset.easyaiotHero
  }

  function patchHero(el) {
    if (!el)
      return
    // 先前误把 Hero 容器 display:none，扫到时先恢复
    if (!isSloganHeadline(el)) {
      restoreIfMistakenHero(el)
      return
    }
    // 不展示 logo /「探索未至之境」标语行
    el.style.display = 'none'
    el.setAttribute('hidden', '')
    el.dataset.easyaiotHero = '1'
  }

  function preferVscodeLight() {
    document.documentElement.style.colorScheme = 'light'
    document.documentElement.classList.add('easyaiot-vscode-light')
    document.documentElement.classList.remove('easyaiot-cursor', 'easyaiot-cursor-light')
    document.body?.removeAttribute('data-ds-dark-theme')
  }

  /** 正红/亮蓝 → VS Code 中性色；失败文案用警告黄而非大红 */
  function neutralizeOddColors(root) {
    const nodes = (root || document).querySelectorAll('span, p, label, div, button, a, code, pre, strong, b')
    const limit = Math.min(nodes.length, 200)
    for (let i = 0; i < limit; i++) {
      const el = nodes[i]
      const style = el.style
      if (!style)
        continue
      const c = (style.color || '').replace(/\s+/g, '').toLowerCase()
      if (!c)
        continue
      const isRed = c === 'red' || c === '#f00' || c === '#ff0000'
        || /^#e[0-9a-f]{2}[0-3][0-9a-f]{3}$/.test(c)
        || /^#c[0-9a-f]{5}$/.test(c)
        || /^rgb\(\s*2(2[4-9]|[3-9]\d)\s*,\s*\d{1,2}\s*,\s*\d{1,2}\s*\)$/.test(c)
        || /^rgb\(\s*18[0-9]|19\d|2\d\d\s*,\s*[0-5]?\d\s*,\s*[0-5]?\d\s*\)$/.test(c)
      const isBlue = c === '#007acc' || c === '#0066cc' || c === 'rgb(0,122,204)' || c === 'dodgerblue'
      const isOrange = c === '#f54e00' || c === '#e8713a' || c === 'orange' || c === '#ff8c00'
      const text = (el.textContent || '').trim()
      const looksError = /失败|错误|MISSING|ERROR|credential|no API key/i.test(text)
      if (isRed) {
        style.color = looksError ? '#6b5a00' : '#6c6c6c'
        if (looksError && !el.dataset.easyaiotWarn) {
          el.dataset.easyaiotWarn = '1'
          el.style.background = '#fff8e1'
          el.style.borderLeft = '3px solid #d6b656'
          el.style.padding = el.style.padding || '4px 8px'
        }
      }
      else if (isBlue || isOrange) {
        style.color = '#6c6c6c'
      }
    }
  }

  function findComposer() {
    const candidates = [
      ...document.querySelectorAll('textarea'),
      ...document.querySelectorAll('[contenteditable="true"]'),
      ...document.querySelectorAll('[role="textbox"]'),
    ]
    // 优先可见且靠近底部的输入框
    let best = null
    let bestScore = -1
    for (const el of candidates) {
      const r = el.getBoundingClientRect()
      if (r.width < 40 || r.height < 16)
        continue
      const style = window.getComputedStyle(el)
      if (style.display === 'none' || style.visibility === 'hidden')
        continue
      const score = r.bottom + r.width * 0.01
      if (score > bestScore) {
        bestScore = score
        best = el
      }
    }
    return best
  }

  function setNativeValue(el, value) {
    const proto = el.tagName === 'INPUT' ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype
    const desc = Object.getOwnPropertyDescriptor(proto, 'value')
    if (desc && desc.set)
      desc.set.call(el, value)
    else
      el.value = value
    el.dispatchEvent(new Event('input', { bubbles: true }))
    el.dispatchEvent(new Event('change', { bubbles: true }))
  }

  function toWorkspaceRel(raw) {
    if (!raw)
      return ''
    let p = String(raw).trim().replace(/\\/g, '/')
    if (!p)
      return ''
    // vscode URI / file URI
    if (/^[a-z][a-z0-9+.-]*:/i.test(p)) {
      try {
        if (p.startsWith('vscode-remote:') || p.startsWith('vscode-file:') || p.startsWith('vscode-userdata:')) {
          // vscode-remote://authority/path
          const m = p.match(/^[^:]+:\/\/[^/]*(\/.*)$/)
          p = m ? decodeURIComponent(m[1]) : p
        }
        else {
          const u = new URL(p)
          p = decodeURIComponent(u.pathname || '')
        }
      }
      catch {
        // keep raw
      }
    }
    p = p.replace(/^\/+/, '/')
    const prefixes = [
      '/home/coder/easyaiot/',
      '/workspace/easyaiot/',
      '/home/coder/project/',
      '/workspaces/easyaiot/',
    ]
    for (const pre of prefixes) {
      if (p.startsWith(pre)) {
        p = p.slice(pre.length)
        break
      }
    }
    p = p.replace(/^\/+/, '')
    p = p.replace(/^(workspace\/)?easyaiot\//, '')
    // 去掉 fragment L1,1
    p = p.replace(/#.*$/, '')
    if (!p || p.endsWith('/'))
      return p.replace(/\/$/, '')
    return p
  }

  let lastAttachKey = ''
  let lastAttachAt = 0

  function insertMentions(paths) {
    const rels = [...new Set((paths || []).map(toWorkspaceRel).filter(Boolean))]
    if (!rels.length)
      return { ok: false, reason: 'empty' }

    const el = findComposer()
    if (!el) {
      notifyParent({ type: 'easyaiot-attach-result', ok: false, reason: 'no-composer', paths: rels })
      return { ok: false, reason: 'no-composer', paths: rels }
    }

    const curText = (el.value != null ? el.value : (el.textContent || '')) || ''
    // 已在输入框中的 @path 不再重复插入
    const need = rels.filter((p) => !curText.includes(`@${p}`))
    if (!need.length) {
      notifyParent({ type: 'easyaiot-attach-result', ok: true, paths: rels, deduped: true })
      return { ok: true, paths: rels, deduped: true }
    }

    const attachKey = need.join('|')
    const now = Date.now()
    if (attachKey === lastAttachKey && now - lastAttachAt < 1000) {
      return { ok: true, paths: need, skipped: true }
    }
    lastAttachKey = attachKey
    lastAttachAt = now

    const chunk = need.map(p => `@${p}`).join(' ') + ' '
    el.focus()

    if (el.isContentEditable || el.getAttribute('contenteditable') === 'true') {
      try {
        document.execCommand('insertText', false, chunk)
      }
      catch {
        el.textContent = `${el.textContent || ''}${chunk}`
        el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: chunk }))
      }
    }
    else {
      const start = typeof el.selectionStart === 'number' ? el.selectionStart : (el.value || '').length
      const end = typeof el.selectionEnd === 'number' ? el.selectionEnd : start
      const cur = el.value || ''
      const next = cur.slice(0, start) + chunk + cur.slice(end)
      setNativeValue(el, next)
      try {
        el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: chunk }))
      }
      catch { /* ignore */ }
      const caret = start + chunk.length
      try {
        el.setSelectionRange(caret, caret)
      }
      catch { /* ignore */ }
    }
    el.focus()
    notifyParent({ type: 'easyaiot-attach-result', ok: true, paths: need })
    return { ok: true, paths: need }
  }

  function notifyParent(payload) {
    try {
      if (window.parent && window.parent !== window)
        window.parent.postMessage(payload, '*')
    }
    catch { /* ignore */ }
  }

  function looksLikeRepoPath(s) {
    const t = String(s || '').trim().replace(/^@/, '')
    if (!t || t.length > 512 || /\s/.test(t))
      return ''
    if (t.includes('..'))
      return ''
    // WEB/foo.ts、README.md、path/to/dir
    if (/^[A-Za-z0-9_.+\-]+(\/[A-Za-z0-9_.+\-]+)*\/?$/.test(t))
      return t.replace(/\/$/, '')
    return ''
  }

  function extractClickPath(target) {
    if (!target || !target.closest)
      return ''
    if (target.closest('.dsh_atFile_remove, [class*="remove"], [aria-label*="移除"], [aria-label*="Remove"]'))
      return ''

    const pathBtn = target.closest('.dsh_atFile_path, [data-at-file-path], [data-path]')
    if (pathBtn) {
      const raw = pathBtn.getAttribute('data-at-file-path')
        || pathBtn.getAttribute('data-path')
        || pathBtn.getAttribute('title')
        || pathBtn.textContent
      return looksLikeRepoPath(raw)
    }

    const row = target.closest('[data-at-file-row], .dsh_atFile_row, [class*="atFile"]')
    if (row) {
      const btn = row.querySelector('.dsh_atFile_path, [title]')
      if (btn) {
        const raw = btn.getAttribute('title') || btn.textContent
        const p = looksLikeRepoPath(raw)
        if (p)
          return p
      }
    }

    // 聊天气泡 / 引用芯片：点击带 @path 的节点
    let el = target
    for (let i = 0; i < 4 && el; i++) {
      const text = (el.getAttribute && (el.getAttribute('title') || el.getAttribute('aria-label'))) || el.textContent || ''
      const compact = String(text).trim()
      if (compact.length < 200) {
        const at = compact.match(/@([^\s@]+)/)
        if (at) {
          const p = looksLikeRepoPath(at[1])
          if (p)
            return p
        }
        const p2 = looksLikeRepoPath(compact)
        if (p2 && (p2.includes('/') || p2.includes('.')))
          return p2
      }
      el = el.parentElement
    }
    return ''
  }

  function isInsideComposerChrome(target) {
    if (!target || !target.closest)
      return false
    // 输入框 / @ 芯片 / 空态 composer：点击只为聚焦编辑，勿打开左侧文件
    return !!(
      target.closest('[role="textbox"], textarea, input, [contenteditable="true"]')
      || target.closest('[class*="uV2eYG_"]')
      || target.closest('[class*="composerSeat"], [class*="composerStack"], [class*="composerHero"]')
      || target.closest('[class*="pXSMma_stack"], [class*="pXSMma_body"], [class*="pXSMma_workspace"], [class*="pXSMma_root"]')
      || target.closest('[class*="EmptyHero"], [class*="emptyHero"]')
    )
  }

  function onClickOpenInIdea(e) {
    if (!(window.parent && window.parent !== window))
      return
    if (isInsideComposerChrome(e.target))
      return
    const path = extractClickPath(e.target)
    if (!path)
      return
    // 仅聊天气泡内的路径：交给左侧 VS Code
    e.preventDefault()
    e.stopPropagation()
    if (typeof e.stopImmediatePropagation === 'function')
      e.stopImmediatePropagation()
    notifyParent({ type: 'easyaiot-open-in-idea', path })
  }

  const DEEPSEEK_PLATFORM_URL = 'https://platform.deepseek.com/'

  function isExternalHttpUrl(raw) {
    try {
      const u = new URL(String(raw || ''), location.href)
      return u.protocol === 'http:' || u.protocol === 'https:'
    }
    catch {
      return false
    }
  }

  // 嵌入门户时：拦截可能弹出的新窗口，改为通知左侧 IDE
  if (window.parent && window.parent !== window) {
    try {
      const origOpen = window.open.bind(window)
      window.open = function (url, target, features) {
        const s = String(url || '')
        // DeepSeek 注册/充值等外链：允许新开（或交给父页）
        if (isExternalHttpUrl(s) && !/vscode-remote:|file:/i.test(s)) {
          try {
            const opened = origOpen(url, target || '_blank', features)
            if (opened)
              return opened
          }
          catch { /* fall through */ }
          notifyParent({ type: 'easyaiot-open-external', url: s })
          return null
        }
        let path = ''
        try {
          if (/vscode-remote:|file:/.test(s)) {
            const u = new URL(s)
            path = decodeURIComponent(u.pathname || '')
          }
        }
        catch { /* ignore */ }
        if (!path) {
          const m = s.match(/([A-Za-z0-9_.\-]+\/[A-Za-z0-9_./+\-]+|[A-Za-z0-9_.\-]+\.[A-Za-z0-9]+)/)
          if (m)
            path = m[1]
        }
        path = looksLikeRepoPath(path.replace(/^\/home\/coder\/easyaiot\//, '').replace(/^\/workspace\/easyaiot\//, ''))
        if (path) {
          notifyParent({ type: 'easyaiot-open-in-idea', path })
          return null
        }
        // 非文件类打开仍走原逻辑（但嵌入场景尽量少弹窗）
        if (target === '_blank' || target === '_new')
          return null
        return origOpen(url, target, features)
      }
    }
    catch { /* ignore */ }
  }

  function isOnboardingKeyDialog(root) {
    if (!root || !root.querySelector)
      return false
    const text = (root.textContent || '').replace(/\s+/g, ' ')
    // dsh DeepSeekOnboardingDialog：无 Key 首次弹框
    if (/添加一个 API Key 开始使用|Add an API key to get started/i.test(text))
      return true
    if (/配置 DeepSeek 官方模型|Configure the official DeepSeek provider/i.test(text)
      && /API (密钥|key|Key)/i.test(text))
      return true
    return false
  }

  function styleOnboardingKeyInputs(dialog) {
    if (!dialog || !dialog.querySelectorAll)
      return
    dialog.querySelectorAll('input:not([type="checkbox"]):not([type="radio"]), textarea').forEach((el) => {
      el.classList.add('easyaiot-key-input-box')
    })
  }

  function ensureDeepseekPlatformHint(root) {
    const scope = root || document
    const nodes = scope.querySelectorAll('[role="dialog"], [class*="dialog"], [class*="Dialog"], [class*="Modal"], [class*="modal"]')
    const candidates = nodes.length ? [...nodes] : [document.body]
    for (const dialog of candidates) {
      if (!isOnboardingKeyDialog(dialog))
        continue

      styleOnboardingKeyInputs(dialog)

      if (dialog.querySelector('.easyaiot-deepseek-platform-hint'))
        continue

      const hint = document.createElement('p')
      hint.className = 'easyaiot-deepseek-platform-hint'
      const zh = /添加一个 API Key|配置 DeepSeek|请输入 API/i.test(dialog.textContent || '')
      const label = zh
        ? '还没有 Key？请前往 DeepSeek 开放平台注册并充值：'
        : 'Need a key? Register and top up at the DeepSeek Platform: '
      hint.appendChild(document.createTextNode(label))
      const a = document.createElement('a')
      a.href = DEEPSEEK_PLATFORM_URL
      a.target = '_blank'
      a.rel = 'noopener noreferrer'
      a.textContent = DEEPSEEK_PLATFORM_URL
      a.addEventListener('click', (e) => {
        // 嵌入 iframe 时确保外链能打开
        if (window.parent && window.parent !== window) {
          e.preventDefault()
          try {
            window.open(DEEPSEEK_PLATFORM_URL, '_blank', 'noopener,noreferrer')
          }
          catch {
            notifyParent({ type: 'easyaiot-open-external', url: DEEPSEEK_PLATFORM_URL })
          }
        }
      })
      hint.appendChild(a)

      // 插在描述段落后、输入区之前
      const desc = dialog.querySelector('p')
      if (desc && desc.parentElement)
        desc.insertAdjacentElement('afterend', hint)
      else {
        const body = dialog.querySelector('[class*="body"], [class*="Body"], [class*="content"], [class*="Content"]') || dialog
        body.insertBefore(hint, body.firstChild)
      }
    }
  }

  function ensureDropHint() {
    if (dropHint)
      return dropHint
    dropHint = document.createElement('div')
    dropHint.className = 'easyaiot-drop-hint'
    document.body.appendChild(dropHint)
    return dropHint
  }

  let hintTimer = 0
  function showDropHint(text) {
    const el = ensureDropHint()
    el.textContent = text
    el.classList.add('show')
    clearTimeout(hintTimer)
    hintTimer = window.setTimeout(() => el.classList.remove('show'), 2600)
  }

  function extractPathsFromDataTransfer(dt) {
    if (!dt)
      return []
    const out = []
    const push = (s) => {
      String(s || '').split(/[\r\n]+/).forEach((line) => {
        const t = line.trim()
        if (t && !t.startsWith('#'))
          out.push(t)
      })
    }
    const types = [...(dt.types || [])]
    const tryGet = (mime) => {
      try {
        return dt.getData(mime) || ''
      }
      catch {
        return ''
      }
    }
    for (const mime of [
      'text/uri-list',
      'application/vnd.code.uri-list',
      'resourceurls',
      'text/plain',
      'text/html',
    ]) {
      if (types.includes(mime) || mime === 'text/plain')
        push(tryGet(mime))
    }
    // resourceurls sometimes JSON
    try {
      const raw = tryGet('resourceurls')
      if (raw && raw.trim().startsWith('[')) {
        JSON.parse(raw).forEach((u) => out.push(String(u)))
      }
    }
    catch { /* ignore */ }

    if (dt.files && dt.files.length) {
      for (const f of dt.files) {
        if (f.name)
          out.push(f.name)
      }
    }
    return out
  }

  let scanPaused = false
  let scanPauseUntil = 0
  let observing = false
  const obs = new MutationObserver(() => {
    if (!observing || scanPaused)
      return
    scheduleScan()
  })
  function startObserve() {
    if (observing || scanPaused)
      return
    observing = true
    // 只看子树增删，属性变动太多会拖垮拖拽帧率
    obs.observe(document.documentElement, { childList: true, subtree: true })
  }

  function pauseScan(ms) {
    scanPaused = true
    scanPauseUntil = Date.now() + (ms || 400)
    try { obs.disconnect() } catch { /* ignore */ }
    observing = false
    if (scanTimer) {
      clearTimeout(scanTimer)
      scanTimer = 0
    }
  }

  function maybeResumeScan() {
    if (!scanPaused)
      return
    if (Date.now() < scanPauseUntil)
      return
    scanPaused = false
    startObserve()
  }

  function onParentMessage(ev) {
    const data = ev.data
    if (!data || typeof data !== 'object')
      return
    if (data.type === 'easyaiot-attach-files' && Array.isArray(data.paths)) {
      insertMentions(data.paths)
    }
    else if (data.type === 'easyaiot-harness-resize-start') {
      pauseScan(60000)
    }
    else if (data.type === 'easyaiot-harness-resize-end') {
      scanPauseUntil = Date.now() + 400
      window.setTimeout(() => {
        maybeResumeScan()
        forceCollapsedChrome()
      }, 420)
    }
    else if (data.type === 'easyaiot-harness-resize') {
      // 兼容旧消息：短暂停扫
      pauseScan(400)
      window.setTimeout(maybeResumeScan, 420)
    }
  }

  function onDragOver(e) {
    if (!e.dataTransfer)
      return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
    ensureDropHint().textContent = '松开以将文件关联到对话（@路径）'
    ensureDropHint().classList.add('show')
  }

  function onDragLeave() {
    // keep hint briefly
  }

  function onDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    const paths = extractPathsFromDataTransfer(e.dataTransfer)
    insertMentions(paths)
    ensureDropHint().classList.remove('show')
  }

  function updateEmbedClass() {
    const embed = isEmbedMode()
    document.documentElement.classList.toggle('easyaiot-embed', embed)
    if (document.body)
      document.body.classList.toggle('easyaiot-embed', embed)
    // 去掉「工作区」浮动开关；侧栏始终按默认布局显示
    document.documentElement.classList.remove('easyaiot-rail-open', 'easyaiot-mobile')
    document.body?.classList.remove('easyaiot-mobile')
    document.querySelectorAll('.easyaiot-rail-toggle').forEach((el) => el.remove())
  }

  function isEmbedMode() {
    if (window.parent && window.parent !== window)
      return true
    const emb = (new URLSearchParams(location.search).get('embed') || '').toLowerCase()
    return emb === 'idea' || emb === '1' || emb === 'portal' || emb === 'true'
  }

  function forceCollapsedChrome() {
    // 宽屏时上游会把 sidebar 自动展开成「工作区」；嵌入时锁成 52px 图标轨
    if (!isEmbedMode())
      return
    document.querySelectorAll('[class*="pI_x6G_frame"]').forEach((el) => {
      el.setAttribute('data-sidebar-collapsed', '')
      el.setAttribute('data-details-collapsed', '')
      try {
        el.style.setProperty('grid-template-columns', '52px minmax(0, 1fr) 0', 'important')
      }
      catch { /* ignore */ }
    })
  }

  function scan() {
    if (scanPaused || Date.now() < scanPauseUntil)
      return
    preferVscodeLight()
    updateEmbedClass()
    forceCollapsedChrome()
    document.querySelectorAll('button[class*="brand"]').forEach(renderSidebar)
    // 标语用 CSS 隐藏；JS 只做极轻量标记，避免 display:none 拆 React 树
    document.querySelectorAll('[class*="pXSMma_headline"]').forEach((el) => {
      if (el.dataset.easyaiotHero === '1')
        return
      el.dataset.easyaiotHero = '1'
    })
    replaceAllFishLogos(document)
    ensureDeepseekPlatformHint(document)
  }

  function scheduleScan() {
    if (scanPaused || Date.now() < scanPauseUntil)
      return
    if (scanTimer)
      return
    scanTimer = window.setTimeout(() => {
      scanTimer = 0
      scan()
    }, 600)
  }

  if (cfg.name)
    document.title = name

  // 禁止单独打开 HARNESS：顶层页面跳回 IDEA 门户
  ;(function enforcePortalEmbed() {
    if (window.parent && window.parent !== window)
      return
    const params = new URLSearchParams(location.search)
    const emb = (params.get('embed') || '').toLowerCase()
    if (emb === 'idea' || emb === '1' || emb === 'portal')
      return
    const idea = (cfg.ideaUrl || '').trim()
      || `${location.protocol}//${location.hostname}:9300`
    const dest = idea.replace(/\/$/, '') + '/?harness=1'
    try {
      location.replace(dest)
    }
    catch {
      location.href = dest
    }
  })()

  preferVscodeLight()
  scan()

  window.addEventListener('message', onParentMessage)
  document.addEventListener('dragover', onDragOver, true)
  document.addEventListener('dragleave', onDragLeave, true)
  document.addEventListener('drop', onDrop, true)
  document.addEventListener('click', onClickOpenInIdea, true)

  // 暴露给同页调试
  window.__easyaiotAttachFiles = insertMentions

  const _scan = scan
  scan = function scanSafe() {
    if (scanPaused || Date.now() < scanPauseUntil)
      return
    observing = false
    try {
      obs.disconnect()
    }
    catch { /* ignore */ }
    try {
      _scan()
    }
    finally {
      startObserve()
    }
  }
  startObserve()
})()
