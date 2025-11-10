package com.basiclab.iot.system.enums.sms;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 短信的接收状态枚举
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date 2024/2/1 13:39
 */
@Getter
@AllArgsConstructor
public enum SmsReceiveStatusEnum {

    INIT(0), // 初始化
    SUCCESS(10), // 接收成功
    FAILURE(20), // 接收失败
    ;

    private final int status;

}
