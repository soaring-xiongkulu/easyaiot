// Single source of truth for connection-type metadata: display label, icon,
// category and default port for every connection type. The new-connection
// form, the sidebar/start-page type filters, the per-type icons and the
// quick-connect protocol map all derive from this registry — adding a
// connection type means adding one entry here.
//
// Scope: registry entries are connection types (values of config.type) plus
// the runtime-only session/panel kinds (wsl-file, k8s-exec, container-exec)
// that share icon/label metadata but never persist as connections and have no
// new-connection form card. Pure UI tab kinds (workspace, settings, start)
// are not connection types and stay local to their consumers.
import type { Component } from 'vue'
import {
  Activity, AppWindow, ArrowLeftRight, Box, Boxes, Cable, Cloud, Database, DatabaseSearch,
  DatabaseZap, FileUp, FolderOpen, FolderUp, Folders, Globe, HardDrive, Laptop,
  LaptopMinimal, LayoutDashboard, Layers, Monitor, MonitorCloud, MonitorSmartphone,
  MoreHorizontal, Settings, ShipWheel, SquarePlus, SquareTerminal, Terminal, Zap,
} from '@lucide/vue'

export type ConnectionCategory = 'terminal' | 'filetransfer' | 'remote' | 'sql' | 'nosql' | 'container' | 'other'

export interface ConnectionTypeInfo {
  type: string
  dbType?: string           // SQL family discriminator on the 'database' type
  containerRuntime?: string // discriminator on the 'container' type
  // Static display label (type filters, badges).
  label: string
  // i18n key preferred over `label` where a localized name reads better
  // (new-connection form).
  labelKey?: string
  icon: Component
  // Filter category. formHidden runtime kinds carry one too so they group
  // with their family; they are excluded from form/filter projections.
  category: ConnectionCategory
  defaultPort?: number
  // Offered only on Windows (WSL, RDP, WSLC).
  windowsOnly?: boolean
  // i18n key for the connection's connect-X context-menu entry.
  connectMenuKey?: string
  // Type without a new-connection form card — either a real connection type
  // opened through context menus (monitor) or a runtime-only session kind
  // that is never persisted as a connection (wsl-file, k8s-exec,
  // container-exec). Icons and labels still resolve from the registry.
  formHidden?: boolean
}

