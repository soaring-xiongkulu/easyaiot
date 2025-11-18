package com.basiclab.iot.sink.codec;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * IotDeviceMessageCodec
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface IotDeviceMessageCodec {

    /**
     * 编码消息
     *
     * @param message 消息
     * @return 编码后的消息内容
     */
    byte[] encode(IotDeviceMessage message);

    /**
     * 解码消息
     *
     * @param bytes 消息内容
     * @return 解码后的消息内容
     */
    IotDeviceMessage decode(byte[] bytes);

    /**
     * @return 支持的 Topic 模式（支持通配符，如 /iot/${productIdentification}/${deviceIdentification}/config/push）
     * 必须返回非空的 topic 模式，用于匹配编解码器
     */
    String topic();

    /**
     * 判断是否支持该 Topic
     *
     * @param topic 实际的 Topic
     * @return 是否支持
     */
    default boolean supports(String topic) {
        String topicPattern = topic();
        if (topicPattern == null || topicPattern.isEmpty()) {
            return false;
        }
        // 将模板转换为正则表达式
        String regex = topicPattern
                .replace("${productIdentification}", "[^/]+")
                .replace("${deviceIdentification}", "[^/]+")
                .replace("${identifier}", "[^/]+")
                .replace("/", "\\/");
        return topic != null && topic.matches("^" + regex + "$");
    }

}
