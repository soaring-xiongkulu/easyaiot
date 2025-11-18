package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

/**
 * DatasetTaskResultRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务结果 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetTaskResultRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "31197")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "数据集图片ID", example = "10634")
    @ExcelProperty("数据集图片ID")
    private Long datasetImageId;

    @Schema(description = "模型ID", example = "28292")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "是否有标注[0:无,1:有]")
    @ExcelProperty("是否有标注[0:无,1:有]")
    private Integer hasAnno;

    @Schema(description = "标注信息")
    @ExcelProperty("标注信息")
    private String annos;

    @Schema(description = "任务类型[0:智能标注,1:人员标注,2:审核]", example = "2")
    @ExcelProperty("任务类型[0:智能标注,1:人员标注,2:审核]")
    private Integer taskType;

    @Schema(description = "标注或审核的用户id", example = "15486")
    @ExcelProperty("标注或审核的用户id")
    private Long userId;

    @Schema(description = "通过状态[0:待审核,1:通过,2:驳回]", example = "1")
    @ExcelProperty("通过状态[0:待审核,1:通过,2:驳回]")
    private Integer passStatus;

    @Schema(description = "任务ID", example = "6721")
    @ExcelProperty("任务ID")
    private Long taskId;

    @Schema(description = "驳回原因", example = "不好")
    @ExcelProperty("驳回原因")
    private String reason;

    @Schema(description = "是否修改过[0:否,1是]")
    @ExcelProperty("是否修改过[0:否,1是]")
    private Integer isUpdate;

}