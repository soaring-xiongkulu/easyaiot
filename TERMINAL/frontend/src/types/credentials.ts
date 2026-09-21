export interface DataDirInfo {
  dataDir: string
  type: 'default' | 'portable' | 'custom'
  firstRun: boolean
}

export interface CredentialStatus {
  mode: 'keychain' | 'master-password' | ''
  unlocked: boolean
  needsSetup: boolean
  keychainLost: boolean
  existingSecrets: number
}
