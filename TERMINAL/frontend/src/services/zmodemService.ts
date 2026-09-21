import Zmodem from 'zmodem.js/src/zmodem_browser'
import {
  SessionEndZmodem,
  SessionEndZmodemWithTrailing,
  SessionStartZmodem,
  SessionWriteBinary,
  AppendFileBase64,
  FileSize,
  ReadFileChunkBase64,
  OpenDirectoryDialog,
  OpenMultipleFilesDialog,
} from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import { useZmodemStore } from '../stores/zmodemStore'
import { queuedSessionWrite } from './sessionWriter'

const dialogLocks = new Set<string>()
const TRANSFER_TIMEOUT_MS = 20_000
const CANCEL_WRITE_TIMEOUT_MS = 2_000
// After the cancel sequence, wait for the residual binary stream to drain
// before leaving binary mode. See waitBinaryQuiet.
const CANCEL_QUIET_MS = 400
const CANCEL_QUIET_CAP_MS = 8_000
const CANCEL_QUIET_POLL_MS = 80
const TRAILING_OUTPUT_GRACE_MS = 75
const MAX_TRAILING_OUTPUT_BYTES = 64 * 1024
const END_MODE_ATTEMPTS = 3
const PEER_ABORT_BEFORE_OFFER = 'peer_aborted_before_offer'
const CAN = 0x18
const PEER_ABORT_CAN_COUNT = 5
const CANCEL_SEQUENCE = new Uint8Array([
  CAN, CAN, CAN, CAN, CAN, CAN, CAN, CAN, CAN, CAN,
  0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
])

interface TransferControl {
  promise: Promise<never>
  abort(error?: Error): void
}

interface ActivityWatchdog {
  start(): void
  touch(): void
  stop(): void
  race<T>(promise: Promise<T>): Promise<T>
}

export interface ZmodemServiceOptions {
  sessionId: string
  direction?: 'upload' | 'download'
  getDefaultDownloadDir?: () => string
  onComplete?: (files: string[], hint?: string) => void
  onError?: (err: string) => void
  onWarning?: (warning: string) => void
  onTerminalRestoreState?: (restoring: boolean) => void
  onRegister?: (abort: () => void) => void
  onUnregister?: () => void
}

