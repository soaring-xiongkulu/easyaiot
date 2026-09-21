import { defineStore } from 'pinia'
import { ref } from 'vue'
import { SaveQuickCommands, LoadQuickCommands } from '../../bindings/easyaiot/terminal/app'

export interface QuickCommand {
  id: string
  name?: string
  remark?: string
  command: string
  groupId?: string
  sortOrder: number
}

export interface QuickCommandGroup {
  id: string
  name: string
  sortOrder: number
}

export interface QuickCommandData {
  version: number
  groups: QuickCommandGroup[]
  commands: QuickCommand[]
}

let idCounter = 0
function genId(prefix: string): string {
  return `${prefix}-${Date.now()}-${++idCounter}`
}

// Expand/collapse bookkeeping for the quick-commands panel, kept pure so it
// can be unit-tested. Mirrors the connections sidebar: only collapsed group
// ids are persisted, so new/unknown groups default to expanded.
export function expandedFromCollapsed(allIds: string[], collapsedIds: string[]): Set<string> {
  const collapsed = new Set(collapsedIds)
  return new Set(allIds.filter(id => !collapsed.has(id)))
}

export function collapsedFromExpanded(allIds: string[], expanded: Set<string>): string[] {
  return allIds.filter(id => !expanded.has(id))
}

export const useQuickCommandStore = defineStore('quickCommands', () => {
  const groups = ref<QuickCommandGroup[]>([])
  const commands = ref<QuickCommand[]>([])
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    try {
      const data: QuickCommandData = await LoadQuickCommands()
      groups.value = data.groups || []
      commands.value = data.commands || []
    } catch (e) {
      console.error('Failed to load quick commands:', e)
      groups.value = []
      commands.value = []
    }
    loaded.value = true
  }

  async function save() {
    try {
      await SaveQuickCommands({
        version: 1,
        groups: JSON.parse(JSON.stringify(groups.value)),
        commands: JSON.parse(JSON.stringify(commands.value)),
      })
    } catch (e) {
      console.error('Failed to save quick commands:', e)
    }
  }

  function addGroup(name: string): QuickCommandGroup {
    const group: QuickCommandGroup = {
      id: genId('qcg'),
      name,
      sortOrder: groups.value.length,
    }
    groups.value.push(group)
    save()
    return group
  }

  function renameGroup(id: string, name: string) {
    const g = groups.value.find(x => x.id === id)
    if (g) { g.name = name; save() }
  }

  function deleteGroup(id: string, deleteCommands: boolean) {
    if (deleteCommands) {
      commands.value = commands.value.filter(c => c.groupId !== id)
    } else {
      commands.value.forEach(c => { if (c.groupId === id) c.groupId = undefined })
    }
    groups.value = groups.value.filter(g => g.id !== id)
    save()
  }

  function addCommand(name: string | undefined, command: string, groupId?: string, remark?: string): QuickCommand {
    const cmd: QuickCommand = {
      id: genId('qcc'),
      name: name || undefined,
      remark: remark || undefined,
      command,
      groupId,
      sortOrder: commands.value.filter(c => c.groupId === groupId).length,
    }
    commands.value.push(cmd)
    save()
    return cmd
  }

  function updateCommand(id: string, name: string | undefined, command: string, groupId?: string, remark?: string) {
    const c = commands.value.find(x => x.id === id)
    if (c) {
      c.name = name || undefined
      c.command = command
      c.groupId = groupId
      if (remark !== undefined) c.remark = remark || undefined
      save()
    }
  }

  function deleteCommand(id: string) {
    commands.value = commands.value.filter(c => c.id !== id)
    save()
  }

  function getCommandsByGroup(groupId?: string): QuickCommand[] {
    return commands.value
      .filter(c => (c.groupId || undefined) === (groupId || undefined))
      .sort((a, b) => a.sortOrder - b.sortOrder)
  }

  return {
    groups, commands, loaded,
    load, save,
    addGroup, renameGroup, deleteGroup,
    addCommand, updateCommand, deleteCommand,
    getCommandsByGroup,
  }
})
