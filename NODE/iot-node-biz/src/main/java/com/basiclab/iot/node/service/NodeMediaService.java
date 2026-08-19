package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.DeviceMediaBindingRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;

import java.util.Map;

public interface NodeMediaService {

    DeviceMediaBindingRespVO allocate(NodeMediaAllocateReqVO reqVO);

    DeviceMediaBindingRespVO getBinding(String deviceId);

    void release(String deviceId);

    Map<String, Object> deployMediaStack(NodeMediaDeployReqVO reqVO);

    NodeMediaRemoteDeployRespVO deployMediaStackBySsh(Long nodeId);

    NodeMediaStackCheckRespVO checkMediaStackBySsh(Long nodeId);

    NodePortCheckRespVO checkMediaPortsBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO stopMediaServiceBySsh(Long nodeId, String service);

    NodeMediaRemoteDeployRespVO removeMediaContainerBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO removeMediaImageBySsh(Long nodeId);

}
