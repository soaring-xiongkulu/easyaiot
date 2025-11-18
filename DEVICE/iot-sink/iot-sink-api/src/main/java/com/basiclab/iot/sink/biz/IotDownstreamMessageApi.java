package com.basiclab.iot.sink.biz;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

import java.util.List;

/**
 * IotDownstreamMessageApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface IotDownstreamMessageApi {

    /**
     * 发送下行消息到设备
     * <p>
     * 如果消息中指定了 serverId，则发送到对应的网关；
     * 如果未指定 serverId，则发送到通用 Topic，由所有网关实例处理
     *
     * @param message 设备消息
     *                必须包含 deviceId
     *                可选包含 serverId（如果指定，则只发送到该网关）
     */
    void sendDownstreamMessage(IotDeviceMessage message);

    /**
     * 发送下行消息到指定网关的设备
     * <p>
     * 明确指定网关的 serverId，消息将只发送到该网关
     *
     * @param serverId 网关的 serverId 标识
     * @param message  设备消息
     *                 必须包含 deviceId
     */
    void sendDownstreamMessageToGateway(String serverId, IotDeviceMessage message);

    /**
     * 根据设备 ID 发送下行消息
     * <p>
     * 自动从 Redis 中查找设备对应的 serverId，然后发送消息
     * 如果找不到 serverId，则发送到通用 Topic，由所有网关实例处理
     *
     * @param deviceId 设备 ID
     * @param message  设备消息（不需要设置 deviceId，会自动设置）
     */
    void sendDownstreamMessageByDeviceId(Long deviceId, IotDeviceMessage message);

    /**
     * 关闭设备连接
     * <p>
     * 根据客户端 ID 列表关闭对应的设备连接
     *
     * @param clientIds 客户端 ID 列表
     * @return 关闭成功的数量
     */
    int closeConnection(List<String> clientIds);

}

