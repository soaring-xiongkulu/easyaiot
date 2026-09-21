import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AIModelConfig } from '../types/settings'
import { DEFAULT_SETTINGS } from '../types/settings'
import { LoadAIModels, SaveAIModels } from '../../bindings/easyaiot/terminal/app'

// aiConfigStore backs ai.json — the syncable slice of the AI settings
// (model catalog + agent turn limit). settingsStore composes this into
// settings.ai alongside the device-local activeModelId.
export const useAIConfigStore = defineStore('aiConfig', () => {
  const maxTurns = ref<number>(DEFAULT_SETTINGS.ai.maxTurns)
  const models = ref<AIModelConfig[]>([...DEFAULT_SETTINGS.ai.models])
  const loaded = ref(false)

  async function load() {
    try {
      const cfg = await LoadAIModels()
      if (cfg) {
        maxTurns.value = cfg.maxTurns ?? DEFAULT_SETTINGS.ai.maxTurns
        models.value = cfg.models?.length ? cfg.models : [...DEFAULT_SETTINGS.ai.models]
      }
    } catch {
      // keep defaults
    } finally {
      loaded.value = true
    }
  }

  async function save() {
    try {
      await SaveAIModels({ maxTurns: maxTurns.value, models: models.value })
    } catch {
      // ignore save errors
    }
  }

  return { maxTurns, models, loaded, load, save }
})
