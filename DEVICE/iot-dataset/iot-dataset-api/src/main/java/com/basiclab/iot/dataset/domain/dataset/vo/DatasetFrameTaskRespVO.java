package com.basiclab.iot.dataset.domain.dataset.vo;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * DatasetFrameTaskRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频流帧捕获任务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetFrameTaskRespVO extends BaseEntity {

    @Schema(description = "主键id", example = "6556")
    @ExcelProperty("主键id")
    private Long id;

    @Schema(description = "数据集ID", example = "15239")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "任务名称", example = "赵六")
    @ExcelProperty("任务名称")
    private String taskName;

    @Schema(description = "任务编码")
    @ExcelProperty("任务编码")
    private String taskCode;

    @Schema(description = "任务类型[0:实时流抽帧,1:GB28181流抽帧]", example = "1")
    @ExcelProperty("任务类型[0:实时流抽帧,1:GB28181流抽帧]")
    private Short taskType;

    @Schema(description = "通道ID", example = "26571")
    @ExcelProperty("通道ID")
    private String channelId;

    @Schema(description = "设备ID", example = "10185")
    @ExcelProperty("设备ID")
    private String deviceId;

    @Schema(description = "RTMP播放流地址", example = "https://www.iocoder.cn")
    @ExcelProperty("RTMP播放流地址")
    private String rtmpUrl;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private String createBy;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private String updateBy;

}