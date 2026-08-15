/**
 * EasyAIoT IDEA ↔ HARNESS bridge
 * 通过 DataTransfer.prototype.setData 钩子捕获 VS Code Explorer 路径，
 * 再 postMessage 给 IDEA 门户（跨源 iframe 下原生 drop 读不到路径）。
 * 每次拖拽只上报一次，避免门户重复写入。
 *
 * 顶层单独打开 code-server 时跳回 IDEA 门户（仅允许门户 iframe 组合访问）。
 */
(function () {
  if (window.__easyaiotIdeBridge)
    return
  window.__easyaiotIdeBridge = 1

  function portalUrl() {
    try {
      const cfg = window.__EASYAIOT_IDEA_PORTAL__ || {}
      if (cfg.url)
        return String(cfg.url).replace(/\/$/, '')
    }
    catch { /* ignore */ }
    return `${location.protocol}//${location.hostname}:9300`
  }

  if (window.parent === window) {
    try {
      location.replace(portalUrl() + '/?harness=1')
    }
    catch {
      location.href = portalUrl() + '/?harness=1'
    }
    return
  }

  const MIME_PRIORITY = [
    'application/vnd.code.uri-list',
    'text/uri-list',
    'ResourceURLs',
    'resourceurls',
    'text/plain',
  ]

  let lastPaths = []
  let activeCapture = null
  let dragEpoch = 0
  let emittedEpoch = -1

  function decodePaths(raw) {
    const out = []
    const pushOne = (s) => {
      const t = String(s || '').trim()
      if (!t || t.startsWith('#'))
        return
      if (t.startsWith('[') && t.endsWith(']')) {
        try {
          JSON.parse(t).forEach(pushOne)
          return
        }
        catch { /* fallthrough */ }
      }
      out.push(t)
    }
    String(raw || '').split(/[\r\n]+/).forEach(pushOne)
    return out
  }

  function pathsFromMap(map) {
    if (!map)
      return []
    const found = []
    for (const mime of MIME_PRIORITY) {
      if (map[mime])
        decodePaths(map[mime]).forEach((p) => found.push(p))
    }
    Object.keys(map).forEach((k) => {
      if (/uri|resource|path|text/i.test(k) && map[k])
        decodePaths(map[k]).forEach((p) => found.push(p))
    })
    return [...new Set(found.filter(Boolean))]
  }

  function post(type, extra) {
    if (type === 'easyaiot-ide-dragstart' && extra && Array.isArray(extra.paths) && extra.paths.length)
      lastPaths = extra.paths.slice()
    try {
      window.parent.postMessage(Object.assign({ type, source: 'easyaiot-ide-bridge' }, extra || {}), '*')
    }
    catch { /* ignore */ }
  }

  try {
    const proto = DataTransfer.prototype
    if (!proto.__easyaiotHooked) {
      proto.__easyaiotHooked = true
      const origSet = proto.setData
      proto.setData = function (type, val) {
        if (activeCapture) {
          try {
            activeCapture[String(type)] = String(val)
          }
          catch { /* ignore */ }
        }
        return origSet.call(this, type, val)
      }
    }
  }
  catch (err) {
    post('easyaiot-ide-bridge-ready', { hookError: String(err && err.message || err) })
  }

  post('easyaiot-ide-bridge-ready', { hooked: !!(DataTransfer.prototype && DataTransfer.prototype.__easyaiotHooked) })

  function emitFrom(epoch, dt, map) {
    if (epoch !== dragEpoch || emittedEpoch === epoch)
      return
    if (dt) {
      for (const mime of MIME_PRIORITY) {
        try {
          const v = dt.getData(mime)
          if (v)
            map[mime] = v
        }
        catch { /* ignore */ }
      }
    }
    const paths = pathsFromMap(map)
    if (!paths.length)
      return
    emittedEpoch = epoch
    post('easyaiot-ide-dragstart', { paths })
  }

  document.addEventListener('dragstart', (e) => {
    dragEpoch += 1
    const epoch = dragEpoch
    emittedEpoch = -1
    activeCapture = Object.create(null)
    const dt = e.dataTransfer
    const map = activeCapture
    // 只保留一次延迟读取（等 VS Code 写完 MIME），不再连发三次
    setTimeout(() => emitFrom(epoch, dt, map), 0)
  }, true)

  document.addEventListener('dragend', () => {
    activeCapture = null
    post('easyaiot-ide-dragend', {})
  }, true)

  window.addEventListener('message', (ev) => {
    const data = ev.data
    if (!data || typeof data !== 'object')
      return
    if (data.type === 'easyaiot-ide-request-paths') {
      if (lastPaths.length) {
        post('easyaiot-ide-dragstart', { paths: lastPaths })
        return
      }
      const label = document.querySelector(
        '.tab.active .label-name, .tabs-container .tab.active .tab-label, [aria-selected="true"] .label-name',
      )
      const name = ((label && label.textContent) || '').trim().replace(/^\[Preview\]\s*/, '')
      if (name)
        post('easyaiot-ide-dragstart', { paths: [name], weak: true })
      else
        post('easyaiot-ide-no-selection', {})
    }
    else if (data.type === 'easyaiot-ide-open-file') {
      openWorkspaceFile(data.path || data.file || '')
    }
  })

  function openWorkspaceFile(raw) {
    let p = String(raw || '').trim().replace(/\\/g, '/').replace(/^@/, '')
    if (!p)
      return
    p = p.replace(/^\/home\/coder\/easyaiot\//, '')
    p = p.replace(/^\/workspace\/easyaiot\//, '')
    p = p.replace(/^\/+/, '').replace(/^(workspace\/)?easyaiot\//, '')
    p = p.replace(/#.*$/, '')
    if (!p || p.includes('..'))
      return
    const abs = '/home/coder/easyaiot/' + p
    const folder = encodeURIComponent('/home/coder/easyaiot')
    const remote = 'vscode-remote://' + abs
    const payload = encodeURIComponent(JSON.stringify([['openFile', remote]]))
    const next = `/?folder=${folder}&payload=${payload}&_t=${Date.now()}`
    post('easyaiot-ide-open-file-done', { path: p })
    location.assign(next)
  }
})()
