package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeAgentHeartbeatReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentRegisterReqVO;

public interface NodeAgentService {

    void register(NodeAgentRegisterReqVO reqVO);

    void heartbeat(NodeAgentHeartbeatReqVO reqVO);

}
