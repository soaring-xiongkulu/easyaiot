package com.basiclab.iot.system.framework.sms.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotNull;
import java.time.Duration;

/**
 * SmsCodeProperties
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ConfigurationProperties(prefix = "iot.sms-code")
@Validated
@Data
public class SmsCodeProperties {

    @NotNull(message = "过期时间不能为空")
    private Duration expireTimes;
    /**
     * 短信发送频率
     */
    @NotNull(message = "短信发送频率不能为空")
    private Duration sendFrequency;
    /**
     * 每日发送最大数量
     */
    @NotNull(message = "每日发送最大数量不能为空")
    private Integer sendMaximumQuantityPerDay;
    /**
     * 验证码最小值
     */
    @NotNull(message = "验证码最小值不能为空")
    private Integer beginCode;
    /**
     * 验证码最大值
     */
    @NotNull(message = "验证码最大值不能为空")
    private Integer endCode;

}
