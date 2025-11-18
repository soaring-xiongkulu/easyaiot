package com.basiclab.iot.dataset.domain.dataset.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

/**
 * DatasetTaskUserPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 标注任务用户分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetTaskUserPageReqVO extends PageParam {

    @Schema(description = "任务ID", example = "11012")
    private Long taskId;

    @Schema(description = "标注用户ID", example = "6114")
    private Long userId;

    @Schema(description = "审核用户ID", example = "22950")
    private Long auditUserId;

}