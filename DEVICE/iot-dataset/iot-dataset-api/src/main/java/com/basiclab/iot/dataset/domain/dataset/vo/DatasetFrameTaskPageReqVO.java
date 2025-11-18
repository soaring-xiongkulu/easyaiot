package com.basiclab.iot.dataset.domain.dataset.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

/**
 * DatasetFrameTaskPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频流帧捕获任务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetFrameTaskPageReqVO extends PageParam {

    @Schema(description = "数据集ID", example = "15239")
    private Long datasetId;

    @Schema(description = "任务名称", example = "赵六")
    private String taskName;

    @Schema(description = "任务编码")
    private String taskCode;

    @Schema(description = "任务类型[0:实时流抽帧,1:GB28181流抽帧]", example = "1")
    private Short taskType;

    @Schema(description = "通道ID", example = "26571")
    private String channelId;

    @Schema(description = "设备ID", example = "10185")
    private String deviceId;

    @Schema(description = "RTMP播放流地址", example = "https://www.iocoder.cn")
    private String rtmpUrl;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "创建人")
    private String updateBy;

}