package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "目标服务器部署端口占用检测结果")
@Data
public class NodePortCheckRespVO {

    @Schema(description = "检测是否完成（SSH 连通且探测成功）")
    private Boolean success;

    @Schema(description = "部署所需端口是否均可使用（空闲或已被本平台服务占用）")
    private Boolean portsReady;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "各端口检测明细")
    private List<PortItem> ports = new ArrayList<>();

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

    @Schema(description = "单个端口检测结果")
    @Data
    public static class PortItem {

        @Schema(description = "端口用途名称")
        private String name;

        @Schema(description = "端口号")
        private Integer port;

        @Schema(description = "状态：free / occupied / allowed")
        private String status;

        @Schema(description = "占用进程或容器信息")
        private String process;
    }

}
