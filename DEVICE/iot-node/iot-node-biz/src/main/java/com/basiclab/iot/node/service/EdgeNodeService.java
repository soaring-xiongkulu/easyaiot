package com.basiclab.iot.node.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.domain.vo.EdgeEnrollReqVO;
import com.basiclab.iot.node.domain.vo.EdgeEnrollRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodePageReqVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeRespVO;
import com.basiclab.iot.node.domain.vo.EdgeNodeUpdateReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigReqVO;
import com.basiclab.iot.node.domain.vo.EdgeRuntimeConfigRespVO;

/**
 * EDGE 模块：自助纳管 + 动态配置 + 边缘节点统一管理
 */
public interface EdgeNodeService {

    EdgeEnrollRespVO enroll(EdgeEnrollReqVO reqVO);

    EdgeRuntimeConfigRespVO runtimeConfig(EdgeRuntimeConfigReqVO reqVO);

    PageResult<EdgeNodeRespVO> getEdgeNodePage(EdgeNodePageReqVO reqVO);

    EdgeNodeRespVO getEdgeNode(Long id);

    void updateEdgeNode(EdgeNodeUpdateReqVO reqVO);

    void deleteEdgeNode(Long id);

    /** enroll / heartbeat 时同步 edge_node 管理表 */
    void syncEdgeNodeRecord(ComputeNodeDO computeNode, EdgeEnrollReqVO enrollHint);

}
