package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.util.List;

@Schema(description = "FFmpeg 批量操作请求（仅需节点列表）")
@Data
public class NodeFfmpegBatchReqVO {

    @Schema(description = "目标节点 ID 列表", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "节点列表不能为空")
    private List<Long> nodeIds;
}
