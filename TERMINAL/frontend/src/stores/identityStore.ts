import { defineStore } from 'pinia'
import { ref } from 'vue'
import { LoadIdentities, SaveIdentities } from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import type { Identity, IdentityStoreData } from '../types/identity'

// Module-level un-subscriber for the cross-window store:identities:changed listener.
let unsubIdentitiesChanged: (() => void) | null = null

export const useIdentityStore = defineStore('identity', () => {
  const identities = ref<Identity[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const data = (await LoadIdentities()) as IdentityStoreData
      identities.value = data.identities ?? []
    } catch (e) {
      console.error('Failed to load identities:', e)
    } finally {
      loading.value = false
    }
  }

  async function save() {
    await SaveIdentities({ identities: identities.value } as any)
  }

  // Reload from disk when the backend pushes updated identity data (e.g. after
  // a cloud sync pull), so the keychain isn't stale until restart.
  unsubIdentitiesChanged?.()
  unsubIdentitiesChanged =Events.On('store:identities:changed', (ev) => { const data: IdentityStoreData = ev.data; 
    if (data?.identities) identities.value = data.identities
   })

  function dispose() {
    unsubIdentitiesChanged?.()
    unsubIdentitiesChanged = null
  }

  async function add(id: Identity) {
    identities.value.push(id)
    await save()
  }

  async function update(id: Identity) {
    const i = identities.value.findIndex((x) => x.id === id.id)
    if (i >= 0) identities.value[i] = id
    await save()
  }

  async function remove(id: string) {
    identities.value = identities.value.filter((x) => x.id !== id)
    await save()
  }

  return { identities, loading, load, save, add, update, remove, dispose }
})
