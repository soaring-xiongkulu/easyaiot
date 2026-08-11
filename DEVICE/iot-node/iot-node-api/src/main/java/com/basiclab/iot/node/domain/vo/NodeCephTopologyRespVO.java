package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 共享媒体节点拓扑（中心 ↔ 存储服务端/客户端）")
@Data
public class NodeCephTopologyRespVO {

    @Schema(description = "控制面/中心节点")
    private TopologyNodeVO center;

    @Schema(description = "拓扑节点列表（含中心）")
    private List<TopologyNodeVO> nodes = new ArrayList<>();

    @Schema(description = "拓扑连线")
    private List<TopologyLinkVO> links = new ArrayList<>();

    @Schema(description = "汇总")
    private TopologySummaryVO summary;

    @Data
    public static class TopologyNodeVO {
        private Long nodeId;
        private String name;
        private String host;
        private String nodeRole;
        private String status;
        private Integer agentPort;
        /** platform | storage_nfs | nfs_client */
        private String kind;
        private Boolean isPlatform;
        /** @deprecated 兼容旧前端，等同 nfsMountReady */
        private Boolean cephMountReady;
        /** @deprecated 兼容旧前端，等同 nfsMountPath */
        private String cephMountPath;
        /** @deprecated 兼容旧前端，等同 nfsServerHost */
        private String cephMonHost;
        /** @deprecated 保留字段 */
        private String cephPool;
        /** @deprecated 保留字段 */
        private String cephfsName;
        private Boolean nfsMountReady;
        private String nfsMountPath;
        private String nfsServerHost;
        private String nfsExportPath;
        /** nfs | local_bind（未指定 NFS 服务端时本机 export） */
        private String storageBackend;
        /** 最近一次 SSH/探针时间（ISO 或可解析字符串） */
        private String nfsProbeAt;
        /** 最近一次探针摘要 */
        private String nfsProbeSummary;
        /** 实际挂载源，如 host:/export */
        private String nfsMountSource;
        private String alertImagesDir;
        private String playbacksDir;
        private String snapsDir;
        private LocalDateTime lastHeartbeatAt;
        private Boolean sshCredentialConfigured;
    }

    @Data
    public static class TopologyLinkVO {
        /** 源节点 ID；中心可用 nodeId，或约定 sourceKind=platform */
        private Long sourceNodeId;
        private Long targetNodeId;
        /** mon | client_mount | platform */
        private String relation;
    }

    @Data
    public static class TopologySummaryVO {
        private int totalNodes;
        private int storageNodes;
        private int clientNodes;
        private int mountReadyCount;
        private int mountNotReadyCount;
        private int offlineCount;
        /** 客户端挂载覆盖率 0-100；clientNodes=0 时为 0 */
        private Integer coveragePercent;
        /** 节点中最新探针时间 */
        private String lastProbeAt;
        /** 尚无 nfs_probe_at 的关联节点数 */
        private int unprobedCount;
    }
}
