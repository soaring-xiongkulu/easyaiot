/**
 * EasyAIoT — 启动时预置唯一工作区，并删除其它注册项（只要 EasyAIoT）
 */
import type { Context } from '@deepseek-ai/cordis'

export const name = 'easyaiot-workspace-seed'
export const inject = ['workspaceRegistry'] as const

type Workspace = { id: string; path: string; title: string }
type WorkspaceRegistry = {
  create: (path: string, title?: string) => Promise<Workspace>
  list: () => Workspace[]
  delete: (id: string) => Promise<boolean>
}

export function apply(ctx: Context) {
  const path = (process.env.HARNESS_WORKSPACE || '/workspace/easyaiot').trim()
  const title = (process.env.HARNESS_WORKSPACE_TITLE || 'EasyAIoT').trim() || 'EasyAIoT'
  if (!path) {
    console.warn('[easyaiot-workspace-seed] HARNESS_WORKSPACE empty — skip')
    return
  }

  const registry = (ctx as Context & { workspaceRegistry: WorkspaceRegistry }).workspaceRegistry

  void (async () => {
    const ws = await registry.create(path, title)
    console.log(`[easyaiot-workspace-seed] ready id=${ws.id} path=${ws.path} title=${ws.title}`)

    const keep = ws.path
    for (const other of registry.list()) {
      if (other.id === ws.id)
        continue
      if (other.path === keep)
        continue
      try {
        await registry.delete(other.id)
        console.log(`[easyaiot-workspace-seed] removed extra workspace id=${other.id} path=${other.path}`)
      }
      catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err)
        console.warn(`[easyaiot-workspace-seed] delete ${other.id} failed: ${msg}`)
      }
    }
  })().catch((err: unknown) => {
    const msg = err instanceof Error ? err.message : String(err)
    console.warn(`[easyaiot-workspace-seed] failed: ${msg}`)
  })
}
