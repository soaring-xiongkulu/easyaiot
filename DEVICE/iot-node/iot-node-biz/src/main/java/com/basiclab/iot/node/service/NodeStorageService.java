package com.basiclab.iot.node.service;

import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;

public interface NodeStorageService {

    /** 中心关联的 NFS 共享媒体节点拓扑 */
    NodeCephTopologyRespVO getCephTopology();

    /** 分配/切换 NFS 集群：指定服务端与客户端，更新节点 tags */
    NodeCephTopologyRespVO assignNfsCluster(NodeNfsClusterAssignReqVO req);

    NodeStorageStackCheckRespVO checkStorageStackBySsh(Long nodeId);

    NodeStorageMountCheckRespVO checkStorageMountBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStorageOsdBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStorageClientBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStoragePoolBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO stopStorageOsdBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO unmountStorageBySsh(Long nodeId);

}