export const CONNECTION_TYPES: ConnectionTypeInfo[] = [
  // Terminal
  { type: 'ssh', label: 'SSH', icon: SquareTerminal, category: 'terminal', defaultPort: 22, connectMenuKey: 'sidebar.connectSSH' },
  { type: 'telnet', label: 'Telnet', icon: Terminal, category: 'terminal', defaultPort: 23, connectMenuKey: 'sidebar.connectTelnet' },
  { type: 'mosh', label: 'Mosh', icon: Zap, category: 'terminal', defaultPort: 22, connectMenuKey: 'sidebar.connectMosh' },
  { type: 'local', label: 'Local', labelKey: 'conn.localTerminal', icon: Laptop, category: 'terminal', connectMenuKey: 'sidebar.connectLocal' },
  { type: 'wsl', label: 'WSL', icon: LaptopMinimal, category: 'terminal', windowsOnly: true, connectMenuKey: 'sidebar.connectWsl' },
  { type: 'serial', label: 'Serial', labelKey: 'serial.title', icon: Cable, category: 'terminal', connectMenuKey: 'sidebar.connectSerial' },
  { type: 'tcp', label: 'TCP', icon: ArrowLeftRight, category: 'terminal', defaultPort: 23, connectMenuKey: 'sidebar.connectTcp' },
  // Runtime exec panels inside workspace terminals — never persisted
  { type: 'k8s-exec', label: 'Kubernetes Exec', icon: Box, category: 'terminal', formHidden: true },
  { type: 'container-exec', label: 'Container Exec', icon: Box, category: 'terminal', formHidden: true },
  // File transfer
  { type: 'sftp', label: 'SFTP', icon: Folders, category: 'filetransfer', defaultPort: 22, connectMenuKey: 'sidebar.connectSftp' },
  { type: 'scp', label: 'SCP', icon: FileUp, category: 'filetransfer', defaultPort: 22, connectMenuKey: 'sidebar.connectScp' },
  { type: 'ftp', label: 'FTP', icon: FolderUp, category: 'filetransfer', defaultPort: 21, connectMenuKey: 'sidebar.connectFtp' },
  { type: 'smb', label: 'SMB', icon: HardDrive, category: 'filetransfer', defaultPort: 445, connectMenuKey: 'sidebar.connectSmb' },
  { type: 's3', label: 'S3', icon: Cloud, category: 'filetransfer', connectMenuKey: 'sidebar.connectS3' },
  { type: 'webdav', label: 'WebDAV', icon: Globe, category: 'filetransfer', connectMenuKey: 'sidebar.connectWebdav' },
  // WSL file browser — a runtime variant of the wsl terminal, never persisted
  { type: 'wsl-file', label: 'WSL Files', icon: FolderOpen, category: 'filetransfer', formHidden: true },
  // Remote desktop
  { type: 'rdp', label: 'RDP', icon: Monitor, category: 'remote', defaultPort: 3389, windowsOnly: true, connectMenuKey: 'sidebar.connectRDP' },
  { type: 'vnc', label: 'VNC', icon: MonitorSmartphone, category: 'remote', defaultPort: 5900, connectMenuKey: 'sidebar.connectVNC' },
  { type: 'spice', label: 'SPICE', icon: MonitorCloud, category: 'remote', defaultPort: 5900, connectMenuKey: 'sidebar.connectSPICE' },
  { type: 'x11-desktop', label: 'X11 Desktop', icon: AppWindow, category: 'remote', defaultPort: 22, connectMenuKey: 'sidebar.connectX11Desktop' },
  // SQL family: shared 'database' type with a dbType discriminator
  { type: 'database', dbType: 'mysql', label: 'MySQL', icon: Database, category: 'sql', defaultPort: 3306, connectMenuKey: 'db.connectDB' },
  { type: 'database', dbType: 'postgres', label: 'PostgreSQL', icon: Database, category: 'sql', defaultPort: 5432, connectMenuKey: 'db.connectDB' },
  { type: 'database', dbType: 'oracle', label: 'Oracle', icon: Database, category: 'sql', defaultPort: 1521, connectMenuKey: 'db.connectDB' },
  { type: 'database', dbType: 'sqlserver', label: 'SQL Server', icon: Database, category: 'sql', defaultPort: 1433, connectMenuKey: 'db.connectDB' },
  { type: 'database', dbType: 'rqlite', label: 'rqlite', icon: Database, category: 'sql', defaultPort: 4001, connectMenuKey: 'db.connectDB' },
  // NoSQL: standalone connection types
  { type: 'redis', label: 'Redis', icon: DatabaseZap, category: 'nosql', defaultPort: 6379, connectMenuKey: 'sidebar.connectRedis' },
  { type: 'mongodb', label: 'MongoDB', icon: Layers, category: 'nosql', defaultPort: 27017, connectMenuKey: 'sidebar.connectMongodb' },
  { type: 'elasticsearch', label: 'Elasticsearch', icon: DatabaseSearch, category: 'nosql', defaultPort: 9200, connectMenuKey: 'sidebar.connectElasticsearch' },
  // Containers
  { type: 'k8s', label: 'Kubernetes', icon: ShipWheel, category: 'container', connectMenuKey: 'sidebar.connectK8s' },
  { type: 'container', containerRuntime: 'docker', label: 'Docker', icon: Boxes, category: 'container', connectMenuKey: 'sidebar.connectContainer' },
  { type: 'container', containerRuntime: 'podman', label: 'Podman', icon: Boxes, category: 'container', connectMenuKey: 'sidebar.connectContainer' },
  { type: 'container', containerRuntime: 'nerdctl', label: 'nerdctl', icon: Boxes, category: 'container', connectMenuKey: 'sidebar.connectContainer' },
  { type: 'container', containerRuntime: 'wslc', label: 'WSLC', icon: Boxes, category: 'container', windowsOnly: true, connectMenuKey: 'sidebar.connectContainer' },
  // Registry-only: monitor connections are opened from the SSH context menu,
  // not created in the form, and carry no default port.
  { type: 'monitor', label: 'Monitor', icon: Activity, category: 'other', connectMenuKey: 'sidebar.connectMonitor', formHidden: true },
  // Pure UI tab kinds — no connection session behind them, icon/label only.
  { type: 'workspace', label: 'Workspace', icon: LayoutDashboard, category: 'other', formHidden: true },
  { type: 'settings', label: 'Settings', icon: Settings, category: 'other', formHidden: true },
  { type: 'start', label: 'Start', icon: SquarePlus, category: 'other', formHidden: true },
]

