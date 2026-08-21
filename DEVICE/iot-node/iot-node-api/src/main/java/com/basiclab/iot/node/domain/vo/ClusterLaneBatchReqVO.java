package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.util.List;

@Schema(description = "泳道工作节点批量操作 Request VO")
@Data
public class ClusterLaneBatchReqVO {

    @Schema(description = "泳道键：local 或 peer-{id}")
    private String laneKey;

    @Schema(description = "工作节点 ID 列表", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "节点列表不能为空")
    private List<Long> nodeIds;

    @Schema(description = "操作：maintenance_on | maintenance_off")
    private String action;

}
