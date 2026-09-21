// Point-and-click workspace creation shared by the 新建工作区 dialog and the
// sidebar「在工作区打开 → 新建工作区」entry. Open sessions are reused (their
// tab folds into the workspace); saved hosts connect fresh through the normal
// flow with sequential credential prompts.
import { t } from '../i18n'
import { msg } from '../services/message'
import { useTabStore } from '../stores/tabStore'
import type { TerminalTab, WorkspaceTab } from '../types/workspace'
import type { ConnectionConfig } from '../types/session'
import type { MemberConnectStatus } from './savedWorkspace'

export interface CreateWorkspaceDeps {
  connectMember(config: ConnectionConfig, workspaceTabId: string, persist: boolean): Promise<{ status: MemberConnectStatus; panelId?: string }>
}

// Terminal connection types that make sense as workspace members.
const WORKSPACE_HOST_TYPES = new Set(['ssh', 'telnet', 'mosh', 'serial', 'tcp', 'local', 'wsl'])

export function isWorkspaceHostType(type: string | undefined): boolean {
  return !!type && WORKSPACE_HOST_TYPES.has(type)
}

// Build a workspace from the selection and return its tab id, or null when
// nothing landed (e.g. the user cancelled the credential prompt before any
// member connected).
export async function createWorkspaceFromSelection(
  name: string,
  openTabIds: string[],
  hostConfigs: ConnectionConfig[],
  deps: CreateWorkspaceDeps
): Promise<WorkspaceTab | null> {
  const tabStore = useTabStore()

  const hosts = hostConfigs.filter(c => isWorkspaceHostType(c.type))
  const skippedHosts = hostConfigs.length - hosts.length
  const openTabs = openTabIds
    .map(id => tabStore.tabs.find(x => x.id === id && x.type === 'terminal') as TerminalTab | undefined)
    .filter((x): x is TerminalTab => !!x)

  if (hosts.length === 0 && openTabs.length === 0) return null

  const ws = tabStore.createWorkspaceTab(name || tabStore.generateWorkspaceName(tabStore.tabs), [], {
    root: { type: 'leaf', panelId: '' }
  })

  // 1. Fold the selected open terminal tabs in (sessions reused, not
  //    duplicated). addPanelToWorkspaceTab handles the empty shell.
  for (const termTab of openTabs) {
    tabStore.addPanelToWorkspaceTab(termTab.id, ws.id, ws.activePanelId || '', 'horizontal', false)
  }

  // 2. Connect saved hosts one by one (sequential awaits keep the credential
  //    prompts serial). A cancelled prompt keeps what already landed and
  //    stops prompting.
  let cancelled = false
  for (const host of hosts) {
    const res = await deps.connectMember(host, ws.id, true)
    if (res.status === 'cancelled') {
      cancelled = true
      break
    }
  }

  // 3. Re-flow the members into a balanced grid (the fold/insert path builds
  //    a left-leaning chain).
  if (ws.panelIds.length > 1) {
    tabStore.applyWorkspaceLayout(ws.id, tabStore.buildGridLayout(ws.panelIds))
  }
  if (ws.panelIds[0]) tabStore.setActivePanel(ws.id, ws.panelIds[0])

  if (ws.panelIds.length === 0) {
    // Nothing landed (all prompts cancelled / all connects failed).
    tabStore.closeTab(ws.id)
    return null
  }

  if (cancelled) {
    msg.info(t('workspace.createCancelled'))
  }
  if (skippedHosts > 0) {
    msg.warning(t('workspace.createSkippedHosts', { count: skippedHosts }))
  }
  return ws
}
