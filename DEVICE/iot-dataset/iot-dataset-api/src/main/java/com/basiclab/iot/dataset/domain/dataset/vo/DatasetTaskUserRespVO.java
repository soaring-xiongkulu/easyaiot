package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

/**
 * DatasetTaskUserRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务用户 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetTaskUserRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "2425")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "任务ID", example = "11012")
    @ExcelProperty("任务ID")
    private Long taskId;

    @Schema(description = "标注用户ID", example = "6114")
    @ExcelProperty("标注用户ID")
    private Long userId;

    @Schema(description = "审核用户ID", example = "22950")
    @ExcelProperty("审核用户ID")
    private Long auditUserId;

}