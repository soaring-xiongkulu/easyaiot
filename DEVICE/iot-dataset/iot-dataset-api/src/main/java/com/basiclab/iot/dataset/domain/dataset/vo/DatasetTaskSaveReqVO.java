package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

/**
 * DatasetTaskSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务新增/修改 Request VO")
@Data
public class DatasetTaskSaveReqVO {

    @Schema(description = "主键ID", example = "15219")
    private Long id;

    @Schema(description = "任务名称", example = "李四")
    @NotEmpty(message = "任务名称不能为空")
    private String name;

    @Schema(description = "数据集ID", example = "4591")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "数据范围[0:全部,1:无标注,2:有标注]")
    @NotNull(message = "数据范围[0:全部,1:无标注,2:有标注]不能为空")
    private Integer dataRange;

    @Schema(description = "计划标注数量")
    @NotNull(message = "计划标注数量不能为空")
    private Integer plannedQuantity;

    @Schema(description = "已标注数量")
    private Integer markedQuantity;

    @Schema(description = "新标签入库[0:否,1:是]")
    @NotNull(message = "新标签入库[0:否,1:是]不能为空")
    private Integer newLabel;

    @Schema(description = "完成状态[0:未完成,1:已完成]", example = "1")
    @NotNull(message = "完成状态[0:未完成,1:已完成]不能为空")
    private Integer finishStatus;

    @Schema(description = "完成时间")
    private LocalDateTime finishTime;

    @Schema(description = "模型ID", example = "24336")
    private Long modelId;

    @Schema(description = "模型服务ID", example = "2482")
    private Long modelServeId;

    @Schema(description = "是否停止[0:否,1:是]")
    @NotNull(message = "是否停止[0:否,1:是]不能为空")
    private Integer isStop;

    @Schema(description = "任务类型[0:智能标注,1:人员标注,2:审核]", example = "1")
    @NotNull(message = "任务类型[0:智能标注,1:人员标注,2:审核]不能为空")
    private Integer taskType;

    @Schema(description = "截止时间(人员或审核)")
    private LocalDateTime endTime;

    @Schema(description = "无目标数量", example = "7137")
    private Integer notTargetCount;

}