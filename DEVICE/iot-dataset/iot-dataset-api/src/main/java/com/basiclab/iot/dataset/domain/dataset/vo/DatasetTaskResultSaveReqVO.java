package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * DatasetTaskResultSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务结果新增/修改 Request VO")
@Data
public class DatasetTaskResultSaveReqVO {

    @Schema(description = "主键ID", example = "31197")
    private Long id;

    @Schema(description = "数据集图片ID", example = "10634")
    @NotNull(message = "数据集图片ID不能为空")
    private Long datasetImageId;

    @Schema(description = "模型ID", example = "28292")
    private Long modelId;

    @Schema(description = "是否有标注[0:无,1:有]")
    @NotNull(message = "是否有标注[0:无,1:有]不能为空")
    private Integer hasAnno;

    @Schema(description = "标注信息")
    @NotEmpty(message = "标注信息不能为空")
    private String annos;

    @Schema(description = "任务类型[0:智能标注,1:人员标注,2:审核]", example = "2")
    @NotNull(message = "任务类型[0:智能标注,1:人员标注,2:审核]不能为空")
    private Integer taskType;

    @Schema(description = "标注或审核的用户id", example = "15486")
    @NotNull(message = "标注或审核的用户id不能为空")
    private Long userId;

    @Schema(description = "通过状态[0:待审核,1:通过,2:驳回]", example = "1")
    @NotNull(message = "通过状态[0:待审核,1:通过,2:驳回]不能为空")
    private Integer passStatus;

    @Schema(description = "任务ID", example = "6721")
    @NotNull(message = "任务ID不能为空")
    private Long taskId;

    @Schema(description = "驳回原因", example = "不好")
    private String reason;

    @Schema(description = "是否修改过[0:否,1是]")
    @NotNull(message = "是否修改过[0:否,1是]不能为空")
    private Integer isUpdate;

}