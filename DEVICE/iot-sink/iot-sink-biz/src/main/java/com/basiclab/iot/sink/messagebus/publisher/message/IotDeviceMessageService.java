package com.basiclab.iot.sink.messagebus.publisher.message;


import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * IotDeviceMessageService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface IotDeviceMessageService {

    /**
     * 编码消息
     *
     * @param message               消息
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification  设备唯一标识
     * @return 编码后的消息内容
     */
    byte[] encodeDeviceMessage(IotDeviceMessage message,
                               String productIdentification, String deviceIdentification);

    /**
     * 解码消息
     *
     * @param bytes                 消息内容
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification  设备唯一标识
     * @return 解码后的消息内容
     */
    IotDeviceMessage decodeDeviceMessage(byte[] bytes,
                                         String productIdentification, String deviceIdentification);

    /**
     * 根据 Topic 解码消息
     *
     * @param bytes 消息内容
     * @param topic 实际的 Topic
     * @return 解码后的消息内容
     */
    IotDeviceMessage decodeDeviceMessageByTopic(byte[] bytes, String topic);

    /**
     * 发送消息
     *
     * @param message               消息
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification  设备唯一标识
     * @param serverId               设备连接的 serverId
     */
    void sendDeviceMessage(IotDeviceMessage message,
                           String productIdentification, String deviceIdentification, String serverId);

}
