// Save / open named workspaces. A saved workspace is a `type: "workspace"`
// ConnectionConfig living in the connection tree (see
// docs/superpowers/specs/2026-09-21-workspace-overhaul-design.md):
// members hold only connectionId references — host credentials re-resolve at
// connect time, so no secret is ever persisted here.
import { ElMessageBox } from 'element-plus'
import { t } from '../i18n'
import { msg } from '../services/message'
import { useConnectionStore } from '../stores/connectionStore'
import { usePanelStore } from '../stores/panelStore'
import { useTabStore } from '../stores/tabStore'
import type { ConnectionConfig, MemberConnectStatus, SavedWorkspaceLayoutNode, SavedWorkspaceMember } from '../types/session'
import type { LayoutNode, PanelLayout, WorkspaceTab } from '../types/workspace'

export type { MemberConnectStatus } from '../types/session'

export interface OpenWorkspaceDeps {
  // Connect one member host (or synthesized local/wsl config) into the given
  // workspace tab. Returns the created panel id on success.
  connectMember(config: ConnectionConfig, workspaceTabId: string, persist: boolean): Promise<{ status: MemberConnectStatus; panelId?: string }>
}

// ── Save ──

// Map a runtime layout to the saved-layout shape. Leaves whose panel is not
// in the member map (skipped transient panels) become empty leaves; the caller
// prunes the result.
function toSavedLayout(node: LayoutNode, memberByPanel: Map<string, string>): SavedWorkspaceLayoutNode {
  if (node.type === 'leaf') {
    return { type: 'leaf', memberId: memberByPanel.get(node.panelId) ?? '' }
  }
  return {
    type: 'split',
    direction: node.direction,
    children: node.children.map(c => toSavedLayout(c, memberByPanel)),
    sizes: [...node.sizes]
  }
}

function pruneEmpty(node: SavedWorkspaceLayoutNode): SavedWorkspaceLayoutNode {
  if (node.type === 'leaf') return node
  const children = (node.children ?? []).map(pruneEmpty).filter(c => c.type === 'leaf' ? !!c.memberId : true)
  if (children.length === 0) return { type: 'leaf', memberId: '' }
  if (children.length === 1) return children[0]
  return {
    type: 'split',
    direction: node.direction,
    children,
    sizes: node.sizes && node.sizes.length === children.length ? node.sizes : children.map(() => 1 / children.length)
  }
}

function collectSavedLeafIds(node: SavedWorkspaceLayoutNode): string[] {
  if (node.type === 'leaf') return node.memberId ? [node.memberId] : []
  return (node.children ?? []).flatMap(collectSavedLeafIds)
}

// Save a live workspace tab as / into a `type: "workspace"` connection.
// Always prompts for the name (pre-filled): same name → overwrite in place,
// new name → 另存为 a new record and re-link the tab to it.
// Returns the connection id of the record, or null when cancelled/empty.
export async function saveWorkspaceToConnections(tab: WorkspaceTab): Promise<string | null> {
  const panelStore = usePanelStore()
  const connectionStore = useConnectionStore()
  const tabStore = useTabStore()

  // Collect members in visual order. Saved hosts persist by connectionId;
  // local/wsl persist by type+shellPath (self-contained); anything else is
  // transient and skipped.
  const members: SavedWorkspaceMember[] = []
  const memberByPanel = new Map<string, string>()
  const skipped: string[] = []
  for (const panelId of tab.panelIds) {
    const p = panelStore.getPanel(panelId)
    if (!p) continue
    const connId = p.config?.id || ''
    const selfContained = p.type === 'local' || p.type === 'wsl'
    if (!connId && !selfContained) {
      skipped.push(p.title)
      continue
    }
    members.push({
      id: panelId,
      connectionId: connId,
      type: p.type,
      title: p.title,
      shellPath: p.config?.shellPath || ''
    })
    memberByPanel.set(panelId, panelId)
  }
  if (members.length === 0) {
    msg.warning(t('workspace.saveEmpty'))
    return null
  }

  const layout = pruneEmpty(toSavedLayout(tab.layout.root, memberByPanel))
  // Safety net: a layout that pruned to nothing means every member was
  // skipped — nothing meaningful to persist.
  if (collectSavedLeafIds(layout).length === 0) {
    msg.warning(t('workspace.saveEmpty'))
    return null
  }

  const existing = tab.savedWorkspaceId
    ? connectionStore.connections.find(c => c.id === tab.savedWorkspaceId)
    : undefined

  let name = tab.name
  try {
    const { value } = await ElMessageBox.prompt(
      t('workspace.savePromptTitle'),
      t('workspace.save'),
      {
        inputValue: existing?.name || tab.name,
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel')
      }
    )
    name = value?.trim() || tab.name
  } catch {
    return null
  }

  if (existing && name === existing.name) {
    // Overwrite in place (members + layout).
    await connectionStore.update(existing.id, {
      name,
      workspaceMembers: members,
      workspaceLayout: layout
    })
    msg.success(t('workspace.saved'))
    return existing.id
  }

  // First save, or 另存为 under a new name: create a new record and re-link.
  const record: ConnectionConfig = {
    id: '',
    name,
    type: 'workspace',
    host: '',
    port: 0,
    user: '',
    authType: 'password',
    workspaceMembers: members,
    workspaceLayout: layout
  }
  await connectionStore.add(record)
  tabStore.setWorkspaceSavedId(tab.id, record.id)
  // 另存为 under a new name: the live tab follows the new record's name.
  if (name !== tab.name) tabStore.renameTab(tab.id, name)
  msg.success(t('workspace.saved'))
  return record.id
}

