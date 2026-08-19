package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "创建 NFS 桥接")
@Data
public class NfsBridgeCreateReqVO {

    @Schema(description = "名称")
    private String name;

    @Schema(description = "源集群 ID（必须是当前主集群）")
    private Long sourceClusterId;

    @Schema(description = "目标集群 ID")
    private Long targetClusterId;

    @Schema(description = "源相对目录，逗号分隔；默认 alert_images,playbacks,snaps")
    private String sourceRelPaths;

    @Schema(description = "目标相对前缀；默认 _bridge/{sourceClusterId}；必须落在 _bridge/ 下")
    private String targetRelPath;

    @Schema(description = "可选 cron；空则仅手动")
    private String scheduleCron;
}
