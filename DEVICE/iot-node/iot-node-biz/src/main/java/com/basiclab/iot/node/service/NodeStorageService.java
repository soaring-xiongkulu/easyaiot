package com.basiclab.iot.node.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.domain.vo.NodeCephTopologyRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshReqVO;
import com.basiclab.iot.node.domain.vo.NodeNfsBatchRefreshRespVO;
import com.basiclab.iot.node.domain.vo.NodeNfsClusterAssignReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileDownloadResult;
import com.basiclab.iot.node.domain.vo.NodeStorageFileListRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageFileOpsRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageMountCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogPageReqVO;
import com.basiclab.iot.node.domain.vo.NodeStorageOpLogRespVO;
import com.basiclab.iot.node.domain.vo.NodeStorageStackCheckRespVO;
import org.springframework.web.multipart.MultipartFile;

public interface NodeStorageService {

    /** 中心关联的 NFS 共享媒体节点拓扑 */
    NodeCephTopologyRespVO getCephTopology();

    /** 分配/切换 NFS 集群：指定主/备服务端与客户端，更新节点 tags */
    NodeCephTopologyRespVO assignNfsCluster(NodeNfsClusterAssignReqVO req);

    /** 软 HA：将指定节点升为 NFS 主服务端，原主降为备，客户端改挂载目标标签 */
    NodeCephTopologyRespVO promoteNfsPrimary(Long nodeId);

    /** 批量 SSH 刷新 NFS 现状并落库 */
    NodeNfsBatchRefreshRespVO batchRefreshBySsh(NodeNfsBatchRefreshReqVO req);

    PageResult<NodeStorageOpLogRespVO> getOpLogPage(NodeStorageOpLogPageReqVO req);

    NodeStorageFileListRespVO listMediaFiles(Long nodeId, String relativePath);

    NodeStorageFileDownloadResult downloadMediaFile(Long nodeId, String relativePath);

    NodeStorageFileOpsRespVO mkdirMediaDir(Long nodeId, String parentRelativePath, String name);

    NodeStorageFileOpsRespVO uploadMediaFile(Long nodeId, String parentRelativePath, MultipartFile file);

    NodeStorageFileOpsRespVO deleteMediaPath(Long nodeId, String relativePath);

    /** 同目录重命名媒体根内文件或目录 */
    NodeStorageFileOpsRespVO renameMediaPath(Long nodeId, String relativePath, String newName);

    NodeStorageStackCheckRespVO checkStorageStackBySsh(Long nodeId);

    NodeStorageMountCheckRespVO checkStorageMountBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStorageOsdBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStorageClientBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO deployStoragePoolBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO stopStorageOsdBySsh(Long nodeId);

    NodeMediaRemoteDeployRespVO unmountStorageBySsh(Long nodeId);

}
