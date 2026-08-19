package com.basiclab.iot.node.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeRespVO;
import com.basiclab.iot.node.domain.vo.ComputeNodeSaveReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendReqVO;
import com.basiclab.iot.node.domain.vo.NodeMetricTrendRespVO;
import com.basiclab.iot.node.domain.vo.PlatformAgentBootstrapRespVO;

public interface ComputeNodeService {

    ComputeNodeRespVO createNode(ComputeNodeSaveReqVO createReqVO);

    void updateNode(ComputeNodeSaveReqVO updateReqVO);

    void deleteNode(Long id);

    ComputeNodeRespVO getNode(Long id);

    PageResult<ComputeNodeRespVO> getNodePage(ComputeNodePageReqVO pageReqVO);

    void ensurePlatformNode();

    PlatformAgentBootstrapRespVO getPlatformAgentBootstrap();

    boolean testSsh(Long id);

    String resetAgentToken(Long id);

    ComputeNodeRespVO getAgentSetup(Long id);

    NodeMediaRemoteDeployRespVO deployAgentBySsh(Long nodeId, String controlPlaneUrl);

    NodeAgentCheckRespVO checkAgentBySsh(Long nodeId, String controlPlaneUrl);

    NodePortCheckRespVO checkAgentPortBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO stopAgentBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO removeAgentBySsh(Long nodeId);

    void setMaintenance(Long id, boolean enabled);

    NodeMetricTrendRespVO getMetricTrend(NodeMetricTrendReqVO reqVO);

}
