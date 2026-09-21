export interface ScanResult {
    keys: RedisKeyInfo[]
    cursor: number
    scanCount: number
}

export interface RedisKeyInfo {
    name: string
    type: 'string' | 'hash' | 'list' | 'set' | 'zset'
    ttl: number
}

// Tree node for the namespace view, shared by RedisTabContent (builds the
// tree) and RedisKeyTreeItem (renders one row + recurses). Empty children =
// a leaf key; otherwise a folder aggregating namespaces.
export interface KeyNode {
    id: string          // full path from root, e.g. "app:cache"
    label: string       // last segment
    count: number       // leaf keys under this node (recursive)
    children: KeyNode[] // empty array = leaf key
    keyName?: string    // leaf only: full redis key
    keyType?: RedisKeyInfo['type']  // leaf only
}

export interface FieldEntry {
    field: string
    value: string
}

export interface ScoredMember {
    score: number
    member: string
}
