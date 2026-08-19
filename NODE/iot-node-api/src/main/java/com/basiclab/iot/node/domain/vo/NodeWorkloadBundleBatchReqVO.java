package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.util.List;

@Schema(description = "工作负载 bundle 批量操作请求")
@Data
public class NodeWorkloadBundleBatchReqVO {

    @Schema(description = "目标节点 ID 列表", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "节点列表不能为空")
    private List<Long> nodeIds;

    @Schema(description = "bundle 类型: stream_forward | ... | transform_runtime",
            requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "bundleType 不能为空")
    private String bundleType;

    @Schema(description = "TRANSFORM 全量分发后拉起的容器副本数（默认读配置，通常 1）")
    private Integer replicas;
}
