package com.basiclab.iot.infra.enums.config;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * ConfigTypeEnum
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Getter
@AllArgsConstructor
public enum ConfigTypeEnum {

    SYSTEM(1),
    /**
     * 自定义配置
     */
    CUSTOM(2);

    private final Integer type;

}
