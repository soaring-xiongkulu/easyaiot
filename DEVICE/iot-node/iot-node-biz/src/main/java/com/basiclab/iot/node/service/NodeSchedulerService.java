package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateRespVO;

public interface NodeSchedulerService {

    NodeSchedulerAllocateRespVO allocate(NodeSchedulerAllocateReqVO reqVO);

    void release(String workloadType, String workloadId);

}
