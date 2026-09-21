import { defineStore } from 'pinia'
import { ref } from 'vue'
import { GetFavoriteConnections, SaveFavoriteConnections } from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'

// Module-level un-subscriber for the cross-window store:favorites:changed listener.
// Tracked at module scope so re-imports under HMR can detach the previous
// listener before re-subscribing (same pattern as connectionStore, FE-03).
let unsubFavoritesChanged: (() => void) | null = null

// Ordered favorite connection ids, persisted in favorites.json (synced).
// Array order = display order; drag & drop rewrites the whole list.
export const useFavoriteStore = defineStore('favorite', () => {
  const favoriteIds = ref<string[]>([])
  const loaded = ref(false)

  async function load() {
    try {
      favoriteIds.value = (await GetFavoriteConnections()) || []
      loaded.value = true
    } catch (e) {
      console.error('Failed to load favorites:', e)
    }
  }

  async function persist() {
    try {
      await SaveFavoriteConnections([...favoriteIds.value])
    } catch (e) {
      console.error('Failed to save favorites:', e)
    }
  }

  function isFavorite(id: string): boolean {
    return favoriteIds.value.includes(id)
  }

  async function add(id: string) {
    if (!id || favoriteIds.value.includes(id)) return
    favoriteIds.value = [...favoriteIds.value, id]
    await persist()
  }

  async function remove(id: string) {
    if (!favoriteIds.value.includes(id)) return
    favoriteIds.value = favoriteIds.value.filter(x => x !== id)
    await persist()
  }

  async function toggle(id: string) {
    if (favoriteIds.value.includes(id)) {
      await remove(id)
    } else {
      await add(id)
    }
  }

  // Move the given ids (preserving their relative order) so they land right
  // before beforeId — or at the end of the list when beforeId is omitted.
  async function reorder(ids: string[], beforeId?: string) {
    const moveSet = new Set(ids)
    const moved = favoriteIds.value.filter(id => moveSet.has(id))
    if (moved.length === 0) return
    const rest = favoriteIds.value.filter(id => !moveSet.has(id))

    let insertAt = rest.length
    if (beforeId && !moveSet.has(beforeId)) {
      const idx = rest.indexOf(beforeId)
      if (idx >= 0) insertAt = idx
    }
    rest.splice(insertAt, 0, ...moved)
    favoriteIds.value = rest
    await persist()
  }

  // Listen for cross-window favorites sync.
  unsubFavoritesChanged?.()
  unsubFavoritesChanged = Events.On('store:favorites:changed', (ev) => {
    const data = ev.data as string[] | undefined
    if (Array.isArray(data)) {
      favoriteIds.value = data
    }
  })

  // Load once on first store use — favorites are needed by the sidebar and
  // the start page, and neither should block rendering on the roundtrip.
  load()

  function dispose() {
    unsubFavoritesChanged?.()
    unsubFavoritesChanged = null
  }

  return {
    favoriteIds,
    loaded,
    load,
    isFavorite,
    add,
    remove,
    toggle,
    reorder,
    dispose
  }
})
