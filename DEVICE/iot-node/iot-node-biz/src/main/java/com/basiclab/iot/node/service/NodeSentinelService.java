package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeSentinelProbeReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateLogRespVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReportReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRespVO;

import java.util.List;
import java.util.Map;

public interface NodeSentinelService {

    void ingestHeartbeat(Long nodeId, Map<String, Object> sentinelPayload);

    NodeSentinelRespVO getSnapshot(Long nodeId);

    NodeSentinelRespVO probe(NodeSentinelProbeReqVO reqVO);

    NodeSentinelRespVO resync(Long nodeId);

    Map<String, Object> getRegistry();

    Map<String, Boolean> getSchedulableMap(Long nodeId);

    boolean isCapabilitySchedulable(Long nodeId, String capability);

    Map<String, Object> remediate(NodeSentinelRemediateReqVO reqVO);

    Map<String, Object> reportRemediation(NodeSentinelRemediateReportReqVO reqVO);

    List<NodeSentinelRemediateLogRespVO> listRemediateLogs(Long nodeId);

    void validateBeforeDeploy(Long nodeId, String workloadType, Map<String, Object> requirements);
}
