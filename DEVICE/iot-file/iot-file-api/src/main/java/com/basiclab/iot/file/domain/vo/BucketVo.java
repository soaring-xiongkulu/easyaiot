package com.basiclab.iot.file.domain.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.time.ZonedDateTime;

/**
 * 桶信息
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "桶对象", description = "桶Vo")
public class BucketVo {
    @ApiModelProperty(value = "桶名称")
    private String name;
    @ApiModelProperty(value = "创建时间")
    private ZonedDateTime creationDate;
}
