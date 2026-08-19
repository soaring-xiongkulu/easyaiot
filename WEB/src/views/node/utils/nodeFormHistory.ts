import { MEDIA_PORT_DEFAULTS, STORAGE_TAG_DEFAULTS, formatNodeFunctions } from './constants';

export interface NodeFormHistoryEntry {
  id: string;
  savedAt: number;
  name: string;
  host: string;
  nodeRole?: string;
  functions?: string[];
  region?: string;
  remark?: string;
  sshPort?: number;
  agentPort?: number;
  sshUsername?: string;
  sshAuthType?: string;
  sshPassword?: string;
  sshPrivateKey?: string;
  srsRtmpPort?: number;
  srsHttpPort?: number;
  srsApiPort?: number;
  srsRtcPort?: number;
  zlmHttpPort?: number;
  zlmRtmpPort?: number;
  zlmRtspPort?: number;
  zlmRtcPort?: number;
  zlmRtpPortMin?: number;
  zlmRtpPortMax?: number;
  cephPool?: string;
  cephOsdPath?: string;
  cephfsName?: string;
  cephMonHost?: string;
  mediaMountPath?: string;
}

const STORAGE_KEY = 'easyaiot_node_form_history_v1';
const MAX_ENTRIES = 15;

function loadAll(): NodeFormHistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const list = JSON.parse(raw);
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function persist(list: NodeFormHistoryEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function functionsKey(entry: Pick<NodeFormHistoryEntry, 'functions' | 'nodeRole'>): string {
  if (entry.functions?.length) {
    return [...entry.functions].map((id) => String(id).trim()).filter(Boolean).sort().join(',');
  }
  return String(entry.nodeRole || '')
    .split(/[,\s]+/)
    .map((id) => id.trim())
    .filter(Boolean)
    .sort()
    .join(',');
}

function entryFingerprint(entry: Pick<NodeFormHistoryEntry, 'name' | 'host' | 'functions' | 'nodeRole' | 'sshPort' | 'agentPort'>): string {
  return [
    (entry.name || '').trim(),
    (entry.host || '').trim(),
    functionsKey(entry),
    String(entry.sshPort ?? 22),
    String(entry.agentPort ?? ''),
  ].join('\0');
}

export function loadNodeFormHistory(): NodeFormHistoryEntry[] {
  return loadAll().sort((a, b) => b.savedAt - a.savedAt);
}

export function saveNodeFormHistory(
  entry: Omit<NodeFormHistoryEntry, 'id' | 'savedAt'> & { id?: string; savedAt?: number },
): NodeFormHistoryEntry[] {
  const saved: NodeFormHistoryEntry = {
    ...entry,
    name: (entry.name || '').trim(),
    host: (entry.host || '').trim(),
    functions: entry.functions?.length ? entry.functions : undefined,
    nodeRole: functionsKey(entry) || undefined,
    id: entry.id || `node_${Date.now()}`,
    savedAt: entry.savedAt ?? Date.now(),
  };
  const fp = entryFingerprint(saved);
  const deduped = loadAll().filter((e) => entryFingerprint(e) !== fp);
  persist([saved, ...deduped].slice(0, MAX_ENTRIES));
  return loadNodeFormHistory();
}

export function removeNodeFormHistory(id: string): void {
  persist(loadAll().filter((e) => e.id !== id));
}

export function formatNodeFormHistoryTime(savedAt: number): string {
  const t = new Date(savedAt);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}`;
}

export function formatNodeFormHistoryPrimary(entry: NodeFormHistoryEntry): string {
  const name = entry.name?.trim();
  const host = entry.host?.trim() || '未填写主机';
  return name ? `${name} · ${host}` : host;
}

export function formatNodeFormHistoryMeta(entry: NodeFormHistoryEntry): string {
  const parts: string[] = [
    formatNodeFunctions(entry),
    formatNodeFormHistoryTime(entry.savedAt),
  ];
  if (entry.region?.trim()) {
    parts.splice(1, 0, entry.region.trim());
  }
  return parts.join(' · ');
}

export function nodeFormHistoryToFields(entry: NodeFormHistoryEntry): Record<string, unknown> {
  return {
    name: entry.name,
    host: entry.host,
    functions: entry.functions,
    nodeRole: entry.nodeRole,
    region: entry.region,
    remark: entry.remark,
    sshPort: entry.sshPort ?? 22,
    agentPort: entry.agentPort,
    sshUsername: entry.sshUsername ?? 'root',
    sshAuthType: entry.sshAuthType ?? 'password',
    sshPassword: entry.sshPassword,
    sshPrivateKey: entry.sshPrivateKey,
    srsRtmpPort: entry.srsRtmpPort ?? MEDIA_PORT_DEFAULTS.srsRtmpPort,
    srsHttpPort: entry.srsHttpPort ?? MEDIA_PORT_DEFAULTS.srsHttpPort,
    srsApiPort: entry.srsApiPort ?? MEDIA_PORT_DEFAULTS.srsApiPort,
    srsRtcPort: entry.srsRtcPort ?? MEDIA_PORT_DEFAULTS.srsRtcPort,
    zlmHttpPort: entry.zlmHttpPort ?? MEDIA_PORT_DEFAULTS.zlmHttpPort,
    zlmRtmpPort: entry.zlmRtmpPort ?? MEDIA_PORT_DEFAULTS.zlmRtmpPort,
    zlmRtspPort: entry.zlmRtspPort ?? MEDIA_PORT_DEFAULTS.zlmRtspPort,
    zlmRtcPort: entry.zlmRtcPort ?? MEDIA_PORT_DEFAULTS.zlmRtcPort,
    zlmRtpPortMin: entry.zlmRtpPortMin ?? MEDIA_PORT_DEFAULTS.zlmRtpPortMin,
    zlmRtpPortMax: entry.zlmRtpPortMax ?? MEDIA_PORT_DEFAULTS.zlmRtpPortMax,
    cephPool: entry.cephPool ?? STORAGE_TAG_DEFAULTS.cephPool,
    cephOsdPath: entry.cephOsdPath ?? STORAGE_TAG_DEFAULTS.cephOsdPath,
    cephfsName: entry.cephfsName ?? STORAGE_TAG_DEFAULTS.cephfsName,
    cephMonHost: entry.cephMonHost ?? STORAGE_TAG_DEFAULTS.cephMonHost,
    mediaMountPath: entry.mediaMountPath ?? STORAGE_TAG_DEFAULTS.mediaMountPath,
  };
}

export function valuesToNodeFormHistoryEntry(values: Record<string, unknown>): Omit<NodeFormHistoryEntry, 'id' | 'savedAt'> {
  return {
    name: String(values.name || '').trim(),
    host: String(values.host || '').trim(),
    functions: Array.isArray(values.functions)
      ? (values.functions as string[]).map((id) => String(id).trim()).filter(Boolean)
      : undefined,
    nodeRole: Array.isArray(values.functions)
      ? (values.functions as string[]).join(',')
      : String(values.nodeRole || ''),
    region: values.region ? String(values.region) : undefined,
    remark: values.remark ? String(values.remark) : undefined,
    sshPort: values.sshPort != null ? Number(values.sshPort) : 22,
    agentPort: values.agentPort != null ? Number(values.agentPort) : undefined,
    sshUsername: values.sshUsername ? String(values.sshUsername) : 'root',
    sshAuthType: values.sshAuthType ? String(values.sshAuthType) : 'password',
    sshPassword: values.sshPassword ? String(values.sshPassword) : undefined,
    sshPrivateKey: values.sshPrivateKey ? String(values.sshPrivateKey) : undefined,
    srsRtmpPort: values.srsRtmpPort != null ? Number(values.srsRtmpPort) : undefined,
    srsHttpPort: values.srsHttpPort != null ? Number(values.srsHttpPort) : undefined,
    srsApiPort: values.srsApiPort != null ? Number(values.srsApiPort) : undefined,
    srsRtcPort: values.srsRtcPort != null ? Number(values.srsRtcPort) : undefined,
    zlmHttpPort: values.zlmHttpPort != null ? Number(values.zlmHttpPort) : undefined,
    zlmRtmpPort: values.zlmRtmpPort != null ? Number(values.zlmRtmpPort) : undefined,
    zlmRtspPort: values.zlmRtspPort != null ? Number(values.zlmRtspPort) : undefined,
    zlmRtcPort: values.zlmRtcPort != null ? Number(values.zlmRtcPort) : undefined,
    zlmRtpPortMin: values.zlmRtpPortMin != null ? Number(values.zlmRtpPortMin) : undefined,
    zlmRtpPortMax: values.zlmRtpPortMax != null ? Number(values.zlmRtpPortMax) : undefined,
    cephPool: values.cephPool ? String(values.cephPool) : undefined,
    cephOsdPath: values.cephOsdPath ? String(values.cephOsdPath) : undefined,
    cephfsName: values.cephfsName ? String(values.cephfsName) : undefined,
    cephMonHost: values.cephMonHost ? String(values.cephMonHost) : undefined,
    mediaMountPath: values.mediaMountPath ? String(values.mediaMountPath) : undefined,
  };
}
