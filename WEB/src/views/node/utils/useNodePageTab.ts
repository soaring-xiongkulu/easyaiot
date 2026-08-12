import { shallowRef } from 'vue';

export type StorageSubTabKey = 'manage' | 'topology' | 'clusters' | 'ops' | 'files';

export interface NodePageTabRequest {
  tab: string;
  nodeIds?: number[];
  nodeId?: number;
  bundle?: string;
}

const tabRequest = shallowRef<NodePageTabRequest | null>(null);

/** 页内 Tab 切换（不修改 URL，避免布局层新开顶级 Tab） */
export function requestNodePageTab(req: NodePageTabRequest) {
  tabRequest.value = { ...req };
}

export function useNodePageTabRequest() {
  return tabRequest;
}
