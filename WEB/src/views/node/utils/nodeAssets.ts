/** 节点角色视觉配置（Icon 组合 + 主题色，对齐存储空间文件夹图标方案） */
export interface NodeRoleVisual {
  coverClass: string;
  iconClass: string;
  bodyIcon: string;
  roleMarkIcon: string;
}

export const NODE_ROLE_VISUAL: Record<string, NodeRoleVisual> = {
  algorithm: {
    coverClass: 'node-card-cover--compute',
    iconClass: 'node-server-icon--compute',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:video-outline',
  },
  forward: {
    coverClass: 'node-card-cover--media',
    iconClass: 'node-server-icon--media',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:transit-connection-variant',
  },
  live: {
    coverClass: 'node-card-cover--media',
    iconClass: 'node-server-icon--media',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:cast',
  },
  train: {
    coverClass: 'node-card-cover--compute',
    iconClass: 'node-server-icon--compute',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:school-outline',
  },
  llm: {
    coverClass: 'node-card-cover--compute',
    iconClass: 'node-server-icon--compute',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:robot-outline',
  },
  label: {
    coverClass: 'node-card-cover--compute',
    iconClass: 'node-server-icon--compute',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:tag-outline',
  },
  infer: {
    coverClass: 'node-card-cover--compute',
    iconClass: 'node-server-icon--compute',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:chip',
  },
  mqtt: {
    coverClass: 'node-card-cover--mqtt',
    iconClass: 'node-server-icon--mqtt',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:access-point-network',
  },
  nfs: {
    coverClass: 'node-card-cover--storage',
    iconClass: 'node-server-icon--storage',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:folder-network-outline',
  },
  transform: {
    coverClass: 'node-card-cover--hybrid',
    iconClass: 'node-server-icon--hybrid',
    bodyIcon: 'mdi:server',
    roleMarkIcon: 'mdi:swap-horizontal',
  },
};

export function getNodeRoleVisual(role?: string): NodeRoleVisual {
  return NODE_ROLE_VISUAL[role || ''] || NODE_ROLE_VISUAL.algorithm;
}
