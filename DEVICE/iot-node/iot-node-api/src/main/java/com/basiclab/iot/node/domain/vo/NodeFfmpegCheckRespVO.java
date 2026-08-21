package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "单节点 FFmpeg 检测响应")
@Data
public class NodeFfmpegCheckRespVO {

    @Schema(description = "FFmpeg 是否就绪")
    private Boolean ffmpegReady;

    @Schema(description = "远程 ffmpeg 路径")
    private String ffmpegPath;

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "检测步骤")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
