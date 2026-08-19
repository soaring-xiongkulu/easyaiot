package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Schema(description = "管理后台 - 平台宿主机地址")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PlatformHostRespVO {

    @Schema(description = "宿主机 IPv4")
    private String host;

    @Schema(description = "Gateway 端口")
    private Integer port;
}
