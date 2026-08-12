package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 多集群与桥接总览")
@Data
public class NfsMultiClusterOverviewRespVO {

    private Long activeClusterId;
    private String activeClusterName;
    private List<NfsClusterRespVO> clusters = new ArrayList<>();
    private List<NfsBridgeRespVO> bridges = new ArrayList<>();

    @Data
    public static class NfsClusterRespVO {
        private Long id;
        private String name;
        private String laneKey;
        private Long controlPlaneId;
        private Long primaryNodeId;
        private String primaryHost;
        private String primaryName;
        private Long standbyNodeId;
        private String standbyHost;
        private String standbyName;
        private String mountRoot;
        private String nfsExport;
        private Boolean isActive;
        private String status;
        private Boolean primaryReady;
        private Integer clientCount;
        private Integer clientReadyCount;
    }

    @Data
    public static class NfsBridgeRespVO {
        private Long id;
        private String name;
        private Long sourceClusterId;
        private String sourceClusterName;
        private Long targetClusterId;
        private String targetClusterName;
        private String sourceRelPaths;
        private String targetRelPath;
        private String scheduleCron;
        private Boolean enabled;
        private String status;
        private LocalDateTime lastRunAt;
        private Boolean lastSuccess;
        private String lastMessage;
        private LocalDateTime createTime;
    }
}
