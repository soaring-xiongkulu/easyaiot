package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

/**
 * DatasetTaskRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetTaskRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "15219")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "任务名称", example = "李四")
    @ExcelProperty("任务名称")
    private String name;

    @Schema(description = "数据集ID", example = "4591")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "数据范围[0:全部,1:无标注,2:有标注]")
    @ExcelProperty("数据范围[0:全部,1:无标注,2:有标注]")
    private Integer dataRange;

    @Schema(description = "计划标注数量")
    @ExcelProperty("计划标注数量")
    private Integer plannedQuantity;

    @Schema(description = "已标注数量")
    @ExcelProperty("已标注数量")
    private Integer markedQuantity;

    @Schema(description = "新标签入库[0:否,1:是]")
    @ExcelProperty("新标签入库[0:否,1:是]")
    private Integer newLabel;

    @Schema(description = "完成状态[0:未完成,1:已完成]", example = "1")
    @ExcelProperty("完成状态[0:未完成,1:已完成]")
    private Integer finishStatus;

    @Schema(description = "完成时间")
    @ExcelProperty("完成时间")
    private LocalDateTime finishTime;

    @Schema(description = "模型ID", example = "24336")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "模型服务ID", example = "2482")
    @ExcelProperty("模型服务ID")
    private Long modelServeId;

    @Schema(description = "是否停止[0:否,1:是]")
    @ExcelProperty("是否停止[0:否,1:是]")
    private Integer isStop;

    @Schema(description = "任务类型[0:智能标注,1:人员标注,2:审核]", example = "1")
    @ExcelProperty("任务类型[0:智能标注,1:人员标注,2:审核]")
    private Integer taskType;

    @Schema(description = "截止时间(人员或审核)")
    @ExcelProperty("截止时间(人员或审核)")
    private LocalDateTime endTime;

    @Schema(description = "无目标数量", example = "7137")
    @ExcelProperty("无目标数量")
    private Integer notTargetCount;

}