export function startZmodemService(options: ZmodemServiceOptions) {
  let binaryUnsub: (() => void) | null = null
  let currentZsession: import('zmodem.js/src/zmodem_browser').Session | null = null
  let aborted = false
  let disposed = false
  let notified = false
  let writeChain: Promise<void> = Promise.resolve()
  let writeFailure: unknown = null
  let suppressSender = false
  let cancelPromise: Promise<void> | null = null
  let startSessionPromise: Promise<void> | null = null
  let endSessionPromise: Promise<void> | null = null
  let captureTrailingOutput = false
  let captureLateTrailingOutput = false
  let receivedFileOffer = false
  let lastBinaryAt = 0
  const trailingOutput: number[] = []
  const lateTrailingOutput: number[] = []
  const { sessionId } = options
  const abortCtl = createTransferControl()
  const watchdog = createActivityWatchdog(TRANSFER_TIMEOUT_MS)

  function appendTrailingOutput(bytes: ArrayLike<number>, start = 0, end = bytes.length) {
    const target = captureLateTrailingOutput ? lateTrailingOutput : trailingOutput
    if (end <= start) return
    if (end - start >= MAX_TRAILING_OUTPUT_BYTES) {
      target.length = 0
      start = end - MAX_TRAILING_OUTPUT_BYTES
    } else {
      const overflow = target.length + end - start - MAX_TRAILING_OUTPUT_BYTES
      if (overflow > 0) target.splice(0, overflow)
    }
    for (let i = start; i < end; i++) target.push(bytes[i])
  }

  const notifyComplete = (files: string[], hint?: string) => {
    if (notified) return
    notified = true
    watchdog.stop()
    if (hint === undefined) options.onComplete?.(files)
    else options.onComplete?.(files, hint)
  }
  const notifyError = (error: unknown) => {
    if (notified) return
    notified = true
    watchdog.stop()
    options.onError?.(errorMessage(error))
  }

  function sender(octets: number[]) {
    if (aborted || disposed || suppressSender) return
    const base64 = arrayBufferToBase64(new Uint8Array(octets))
    writeChain = writeChain
      .then(() => {
        if (aborted || disposed) return
        return SessionWriteBinary(sessionId, base64)
      })
      .then(() => watchdog.touch())
      .catch((error) => {
        writeFailure = writeFailure || error
        abortCtl.abort(error instanceof Error ? error : new Error(errorMessage(error)))
      })
  }

  async function drainWrites() {
    const pending = writeChain
    await watchdog.race(pending)
    if (writeFailure) throw writeFailure
  }

  function startBackendMode(): Promise<void> {
    if (!startSessionPromise) startSessionPromise = SessionStartZmodem(sessionId)
    return startSessionPromise!
  }

  function endBackendMode(trailing?: Uint8Array): Promise<void> {
    if (endSessionPromise) return endSessionPromise
    endSessionPromise = (async () => {
      // A quick cancel can arrive while the start bridge call is still in
      // flight. Never let that delayed start overtake the matching end.
      try { await startSessionPromise } catch (_) {}
      if (trailing && trailing.length > 0) {
        // Decoding advances the session's streaming decoder, so this call is
        // deliberately not retried: replaying it could duplicate output or
        // corrupt decoder state if the first response was lost.
        try {
          await watchdog.race(
            SessionEndZmodemWithTrailing(sessionId, arrayBufferToBase64(trailing)),
          )
          return
        } catch (error) {
          // The bridge may have failed before the backend handled the call.
          // A plain end is idempotent and prevents binary mode remaining set;
          // preserve the original error because the prompt could be missing.
          try { await withTimeout(SessionEndZmodem(sessionId), CANCEL_WRITE_TIMEOUT_MS) } catch (_) {}
          throw error
        }
      }
      let lastError: unknown
      for (let attempt = 0; attempt < END_MODE_ATTEMPTS; attempt++) {
        try {
          await SessionEndZmodem(sessionId)
          return
        } catch (error) {
          lastError = error
        }
      }
      throw lastError
    })()
    return endSessionPromise
  }

  // The SSH channel still holds ZDATA frames sz pushed before it noticed the
  // CANs; while its send window is full sz does not read input at all, so it
  // can keep sending well past the cancel click. Keep binary mode alive until
  // the binary stream goes quiet so the residual frames stay on the ignored
  // binary path instead of leaking into the text terminal as garbage. The cap
  // bounds the wait when the peer ignores the cancel entirely.
  function waitBinaryQuiet(): Promise<void> {
    lastBinaryAt = Date.now()
    const deadline = Date.now() + CANCEL_QUIET_CAP_MS
    return new Promise(resolve => {
      const poll = () => {
        const now = Date.now()
        if (now - lastBinaryAt >= CANCEL_QUIET_MS || now >= deadline) {
          resolve()
          return
        }
        setTimeout(poll, CANCEL_QUIET_POLL_MS)
      }
      setTimeout(poll, CANCEL_QUIET_POLL_MS)
    })
  }

  function cancel(reason = new Error('aborted')): Promise<void> {
    if (cancelPromise) return cancelPromise
    aborted = true
    watchdog.stop()
    abortCtl.abort(reason)
    suppressSender = true
    try { currentZsession?.abort() } catch (_) {}

    cancelPromise = (async () => {
      // Preserve protocol ordering where possible. A broken in-flight bridge
      // call is bounded so it cannot prevent local recovery.
      try { await withTimeout(writeChain, CANCEL_WRITE_TIMEOUT_MS) } catch (_) {}
      try {
        await withTimeout(
          SessionWriteBinary(sessionId, arrayBufferToBase64(CANCEL_SEQUENCE)),
          CANCEL_WRITE_TIMEOUT_MS,
        )
      } catch (_) {
        // Local cleanup below must run even if the session bridge is broken.
      } finally {
        queuedSessionWrite(sessionId, '\x03')
        await waitBinaryQuiet()
        await endBackendMode()
        disarmTerminalRestore()
      }
    })()
    return cancelPromise
  }

  async function fail(error: unknown) {
    const reason = error instanceof Error ? error : new Error(errorMessage(error))
    try {
      await cancel(reason)
      notifyError(error)
    } catch (cleanupError) {
      notifyError(cleanupError)
    }
  }

  function recoverMissingOverAndOut(error: unknown): boolean {
    if (!errorMessage(error).startsWith('PROTOCOL: Only thing after ZFIN should be')) return false

    const session = currentZsession as any
    if (session?.type !== 'receive' || !session._got_ZFIN || !Array.isArray(session._input_buffer)) {
      return false
    }

    // Some sz implementations restore the shell immediately after ZFIN and
    // omit the expected "OO" terminator. zmodem.js treats the prompt already
    // buffered after ZFIN as fatal; finish the otherwise complete session and
    // preserve those bytes as ordinary terminal output instead.
    const trailing = session._input_buffer.slice()
    if (trailing.length === 0 || typeof session._on_session_end !== 'function') return false
    session._input_buffer.length = 0
    session._bytes_after_OO = trailing.slice()
    session._on_session_end()
    if (captureTrailingOutput) appendTrailingOutput(trailing)
    return true
  }

  function tolerateUnexpectedZack(error: unknown): boolean {
    if (errorMessage(error) !== 'Unhandled header: ZACK') return false

    const session = currentZsession as any
    if (session?.type !== 'send') return false

    // zmodem.js sends periodic ZSINIT keepalives while the file picker is
    // open. More than one delayed ZACK can arrive after send_offer() has
    // replaced the keepalive handler with the ZRPOS/ZSKIP handler. The
    // library has already consumed the duplicate header before throwing, so
    // retain the active handler and wait for the receiver's actual response.
    session._got_ZSINIT_ZACK = true
    if (Array.isArray(session._input_buffer) && session._input_buffer.length > 0
      && typeof session._consume_first === 'function') {
      while (session._input_buffer.length > 0) {
        const previousLength = session._input_buffer.length
        try {
          session._consume_first()
          break
        } catch (resumeError) {
          if (errorMessage(resumeError) !== 'Unhandled header: ZACK'
            || session._input_buffer.length >= previousLength) {
            void fail(resumeError)
            break
          }
          session._got_ZSINIT_ZACK = true
        }
      }
    }
    return true
  }

  function recoverPeerAbortBeforeOffer(error: unknown): boolean {
    if (errorMessage(error) !== 'Peer aborted session') return false

    const session = currentZsession as any
    if (session?.type !== 'receive' || receivedFileOffer) return false

    // lsz sends CANs when it cannot open the requested file. zmodem.js drops
    // everything through the first five CANs, including useful stderr that
    // preceded them. Recover text around the cancel sequence and discard the
    // remaining CAN/backspace padding before restoring normal terminal mode.
    const consumed = Array.isArray(session._bytes_being_consumed)
      ? session._bytes_being_consumed
      : []
    const abortAt = findAbortSequence(consumed)
    if (abortAt >= 0) {
      appendTrailingOutput(consumed, 0, abortAt)
      let trailingAt = abortAt + PEER_ABORT_CAN_COUNT
      while (consumed[trailingAt] === CAN || consumed[trailingAt] === 0x08) trailingAt++
      appendTrailingOutput(consumed, trailingAt)
    }
    abortCtl.abort(new Error(PEER_ABORT_BEFORE_OFFER))
    return true
  }

  function consumeIncoming(data: Uint8Array) {
    try {
      sentry.consume(data)
    } catch (error) {
      // Residual remote output after our cancel sequence (e.g. sz's own
      // abort reply) hits the already-aborted session; it is cleanup noise,
      // not a transfer failure.
      if (aborted) return
      if (!recoverMissingOverAndOut(error)
        && !tolerateUnexpectedZack(error)
        && !recoverPeerAbortBeforeOffer(error)) {
        void fail(error)
      }
    }
  }

  function beginTerminalRestore() {
    if (captureTrailingOutput) return
    captureTrailingOutput = true
    options.onTerminalRestoreState?.(true)
  }

  // The receive session's `session_end` handler arms terminal-restore capture,
  // and zmodem.js fires session_end synchronously inside abort(). finishTransfer
  // is the only place that normally disarms it, but cancellation never goes
  // through finishTransfer — leaving the terminal swallowing all subsequent
  // output forever. Disarm here so the normal text path resumes and the
  // completion/error handler can recycle the service.
  function disarmTerminalRestore() {
    captureTrailingOutput = false
    captureLateTrailingOutput = false
    trailingOutput.length = 0
    lateTrailingOutput.length = 0
    options.onTerminalRestoreState?.(false)
  }

  async function finishTransfer(files: string[], hint?: string) {
    try {
      // session_end can fire before the bridge promise for the final response
      // has settled. Wait until that response (normally our final ZFIN) has
      // reached the remote sz before leaving binary mode; otherwise the end
      // call can overtake it and the remote shell will not print its next
      // prompt until the user presses Enter.
      await drainWrites()

      // lsz can restore the tty and print the shell prompt in the SSH read
      // immediately after the chunk containing OO. Keep binary routing alive
      // briefly so Sentry can forward that separate trailing chunk instead of
      // losing it during the service teardown.
      const session = currentZsession as any
      if (trailingOutput.length === 0 && session?.type === 'send') {
        await delay(TRAILING_OUTPUT_GRACE_MS)
      } else if (trailingOutput.length === 0
        && session?.type === 'receive'
        && typeof session.get_trailing_bytes === 'function') {
        let trailingBytes: number[] = []
        try { trailingBytes = session.get_trailing_bytes() } catch (_) {}
        if (trailingBytes.length === 0) await delay(TRAILING_OUTPUT_GRACE_MS)
      }

      // Start the ordered backend handoff, but report completion before its
      // trailing terminal event is emitted. This keeps the restored shell
      // prompt below our status message. Reporting after the awaited handoff
      // can print the status below an already-rendered prompt, leaving the
      // cursor on a blank line until the user presses Enter.
      captureLateTrailingOutput = true
      const ending = endBackendMode(Uint8Array.from(trailingOutput))
      dialogLocks.delete(sessionId)
      notifyComplete(files, hint)
      await ending
      // A binary event already queued before EndZmodem may be delivered while
      // the bridge call is in flight. Emit only those newly captured bytes;
      // later SSH reads are already routed through the normal text path.
      if (lateTrailingOutput.length > 0) {
        await SessionEndZmodemWithTrailing(
          sessionId,
          arrayBufferToBase64(Uint8Array.from(lateTrailingOutput)),
        )
      }
      trailingOutput.length = 0
      lateTrailingOutput.length = 0
    } catch (error) {
      // The transfer itself has completed. Failure to restore trailing shell
      // output must not send a cancel sequence or Ctrl+C to the restored shell.
      // Still leave binary mode so the terminal returns to text output instead
      // of waiting for the backend's minutes-long zmodem safety timeout; this
      // is idempotent when endBackendMode already ran before the failure.
      try { await endBackendMode() } catch (_) {}
      dialogLocks.delete(sessionId)
      notifyComplete(files, hint)
      options.onWarning?.(`Shell output restore failed: ${errorMessage(error)}`)
    } finally {
      captureLateTrailingOutput = false
      options.onTerminalRestoreState?.(false)
    }
  }

  const sentry = new Zmodem.Sentry({
    // A receive session can deliver the final "OO" and the restored shell
    // prompt in one chunk. zmodem.js strips OO and forwards the remaining
    // bytes here; retain them until the completion message has been shown.
    to_terminal: (octets: number[]) => {
      if (captureTrailingOutput) appendTrailingOutput(octets)
    },
    sender,
    on_detect: (detection: import('zmodem.js/src/zmodem_browser').Detection) => {
      if (disposed || dialogLocks.has(sessionId)) return
      const zsession = detection.confirm()
      currentZsession = zsession
      dialogLocks.add(sessionId)
      if (zsession.type === 'send') {
        // zmodem.js discards trailing input after a send session ends. Start
        // capturing before Sentry finishes consuming the ZFIN chunk so a
        // prompt in that chunk, or in the immediately following one, is
        // restored after our completion message.
        zsession.on('session_end', () => {
          if ((zsession as any)._sent_OO) beginTerminalRestore()
        })
      }

      const run = async () => {
        if (zsession.type === 'send') {
          const store = useZmodemStore()
          const pendingPaths = store.getPendingUploadFiles(sessionId)
          const paths: string[] = pendingPaths && pendingPaths.length > 0
            ? pendingPaths
            : await abortable(
              OpenMultipleFilesDialog().catch((err: unknown) => dialogCancelToEmpty<string[]>(err, [])),
              abortCtl,
            )
          if (paths.length === 0) {
            await cancel()
            notifyComplete([])
            return
          }
          watchdog.start()
          const result = await handleSend(zsession, sessionId, paths, drainWrites, () => aborted, abortCtl, watchdog)
          await finishTransfer(result.files, result.hint)
        } else {
          let saveDirPromise: Promise<string> | null = null
          const getSaveDir = () => {
            if (!saveDirPromise) {
              const configuredDir = options.getDefaultDownloadDir?.() || ''
              saveDirPromise = configuredDir.trim()
                ? Promise.resolve(configuredDir)
                : abortable(
                  OpenDirectoryDialog().catch((err: unknown) => dialogCancelToEmpty<string>(err, '')),
                  abortCtl,
                )
            }
            return saveDirPromise
          }
          watchdog.start()
          const files = await handleReceive(
            zsession, sessionId, getSaveDir, () => aborted, abortCtl, watchdog,
            beginTerminalRestore,
            () => { receivedFileOffer = true },
          )
          await finishTransfer(files)
        }
      }

      run().catch(async (err: unknown) => {
        if (disposed) return
        if (errorMessage(err) === PEER_ABORT_BEFORE_OFFER) {
          await finishTransfer([], 'Remote ZMODEM sender stopped before offering a file')
          return
        }
        if (errorMessage(err) === 'aborted') {
          try {
            await cancel()
            notifyComplete([])
          } catch (cleanupError) {
            notifyError(cleanupError)
          }
          return
        }
        await fail(err)
      }).finally(() => {
        dialogLocks.delete(sessionId)
        watchdog.stop()
      })
    },
    on_retract: () => { currentZsession = null },
  })

  binaryUnsub = Events.On('session:binary', (ev) => {
    const payload: { id: string; data: string } = ev.data
    if (payload.id !== sessionId || disposed) return
    lastBinaryAt = Date.now()
    watchdog.touch()
    consumeIncoming(base64ToUint8Array(payload.data))
  })

  const svc = {
    start: (data: string) => {
      if (disposed) return
      void startBackendMode().catch(err => { void fail(err) })
      svc.consume(data)
    },
    consume: (data: string) => {
      if (disposed) return
      watchdog.touch()
      consumeIncoming(new TextEncoder().encode(data))
    },
    dispose: async () => {
      if (disposed) return
      disposed = true
      watchdog.stop()
      abortCtl.abort(new Error('aborted'))
      binaryUnsub?.()
      binaryUnsub = null
      dialogLocks.delete(sessionId)
      options.onUnregister?.()
      // Pair disposal with an ordered end even when the component is
      // unmounted before the pending start bridge call completes.
      try { await endBackendMode() } catch (_) {}
    },
    isAborted: () => aborted,
    abort: async () => {
      try { await cancel() } catch (err) { notifyError(err) }
    },
  }

  options.onRegister?.(() => { void svc.abort() })
  return svc
}

