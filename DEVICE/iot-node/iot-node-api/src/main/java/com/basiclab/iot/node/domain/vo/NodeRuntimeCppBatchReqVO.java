package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.util.List;

@Schema(description = "RUNTIME(C++) 批量操作请求")
@Data
public class NodeRuntimeCppBatchReqVO {

    @Schema(description = "目标节点 ID 列表", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "节点列表不能为空")
    private List<Long> nodeIds;
}
