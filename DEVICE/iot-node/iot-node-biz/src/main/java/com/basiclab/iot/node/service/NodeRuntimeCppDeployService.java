package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;

import java.util.List;

public interface NodeRuntimeCppDeployService {

    NodeRuntimeCppCheckRespVO checkBySsh(Long nodeId);

    NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeRuntimeCppBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchDeployBySsh(NodeRuntimeCppBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchRemoveBySsh(NodeRuntimeCppBatchReqVO reqVO);

    /** 单节点部署 RUNTIME（供算法 bundle 全量分发调用） */
    boolean deployOnNodeIfMissing(Long nodeId, List<NodeMediaRemoteDeployRespVO.DeployStep> steps);
}
