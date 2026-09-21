import { defineStore } from 'pinia'
import { ref } from 'vue'
import { LoadProxies, SaveProxies } from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import type { Proxy, ProxyStoreData } from '../types/proxy'

// Module-level un-subscriber for the cross-window store:proxies:changed listener.
let unsubProxiesChanged: (() => void) | null = null

export const useProxyStore = defineStore('proxy', () => {
  const proxies = ref<Proxy[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const data = (await LoadProxies()) as ProxyStoreData
      proxies.value = data.proxies ?? []
    } catch (e) {
      console.error('Failed to load proxies:', e)
    } finally {
      loading.value = false
    }
  }

  async function save() {
    await SaveProxies({ proxies: proxies.value } as any)
  }

  // Reload from disk when the backend pushes updated proxy data (e.g. after a
  // cloud sync pull), so the list isn't stale until restart.
  unsubProxiesChanged?.()
  unsubProxiesChanged =Events.On('store:proxies:changed', (ev) => { const data: ProxyStoreData = ev.data; 
    if (data?.proxies) proxies.value = data.proxies
   })

  function dispose() {
    unsubProxiesChanged?.()
    unsubProxiesChanged = null
  }

  async function add(p: Proxy) {
    proxies.value.push(p)
    await save()
  }

  async function update(p: Proxy) {
    const i = proxies.value.findIndex((x) => x.id === p.id)
    if (i >= 0) proxies.value[i] = p
    await save()
  }

  async function remove(id: string) {
    proxies.value = proxies.value.filter((x) => x.id !== id)
    await save()
  }

  return { proxies, loading, load, save, add, update, remove, dispose }
})
