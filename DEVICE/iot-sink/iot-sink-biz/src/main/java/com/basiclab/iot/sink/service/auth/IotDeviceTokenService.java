package com.basiclab.iot.sink.service.auth;

import com.basiclab.iot.sink.util.IotDeviceAuthUtils;

/**
 * IoT 设备 Token Service 接口
 *
 * @author 芋道源码
 */
public interface IotDeviceTokenService {

    /**
     * 创建设备 Token
     *
     * @param productKey 产品 Key
     * @param deviceName 设备名称
     * @return 设备 Token
     */
    String createToken(String productKey, String deviceName);

    /**
     * 验证设备 Token
     *
     * @param token 设备 Token
     * @return 设备信息
     */
    IotDeviceAuthUtils.DeviceInfo verifyToken(String token);

    /**
     * 解析用户名
     *
     * @param username 用户名
     * @return 设备信息
     */
    IotDeviceAuthUtils.DeviceInfo parseUsername(String username);

}
