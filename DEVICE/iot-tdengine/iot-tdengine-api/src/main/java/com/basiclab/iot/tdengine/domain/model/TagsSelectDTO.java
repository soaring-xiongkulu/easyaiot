package com.basiclab.iot.tdengine.domain.model;

import lombok.Data;

import javax.validation.constraints.NotBlank;

/**
 * @program: EasyAIoT
 * @description: 标签查询模型
 * @packagename: com.basiclab.iot.tdengine.api.domain.rule
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date: 2025-07-27 18:40
 **/
@Data
public class TagsSelectDTO {

    private String dataBaseName;

    @NotBlank(message = "invalid operation: stableName can not be empty")
    private String stableName;

    @NotBlank(message = "invalid operation: tagsName can not be empty")
    private String tagsName;

    private Long startTime;

    private Long endTime;

}
