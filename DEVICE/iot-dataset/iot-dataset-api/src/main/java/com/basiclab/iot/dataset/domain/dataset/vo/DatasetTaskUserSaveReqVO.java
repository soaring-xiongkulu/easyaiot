package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * DatasetTaskUserSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务用户新增/修改 Request VO")
@Data
public class DatasetTaskUserSaveReqVO {

    @Schema(description = "主键ID", example = "2425")
    private Long id;

    @Schema(description = "任务ID", example = "11012")
    @NotNull(message = "任务ID不能为空")
    private Long taskId;

    @Schema(description = "标注用户ID", example = "6114")
    @NotNull(message = "标注用户ID不能为空")
    private Long userId;

    @Schema(description = "审核用户ID", example = "22950")
    private Long auditUserId;

}