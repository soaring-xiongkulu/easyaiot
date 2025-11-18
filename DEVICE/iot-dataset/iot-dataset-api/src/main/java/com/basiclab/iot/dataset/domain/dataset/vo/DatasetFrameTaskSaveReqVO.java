package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * DatasetFrameTaskSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频流帧捕获任务新增/修改 Request VO")
@Data
public class DatasetFrameTaskSaveReqVO {

    @Schema(description = "主键id", example = "6556")
    private Long id;

    @Schema(description = "数据集ID", example = "15239")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "任务名称", example = "赵六")
    @NotEmpty(message = "任务名称不能为空")
    private String taskName;

    @Schema(description = "任务编码")
    private String taskCode;

    @Schema(description = "任务类型[0:实时流抽帧,1:GB28181流抽帧]", example = "1")
    @NotNull(message = "任务类型[0:实时流抽帧,1:GB28181流抽帧]不能为空")
    private Short taskType;

    @Schema(description = "通道ID", example = "26571")
    private String channelId;

    @Schema(description = "设备ID", example = "10185")
    private String deviceId;

    @Schema(description = "RTMP播放流地址", example = "https://www.iocoder.cn")
    private String rtmpUrl;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "创建人")
    private String updateBy;

}