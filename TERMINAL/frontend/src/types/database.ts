export interface TableInfo {
  name: string
  type?: string  // "table" or "view"
  comment?: string
}

export interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
  defaultVal: string
  defaultType: string  // "none" | "null" | "value" | "auto"
  isPrimary: boolean
  comment: string
  collation: string
  onUpdate: boolean
}

export interface IndexInfo {
  name: string
  columns: string[]
  unique: boolean
  isPrimary: boolean
}

export interface SchemaResult {
  columns: ColumnInfo[]
  indexes: IndexInfo[]
}

export interface QueryResultColumn {
  name: string
  type: string
}

export interface QueryResult {
  columns: QueryResultColumn[]
  rows: Record<string, any>[]
}

export interface ExecResult {
  affected: number
  lastInsertId: number
}

export interface HistoryEntry {
  id: string
  sql: string
  executedAt: string
  durationMs: number
  error?: string
  rowCount?: number
}

export interface ColumnDef {
  name: string
  type: string
  nullable: boolean
  defaultVal: string
  defaultType: string  // "none" | "null" | "value" | "auto"
  comment: string
  collation: string
  onUpdate: boolean
}

export interface IndexDef {
  name: string
  columns: string[]
  unique: boolean
  isPrimary: boolean
}
