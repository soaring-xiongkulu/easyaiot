package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployRespVO;

public interface NodeCommandService {

    NodeWorkloadDeployRespVO deployWorkload(NodeWorkloadDeployReqVO reqVO);

    void stopWorkload(Long nodeId, String workloadType, String workloadId);

    /** 按绑定表反查节点后硬停（心跳未带 TRANSFORM_NODE_ID 时可用） */
    void stopWorkloadByBinding(String workloadType, String workloadId);

}
