package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleCheckRespVO;

public interface NodeWorkloadBundleService {

    NodeWorkloadBundleCheckRespVO checkBySsh(Long nodeId, String bundleType);

    NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeWorkloadBundleBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchDeployEnvBySsh(NodeWorkloadBundleBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchDeployScriptsBySsh(NodeWorkloadBundleBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchDeployFullBySsh(NodeWorkloadBundleBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchRemoveEnvBySsh(NodeWorkloadBundleBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchRemoveScriptsBySsh(NodeWorkloadBundleBatchReqVO reqVO);
}
