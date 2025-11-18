package com.basiclab.iot.system.enums.sms;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * SmsSendStatusEnum
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Getter
@AllArgsConstructor
public enum SmsSendStatusEnum {

    INIT(0), // 初始化
    SUCCESS(10), // 发送成功
    FAILURE(20), // 发送失败
    IGNORE(30), // 忽略，即不发送
    ;

    private final int status;

}
