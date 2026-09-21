import type { CredentialResult } from '../components/CredentialPrompt.vue'
import type { ConnectionConfig } from '../types/session'
import { useConnectionStore } from '../stores/connectionStore'
import { useI18n } from '../i18n'
import { inject } from 'vue'

type ShowCredentialDialog = (
  title: string,
  subtitle: string,
  fields: ('user' | 'password')[],
  initialUser?: string,
  initialPassword?: string
) => Promise<CredentialResult | null>

function needsCred(cfg: ConnectionConfig): boolean {
  if (cfg.type !== 'ssh' && cfg.type !== 'mosh' && cfg.type !== 'sftp' && cfg.type !== 'scp' && cfg.type !== 'ftp') return false
  if ((cfg.type === 'ssh' || cfg.type === 'mosh' || cfg.type === 'scp' || cfg.type === 'sftp') && (cfg.authType === 'key' || cfg.authType === 'keyText')) return false
  // 身份认证：账密来自身份库(密钥库)，由后端 materializeIdentity 解析，无需补全提示。
  // 与 App.vue needsCredentialCheck 保持一致 —— 否则 identity 连接的 user/password 字段
  // 为空会被误判为"缺少凭据"而弹窗，弹窗里的临时/旧密码又会压过后端从密钥库解析出的正确值。
  if (cfg.authType === 'identity' || cfg.authType === 'kerberos' || cfg.authType === 'agent') return false
  return !cfg.user || !cfg.password
}

// 解析 tunnel 连接的 user/password：需要时弹 credential 对话框，用户取消返回 null。
// 逻辑复刻自 App.vue 中 ensureCredentials 的 tunnel 分支，供无 App.vue 上下文的 tab
// 组件（例如 K8sTabContent）在不复用整个 ensureCredentials 的情况下同样得到凭据。
export function useTunnelCredentials() {
  const connectionStore = useConnectionStore()
  const { t } = useI18n()
  const showCredentialDialog = inject<ShowCredentialDialog>(
    'showCredentialDialog',
    () => Promise.resolve(null)
  )

  async function resolve(tunnelSSHConnId: string): Promise<{ user: string; password: string } | null> {
    if (!tunnelSSHConnId) return { user: '', password: '' }
    const tunnelConn = connectionStore.connections.find(c => c.id === tunnelSSHConnId)
    if (!tunnelConn) return { user: '', password: '' }
    if (!needsCred(tunnelConn)) {
      return { user: tunnelConn.user || '', password: tunnelConn.password || '' }
    }
    const result = await showCredentialDialog(
      t('credential.tunnelTitle'),
      t('credential.tunnelSubtitle', { name: tunnelConn.name }),
      ['user', 'password'],
      tunnelConn.user,
      tunnelConn.password
    )
    if (!result) return null
    const user = result.user || tunnelConn.user || ''
    const password = result.password || tunnelConn.password || ''
    if (result.action === 'save_and_connect') {
      await connectionStore.update(tunnelConn.id, { user, password })
    }
    return { user, password }
  }

  return { resolveTunnelCredentials: resolve }
}
