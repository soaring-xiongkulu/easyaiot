import {
  ContainerConnect, ContainerDisconnect, ContainerList, ContainerInspect,
  ContainerAction, ContainerRename, ContainerStats, ContainerImages,
  ContainerRemoveImage, ContainerCreate, ContainerNamespaces,
  ContainerSetNamespace, ContainerStartLogs, ContainerStartPull,
  ContainerStopStream, ContainerExecSession,
} from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import type {
  ContainerInfo, InspectResult, ContainerImage, ContainerStats as ContainerStatsInfo, ContainerCreateOptions,
} from '../types/container'

export const connect = (id: string) => ContainerConnect(id)
export const disconnect = (id: string) => ContainerDisconnect(id)
export const list = (id: string) => ContainerList(id) as Promise<ContainerInfo[]>
export const inspect = (id: string, cid: string) => ContainerInspect(id, cid) as Promise<InspectResult>
export const action = (id: string, cid: string, act: string) => ContainerAction(id, cid, act)
export const rename = (id: string, cid: string, name: string) => ContainerRename(id, cid, name)
export const stats = (id: string) => ContainerStats(id) as Promise<ContainerStatsInfo[]>
export const images = (id: string) => ContainerImages(id) as Promise<ContainerImage[]>
export const removeImage = (id: string, imageID: string) => ContainerRemoveImage(id, imageID)
export const create = (id: string, opts: ContainerCreateOptions) => ContainerCreate(id, opts as any)
export const namespaces = (id: string) => ContainerNamespaces(id) as Promise<string[]>
export const setNamespace = (connId: string, ns: string) => ContainerSetNamespace(connId, ns)
export const execSession = (connId: string, cid: string, shell: string) =>
  ContainerExecSession(connId, cid, shell)

export interface StreamHandle {
  id: string
  stop: () => void
}

async function startStream(
  start: () => Promise<string>,
  onLine: (line: string) => void,
  onEnd?: (err: string) => void
): Promise<StreamHandle> {
  const id = await start()
  const evName = `container:stream:${id}`
  const endName = `container:stream-end:${id}`
 Events.On(evName, (ev) => { const p: { line: string } = ev.data; return onLine(p?.line ?? '') })
 Events.On(endName, (ev) => { const p: { error: string } = ev.data; 
    onEnd?.(p?.error || '')
    Events.Off(evName)
    Events.Off(endName)
   })
  return {
    id,
    stop: () => {
      Events.Off(evName)
      Events.Off(endName)
      ContainerStopStream(id)
    },
  }
}

export const startLogs = (connId: string, cid: string, tail: number, timestamps: boolean,
  onLine: (l: string) => void, onEnd?: (e: string) => void) =>
  startStream(() => ContainerStartLogs(connId, cid, tail, timestamps), onLine, onEnd)

export const startPull = (connId: string, image: string,
  onLine: (l: string) => void, onEnd?: (e: string) => void) =>
  startStream(() => ContainerStartPull(connId, image), onLine, onEnd)
