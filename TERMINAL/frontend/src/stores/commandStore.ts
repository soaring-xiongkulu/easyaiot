import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ListCommands, GetCommandBody, SetCommandEnabled, SetCommandLocked, DeleteCommand, CreateCommand, SaveCommand, OpenPathInExplorer } from '../../bindings/easyaiot/terminal/app'
import type { CommandMeta } from '../types/command'

export const useCommandStore = defineStore('commands', () => {
  const commands = ref<CommandMeta[]>([])
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    try {
      commands.value = await ListCommands() || []
    } catch (e) {
      console.error('Failed to load commands:', e)
      commands.value = []
    }
    loaded.value = true
  }

  function reload() {
    loaded.value = false
    return load()
  }

  const enabledCommands = computed(() => commands.value.filter(c => c.enabled))

  async function toggleEnabled(name: string) {
    const c = commands.value.find(x => x.name === name)
    if (!c) return
    c.enabled = !c.enabled
    try {
      await SetCommandEnabled(name, c.enabled)
    } catch (e) {
      console.error('Failed to toggle command enabled:', e)
    }
  }

  async function toggleLocked(name: string) {
    const c = commands.value.find(x => x.name === name)
    if (!c) return
    c.locked = !c.locked
    try {
      await SetCommandLocked(name, c.locked)
    } catch (e) {
      console.error('Failed to toggle command lock:', e)
    }
  }

  async function remove(name: string) {
    const c = commands.value.find(x => x.name === name)
    if (!c || c.locked) return
    try {
      await DeleteCommand(name)
      commands.value = commands.value.filter(x => x.name !== name)
    } catch (e) {
      console.error('Failed to delete command:', e)
    }
  }

  async function create(name: string, description: string, body: string, argumentHint = '') {
    try {
      await CreateCommand(name, description, argumentHint, body)
      await reload()
    } catch (e) {
      console.error('Failed to create command:', e)
      throw e
    }
  }

  async function save(name: string, description: string, body: string, argumentHint = '') {
    try {
      await SaveCommand(name, description, argumentHint, body)
      await reload()
    } catch (e) {
      console.error('Failed to save command:', e)
      throw e
    }
  }

  async function getBody(name: string): Promise<string> {
    try {
      return await GetCommandBody(name)
    } catch (e) {
      console.error('Failed to get command body:', e)
      return ''
    }
  }

  async function openFolder(path: string): Promise<void> {
    if (!path) return
    try {
      await OpenPathInExplorer(path)
    } catch (e) {
      console.error('Failed to open command folder:', e)
    }
  }

  return {
    commands, loaded, enabledCommands,
    load, reload,
    toggleEnabled, toggleLocked, remove, create, save, getBody, openFolder,
  }
})
