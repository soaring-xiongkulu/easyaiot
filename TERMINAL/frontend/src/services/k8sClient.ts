import {
  K8sListContexts,
  K8sConnect,
  K8sDisconnect,
  K8sRequest,
  K8sStartWatch,
  K8sStopWatch,
  K8sStartLogStream,
  K8sStopLogStream,
  K8sExecSession,
} from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import type { K8sContextInfo, K8sWatchEvent } from '../types/k8s'

export async function listContexts(source: string, sourceIsPath: boolean): Promise<K8sContextInfo[]> {
  return await K8sListContexts(source, sourceIsPath) as K8sContextInfo[]
}

export async function connect(
  source: string,
  sourceIsPath: boolean,
  contextName: string,
  tunnelSSHConnId = '',
  tunnelSSHUser = '',
  tunnelSSHPassword = ''
): Promise<string> {
  return await K8sConnect(source, sourceIsPath, contextName, tunnelSSHConnId, tunnelSSHUser, tunnelSSHPassword)
}

export function disconnect(connID: string): void {
  K8sDisconnect(connID)
}

export async function requestJSON<T = any>(
  connID: string,
  method: string,
  path: string,
  body: any = null,
  contentType = ''
): Promise<{ status: number; data: T | null; raw: string }> {
  const rawBody = body == null ? '' : (typeof body === 'string' ? body : JSON.stringify(body))
  const resp = await K8sRequest(connID, method, path, rawBody, contentType)
  let data: T | null = null
  try {
    data = resp.body ? JSON.parse(resp.body) as T : null
  } catch {
    data = null
  }
  return { status: resp.status, data, raw: resp.body }
}

export interface WatchHandle {
  id: string
  stop: () => void
}

export async function startWatch(
  connID: string,
  path: string,
  onEvent: (ev: K8sWatchEvent) => void,
  onEnd?: (err: string) => void
): Promise<WatchHandle> {
  const id = await K8sStartWatch(connID, path)
  const eventName = `k8s:watch:${id}`
  const endName = `k8s:watch-end:${id}`
 Events.On(eventName, (ev) => { const payload: K8sWatchEvent = ev.data; return onEvent(payload) })
 Events.On(endName, (ev) => { const payload: { error: string } = ev.data; 
    onEnd?.(payload?.error || '')
   })
  return {
    id,
    stop: () => {
      Events.Off(eventName)
      Events.Off(endName)
      K8sStopWatch(id)
    },
  }
}

export interface LogHandle {
  stop(): void
}

export async function startLogStream(
  connId: string,
  ns: string,
  pod: string,
  container: string,
  tailLines: number,
  timestamps: boolean,
  previous: boolean,
  onLine: (line: string) => void,
  onEnd: (err: string) => void
): Promise<LogHandle> {
  const streamId = await K8sStartLogStream(connId, ns, pod, container, tailLines, timestamps, previous)
  const evName = `k8s:log:${streamId}`
  const endName = `k8s:log-end:${streamId}`
 Events.On(evName, (ev) => { const line: string = ev.data; return onLine(line) })
 Events.On(endName, (ev) => { const p: any = ev.data; return onEnd(p?.error || '') })
  return {
    stop() {
      Events.Off(evName)
      Events.Off(endName)
      K8sStopLogStream(streamId)
    },
  }
}

export async function execSession(connId: string, ns: string, pod: string, container: string) {
  return await K8sExecSession(connId, ns, pod, container)
}
