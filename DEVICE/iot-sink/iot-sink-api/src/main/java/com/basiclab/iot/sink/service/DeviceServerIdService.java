package com.basiclab.iot.sink.service;

/**
 * 设备 ServerId 服务接口
 * <p>
 * 用于管理设备与网关 serverId 的映射关系（存储在 Redis 中）
 * <p>
 * 此接口在 sink-api 中定义，实现类在 sink-biz 中
 *
 * @author 翱翔的雄库鲁
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

