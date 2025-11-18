package com.basiclab.iot.sink.enums;

import com.basiclab.iot.common.core.ArrayValuable;
import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;

/**
 * IotDeviceStateEnum
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@RequiredArgsConstructor
@Getter
public enum IotDeviceStateEnum implements ArrayValuable<Integer> {

    INACTIVE(0, "未激活"),
    ONLINE(1, "在线"),
    OFFLINE(2, "离线");

    public static final Integer[] ARRAYS = Arrays.stream(values()).map(IotDeviceStateEnum::getState).toArray(Integer[]::new);

    /**
     * 状态
     */
    private final Integer state;
    /**
     * 状态名
     */
    private final String name;

    @Override
    public Integer[] array() {
        return ARRAYS;
    }

    public static boolean isOnline(Integer state) {
        return ONLINE.getState().equals(state);
    }

    public static boolean isNotOnline(Integer state) {
        return !isOnline(state);
    }

}