async function handleSend(
  zsession: import('zmodem.js/src/zmodem_browser').Session,
  sessionId: string,
  paths: string[],
  drainWrites: () => Promise<void>,
  isAborted: () => boolean,
  abortCtl: TransferControl,
  watchdog: ActivityWatchdog,
): Promise<{ files: string[]; hint?: string }> {
  const store = useZmodemStore()
  const files: string[] = []
  for (let i = 0; i < paths.length; i++) {
    if (isAborted()) throw new Error('aborted')
    const path = paths[i]
    const filename = path.split(/[\\/]/).pop() || 'unknown'
    const transferId = `${sessionId}-up-${i}`
    const fileSize = Number(await watchdog.race<number>(FileSize(path)))
    store.addTransfer(sessionId, {
      id: transferId, sessionId, filename, size: fileSize, transferred: 0,
      direction: 'upload', status: 'transferring', speed: 0,
    })

    const xfer: any = await abortable(
      watchdog.race((zsession as any).send_offer({
        name: filename, size: fileSize, mode: 0o644, mtime: new Date(),
        files_remaining: paths.length - i,
        bytes_remaining: fileSize,
      })),
      abortCtl,
    )
    if (!xfer) {
      store.updateTransfer(sessionId, transferId, {
        status: 'cancelled', error: 'File exists, please delete and retry',
      })
      await watchdog.race(zsession.close())
      return {
        files,
        hint: `"${filename}" already exists. Please delete it first (rm "${filename}"), then retry.`,
      }
    }

    await abortable(
      sendFileChunks(xfer, path, fileSize, CHUNK, sessionId, transferId, drainWrites, isAborted, watchdog),
      abortCtl,
    )
    store.updateTransfer(sessionId, transferId, { status: 'completed', transferred: fileSize })
    files.push(filename)
  }
  if (!isAborted()) await abortable(watchdog.race(zsession.close()), abortCtl)
  return { files }
}

