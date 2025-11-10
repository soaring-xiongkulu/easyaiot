package com.basiclab.iot.device.constant;

import lombok.Getter;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc    终端枚举
 * @created 2025-06-24
 */
public enum MpTerminalEnum {
    TER_DEVICE("device","设备端"),
    TER_APP_IOS("ios","移动app-ios端"),
    TER_APP_ANDROID("android","移动app-android端"),
    ;
    @Getter
    private String code;
    @Getter
    private String desc;

    MpTerminalEnum(String code, String desc){
        this.code = code;
        this.desc = desc;
    }
}
