import { defineStore } from 'pinia'
import * as client from '../services/containerClient'
import { usePanelStore } from './panelStore'
import { useTabStore } from './tabStore'
import { useSessionStore } from './sessionStore'
import type { ContainerTab, ContainerInfo, ContainerImage, InspectResult } from '../types/container'

export interface ContainerSession {
  connId: string
  runtime: ContainerTab['runtime']
  containers: ContainerInfo[]
  images: ContainerImage[]
  namespaces: string[]
  namespace: string
  loading: boolean
  refreshing: boolean
  error: string
}

export const useContainerStore = defineStore('container', {
  state: () => ({ sessions: {} as Record<string, ContainerSession> }),
  actions: {
    async open(tab: ContainerTab) {
      this.sessions[tab.id] = {
        connId: tab.connectionId, runtime: tab.runtime,
        containers: [], images: [], namespaces: [], namespace: 'default',
        loading: true, refreshing: false, error: '',
      }
      // 读回响应式代理再操作：直接改闭包里的原始对象不会触发视图更新
      const s = this.sessions[tab.id]
      try {
        await client.connect(tab.connectionId)
        if (this.sessions[tab.id] !== s) {
          // 连接期间 tab 已关闭：回收后端连接
          client.disconnect(tab.connectionId)
          return
        }
        await this.refresh(tab.id)
        if (tab.runtime === 'nerdctl') {
          this.loadNamespaces(tab.id)
        }
      } catch (e: any) {
        s.error = e?.message || String(e)
      } finally {
        s.loading = false
      }
    },
    async refresh(tabId: string) {
      const s = this.sessions[tabId]
      if (!s || s.refreshing) return // 防止手动连点叠加并发 SSH 会话
      s.refreshing = true
      try {
        s.containers = await client.list(s.connId)
        s.error = ''
      } catch (e: any) {
        s.error = e?.message || String(e)
      } finally {
        s.refreshing = false
      }
    },
    async action(tabId: string, cid: string, act: string) {
      const s = this.sessions[tabId]
      if (!s) return
      await client.action(s.connId, cid, act)
      await this.refresh(tabId)
    },
    async rename(tabId: string, cid: string, name: string) {
      const s = this.sessions[tabId]
      if (!s) return
      await client.rename(s.connId, cid, name)
      await this.refresh(tabId)
    },
    async loadDetail(tabId: string, cid: string): Promise<InspectResult | null> {
      const s = this.sessions[tabId]
      if (!s) return null
      return await client.inspect(s.connId, cid)
    },
    async loadImages(tabId: string) {
      const s = this.sessions[tabId]
      if (!s) return
      s.images = await client.images(s.connId)
    },
    async loadNamespaces(tabId: string) {
      const s = this.sessions[tabId]
      if (!s) return
      try {
        s.namespaces = await client.namespaces(s.connId)
      } catch {
        s.namespaces = []
      }
    },
    async setNamespace(tabId: string, ns: string) {
      const s = this.sessions[tabId]
      if (!s) return
      s.namespace = ns
      await client.setNamespace(s.connId, ns)
      s.refreshing = false
      await this.refresh(tabId)
    },
    async createContainer(tabId: string, opts: Parameters<typeof client.create>[1]) {
      const s = this.sessions[tabId]
      if (!s) return
      await client.create(s.connId, opts)
      await this.refresh(tabId)
    },
    // Mirrors K8sTabContent.openTerminal: exec params go on the panel config so
    // Panel.vue / TabItem.vue can redial the stream on reconnect / duplicate.
    async openContainerExec(tab: ContainerTab, c: ContainerInfo, shell = 'sh') {
      const info = await client.execSession(tab.connectionId, c.id, shell)
      const cfg = {
        id: '', name: c.name, type: 'container-exec' as any, host: '', port: 0, user: '', authType: 'password' as any,
        containerExecConnId: tab.connectionId, containerExecContainerId: c.id, containerExecShell: shell,
      }
      const panelStore = usePanelStore()
      const tabStore = useTabStore()
      const sessionStore = useSessionStore()
      const panel = panelStore.createPanel(cfg as any, 'container-exec')
      panelStore.updateTitle(panel.id, c.name)
      panelStore.bindSession(panel.id, info.id)
      sessionStore.initSession(info.id)
      sessionStore.updateStatus(info.id, 'connected')
      const termTab = tabStore.createTerminalTab(panel.title, panel.id)
      panelStore.movePanelToTab(panel.id, termTab.id)
    },
    close(tabId: string) {
      const s = this.sessions[tabId]
      if (!s) return
      client.disconnect(s.connId)
      delete this.sessions[tabId]
    },
  },
})
