package com.basiclab.iot.sink.auth.service;

import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.util.IotDeviceAuthUtils;

/**
 * DeviceAuthService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface DeviceAuthService {

    /**
     * 设备认证
     *
     * @param authReqDTO 认证请求
     * @return 认证结果
     */
    boolean authDevice(IotDeviceAuthReqDTO authReqDTO);

    /**
     * 创建设备 Token
     *
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification 设备唯一标识
     * @return 设备 Token
     */
    String createToken(String productIdentification, String deviceIdentification);

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

