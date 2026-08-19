package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "工作负载 bundle 批量操作结果")
@Data
public class NodeWorkloadBundleBatchRespVO {

    @Schema(description = "bundle 类型")
    private String bundleType;

    @Schema(description = "整体是否全部成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "各节点结果")
    private List<NodeWorkloadBundleNodeResultVO> results = new ArrayList<>();
}