export const CATEGORY_ORDER: ConnectionCategory[] = ['terminal', 'filetransfer', 'remote', 'sql', 'nosql', 'container']

// Category titles + icons, used by the new-connection form sidebar and the
// two-level type filter menus.
export const CATEGORY_META: Record<ConnectionCategory, { labelKey: string; icon: Component }> = {
  terminal: { labelKey: 'conn.categoryTerminal', icon: SquareTerminal },
  filetransfer: { labelKey: 'conn.categoryFileTransfer', icon: FolderUp },
  remote: { labelKey: 'conn.categoryRemote', icon: Monitor },
  sql: { labelKey: 'db.categorySQL', icon: Database },
  nosql: { labelKey: 'db.categoryNoSQL', icon: DatabaseZap },
  container: { labelKey: 'conn.categoryContainer', icon: Boxes },
  other: { labelKey: 'conn.categoryOther', icon: MoreHorizontal },
}

// Filter key for an entry: plain type, or `database:<dbType>` /
// `container:<runtime>` for discriminated subtypes — the same shape the type
// filters store in settings.
export function typeFilterKey(info: ConnectionTypeInfo): string {
  if (info.dbType) return `${info.type}:${info.dbType}`
  if (info.containerRuntime) return `${info.type}:${info.containerRuntime}`
  return info.type
}

export function connectionTypeInfo(type: string): ConnectionTypeInfo | undefined {
  return CONNECTION_TYPES.find(t => t.type === type)
}

// Icon for a config/panel-like object. Discriminated subtypes of a base type
// share the same icon, so a type-level lookup is enough.
export function connectionTypeIcon(config: { type?: string } | null | undefined): Component | undefined {
  return connectionTypeInfo(config?.type ?? '')?.icon
}

// Icon for a bare type/kind string (tab.type, panel.type).
export function connectionTypeIconOfKind(type: string | null | undefined): Component | undefined {
  return connectionTypeInfo(type ?? '')?.icon
}

// Label for a filter key ('database:mysql', 'container:docker', 'redis', ...).
// Returns undefined when the key is unknown so callers can fall back.
export function connectionTypeLabel(key: string): string | undefined {
  return CONNECTION_TYPES.find(t => typeFilterKey(t) === key)?.label
}

// Label the new-connection form displays for an entry (localized when available).
export function connectionTypeFormLabel(info: ConnectionTypeInfo, t: (key: string) => string): string {
  return info.labelKey ? t(info.labelKey) : info.label
}

export const SQL_DB_TYPES = CONNECTION_TYPES
  .filter(t => t.type === 'database' && t.dbType)
  .map(t => t.dbType!)

export function isSqlDbType(dbType?: string): boolean {
  return !!dbType && SQL_DB_TYPES.includes(dbType)
}

export function defaultPortFor(type: string, dbType?: string): number | undefined {
  const info = dbType
    ? CONNECTION_TYPES.find(t => t.type === type && t.dbType === dbType)
    : CONNECTION_TYPES.find(t => t.type === type)
  return info?.defaultPort
}
