package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReqVO;

import java.util.Map;

public interface NodeSentinelRemediatorService {

    Map<String, Object> remediate(NodeSentinelRemediateReqVO reqVO);
}
