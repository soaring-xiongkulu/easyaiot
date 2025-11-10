package com.basiclab.iot.system.enums.sms;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 短信的模板类型枚举
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Getter
@AllArgsConstructor
public enum SmsTemplateTypeEnum {

    VERIFICATION_CODE(1), // 验证码
    NOTICE(2), // 通知
    PROMOTION(3), // 营销
    ;

    /**
     * 类型
     */
    private final int type;

}
