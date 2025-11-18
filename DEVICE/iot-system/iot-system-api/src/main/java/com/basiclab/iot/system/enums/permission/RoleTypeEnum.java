package com.basiclab.iot.system.enums.permission;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * RoleTypeEnum
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Getter
@AllArgsConstructor
public enum RoleTypeEnum {

    SYSTEM(1),
    /**
     * 自定义角色
     */
    CUSTOM(2);

    private final Integer type;

}