const CHUNK = 8192
const READ_CHUNK = CHUNK * 16
const DOWNLOAD_BATCH = 64 * 1024

async function sendFileChunks(
  xfer: any, path: string, size: number, chunkSize: number,
  sessionId: string, transferId: string,
  drainWrites: () => Promise<void>,
  isAborted: () => boolean,
  watchdog: ActivityWatchdog,
) {
  const store = useZmodemStore()
  let offset = 0
  while (offset < size) {
    if (isAborted()) throw new Error('aborted')
    const length = Math.min(READ_CHUNK, size - offset)
    const encoded = await watchdog.race<string>(ReadFileChunkBase64(path, offset, length))
    const data = base64ToUint8Array(encoded)
    if (data.length === 0) throw new Error(`Read empty chunk at offset ${offset}`)
    for (let chunkOffset = 0; chunkOffset < data.length;) {
      if (isAborted()) throw new Error('aborted')
      const end = Math.min(chunkOffset + chunkSize, data.length)
      const chunk = Array.from(data.slice(chunkOffset, end)) as number[]
      xfer.send(chunk)
      await drainWrites()
      chunkOffset = end
      offset += chunk.length
      watchdog.touch()
      store.updateTransfer(sessionId, transferId, { transferred: offset })
    }
  }
  await watchdog.race(xfer.end([]))
  await drainWrites()
}

