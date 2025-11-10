package com.basiclab.iot.common.domain;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

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
@ApiModel(value = "排序规则", description = "按指定字段进行升序或降序排列")
public class SortOrder {

    @ApiModelProperty(value = "排序字段属性名称", example = "id")
    private String property;

    @ApiModelProperty(value = "排序方向：ASC(升序)；DESC(降序)", example = "DESC")
    private Direction direction;
}
