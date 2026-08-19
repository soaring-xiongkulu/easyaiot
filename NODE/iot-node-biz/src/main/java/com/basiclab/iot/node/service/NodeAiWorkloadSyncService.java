package com.basiclab.iot.node.service;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;

/**
 * 远程 AI 工作负载部署前同步 AI 代码到计算节点。
 */
public interface NodeAiWorkloadSyncService {

    void syncBeforeDeploy(ComputeNodeDO node, String workloadType);
}