async function handleReceive(
  zsession: import('zmodem.js/src/zmodem_browser').Session,
  sessionId: string,
  getSaveDir: () => Promise<string>,
  isAborted: () => boolean,
  abortCtl: TransferControl,
  watchdog: ActivityWatchdog,
  onSessionEnd: () => void,
  onOffer: () => void,
): Promise<string[]> {
  const store = useZmodemStore()
  const files: string[] = []
  const activeOffers = new Set<Promise<void>>()
  let offerCount = 0
  let offerFailure: unknown = null
  let endSession!: () => void
  const sessionEnded = new Promise<void>(resolve => { endSession = resolve })
  zsession.on('session_end', () => {
    onSessionEnd()
    endSession()
  })

  zsession.on('offer', (offer: any) => {
    if (isAborted()) {
      try { offer.skip() } catch (_) {}
      return
    }
    const task = (async () => {
      const saveDir = await getSaveDir()
      if (!saveDir) throw new Error('aborted')
      onOffer()
      const windowsPath = /^[a-zA-Z]:[\\/]/.test(saveDir) || saveDir.startsWith('\\\\')
      const sep = windowsPath ? '\\' : '/'
      await receiveOffer(offer, saveDir, sep, sessionId, offerCount++, store, watchdog, files)
    })()
    activeOffers.add(task)
    task.catch(err => {
      offerFailure = offerFailure || err
      abortCtl.abort(err instanceof Error ? err : new Error(errorMessage(err)))
    }).finally(() => activeOffers.delete(task))
  })

  await abortable(watchdog.race(zsession.start()), abortCtl)
  await abortable(watchdog.race(sessionEnded), abortCtl)
  while (activeOffers.size > 0) {
    await abortable(watchdog.race(Promise.allSettled([...activeOffers]).then(() => undefined)), abortCtl)
  }
  if (offerFailure) throw offerFailure
  return files
}

