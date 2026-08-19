package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeMqttDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMqttStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;

import java.util.Map;

public interface NodeMqttService {

    Map<String, Object> deployMqttStack(NodeMqttDeployReqVO reqVO);

    NodeMediaRemoteDeployRespVO deployMqttStackBySsh(Long nodeId);

    NodeMqttStackCheckRespVO checkMqttStackBySsh(Long nodeId);

    NodePortCheckRespVO checkMqttPortsBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO stopMqttServiceBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO removeMqttContainerBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO removeMqttImageBySsh(Long nodeId);

}
