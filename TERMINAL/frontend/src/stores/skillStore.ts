import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ListSkills, GetSkillBody, SetSkillEnabled, SetSkillLocked, DeleteSkill, CreateSkill, SaveSkill, OpenPathInExplorer } from '../../bindings/easyaiot/terminal/app'
import type { SkillMeta } from '../types/skill'

export const useSkillStore = defineStore('skills', () => {
  const skills = ref<SkillMeta[]>([])
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    try {
      skills.value = await ListSkills() || []
    } catch (e) {
      console.error('Failed to load skills:', e)
      skills.value = []
    }
    loaded.value = true
  }

  function reload() {
    loaded.value = false
    return load()
  }

  const enabledSkills = computed(() => skills.value.filter(s => s.enabled))

  async function toggleEnabled(name: string) {
    const s = skills.value.find(x => x.name === name)
    if (!s) return
    s.enabled = !s.enabled
    try {
      await SetSkillEnabled(name, s.enabled)
    } catch (e) {
      console.error('Failed to toggle skill enabled:', e)
    }
  }

  async function toggleLocked(name: string) {
    const s = skills.value.find(x => x.name === name)
    if (!s) return
    s.locked = !s.locked
    try {
      await SetSkillLocked(name, s.locked)
    } catch (e) {
      console.error('Failed to toggle skill lock:', e)
    }
  }

  async function remove(name: string) {
    const s = skills.value.find(x => x.name === name)
    if (!s) return
    if (s.locked) {
      return
    }
    try {
      await DeleteSkill(name)
      skills.value = skills.value.filter(x => x.name !== name)
    } catch (e) {
      console.error('Failed to delete skill:', e)
    }
  }

  async function create(name: string, description: string, body: string) {
    try {
      await CreateSkill(name, description, body)
      await reload()
    } catch (e) {
      console.error('Failed to create skill:', e)
      throw e
    }
  }

  async function save(name: string, description: string, body: string) {
    try {
      await SaveSkill(name, description, body)
      await reload()
    } catch (e) {
      console.error('Failed to save skill:', e)
      throw e
    }
  }

  // AI 侧保存：已存在则覆写（后端拒绝 locked），不存在则新建。
  async function saveByAgent(name: string, description: string, body: string) {
    await load()
    const exists = skills.value.some(s => s.name === name)
    if (exists) {
      await SaveSkill(name, description, body)
    } else {
      await CreateSkill(name, description, body)
    }
    await reload()
  }

  async function getBody(name: string): Promise<string> {
    try {
      return await GetSkillBody(name)
    } catch (e) {
      console.error('Failed to get skill body:', e)
      return ''
    }
  }

  async function openFolder(path: string): Promise<void> {
    if (!path) return
    try {
      await OpenPathInExplorer(path)
    } catch (e) {
      console.error('Failed to open skill folder:', e)
    }
  }

  return {
    skills, loaded, enabledSkills,
    load, reload,
    toggleEnabled, toggleLocked, remove, create, save, saveByAgent, getBody, openFolder,
  }
})