async function receiveOffer(
  offer: any, saveDir: string, sep: string, sessionId: string, offerIndex: number,
  store: ReturnType<typeof useZmodemStore>, watchdog: ActivityWatchdog, files: string[],
) {
  watchdog.touch()
  const details = offer.get_details()
  const filename = safeDownloadFilename(details.name, sep === '\\')
  const size = details.size || 0
  const finalSavePath = `${saveDir}${saveDir.endsWith('/') || saveDir.endsWith('\\') ? '' : sep}${filename}`
  const transferId = `${sessionId}-dl-${offerIndex}`
  store.addTransfer(sessionId, {
    id: transferId, sessionId, filename, size, transferred: 0,
    direction: 'download', status: 'transferring', speed: 0, savePath: finalSavePath,
  })

  let received = 0
  let buffer: number[] = []
  let bufferOffset = 0
  let pendingWrites: Promise<void> = Promise.resolve()
  const flush = () => {
    while (buffer.length > 0) {
      const bytes = buffer.splice(0, Math.min(DOWNLOAD_BATCH, buffer.length))
      const offset = bufferOffset
      bufferOffset += bytes.length
      pendingWrites = pendingWrites.then(async () => {
        await watchdog.race(AppendFileBase64(
          finalSavePath, arrayBufferToBase64(Uint8Array.from(bytes)), offset,
        ))
        watchdog.touch()
      })
    }
  }
  const onInput = (payload: number[]) => {
    buffer.push(...payload)
    received += payload.length
    watchdog.touch()
    store.updateTransfer(sessionId, transferId, { transferred: received })
    if (buffer.length >= DOWNLOAD_BATCH) flush()
  }

  try {
    await watchdog.race(offer.accept({ on_input: onInput }))
    flush()
    await watchdog.race(pendingWrites)
    store.updateTransfer(sessionId, transferId, { status: 'completed', transferred: received })
    files.push(finalSavePath)
  } catch (err) {
    store.updateTransfer(sessionId, transferId, { status: 'error', error: errorMessage(err) })
    throw err
  }
}

