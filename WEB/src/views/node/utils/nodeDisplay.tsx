import { h, type VNode } from 'vue';
import type { ComputeNodeVO } from '@/api/device/node';
import { NODE_FUNCTION_MAP, NODE_STATUS_MAP, NODE_TERM, SETUP_COPY, CEPH_MOUNT_LABELS, readCephMountFromTags, formatNodeFunctions, primaryNodeFunction, type CephMountStatus } from './constants';
import { isPlatformNode } from './platformNode';

type SshCredentialNode = Pick<ComputeNodeVO, 'sshUsername' | 'sshCredentialConfigured'>;

export function isSshUsernameConfigured(node?: SshCredentialNode | null): boolean {
  if (!node) return false;
  if (node.sshUsername?.trim()) return true;
  return node.sshCredentialConfigured === true;
}

export function formatSshUsername(val?: string, node?: SshCredentialNode | null): string {
  const name = val?.trim();
  if (name) return name;
  if (isSshUsernameConfigured(node)) return '已配置';
  return '未配置';
}

export const NODE_STATUS_STYLE: Record<string, { bg: string; color: string; border: string }> = {
  pending: { bg: '#f0f5ff', color: '#1d39c4', border: '#adc6ff' },
  online: { bg: '#f6ffed', color: '#389e0d', border: '#b7eb8f' },
  offline: { bg: '#fff2f0', color: '#cf1322', border: '#ffccc7' },
  maintenance: { bg: '#fffbe6', color: '#d48806', border: '#ffe58f' },
};

function resolveStatusKey(status?: string) {
  return status && NODE_STATUS_MAP[status] ? status : 'pending';
}

function resolveRoleKey(node?: { functions?: string[] | null; nodeRole?: string | null } | string | null) {
  if (typeof node === 'string') {
    return node in NODE_FUNCTION_MAP ? node : primaryNodeFunction({ nodeRole: node });
  }
  return primaryNodeFunction(node);
}

export function renderNodeStatusBadge(status?: string) {
  const key = resolveStatusKey(status);
  const label = NODE_STATUS_MAP[key]?.text || status || '-';
  return h('span', { class: `node-meta-badge node-meta-badge--status-${key}` }, [
    h('span', { class: 'node-meta-badge__dot' }),
    label,
  ]);
}

export function renderNodeRoleBadge(node?: { functions?: string[] | null; nodeRole?: string | null } | string | null) {
  const key = resolveRoleKey(node);
  const label = typeof node === 'string' ? (NODE_FUNCTION_MAP[node] || node) : formatNodeFunctions(node);
  return h('span', { class: `node-meta-badge node-meta-badge--role-${key}` }, label || '-');
}

export function renderNodeReadinessBadge(ready: boolean) {
  return h(
    'span',
    { class: `node-meta-badge node-meta-badge--readiness-${ready ? 'ready' : 'pending'}` },
    ready ? SETUP_COPY.readinessReady : SETUP_COPY.readinessPending,
  );
}

export function renderPlatformNodeBadge() {
  return h('span', { class: 'node-meta-badge node-meta-badge--xs node-meta-badge--scope-control-plane' }, NODE_TERM.controlPlaneNode);
}

function cephBadgeClass(status: CephMountStatus): string {
  if (status === 'ready') return 'node-meta-badge--ceph-ready';
  if (status === 'not_ready') return 'node-meta-badge--ceph-not-ready';
  return 'node-meta-badge--ceph-unknown';
}

export function renderCephMountBadge(tags?: Record<string, string | undefined>) {
  const { status, mountPath } = readCephMountFromTags(tags);
  const label = CEPH_MOUNT_LABELS[status];
  const title = mountPath ? `${label} · ${mountPath}` : label;
  return h('span', { class: `node-meta-badge ${cephBadgeClass(status)}`, title }, label);
}

export function renderNodeNameWithPlatformBadge(
  name?: string,
  node?: Pick<ComputeNodeVO, 'isPlatform' | 'capabilities'> | null,
) {
  const children: VNode[] = [h('span', null, name || '-')];
  if (isPlatformNode(node)) {
    children.push(h('span', { class: 'node-name-platform-badge' }, [renderPlatformNodeBadge()]));
  }
  return h('span', { class: 'node-name-with-badge' }, children);
}
