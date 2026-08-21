package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 共享媒体节点拓扑（主/备服务端 ↔ 客户端）")
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
        private List<String> functions;
        private String status;
        private Integer agentPort;
        /**
         * platform | nfs_primary | nfs_standby | nfs_client | nfs_candidate
         * 兼容旧值：storage_nfs≈nfs_primary/candidate，ceph_client≈nfs_client
         */
        private String kind;
        private Boolean isPlatform;
        /** primary | standby | client | candidate */
        private String nfsClusterRole;
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
        /** 真 NFS Export（exportfs + :2049）是否就绪；与本机目录可写无关 */
        private Boolean nfsExportReady;
        private String nfsMountPath;
        private String nfsServerHost;
        private String nfsExportPath;
        /** 唯一存储通路：nfs（历史 local_bind 已废弃，拓扑不再返回） */
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
        private Long sourceNodeId;
        private Long targetNodeId;
        /** nfs_mount | nfs_standby | platform */
        private String relation;
    }

    @Data
    public static class TopologySummaryVO {
        private int totalNodes;
        /** 主+备服务端数量（兼容旧字段） */
        private int storageNodes;
        private int clientNodes;
        /** 主服务端数量（0 或 1） */
        private int primaryCount;
        /** 备服务端数量 */
        private int standbyCount;
        /** 未分配的存储候选 */
        private int candidateCount;
        /** 主服务端 Export 是否就绪 */
        private Boolean primaryReady;
        private Long primaryNodeId;
        private String primaryHost;
        private Long standbyNodeId;
        private String standbyHost;
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