function createActivityWatchdog(timeoutMs: number): ActivityWatchdog {
  let timer: ReturnType<typeof setTimeout> | null = null
  let rejectTimeout: ((error: Error) => void) | null = null
  let timeoutPromise: Promise<never> = new Promise(() => {})
  let running = false

  const arm = () => {
    if (!running) return
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      rejectTimeout?.(new Error(`ZMODEM transfer timed out after ${timeoutMs / 1000}s without activity`))
    }, timeoutMs)
  }
  return {
    start() {
      if (running) return
      running = true
      timeoutPromise = new Promise<never>((_, reject) => { rejectTimeout = reject })
      arm()
    },
    touch: arm,
    stop() {
      running = false
      if (timer) clearTimeout(timer)
      timer = null
      rejectTimeout = null
    },
    race<T>(promise: Promise<T>) {
      return running ? Promise.race([promise, timeoutPromise]) : promise
    },
  }
}

async function abortable<T>(promise: Promise<T>, control: TransferControl): Promise<T> {
  return Promise.race([promise, control.promise])
}

function createTransferControl(): TransferControl {
  let reject!: (error: Error) => void
  let aborted = false
  const promise = new Promise<never>((_, rejectPromise) => { reject = rejectPromise })
  void promise.catch(() => {})
  return {
    promise,
    abort(error = new Error('aborted')) {
      if (aborted) return
      aborted = true
      reject(error)
    },
  }
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('cancel write timed out')), timeoutMs)
    promise.then(
      value => { clearTimeout(timer); resolve(value) },
      error => { clearTimeout(timer); reject(error) },
    )
  })
}

function dialogCancelToEmpty<T>(err: unknown, empty: T): T {
  if (String(err).toLowerCase().includes('cancel')) return empty
  throw err
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function findAbortSequence(bytes: number[]): number {
  let runLength = 0
  for (let i = 0; i < bytes.length; i++) {
    runLength = bytes[i] === CAN ? runLength + 1 : 0
    if (runLength === PEER_ABORT_CAN_COUNT) return i - PEER_ABORT_CAN_COUNT + 1
  }
  return -1
}

function safeDownloadFilename(value: unknown, windowsPath: boolean): string {
  const name = String(value || '')
  if (!name || name === '.' || name === '..' || name.includes('/') || name.includes('\\') || name.includes('\0')) {
    throw new Error(`Unsafe ZMODEM filename: ${JSON.stringify(name)}`)
  }
  if (windowsPath && (/[<>:"|?*]/.test(name) || /[. ]$/.test(name))) {
    throw new Error(`Unsafe ZMODEM filename: ${JSON.stringify(name)}`)
  }
  return name
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

function arrayBufferToBase64(buffer: Uint8Array): string {
  let binary = ''
  for (let i = 0; i < buffer.length; i++) binary += String.fromCharCode(buffer[i])
  return btoa(binary)
}