// ── Open ──

// Rebuild a runtime LayoutNode from the saved shape, mapping member ids to
// the freshly created panel ids. Members that never landed become empty
// leaves (applyWorkspaceLayout prunes them).
function toRuntimeLayout(node: SavedWorkspaceLayoutNode, panelByMember: Map<string, string>): LayoutNode {
  if (node.type === 'leaf') {
    const panelId = node.memberId ? panelByMember.get(node.memberId) : undefined
    return { type: 'leaf', panelId: panelId ?? '' }
  }
  const children = (node.children ?? [])
    .map(c => toRuntimeLayout(c, panelByMember))
    .filter(c => c.type === 'leaf' ? !!c.panelId : true)
  if (children.length === 0) return { type: 'leaf', panelId: '' }
  if (children.length === 1) return children[0]
  return {
    type: 'split',
    direction: node.direction === 'vertical' ? 'vertical' : 'horizontal',
    children,
    sizes: node.sizes && node.sizes.length === children.length ? node.sizes : children.map(() => 1 / children.length)
  }
}

// Open a saved workspace connection: create a live workspace tab and connect
// the members in order (sequential awaits — credential prompts must not
// interleave). Returns the workspace tab id, or null when nothing could be
// opened.
export async function openSavedWorkspace(conn: ConnectionConfig, deps: OpenWorkspaceDeps): Promise<string | null> {
  const tabStore = useTabStore()
  const connectionStore = useConnectionStore()

  const members = conn.workspaceMembers || []
  if (members.length === 0) {
    msg.warning(t('workspace.openEmpty'))
    return null
  }

  const ws = tabStore.createWorkspaceTab(conn.name, [], { root: { type: 'leaf', panelId: '' } })
  tabStore.setWorkspaceSavedId(ws.id, conn.id)

  const panelByMember = new Map<string, string>()
  const skipped: string[] = []
  let cancelled = false

  for (const m of members) {
    if (!m.connectionId) {
      // Self-contained member (local/wsl): recreate from type + shellPath.
      const cfg: ConnectionConfig = {
        id: '',
        name: m.title,
        type: m.type as ConnectionConfig['type'],
        host: '',
        port: 0,
        user: '',
        authType: 'password',
        shellPath: m.shellPath
      }
      const res = await deps.connectMember(cfg, ws.id, false)
      if (res.panelId) panelByMember.set(m.id, res.panelId)
      else skipped.push(m.title)
      continue
    }

    const host = connectionStore.connections.find(c => c.id === m.connectionId)
    if (!host) {
      skipped.push(m.title)
      continue
    }
    const res = await deps.connectMember(host, ws.id, true)
    if (res.panelId) {
      panelByMember.set(m.id, res.panelId)
    } else if (res.status === 'cancelled') {
      // User aborted the credential prompt: keep what already landed, stop
      // prompting for the rest.
      skipped.push(m.title)
      cancelled = true
      break
    } else {
      skipped.push(m.title)
    }
  }

  if (panelByMember.size === 0) {
    tabStore.closeTab(ws.id)
    msg.error(t('workspace.openEmpty'))
    return null
  }

  // Remap the saved layout onto the live panels (missing members pruned).
  const savedLayout = conn.workspaceLayout
    ? pruneEmpty(conn.workspaceLayout)
    : null
  if (savedLayout && collectSavedLeafIds(savedLayout).length > 0) {
    const runtime: PanelLayout = { root: toRuntimeLayout(savedLayout, panelByMember) }
    tabStore.applyWorkspaceLayout(ws.id, runtime)
  } else {
    // No usable saved layout: fall back to a balanced grid.
    tabStore.applyWorkspaceLayout(ws.id, tabStore.buildGridLayout([...panelByMember.values()]))
  }
  tabStore.setActivePanel(ws.id, ws.panelIds[0])

  if (cancelled) msg.info(t('workspace.openCancelled', { count: skipped.length }))
  else if (skipped.length > 0) msg.warning(t('workspace.openSkipped', { count: skipped.length }))
  return ws.id
}
