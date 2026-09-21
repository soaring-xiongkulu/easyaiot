export interface MongoIndexInfo {
  name: string
  keys: string[]
  type: string
  unique: boolean
}

export interface MongoQueryResult {
  documents: string[]
  total: number
  skip: number
  limit: number
}
