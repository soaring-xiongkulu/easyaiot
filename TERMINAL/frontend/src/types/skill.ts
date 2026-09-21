export interface SkillMeta {
  name: string
  description: string
  isSystem: boolean
  origin: 'created' | 'imported'
  locked: boolean
  enabled: boolean
  sortOrder: number
  dir: string
  path: string
  hasReferences: boolean
  scriptCount: number
  modelInvocable: boolean
  createdModel: string
  createdAt: string
  version: number
}