import type { Router } from 'vue-router';
import {
  CAMERA_NFS_TAB,
  NODE_SERVICE_TAB,
  STORAGE_SUB_TAB_TO_PAGE,
  isCameraNfsTab,
  resolveOnboardServiceTab,
  type NodeServiceTabKey,
} from './constants';
import { requestNodePageTab, type StorageSubTabKey } from './useNodePageTab';

function isNodeIndexRoute(router: Router) {
  return router.currentRoute.value.path === '/node/index';
}

function resolveTabKey(tab: NodeServiceTabKey | string) {
  return tab in NODE_SERVICE_TAB ? NODE_SERVICE_TAB[tab as NodeServiceTabKey] : String(tab);
}

function pushCameraNfsTab(router: Router, tab: string, opts?: { nodeId?: number; nodeIds?: number[] }) {
  const query: Record<string, string> = { tab };
  if (opts?.nodeId) query.nodeId = String(opts.nodeId);
  if (opts?.nodeIds?.length) query.nodeIds = opts.nodeIds.join(',');
  return router.push({ path: '/camera/index', query });
}

export function navigateToNodeServiceTab(
  router: Router,
  tab: NodeServiceTabKey | string,
  nodeId?: number,
) {
  const tabKey = resolveTabKey(tab);
  if (isCameraNfsTab(tabKey)) {
    void pushCameraNfsTab(router, tabKey, { nodeId });
    return;
  }
  if (isNodeIndexRoute(router)) {
    requestNodePageTab({ tab: tabKey, nodeId });
    return;
  }
  router.push({
    path: '/node/index',
    query: {
      tab: tabKey,
      ...(nodeId ? { nodeId: String(nodeId) } : {}),
    },
  });
}

/** 跳转到流媒体管理 — NFS 一级 Tab */
export function navigateToStorageSubTab(
  router: Router,
  subTab: StorageSubTabKey = 'manage',
  nodeId?: number,
) {
  const tabKey = STORAGE_SUB_TAB_TO_PAGE[subTab] || CAMERA_NFS_TAB.manage;
  void pushCameraNfsTab(router, tabKey, { nodeId });
}

/** 泳道批量操作：携带多节点跳转部署 Tab */
export function navigateToNodeBatchTab(router: Router, tab: string, nodeIds: number[]) {
  if (!nodeIds.length) return;
  if (isCameraNfsTab(tab)) {
    void pushCameraNfsTab(router, tab, { nodeIds });
    return;
  }
  if (isNodeIndexRoute(router)) {
    requestNodePageTab({ tab, nodeIds });
    return;
  }
  router.push({
    path: '/node/index',
    query: {
      tab,
      nodeIds: nodeIds.join(','),
    },
  });
}

export function navigateToOnboardService(
  router: Router,
  node: { id?: number; functions?: string[] | null; nodeRole?: string | null },
) {
  if (!node.id) return;
  navigateToNodeServiceTab(router, resolveOnboardServiceTab(node), node.id);
}
