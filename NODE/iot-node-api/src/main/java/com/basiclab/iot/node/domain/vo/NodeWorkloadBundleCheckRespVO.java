package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "工作负载 bundle 检测响应")
@Data
public class NodeWorkloadBundleCheckRespVO {

    @Schema(description = "bundle 类型")
    private String bundleType;

    @Schema(description = "运行时是否就绪")
    private Boolean envReady;

    @Schema(description = "脚本是否就绪")
    private Boolean scriptsReady;

    @Schema(description = "FFmpeg 是否就绪（仅 VIDEO 类 bundle）")
    private Boolean ffmpegReady;

    @Schema(description = "远程 ffmpeg 路径")
    private String ffmpegPath;

    @Schema(description = "远程 Python 启动器路径")
    private String pythonLauncher;

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "检测步骤")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
