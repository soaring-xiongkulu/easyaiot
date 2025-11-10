package com.basiclab.iot.common.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 环境配置
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ConfigurationProperties(prefix = "iot.env")
@Data
public class EnvProperties {

    public static final String TAG_KEY = "iot.env.tag";

    /**
     * 环境标签
     */
    private String tag;

}
