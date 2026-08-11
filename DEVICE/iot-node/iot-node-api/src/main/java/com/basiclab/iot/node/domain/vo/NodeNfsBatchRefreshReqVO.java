package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 集群批量刷新现状请求")
@Data
public class NodeNfsBatchRefreshReqVO {

    @Schema(description = "节点 ID 列表；为空则刷新拓扑中全部 storage/client 节点")
    private List<Long> nodeIds = new ArrayList<>();

    @Schema(description = "是否定时自动巡检（影响 op_log 类型为 auto_refresh）")
    private Boolean auto;
}
