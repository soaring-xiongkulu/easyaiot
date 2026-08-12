package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 集群节点分配（主服务端 + 备服务端 + 客户端挂载）")
@Data
public class NodeNfsClusterAssignReqVO {

    @Schema(description = "NFS 主服务端节点 ID；为空则优先 storage，否则控制面")
    private Long serverNodeId;

    @Schema(description = "NFS 备服务端节点 ID（软 HA，可选）")
    private Long standbyNodeId;

    @Schema(description = "需要挂载 NFS 的客户端节点 ID 列表；为空则自动选取")
    private List<Long> clientNodeIds = new ArrayList<>();

    @Schema(description = "媒体挂载根，默认 /mnt/easyaiot-media")
    private String mountRoot;

    @Schema(description = "NFS export 路径（服务端），默认与 mountRoot 相同")
    private String nfsExport;

    @Schema(description = "NFS 挂载选项，默认 vers=3,tcp,nolock,_netdev")
    private String nfsMountOpts;
}
