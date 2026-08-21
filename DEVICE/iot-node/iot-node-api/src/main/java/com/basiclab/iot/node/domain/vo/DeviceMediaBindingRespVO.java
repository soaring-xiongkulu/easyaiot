package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "媒体 - 设备流绑定 Response VO")
@Data
public class DeviceMediaBindingRespVO {

    private String deviceId;

    private Long srsLiveNodeId;

    private Long srsAiNodeId;

    private Long zlmNodeId;

    private String rtmpStream;

    private String httpStream;

    private String aiRtmpStream;

    private String aiHttpStream;

    private String zlmHost;

    private Integer zlmHttpPort;

    private Integer zlmRtmpPort;

    private String region;

    private String status;

}
