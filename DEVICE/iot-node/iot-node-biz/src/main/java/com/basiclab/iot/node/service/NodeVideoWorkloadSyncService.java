package com.basiclab.iot.node.service;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;

/**
 * 远程工作负载部署前同步 VIDEO 代码到计算节点。
 */
public interface NodeVideoWorkloadSyncService {

    void syncBeforeDeploy(ComputeNodeDO node, String workloadType);
}
