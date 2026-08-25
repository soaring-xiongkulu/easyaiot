package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.util.HashMap;
import java.util.Map;

@Schema(description = "节点摄像头接入代理请求")
@Data
public class NodeCameraAccessReqVO {

    @Schema(description = "compute_node.id", required = true)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "发现/扫描/探测参数")
    private Map<String, Object> payload = new HashMap<>();
}
