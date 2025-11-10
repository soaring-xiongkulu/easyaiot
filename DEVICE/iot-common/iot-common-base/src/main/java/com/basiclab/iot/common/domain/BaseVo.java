package com.basiclab.iot.common.domain;

import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class BaseVo implements Serializable {
    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "id", example = "admin")
    protected Long id;

    @ApiModelProperty(value = "创建人", example = "admin")
    protected String createdBy;

    @ApiModelProperty(value = "创建时间", example = "2020/7/16 14:31:27")
    protected LocalDateTime createdTime;

    @ApiModelProperty(value = "更新人", example = "admin")
    protected String updatedBy;

    @ApiModelProperty(value = "更新时间", example = "2020/7/16 14:31:27")
    protected LocalDateTime updatedTime;
}
