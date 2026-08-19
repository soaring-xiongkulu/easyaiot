package com.basiclab.iot.node.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.*;

import java.util.List;

public interface ControlPlaneService {

    PageResult<ClusterLaneRespVO> listLanes(ClusterLanePageReqVO reqVO);

    List<ControlPlanePeerRespVO> listPeers();

    ControlPlanePeerRespVO createPeer(ControlPlanePeerSaveReqVO reqVO);

    void deletePeer(Long id);

    void syncPeer(Long id);

    void registerPeer(ControlPlanePeerRegisterReqVO reqVO, String inboundToken);

    ControlPlaneSnapshotRespVO getSnapshot(String inboundToken);

    void batchLaneAction(ClusterLaneBatchReqVO reqVO);

    void ensureWorkerControlPlaneAssignments();

}
