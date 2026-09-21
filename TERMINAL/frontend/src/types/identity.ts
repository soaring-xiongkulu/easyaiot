export interface Identity {
  id: string
  name: string
  username: string
  authType: 'password' | 'key' | 'keyText'
  password?: string
  keyPath?: string
  keyContent?: string // inline private-key text (authType === 'keyText')
}

export interface IdentityStoreData {
  identities: Identity[]
}
