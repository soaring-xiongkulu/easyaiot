import { shallowRef } from 'vue';

export type StorageSubTabKey = 'topology' | 'ops' | 'files';

export interface NodePageTabRequest {
  tab: string;
  nodeIds?: number[];
  nodeId?: number;
  bundle?: string;
  /** 分布式存储子 Tab（页内切换，不写 URL） */
  storageTab?: StorageSubTabKey;
}

const tabRequest = shallowRef<NodePageTabRequest | null>(null);

/** 页内 Tab 切换（不修改 URL，避免布局层新开顶级 Tab） */
export function requestNodePageTab(req: NodePageTabRequest) {
  tabRequest.value = { ...req };
}

export function useNodePageTabRequest() {
  return tabRequest;
}
