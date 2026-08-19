package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeFfmpegBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeFfmpegCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;

public interface NodeFfmpegDeployService {

    NodeFfmpegCheckRespVO checkBySsh(Long nodeId);

    NodeWorkloadBundleBatchRespVO batchCheckBySsh(NodeFfmpegBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchDeployBySsh(NodeFfmpegBatchReqVO reqVO);

    NodeWorkloadBundleBatchRespVO batchRemoveBySsh(NodeFfmpegBatchReqVO reqVO);

    /** 单节点部署 FFmpeg（供 VIDEO bundle 全量分发调用） */
    boolean deployOnNodeIfMissing(Long nodeId, java.util.List<com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO.DeployStep> steps);
}
