package com.basiclab.iot.sink.service;

/**
 * DeviceServerIdService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface DeviceServerIdService {

    /**
     * 存储设备与 serverId 的映射
     *
     * @param deviceId 设备 ID
     * @param serverId 网关 serverId
     */
    void saveDeviceServerId(Long deviceId, String serverId);

    /**
     * 获取设备对应的 serverId
     *
     * @param deviceId 设备 ID
     * @return serverId，如果不存在返回 null
     */
    String getDeviceServerId(Long deviceId);

    /**
     * 删除设备与 serverId 的映射
     *
     * @param deviceId 设备 ID
     */
    void removeDeviceServerId(Long deviceId);

}

