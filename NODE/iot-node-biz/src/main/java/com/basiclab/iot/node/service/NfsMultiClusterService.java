package com.basiclab.iot.node.service;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NfsClusterDO;
import com.basiclab.iot.node.domain.vo.NfsBridgeCreateReqVO;
import com.basiclab.iot.node.domain.vo.NfsClusterActivateReqVO;
import com.basiclab.iot.node.domain.vo.NfsMultiClusterOverviewRespVO;

public interface NfsMultiClusterService {

    NfsMultiClusterOverviewRespVO getOverview();

    /** 分配后同步本地泳道集群记录；返回集群 ID */
    NfsClusterDO upsertLocalCluster(ComputeNodeDO primary, ComputeNodeDO standby, String mountRoot, String nfsExport, String mountOpts);

    NfsMultiClusterOverviewRespVO activateCluster(NfsClusterActivateReqVO req);

    NfsMultiClusterOverviewRespVO createBridge(NfsBridgeCreateReqVO req);

    NfsMultiClusterOverviewRespVO stopBridge(Long bridgeId);

    NfsMultiClusterOverviewRespVO enableBridge(Long bridgeId, boolean enabled);

    NfsMultiClusterOverviewRespVO runBridge(Long bridgeId);

    /** 停用指定主集群发出的全部桥接 */
    int stopBridgesBySourceCluster(Long sourceClusterId);
}
